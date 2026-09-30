from collections import defaultdict
import csv
from datetime import datetime
from monitor.paths import get_data_path

FILE = get_data_path("usage_sessions.csv")


def load_data():
    data = []
    try:
        with open(FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except:
        pass
    return data


def group_by_day():
    data = load_data()

    grouped = defaultdict(list)

    for row in data:
        ts = row.get("timestamp")
        if not ts:
            continue

        date = ts.split(" ")[0]  # YYYY-MM-DD
        grouped[date].append(row)

    return grouped


def analyze_day(date):

    grouped = group_by_day()
    day_data = grouped.get(date, [])

    total = 0
    app_usage = defaultdict(int)
    category_usage = defaultdict(int)

    for row in day_data:
        duration = int(row.get("duration", 0))
        total += duration

        app_usage[row["app"]] += duration
        category_usage[row["category"]] += duration

    return {
        "total": total // 60,
        "apps": dict(app_usage),
        "categories": dict(category_usage),
        "sessions": len(day_data)
    }