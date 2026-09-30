import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QApplication, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ui.components.core_ui import (
    create_card_frame, fade_in,
    install_button_hover, install_button_press
)
from storage.db import log_focus_session, log_notification
from monitor.ambient_sound_engine import play_ambient, stop_ambient
from ui.components.breathing_modal import BreathingModal


class FocusPage(QWidget):
    timer_updated = pyqtSignal(str)
    session_finished = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")
        
        self.focus_active = False
        self.time_left = 25 * 60
        self.session_total = self.time_left
        self.current_label = "Pomodoro"
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Focus Mode")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Deep work flow states, ambient soundscapes, and concentration rhythms")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        self.btn_breathe = QPushButton("🧘 2m Mindful Break")
        self.btn_breathe.setObjectName("secondaryButton")
        self.btn_breathe.setMinimumHeight(38)
        self.btn_breathe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_breathe.clicked.connect(self.open_breathing_modal)
        install_button_press(self.btn_breathe)
        header.addWidget(self.btn_breathe)

        main_layout.addLayout(header)
        
        # Timer Display Card
        timer_container = create_card_frame(elevated=True)
        timer_container.setMinimumHeight(300)
        timer_layout = QVBoxLayout(timer_container)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.setContentsMargins(36, 42, 36, 36)
        timer_layout.setSpacing(10)

        self.pulse = QFrame()
        self.pulse.setObjectName("livePulse")
        self.pulse.setFixedSize(12, 12)

        mode_row = QHBoxLayout()
        mode_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label = QLabel("FOCUS ENGINE — READY")
        self.mode_label.setObjectName("metadataLabel")
        mode_row.addWidget(self.pulse)
        mode_row.addWidget(self.mode_label)
        
        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("metricValueLarge")
        self.time_label.setStyleSheet("font-size: 104px; font-weight: 850; color: #FFFFFF; letter-spacing: -0.5px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Ready for Deep Work")
        self.status_label.setStyleSheet("font-size: 18px; color: #7B7DFF; font-weight: 500;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        timer_layout.addLayout(mode_row)
        timer_layout.addWidget(self.time_label)
        timer_layout.addWidget(self.status_label)

        self.progress_track = QFrame()
        self.progress_track.setObjectName("softPanel")
        self.progress_track.setFixedHeight(8)
        self.progress_track.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.progress_layout = QHBoxLayout(self.progress_track)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)
        self.progress_fill = QFrame()
        self.progress_fill.setStyleSheet("background-color: #7EE7C6; border-radius: 4px;")
        self.progress_layout.addWidget(self.progress_fill)
        self.progress_layout.addStretch()
        self.progress_layout.setStretch(0, 100)
        self.progress_layout.setStretch(1, 1)
        timer_layout.addWidget(self.progress_track)
        
        main_layout.addWidget(timer_container)
        
        # Primary Controls Row
        controls = QHBoxLayout()
        controls.setSpacing(16)
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_start = QPushButton("Start Focus")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setMinimumWidth(160)
        self.btn_start.setMinimumHeight(46)
        self.btn_start.clicked.connect(self.toggle_focus)
        
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setMinimumWidth(110)
        self.btn_reset.setMinimumHeight(46)
        self.btn_reset.clicked.connect(self.reset_timer)
        
        install_button_hover(self.btn_start)
        install_button_press(self.btn_start)
        install_button_hover(self.btn_reset)
        install_button_press(self.btn_reset)
        
        controls.addWidget(self.btn_start)
        controls.addWidget(self.btn_reset)
        main_layout.addLayout(controls)

        # Ambient Audio & Presets Container
        ambient_card = create_card_frame()
        ambient_layout = QHBoxLayout(ambient_card)
        ambient_layout.setContentsMargins(20, 14, 20, 14)
        ambient_layout.setSpacing(16)

        ambient_lbl = QLabel("🎧 Ambient Audio:")
        ambient_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        ambient_layout.addWidget(ambient_lbl)

        self.audio_combo = QComboBox()
        self.audio_combo.addItems([
            "🔇 Pure Silence",
            "🌊 14Hz Alpha Drone",
            "🌧️ Calming Rain"
        ])
        self.audio_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-weight: 500;
            }
        """)
        self.audio_combo.currentIndexChanged.connect(self._on_sound_changed)
        ambient_layout.addWidget(self.audio_combo)
        ambient_layout.addStretch()

        presets_lbl = QLabel("Presets:")
        presets_lbl.setObjectName("mutedLabel")
        ambient_layout.addWidget(presets_lbl)

        preset_configs = [
            ("25m", 25, "Pomodoro"),
            ("50m", 50, "Deep Work"),
            ("90m", 90, "Flow"),
            ("5m Break", 5, "Quick Break"),
            ("15m Rest", 15, "Rest")
        ]
        for btn_text, mins, plabel in preset_configs:
            btn = QPushButton(btn_text)
            btn.setObjectName("segmentedButton")
            btn.clicked.connect(lambda checked, m=mins, l=plabel: self.set_preset(m, l))
            install_button_hover(btn)
            install_button_press(btn)
            ambient_layout.addWidget(btn)

        main_layout.addWidget(ambient_card)
        main_layout.addStretch()

    def on_show(self):
        fade_in(self)

    def open_breathing_modal(self):
        was_running = self.focus_active
        if was_running:
            self.toggle_focus()
        modal = BreathingModal(self, duration_seconds=120)
        modal.exec()

    def _on_sound_changed(self, idx):
        if not self.focus_active:
            return
        self._apply_audio_mode()

    def _apply_audio_mode(self):
        idx = self.audio_combo.currentIndex()
        if idx == 1:
            play_ambient("binaural")
        elif idx == 2:
            play_ambient("rain")
        else:
            stop_ambient()

    def set_preset(self, mins, label="Focus"):
        if not self.focus_active:
            self.time_left = mins * 60
            self.session_total = self.time_left
            self.current_label = label
            self.mode_label.setText(f"FOCUS ENGINE — {label.upper()}")
            self.update_display()
            fade_in(self.status_label, duration=140)

    def toggle_focus(self):
        if self.focus_active:
            self.timer.stop()
            self.focus_active = False
            stop_ambient()
            self.btn_start.setText("Resume Focus")
            self.status_label.setText("Paused")
            self.status_label.setStyleSheet("font-size: 18px; color: #FBBF24; font-weight: 500;")
            self.pulse.setStyleSheet("background-color: rgba(251, 191, 36, 0.24); border: 1px solid rgba(251, 191, 36, 0.45); border-radius: 6px;")
            self.timer_updated.emit("")
            fade_in(self.status_label, duration=140)
        else:
            self.timer.start(1000)
            self.focus_active = True
            self._apply_audio_mode()
            self.btn_start.setText("Pause")
            self.status_label.setText("Deep Work Session Running")
            self.status_label.setStyleSheet("font-size: 18px; color: #7EE7C6; font-weight: 500;")
            self.pulse.setStyleSheet("background-color: rgba(126, 231, 198, 0.26); border: 1px solid rgba(126, 231, 198, 0.55); border-radius: 6px;")
            self.mode_label.setText("FOCUS ENGINE — ACTIVE")
            mins, secs = divmod(self.time_left, 60)
            self.timer_updated.emit(f"{mins:02}:{secs:02}")
            fade_in(self.status_label, duration=140)

    def reset_timer(self):
        self.timer.stop()
        self.focus_active = False
        stop_ambient()
        self.time_left = 25 * 60
        self.session_total = self.time_left
        self.btn_start.setText("Start Focus")
        self.status_label.setText("Ready for Deep Work")
        self.status_label.setStyleSheet("font-size: 18px; color: #7B7DFF; font-weight: 500;")
        self.pulse.setStyleSheet("background-color: rgba(126, 231, 198, 0.18); border: 1px solid rgba(126, 231, 198, 0.35); border-radius: 6px;")
        self.mode_label.setText("FOCUS ENGINE — READY")
        self.timer_updated.emit("")
        self.update_display()

    def tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_updated.emit(f"{mins:02}:{secs:02}")
            self.update_display()
        else:
            completed_duration = self.session_total
            self.reset_timer()
            self.status_label.setText("🎉 Focus Session Completed!")
            self.status_label.setStyleSheet("font-size: 20px; color: #7EE7C6; font-weight: 700;")
            
            try:
                QApplication.beep()
            except Exception:
                pass

            try:
                log_focus_session(completed_duration, "completed")
                mins_done = completed_duration // 60
                log_notification("Focus", f"Completed a {mins_done}-minute focus sprint!")
            except Exception as e:
                print(f"[FocusPage] Log error: {e}")

            self.session_finished.emit(completed_duration)

    def update_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.time_label.setText(f"{mins:02}:{secs:02}")
        total = max(1, self.session_total)
        complete = int(((total - self.time_left) / total) * 100)
        self.progress_layout.setStretch(0, max(1, complete))
        self.progress_layout.setStretch(1, max(1, 100 - complete))
