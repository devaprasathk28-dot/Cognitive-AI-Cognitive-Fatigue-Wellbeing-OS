import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "fatigue_state.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ======================================================
# SUGGESTION ENGINE
# ======================================================

def generate_suggestions():

    state = load_state()

    fatigue = state.get("fatigue_score", 0)
    burnout = state.get("burnout_probability", 0)
    category = state.get("last_category", "Unknown")

    suggestions = []

    # ---------------------------
    # FATIGUE RULES
    # ---------------------------

    if fatigue > 75:
        suggestions.append("⚠️ High fatigue detected. Take an immediate break.")

    elif fatigue > 50:
        suggestions.append("⏳ You're getting tired. A short 5–10 min break is recommended.")

    elif fatigue < 20:
        suggestions.append("✅ You're fresh. This is a great time for deep work.")

    # ---------------------------
    # BURNOUT RULES
    # ---------------------------

    if burnout > 0.7:
        suggestions.append("🔥 Burnout risk is high. Reduce workload and rest.")

    elif burnout > 0.5:
        suggestions.append("⚠️ Burnout building up. Try slowing down.")

    # ---------------------------
    # CONTEXT BASED
    # ---------------------------

    if category in ["Development", "Learning"]:
        suggestions.append("💡 Stay focused. Avoid switching tasks frequently.")

    if category == "Entertainment":
        suggestions.append("🎯 Try returning to productive work when ready.")

    if category == "Idle":
        suggestions.append("🚀 Good time to start a focused task.")

    # ---------------------------
    # DEFAULT
    # ---------------------------

    if not suggestions:
        suggestions.append("You're doing well. Keep going!")

    return suggestions