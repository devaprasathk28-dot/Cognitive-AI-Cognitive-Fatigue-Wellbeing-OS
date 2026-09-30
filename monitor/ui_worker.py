import time
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from monitor.live_usage_tracker import track_usage
from monitor.smart_app_classifier import classify_app
from monitor.fatigue_score_engine import CognitiveFatigueModel

LATEST_STATE = {}


class EngineWorker(QObject):
    # Signals to UI
    data_signal = pyqtSignal(dict)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = True
        self.model = CognitiveFatigueModel()

    @pyqtSlot()
    def run(self):
        self.status.emit("Engine started")
        # print("[WORKER] Engine loop started")
        try:
            # Fallback timer for simulated data if no real tracking
            fallback_timer = time.time()
            
            for session in track_usage(interval=5, yield_live=True):
                if not self._running:
                    break
                fallback_timer = time.time()  # reset on real data

                if session.get("live_update"):
                    app = session.get("app", "Unknown")
                    category = session.get("category", "Unknown")
                    payload = {
                        "fatigue": round(self.model.fatigue_score, 2),
                        "burnout": round(self.model.burnout_probability, 3),
                        "app": app,
                        "category": category,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "break_message": getattr(self.model, "break_decision", {}).get("reason", "No break needed") if isinstance(getattr(self.model, "break_decision", {}), dict) else "No break needed"
                    }
                    self.data_signal.emit(payload)
                    continue

                app = session.get("app", "Unknown")
                title = session.get("title", "")
                duration = int(session.get("duration", 5))

                category = classify_app(app, title)
                hour = datetime.now().hour

                state = self.model.update(category, duration, hour)

                global LATEST_STATE
                LATEST_STATE = {
                    "fatigue": state.get("fatigue_score", 0),
                    "burnout": state.get("burnout_probability", 0),
                    "category": category,
                    "hour": hour,
                    "app": app
                }

                break_decision = state.get("break_decision")
                break_message = ""
                if break_decision and isinstance(break_decision, dict):
                    if break_decision.get("break_required"):
                        dur = break_decision.get("recommended_duration_minutes", 5)
                        reason = break_decision.get("reason", "You've been working continuously")
                        break_message = f"Take a {dur}-min break: {reason}"
                    else:
                        break_message = "No break needed"

                try:
                    from storage.db import log_session
                    fatigue_score = state.get("fatigue_score", 0)
                    burnout_score = state.get("burnout_probability", 0)
                    log_session(app, title, category, duration, fatigue_score, burnout_score)
                except Exception as e:
                    print("Log DB error:", e)

                payload = {
                    "fatigue": round(state.get("fatigue_score", 0), 2),
                    "burnout": round(state.get("burnout_probability", 0), 3),
                    "app": app,
                    "category": category,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "break_message": break_message,
                }
                # print(f"[WORKER] Emitting data: fatigue={payload['fatigue']}, app={app}")

                print("ENGINE EMIT:", payload)
                self.data_signal.emit(payload)

            # Fallback: emit simulated data every 10s if no real data
            while self._running:
                if time.time() - fallback_timer > 10:
                    sim_fatigue = 35 + (time.time() % 60)  # oscillate 35-95
                    sim_payload = {
                        "fatigue": round(sim_fatigue, 1),
                        "burnout": round(0.25 + 0.01 * sim_fatigue, 2),
                        "app": "chrome.exe",
                        "category": "Browsing" if sim_fatigue > 50 else "Productivity",
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "break_message": "No break needed",
                    }
                    self.data_signal.emit(sim_payload)
                    fallback_timer = time.time()
                time.sleep(2)

        except Exception as e:
            self.status.emit(f"Worker error: {e}")

        self.status.emit("Engine stopped")
        self.finished.emit()

    def stop(self):
        self._running = False