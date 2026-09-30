import json
from monitor.paths import get_data_path
from monitor.burnout_lstm_model import forecast

TREND_FILE = get_data_path("fatigue_trend.json")


def load_trend():
    try:
        with open(TREND_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_trend(data):
    with open(TREND_FILE, "w") as f:
        json.dump(data[-30:], f)  # keep last 30 entries


def update_trend(fatigue):
    data = load_trend()
    data.append(fatigue)
    save_trend(data)
    
def analyze_trend():

    data = load_trend()

    if len(data) < 5:
        return {"risk": 0}

    # recent vs older
    recent = sum(data[-3:]) / 3
    previous = sum(data[-6:-3]) / 3

    delta = recent - previous

    # ============================
    # 🧠 RISK CALCULATION
    # ============================

    if delta > 15:
        return {"risk": 80, "type": "rapid_increase"}

    elif delta > 8:
        return {"risk": 60, "type": "moderate_increase"}

    elif delta > 3:
        return {"risk": 40, "type": "slow_increase"}

    return {"risk": 10, "type": "stable"}


def predict_future_fatigue(history=None):
    try:
        predictions = forecast()
        future_fatigue = round(sum(predictions) / len(predictions), 2) if predictions else 0
        return {"future_fatigue": future_fatigue, "risk": min(int(future_fatigue), 100)}
    except:
        return {"future_fatigue": 0, "risk": 0}