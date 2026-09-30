# ======================================================
# BACKGROUND ENGINE RUNNER
# ======================================================

import time
from datetime import datetime

from monitor.fatigue_score_engine import CognitiveFatigueModel

model = CognitiveFatigueModel()

print("🧠 Cognitive Engine Running")

while True:
    try:
        category = "Development"
        duration = 60
        hour = datetime.now().hour

        state = model.update(category, duration, hour)

        print(
            f"[{state['timestamp']}] "
            f"Fatigue={state['fatigue_score']} "
            f"Level={state['level']} "
            f"Burnout={state['burnout_probability']} "
            f"BurnoutLevel={state['burnout_level']}"
        )

        time.sleep(60)

    except Exception as e:
        print("Engine Error:", e)
        time.sleep(10)