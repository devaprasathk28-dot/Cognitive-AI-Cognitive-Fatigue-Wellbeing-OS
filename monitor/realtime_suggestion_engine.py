import time
from datetime import datetime
import os
import csv


from monitor.live_usage_tracker import track_usage
from monitor.smart_suggestion_engine import generate_suggestions
from monitor.fatigue_score_engine import CognitiveFatigueModel
from monitor.notification_engine import show_notification
from monitor.break_enforcement_engine import start_break
from monitor.smart_break_engine import SmartBreakManager
from monitor.focus_protection_engine import enforce_focus_mode
from monitor.focus_session_engine import FocusSessionManager
from monitor.feature_detection import detect_features
from monitor.smart_app_classifier import classify_app
from monitor.pattern_loader import load_patterns
from monitor.personalization_engine import get_personalized_thresholds
from monitor.control_engine import is_stopped, is_paused

detect_features()
patterns = load_patterns()

last_pattern_update = 0
# ======================================================
# CONFIG
# ======================================================

CHECK_INTERVAL = 10  # seconds
SESSION_FILE = "data/usage_sessions.csv"


# ======================================================
# READ LATEST SESSION (REAL INPUT)
# ======================================================

def get_latest_session():

    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(SESSION_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

            if not rows:
                return None

            last = rows[-1]

            return {
                "category": last.get("category", "Unknown"),
                "duration_sec": int(float(last.get("duration_sec", 60)))
            }

    except Exception as e:
        print("Session Read Error:", e)
        return None


# ======================================================
# REAL-TIME ENGINE
# ======================================================

def run_realtime_suggestions():

    print("🧠 Real-Time Suggestion Engine Started\n")

    global last_pattern_update
    model = CognitiveFatigueModel()
    break_manager = SmartBreakManager()
    focus_manager = FocusSessionManager()
    last_suggestions = []

    for session in track_usage():

        if is_stopped():
            print("🛑 System stopped by user")
            break

        if is_paused():
            print("⏸ System paused...")
            time.sleep(5)
            continue

        try:
            now = datetime.now().strftime("%H:%M:%S")

            app_name = session["app"]
            duration = session["duration"]

            # -----------------------------
            # APP → CATEGORY MAPPING
            # -----------------------------
            app = app_name.lower()

            app_name = session["app"]
            title = session["title"]
            duration = session["duration"]

            category = classify_app(app_name, title)

            hour = datetime.now().hour

            print(f"[{now}] 📊 App={app_name} Category={category} Duration={duration}")

            # -----------------------------
            # FATIGUE UPDATE
            # -----------------------------
            state = model.update(category, duration, hour)

            fatigue = state.get("fatigue_score", 0)
            burnout = state.get("burnout_probability", 0)
            momentum = state.get("fatigue_momentum", 0)

            # -----------------------------
            # LOAD BEHAVIOR PATTERNS
            # -----------------------------
            patterns = load_patterns()

            # -----------------------------
            # AUTO-LEARNING (every 10 min)
            # -----------------------------
            if time.time() - last_pattern_update > 600:
                from monitor.behavior_pattern_engine import run_behavior_analysis
                print("🧠 Updating behavior patterns...")
                run_behavior_analysis()
                
                # -----------------------------
                # UPDATE PROFILE FROM BEHAVIOR
                # -----------------------------
                from monitor.profile_updater import update_profile_from_behavior
                updated_patterns = load_patterns()
                update_profile_from_behavior(updated_patterns)
                print("✅ User profile updated from behavior")
                
                last_pattern_update = time.time()
            
            # -----------------------------
            # READ BEHAVIOR VALUES
            # -----------------------------
            productivity_ratio = patterns.get("productivity_ratio", 0.5)
            peak_hour = patterns.get("peak_productivity_hour", None)
            distraction_ratio = patterns.get("distraction_ratio", 0)
            # -----------------------------
            # FOCUS PROTECTION
            # -----------------------------
            enforce_focus_mode(fatigue=fatigue, category=category)

            # -----------------------------
            # FOCUS SESSION
            # -----------------------------
            status = focus_manager.update()

            if not focus_manager.active:
                focus_duration = focus_manager.decide_focus_duration(fatigue, momentum)
                focus_manager.start_focus(focus_duration)

            elif status == "focus_complete":
                break_duration = focus_manager.decide_break_duration(fatigue)
                focus_manager.start_break(break_duration)

            elif status == "break_complete":
                print("Ready for next focus session")
            # -----------------------------
            # 🧠 ADAPTIVE AI DECISIONS
            # -----------------------------

            # 🔥 Peak productivity boost
            if peak_hour == hour and fatigue < 50 and not focus_manager.active:
                print("🔥 Peak productivity time → boosting focus")
                focus_manager.start_focus(45)


            # ⚠️ Low productivity → early break
            if productivity_ratio < 0.4 and fatigue > 40:
                print("⚠️ Low productivity pattern → early break")
                start_break(duration_minutes=5)


            # 🚫 High distraction users → stricter control
            if distraction_ratio > 0.3:
                enforce_focus_mode(fatigue, category)
            # -----------------------------
            # SMART BREAK
            # -----------------------------
            decision = break_manager.evaluate(fatigue, burnout, momentum)

            if decision.get("take_break"):
                duration = decision["duration"]
                print(f"\n🧠 Smart Break Triggered → {duration} min")
                start_break(duration_minutes=duration)

            # -----------------------------
            # SUGGESTIONS
            # -----------------------------
            suggestions = generate_suggestions()

            if suggestions != last_suggestions:

                print(f"\n[{now}] 🔔 Suggestions:\n")

                for s in suggestions:
                    print("-", s)
                    show_notification("🧠 Cognitive AI", s)

                last_suggestions = suggestions

        except Exception as e:
            print("Engine Error:", e)
            time.sleep(5)


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run_realtime_suggestions()