import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

META_FILE = os.path.join(BASE_DIR, "data", "meta_cognition.json")
CONFIG_FILE = os.path.join(BASE_DIR, "data", "adaptive_config.json")


DEFAULT_CONFIG = {

    "fatigue_threshold": 70,
    "break_sensitivity": 1.0,
    "burnout_sensitivity": 1.0,
    "focus_weight": 1.0

}


def load_json(path):

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_config():

    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    return load_json(CONFIG_FILE)


def adapt_parameters(config, meta):

    accuracy = meta.get("prediction_accuracy", 1)

    if accuracy == 0:

        config["break_sensitivity"] += 0.05
        config["burnout_sensitivity"] += 0.05

        config["fatigue_threshold"] -= 1

    else:

        config["focus_weight"] += 0.02

    config["break_sensitivity"] = min(2.0, config["break_sensitivity"])
    config["burnout_sensitivity"] = min(2.0, config["burnout_sensitivity"])

    config["fatigue_threshold"] = max(50, min(90, config["fatigue_threshold"]))

    return config


def run_adaptation():

    meta = load_json(META_FILE)

    if not meta:
        print("No meta cognition data found")
        return

    config = load_config()

    new_config = adapt_parameters(config, meta)

    save_json(CONFIG_FILE, new_config)

    report = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_config": new_config

    }

    print("🧠 Cognitive Adaptation Engine Running")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":

    run_adaptation()