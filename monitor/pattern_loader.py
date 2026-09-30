import json
import os

PATTERN_FILE = "data/behavior_patterns.json"


def load_patterns():

    if not os.path.exists(PATTERN_FILE):
        return {}

    try:
        with open(PATTERN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}