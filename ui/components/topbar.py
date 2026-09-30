from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame


class TopBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(58)
        self.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0D1017, stop:1 #090B10);"
            "border-bottom: 1px solid rgba(255, 255, 255, 0.065);"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        pulse = QFrame()
        pulse.setFixedSize(9, 9)
        pulse.setStyleSheet("background-color: #7EE7C6; border-radius: 4px;")
        layout.addWidget(pulse)

        self.status = QLabel("Active")
        self.status.setObjectName("metadataLabel")
        self.status.setStyleSheet("color: #7EE7C6; border: none;")
        layout.addWidget(self.status)

        self.focus_timer_lbl = QLabel("00:00")
        self.focus_timer_lbl.setStyleSheet("color: #FBBF24; font-weight: 800; font-size: 13px; border: none;")
        self.focus_timer_lbl.hide()
        layout.addWidget(self.focus_timer_lbl)

        layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search insights...")
        self.search_input.setFixedWidth(230)
        self.search_input.setFixedHeight(34)
        layout.addWidget(self.search_input)

        self.notif_btn = self._top_button("🔔", "Notifications")
        layout.addWidget(self.notif_btn)

        self.profile_btn = self._top_button("⚙️", "Settings")
        layout.addWidget(self.profile_btn)

    def _top_button(self, text, tooltip):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(34, 34)
        btn.setObjectName("iconButton")
        return btn

    def set_focus_time(self, time_str: str):
        if time_str:
            self.focus_timer_lbl.setText(f"Focus {time_str}")
            self.focus_timer_lbl.show()
        else:
            self.focus_timer_lbl.hide()
