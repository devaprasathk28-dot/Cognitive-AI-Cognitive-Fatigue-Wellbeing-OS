# ======================================================
# STEP-2.9 — CIRCADIAN RHYTHM ENGINE
# Biological Fatigue Weighting
# ======================================================

from datetime import datetime

def get_circadian_multiplier(current_time=None):
    """
    Returns fatigue multiplier based on biological clock.
    """

    if current_time is None:
        current_time = datetime.now()

    hour = current_time.hour

    # Morning Rise
    if 5 <= hour < 9:
        return 0.9

    # Peak Cognitive Hours
    elif 9 <= hour < 13:
        return 0.8

    # Afternoon Dip
    elif 13 <= hour < 16:
        return 1.1

    # Evening Stable
    elif 16 <= hour < 21:
        return 1.0

    # Late Evening Decline
    elif 21 <= hour < 24:
        return 1.3

    # Biological Low (Midnight–4AM)
    else:
        return 1.6


def get_circadian_risk():
    hour = datetime.now().hour
    if 2 <= hour <= 6:
        return 80
    elif 13 <= hour <= 15:
        return 50
    elif 22 <= hour <= 24:
        return 70
    return 20
