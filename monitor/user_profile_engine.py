import json
import os
from monitor.paths import get_data_path

PROFILE_FILE = get_data_path("user_profile.json")

DEFAULT_PROFILE = {
    "experience_level": "beginner",   # beginner / intermediate / advanced
    "learning_style": "balanced",     # simple / detailed / balanced
    "focus_level": 0.5,               # 0–1
    "distraction_level": 0.0,         # 0–1
    "preferred_length": "medium",     # short / medium / long
    "topics": {},                     # {"python": 3, "ml": 1}
    "profile_thresholds": {
        "fatigue_break": 60,
        "fatigue_warning": 45
    }
}


def load_profile():
    if not os.path.exists(PROFILE_FILE):
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_PROFILE


def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)


def update_profile_from_chat(prompt: str):
    profile = load_profile()
    words = prompt.lower().split()

    for word in words:
        profile["topics"][word] = profile["topics"].get(word, 0) + 1

    if len(words) > 20:
        profile["preferred_length"] = "long"
    elif len(words) < 6:
        profile["preferred_length"] = "short"

    save_profile(profile)


def adjust_thresholds(profile):
    focus = profile.get("focus_level", 0.5)
    if focus < 0.4:
        profile["profile_thresholds"]["fatigue_break"] = 50
    elif focus > 0.7:
        profile["profile_thresholds"]["fatigue_break"] = 70
    save_profile(profile)

def update_productivity_profile():
    try:
        from monitor.analytics_engine import load_data_df
        df = load_data_df()
        if df.empty:
            return
            
        profile = load_profile()
        
        # Peak productivity hour
        if 'hour' not in df.columns and 'timestamp' in df.columns:
            df['hour'] = df['timestamp'].dt.hour
            
        if 'hour' in df.columns:
            prod_apps = df[df['category'].isin(["Development", "Productivity", "Learning"])]
            if not prod_apps.empty:
                peak_hour = int(prod_apps.groupby('hour')['duration_sec'].sum().idxmax())
                profile['peak_productivity_hour'] = peak_hour
        
        # Distraction ratio
        total_time = df['duration_sec'].sum()
        if total_time > 0:
            distraction_time = df[df['category'].isin(["Entertainment", "Browsing"])]['duration_sec'].sum()
            profile['distraction_ratio'] = round(distraction_time / total_time, 2)
            
        # Avg session length
        profile['avg_session_length'] = round(df['duration_sec'].mean(), 1)
        
        save_profile(profile)
    except Exception as e:
        print(f"Error updating productivity profile: {e}")