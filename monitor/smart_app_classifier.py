def classify_app(app_name, window_title):

    app = app_name.lower()
    title = window_title.lower()

    # ===============================
    # 🎯 DEVELOPMENT
    # ===============================
    if "code" in app or "pycharm" in app:
        return "Development"

    if "github" in title or "gitlab" in title:
        return "Development"

    # ===============================
    # 📚 LEARNING
    # ===============================
    if "stackoverflow" in title or "tutorial" in title:
        return "Learning"

    if "documentation" in title or "docs" in title:
        return "Learning"

    # ===============================
    # 🎬 ENTERTAINMENT
    # ===============================
    if "youtube" in title or "netflix" in title:
        return "Entertainment"

    if "spotify" in app:
        return "Entertainment"

    # ===============================
    # 💼 PRODUCTIVITY
    # ===============================
    if "word" in app or "excel" in app:
        return "Productivity"

    # ===============================
    # 🌐 GENERAL BROWSING
    # ===============================
    if "chrome" in app or "edge" in app:
        return "Browsing"

    # ===============================
    # 💤 IDLE / OTHER
    # ===============================
    return "Other"