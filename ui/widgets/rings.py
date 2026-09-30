from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF

class CircularProgress(QWidget):
    def __init__(self, title, color_hex):
        super().__init__()
        self.setFixedSize(120, 140)
        self.value = 0
        self.max_val = 100
        self.color = QColor(color_hex)
        self.bg_color = QColor(color_hex)
        self.bg_color.setAlpha(30)
        self.title_str = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setStyleSheet("color: #A0A0AB; font-size: 12px; font-weight: 500;")
        
        layout.addStretch()
        layout.addWidget(self.title_lbl)

    def set_value(self, val, max_val=100):
        self.value = min(val, max_val)
        self.max_val = max(1, max_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height() - 30)
        rect = QRectF(self.width()/2 - size/2 + 5, 5, size - 10, size - 10)

        # Draw Background Ring
        pen_bg = QPen(self.bg_color)
        pen_bg.setWidth(8)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height()), 0, 360 * 16)

        # Draw Progress Ring
        pen_fg = QPen(self.color)
        pen_fg.setWidth(8)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        span_angle = int((self.value / self.max_val) * 360 * 16)
        # Qt starts 0 at 3 o'clock, we want 12 o'clock, so start at 90 deg (90*16=1440)
        painter.drawArc(int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height()), 90 * 16, -span_angle)

        # Draw Text
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        text = str(int(self.value)) + "%" if self.max_val == 100 else f"{int(self.value)}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.end()
