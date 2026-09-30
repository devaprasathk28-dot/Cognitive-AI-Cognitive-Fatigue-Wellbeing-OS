import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FATIGUE_STATE = os.path.join(BASE_DIR, "data", "fatigue_state.json")
BEHAVIOR_PROFILE = os.path.join(BASE_DIR, "data", "behavior_profile.json")

OUTPUT_FILE = os.path.join(BASE_DIR, "data", "digital_twin_state.json")


# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------

def load_json(path):

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


# ------------------------------------------------
# STATE PREDICTION
# ------------------------------------------------

def predict_state(fatigue, burnout, deep_ratio):

    if fatigue > 70:
        return "Critical Fatigue"

    if fatigue > 40:
        return "High Fatigue"

    if deep_ratio > 0.4 and fatigue < 40:
        return "Focused"

    return "Normal"


# ------------------------------------------------
# FUTURE FATIGUE ESTIMATION
# ------------------------------------------------

def predict_future(fatigue, burnout):

    fatigue_30 = fatigue + (burnout * 20)
    fatigue_4h = fatigue + (burnout * 35)

    fatigue_30 = min(100, fatigue_30)
    fatigue_4h = min(100, fatigue_4h)

    return fatigue_30, fatigue_4h


# ------------------------------------------------
# ACTION RECOMMENDER
# ------------------------------------------------

def recommend_action(fatigue, burnout):

    if fatigue > 80 or burnout > 0.85:
        return "Immediate break required"

    if fatigue > 60:
        return "Break within 10 minutes"

    if burnout > 0.6:
        return "Schedule longer rest"

    return "Continue work"


# ------------------------------------------------
# DIGITAL TWIN ENGINE
# ------------------------------------------------

def build_digital_twin():

    fatigue_data = load_json(FATIGUE_STATE)
    behavior_data = load_json(BEHAVIOR_PROFILE)

    fatigue = fatigue_data.get("fatigue_score", 0)
    burnout = fatigue_data.get("burnout_probability", 0)

    deep_ratio = behavior_data.get("deep_work_ratio", 0)

    current_state = predict_state(
        fatigue,
        burnout,
        deep_ratio
    )

    f30, f4h = predict_future(
        fatigue,
        burnout
    )

    action = recommend_action(
        fatigue,
        burnout
    )

    twin = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "current_state": current_state,

        "fatigue_score": fatigue,

        "burnout_probability": burnout,

        "predicted_30min_fatigue": round(f30, 2),

        "predicted_4h_fatigue": round(f4h, 2),

        "recommended_action": action
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(twin, f, indent=2)

    return twin


# ------------------------------------------------
# RUN
# ------------------------------------------------

if __name__ == "__main__":

    print("🧠 Cognitive Digital Twin Running")

    twin = build_digital_twin()

    print(json.dumps(twin, indent=2))