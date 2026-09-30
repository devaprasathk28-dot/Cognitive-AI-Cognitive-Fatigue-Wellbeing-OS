# ======================================================
# STEP-2.8 — RECOVERY ENGINE
# Cognitive Recovery Modeling
# ======================================================

from datetime import datetime
import csv
import os

INPUT_FILE = "data/usage_sessions.csv"
STATE_FILE = "data/fatigue_state.json"

# ------------------------------------------------------
# Helpers
# ------------------------------------------------------

def parse_time(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------
# Recovery Rules
# ------------------------------------------------------

def detect_long_breaks(sessions):
    recovery = 0

    for i in range(len(sessions) - 1):
        end_time = parse_time(sessions[i]["end_time"])
        next_start = parse_time(sessions[i + 1]["start_time"])

        gap = (next_start - end_time).total_seconds()

        # 30+ min break
        if gap >= 1800:
            recovery += 8

        # 1+ hour break
        if gap >= 3600:
            recovery += 15

    return recovery


def detect_deep_focus_recovery(sessions):
    recovery = 0

    for s in sessions:
        if (
            s["focus_type"] == "Deep Work"
            and float(s["confidence_avg"]) >= 0.7
            and int(s["duration_sec"]) >= 1800
        ):
            recovery += 5

    return recovery


def detect_sleep_reset(sessions):
    recovery = 0

    for i in range(len(sessions) - 1):
        end_time = parse_time(sessions[i]["end_time"])
        next_start = parse_time(sessions[i + 1]["start_time"])

        gap = (next_start - end_time).total_seconds()

        # 6+ hour gap (likely sleep)
        if gap >= 21600:
            recovery += 40

    return recovery


def detect_low_stimulus_period(sessions):
    recovery = 0

    low_stim_count = 0

    for s in sessions:
        if s["category"] in ["Utilities", "Productivity"] and float(s["confidence_avg"]) <= 0.4:
            low_stim_count += 1

    if low_stim_count >= 3:
        recovery += 5

    return recovery


# ------------------------------------------------------
# Main Recovery Computation
# ------------------------------------------------------

def compute_recovery_score(sessions):

    total_recovery = 0

    total_recovery += detect_long_breaks(sessions)
    total_recovery += detect_deep_focus_recovery(sessions)
    total_recovery += detect_sleep_reset(sessions)
    total_recovery += detect_low_stimulus_period(sessions)

    return total_recovery


# ------------------------------------------------------
# Loader
# ------------------------------------------------------

def load_sessions():
    if not os.path.exists(INPUT_FILE):
        return []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------
# Runner
# ------------------------------------------------------

if __name__ == "__main__":

    print("🧘 STEP-2.8 RECOVERY ENGINE RUNNING")

    sessions = load_sessions()

    if not sessions:
        print("No sessions found.")
    else:
        recovery = compute_recovery_score(sessions)
        print(f"🌿 Recovery Score: {recovery}")

    print("✅ STEP-2.8 COMPLETED")
