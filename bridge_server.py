import json
import time
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from storage.db import (
    get_connection, fatigue_to_focus_score,
    get_streak_count, get_today_deep_work_stats,
    log_notification, get_notifications, clear_notifications,
    log_focus_session, get_focus_stats_today,
    save_chat_message, get_chat_history
)
from monitor.settings_manager import load_settings, save_settings
from monitor.fatigue_score_engine import CognitiveFatigueModel
from monitor.live_usage_tracker import track_usage
from monitor.smart_app_classifier import classify_app
from monitor.ai_companion_engine import ask_ai

PORT = 8765

# Shared Global State
LATEST_STATE = {
    "fatigue": 0.0,
    "focus_score": 100,
    "burnout": 0.0,
    "app": "Initializing",
    "category": "General",
    "window_title": "",
    "break_message": "Cognitive engine active.",
    "streak": 1,
    "timestamp": datetime.now().isoformat()
}

_MODEL = CognitiveFatigueModel()
_STOP_EVENT = threading.Event()


def background_tracking_loop():
    """Continuously tracks foreground window usage and updates fatigue model."""
    global LATEST_STATE
    try:
        for session in track_usage(interval=4, yield_live=True):
            if _STOP_EVENT.is_set():
                break

            app = session.get("app", "Desktop")
            title = session.get("title", "")
            cat = session.get("category") or classify_app(app, title)
            dur = int(session.get("duration", 4))

            hour = datetime.now().hour
            state = _MODEL.update(cat, dur, hour)

            fatigue_val = _MODEL.fatigue_score
            focus_val = fatigue_to_focus_score(fatigue_val)

            LATEST_STATE = {
                "fatigue": round(fatigue_val, 2),
                "focus_score": focus_val,
                "burnout": round(_MODEL.burnout_probability, 3),
                "app": app,
                "category": cat,
                "window_title": title,
                "break_message": getattr(_MODEL, "break_decision", {}).get("reason", "Steady concentration.") if isinstance(getattr(_MODEL, "break_decision", {}), dict) else "Steady concentration.",
                "streak": get_streak_count(),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"[Tracker Loop Error] {e}")


class APIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        if path == "/api/status":
            today_stats = get_today_deep_work_stats()
            settings = load_settings()
            response = {
                **LATEST_STATE,
                "deep_work_sec": today_stats.get("deep_work_sec", 0),
                "distraction_count": today_stats.get("distraction_count", 0),
                "focus_mode": settings.get("focus_mode", False),
                "goal_focus_hours": settings.get("goal_focus_hours", 5),
                "goal_distraction_mins": settings.get("goal_distraction_mins", 60),
                "goal_screen_time_hours": settings.get("goal_screen_time_hours", 8)
            }
            self._json_response(response)

        elif path == "/api/notifications":
            notifs = get_notifications(limit=50)
            self._json_response({"notifications": notifs})

        elif path == "/api/chat/history":
            history = get_chat_history(limit=30)
            self._json_response({"history": history})

        elif path == "/api/insights":
            from ui.pages.insights_page import InsightsPage
            # Compute real analytics from db
            try:
                page = InsightsPage()
                insights = page._analyze_database()
            except Exception:
                insights = []
            self._json_response({"insights": insights})

        elif path == "/api/analytics":
            query = parse_qs(url.query)
            days = int(query.get("days", ["7"])[0])
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                SELECT category, SUM(duration_sec)
                FROM sessions
                WHERE timestamp >= datetime('now', ?, 'localtime')
                GROUP BY category
                ORDER BY SUM(duration_sec) DESC
            """, (f"-{days} days",))
            categories = [{"category": r[0], "duration_sec": r[1]} for r in c.fetchall()]

            c.execute("""
                SELECT app_name, SUM(duration_sec), AVG(fatigue_score)
                FROM sessions
                WHERE timestamp >= datetime('now', ?, 'localtime')
                GROUP BY app_name
                ORDER BY SUM(duration_sec) DESC
                LIMIT 6
            """, (f"-{days} days",))
            apps = [{
                "app": r[0],
                "duration_sec": r[1],
                "focus_score": fatigue_to_focus_score(r[2])
            } for r in c.fetchall()]

            c.execute("""
                SELECT date(timestamp), SUM(duration_sec)
                FROM sessions
                WHERE timestamp >= datetime('now', ?, 'localtime')
                GROUP BY date(timestamp)
                ORDER BY date(timestamp) ASC
            """, (f"-{days} days",))
            daily = [{"date": r[0], "minutes": (r[1] or 0) // 60} for r in c.fetchall()]

            conn.close()
            self._json_response({
                "days": days,
                "categories": categories,
                "apps": apps,
                "daily": daily
            })

        elif path == "/api/settings":
            settings = load_settings()
            self._json_response(settings)

        else:
            self._json_response({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        if path == "/api/focus/toggle":
            settings = load_settings()
            new_val = not settings.get("focus_mode", False)
            settings["focus_mode"] = new_val
            save_settings(settings)
            status_str = "activated" if new_val else "deactivated"
            log_notification("Alert" if new_val else "Info", f"Focus Mode {status_str}")
            self._json_response({"focus_mode": new_val})

        elif path == "/api/focus/log":
            duration_sec = body.get("duration_sec", 1500)
            log_focus_session(duration_sec, "completed")
            mins = duration_sec // 60
            log_notification("Focus", f"Completed a {mins}-minute focus sprint!")
            self._json_response({"success": True, "duration_sec": duration_sec})

        elif path == "/api/break/complete":
            log_notification("Break", "Completed a restorative 4-7-8 mindful breathing break.")
            self._json_response({"success": True})

        elif path == "/api/chat":
            prompt = body.get("prompt", "")
            if not prompt:
                self._json_response({"error": "Prompt required"}, status=400)
                return
            reply = ask_ai(prompt)
            save_chat_message(prompt, reply)
            self._json_response({"reply": reply})

        elif path == "/api/notifications/clear":
            clear_notifications()
            self._json_response({"success": True})

        elif path == "/api/settings":
            settings = load_settings()
            settings.update(body)
            save_settings(settings)
            self._json_response({"success": True, "settings": settings})

        elif path == "/api/report/generate":
            try:
                from analytics.report_generator import generate_executive_html_report
                report_path = generate_executive_html_report()
                log_notification("Report", f"Executive report generated: {os.path.basename(report_path)}")
                self._json_response({"success": True, "report_path": report_path, "filename": os.path.basename(report_path)})
            except Exception as e:
                self._json_response({"error": str(e)}, status=500)

        else:
            self._json_response({"error": "Endpoint not found"}, status=404)

    def log_message(self, format, *args):
        # Silence HTTP server logs to keep terminal clean
        return


def run_server():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    server = HTTPServer(("127.0.0.1", PORT), APIHandler)
    print(f"[Cognitive AI Bridge Server] Running on http://127.0.0.1:{PORT}")
    
    # Start tracking loop in daemon thread
    t = threading.Thread(target=background_tracking_loop, daemon=True)
    t.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _STOP_EVENT.set()
        server.server_close()
        print("Bridge Server stopped.")


if __name__ == "__main__":
    run_server()
