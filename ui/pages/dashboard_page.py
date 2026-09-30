import os
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QGridLayout
from PyQt6.QtCore import Qt, QTimer, QTime
from ui.components.core_ui import (
    create_card_frame, create_divider, fade_in,
    install_button_hover, install_button_press, animate_value_change
)
from ui.widgets.rings import CircularProgress
from ui.components.breathing_modal import BreathingModal
from monitor.settings_manager import load_settings, save_settings
from storage.db import (
    fatigue_to_focus_score, get_streak_count,
    get_today_deep_work_stats, log_notification
)

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")
        
        self.settings = load_settings()
        self.last_app = None
        self.activities = []
        self._last_focus_score = 0
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 60)

        # Header Row
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Your daily productivity overview")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        
        # Streak System Header Widget
        streak_card = QFrame()
        streak_card.setObjectName("card")
        streak_card.setStyleSheet("background-color: rgba(93, 95, 239, 0.1); border: 1px solid rgba(93, 95, 239, 0.3);")
        streak_layout = QHBoxLayout(streak_card)
        streak_layout.setContentsMargins(16, 8, 16, 8)
        self.streak_label = QLabel(f"🔥 {get_streak_count()} Day Streak")
        self.streak_label.setStyleSheet("font-weight: 700; color: #7B7DFF;")
        streak_layout.addWidget(self.streak_label)
        header.addWidget(streak_card)

        # Focus Mode Toggle Button (Phase 6)
        self.focus_toggle_btn = QPushButton()
        self.focus_toggle_btn.setObjectName("segmentedButton")
        self.focus_toggle_btn.setMinimumHeight(38)
        self.focus_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sync_focus_button_state()
        self.focus_toggle_btn.clicked.connect(self.toggle_focus_mode)
        install_button_press(self.focus_toggle_btn)
        header.addWidget(self.focus_toggle_btn)
        
        layout.addLayout(header)

        # ----------------------------------------------------
        # TOP ROW: Productivity Summary & Active Session
        # ----------------------------------------------------
        top_row = QHBoxLayout()
        top_row.setSpacing(24)

        # 1. Productivity Summary Card
        summary_card = create_card_frame()
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setSpacing(14)
        summary_layout.setContentsMargins(24, 20, 24, 20)
        
        sum_title = QLabel("Today's Productivity Engine")
        sum_title.setObjectName("sectionTitle")
        summary_layout.addWidget(sum_title)

        summary_body = QHBoxLayout()
        summary_body.setSpacing(24)

        # Interactive Progress Ring
        self.focus_ring = CircularProgress("Focus Stamina", "#7EE7C6")
        summary_body.addWidget(self.focus_ring)
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.val_focus = QLabel("0%")
        self.val_focus.setObjectName("metricValue")
        metrics_grid.addWidget(QLabel("Focus Index", objectName="mutedLabel"), 0, 0)
        metrics_grid.addWidget(self.val_focus, 1, 0)
        
        self.val_deep = QLabel("0h 0m")
        self.val_deep.setObjectName("metricValue")
        metrics_grid.addWidget(QLabel("Deep Work", objectName="mutedLabel"), 0, 1)
        metrics_grid.addWidget(self.val_deep, 1, 1)
        
        self.val_distract = QLabel("0")
        self.val_distract.setObjectName("metricValue")
        self.val_distract.setStyleSheet("color: #FF7A90;")
        metrics_grid.addWidget(QLabel("Distractions", objectName="mutedLabel"), 2, 0)
        metrics_grid.addWidget(self.val_distract, 3, 0)
        
        self.val_burnout = QLabel("Low")
        self.val_burnout.setObjectName("metricValue")
        self.val_burnout.setStyleSheet("color: #7EE7C6;")
        metrics_grid.addWidget(QLabel("Burnout Risk", objectName="mutedLabel"), 2, 1)
        metrics_grid.addWidget(self.val_burnout, 3, 1)
        
        summary_body.addLayout(metrics_grid, 1)
        summary_layout.addLayout(summary_body)
        top_row.addWidget(summary_card, 2)

        # 2. Active Session Widget
        session_card = create_card_frame()
        session_card.setStyleSheet("background-color: rgba(93, 95, 239, 0.05);")
        session_layout = QVBoxLayout(session_card)
        session_layout.setSpacing(12)
        session_layout.setContentsMargins(24, 24, 24, 24)
        
        sess_title = QLabel("Active Context")
        sess_title.setObjectName("sectionTitle")
        session_layout.addWidget(sess_title)
        
        self.app_icon = QLabel("💻")
        self.app_icon.setStyleSheet("font-size: 32px;")
        
        self.app_val = QLabel("Tracking...")
        self.app_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF;")
        
        self.cat_val = QLabel("Category: Initializing")
        self.cat_val.setObjectName("mutedLabel")
        
        session_layout.addWidget(self.app_icon)
        session_layout.addWidget(self.app_val)
        session_layout.addWidget(self.cat_val)
        session_layout.addStretch()
        
        self.intensity_bar = QFrame()
        self.intensity_bar.setFixedHeight(6)
        self.intensity_bar.setStyleSheet("background-color: #5D5FEF; border-radius: 3px; max-width: 80%;")
        session_layout.addWidget(QLabel("Focus Intensity", objectName="mutedLabel"))
        session_layout.addWidget(self.intensity_bar)
        
        top_row.addWidget(session_card, 1)
        layout.addLayout(top_row)

        # ----------------------------------------------------
        # MIDDLE ROW: AI Recommendations
        # ----------------------------------------------------
        ai_card = create_card_frame()
        ai_card.setStyleSheet("border-left: 4px solid #5D5FEF;")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(8)
        ai_layout.setContentsMargins(24, 20, 24, 20)
        
        ai_header = QHBoxLayout()
        ai_title = QLabel("✨ Smart AI Recommendation")
        ai_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #5D5FEF;")
        ai_header.addWidget(ai_title)
        ai_header.addStretch()

        self.btn_rec_break = QPushButton("🧘 2m Mindful Break")
        self.btn_rec_break.setObjectName("secondaryButton")
        self.btn_rec_break.setMinimumHeight(30)
        self.btn_rec_break.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rec_break.clicked.connect(self.open_guided_break)
        install_button_press(self.btn_rec_break)
        ai_header.addWidget(self.btn_rec_break)
        ai_layout.addLayout(ai_header)
        
        self.ai_rec = QLabel("Collect enough data to generate recommendations. Stay focused on your primary tasks.")
        self.ai_rec.setWordWrap(True)
        self.ai_rec.setStyleSheet("font-size: 16px; color: #E2E2E8; line-height: 1.4;")
        ai_layout.addWidget(self.ai_rec)
        
        layout.addWidget(ai_card)

        # ----------------------------------------------------
        # BOTTOM ROW: Timeline & Notifications
        # ----------------------------------------------------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)
        
        # Timeline
        timeline_card = create_card_frame()
        tl = QVBoxLayout(timeline_card)
        tl.setSpacing(16)
        tl.setContentsMargins(24, 24, 24, 24)
        tl_title = QLabel("Daily Focus Timeline")
        tl_title.setObjectName("sectionTitle")
        tl.addWidget(tl_title)
        
        self.timeline_list = QVBoxLayout()
        self.timeline_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.timeline_list.setSpacing(12)
        tl.addLayout(self.timeline_list)
        tl.addStretch()
        bottom_row.addWidget(timeline_card, 1)
        
        # Notifications Feed
        notif_card = create_card_frame()
        nl = QVBoxLayout(notif_card)
        nl.setSpacing(16)
        nl.setContentsMargins(24, 24, 24, 24)
        nl_title = QLabel("Live Activity Feed")
        nl_title.setObjectName("sectionTitle")
        nl.addWidget(nl_title)
        
        self.notifications_list = QVBoxLayout()
        self.notifications_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.notifications_list.setSpacing(12)
        nl.addLayout(self.notifications_list)
        nl.addStretch()
        bottom_row.addWidget(notif_card, 1)
        
        layout.addLayout(bottom_row)
        layout.addStretch()
        
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def _sync_focus_button_state(self):
        is_focus = self.settings.get("focus_mode", False)
        if is_focus:
            self.focus_toggle_btn.setText("🎯 Focus Mode: ON")
            self.focus_toggle_btn.setStyleSheet(
                "background-color: rgba(126, 231, 198, 0.18); color: #7EE7C6; "
                "border: 1px solid rgba(126, 231, 198, 0.45); font-weight: 700; border-radius: 8px; padding: 0 16px;"
            )
        else:
            self.focus_toggle_btn.setText("🎯 Focus Mode: OFF")
            self.focus_toggle_btn.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.04); color: #A0A5B5; "
                "border: 1px solid rgba(255, 255, 255, 0.08); font-weight: 600; border-radius: 8px; padding: 0 16px;"
            )

    def toggle_focus_mode(self):
        current = self.settings.get("focus_mode", False)
        new_state = not current
        self.settings["focus_mode"] = new_state
        save_settings(self.settings)
        self._sync_focus_button_state()
        
        status_text = "activated" if new_state else "deactivated"
        self.add_notification_item(f"Focus Mode {status_text}", "Alert" if new_state else "Info")

    def on_show(self):
        fade_in(self)
        self.refresh_stats()

    def refresh_stats(self):
        # Update streak
        self.streak_label.setText(f"🔥 {get_streak_count()} Day Streak")
        
        # Update today's deep work and distractions from SQLite
        stats = get_today_deep_work_stats()
        deep_sec = stats.get("deep_work_sec", 0)
        h = deep_sec // 3600
        m = (deep_sec % 3600) // 60
        self.val_deep.setText(f"{h}h {m}m")
        self.val_distract.setText(str(stats.get("distraction_count", 0)))

    def open_guided_break(self):
        modal = BreathingModal(self, duration_seconds=120)
        modal.exec()
        self.refresh_stats()

    def update_from_engine(self, data):
        # Update session widget
        app = data.get("app", "--")
        cat = data.get("category", "--")
        self.app_val.setText(app)
        self.cat_val.setText(f"Category: {cat}")
        
        # Map app to icon placeholder
        if cat == "Browsing": self.app_icon.setText("🌐")
        elif cat == "Development": self.app_icon.setText("💻")
        elif cat == "Entertainment": self.app_icon.setText("🍿")
        elif cat == "Communication": self.app_icon.setText("💬")
        else: self.app_icon.setText("⚡")
        
        # Metrics - Real Normalized Focus Score
        f = data.get("fatigue", 0)
        score = fatigue_to_focus_score(f)
        if hasattr(self, "focus_ring"):
            self.focus_ring.set_value(score)

        if score != self._last_focus_score:
            animate_value_change(self.val_focus, self._last_focus_score, score, duration=360, suffix="%")
            self._last_focus_score = score
        
        b = data.get("burnout", 0)
        try: b_val = float(b)
        except: b_val = 0
        if b_val < 0.3:
            self.val_burnout.setText("Low")
            self.val_burnout.setStyleSheet("color: #7EE7C6;")
        elif b_val < 0.7:
            self.val_burnout.setText("Medium")
            self.val_burnout.setStyleSheet("color: #FBBF24;")
        else:
            self.val_burnout.setText("High")
            self.val_burnout.setStyleSheet("color: #FF7A90;")
            
        # Update Timeline & Live Feed
        if app != self.last_app and app != "--":
            t = QTime.currentTime().toString("HH:mm")
            self.add_timeline_item(t, app, cat, score)
            self.add_notification_item(f"Switched to {app} ({cat})", "Info")
            self.last_app = app
            self.refresh_stats()
            
        # Update AI recommendation based on context
        try:
            f_float = float(f)
        except:
            f_float = 0.0
        self.update_ai_recommendation(cat, score, f_float)

    def update_ai_recommendation(self, cat, score, fatigue):
        if fatigue > 60 or (fatigue <= 1.0 and fatigue > 0.6):
            self.ai_rec.setText("Your cognitive load is peaking. We strongly recommend stepping away for a 10-minute micro-break to restore mental agility.")
        elif cat in ["Entertainment", "Gaming"]:
            self.ai_rec.setText("You're engaged in a high-dopamine app. Ensure this is an intentional pause to protect your focus momentum.")
        elif cat in ["Development", "Writing", "Work"] and score >= 75:
            self.ai_rec.setText("You are in a prime deep work state. Keep distractions away and maintain this flow.")
        elif score < 50:
            self.ai_rec.setText("Your focus is dropping. Try a quick 2-minute breathing exercise or switch to a lower-effort task.")
        else:
            self.ai_rec.setText("Steady workload pacing detected. Maintain current rhythm and stay hydrated.")

    def add_timeline_item(self, time_str, app, cat, score):
        item = QFrame()
        l = QHBoxLayout(item)
        l.setContentsMargins(0, 0, 0, 0)
        
        t_lbl = QLabel(time_str)
        t_lbl.setObjectName("mutedLabel")
        t_lbl.setFixedWidth(40)
        
        dot = QLabel("●")
        if score > 80: dot.setStyleSheet("color: #7EE7C6; font-size: 16px;")
        elif score > 50: dot.setStyleSheet("color: #FBBF24; font-size: 16px;")
        else: dot.setStyleSheet("color: #FF7A90; font-size: 16px;")
            
        app_lbl = QLabel(f"{app} ({cat})")
        app_lbl.setStyleSheet("font-weight: 500; font-size: 14px;")
        
        l.addWidget(t_lbl)
        l.addWidget(dot)
        l.addWidget(app_lbl)
        l.addStretch()
        
        self.timeline_list.insertWidget(0, item)
        while self.timeline_list.count() > 6:
            w = self.timeline_list.takeAt(self.timeline_list.count()-1)
            if w and w.widget(): w.widget().deleteLater()

    def add_notification_item(self, text, priority="Info", persist=True):
        if persist:
            try:
                log_notification(priority, text)
            except Exception:
                pass

        item = QFrame()
        item.setStyleSheet("background: rgba(255,255,255,0.02); border-radius: 8px; padding: 10px;")
        l = QHBoxLayout(item)
        l.setContentsMargins(0, 0, 0, 0)
        
        icon = QLabel("💡" if priority == "Info" else "⚠️")
        msg = QLabel(text)
        msg.setStyleSheet("font-size: 13px; color: #E2E2E8;")
        
        l.addWidget(icon)
        l.addWidget(msg)
        l.addStretch()
        
        self.notifications_list.insertWidget(0, item)
        while self.notifications_list.count() > 5:
            w = self.notifications_list.takeAt(self.notifications_list.count()-1)
            if w and w.widget(): w.widget().deleteLater()
