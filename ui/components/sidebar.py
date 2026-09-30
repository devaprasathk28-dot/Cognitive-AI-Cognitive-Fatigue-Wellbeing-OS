from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect
from ui.components.core_ui import install_button_press


class SidebarButton(QPushButton):
    def __init__(self, icon_str, text, is_active=False):
        super().__init__()
        self.icon_str = icon_str
        self.label = text
        self.compact = False
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        self.setChecked(is_active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setToolTip(text)
        self.refresh_text()
        install_button_press(self)

    def set_compact(self, compact):
        self.compact = compact
        self.refresh_text()

    def refresh_text(self):
        if self.compact:
            self.setText(f"  {self.icon_str}")
        else:
            self.setText(f"  {self.icon_str}    {self.label}")


class Sidebar(QFrame):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.expanded_width = 246
        self.collapsed_width = 78
        self.collapsed = False
        self.active_index = 0
        self.setMinimumWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)

        self.active_rail = QFrame(self)
        self.active_rail.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #7EE7C6, stop:1 #7781FF);"
            "border-radius: 2px;"
        )
        self.active_rail.setFixedWidth(3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(8)

        brand_row = QVBoxLayout()
        brand_row.setContentsMargins(12, 0, 8, 18)
        brand_row.setSpacing(2)
        self.brand = QLabel("Cognitive AI")
        self.brand.setObjectName("brandTitle")
        self.brand_subtitle = QLabel("WELLBEING OS")
        self.brand_subtitle.setObjectName("brandSubtitle")
        brand_row.addWidget(self.brand)
        brand_row.addWidget(self.brand_subtitle)
        layout.addLayout(brand_row)

        self.buttons = []
        pages = [
            ("📊", "Dashboard"),
            ("🧠", "Insights"),
            ("🎯", "Focus"),
            ("📈", "Analytics"),
            ("🤖", "AI Coach"),
            ("🏆", "Goals"),
            ("🔔", "Notifications"),
            ("⚙️", "Settings"),
        ]

        for i, (icon, name) in enumerate(pages):
            btn = SidebarButton(icon, name, is_active=(i == 0))
            btn.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self.collapse_btn = QPushButton("Collapse")
        self.collapse_btn.setObjectName("segmentedButton")
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        install_button_press(self.collapse_btn)
        layout.addWidget(self.collapse_btn)

        QTimer.singleShot(0, self._position_active_rail)

    def _on_button_clicked(self, index):
        self.set_active(index)
        self.page_changed.emit(index)

    def set_active(self, index):
        self.active_index = index
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self._position_active_rail(animated=True)

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        target = self.collapsed_width if self.collapsed else self.expanded_width
        for btn in self.buttons:
            btn.set_compact(self.collapsed)
        self.brand.setVisible(not self.collapsed)
        self.brand_subtitle.setVisible(not self.collapsed)
        self.collapse_btn.setText(">>" if self.collapsed else "Collapse")

        for prop in (b"minimumWidth", b"maximumWidth"):
            animation = QPropertyAnimation(self, prop, self)
            animation.setDuration(190)
            animation.setStartValue(self.width())
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            setattr(self, f"_width_anim_{prop.decode()}", animation)

        QTimer.singleShot(200, self._position_active_rail)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_active_rail()

    def _position_active_rail(self, animated=False):
        if not self.buttons or self.active_index >= len(self.buttons):
            return
        btn = self.buttons[self.active_index]
        target_y = btn.y() + 8
        target_h = max(22, btn.height() - 16)
        self.active_rail.raise_()
        if animated:
            animation = QPropertyAnimation(self.active_rail, b"geometry", self)
            animation.setDuration(160)
            animation.setStartValue(self.active_rail.geometry())
            animation.setEndValue(QRect(8, target_y, 3, target_h))
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            self._rail_anim = animation
        else:
            self.active_rail.setGeometry(8, target_y, 3, target_h)
