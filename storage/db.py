import sqlite3
import os
from datetime import datetime
from monitor.paths import get_data_path

DB_PATH = get_data_path("cognitive.db")

def get_connection():
    # Use check_same_thread=False since we use DB from multiple threads (worker, ui)
    # We will handle our own small scoped cursors.
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # App Usage Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT,
            window_title TEXT,
            category TEXT,
            duration_sec INTEGER,
            fatigue_score REAL,
            burnout_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI Chat History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_msg TEXT,
            ai_msg TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priority TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Focus Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration_sec INTEGER,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    
    # Auto-migrate if JSON exists and DB is empty
    cursor.execute("SELECT COUNT(*) FROM sessions")
    if cursor.fetchone()[0] == 0:
        import json, os
        from monitor.paths import get_data_path
        old_log = get_data_path("usage_log.json")
        if os.path.exists(old_log):
            try:
                with open(old_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        cursor.execute('''
                            INSERT INTO sessions (app_name, category, duration_sec, fatigue_score, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            item.get("app", "Unknown"),
                            item.get("category", "Unknown"),
                            item.get("duration", 0),
                            item.get("fatigue", 0.0),
                            item.get("timestamp", datetime.now().isoformat())
                        ))
                conn.commit()
            except Exception as e:
                print(f"Migration error: {e}")
                
    conn.close()

def log_session(app_name, title, category, duration, fatigue, burnout):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (app_name, window_title, category, duration_sec, fatigue_score, burnout_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (app_name, title, category, duration, fatigue, burnout))
    conn.commit()
    conn.close()

def fatigue_to_focus_score(fatigue: float) -> int:
    """Normalize fatigue to a 0-100 focus score safely handling 0-1 and 0-100 ranges."""
    try:
        f = float(fatigue)
    except (ValueError, TypeError):
        return 80
    if f <= 1.0:
        return int(max(0, min(100, round((1.0 - f) * 100))))
    return int(max(0, min(100, round(100.0 - f))))

def log_notification(priority: str, message: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (priority, message)
        VALUES (?, ?)
    ''', (priority, message))
    conn.commit()
    conn.close()

def get_notifications(limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, priority, message, timestamp
        FROM notifications
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "priority": r[1], "message": r[2], "timestamp": r[3]} for r in rows]

def clear_notifications():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notifications')
    conn.commit()
    conn.close()

def log_focus_session(duration_sec: int, status: str = "completed"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO focus_sessions (duration_sec, status)
        VALUES (?, ?)
    ''', (duration_sec, status))
    conn.commit()
    conn.close()

def get_focus_stats_today():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(duration_sec), 0)
        FROM focus_sessions
        WHERE date(timestamp) = date('now', 'localtime') AND status = 'completed'
    ''')
    row = cursor.fetchone()
    conn.close()
    count = row[0] if row else 0
    total_sec = row[1] if row else 0
    return {"completed_count": count, "total_seconds": total_sec}

def save_chat_message(user_msg: str, ai_msg: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (user_msg, ai_msg)
        VALUES (?, ?)
    ''', (user_msg, ai_msg))
    conn.commit()
    conn.close()

def get_chat_history(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_msg, ai_msg, timestamp
        FROM chat_history
        ORDER BY id ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"user": r[0], "ai": r[1], "timestamp": r[2]} for r in rows]

def get_streak_count() -> int:
    """Calculate consecutive active days from tracked sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT date(timestamp)
        FROM sessions
        ORDER BY date(timestamp) DESC
        LIMIT 60
    ''')
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()

    if not rows:
        return 1

    from datetime import date, timedelta
    today = date.today()
    streak = 0
    check_day = today

    # Check if there is data today; if not, check starting yesterday
    first_date_str = rows[0]
    try:
        first_date = date.fromisoformat(first_date_str)
        if first_date != today and first_date != (today - timedelta(days=1)):
            return 1
        if first_date == (today - timedelta(days=1)):
            check_day = first_date
    except Exception:
        return 1

    date_set = set(rows)
    while check_day.isoformat() in date_set:
        streak += 1
        check_day -= timedelta(days=1)

    return max(1, streak)

def get_today_deep_work_stats():
    """Returns deep work seconds, distraction count, and screen time today."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, duration_sec
        FROM sessions
        WHERE date(timestamp) = date('now', 'localtime')
    ''')
    rows = cursor.fetchall()
    conn.close()

    deep_work_sec = 0
    distraction_count = 0
    total_screen_sec = 0

    deep_categories = {"Development", "Work", "Productivity", "Writing", "Learning", "Research"}
    distract_categories = {"Entertainment", "Gaming", "Social Media", "Distraction"}

    for cat, dur in rows:
        dur = dur or 0
        total_screen_sec += dur
        if cat in deep_categories:
            deep_work_sec += dur
        elif cat in distract_categories:
            distraction_count += 1

    return {
        "deep_work_sec": deep_work_sec,
        "distraction_count": distraction_count,
        "total_screen_sec": total_screen_sec
    }

init_db()

