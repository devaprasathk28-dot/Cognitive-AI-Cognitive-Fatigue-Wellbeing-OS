def get_personalized_thresholds(patterns):

    productivity = patterns.get("productivity_ratio", 0.5)
    distraction = patterns.get("distraction_ratio", 0.2)

    thresholds = {}

    # -----------------------------
    # FATIGUE BREAK THRESHOLD
    # -----------------------------
    if productivity > 0.7:
        thresholds["fatigue_break"] = 70  # high performers tolerate more

    elif productivity < 0.4:
        thresholds["fatigue_break"] = 45  # early break needed

    else:
        thresholds["fatigue_break"] = 55

    # -----------------------------
    # FOCUS DURATION
    # -----------------------------
    if productivity > 0.7:
        thresholds["focus_duration"] = 45

    elif productivity < 0.4:
        thresholds["focus_duration"] = 20

    else:
        thresholds["focus_duration"] = 30

    # -----------------------------
    # STRICTNESS (DISTRACTION CONTROL)
    # -----------------------------
    if distraction > 0.4:
        thresholds["strict_mode"] = True
    else:
        thresholds["strict_mode"] = False

    return thresholds