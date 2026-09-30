# ======================================================
# SMART APP BLOCKER ENGINE
# STEP-2.19
# ======================================================

try:
    import psutil
except ImportError:
    psutil = None

BLOCK_POLICY = {
    "Entertainment": [
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "spotify.exe",
        "vlc.exe",
        "steam.exe"
    ],
    "Social": [
        "discord.exe",
        "linkedin.exe"
    ]
}

ALWAYS_ALLOW = [
    "explorer.exe",
    "taskmgr.exe",
    "python.exe",
    "cmd.exe",
    "powershell.exe"
]

BLOCKED_PROCESSES = set()


def block_apps(category: str):
    """Terminate distracting apps safely"""
    if psutil is None:
        return
    targets = BLOCK_POLICY.get(category, [])

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.name().lower()

            if name in ALWAYS_ALLOW:
                continue

            if name in targets and name not in BLOCKED_PROCESSES:
                proc.terminate()
                BLOCKED_PROCESSES.add(name)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def unblock_apps():
    """Clear blocked memory (apps can reopen normally)"""
    BLOCKED_PROCESSES.clear()


def enforce_blocking(
    fatigue_level: str,
    burnout_probability: float
):
    if psutil is None:
        return "BLOCKING_UNAVAILABLE"

    if fatigue_level == "Critical Fatigue" or burnout_probability >= 0.75:
        block_apps("Entertainment")
        block_apps("Social")
        return "BLOCKING_ACTIVE"

    else:
        unblock_apps()
        return "BLOCKING_INACTIVE"
