import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATE_FILE = os.path.join(BASE_DIR, "data", "cognitive_state.json")
FATIGUE_FILE = os.path.join(BASE_DIR, "data", "fatigue_state.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "meta_cognition.json")


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def evaluate_prediction(predicted, observed):

    if predicted == observed:
        return 1
    return 0


def infer_actual_state(fatigue_score, app_category):

    if fatigue_score > 70:
        return "fatigued"

    if app_category == "Entertainment":
        return "distracted"

    return "focused"


def meta_evaluate():

    cognitive = load_json(STATE_FILE)
    fatigue = load_json(FATIGUE_FILE)

    predicted = cognitive.get("dominant_state", "unknown")
    fatigue_score = fatigue.get("fatigue_score", 0)

    # simple observation proxy
    app_category = fatigue.get("last_category", "Unknown")

    observed = infer_actual_state(
        fatigue_score,
        app_category
    )

    accuracy = evaluate_prediction(
        predicted,
        observed
    )

    report = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "predicted_state": predicted,

        "observed_state": observed,

        "prediction_accuracy": accuracy,

        "fatigue_score": fatigue_score
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":

    print("🧠 Meta-Cognition Engine Running")

    result = meta_evaluate()

    print(json.dumps(result, indent=2))