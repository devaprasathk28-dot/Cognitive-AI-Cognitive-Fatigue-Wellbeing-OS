# ======================================================
# STEP-2.10 — COGNITIVE LOAD SLOPE ENGINE
# Non-linear fatigue acceleration
# ======================================================

def compute_load_penalty(session):
    """
    Calculates fatigue penalty based on cognitive intensity
    and session duration using non-linear slope.
    """

    duration_minutes = int(session["duration_sec"]) / 60

    category = session.get("category", "")
    intent = session.get("focus_type", "")

    # ----------------------------
    # Base intensity weights
    # ----------------------------

    intensity_map = {
        "Development": 1.5,
        "Learning": 1.3,
        "Productivity": 1.2,
        "Communication": 0.9,
        "Browsing": 0.7,
        "Entertainment": 0.5,
        "Utilities": 0.4,
    }

    base_intensity = intensity_map.get(category, 0.6)

    # Bonus intensity for Deep Work
    if intent == "Deep Work":
        base_intensity += 0.5

    # ----------------------------
    # Non-linear growth
    # ----------------------------

    duration_factor = duration_minutes / 30  # normalized 30 min blocks

    slope_penalty = base_intensity * (duration_factor ** 2)

    return round(slope_penalty, 2)
