# ======================================================
# STEP-2.16 → AUTO-BREAK AI DECISION ENGINE
# ======================================================

from datetime import datetime
from monitor.feature_flags import FEATURES

if FEATURES["lstm_enabled"]:
    from monitor.burnout_lstm_model import forecast
else:
    forecast = None
from monitor.circadian_engine import get_circadian_multiplier


def classify_urgency(fatigue_score, burnout_prob):
    if fatigue_score > 80 or burnout_prob > 75:
        return "Critical"
    elif fatigue_score > 60 or burnout_prob > 60:
        return "High"
    elif fatigue_score > 40:
        return "Medium"
    else:
        return "Low"


def decide_break(
    fatigue_score,
    fatigue_momentum,
    burnout_probability,
    last_category,
    continuous_deep_work_minutes,
):
    """
    Main Break Decision Engine
    """

    now = datetime.now()
    hour = now.hour
    circadian_factor = get_circadian_multiplier()

    break_required = False
    break_type = "None"
    duration = 0
    reason = []
    confidence = 0.0
        # ==================================================
    # 🔮 OPTIONAL LSTM PREDICTION (ADVANCED AI)
    # ==================================================

    predicted_burnout = None

    if forecast:
        try:
            predictions = forecast()
            predicted_burnout = predictions[0] if predictions else None

            if predicted_burnout and predicted_burnout > 80:
                reason.append("LSTM predicts high future burnout")
                confidence += 0.2

        except Exception:
            predicted_burnout = None
    # ==================================================
    # 1️⃣ HARD THRESHOLD (CRITICAL STATE)
    # ==================================================

    if fatigue_score >= 85 or burnout_probability >= 80:
        break_required = True
        break_type = "Deep Recovery"
        duration = 30
        reason.append("Critical fatigue or burnout risk")
        confidence += 0.9

    # ==================================================
    # 2️⃣ MOMENTUM OVERLOAD
    # ==================================================

    elif fatigue_momentum >= 10:
        break_required = True
        break_type = "Short Break"
        duration = 15
        reason.append("High fatigue momentum detected")
        confidence += 0.7

    # ==================================================
    # 3️⃣ PROLONGED DEEP WORK
    # ==================================================

    elif (
        last_category in ["Development", "Learning", "Design"]
        and continuous_deep_work_minutes >= 90
    ):
        break_required = True
        break_type = "Micro Break"
        duration = 7
        reason.append("Long continuous deep work session")
        confidence += 0.6

    # ==================================================
    # 4️⃣ LATE NIGHT COGNITIVE DECLINE
    # ==================================================

    elif hour >= 23 and fatigue_score > 40:
        break_required = True
        break_type = "Sleep Recommendation"
        duration = 60
        reason.append("Late-night cognitive strain")
        confidence += 0.75

    # ==================================================
    # 5️⃣ CIRCADIAN LOW WINDOW
    # ==================================================

    elif circadian_factor > 1.2 and fatigue_score > 35:
        break_required = True
        break_type = "Micro Break"
        duration = 5
        reason.append("Circadian dip detected")
        confidence += 0.5

    # ==================================================
    # 6️⃣ MODERATE FATIGUE PREVENTION
    # ==================================================

    elif fatigue_score >= 50:
        break_required = True
        break_type = "Short Break"
        duration = 10
        reason.append("Moderate fatigue accumulation")
        confidence += 0.5

    # ==================================================
    # URGENCY CLASSIFICATION
    # ==================================================

    urgency = classify_urgency(fatigue_score, burnout_probability)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "break_required": break_required,
        "break_type": break_type,
        "recommended_duration_minutes": duration,
        "urgency_level": urgency,
        "reason": ", ".join(reason) if reason else "Stable cognitive state",
        "confidence": round(min(confidence, 1.0), 2),
    }
