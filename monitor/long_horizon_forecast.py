import csv
import json
import os
from datetime import datetime
import statistics

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIMESERIES_FILE = os.path.join(BASE_DIR, "data", "fatigue_timeseries.csv")
STATE_FILE = os.path.join(BASE_DIR, "data", "fatigue_state.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cognitive_forecast.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE) as f:
        return json.load(f)


def load_timeseries():

    if not os.path.exists(TIMESERIES_FILE):
        return []

    scores = []

    with open(TIMESERIES_FILE, newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            scores.append(float(row["fatigue_score"]))

    return scores


def forecast(scores, current):

    if len(scores) < 5:
        trend = 0
    else:
        recent = scores[-5:]
        trend = statistics.mean(recent) - statistics.mean(scores[:5])

    predicted_30 = current + trend * 0.5
    predicted_2h = current + trend * 2

    predicted_30 = max(0, min(100, predicted_30))
    predicted_2h = max(0, min(100, predicted_2h))

    return predicted_30, predicted_2h


def forecast_burnout(current_burnout):

    tomorrow = current_burnout + 0.1

    return min(1.0, tomorrow)


def recommend_action(predicted_2h):

    if predicted_2h > 80:
        return "Immediate break recommended"

    if predicted_2h > 60:
        return "Schedule break within 20 minutes"

    if predicted_2h > 40:
        return "Micro-break recommended"

    return "Continue work"


def run_forecast():

    state = load_state()

    scores = load_timeseries()

    current_fatigue = state.get("fatigue_score", 0)
    burnout = state.get("burnout_probability", 0)

    f30, f2h = forecast(scores, current_fatigue)

    tomorrow_burnout = forecast_burnout(burnout)

    action = recommend_action(f2h)

    result = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "current_fatigue": current_fatigue,

        "predicted_30min_fatigue": round(f30, 2),

        "predicted_2h_fatigue": round(f2h, 2),

        "predicted_tomorrow_burnout": round(tomorrow_burnout, 3),

        "recommended_action": action

    }

    with open(OUTPUT_FILE, "w") as f:

        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":

    print("🧠 Long-Horizon Cognitive Forecast Running")

    result = run_forecast()

    print(json.dumps(result, indent=2))