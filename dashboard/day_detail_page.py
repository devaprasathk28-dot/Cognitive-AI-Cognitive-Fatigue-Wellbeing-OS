from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

from monitor.day_analysis_engine import analyze_day
from monitor.ui_components import create_card
from monitor.ui_animations import slide_in, fade_in


class DayDetailPage(QWidget):

    def __init__(self, date):
        super().__init__()

        self.setWindowTitle(f"Details - {date}")
        self.setGeometry(300, 100, 500, 700)

        self.setStyleSheet("""
        QWidget { background-color: #0E0E11; color: white; }
        QFrame#card {
            background-color: rgba(30,30,35,0.9);
            border-radius: 14px;
            padding: 12px;
        }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        data = analyze_day(date)

        # ======================
        # HEADER
        # ======================
        header = QLabel(f"{data['total']} min")
        header.setStyleSheet("font-size:28px; font-weight:bold;")

        sub = QLabel(date)
        sub.setStyleSheet("color:#888;")

        layout.addWidget(header)
        layout.addWidget(sub)

        # ======================
        # METRICS CARDS
        # ======================
        card_row = QHBoxLayout()

        sessions_card = create_card("Sessions", str(data["sessions"]))
        apps_card = create_card("Apps Used", str(len(data["apps"])))

        card_row.addWidget(sessions_card)
        card_row.addWidget(apps_card)

        layout.addLayout(card_row)

        # ======================
        # APP LIST
        # ======================
        layout.addWidget(QLabel("Top Apps"))

        for app, time in sorted(data["apps"].items(), key=lambda x: x[1], reverse=True):
            layout.addWidget(QLabel(f"{app} — {time // 60} min"))

        # ======================
        # CATEGORY
        # ======================
        layout.addWidget(QLabel("Categories"))

        for cat, time in data["categories"].items():
            layout.addWidget(QLabel(f"{cat} — {time // 60} min"))

        # ======================
        # AI INSIGHT
        # ======================
        insight = self.generate_insight(data)

        insight_label = QLabel(f"🧠 {insight}")
        insight_label.setWordWrap(True)
        insight_label.setStyleSheet("color:#FFC107;")

        layout.addWidget(insight_label)

        self.setLayout(layout)

        # ======================
        # ANIMATION
        # ======================
        self.setWindowOpacity(0)
        fade_in(self)
        slide_in(self, 200, 0)

    def generate_insight(self, data):

        if data["total"] > 300:
            return "High usage detected. Consider reducing screen time."

        if data["sessions"] > 50:
            return "Frequent app switching detected."

        return "Good usage balance today."
