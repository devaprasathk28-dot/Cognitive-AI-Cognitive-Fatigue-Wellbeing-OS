import time
import json
import os
from datetime import datetime

from monitor.fatigue_score_engine import CognitiveFatigueModel
from monitor.cognitive_state_estimator import estimate_state
from monitor.long_horizon_forecast import run_forecast
from monitor.meta_cognition_engine import meta_evaluate
from monitor.cognitive_adaptation_engine import run_adaptation
from monitor.rl_break_optimizer import decide_break_rl


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "fatigue_state.json")

INTERVAL = 60


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def get_current_category():
    state = load_state()
    return state.get("last_category", "Unknown")


def orchestrator_loop():

    print("🧠 Cognitive Orchestrator Started")

    model = CognitiveFatigueModel()

    while True:

        try:

            now = datetime.now()

            category = get_current_category()

            duration = 60
            hour = now.hour

            # -------------------------------
            # FATIGUE ENGINE
            # -------------------------------

            fatigue_state = model.update(
                category,
                duration,
                hour
            )

            fatigue_score = fatigue_state["fatigue_score"]
            burnout_probability = fatigue_state.get("burnout_probability", 0)
            fatigue_momentum = model.fatigue_momentum

            print(
                f"[{now.strftime('%H:%M:%S')}] "
                f"Fatigue={fatigue_score} "
                f"Level={fatigue_state['level']} "
                f"Burnout={burnout_probability}"
            )

            # -------------------------------
            # COGNITIVE STATE ESTIMATION
            # -------------------------------

            cognitive_state = estimate_state()

            # -------------------------------
            # LONG HORIZON FORECAST
            # -------------------------------

            forecast = run_forecast()

            # -------------------------------
            # RL BREAK DECISION
            # -------------------------------

            break_action = decide_break_rl(
                fatigue_score,
                burnout_probability,
                fatigue_momentum
            )

            print(f"Break decision → {break_action}")

            # -------------------------------
            # META COGNITION
            # -------------------------------

            meta_evaluate()

            # -------------------------------
            # ADAPTATION ENGINE
            # -------------------------------

            run_adaptation()

            time.sleep(INTERVAL)

        except Exception as e:

            print("Orchestrator error:", e)
            time.sleep(10)


if __name__ == "__main__":

    orchestrator_loop()