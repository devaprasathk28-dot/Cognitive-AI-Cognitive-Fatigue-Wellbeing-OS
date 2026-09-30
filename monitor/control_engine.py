import os

CONTROL_DIR = "monitor"


def is_paused():
    return os.path.exists(os.path.join(CONTROL_DIR, "PAUSE"))


def is_stopped():
    return os.path.exists(os.path.join(CONTROL_DIR, "STOP"))


def is_strict_disabled():
    return os.path.exists(os.path.join(CONTROL_DIR, "NO_STRICT"))


def set_pause():
    open(os.path.join(CONTROL_DIR, "PAUSE"), "w").close()


def resume():
    try:
        os.remove(os.path.join(CONTROL_DIR, "PAUSE"))
    except:
        pass


def stop():
    open(os.path.join(CONTROL_DIR, "STOP"), "w").close()