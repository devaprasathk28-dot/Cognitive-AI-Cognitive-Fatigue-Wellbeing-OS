import json
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QCheckBox,
    QPushButton, QGridLayout, QSlider, QComboBox, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from ui.components.core_ui import create_card_frame, fade_in, install_button_press
from monitor.settings_manager import load_settings, save_settings


class SettingsPage(QWidget):
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
        layout.setSpacing(20)
        layout.setContentsMargins(36, 34, 36, 54)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(5)
        title = QLabel("Preferences")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Tune privacy, focus behavior, appearance, and data ownership.")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save)
        install_button_press(self.save_btn)
        header.addWidget(self.save_btn)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(18)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._privacy_card(), 0, 0)
        grid.addWidget(self._wellness_card(), 0, 1)
        grid.addWidget(self._appearance_card(), 1, 0)
        grid.addWidget(self._personalization_card(), 1, 1)
        grid.addWidget(self._data_card(), 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def _privacy_card(self):
        card, body = self._section_card("Tracking & Privacy", "Local-first intelligence controls")
        self.ai_toggle = QCheckBox("Enabled")
        self.ai_toggle.setChecked(self.settings.get("ai_enabled", True))
        body.addWidget(self._preference_row(
            "Local AI processing",
            "Analyze behavior on-device for coach recommendations.",
            self.ai_toggle,
        ))

        self.dist_toggle = QCheckBox("Enabled")
        self.dist_toggle.setChecked(self.settings.get("distraction_ai", True))
        body.addWidget(self._preference_row(
            "Distraction pattern detection",
            "Detect repeated context switching and attention drift.",
            self.dist_toggle,
        ))

        self.autostart_toggle = QCheckBox("Enabled")
        self.autostart_toggle.setChecked(self.settings.get("auto_start", False))
        body.addWidget(self._preference_row(
            "Launch at sign-in",
            "Start quietly in the background when Windows starts.",
            self.autostart_toggle,
        ))
        body.addStretch()
        return card

    def _wellness_card(self):
        card, body = self._section_card("Notifications & Wellness", "How assertive the system should be")
        self.notif_toggle = QCheckBox("Enabled")
        self.notif_toggle.setChecked(self.settings.get("notifications", True))
        body.addWidget(self._preference_row(
            "Smart break reminders",
            "Use fatigue and session intensity to time wellness nudges.",
            self.notif_toggle,
        ))

        self.strict_toggle = QCheckBox("Enabled")
        self.strict_toggle.setChecked(self.settings.get("strict_mode", False))
        body.addWidget(self._preference_row(
            "Strict focus protection",
            "Block distracting apps during protected focus sessions.",
            self.strict_toggle,
        ))

        self.focus_slider, self.focus_value = self._slider_control(
            self.settings.get("focus_duration", 45), 15, 120, "min"
        )
        body.addWidget(self._preference_row(
            "Default focus duration",
            "The starting length for deep work sessions.",
            self.focus_slider,
            self.focus_value,
        ))

        self.break_slider, self.break_value = self._slider_control(
            self.settings.get("break_duration", 10), 3, 30, "min"
        )
        body.addWidget(self._preference_row(
            "Recovery break duration",
            "Recommended reset length after demanding sessions.",
            self.break_slider,
            self.break_value,
        ))
        body.addStretch()
        return card

    def _appearance_card(self):
        card, body = self._section_card("Appearance", "Desktop-native visual comfort")
        self.theme_combo = self._combo(["Midnight", "Graphite", "High contrast"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Midnight"))
        body.addWidget(self._preference_row(
            "Theme",
            "Choose the visual atmosphere used across the app.",
            self.theme_combo,
        ))

        self.density_combo = self._combo(["Comfortable", "Compact", "Spacious"])
        self.density_combo.setCurrentText(self.settings.get("density", "Comfortable"))
        body.addWidget(self._preference_row(
            "Interface density",
            "Adjust spacing rhythm for dashboards and lists.",
            self.density_combo,
        ))

        self.accent_combo = self._combo(["Iris", "Mint", "Amber", "Rose"])
        self.accent_combo.setCurrentText(self.settings.get("accent", "Iris"))
        body.addWidget(self._preference_row(
            "Accent color",
            "Personalize highlights, chart peaks, and active states.",
            self.accent_combo,
        ))
        body.addStretch()
        return card

    def _personalization_card(self):
        card, body = self._section_card("Personalization", "Coach behavior and daily goals")
        self.coach_combo = self._combo(["Calm", "Direct", "Analytical"])
        self.coach_combo.setCurrentText(self.settings.get("coach_style", "Calm"))
        body.addWidget(self._preference_row(
            "AI coach style",
            "Control how recommendations are phrased.",
            self.coach_combo,
        ))

        self.goal_focus_slider, self.goal_focus_value = self._slider_control(
            self.settings.get("goal_focus_hours", 5), 1, 10, "h"
        )
        body.addWidget(self._preference_row(
            "Daily focus goal",
            "Target amount of high-quality deep work.",
            self.goal_focus_slider,
            self.goal_focus_value,
        ))

        self.distraction_slider, self.distraction_value = self._slider_control(
            self.settings.get("goal_distraction_mins", 75), 10, 180, "min"
        )
        body.addWidget(self._preference_row(
            "Distraction budget",
            "Daily upper bound for low-value app usage.",
            self.distraction_slider,
            self.distraction_value,
        ))
        body.addStretch()
        return card

    def _data_card(self):
        card, body = self._section_card("Data & Backups", "Ownership controls for preferences and local state")
        actions = QGridLayout()
        actions.setSpacing(12)
        for i, (label, desc, handler) in enumerate([
            ("Export Preferences", "Save your current preferences as JSON.", self.export_settings),
            ("Import Preferences", "Restore preferences from a JSON file.", self.import_settings),
            ("Create Backup", "Copy settings into the local data folder.", self.create_backup),
        ]):
            row = QFrame()
            row.setObjectName("preferenceRow")
            row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(14, 12, 14, 12)
            row_layout.setSpacing(10)
            t = QLabel(label)
            t.setStyleSheet("font-size: 14px; font-weight: 800; color: #FFFFFF;")
            d = QLabel(desc)
            d.setObjectName("mutedLabel")
            d.setWordWrap(True)
            btn = QPushButton(label.split()[0])
            btn.setMinimumHeight(34)
            btn.clicked.connect(handler)
            install_button_press(btn)
            row_layout.addWidget(t)
            row_layout.addWidget(d)
            row_layout.addWidget(btn)
            actions.addWidget(row, 0, i)
        body.addLayout(actions)
        self.status_label = QLabel("Preferences are stored locally in user_settings.json.")
        self.status_label.setObjectName("mutedLabel")
        body.addWidget(self.status_label)
        return card

    def _section_card(self, title, subtitle):
        card = create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        t = QLabel(title)
        t.setObjectName("subsectionTitle")
        s = QLabel(subtitle)
        s.setObjectName("mutedLabel")
        layout.addWidget(t)
        layout.addWidget(s)
        return card, layout

    def _preference_row(self, title, desc, control, value_label=None):
        row = QFrame()
        row.setObjectName("preferenceRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(16)
        copy = QVBoxLayout()
        copy.setSpacing(3)
        t = QLabel(title)
        t.setStyleSheet("font-size: 14px; font-weight: 800; color: #FFFFFF;")
        d = QLabel(desc)
        d.setObjectName("mutedLabel")
        d.setWordWrap(True)
        copy.addWidget(t)
        copy.addWidget(d)
        layout.addLayout(copy, 1)
        if value_label:
            layout.addWidget(value_label)
        layout.addWidget(control)
        return row

    def _slider_control(self, value, minimum, maximum, suffix):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(int(value))
        slider.setFixedWidth(150)
        value_label = QLabel(f"{int(value)}{suffix}")
        value_label.setObjectName("mutedLabel")
        value_label.setFixedWidth(52)
        slider.valueChanged.connect(lambda v, lbl=value_label, s=suffix: lbl.setText(f"{v}{s}"))
        return slider, value_label

    def _combo(self, values):
        combo = QComboBox()
        combo.addItems(values)
        combo.setMinimumWidth(145)
        return combo

    def save(self):
        self.settings["ai_enabled"] = self.ai_toggle.isChecked()
        self.settings["distraction_ai"] = self.dist_toggle.isChecked()
        self.settings["auto_start"] = self.autostart_toggle.isChecked()
        self.settings["notifications"] = self.notif_toggle.isChecked()
        self.settings["strict_mode"] = self.strict_toggle.isChecked()
        self.settings["focus_duration"] = self.focus_slider.value()
        self.settings["break_duration"] = self.break_slider.value()
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["density"] = self.density_combo.currentText()
        self.settings["accent"] = self.accent_combo.currentText()
        self.settings["coach_style"] = self.coach_combo.currentText()
        self.settings["goal_focus_hours"] = self.goal_focus_slider.value()
        save_settings(self.settings)
        
        # Apply Windows Auto-Start
        try:
            from monitor.auto_start import enable_auto_start, disable_auto_start
            import sys
            if self.settings["auto_start"]:
                exe = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
                enable_auto_start("CognitiveAI", exe)
            else:
                disable_auto_start("CognitiveAI")
        except Exception as e:
            print(f"[SettingsPage] Auto-start config error: {e}")

        self.status_label.setText("Preferences saved.")

    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Preferences", "cognitive_ai_preferences.json", "JSON Files (*.json)")
        if not path:
            return
        self.save()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)
        self.status_label.setText(f"Exported preferences to {os.path.basename(path)}.")

    def import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Preferences", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                incoming = json.load(f)
            if not isinstance(incoming, dict):
                raise ValueError("Invalid settings file")
            self.settings.update(incoming)
            save_settings(self.settings)
            self._sync_controls()
            self.status_label.setText("Imported preferences.")
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))

    def create_backup(self):
        os.makedirs("data", exist_ok=True)
        self.save()
        shutil.copyfile("user_settings.json", os.path.join("data", "settings_backup.json"))
        self.status_label.setText("Backup created at data/settings_backup.json.")

    def _sync_controls(self):
        self.ai_toggle.setChecked(self.settings.get("ai_enabled", True))
        self.dist_toggle.setChecked(self.settings.get("distraction_ai", True))
        self.autostart_toggle.setChecked(self.settings.get("auto_start", False))
        self.notif_toggle.setChecked(self.settings.get("notifications", True))
        self.strict_toggle.setChecked(self.settings.get("strict_mode", False))
        self.focus_slider.setValue(int(self.settings.get("focus_duration", 45)))
        self.break_slider.setValue(int(self.settings.get("break_duration", 10)))
        self.theme_combo.setCurrentText(self.settings.get("theme", "Midnight"))
        self.density_combo.setCurrentText(self.settings.get("density", "Comfortable"))
        self.accent_combo.setCurrentText(self.settings.get("accent", "Iris"))
        self.coach_combo.setCurrentText(self.settings.get("coach_style", "Calm"))
        self.goal_focus_slider.setValue(int(self.settings.get("goal_focus_hours", 5)))
        self.distraction_slider.setValue(int(self.settings.get("goal_distraction_mins", 75)))

    def on_show(self):
        fade_in(self)
