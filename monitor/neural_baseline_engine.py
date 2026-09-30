# ======================================================
# STEP-2.12 — PERSONALIZED NEURAL BASELINE ENGINE
# ======================================================

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_FILE = os.path.join(BASE_DIR, "data", "neural_baseline.json")


DEFAULT_BASELINE = {
    "baseline_load_factor": 1.0,
    "baseline_recovery_factor": 1.0,
    "dopamine_sensitivity": 1.0,
    "fatigue_adaptation_rate": 0.02,
    "sessions_observed": 0,
    "last_updated": None
}


# --------------------------------------------------
# LOAD BASELINE
# --------------------------------------------------

def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        save_baseline(DEFAULT_BASELINE)
        return DEFAULT_BASELINE.copy()

    with open(BASELINE_FILE, "r") as f:
        return json.load(f)


# --------------------------------------------------
# SAVE BASELINE
# --------------------------------------------------

def save_baseline(data):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f, indent=4)


# --------------------------------------------------
# UPDATE BASELINE (ADAPTIVE LEARNING)
# --------------------------------------------------

def update_baseline(fatigue_score, recovery_applied):

    baseline = load_baseline()

    adaptation = baseline["fatigue_adaptation_rate"]

    # If fatigue rising too quickly → reduce load factor
    if fatigue_score > 70:
        baseline["baseline_load_factor"] -= adaptation

    # If user consistently stays fresh → increase load tolerance
    elif fatigue_score < 25:
        baseline["baseline_load_factor"] += adaptation

    # If recovery works strongly → increase recovery efficiency
    if recovery_applied > 2.0:
        baseline["baseline_recovery_factor"] += adaptation

    # Clamp values
    baseline["baseline_load_factor"] = max(0.6, min(1.4, baseline["baseline_load_factor"]))
    baseline["baseline_recovery_factor"] = max(0.6, min(1.4, baseline["baseline_recovery_factor"]))

    baseline["sessions_observed"] += 1
    baseline["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_baseline(baseline)

    return baseline
