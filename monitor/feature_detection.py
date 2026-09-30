from monitor.feature_flags import FEATURES

def detect_features():

    # LSTM (torch)
    try:
        import torch
        FEATURES["lstm_enabled"] = True
    except:
        FEATURES["lstm_enabled"] = False

    # AI Chat (Ollama / local)
    try:
        import requests
        FEATURES["ai_chat_enabled"] = True
    except:
        FEATURES["ai_chat_enabled"] = False