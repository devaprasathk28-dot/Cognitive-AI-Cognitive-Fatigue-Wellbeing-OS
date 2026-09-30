from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from PyQt6.QtCore import Qt
from ui.components.core_ui import create_card_frame, fade_in
from storage.db import get_connection, fatigue_to_focus_score


class InsightsPage(QWidget):
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
        layout = QVBoxLayout(inner)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 60)
        
        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("AI Insights")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Automated behavioral pattern analysis and digital energy intelligence")
        subtitle.setObjectName("mutedLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)
        
        # Grid for insights
        self.grid = QGridLayout()
        self.grid.setSpacing(24)
        layout.addLayout(self.grid)
        layout.addStretch()
        
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def on_show(self):
        fade_in(self)
        self.refresh_insights()

    def refresh_insights(self):
        # Clear existing grid widgets
        while self.grid.count() > 0:
            item = self.grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        insights = self._analyze_database()

        for i, card_info in enumerate(insights):
            row = i // 2
            col = i % 2
            card = create_card_frame()
            card.setStyleSheet(f"border-left: 4px solid {card_info['color']};")
            
            l = QVBoxLayout(card)
            l.setSpacing(10)
            l.setContentsMargins(22, 20, 22, 20)
            
            hdr = QHBoxLayout()
            icon_lbl = QLabel(card_info["icon"])
            icon_lbl.setStyleSheet("font-size: 18px;")
            title_lbl = QLabel(card_info["title"], objectName="sectionTitle")
            title_lbl.setStyleSheet(f"color: {card_info['color']}; font-weight: 700;")
            
            hdr.addWidget(icon_lbl)
            hdr.addWidget(title_lbl)
            hdr.addStretch()
            l.addLayout(hdr)
            
            desc = QLabel(card_info["text"])
            desc.setWordWrap(True)
            desc.setStyleSheet("font-size: 15px; color: #E2E2E8; line-height: 1.5;")
            l.addWidget(desc)

            tip = QLabel(f"Recommendation: {card_info['tip']}")
            tip.setWordWrap(True)
            tip.setStyleSheet("font-size: 13px; color: rgba(224, 229, 240, 0.65); font-style: italic;")
            l.addWidget(tip)

            self.grid.addWidget(card, row, col)

    def _analyze_database(self):
        insights = []
        try:
            conn = get_connection()
            c = conn.cursor()

            # 1. Distraction & Context Switching Pattern
            c.execute("""
                SELECT AVG(duration_sec), COUNT(*)
                FROM sessions
                WHERE timestamp >= datetime('now', '-7 days', 'localtime')
            """)
            avg_row = c.fetchone()
            avg_dur = avg_row[0] or 180
            total_sessions = avg_row[1] or 0
            avg_mins = max(1, int(avg_dur // 60))

            if avg_mins < 15:
                distract_text = f"You switch active application context every ~{avg_mins} minutes across {total_sessions} logged sessions this week."
                distract_tip = "Try working in structured 25-minute Pomodoro blocks to minimize context penalty."
            else:
                distract_text = f"Solid concentration rhythm detected. Average sustained session length is {avg_mins} minutes."
                distract_tip = "Maintain this deep work momentum and take scheduled micro-pauses."

            insights.append({
                "title": "Context Switching Rhythm",
                "icon": "🔄",
                "color": "#7B7DFF",
                "text": distract_text,
                "tip": distract_tip
            })

            # 2. Peak Energy Window
            c.execute("""
                SELECT strftime('%H', timestamp) as hr, AVG(fatigue_score), COUNT(*)
                FROM sessions
                GROUP BY hr
                HAVING COUNT(*) >= 2
                ORDER BY AVG(fatigue_score) ASC
                LIMIT 1
            """)
            peak_row = c.fetchone()
            if peak_row:
                peak_hr = int(peak_row[0])
                peak_focus = fatigue_to_focus_score(peak_row[1])
                peak_text = f"Your highest cognitive stamina occurs around {peak_hr:02d}:00 with an average focus score of {peak_focus}%."
                peak_tip = f"Reserve {peak_hr:02d}:00 - {(peak_hr+2)%24:02d}:00 for high-complexity engineering or creative tasks."
            else:
                peak_text = "Data collection in progress. Peak focus hours typically stabilize between 9:00 AM and 11:30 AM."
                peak_tip = "Continue normal daily workflow to calibrate your neural baseline."

            insights.append({
                "title": "Peak Stamina Window",
                "icon": "⚡",
                "color": "#7EE7C6",
                "text": peak_text,
                "tip": peak_tip
            })

            # 3. Afternoon Fatigue Dip
            c.execute("""
                SELECT AVG(fatigue_score)
                FROM sessions
                WHERE CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 13 AND 16
            """)
            afternoon_row = c.fetchone()
            afternoon_fatigue = afternoon_row[0] if afternoon_row and afternoon_row[0] is not None else 0
            afternoon_score = fatigue_to_focus_score(afternoon_fatigue)

            if afternoon_score < 70:
                dip_text = f"Midday circadian dip detected: focus dips to {afternoon_score}% between 1:00 PM and 4:00 PM."
                dip_tip = "Schedule meetings, administrative tasks, or light review during this window."
            else:
                dip_text = f"Balanced energy pacing observed during the afternoon (focus index {afternoon_score}%)."
                dip_tip = "Hydrate and step away for a 5-minute movement break at 3:00 PM."

            insights.append({
                "title": "Circadian Energy Curve",
                "icon": "🌅",
                "color": "#FBBF24",
                "text": dip_text,
                "tip": dip_tip
            })

            # 4. Tool Correlation & Flow State
            c.execute("""
                SELECT app_name, category, SUM(duration_sec), AVG(fatigue_score)
                FROM sessions
                GROUP BY app_name
                ORDER BY SUM(duration_sec) DESC
                LIMIT 2
            """)
            app_rows = c.fetchall()
            if len(app_rows) >= 2:
                top_app1 = app_rows[0][0]
                top_app2 = app_rows[1][0]
                f1 = fatigue_to_focus_score(app_rows[0][3])
                f2 = fatigue_to_focus_score(app_rows[1][3])
                corr_text = f"Comparing primary apps: {top_app1} yields {f1}% focus, while {top_app2} yields {f2}% focus."
                corr_tip = f"Notice whether tool switching to {top_app2} aligns with fatigue spikes."
            elif len(app_rows) == 1:
                top_app = app_rows[0][0]
                corr_text = f"Primary tool usage is centered on {top_app}."
                corr_tip = "Use fullscreen or distraction-free mode to prolong deep concentration."
            else:
                corr_text = "Logging sessions to establish cross-application cognitive load correlations."
                corr_tip = "Ensure tracking runs in the background while you work."

            insights.append({
                "title": "Application Load Correlation",
                "icon": "🧠",
                "color": "#FF7A90",
                "text": corr_text,
                "tip": corr_tip
            })

            conn.close()
        except Exception as e:
            insights = [
                {
                    "title": "Context Switching Rhythm",
                    "icon": "🔄",
                    "color": "#7B7DFF",
                    "text": "Frequent context switching creates attention residue. Aim for 25-minute focus intervals.",
                    "tip": "Use Focus Mode to lock down distracting applications."
                },
                {
                    "title": "Peak Stamina Window",
                    "icon": "⚡",
                    "color": "#7EE7C6",
                    "text": "Morning hours (9 AM - 11 AM) exhibit the lowest fatigue build-up.",
                    "tip": "Tackle the day's hardest problem first."
                }
            ]

        return insights
