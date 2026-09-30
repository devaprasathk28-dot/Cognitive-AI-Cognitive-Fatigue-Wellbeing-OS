import time
from datetime import datetime

from monitor.notification_engine import show_notification


class FocusSessionManager:

    def __init__(self):
        self.active = False
        self.session_type = None
        self.end_time = None

    # --------------------------------------------------
    # START FOCUS SESSION
    # --------------------------------------------------
    def start_focus(self, duration_minutes):

        self.active = True
        self.session_type = "focus"
        self.end_time = time.time() + duration_minutes * 60

        print(f"\n🎯 Focus Session Started ({duration_minutes} min)\n")

        show_notification(
            "🎯 Focus Mode",
            f"Deep work session started for {duration_minutes} minutes"
        )

    # --------------------------------------------------
    # START BREAK SESSION
    # --------------------------------------------------
    def start_break(self, duration_minutes):

        self.active = True
        self.session_type = "break"
        self.end_time = time.time() + duration_minutes * 60

        print(f"\n🛑 Break Session Started ({duration_minutes} min)\n")

        show_notification(
            "🛑 Break Time",
            f"Take a break for {duration_minutes} minutes"
        )

    # --------------------------------------------------
    # UPDATE SESSION STATE
    # --------------------------------------------------
    def update(self):

        if not self.active or self.end_time is None:
            return None

        remaining = int(self.end_time - time.time())

        if remaining <= 0:

            if self.session_type == "focus":
                self.active = False
                return "focus_complete"

            elif self.session_type == "break":
                self.active = False
                return "break_complete"

        return None

    # --------------------------------------------------
    # ADAPTIVE DECISION
    # --------------------------------------------------
    def decide_focus_duration(self, fatigue, momentum):

        if fatigue < 30:
            return 45

        if fatigue < 50:
            return 30

        if fatigue < 70:
            return 20

        return 10

    def decide_break_duration(self, fatigue):

        if fatigue > 80:
            return 10

        if fatigue > 60:
            return 7

        return 5