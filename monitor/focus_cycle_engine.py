# ======================================================
# ADAPTIVE FOCUS WINDOW ENGINE
# ======================================================

import time
import threading

from monitor.focus_lock_engine import activate_focus_lock, release_focus_lock


FOCUS_STATE = {
    "cycle_active": False,
    "cycle_end_time": None,
    "cycle_duration": 0
}


def get_focus_duration(fatigue_score):

    if fatigue_score < 40:
        return 30 * 60
    elif fatigue_score < 60:
        return 25 * 60
    elif fatigue_score < 75:
        return 20 * 60
    else:
        return 15 * 60


def start_focus_cycle(fatigue_score):

    if FOCUS_STATE["cycle_active"]:
        return "FOCUS_ALREADY_RUNNING"

    duration = get_focus_duration(fatigue_score)

    FOCUS_STATE["cycle_active"] = True
    FOCUS_STATE["cycle_duration"] = duration
    FOCUS_STATE["cycle_end_time"] = time.time() + duration

    activate_focus_lock()

    thread = threading.Thread(target=run_focus_timer)
    thread.daemon = True
    thread.start()

    return "FOCUS_STARTED"


def run_focus_timer():

    while FOCUS_STATE["cycle_active"]:

        remaining = FOCUS_STATE["cycle_end_time"] - time.time()

        if remaining <= 0:
            break

        time.sleep(1)

    if FOCUS_STATE["cycle_active"]:
        end_focus_cycle(force_break=True)


def end_focus_cycle(force_break=False):

    FOCUS_STATE["cycle_active"] = False
    release_focus_lock()

    if force_break:
        return "BREAK_TRIGGERED"

    return "FOCUS_ENDED"
