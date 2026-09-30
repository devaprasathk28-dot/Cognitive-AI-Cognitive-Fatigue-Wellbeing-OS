import csv
import time
from datetime import datetime

from monitor.fatigue_score_engine import CognitiveFatigueModel

INPUT_FILE = "data/usage_categorized_v2.csv"

model = CognitiveFatigueModel()

print("🧠 Cognitive Engine Connected To Usage Monitor")


def read_last_activity():
    try:
        with open(INPUT_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            return None

        return rows[-1]

    except Exception:
        return None


while True:

    try:
        activity = read_last_activity()

        if activity is None:
            time.sleep(5)
            continue

        category = activity.get("category", "Unknown")
        app_name = activity.get("app_display_name", "Unknown")

        # SAFE duration parsing
        try:
            duration = int(activity.get("duration_sec", 5))
        except:
            duration = 5

        hour = datetime.now().hour

        state = model.update(category, duration, hour)

        print(
            f"[{state['timestamp']}] "
            f"App={app_name} "
            f"Category={category} "
            f"Fatigue={state['fatigue_score']} "
            f"Level={state['level']} "
            f"Burnout={state['burnout_probability']}"
        )

        time.sleep(duration)

    except Exception as e:
        print("Bridge error:", e)
        time.sleep(5)