import csv
import os
import re
from datetime import datetime

USAGE_LOG = "data/usage_categorized_v2.csv"
MEMORY_FILE = "data/intent_memory.csv"

def get_time_bucket(ts):
    hour = ts.hour
    if 5 <= hour <= 11:
        return "morning"
    elif 12 <= hour <= 16:
        return "afternoon"
    elif 17 <= hour <= 21:
        return "evening"
    else:
        return "night"

def extract_keywords(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9 ]", " ", title)
    words = [w for w in title.split() if len(w) > 3]
    return list(dict.fromkeys(words))[:3]

def load_memory():
    memory = {}

    if not os.path.exists(MEMORY_FILE):
        return memory

    with open(MEMORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        fieldnames = reader.fieldnames or []
        if "pattern_key" not in fieldnames:
            print("⚠️ intent_memory.csv schema mismatch — reinitializing memory")
            return memory

        for row in reader:
            key = row.get("pattern_key")
            if key:
                memory[key] = row

    return memory
def reinforce_memory(memory, pattern_key, final_category, final_intent, decision_source):
    if pattern_key not in memory:
        return

    mem = memory[pattern_key]
    conf = float(mem["confidence"])

    # Positive reinforcement
    if decision_source == "MEMORY":
        conf = min(0.95, conf + 0.02)

    # Negative reinforcement
    elif decision_source in ("REGISTRY", "ML"):
        conf = max(0.05, conf - 0.05)

    mem["confidence"] = str(conf)
    mem["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Forget bad memories
    if conf <= 0.15:
        del memory[pattern_key]


def save_memory(memory):
    with open(MEMORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "pattern_key",
                "raw_app_name",
                "keywords",
                "time_bucket",
                "category",
                "intent",
                "confidence",
                "seen_count",
                "first_seen",
                "last_updated",
            ],
        )
        writer.writeheader()
        for row in memory.values():
            writer.writerow(row)

def main():
    print("🧠 STEP-2.3.2 — Extracting Intent Memory")

    memory = load_memory()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(USAGE_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_app = row["raw_app_name"]
            category = row["category"]
            intent = row.get("intent", "General Usage")
            title = row.get("window_title", "")

            if not title.strip():
                continue

            ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            time_bucket = get_time_bucket(ts)
            keywords = extract_keywords(title)

            if not keywords:
                continue

            key = f"{raw_app}|{'_'.join(keywords)}|{time_bucket}"

            if key not in memory:
                memory[key] = {
                    "pattern_key": key,
                    "raw_app_name": raw_app,
                    "keywords": ",".join(keywords),
                    "time_bucket": time_bucket,
                    "category": category,
                    "intent": intent,
                    "confidence": "0.30",
                    "seen_count": "1",
                    "first_seen": now,
                    "last_updated": now,
                }
            else:
                mem = memory[key]
                mem["seen_count"] = str(int(mem["seen_count"]) + 1)
                mem["confidence"] = str(min(0.95, float(mem["confidence"]) + 0.05))
                mem["last_updated"] = now

    save_memory(memory)
    print(f"✅ Intent memory updated — {len(memory)} patterns stored")

if __name__ == "__main__":
    main()
