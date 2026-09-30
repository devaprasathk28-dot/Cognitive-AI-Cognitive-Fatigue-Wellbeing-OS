import time
import psutil

from monitor.notification_engine import show_notification


# ======================================================
# DISTRACTION APPS LIST
# ======================================================

DISTRACTION_APPS = [
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "youtube",
    "spotify",
    "discord",
]


# ======================================================
# CHECK ACTIVE APP
# ======================================================

def get_active_app():
    try:
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        process = psutil.Process(pid)
        return process.name().lower()

    except:
        return "unknown"


# ======================================================
# APPLY THROTTLING
# ======================================================

def apply_throttle(app_name):

    print(f"🚫 Blocking distraction: {app_name}")

    show_notification(
        "🎯 Focus Mode",
        f"{app_name} is distracting. Stay focused!"
    )

    # Soft delay instead of kill
    time.sleep(5)


# ======================================================
# MAIN PROTECTION LOGIC
# ======================================================

def enforce_focus_mode(fatigue, category):

    # Only enforce during productive states
    if category not in ["Development", "Learning"]:
        return

    # If fatigue is moderate (good focus zone)
    if fatigue < 70:

        app = get_active_app()

        if any(d in app for d in DISTRACTION_APPS):
            apply_throttle(app)
