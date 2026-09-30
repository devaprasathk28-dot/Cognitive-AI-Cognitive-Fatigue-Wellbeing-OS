# ======================================================
# SMART APP THROTTLE ENGINE
# STEP-2.20.1 → Progressive Delay Escalation
# ======================================================


import time
import threading
from typing import TYPE_CHECKING

try:
    import psutil
except ImportError:
    psutil = None


THROTTLE_TARGETS = [
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "spotify.exe",
    "steam.exe",
    "discord.exe"
]

ACTIVE_THROTTLES = {}

# Escalation memory
ESCALATION_STATE = {
    "level": 0,
    "last_trigger_time": None
}

MAX_ESCALATION = 5


# --------------------------------------------------
# Base Delay Logic
# --------------------------------------------------

def get_base_delay(fatigue_level, burnout_probability):

    if burnout_probability >= 0.8:
        return 45

    if fatigue_level == "Critical Fatigue":
        return 30

    if fatigue_level == "High Fatigue":
        return 10

    return 0


# --------------------------------------------------
# Escalation Logic
# --------------------------------------------------

def get_escalated_delay(base_delay):
    escalation_level = ESCALATION_STATE["level"]

    multiplier = 1 + (escalation_level * 0.5)
    return int(base_delay * multiplier)


def increase_escalation():
    if ESCALATION_STATE["level"] < MAX_ESCALATION:
        ESCALATION_STATE["level"] += 1


def decrease_escalation():
    if ESCALATION_STATE["level"] > 0:
        ESCALATION_STATE["level"] -= 1


# --------------------------------------------------
# Throttle Process
# --------------------------------------------------

def throttle_process(proc, delay):
    try:
        name = proc.name().lower()

        if name in ACTIVE_THROTTLES:
            return

        ACTIVE_THROTTLES[name] = True

        proc.suspend()
        print(f"⏳ Progressive Throttle: {name} delayed {delay}s")

        time.sleep(delay)

        proc.resume()
        print(f"✅ {name} resumed")

        del ACTIVE_THROTTLES[name]

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


# --------------------------------------------------
# Main Enforcement
# --------------------------------------------------

def enforce_throttle(fatigue_level, burnout_probability):
    if psutil is None:
        return "THROTTLE_UNAVAILABLE"
    base_delay = get_base_delay(fatigue_level, burnout_probability)

    if base_delay == 0:
        decrease_escalation()
        return "THROTTLE_INACTIVE"

    increase_escalation()

    delay = get_escalated_delay(base_delay)

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.name().lower()

            if name in THROTTLE_TARGETS:
                threading.Thread(
                    target=throttle_process,
                    args=(proc, delay),
                    daemon=True
                ).start()

        except Exception:
            continue

    return f"THROTTLE_ESCALATED_{delay}s"
