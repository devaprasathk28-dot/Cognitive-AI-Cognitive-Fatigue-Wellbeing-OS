# ======================================================
# ADAPTIVE FOCUS MODE LOCK ENGINE
# STEP-2.21
# ======================================================

try:
    import psutil
except ImportError:
    psutil = None
import time
import threading

# Allowed apps during Focus Lock
FOCUS_WHITELIST = [
    "code.exe",
    "pycharm64.exe",
    "idea64.exe",
    "androidstudio.exe",
    "notepad.exe",
    "winword.exe",
    "excel.exe",
    "powerpnt.exe",
    "cmd.exe",
    "powershell.exe",
    "windowsterminal.exe"
]

FOCUS_LOCK_STATE = {
    "active": False
}

LOCKED_PROCESSES = {}


# --------------------------------------------------
# Activate Focus Lock
# --------------------------------------------------

def activate_focus_lock():
    if psutil is None:
        return "FOCUS_LOCK_UNAVAILABLE"
    if FOCUS_LOCK_STATE["active"]:
        return "FOCUS_ALREADY_ACTIVE"

    FOCUS_LOCK_STATE["active"] = True
    print("🔒 FOCUS MODE ACTIVATED")

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.name().lower()

            if name not in FOCUS_WHITELIST:
                proc.suspend()
                LOCKED_PROCESSES[name] = proc

        except Exception:
            continue

    return "FOCUS_LOCK_ENABLED"


# --------------------------------------------------
# Release Focus Lock
# --------------------------------------------------

def release_focus_lock():

    if not FOCUS_LOCK_STATE["active"]:
        return "FOCUS_NOT_ACTIVE"

    for name, proc in list(LOCKED_PROCESSES.items()):
        try:
            proc.resume()
        except Exception:
            pass

    LOCKED_PROCESSES.clear()
    FOCUS_LOCK_STATE["active"] = False

    print("🔓 FOCUS MODE RELEASED")

    return "FOCUS_LOCK_DISABLED"
