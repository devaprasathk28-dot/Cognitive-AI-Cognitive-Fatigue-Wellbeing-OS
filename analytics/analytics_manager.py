from storage.db import get_connection, fatigue_to_focus_score
import datetime

def get_dashboard_metrics():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get today's stats
    cursor.execute('''
        SELECT SUM(duration_sec), COUNT(*) 
        FROM sessions 
        WHERE date(timestamp) = date('now', 'localtime')
    ''')
    res = cursor.fetchone()
    total_time_sec = res[0] or 0
    sessions = res[1] or 0
    
    cursor.execute('''
        SELECT app_name, SUM(duration_sec) as total
        FROM sessions
        WHERE date(timestamp) = date('now', 'localtime')
        GROUP BY app_name
        ORDER BY total DESC
        LIMIT 1
    ''')
    top_app_row = cursor.fetchone()
    top_app = top_app_row[0] if top_app_row else "N/A"
    
    cursor.execute('''
        SELECT AVG(fatigue_score)
        FROM sessions
        WHERE date(timestamp) = date('now', 'localtime')
    ''')
    avg_fatigue_row = cursor.fetchone()
    avg_fatigue = avg_fatigue_row[0] if avg_fatigue_row and avg_fatigue_row[0] is not None else 0
    avg_focus = fatigue_to_focus_score(avg_fatigue)

    cursor.execute('''
        SELECT COUNT(*)
        FROM notifications
        WHERE date(timestamp) = date('now', 'localtime')
    ''')
    notif_row = cursor.fetchone()
    notification_total = notif_row[0] if notif_row else 0
    
    conn.close()
    
    return {
        "total_time": total_time_sec // 60,
        "sessions": sessions,
        "top_app": top_app,
        "avg_focus_score": avg_focus,
        "notification_total": notification_total
    }

def get_weekly_summary():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT SUM(duration_sec)
        FROM sessions 
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
    ''')
    res = cursor.fetchone()
    weekly_time_sec = res[0] or 0
    
    cursor.execute('''
        SELECT app_name, SUM(duration_sec) as total
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
        GROUP BY app_name
        ORDER BY total DESC
        LIMIT 1
    ''')
    top_app_row = cursor.fetchone()
    top_app = top_app_row[0] if top_app_row else "N/A"
    
    cursor.execute('''
        SELECT AVG(fatigue_score)
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
    ''')
    avg_fatigue_row = cursor.fetchone()
    avg_fatigue = avg_fatigue_row[0] if avg_fatigue_row and avg_fatigue_row[0] is not None else 0
    avg_focus = fatigue_to_focus_score(avg_fatigue)
    
    cursor.execute('''
        SELECT category, SUM(duration_sec) as total
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
        GROUP BY category
        ORDER BY total DESC
    ''')
    categories = {row[0]: row[1] // 60 for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "weekly_time": weekly_time_sec // 60,
        "top_app": top_app,
        "avg_focus": avg_focus,
        "categories": categories
    }

def get_daily_usage_last_7_days():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Pre-fill last 7 days
    today = datetime.date.today()
    date_range = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    daily_dict = {d.strftime('%Y-%m-%d'): 0 for d in date_range}
    
    cursor.execute('''
        SELECT date(timestamp), SUM(duration_sec)
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
        GROUP BY date(timestamp)
    ''')
    
    for row in cursor.fetchall():
        d_str = row[0]
        if d_str in daily_dict:
            daily_dict[d_str] = row[1] // 60
            
    conn.close()
    
    # Convert keys to day names
    return {datetime.datetime.strptime(k, '%Y-%m-%d').strftime('%a'): v for k, v in daily_dict.items()}

def get_day_detail(day_name: str):
    # Map back 'Mon', 'Tue' to recent dates
    today = datetime.date.today()
    target_date = None
    for i in range(7):
        d = today - datetime.timedelta(days=i)
        if d.strftime('%a') == day_name:
            target_date = d.strftime('%Y-%m-%d')
            break
            
    if not target_date:
        return {"apps": {}, "categories": {}}
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT app_name, SUM(duration_sec) as total
        FROM sessions
        WHERE date(timestamp) = ?
        GROUP BY app_name
        ORDER BY total DESC
    ''', (target_date,))
    apps = {row[0]: row[1] // 60 for row in cursor.fetchall()}
    
    cursor.execute('''
        SELECT category, SUM(duration_sec) as total
        FROM sessions
        WHERE date(timestamp) = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (target_date,))
    categories = {row[0]: row[1] // 60 for row in cursor.fetchall()}
    
    conn.close()
    return {
        "apps": apps,
        "categories": categories
    }
