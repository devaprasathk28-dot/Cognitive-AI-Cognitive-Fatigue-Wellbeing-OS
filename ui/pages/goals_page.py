from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt
from ui.components.core_ui import create_card_frame, fade_in
from monitor.settings_manager import load_settings
from storage.db import get_streak_count, get_today_deep_work_stats, get_connection


class GoalsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")
        self.settings = load_settings()

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

        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Goals & Streaks")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Track daily consistency, focus milestones, and habit growth")
        subtitle.setObjectName("mutedLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        
        # Streak Badge
        streak_badge = QFrame()
        streak_badge.setStyleSheet("background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 8px;")
        badge_layout = QHBoxLayout(streak_badge)
        badge_layout.setContentsMargins(16, 8, 16, 8)
        self.streak_lbl = QLabel(f"🔥 {get_streak_count()} Day Focus Streak")
        self.streak_lbl.setStyleSheet("color: #FBBF24; font-weight: 600; font-size: 15px;")
        badge_layout.addWidget(self.streak_lbl)
        header.addWidget(streak_badge, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header)

        # Progress Grid
        grid = QGridLayout()
        grid.setSpacing(24)

        # Goal 1: Deep Work
        g1_card = create_card_frame()
        g1_layout = QVBoxLayout(g1_card)
        g1_layout.setSpacing(12)
        g1_header = QHBoxLayout()
        g1_header.addWidget(QLabel("🎯 Deep Work Target", objectName="sectionTitle"))
        g1_header.addStretch()
        self.g1_val_lbl = QLabel("0 / 5 Hours", objectName="mutedLabel")
        g1_header.addWidget(self.g1_val_lbl)
        g1_layout.addLayout(g1_header)
        
        self.g1_prog = QProgressBar()
        self.g1_prog.setFixedHeight(8)
        self.g1_prog.setValue(0)
        self.g1_prog.setTextVisible(False)
        self.g1_prog.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.05); border-radius: 4px; } QProgressBar::chunk { background-color: #5D5FEF; border-radius: 4px; }")
        g1_layout.addWidget(self.g1_prog)
        grid.addWidget(g1_card, 0, 0)

        # Goal 2: Distraction Limit
        g2_card = create_card_frame()
        g2_layout = QVBoxLayout(g2_card)
        g2_layout.setSpacing(12)
        g2_header = QHBoxLayout()
        g2_header.addWidget(QLabel("🛑 Distraction Cap", objectName="sectionTitle"))
        g2_header.addStretch()
        self.g2_val_lbl = QLabel("0 / 60 Mins", objectName="mutedLabel")
        g2_header.addWidget(self.g2_val_lbl)
        g2_layout.addLayout(g2_header)
        
        self.g2_prog = QProgressBar()
        self.g2_prog.setFixedHeight(8)
        self.g2_prog.setValue(0)
        self.g2_prog.setTextVisible(False)
        self.g2_prog.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.05); border-radius: 4px; } QProgressBar::chunk { background-color: #7EE7C6; border-radius: 4px; }")
        g2_layout.addWidget(self.g2_prog)
        grid.addWidget(g2_card, 0, 1)

        # Goal 3: Screen Time Budget
        g3_card = create_card_frame()
        g3_layout = QVBoxLayout(g3_card)
        g3_layout.setSpacing(12)
        g3_header = QHBoxLayout()
        g3_header.addWidget(QLabel("⏱️ Daily Screen Time Budget", objectName="sectionTitle"))
        g3_header.addStretch()
        self.g3_val_lbl = QLabel("0 / 8 Hours", objectName="mutedLabel")
        g3_header.addWidget(self.g3_val_lbl)
        g3_layout.addLayout(g3_header)
        
        self.g3_prog = QProgressBar()
        self.g3_prog.setFixedHeight(8)
        self.g3_prog.setValue(0)
        self.g3_prog.setTextVisible(False)
        self.g3_prog.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.05); border-radius: 4px; } QProgressBar::chunk { background-color: #FBBF24; border-radius: 4px; }")
        g3_layout.addWidget(self.g3_prog)
        grid.addWidget(g3_card, 1, 0, 1, 2)

        layout.addLayout(grid)
        
        # Milestones Section
        m_label = QLabel("Achievements & Milestones")
        m_label.setObjectName("sectionTitle")
        layout.addWidget(m_label)
        
        m_card = create_card_frame()
        self.m_layout = QHBoxLayout(m_card)
        self.m_layout.setSpacing(24)
        layout.addWidget(m_card)

        layout.addStretch()

        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def on_show(self):
        fade_in(self)
        self.refresh_goals()

    def refresh_goals(self):
        self.settings = load_settings()
        streak = get_streak_count()
        self.streak_lbl.setText(f"🔥 {streak} Day Focus Streak")

        stats = get_today_deep_work_stats()
        deep_sec = stats.get("deep_work_sec", 0)
        distract_cnt = stats.get("distraction_count", 0)
        total_screen_sec = stats.get("total_screen_sec", 0)

        # 1. Deep work target
        target_focus_h = self.settings.get("goal_focus_hours", 5)
        current_focus_h = deep_sec / 3600.0
        self.g1_val_lbl.setText(f"{current_focus_h:.1f} / {target_focus_h} Hours")
        pct_focus = min(100, int((current_focus_h / max(0.5, target_focus_h)) * 100))
        self.g1_prog.setValue(pct_focus)

        # 2. Distraction limit
        limit_distract_mins = self.settings.get("goal_distraction_mins", 60)
        est_distract_mins = distract_cnt * 3
        self.g2_val_lbl.setText(f"{est_distract_mins} / {limit_distract_mins} Mins")
        pct_distract = min(100, int((est_distract_mins / max(1, limit_distract_mins)) * 100))
        self.g2_prog.setValue(pct_distract)
        if pct_distract > 85:
            self.g2_prog.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.05); border-radius: 4px; } QProgressBar::chunk { background-color: #FF7A90; border-radius: 4px; }")
        else:
            self.g2_prog.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.05); border-radius: 4px; } QProgressBar::chunk { background-color: #7EE7C6; border-radius: 4px; }")

        # 3. Screen time budget
        budget_screen_h = self.settings.get("goal_screen_time_hours", 8)
        current_screen_h = total_screen_sec / 3600.0
        self.g3_val_lbl.setText(f"{current_screen_h:.1f} / {budget_screen_h} Hours")
        pct_screen = min(100, int((current_screen_h / max(1, budget_screen_h)) * 100))
        self.g3_prog.setValue(pct_screen)

        # Total all-time deep work hours query
        total_deep_hours = 0
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT COALESCE(SUM(duration_sec), 0) FROM sessions WHERE category IN ('Development', 'Work', 'Productivity', 'Writing')")
            row = c.fetchone()
            if row:
                total_deep_hours = (row[0] or 0) / 3600.0
            conn.close()
        except Exception:
            pass

        # Milestones
        while self.m_layout.count() > 0:
            item = self.m_layout.takeAt(0)
            if item and item.layout():
                while item.layout().count() > 0:
                    sub = item.layout().takeAt(0)
                    if sub and sub.widget(): sub.widget().deleteLater()
            elif item and item.widget():
                item.widget().deleteLater()

        milestones = [
            ("🏆", "First Session", total_deep_hours > 0.05),
            ("⚡", "Deep Flow (10h)", total_deep_hours >= 10),
            ("🔥", "3-Day Streak", streak >= 3),
            ("🧘", "Iron Focus (7d)", streak >= 7),
        ]

        for icon, name, done in milestones:
            badge = QVBoxLayout()
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            i_lbl = QLabel(icon)
            i_lbl.setStyleSheet(f"font-size: 32px; opacity: {1.0 if done else 0.25};")
            i_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            n_lbl = QLabel(name)
            n_lbl.setStyleSheet(f"color: {'#7EE7C6' if done else '#6E6E7A'}; font-size: 13px; font-weight: {'700' if done else '400'};")
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            badge.addWidget(i_lbl)
            badge.addWidget(n_lbl)
            self.m_layout.addLayout(badge)
