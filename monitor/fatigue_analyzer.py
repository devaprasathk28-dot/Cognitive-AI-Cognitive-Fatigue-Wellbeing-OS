import csv
from datetime import datetime
from monitor.fatigue_score_engine import CognitiveFatigueModel

FATIGUE_HEADER = [
    "timestamp",
    "fatigue_type",
    "severity",
    "description",
    "session_id",
    "confidence"
]

INPUT_FILE = "data/usage_sessions.csv"
OUTPUT_FILE = "data/fatigue_events.csv"

def parse_time(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
def detect_long_sessions(sessions):
    events = []
    for s in sessions:
        if (
            s["focus_type"] == "Deep Work"
            and int(s["duration_sec"]) >= 5400
        ):
            events.append({
                "type": "Prolonged Deep Work",
                "severity": "High",
                "desc": "Long continuous focus may cause mental fatigue",
                "session_id": s["session_id"],
                "confidence": s["confidence_avg"]
            })
    return events

def detect_dopamine_shift(sessions):
    events = []
    for i in range(len(sessions) - 1):
        a = sessions[i]
        b = sessions[i + 1]

        if (
            a["category"] in ["Development", "Learning"]
            and b["category"] == "Entertainment"
        ):
            gap = parse_time(b["start_time"]) - parse_time(a["end_time"])
            if gap.total_seconds() <= 300:
                events.append({
                    "type": "Productivity Drift",
                    "severity": "Medium",
                    "desc": "Sudden switch to entertainment suggests fatigue",
                    "session_id": b["session_id"],
                    "confidence": b["confidence_avg"]
                })
    return events

def detect_late_night_episode(sessions):
    events = []

    late_sessions = []
    for s in sessions:
        t = parse_time(s["start_time"])
        if t.hour >= 22 and float(s["confidence_avg"]) <= 0.4:
            late_sessions.append(s)

    if len(late_sessions) >= 3:
        first = late_sessions[0]
        last = late_sessions[-1]

        duration = (
            parse_time(last["end_time"]) -
            parse_time(first["start_time"])
        ).total_seconds()

        if duration <= 1800:  # 30 minutes
            events.append({
                "type": "Late Night Fatigue",
                "severity": "Medium",
                "desc": "Sustained low-confidence late-night activity detected",
                "session_id": f"{first['session_id']}–{last['session_id']}",
                "confidence": round(
                    sum(float(s["confidence_avg"]) for s in late_sessions) /
                    len(late_sessions), 2
                )
            })

    return events


def analyze_fatigue(sessions):
    events = []
    events += detect_long_sessions(sessions)
    events += detect_dopamine_shift(sessions)
    events += detect_late_night_episode(sessions)
    return events


def save_events(events):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FATIGUE_HEADER)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for e in events:
            writer.writerow([
                now,
                e["type"],
                e["severity"],
                e["desc"],
                e["session_id"],
                e["confidence"]
            ])

def load_sessions():
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def compute_score(events):
    model = CognitiveFatigueModel()

    # simulate fatigue update using event weight
    total_delta = 0

    for e in events:
        if e["severity"] == "High":
            total_delta += 10
        elif e["severity"] == "Medium":
            total_delta += 5
        else:
            total_delta += 2

    model.fatigue_score += total_delta
    model.save_state()

    return model.get_state()

if __name__ == "__main__":
    print("🧠 STEP-2.6 FATIGUE ANALYZER RUNNING")
    sessions = load_sessions()
    events = analyze_fatigue(sessions)
    save_events(events)
    print(f"⚠️ {len(events)} fatigue signals detected")
    score_report = compute_score(events)
    print(f"📊 Current Fatigue Score: {score_report['fatigue_score']} ({score_report['level']})")
    print("✅ STEP-2.6 FATIGUE ANALYZER COMPLETED")
