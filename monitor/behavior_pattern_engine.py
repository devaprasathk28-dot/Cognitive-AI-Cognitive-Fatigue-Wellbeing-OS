import csv
import os
from datetime import datetime
from collections import defaultdict

INPUT_FILE = "data/usage_sessions.csv"
OUTPUT_FILE = "data/behavior_patterns.json"


def load_sessions():

    if not os.path.exists(INPUT_FILE):
        return []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def analyze_patterns(sessions):

    total_time_by_category = defaultdict(int)
    session_count_by_category = defaultdict(int)
    hourly_activity = defaultdict(int)

    deep_work_sessions = 0
    distraction_sessions = 0

    for s in sessions:

        category = s.get("category", "Unknown")
        duration = int(float(s.get("duration_sec", 0)))

        timestamp = s.get("start_time", "")
        hour = 0

        if timestamp:
            hour = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").hour

        # -----------------------------
        # CATEGORY TIME
        # -----------------------------
        total_time_by_category[category] += duration
        session_count_by_category[category] += 1

        # -----------------------------
        # HOURLY PATTERN
        # -----------------------------
        hourly_activity[hour] += duration

        # -----------------------------
        # FOCUS QUALITY
        # -----------------------------
        if s.get("focus_type") == "Deep Work":
            deep_work_sessions += 1

        if category in ["Entertainment", "Browsing"]:
            if duration > 300:
                distraction_sessions += 1

    # -----------------------------
    # DERIVED METRICS
    # -----------------------------
    total_time = sum(total_time_by_category.values()) or 1

    productivity_ratio = (
        total_time_by_category.get("Development", 0) +
        total_time_by_category.get("Learning", 0)
    ) / total_time

    distraction_ratio = (
        total_time_by_category.get("Entertainment", 0)
    ) / total_time

    # Peak productivity hour
    peak_hour = max(hourly_activity, key=lambda k: hourly_activity[k]) if hourly_activity else None

    return {
        "total_time_by_category": dict(total_time_by_category),
        "session_count_by_category": dict(session_count_by_category),
        "productivity_ratio": round(productivity_ratio, 2),
        "distraction_ratio": round(distraction_ratio, 2),
        "deep_work_sessions": deep_work_sessions,
        "distraction_sessions": distraction_sessions,
        "peak_productivity_hour": peak_hour
    }


def save_patterns(patterns):

    import json

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=4)


def run_behavior_analysis():

    print("🧠 Behavior Pattern Engine Running")

    sessions = load_sessions()

    if not sessions:
        print("No session data found")
        return

    patterns = analyze_patterns(sessions)

    save_patterns(patterns)

    print("✅ Behavior patterns updated")