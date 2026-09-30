import json
import os
import math
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FATIGUE_STATE = os.path.join(BASE_DIR, "data", "fatigue_state.json")
BEHAVIOR_PROFILE = os.path.join(BASE_DIR, "data", "behavior_profile.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cognitive_state.json")


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


# -----------------------------
# BAYES HELPERS
# -----------------------------

def normalize(probs):
    total = sum(probs.values())
    if total == 0:
        return probs
    return {k: v / total for k, v in probs.items()}


# -----------------------------
# LIKELIHOOD FUNCTIONS
# -----------------------------

def likelihood_focus(fatigue, deep_ratio):
    return math.exp(-(fatigue / 50)) * (1 + deep_ratio)


def likelihood_fatigue(fatigue, burnout):
    return (fatigue / 100) * (1 + burnout)


def likelihood_distraction(momentum):
    return momentum / 15


# -----------------------------
# MAIN ESTIMATOR
# -----------------------------

def estimate_state():

    fatigue_data = load_json(FATIGUE_STATE)
    behavior_data = load_json(BEHAVIOR_PROFILE)

    fatigue = fatigue_data.get("fatigue_score", 0)
    burnout = fatigue_data.get("burnout_probability", 0)
    momentum = fatigue_data.get("fatigue_momentum", 0)

    deep_ratio = behavior_data.get("deep_work_ratio", 0)

    priors = {
        "focused": 0.33,
        "fatigued": 0.33,
        "distracted": 0.34
    }

    likelihoods = {
        "focused": likelihood_focus(fatigue, deep_ratio),
        "fatigued": likelihood_fatigue(fatigue, burnout),
        "distracted": likelihood_distraction(momentum)
    }

    posterior = {}

    for state in priors:
        posterior[state] = priors[state] * likelihoods[state]

    posterior = normalize(posterior)

    current_state = max(posterior, key=lambda k: posterior[k])

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "probabilities": posterior,
        "dominant_state": current_state
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":

    print("🧠 Cognitive State Estimator Running")

    state = estimate_state()

    print(json.dumps(state, indent=2))