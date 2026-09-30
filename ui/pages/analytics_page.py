import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout,
    QFrame, QPushButton, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from ui.widgets.charts import NativeBarChart
from ui.components.core_ui import create_card_frame, fade_in, create_badge, create_progress_bar
from analytics.analytics_manager import get_dashboard_metrics, get_weekly_summary
from storage.db import get_connection, fatigue_to_focus_score


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")
        self.range_days = 7

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(20)
        layout.setContentsMargins(36, 34, 36, 54)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(5)
        title = QLabel("Analytics")
        title.setObjectName("pageTitle")
        subtitle = QLabel("A dense operating view of focus, context, and digital energy.")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        header.addLayout(self._build_range_selector())
        layout.addLayout(header)

        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(14)
        self.metric_labels = {}
        for i, (key, label, value, caption) in enumerate([
            ("time", "Total Time", "0h", "tracked workload"),
            ("focus", "Avg Focus", "0%", "fatigue adjusted"),
            ("sessions", "Sessions", "0", "context switches"),
            ("top", "Top App", "--", "dominant tool"),
        ]):
            card, value_label = self._metric_card(label, value, caption)
            self.metric_labels[key] = value_label
            self.summary_grid.addWidget(card, 0, i)
        layout.addLayout(self.summary_grid)

        grid = QGridLayout()
        grid.setSpacing(18)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)

        trend_card = create_card_frame(elevated=True)
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(22, 20, 22, 20)
        trend_layout.setSpacing(14)
        trend_header = self._card_header("Usage Trend", "Minutes per day with hover tooltips")
        trend_header.addStretch()
        trend_header.addWidget(create_badge("LIVE", "#7EE7C6"))
        trend_layout.addLayout(trend_header)
        self.weekly_chart = NativeBarChart()
        trend_layout.addWidget(self.weekly_chart)
        grid.addWidget(trend_card, 0, 0, 1, 2)

        category_card = create_card_frame()
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(22, 20, 22, 20)
        category_layout.setSpacing(14)
        category_layout.addLayout(self._card_header("Category Mix", "Where attention is being spent"))
        self.category_chart = NativeBarChart()
        category_layout.addWidget(self.category_chart)
        category_layout.addLayout(self._legend_row())
        grid.addWidget(category_card, 1, 0)

        insight_card = create_card_frame()
        insight_layout = QVBoxLayout(insight_card)
        insight_layout.setContentsMargins(22, 20, 22, 20)
        insight_layout.setSpacing(14)
        insight_layout.addLayout(self._card_header("Productivity Intelligence", "Signals worth acting on"))
        self.insight_layout = QVBoxLayout()
        self.insight_layout.setSpacing(10)
        insight_layout.addLayout(self.insight_layout)
        insight_layout.addStretch()
        grid.addWidget(insight_card, 1, 1)

        apps_card = create_card_frame()
        apps_layout = QVBoxLayout(apps_card)
        apps_layout.setContentsMargins(22, 20, 22, 20)
        apps_layout.setSpacing(14)
        apps_layout.addLayout(self._card_header("Top Apps", "Ranked by active time"))
        self.app_list_layout = QVBoxLayout()
        self.app_list_layout.setSpacing(10)
        apps_layout.addLayout(self.app_list_layout)
        apps_layout.addStretch()
        grid.addWidget(apps_card, 2, 0)

        correlation_card = create_card_frame()
        correlation_layout = QVBoxLayout(correlation_card)
        correlation_layout.setContentsMargins(22, 20, 22, 20)
        correlation_layout.setSpacing(14)
        correlation_layout.addLayout(self._card_header("Activity Correlations", "How the week is leaning"))
        self.correlation_layout = QVBoxLayout()
        self.correlation_layout.setSpacing(10)
        correlation_layout.addLayout(self.correlation_layout)
        correlation_layout.addStretch()
        grid.addWidget(correlation_card, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        self.scroll.setWidget(inner)
        main_layout.addWidget(self.scroll)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(5000)
        self.update_charts()

    def _build_range_selector(self):
        wrapper = QHBoxLayout()
        wrapper.setSpacing(8)
        self.range_group = QButtonGroup(self)
        self.range_group.setExclusive(True)
        for label, days in [("7D", 7), ("14D", 14), ("30D", 30)]:
            btn = QPushButton(label)
            btn.setObjectName("segmentedButton")
            btn.setCheckable(True)
            btn.setChecked(days == self.range_days)
            btn.clicked.connect(lambda checked, d=days: self._set_range(d))
            self.range_group.addButton(btn)
            wrapper.addWidget(btn)

        self.btn_export = QPushButton("📑 Export Report")
        self.btn_export.setObjectName("secondaryButton")
        self.btn_export.setMinimumHeight(34)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.clicked.connect(self.export_report)
        wrapper.addWidget(self.btn_export)

        return wrapper

    def export_report(self):
        try:
            from analytics.report_generator import generate_executive_html_report
            import webbrowser
            path = generate_executive_html_report()
            webbrowser.open(f"file://{path}")
        except Exception as e:
            print(f"[AnalyticsPage] Export error: {e}")

    def _set_range(self, days):
        self.range_days = days
        self.update_charts()

    def _metric_card(self, title, value, caption):
        card = create_card_frame()
        card.setMinimumHeight(116)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(5)
        label = QLabel(title)
        label.setObjectName("metadataLabel")
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        cap = QLabel(caption)
        cap.setObjectName("metricCaption")
        layout.addWidget(label)
        layout.addWidget(value_label)
        layout.addStretch()
        layout.addWidget(cap)
        return card, value_label

    def _card_header(self, title, subtitle):
        header = QHBoxLayout()
        copy = QVBoxLayout()
        copy.setSpacing(3)
        t = QLabel(title)
        t.setObjectName("subsectionTitle")
        s = QLabel(subtitle)
        s.setObjectName("mutedLabel")
        copy.addWidget(t)
        copy.addWidget(s)
        header.addLayout(copy)
        return header

    def _legend_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        for color, text in [("#8D95FF", "Historical"), ("#7EE7C6", "Current peak")]:
            item = QHBoxLayout()
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            label = QLabel(text)
            label.setObjectName("metricCaption")
            item.addWidget(dot)
            item.addWidget(label)
            row.addLayout(item)
        row.addStretch()
        return row

    def update_charts(self):
        try:
            dash = get_dashboard_metrics()
            weekly = get_weekly_summary()
            daily = self._daily_usage(self.range_days)
            categories = self._category_usage(self.range_days)
            top_apps = self._top_apps(self.range_days)
            avg_focus = self._avg_focus(self.range_days)
            total_minutes = sum(daily.values())

            self.metric_labels["time"].setText(self._format_minutes(total_minutes))
            self.metric_labels["focus"].setText(f"{avg_focus}%")
            self.metric_labels["sessions"].setText(str(dash.get("sessions", 0)))
            self.metric_labels["top"].setText((top_apps[0][0] if top_apps else weekly.get("top_app", "--"))[:14])

            self.weekly_chart.setData(list(daily.keys()), list(daily.values()))
            self.category_chart.setData(list(categories.keys()), list(categories.values()))
            self._update_top_apps(top_apps)
            self._update_insights(categories, avg_focus, total_minutes)
            self._update_correlations(categories)
        except Exception as e:
            print(f"Analytics Update Error: {e}")

    def _daily_usage(self, days):
        today = datetime.date.today()
        date_range = [today - datetime.timedelta(days=i) for i in range(days - 1, -1, -1)]
        daily = {d.strftime("%Y-%m-%d"): 0 for d in date_range}
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date(timestamp), SUM(duration_sec)
            FROM sessions
            WHERE timestamp >= datetime('now', ?, 'localtime')
            GROUP BY date(timestamp)
            """,
            (f"-{days} days",),
        )
        for date_str, seconds in cursor.fetchall():
            if date_str in daily:
                daily[date_str] = (seconds or 0) // 60
        conn.close()
        if days <= 14:
            return {datetime.datetime.strptime(k, "%Y-%m-%d").strftime("%a"): v for k, v in daily.items()}
        return {datetime.datetime.strptime(k, "%Y-%m-%d").strftime("%d %b"): v for k, v in daily.items()}

    def _category_usage(self, days):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, SUM(duration_sec) as total
            FROM sessions
            WHERE timestamp >= datetime('now', ?, 'localtime')
            GROUP BY category
            ORDER BY total DESC
            LIMIT 7
            """,
            (f"-{days} days",),
        )
        data = {row[0] or "Unsorted": (row[1] or 0) // 60 for row in cursor.fetchall()}
        conn.close()
        return data

    def _top_apps(self, days):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT app_name, SUM(duration_sec) as total
            FROM sessions
            WHERE timestamp >= datetime('now', ?, 'localtime')
            GROUP BY app_name
            ORDER BY total DESC
            LIMIT 6
            """,
            (f"-{days} days",),
        )
        rows = [(row[0] or "Unknown", (row[1] or 0) // 60) for row in cursor.fetchall()]
        conn.close()
        return rows

    def _avg_focus(self, days):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT AVG(fatigue_score)
            FROM sessions
            WHERE timestamp >= datetime('now', ?, 'localtime')
            """,
            (f"-{days} days",),
        )
        row = cursor.fetchone()
        conn.close()
        fatigue = row[0] if row and row[0] is not None else 0
        return fatigue_to_focus_score(fatigue)

    def _update_top_apps(self, apps):
        self._clear_layout(self.app_list_layout)
        max_val = max([mins for _, mins in apps], default=1)
        if not apps:
            self.app_list_layout.addWidget(self._empty_state("No app sessions captured yet."))
            return
        for index, (app, minutes) in enumerate(apps, start=1):
            row = QFrame()
            row.setObjectName("softPanel")
            row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            row.setToolTip(f"{app}: {minutes} minutes")
            layout = QVBoxLayout(row)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(7)
            top = QHBoxLayout()
            rank = QLabel(f"{index:02}")
            rank.setObjectName("metadataLabel")
            name = QLabel(app)
            name.setStyleSheet("font-size: 13px; font-weight: 750; color: #FFFFFF;")
            time = QLabel(f"{minutes}m")
            time.setObjectName("mutedLabel")
            top.addWidget(rank)
            top.addWidget(name)
            top.addStretch()
            top.addWidget(time)
            layout.addLayout(top)
            layout.addWidget(create_progress_bar((minutes / max_val) * 100, "#7781FF"))
            self.app_list_layout.addWidget(row)

    def _update_insights(self, categories, avg_focus, total_minutes):
        self._clear_layout(self.insight_layout)
        dominant = next(iter(categories.items()), ("No dominant category", 0))
        focus_copy = "Stable cognitive load" if avg_focus >= 70 else "Focus is under pressure"
        density = "High activity density" if total_minutes > self.range_days * 360 else "Moderate workload"
        for title, body, accent in [
            (focus_copy, f"Average focus is running at {avg_focus}% across the selected range.", "#7EE7C6" if avg_focus >= 70 else "#FBBF24"),
            ("Dominant context", f"{dominant[0]} leads your attention profile with {dominant[1]} minutes.", "#8D95FF"),
            (density, f"{self._format_minutes(total_minutes)} tracked in {self.range_days} days.", "#FF7A90" if total_minutes > self.range_days * 420 else "#7EE7C6"),
        ]:
            self.insight_layout.addWidget(self._insight_row(title, body, accent))

    def _update_correlations(self, categories):
        self._clear_layout(self.correlation_layout)
        total = max(1, sum(categories.values()))
        if not categories:
            self.correlation_layout.addWidget(self._empty_state("Correlations appear after usage data is collected."))
            return
        for category, minutes in list(categories.items())[:5]:
            share = int((minutes / total) * 100)
            row = QFrame()
            row.setObjectName("softPanel")
            row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            layout = QVBoxLayout(row)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(7)
            top = QHBoxLayout()
            name = QLabel(category)
            name.setStyleSheet("font-size: 13px; font-weight: 750;")
            share_label = QLabel(f"{share}%")
            share_label.setObjectName("mutedLabel")
            top.addWidget(name)
            top.addStretch()
            top.addWidget(share_label)
            layout.addLayout(top)
            layout.addWidget(create_progress_bar(share, "#7EE7C6" if share < 35 else "#FBBF24"))
            self.correlation_layout.addWidget(row)

    def _insight_row(self, title, body, accent):
        row = QFrame()
        row.setObjectName("softPanel")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        marker = QFrame()
        marker.setFixedSize(8, 32)
        marker.setStyleSheet(f"background-color: {accent}; border-radius: 4px;")
        text = QVBoxLayout()
        text.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF;")
        b = QLabel(body)
        b.setWordWrap(True)
        b.setObjectName("mutedLabel")
        text.addWidget(t)
        text.addWidget(b)
        layout.addWidget(marker)
        layout.addLayout(text)
        return row

    def _empty_state(self, text):
        label = QLabel(text)
        label.setObjectName("mutedLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(72)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return label

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _format_minutes(self, minutes):
        hours, mins = divmod(int(minutes), 60)
        if hours <= 0:
            return f"{mins}m"
        return f"{hours}h {mins}m"

    def on_show(self):
        fade_in(self)
