# ======================================================
# REAL COGNITIVE FATIGUE ENGINE (LIVE + PERSISTENT)
# FULLY CORRECTED VERSION
# ======================================================

import json
import os
from datetime import datetime

from monitor.paths import get_data_path
from monitor.recovery_engine import compute_recovery_score, load_sessions
from monitor.circadian_engine import get_circadian_multiplier
from monitor.cognitive_load_engine import compute_load_penalty
from monitor.dopamine_engine import detect_dopamine_spike, compute_dopamine_effect
from monitor.neural_baseline_engine import load_baseline, update_baseline
from monitor.burnout_risk_engine import compute_burnout_risk, interpret_burnout_risk
from monitor.break_decision_engine import decide_break
from monitor.notification_engine import notify_break, predictive_notification
from monitor.trend_engine import update_trend
from monitor.break_timer_engine import start_break_timer
from monitor.app_blocker_engine import enforce_blocking
from monitor.app_throttle_engine import enforce_throttle
from monitor.focus_lock_engine import activate_focus_lock, release_focus_lock
from monitor.focus_cycle_engine import start_focus_cycle
from monitor.rl_break_optimizer import decide_break_rl
from monitor.feature_flags import FEATURES

# Phase 3.1: Defensive imports
def safe_import(module_name, func_names):
    """Safely import functions with fallbacks"""
    try:
        module = __import__(f'monitor.{module_name}', fromlist=[''])
        return {name: getattr(module, name) for name in func_names}
    except (ImportError, AttributeError) as e:
        print(f"[FALLBACK] {module_name}: {e}")
        return {name: lambda *args, **kwargs: 0 for name in func_names}

# ======================================================
# PATHS
# ======================================================

STATE_FILE = get_data_path("fatigue_state.json")
TIMESERIES_FILE = get_data_path("fatigue_timeseries.csv")

MAX_FATIGUE = 100
MIN_FATIGUE = 0


# ======================================================
# COGNITIVE FATIGUE MODEL
# ======================================================

class CognitiveFatigueModel:

    def __init__(self):
        self.fatigue_score = 0
        self.last_category = None
        self.last_session = None
        self.switch_count = 0
        self.fatigue_momentum = 0
        self.baseline_offset = 0
        self.weekly_load_accumulator = 0
        self.last_recalibration_date = None
        self.burnout_probability = 0
        self.burnout_level = "Low Risk"
        self.blocking_state = "BLOCKING_INACTIVE"
        self.throttle_state = "THROTTLE_INACTIVE"
        self.focus_lock_active = False
        self.focus_cycle_started = False


        self.load_state()
        self.start_time = datetime.now()
    # --------------------------------------------------
    # LOAD STATE
    # --------------------------------------------------

    def load_state(self):
        if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
            with open(STATE_FILE, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return
                self.fatigue_score = data.get("fatigue_score", 0)
                self.last_category = data.get("last_category")
                self.switch_count = data.get("switch_count", 0)
                self.fatigue_momentum = data.get("fatigue_momentum", 0)
                self.baseline_offset = data.get("baseline_offset", 0)
                self.weekly_load_accumulator = data.get("weekly_load_accumulator", 0)
                self.last_recalibration_date = data.get("last_recalibration_date")
                self.burnout_probability = data.get("burnout_probability", 0)
                self.burnout_level = data.get("burnout_level", "Low Risk")
    # --------------------------------------------------
    # SAVE STATE
    # --------------------------------------------------

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "fatigue_score": self.fatigue_score,
                "last_category": self.last_category,
                "switch_count": self.switch_count,
                "fatigue_momentum": self.fatigue_momentum,
                "baseline_offset": self.baseline_offset,
                "weekly_load_accumulator": self.weekly_load_accumulator,
                "last_recalibration_date": self.last_recalibration_date,
                "burnout_probability": self.burnout_probability,
                "burnout_level": self.burnout_level,
                }, f)

    # --------------------------------------------------
    # MAIN UPDATE ENGINE
    # --------------------------------------------------

    def update(self, category, duration_sec, hour):

        # ===============================================
        # STEP-1: RECOVERY
        # ===============================================

        # Phase 3.1: Safe imports
        recovery_funcs = safe_import('recovery_engine', ['load_sessions'])
        baseline_funcs = safe_import('neural_baseline_engine', ['load_baseline'])
        
        sessions = recovery_funcs['load_sessions']()
        baseline = baseline_funcs['load_baseline']()

        recovery_funcs = safe_import('recovery_engine', ['compute_recovery_score'])
        recovery = recovery_funcs['compute_recovery_score'](sessions)
        recovery *= getattr(baseline, 'get', lambda k, d=1.0: d)('baseline_recovery_factor')

        self.fatigue_score -= recovery
        self.fatigue_score = max(MIN_FATIGUE, self.fatigue_score)

        # ===============================================
        # STEP-2: BASE LOAD
        # ===============================================

        session_data = {
            "category": category,
            "duration_sec": duration_sec,
            "focus_type": "Deep Work"
                if category in ["Development", "Learning"]
                else "Normal"
        }

        load_funcs = safe_import('cognitive_load_engine', ['compute_load_penalty'])
        delta = load_funcs['compute_load_penalty'](session_data)
        delta *= getattr(baseline, 'get', lambda k, d=1.0: d)('baseline_load_factor')

        # ===============================================
        # STEP-3: SWITCH PENALTY
        # ===============================================

        if self.last_category and self.last_category != category:
            self.switch_count += 1
            delta += 0.8

        # ===============================================
        # STEP-4: IDLE RECOVERY
        # ===============================================

        if category == "Idle":
            delta -= 3.0

        # ===============================================
        # STEP-5: CIRCADIAN WEIGHT
        # ===============================================

        circadian_funcs = safe_import('circadian_engine', ['get_circadian_multiplier'])
        delta *= circadian_funcs['get_circadian_multiplier']()

        # ===============================================
        # STEP-6: DOPAMINE SPIKE DECAY
        # ===============================================

        current_session = {"category": category}

        if self.last_session:
            detect_dopamine_spike(self.last_session, current_session)

        delta += compute_dopamine_effect()

        # ===============================================
        # STEP-7: MOMENTUM BUILDING
        # ===============================================

        if category in ["Development", "Learning", "Design"]:
            self.fatigue_momentum += 0.4

        if self.switch_count > 3:
            self.fatigue_momentum += 0.3

        if category == "Idle":
            self.fatigue_momentum -= 0.6

        if category == "Entertainment":
            self.fatigue_momentum -= 0.2

        self.fatigue_momentum = max(0, min(15, self.fatigue_momentum))

        # Momentum amplifies load BEFORE applying it
        momentum_multiplier = 1 + (self.fatigue_momentum / 25)
        delta *= momentum_multiplier

        # ===============================================
        # STEP-8: APPLY DELTA
        # ===============================================

        self.fatigue_score += delta

        # ===============================================
        # STEP-9: LONG-TERM BASELINE DRIFT
        # ===============================================

        self.fatigue_score += self.baseline_offset

        # Clamp
        self.fatigue_score = max(MIN_FATIGUE, min(MAX_FATIGUE, self.fatigue_score))
        

        # Track weekly load
        self.weekly_load_accumulator += abs(delta)

        update_trend(self.fatigue_score)
        predictive_notification(self.break_decision if hasattr(self, "break_decision") else {})
        
        # -----------------------------------------------
        # STEP-2.16 BREAK DECISION ENGINE
        # -----------------------------------------------

        startup_seconds = (datetime.now() - self.start_time).total_seconds()

        if startup_seconds < 300:
            # Ignore breaks during first 5 minutes after boot
            self.break_decision = {"break_required": False}
        else:
            self.break_decision = decide_break_rl(
                fatigue_score=self.fatigue_score,
                burnout_probability=self.burnout_probability,
                fatigue_momentum=self.fatigue_momentum
            )
        

        # ===============================================
        # STEP-10: WEEKLY RECALIBRATION
        # ===============================================

        self.weekly_recalibration()
        
        if isinstance(self.break_decision, dict):
            if FEATURES.get("notifications_enabled", True) and self.break_decision.get("break_required"):
                try:
                    notify_break(self.break_decision)
                except Exception as e:
                    print("Notify error:", e)
            if self.break_decision.get("break_required") and FEATURES.get("break_timer_enabled", True):
                try:
                    urgency = self.break_decision.get("urgency_level", "Medium")
                    start_break_timer(
                        duration_minutes=self.break_decision.get("recommended_duration_minutes", 5),
                        urgency=str(urgency) if urgency else "Medium"
                    )
                except Exception as e:
                    print("Break timer error:", e)
        # ===============================================
        # UPDATE STATE
        # ===============================================

        self.last_category = category
        self.last_session = current_session
        
        # ===============================================
        # STEP-2.14: BURNOUT RISK PROBABILITY
        # ===============================================

        burnout_probability = compute_burnout_risk(
            fatigue_score=self.fatigue_score,
            fatigue_momentum=self.fatigue_momentum,
            baseline_offset=self.baseline_offset,
            switch_count=self.switch_count,
            recovery_value=recovery
        )

        self.burnout_probability = burnout_probability
        self.burnout_level = interpret_burnout_risk(burnout_probability)
        self.save_state()
        self.log_timeseries()
        
        update_baseline(self.fatigue_score, recovery)
        if FEATURES.get("app_blocking_enabled", True):
            try:
                blocking_state = enforce_blocking(
                    fatigue_level=self.get_state()["level"],
                    burnout_probability=self.burnout_probability
                )
                self.blocking_state = blocking_state
            except Exception as e:
                print("Blocking error:", e)
        if FEATURES.get("app_throttle_enabled", True):
            try:
                self.throttle_state = enforce_throttle(
                    fatigue_level=self.get_state()["level"],
                    burnout_probability=self.burnout_probability
                )
            except Exception as e:
                print("Throttle error:", e)
        
        # ==============================
        # STEP-2.21 — Adaptive Focus Lock
        # ==============================

        if FEATURES.get("focus_lock_enabled", True):
            try:
                if (
                    self.fatigue_score > 55 and
                    self.burnout_probability > 0.65 and
                    self.fatigue_momentum > 5
                ):
                    if not self.focus_lock_active:
                        activate_focus_lock()
                        self.focus_lock_active = True
                else:
                    if self.focus_lock_active:
                        release_focus_lock()
                        self.focus_lock_active = False
            except Exception as e:
                print("Focus lock error:", e)
        # ==============================
        # STEP-2.22 — Adaptive Focus Cycle
        # ==============================

        if (
            FEATURES.get("focus_lock_enabled", True) and
            self.focus_lock_active and
            self.fatigue_score > 45 and
            not getattr(self, "focus_cycle_started", False)
        ):
            try:
                start_focus_cycle(self.fatigue_score)
                self.focus_cycle_started = True
            except Exception as e:
                print("Focus cycle error:", e)
        state = self.get_state()

        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

        return state

    # --------------------------------------------------
    # WEEKLY RECALIBRATION
    # --------------------------------------------------

    def weekly_recalibration(self):
        today = datetime.now().date()

        if self.last_recalibration_date is None:
            self.last_recalibration_date = str(today)
            return

        last_date = datetime.strptime(
            self.last_recalibration_date, "%Y-%m-%d"
        ).date()

        days_passed = (today - last_date).days

        if days_passed >= 7:

            avg_weekly_load = self.weekly_load_accumulator / max(days_passed, 1)

            if avg_weekly_load > 25:
                self.baseline_offset += 3
            elif avg_weekly_load > 15:
                self.baseline_offset += 1
            elif avg_weekly_load < 8:
                self.baseline_offset -= 2

            self.baseline_offset = max(-10, min(20, self.baseline_offset))

            self.weekly_load_accumulator = 0
            self.last_recalibration_date = str(today)

    # --------------------------------------------------
    # LOG TIMESERIES
    # --------------------------------------------------

    def log_timeseries(self):
        file_exists = os.path.exists(TIMESERIES_FILE)

        with open(TIMESERIES_FILE, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("timestamp,fatigue_score,fatigue_momentum\n")

            f.write(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},"
                f"{round(self.fatigue_score,2)},"
                f"{round(self.fatigue_momentum,2)}\n"
            )

    # --------------------------------------------------
    # OUTPUT STATE
    # --------------------------------------------------

    def get_state(self):

        if self.fatigue_score < 20:
            level = "Fresh"

        elif self.fatigue_score < 40:
            level = "Mild Fatigue"

        elif self.fatigue_score < 70:
            level = "High Fatigue"

        else:
            level = "Critical Fatigue"

    # Burnout level
        if self.burnout_probability < 0.3:
            burnout_level = "Low"

        elif self.burnout_probability < 0.6:
            burnout_level = "Moderate"

        elif self.burnout_probability < 0.85:
            burnout_level = "High"

        else:
            burnout_level = "Severe"

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fatigue_score": round(self.fatigue_score, 2),
            "level": level,
            "burnout_probability": round(self.burnout_probability, 3),
            "burnout_level": burnout_level,
            "break_decision": getattr(self, "break_decision", "NO_BREAK")
        }


