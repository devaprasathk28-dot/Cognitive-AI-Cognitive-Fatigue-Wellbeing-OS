import csv
import random
from datetime import datetime

SESSION_GAP_SEC = 15
SESSION_HEADER = [
    "session_id",
    "app_display_name",
    "category",
    "activity_intent",
    "start_time",
    "end_time",
    "duration_sec",
    "session_count",
    "notification_count",
    "focus_score",
    "confidence_avg",
    "focus_type",
    "timestamp"
]

def calc_focus_score(duration_sec, category):
    base = min(100, int(duration_sec / 6))  # 10 min = 100
    penalty = {"Entertainment": 30, "Browsing": 15}.get(category, 0)
    return max(0, base - penalty)

def classify_focus(duration_sec, category):
    if category in ["Development", "Learning"] and duration_sec >= 900:
        return "Deep Work"
    if duration_sec >= 300:
        return "Focused"
    return "Shallow / Distracted"

INPUT_FILE = "data/usage_categorized_v2.csv"
OUTPUT_FILE = "data/usage_sessions.csv"

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
def build_sessions():
    sessions = []
    current = None
    session_id = 1

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ts = parse_time(row["timestamp"])

            if not current:
                current = {
                    "session_id": session_id,
                    "app": row["app_display_name"],
                    "category": row["category"],
                    "intent": row["activity_intent"],
                    "start": ts,
                    "end": ts,
                    "confidence": float(row["confidence_score"]),
                    "count": 1
                }
                continue

            gap = (ts - current["end"]).total_seconds()

            if (
                gap <= SESSION_GAP_SEC
                and row["app_display_name"] == current["app"]
                and row["activity_intent"] == current["intent"]
            ):
                current["end"] = ts
                current["confidence"] += float(row["confidence_score"])
                current["count"] += 1
            else:
                sessions.append(current)
                session_id += 1

                intent = row.get("activity_intent")

                if not intent or intent.strip() == "":
                    cat = row.get("category", "Unknown")

                    if cat == "Development":
                        intent = "Coding / Technical Work"
                    elif cat == "Browsing":
                        intent = "Online Browsing"
                    elif cat == "Productivity":
                        intent = "Office / Writing Work"
                    elif cat == "Communication":
                        intent = "Meetings / Chat"
                    elif cat == "Entertainment":
                        intent = "Leisure / Media"
                    else:
                        intent = "General Usage"

                current = {
                    "session_id": session_id,
                    "app": row["app_display_name"],
                    "category": row["category"],
                    "intent": intent,
                    "start": ts,
                    "end": ts,
                    "confidence": float(row.get("confidence_score", 0.3)),
                    "count": 1
                }


        if current:
            sessions.append(current)

    return sessions
def save_sessions(sessions):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SESSION_HEADER)

        for s in sessions:
            duration = int((s["end"] - s["start"]).total_seconds()) + 5
            avg_conf = round(s["confidence"] / s["count"], 2)
            focus = classify_focus(duration, s["category"])

            notif_count = random.randint(0, 5)
            focus_score = calc_focus_score(duration, s["category"])
            writer.writerow([
                s["session_id"],
                s["app"],
                s["category"],
                s["intent"],
                s["start"].strftime("%Y-%m-%d %H:%M:%S"),
                s["end"].strftime("%Y-%m-%d %H:%M:%S"),
                duration,
                s["count"],
                notif_count,
                focus_score,
                avg_conf,
                focus,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

if __name__ == "__main__":
    print("🧠 STEP-2.5 SESSION BUILDER RUNNING")
    sessions = build_sessions()
    save_sessions(sessions)
    print(f"✅ {len(sessions)} sessions created")
