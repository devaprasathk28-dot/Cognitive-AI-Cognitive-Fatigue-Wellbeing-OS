from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent


class CommandPalette(QDialog):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(560)
        self.setFixedHeight(380)

        # Container
        container = QFrame(self)
        container.setObjectName("commandPaletteContainer")
        container.setStyleSheet("""
            QFrame#commandPaletteContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #121622, stop:1 #0B0E14);
                border: 1px solid rgba(126, 231, 198, 0.35);
                border-radius: 14px;
            }
        """)
        container.setGeometry(10, 10, 540, 360)

        # Shadow
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 180))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Search Input
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 16px;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or jump to page... (Esc to close)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 500;
                padding: 4px;
            }
        """)
        self.search_input.textChanged.connect(self._filter_items)
        input_row.addWidget(icon)
        input_row.addWidget(self.search_input, 1)
        layout.addLayout(input_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255, 255, 255, 0.08);")
        layout.addWidget(sep)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 8px;
                color: #E2E2E8;
                font-size: 14px;
                font-weight: 500;
            }
            QListWidget::item:selected {
                background: rgba(126, 231, 198, 0.15);
                color: #7EE7C6;
                border: 1px solid rgba(126, 231, 198, 0.35);
            }
        """)
        self.list_widget.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.list_widget, 1)

        # Footer Hint
        hint = QLabel("↑↓ Navigate   ↵ Execute   Esc Dismiss")
        hint.setStyleSheet("color: rgba(224, 229, 240, 0.4); font-size: 11px; font-weight: 600;")
        layout.addWidget(hint, alignment=Qt.AlignmentFlag.AlignRight)

        self._all_commands = [
            ("📊 Go to Dashboard", "nav", 0),
            ("🧠 View Cognitive Insights", "nav", 1),
            ("🎯 Start Focus Sprint (25m)", "focus_start", 25),
            ("⚡ Start Deep Work Sprint (50m)", "focus_start", 50),
            ("🌊 Enter Flow State (90m)", "focus_start", 90),
            ("🧘 Mindful 4-7-8 Breathing Break", "breathing_break", None),
            ("📈 View Analytics & Workload", "nav", 3),
            ("🤖 Chat with AI Coach", "nav", 4),
            ("🏆 Check Goals & Streaks", "nav", 5),
            ("🔔 View Notifications Feed", "nav", 6),
            ("⚙️ Open Preferences & Settings", "nav", 7),
            ("🛡️ Toggle Focus Shield", "toggle_focus", None),
            ("📑 Export Executive HTML Report", "export_report", None),
            ("🧹 Clear Notification History", "clear_notifs", None),
        ]

        self._populate_list(self._all_commands)

    def _populate_list(self, items):
        self.list_widget.clear()
        for label, action_type, payload in items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (action_type, payload))
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_items(self, query: str):
        q = query.lower().strip()
        if not q:
            filtered = self._all_commands
        else:
            filtered = [cmd for cmd in self._all_commands if q in cmd[0].lower()]
        self._populate_list(filtered)

    def _on_item_activated(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            action_type, payload = data
            self.action_triggered.emit(action_type, payload)
        self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr = self.list_widget.currentItem()
            if curr:
                self._on_item_activated(curr)
        elif event.key() == Qt.Key.Key_Down:
            curr_row = self.list_widget.currentRow()
            if curr_row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr_row + 1)
        elif event.key() == Qt.Key.Key_Up:
            curr_row = self.list_widget.currentRow()
            if curr_row > 0:
                self.list_widget.setCurrentRow(curr_row - 1)
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.clear()
        self.search_input.setFocus()
        if self.parent():
            # Center on parent window
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + (parent_geom.height() - self.height()) // 3
            self.move(x, y)
