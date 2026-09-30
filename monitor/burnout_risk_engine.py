# ======================================================
# BURNOUT RISK PROBABILITY ENGINE
# STEP-2.14
# ======================================================

import math


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def compute_burnout_risk(
    fatigue_score,
    fatigue_momentum,
    baseline_offset,
    switch_count,
    recovery_value
):
    """
    Returns burnout probability (0–1)
    """

    # -----------------------------
    # Normalize components
    # -----------------------------

    fatigue_factor = fatigue_score / 100              # 0–1
    momentum_factor = fatigue_momentum / 15          # 0–1
    baseline_factor = max(0, baseline_offset) / 20   # 0–1
    switch_factor = min(switch_count / 10, 1)
    recovery_penalty = max(0, 1 - recovery_value)

    # -----------------------------
    # Weighted Burnout Formula
    # -----------------------------

    raw_score = (
        2.5 * fatigue_factor +
        1.8 * momentum_factor +
        1.5 * baseline_factor +
        1.2 * switch_factor +
        1.0 * recovery_penalty
    )

    probability = sigmoid(raw_score - 3)

    return round(probability, 3)


def interpret_burnout_risk(prob):

    if prob < 0.25:
        return "Low Risk"

    elif prob < 0.5:
        return "Moderate Risk"

    elif prob < 0.75:
        return "High Risk"

    else:
        return "Critical Risk"
