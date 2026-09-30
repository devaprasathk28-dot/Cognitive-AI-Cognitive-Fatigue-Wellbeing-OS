import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
from monitor.paths import get_data_path

JSON_FILE = get_data_path("usage_log.json")
CSV_FILE = get_data_path("usage_sessions.csv")

# Caching mechanism
_DASHBOARD_CACHE = None
_LAST_CACHE_TIME = 0
CACHE_TTL = 30 # seconds

def load_data_df():
    try:
        if os.path.exists(JSON_FILE):
            df = pd.read_json(JSON_FILE)
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Map names to match old CSV format seamlessly
                if 'duration' in df.columns and 'duration_sec' not in df.columns:
                    df['duration_sec'] = df['duration']
                if 'app' in df.columns and 'app_display_name' not in df.columns:
                    df['app_display_name'] = df['app']
            return df
    except Exception as e:
        print("Pandas JSON Load Error:", e)
    
    # Fallback to CSV
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if not df.empty and 'start_time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['start_time'])
            return df
    except Exception as e:
        print("Pandas CSV Load Error:", e)
    
    return pd.DataFrame()

def compute_dashboard():
    global _DASHBOARD_CACHE, _LAST_CACHE_TIME
    if _DASHBOARD_CACHE and time.time() - _LAST_CACHE_TIME < CACHE_TTL:
        return _DASHBOARD_CACHE

    df = load_data_df()
    if df.empty:
        return {
            "total_time": 0, "sessions": 0, "top_app": "N/A", "avg_focus_score": 0,
            "notification_total": 0, "app_usage": {}, "category_usage": {}
        }

    total_time = int(df['duration_sec'].sum())
    sessions = len(df)
    
    app_usage = df.groupby('app_display_name')['duration_sec'].sum().to_dict()
    category_usage = df.groupby('category')['duration_sec'].sum().to_dict()
    
    top_app = max(app_usage, key=app_usage.get) if app_usage else "N/A"
    
    avg_focus = 0
    if 'fatigue' in df.columns:
        # compute focus from fatigue
        scores = (1 - df['fatigue']) * 100
        avg_focus = int(scores.mean())
    elif 'focus_score' in df.columns:
        avg_focus = int(df['focus_score'].mean())
        
    notification_total = int(df['notification_count'].sum()) if 'notification_count' in df.columns else 0

    res = {
        "total_time": total_time // 60,
        "sessions": sessions,
        "top_app": top_app,
        "avg_focus_score": avg_focus,
        "notification_total": notification_total,
        "app_usage": app_usage,
        "category_usage": category_usage,
    }
    _DASHBOARD_CACHE = res
    _LAST_CACHE_TIME = time.time()
    return res

def compute_weekly_summary():
    df = load_data_df()
    if df.empty:
        return {"weekly_time": 0, "top_app": "N/A", "avg_focus": 0, "categories": {}}

    last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
    df_week = df[df['timestamp'] >= last_week]
    
    if df_week.empty:
        return {"weekly_time": 0, "top_app": "N/A", "avg_focus": 0, "categories": {}}

    weekly_time = int(df_week['duration_sec'].sum() // 60)
    app_usage = df_week.groupby('app_display_name')['duration_sec'].sum()
    top_app = app_usage.idxmax() if not app_usage.empty else "N/A"
    
    avg_focus = 0
    if 'fatigue' in df_week.columns:
        scores = (1 - df_week['fatigue']) * 100
        avg_focus = int(scores.mean())
    
    cat_usage = df_week.groupby('category')['duration_sec'].sum()
    categories = {cat: int(secs // 60) for cat, secs in cat_usage.sort_values(ascending=False).items()}
    
    return {
        "weekly_time": weekly_time,
        "top_app": top_app,
        "avg_focus": avg_focus,
        "categories": categories
    }

def get_top_apps(n=5):
    usage = compute_dashboard()["app_usage"]
    return sorted(usage.items(), key=lambda x: x[1], reverse=True)[:n]

def get_category_breakdown():
    usage = compute_dashboard()["category_usage"]
    return {cat: int(secs // 60) for cat, secs in usage.items()}

def get_daily_usage(hours=False):
    df = load_data_df()
    if df.empty: return {}

    if hours:
        today = pd.Timestamp.now().date()
        df_today = df[df['timestamp'].dt.date == today]
        if df_today.empty: return {}
        # Avoid SettingWithCopyWarning
        df_today = df_today.copy()
        df_today['hour'] = df_today['timestamp'].dt.hour
        hourly = df_today.groupby('hour')['duration_sec'].sum()
        return {f"{h}h": int(v // 60) for h, v in sorted(hourly.items())}
    else:
        # Generate last 7 days
        today = pd.Timestamp.now().date()
        date_range = [today - pd.Timedelta(days=i) for i in range(6, -1, -1)]
        
        last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
        df_week = df[df['timestamp'] >= last_week]
        
        daily_dict = {d: 0 for d in date_range}
        
        if not df_week.empty:
            df_week = df_week.copy()
            df_week['date'] = df_week['timestamp'].dt.date
            daily = df_week.groupby('date')['duration_sec'].sum()
            for d, v in daily.items():
                if d in daily_dict:
                    daily_dict[d] = int(v // 60)
        
        return {d.strftime('%a'): v for d, v in daily_dict.items()}

def get_day_detail(date_str):
    df = load_data_df()
    if df.empty: return {"apps": {}, "categories": {}}
    
    target_date = pd.to_datetime(date_str).date()
    df_day = df[df['timestamp'].dt.date == target_date]
    if df_day.empty: return {"apps": {}, "categories": {}}
    
    app_usage = df_day.groupby('app_display_name')['duration_sec'].sum()
    cat_usage = df_day.groupby('category')['duration_sec'].sum()
    
    return {
        "apps": {app: int(mins // 60) for app, mins in app_usage.sort_values(ascending=False).items()},
        "categories": {cat: int(mins // 60) for cat, mins in cat_usage.sort_values(ascending=False).items()}
    }

PRODUCTIVE = {"Development", "Productivity", "Learning"}

def compute_focus_score(category_usage: dict) -> int:
    total = sum(category_usage.values())
    if not total: return 0
    productive = sum(v for k, v in category_usage.items() if k in PRODUCTIVE)
    return min(100, int((productive / total) * 100))

def generate_insight(dash: dict) -> str:
    total_time  = dash["total_time"]
    top_app     = dash["top_app"].lower()
    cat_usage   = dash["category_usage"]
    notif_total = dash["notification_total"]
    sessions    = dash["sessions"]

    focus_pct        = compute_focus_score(cat_usage)
    entertainment_min = cat_usage.get("Entertainment", 0) // 60
    browsing_min      = cat_usage.get("Browsing", 0) // 60

    if total_time > 360:
        return "🚨 Extreme screen time. Cognitive fatigue risk is high — take a long break."
    if total_time > 240:
        return "⚠️ High usage today. Consider a 15-min break to protect focus."
    if "chrome" in top_app or "edge" in top_app or "firefox" in top_app:
        return "🌐 Browsing dominates your time. Try batching web tasks to protect deep work."
    if "youtube" in top_app or "netflix" in top_app or "spotify" in top_app:
        return "🎬 Entertainment is your top activity. Consider a focus session next."
    if entertainment_min > 60:
        return f"🎮 {entertainment_min} min on Entertainment. Set a limit to stay on track."
    if browsing_min > 90:
        return f"🌐 {browsing_min} min browsing. Try a distraction blocker."
    if notif_total > 30:
        return f"🔔 {notif_total} notifications today — interruptions hurt deep focus."
    if focus_pct >= 70:
        return "🔥 Excellent focus balance today! Productive categories dominate."
    if focus_pct >= 50:
        return "✅ Good balance. Keep productive sessions going."
    if focus_pct < 30:
        return "⚡ Less than 30% productive time. Try a 25-min focus sprint."
    if sessions > 40:
        return "🔀 High app-switching detected. Context switching drains cognitive energy."
    return "🧠 Tracking your patterns. Keep going!"
