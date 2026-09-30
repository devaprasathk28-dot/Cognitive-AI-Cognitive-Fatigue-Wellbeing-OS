from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QMouseEvent

from monitor.day_analysis_engine import analyze_day
from monitor.ui_animations import is_animating, _RUNNING_ANIMATIONS


class DayDetailPanel(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start = None
        self._orig_geom = None

        self.setFixedWidth(420)
        self.setObjectName("sidePanel")

        self.setStyleSheet("""
        QWidget#sidePanel {
            background-color: rgba(20,20,25,0.88);
            border-left: 1px solid rgba(255,255,255,0.06);
        }
        QFrame#card {
            background-color: rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 12px;
        }
        QLabel { color: #EDEDED; }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        self.title = QLabel("Details")
        self.title.setStyleSheet("font-size:18px; font-weight:bold;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close_requested.emit)

        header_row.addWidget(self.title)
        header_row.addStretch()
        header_row.addWidget(close_btn)

        main_layout.addLayout(header_row)

        self.content = QVBoxLayout()
        main_layout.addLayout(self.content)

        self.setLayout(main_layout)

    # ============================
    # LOAD DATA INTO PANEL
    # ============================
    def load_day(self, date):
        # clear previous
        for i in reversed(range(self.content.count())):
            item = self.content.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget:
                widget.deleteLater()

        data = analyze_day(date)

        # Title
        self.title.setText(date)

        # Total
        total = QLabel(f"{data['total']} min")
        total.setStyleSheet("font-size:24px; font-weight:bold;")
        self.content.addWidget(total)

        # Apps
        self.content.addWidget(QLabel("Top Apps"))
        for app, time in sorted(data["apps"].items(), key=lambda x: x[1], reverse=True):
            self.content.addWidget(QLabel(f"{app} — {time // 60} min"))

        # Categories
        self.content.addWidget(QLabel("Categories"))
        for cat, time in data["categories"].items():
            self.content.addWidget(QLabel(f"{cat} — {time // 60} min"))

        # Insight
        insight = self.generate_insight(data)
        insight_label = QLabel(f"🧠 {insight}")
        insight_label.setWordWrap(True)
        insight_label.setStyleSheet("color:#FFC107;")
        self.content.addWidget(insight_label)

    def generate_insight(self, data):
        if data["total"] > 300:
            return "High usage detected. Consider reducing screen time."
        if data["sessions"] > 50:
            return "Frequent app switching detected."
        return "Good usage balance today."

    def mousePressEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        self._drag_start = a0.globalPosition().toPoint()
        self._orig_geom = self.geometry()

    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if a0 is None or self._drag_start is None or self._orig_geom is None:
            return

        delta = a0.globalPosition().toPoint() - self._drag_start

        # only allow dragging to the right
        if delta.x() > 0:
            self.setGeometry(self._orig_geom.translated(delta.x(), 0))

    def mouseReleaseEvent(self, a0: QMouseEvent | None):
        if a0 is None or self._drag_start is None or self._orig_geom is None:
            return

        moved = self.geometry().x() - self._orig_geom.x()

        # threshold to close
        if moved > 120:
            # Drag far enough - request close.
            self.close_requested.emit()
        else:
            # snap back
            from monitor.ui_animations import animate_panel
            animate_panel(self, self.geometry(), self._orig_geom)

        self._drag_start = None
        self._orig_geom = None
