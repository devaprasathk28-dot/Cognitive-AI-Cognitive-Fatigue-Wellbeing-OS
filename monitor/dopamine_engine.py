# ======================================================
# STEP-2.11 — DOPAMINE SPIKE DECAY MODEL
# ======================================================

from datetime import datetime, timedelta

# In-memory dopamine tracker
dopamine_state = {
    "active_spike": False,
    "spike_time": None,
    "rebound_applied": False
}

def detect_dopamine_spike(prev_session, current_session):
    """
    Detect sudden switch from high-focus to entertainment
    """
    high_focus = ["Development", "Learning", "Productivity"]
    entertainment = ["Entertainment", "Browsing"]

    if (
        prev_session["category"] in high_focus and
        current_session["category"] in entertainment
    ):
        dopamine_state["active_spike"] = True
        dopamine_state["spike_time"] = datetime.now()
        dopamine_state["rebound_applied"] = False
        return True

    return False


def compute_dopamine_effect():
    """
    Returns fatigue adjustment value
    Negative = relief
    Positive = rebound fatigue
    """

    if not dopamine_state["active_spike"]:
        return 0

    now = datetime.now()
    spike_time = dopamine_state["spike_time"]

    if not spike_time:
        return 0

    elapsed = (now - spike_time).total_seconds()

    # --------------------------
    # Phase 1: Immediate Relief (0–15 min)
    # --------------------------
    if elapsed <= 900:
        return -5  # temporary relief

    # --------------------------
    # Phase 2: Rebound Fatigue (15–45 min)
    # --------------------------
    if 900 < elapsed <= 2700 and not dopamine_state["rebound_applied"]:
        dopamine_state["rebound_applied"] = True
        return +12  # rebound spike

    # --------------------------
    # Phase 3: Decay (after 45 min)
    # --------------------------
    if elapsed > 2700:
        dopamine_state["active_spike"] = False
        return 0

    return 0
