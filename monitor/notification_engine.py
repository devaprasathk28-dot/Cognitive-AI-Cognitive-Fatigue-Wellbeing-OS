import time
from monitor.settings_manager import load_settings

try:
    from winotify import Notification
    _WINOTIFY_AVAILABLE = True
except ImportError:
    Notification = None
    _WINOTIFY_AVAILABLE = False

LAST_NOTIFICATION: dict[str, float] = {
    "critical": 0.0,
    "high": 0.0,
    "medium": 0.0,
    "low": 0.0
}

COOLDOWN = {
    "critical": 30,
    "high": 60,
    "medium": 180,
    "low": 600
}


def _show(title: str, message: str):
    if not _WINOTIFY_AVAILABLE:
        print(f"[Notification] {title}: {message}")
        return
    if Notification is None:
        print(f"[Notification] {title}: {message}")
        return
    try:
        Notification(app_id="Cognitive AI", title=title, msg=message, duration="short").show()
    except Exception as e:
        print("Notification Error:", e)


def should_notify(priority: str) -> bool:
    now = time.time()
    if now - LAST_NOTIFICATION[priority] < COOLDOWN[priority]:
        return False
    LAST_NOTIFICATION[priority] = now
    return True


def build_message(decision: dict, priority: str) -> str:
    reason = decision.get("reason", "")
    duration = decision.get("recommended_duration_minutes", 0)

    if priority == "critical":
        return f"⚠️ Immediate break needed ({duration} min)\n{reason}"
    elif priority == "high":
        return f"⚡ High fatigue detected\nTake a {duration} min break"
    elif priority == "medium":
        return f"🧠 Consider a short break\n{reason}"
    elif priority == "low":
        return "🔥 You're doing well. Stay focused!"
    return ""


def notify_break(decision: dict):
    if not decision:
        return

    priority = get_priority(decision)

    if priority == "low":
        return

    settings = load_settings()
    if settings.get("focus_mode") and priority != "critical":
        return

    if not should_notify(priority):
        return

    message = build_message(decision, priority)
    if not message:
        return

    if not _WINOTIFY_AVAILABLE or Notification is None:
        print(f"[Notification] 🧠 Cognitive AI ({priority.upper()}): {message}")
        return

    try:
        Notification(
            app_id="Cognitive AI",
            title=f"🧠 Cognitive AI ({priority.upper()})",
            msg=message,
            duration="short"
        ).show()
    except Exception as e:
        print("Notification Error:", e)


def show_notification(title: str, message: str):
    _show(title, message)


def get_priority(decision: dict) -> str:
    fatigue = decision.get("fatigue_score", 0)
    urgency = decision.get("urgency_level", "Low")

    if urgency == "Critical" or fatigue > 85:
        return "critical"
    elif urgency == "High" or fatigue > 65:
        return "high"
    elif urgency == "Medium":
        return "medium"
    return "low"


def compute_total_risk(decision, trend_risk, future_risk, circadian_risk, profile):
    fatigue = decision.get("fatigue_score", 0)
    threshold = profile["profile_thresholds"]["fatigue_break"]
    total = (
        0.4 * fatigue +
        0.2 * trend_risk +
        0.2 * future_risk +
        0.2 * circadian_risk
    )
    normalized = (total / threshold) * 100
    return min(int(normalized), 100)


def predictive_notification(decision):
    from monitor.trend_engine import analyze_trend

    if decision.get("break_required"):
        return  # skip predictive if already critical

    trend = analyze_trend()
    risk = trend.get("risk", 0)

    if risk < 50 or not should_notify("medium"):
        return

    if risk >= 80:
        msg = "⚠️ Fatigue rising rapidly. Take a break soon!"
    elif risk >= 60:
        msg = "⚡ You're getting tired. Consider a short break."
    else:
        msg = "🧠 Fatigue slowly increasing. Stay mindful."

    _show("Predictive Alert", msg)


def predictive_alert(decision, profile):
    from monitor.trend_engine import load_trend, analyze_trend, predict_future_fatigue
    from monitor.circadian_engine import get_circadian_risk

    history = load_trend()
    trend = analyze_trend()
    future = predict_future_fatigue(history)
    circadian = get_circadian_risk()

    risk = compute_total_risk(
        decision,
        trend["risk"],
        future["risk"],
        circadian,
        profile
    )

    if risk > 85:
        msg = "🚨 High burnout risk incoming. Stop and take a break."
    elif risk > 65:
        msg = "⚠️ You're heading toward fatigue. Slow down."
    elif risk > 50:
        msg = "🧠 Early fatigue signs detected."
    else:
        return

    if not should_notify("medium"):
        return

    show_notification("Predictive AI", msg)
