from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt
from ui.components.core_ui import fade_in, create_card_frame, install_button_press
from storage.db import get_notifications, clear_notifications


class NotificationsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        inner = QWidget()
        self.layout = QVBoxLayout(inner)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(40, 40, 40, 60)
        
        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Notifications")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Activity alerts, focus achievements, and wellness suggestions")
        subtitle.setObjectName("mutedLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.setObjectName("segmentedButton")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.on_clear_all)
        install_button_press(self.clear_btn)
        header.addWidget(self.clear_btn)

        self.layout.addLayout(header)

        # Dynamic Notification Container
        self.feed_layout = QVBoxLayout()
        self.feed_layout.setSpacing(12)
        self.layout.addLayout(self.feed_layout)
        
        self.layout.addStretch()
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def on_show(self):
        fade_in(self)
        self.load_notifications()

    def on_clear_all(self):
        clear_notifications()
        self.load_notifications()

    def load_notifications(self):
        # Clear existing items in feed
        while self.feed_layout.count() > 0:
            item = self.feed_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        notifs = get_notifications(limit=40)

        if not notifs:
            empty_card = create_card_frame()
            el = QVBoxLayout(empty_card)
            el.setContentsMargins(32, 36, 32, 36)
            el.setAlignment(Qt.AlignmentFlag.AlignCenter)
            el.setSpacing(8)
            
            icon = QLabel("🔔")
            icon.setStyleSheet("font-size: 36px;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            t = QLabel("All Caught Up")
            t.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            d = QLabel("You have no pending alerts. Break recommendations and switch notifications will appear here in real time.")
            d.setStyleSheet("color: rgba(224, 229, 240, 0.6); font-size: 14px; text-align: center;")
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            d.setWordWrap(True)
            
            el.addWidget(icon)
            el.addWidget(t)
            el.addWidget(d)
            self.feed_layout.addWidget(empty_card)
            return

        for n in notifs:
            priority = n.get("priority", "Info")
            msg = n.get("message", "")
            timestamp = n.get("timestamp", "")
            
            # Format display time
            time_display = timestamp.split("T")[-1][:5] if "T" in timestamp else timestamp.split()[-1][:5] if " " in timestamp else timestamp

            color = "#7EE7C6"
            icon_str = "💡"
            if priority in ["Alert", "Warning", "High"]:
                color = "#FF7A90"
                icon_str = "⚠️"
            elif priority in ["Focus", "Goal"]:
                color = "#7B7DFF"
                icon_str = "🎯"
            elif priority in ["Streak"]:
                color = "#FBBF24"
                icon_str = "🔥"

            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(f"border-left: 4px solid {color}; border-radius: 8px;")
            
            l = QVBoxLayout(card)
            l.setContentsMargins(18, 14, 18, 14)
            l.setSpacing(6)
            
            hdr = QHBoxLayout()
            t_lbl = QLabel(f"{icon_str}  {priority}")
            t_lbl.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {color};")
            time_lbl = QLabel(time_display)
            time_lbl.setObjectName("mutedLabel")
            
            hdr.addWidget(t_lbl)
            hdr.addStretch()
            hdr.addWidget(time_lbl)
            
            d_lbl = QLabel(msg)
            d_lbl.setStyleSheet("color: #E2E2E8; font-size: 14px; line-height: 1.4;")
            d_lbl.setWordWrap(True)
            
            l.addLayout(hdr)
            l.addWidget(d_lbl)
            self.feed_layout.addWidget(card)
