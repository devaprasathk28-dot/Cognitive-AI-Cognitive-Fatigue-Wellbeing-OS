# ======================================================
# BURNOUT FORECAST RUNNER
# ======================================================

import os
import csv
from datetime import datetime, timedelta
from monitor.burnout_lstm_model import forecast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "burnout_forecast.csv")


def main():
    print("🧠 STEP-2.15 — Multi-Day Burnout Forecast Running")

    predictions = forecast()

    if not predictions:
        print("⚠️ Not enough historical data")
        return

    today = datetime.now()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "burnout_probability_percent"])

        for i, prob in enumerate(predictions):
            future_date = today + timedelta(days=i+1)
            writer.writerow([
                future_date.strftime("%Y-%m-%d"),
                prob
            ])

    print("✅ Burnout forecast saved")
    print("Predictions:", predictions)


if __name__ == "__main__":
    main()
