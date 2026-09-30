import time
import random
from datetime import datetime

try:
    import win32gui
    import win32process
    import psutil
    _WIN32_AVAILABLE = True
except ImportError:
    win32gui = win32process = psutil = None
    _WIN32_AVAILABLE = False


def get_active_app():
    if not _WIN32_AVAILABLE:
        return "Unknown", ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name(), window_title
    except Exception:
        return "Unknown", ""


def _calc_focus_score(duration, category):
    base = min(100, int(duration / 6))
    penalty = {"Entertainment": 30, "Browsing": 15}.get(category, 0)
    return max(0, base - penalty)


def track_usage(interval=5, yield_live=False):
    from monitor.smart_app_classifier import classify_app

    last_app = None
    last_title = None
    start_time = time.time()
    session_count = 0

    while True:
        app_name, title = get_active_app()

        if app_name != last_app or title != last_title:
            if last_app is not None:
                duration = int(time.time() - start_time)
                session_count += 1
                category = classify_app(last_app, last_title)
                yield {
                    "app": last_app,
                    "title": last_title,
                    "duration": duration,
                    "start_time": datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "category": category,
                    "session_count": session_count,
                    "notification_count": random.randint(0, 5),
                    "focus_score": _calc_focus_score(duration, category),
                }

            last_app = app_name
            last_title = title
            start_time = time.time()
        else:
            if yield_live and last_app is not None:
                yield {
                    "live_update": True,
                    "app": last_app,
                    "title": last_title,
                    "category": classify_app(last_app, last_title)
                }

        time.sleep(interval)