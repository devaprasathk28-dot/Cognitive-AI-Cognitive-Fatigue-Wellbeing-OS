from monitor.auto_start import enable_auto_start, disable_auto_start
import sys
import json
import os

SETTINGS_FILE = "user_settings.json"

DEFAULT_SETTINGS = {
    "onboarding_done": False,
    "auto_start": False,
    "focus_duration": 45,
    "break_duration": 10
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
    except:
        return DEFAULT_SETTINGS.copy()


def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def toggle_auto_start(self, enabled):
    exe_path = sys.executable

    if enabled:
        enable_auto_start("CognitiveAI", exe_path)
    else:
        disable_auto_start("CognitiveAI")

    self.settings["auto_start"] = enabled
    save_settings(self.settings)