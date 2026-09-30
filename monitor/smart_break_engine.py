import time
from datetime import datetime, timedelta


class SmartBreakManager:

    def __init__(self):
        self.last_break_time = None
        self.cooldown_minutes = 10  # minimum gap between breaks

    # --------------------------------------------------
    # CHECK COOLDOWN
    # --------------------------------------------------
    def can_trigger_break(self):

        if self.last_break_time is None:
            return True

        elapsed = datetime.now() - self.last_break_time

        return elapsed >= timedelta(minutes=self.cooldown_minutes)

    # --------------------------------------------------
    # DECIDE BREAK DURATION
    # --------------------------------------------------
    def get_break_duration(self, fatigue, burnout, momentum):

        # High risk → long break
        if fatigue > 80 or burnout > 0.8:
            return 10

        # Medium risk
        if fatigue > 60 or momentum > 8:
            return 5

        # Mild fatigue
        if fatigue > 40:
            return 3

        return 0  # no break needed

    # --------------------------------------------------
    # MAIN DECISION FUNCTION
    # --------------------------------------------------
    def evaluate(self, fatigue, burnout, momentum):

        if not self.can_trigger_break():
            return {
                "take_break": False,
                "reason": "Cooldown active"
            }

        duration = self.get_break_duration(fatigue, burnout, momentum)

        if duration > 0:
            self.last_break_time = datetime.now()

            return {
                "take_break": True,
                "duration": duration
            }

        return {
            "take_break": False
        }