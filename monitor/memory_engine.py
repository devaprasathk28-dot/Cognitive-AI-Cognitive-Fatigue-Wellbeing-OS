import json
import os
from datetime import datetime
from monitor.paths import get_data_path

MEMORY_FILE = get_data_path("chat_memory.json")
_CACHE = None


def load_memory():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not os.path.exists(MEMORY_FILE):
        _CACHE = []
        return _CACHE
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            _CACHE = json.load(f)
    except:
        _CACHE = []
    return _CACHE


def save_memory(memory):
    global _CACHE
    _CACHE = memory[-50:]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(_CACHE, f, indent=2)


def add_memory(user, ai):
    memory = load_memory()
    memory.append({"timestamp": datetime.now().isoformat(), "user": user, "ai": ai})
    save_memory(memory)


def get_recent_context(limit=5):
    return load_memory()[-limit:]