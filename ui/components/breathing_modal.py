from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QFont
from storage.db import log_notification


class BreathingCircle(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.radius_factor = 0.5  # 0.4 to 0.95
        self.glow_color = QColor(126, 231, 198)

    def set_expansion(self, factor: float, color: QColor):
        self.radius_factor = max(0.35, min(0.95, factor))
        self.glow_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        max_r = min(self.width(), self.height()) / 2 - 10
        r = max_r * self.radius_factor

        # Background ambient halo
        halo_grad = QRadialGradient(center_x, center_y, r * 1.3)
        halo_color = QColor(self.glow_color)
        halo_color.setAlpha(40)
        halo_grad.setColorAt(0.0, halo_color)
        halo_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(halo_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - r * 1.3), int(center_y - r * 1.3), int(r * 2.6), int(r * 2.6))

        # Main breathing orb
        orb_grad = QRadialGradient(center_x - r * 0.2, center_y - r * 0.2, r)
        c1 = QColor(self.glow_color)
        c1.setAlpha(220)
        c2 = QColor(self.glow_color)
        c2.setAlpha(80)
        orb_grad.setColorAt(0.0, c1)
        orb_grad.setColorAt(0.8, c2)
        orb_grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setBrush(orb_grad)
        painter.drawEllipse(int(center_x - r), int(center_y - r), int(r * 2), int(r * 2))

        # Core outline
        outline = QColor(255, 255, 255, 140)
        painter.setPen(outline)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(center_x - r), int(center_y - r), int(r * 2), int(r * 2))


class BreathingModal(QDialog):
    break_completed = pyqtSignal()

    def __init__(self, parent=None, duration_seconds=120):
        super().__init__(parent)
        self.setWindowTitle("Cognitive Micro-Break")
        self.setFixedSize(480, 460)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0D111A, stop:1 #080A0E);
                border: 1px solid rgba(126, 231, 198, 0.3);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header
        t = QLabel("Mindful Resynchronization")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(t)

        sub = QLabel("4-7-8 Breathing Technique to Clear Cognitive Residue")
        sub.setStyleSheet("font-size: 13px; color: rgba(224, 229, 240, 0.65);")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        # Orb
        self.orb = BreathingCircle(self)
        layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)

        # Phase Label
        self.phase_lbl = QLabel("Breathe In...")
        self.phase_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #7EE7C6;")
        self.phase_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.phase_lbl)

        # Timer countdown
        self.time_left = duration_seconds
        self.countdown_lbl = QLabel(self._format_time(self.time_left))
        self.countdown_lbl.setStyleSheet("font-size: 14px; color: rgba(224, 229, 240, 0.5); font-weight: 600;")
        self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_lbl)

        # Close/Finish Button
        btn_row = QHBoxLayout()
        self.btn_done = QPushButton("End Break & Return")
        self.btn_done.setObjectName("primaryButton")
        self.btn_done.setStyleSheet("""
            QPushButton {
                background: rgba(126, 231, 198, 0.15);
                border: 1px solid rgba(126, 231, 198, 0.4);
                color: #7EE7C6;
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(126, 231, 198, 0.28);
            }
        """)
        self.btn_done.clicked.connect(self.finish_break)
        btn_row.addWidget(self.btn_done)
        layout.addLayout(btn_row)

        # 4-7-8 timing cycle: Inhale 4s, Hold 7s, Exhale 8s = 19s total
        self.cycle_seconds = 19
        self.cycle_elapsed = 0.0
        self.step_timer = QTimer(self)
        self.step_timer.timeout.connect(self._on_tick)
        self.step_timer.start(50)  # 20 ticks per second for smooth expansion

    def _format_time(self, s: int) -> str:
        m, sec = divmod(s, 60)
        return f"{m:02d}:{sec:02d} remaining"

    def _on_tick(self):
        self.cycle_elapsed += 0.05
        cycle_pos = self.cycle_elapsed % self.cycle_seconds

        # Phase calculation
        if cycle_pos < 4.0:
            # INHALE (4 seconds)
            progress = cycle_pos / 4.0
            factor = 0.4 + 0.55 * progress
            self.orb.set_expansion(factor, QColor(126, 231, 198))
            self.phase_lbl.setText("Breathe In Gently")
            self.phase_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #7EE7C6;")
        elif cycle_pos < 11.0:
            # HOLD (7 seconds)
            self.orb.set_expansion(0.95, QColor(123, 125, 255))
            self.phase_lbl.setText("Hold & Calm Your Focus")
            self.phase_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #7B7DFF;")
        else:
            # EXHALE (8 seconds)
            progress = (cycle_pos - 11.0) / 8.0
            factor = 0.95 - 0.55 * progress
            self.orb.set_expansion(factor, QColor(251, 191, 36))
            self.phase_lbl.setText("Slowly Exhale & Release")
            self.phase_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #FBBF24;")

        # Second countdown update
        if int(self.cycle_elapsed * 20) % 20 == 0:
            if self.time_left > 0:
                self.time_left -= 1
                self.countdown_lbl.setText(self._format_time(self.time_left))
            else:
                self.finish_break()

    def finish_break(self):
        self.step_timer.stop()
        try:
            log_notification("Break", "Completed a restorative 4-7-8 micro-break session.")
        except Exception:
            pass
        self.break_completed.emit()
        self.accept()
