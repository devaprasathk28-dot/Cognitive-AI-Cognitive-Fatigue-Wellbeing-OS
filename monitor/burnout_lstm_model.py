# ======================================================
# BURNOUT LSTM FORECAST MODEL
# STEP-2.15
# ======================================================

import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMESERIES_FILE = os.path.join(BASE_DIR, "data", "fatigue_timeseries.csv")
MODEL_FILE = os.path.join(BASE_DIR, "models", "burnout_lstm.pt")

SEQUENCE_LENGTH = 20
PREDICT_DAYS = 7


# ======================================================
# LSTM MODEL
# ======================================================

class BurnoutLSTM(nn.Module):
    def __init__(self, input_size=2, hidden_size=64, num_layers=2):
        super(BurnoutLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return torch.sigmoid(out)


# ======================================================
# LOAD DATA
# ======================================================

def load_data():
    df = pd.read_csv(TIMESERIES_FILE)

    if len(df) < SEQUENCE_LENGTH + 5:
        return None, None, None

    features = df[["fatigue_score", "fatigue_momentum"]].values

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(features)

    X, y = [], []

    for i in range(len(scaled) - SEQUENCE_LENGTH):
        X.append(scaled[i:i+SEQUENCE_LENGTH])
        y.append(scaled[i+SEQUENCE_LENGTH][0])

    return torch.tensor(X, dtype=torch.float32), \
           torch.tensor(y, dtype=torch.float32).unsqueeze(1), \
           scaler


# ======================================================
# TRAIN MODEL
# ======================================================

def train_model():
    X, y, scaler = load_data()

    if X is None:
        print("⚠️ Not enough data for LSTM training")
        return None

    model = BurnoutLSTM()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(50):
        output = model(X)
        loss = criterion(output, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    torch.save(model.state_dict(), MODEL_FILE)

    print("✅ Burnout LSTM model trained & saved")
    return model


# ======================================================
# LOAD MODEL
# ======================================================

def load_model():
    model = BurnoutLSTM()

    if not os.path.exists(MODEL_FILE):
        return train_model()

    model.load_state_dict(torch.load(MODEL_FILE))
    model.eval()
    return model


# ======================================================
# FORECAST NEXT DAYS
# ======================================================

def forecast():
    try:
        import torch
        import pandas as pd
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler

        model = load_model()

        if model is None:
            return []

        df = pd.read_csv(TIMESERIES_FILE)

        if len(df) < SEQUENCE_LENGTH:
            return []

        features = df[["fatigue_score", "fatigue_momentum"]].values

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(features)

        last_seq = scaled[-SEQUENCE_LENGTH:]
        current_seq = torch.tensor(
            last_seq,
            dtype=torch.float32
        ).unsqueeze(0)

        predictions = []

        for _ in range(PREDICT_DAYS):
            pred = model(current_seq)
            burnout_prob = pred.item()

            predictions.append(round(burnout_prob * 100, 2))

            next_step = np.array([[burnout_prob, burnout_prob]])
            next_scaled = scaler.transform(next_step)

            new_seq = np.append(
                current_seq.squeeze(0).numpy()[1:],
                [next_scaled[0]],
                axis=0
            )

            current_seq = torch.tensor(
                new_seq,
                dtype=torch.float32
            ).unsqueeze(0)

        return predictions

    except Exception as e:
        print("⚠️ LSTM Forecast fallback:", e)
        return [30.0] * PREDICT_DAYS  # safe default
