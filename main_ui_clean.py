import sys
import os
import ctypes
from typing import Protocol, cast

from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSystemTrayIcon, QMenu, QFrame
)
from PyQt6.QtGui import QIcon, QCloseEvent, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QThread, QSharedMemory

from monitor.ui_worker import EngineWorker
from monitor.settings_manager import load_settings, save_settings
from storage.db import fatigue_to_focus_score, log_notification
from monitor.ambient_sound_engine import cleanup_temp_audio
from ui.onboarding_page import OnboardingPage
from ui.components.topbar import TopBar
from ui.components.sidebar import Sidebar
from ui.components.command_palette import CommandPalette
from ui.components.breathing_modal import BreathingModal
from ui.theme import apply_theme
from ui.pages.dashboard_page import DashboardPage
from ui.pages.insights_page import InsightsPage
from ui.pages.focus_page import FocusPage
from ui.pages.analytics_page import AnalyticsPage
from ui.pages.chat_page import ChatPage
from ui.pages.goals_page import GoalsPage
from ui.pages.notifications_page import NotificationsPage
from ui.pages.settings_page import SettingsPage
from ui.components.core_ui import fade_in, install_button_press


class PageLifecycle(Protocol):
    def on_show(self) -> None:
        ...

    def on_hide(self) -> None:
        ...


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.setWindowIcon(QIcon("assets/icon.ico"))
        
        if not self.settings.get("onboarding_done", False):
            self.show_onboarding()
        else:
            self.init_main_ui()

    def show_onboarding(self):
        self.onboarding = OnboardingPage(self.finish_onboarding)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.onboarding)

    def finish_onboarding(self):
        self.settings["onboarding_done"] = True
        save_settings(self.settings)
        self.onboarding.deleteLater()
        self.init_main_ui()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(QIcon("assets/icon.ico"), self)
        menu = QMenu()
        menu.addAction("Show Dashboard", self.show_and_activate)
        menu.addAction("Start 25m Focus Sprint", lambda: self.handle_palette_action("focus_start", 25))
        menu.addAction("Mindful Breathing Break", lambda: self.handle_palette_action("breathing_break", None))
        menu.addSeparator()
        menu.addAction("Exit Cognitive AI", self.exit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.show_and_activate()

    def show_and_activate(self):
        self.showNormal()
        self.activateWindow()

    def exit_app(self):
        cleanup_temp_audio()
        if hasattr(self, "worker"):
            self.worker._running = False
        if hasattr(self, "_thread"):
            self._thread.quit()
            self._thread.wait(1000)
        if hasattr(self, "tray"):
            self.tray.hide()
        QApplication.quit()

    def init_main_ui(self):
        self.setWindowTitle("Cognitive AI — Wellbeing & Productivity OS")
        self.resize(1160, 720)
        self.setMinimumSize(1020, 640)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.topbar = TopBar()
        main_layout.addWidget(self.topbar)

        # Focus Shield Floating Warning Banner
        self.shield_banner = QFrame()
        self.shield_banner.setFixedHeight(44)
        self.shield_banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 122, 144, 0.22), stop:1 rgba(251, 191, 36, 0.16));
                border-bottom: 1px solid rgba(255, 122, 144, 0.38);
            }
        """)
        shield_layout = QHBoxLayout(self.shield_banner)
        shield_layout.setContentsMargins(24, 0, 24, 0)
        
        self.shield_text = QLabel("🛡️ Focus Shield Active: Distraction app detected during deep work.")
        self.shield_text.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")
        shield_layout.addWidget(self.shield_text)
        shield_layout.addStretch()
        
        btn_dismiss_shield = QPushButton("Dismiss")
        btn_dismiss_shield.setObjectName("secondaryButton")
        btn_dismiss_shield.setFixedHeight(26)
        btn_dismiss_shield.clicked.connect(self.shield_banner.hide)
        install_button_press(btn_dismiss_shield)
        shield_layout.addWidget(btn_dismiss_shield)
        
        main_layout.addWidget(self.shield_banner)
        self.shield_banner.hide()

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.switch_page)
        content_layout.addWidget(self.sidebar)

        # Main Area
        self.stack = QStackedWidget()
        
        # Initialize Pages
        self.dashboard = DashboardPage()
        self.insights = InsightsPage()
        self.focus = FocusPage()
        self.analytics = AnalyticsPage()
        self.chat = ChatPage()
        self.goals = GoalsPage()
        self.notifications = NotificationsPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.insights)
        self.stack.addWidget(self.focus)
        self.stack.addWidget(self.analytics)
        self.stack.addWidget(self.chat)
        self.stack.addWidget(self.goals)
        self.stack.addWidget(self.notifications)
        self.stack.addWidget(self.settings_page)

        # Connect TopBar Quick Actions
        self.topbar.notif_btn.clicked.connect(lambda: self.switch_page(6))
        self.topbar.profile_btn.clicked.connect(lambda: self.switch_page(7))

        # Command Palette Trigger (Ctrl+K and TopBar search click)
        self.cmd_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.cmd_shortcut.activated.connect(self.open_command_palette)
        self.topbar.search_input.mousePressEvent = lambda e: self.open_command_palette()
        self.topbar.search_input.setPlaceholderText("Search or Command Palette (Ctrl+K)...")

        # Connect Focus Page signals to TopBar & Dashboard
        self.focus.timer_updated.connect(self.topbar.set_focus_time)
        self.focus.session_finished.connect(lambda dur: self.dashboard.refresh_stats())
        
        content_layout.addWidget(self.stack, 1)
        main_layout.addLayout(content_layout, 1)

        self.stack.setCurrentIndex(0)
        self.setup_tray()

        # Engine Worker Thread
        self._thread = QThread()
        self.worker = EngineWorker()
        self.worker.moveToThread(self._thread)
        
        self._thread.started.connect(self.worker.run)
        self.worker.data_signal.connect(self.dashboard.update_from_engine)
        self.worker.data_signal.connect(self.on_engine_update)
        self.worker.finished.connect(self._thread.quit)
        self._thread.start()

    def open_command_palette(self):
        palette = CommandPalette(self)
        palette.action_triggered.connect(self.handle_palette_action)
        palette.exec()

    def handle_palette_action(self, action_type: str, payload):
        if action_type == "nav":
            self.switch_page(int(payload))
        elif action_type == "focus_start":
            self.switch_page(2)  # Focus page
            mins = int(payload)
            self.focus.set_preset(mins, f"{mins}m Sprint")
            if not self.focus.focus_active:
                self.focus.toggle_focus()
        elif action_type == "breathing_break":
            modal = BreathingModal(self, duration_seconds=120)
            modal.exec()
            self.dashboard.refresh_stats()
        elif action_type == "toggle_focus":
            self.dashboard.toggle_focus_mode()
        elif action_type == "export_report":
            try:
                from analytics.report_generator import generate_executive_html_report
                import webbrowser
                path = generate_executive_html_report()
                webbrowser.open(f"file://{path}")
            except Exception as e:
                print(f"[Palette] Report error: {e}")
        elif action_type == "clear_notifs":
            from storage.db import clear_notifications
            clear_notifications()
            self.switch_page(6)

    def on_engine_update(self, data):
        # Update tray tooltip
        f_val = data.get("fatigue", 0)
        score = fatigue_to_focus_score(f_val)
        app = data.get("app", "--")
        cat = data.get("category", "--")
        if hasattr(self, "tray"):
            self.tray.setToolTip(f"Cognitive AI\nFocus Score: {score}%\nActive: {app} ({cat})")

        # Focus Shield: detect distractions if Focus Mode is actively enabled
        settings = load_settings()
        if settings.get("focus_mode", False) or self.focus.focus_active:
            if cat in ["Entertainment", "Gaming"] or any(d in app.lower() for d in ["youtube", "netflix", "steam", "discord"]):
                self.shield_text.setText(f"🛡️ Focus Shield Active: '{app}' is outside your deep work scope.")
                self.shield_banner.show()
            else:
                self.shield_banner.hide()
        else:
            self.shield_banner.hide()

    def switch_page(self, index):
        old_index = self.stack.currentIndex()
        if old_index == index:
            return

        self.sidebar.set_active(index)

        old_widget = self.stack.widget(old_index)
        new_widget = self.stack.widget(index)
        if new_widget is None:
            return

        self.stack.setCurrentIndex(index)
        
        if old_widget is not None and hasattr(old_widget, "on_hide"):
            cast(PageLifecycle, old_widget).on_hide()
        if hasattr(new_widget, "on_show"):
            cast(PageLifecycle, new_widget).on_show()
        else:
            fade_in(new_widget, duration=180)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is not None:
            a0.ignore()
        self.hide()
        if hasattr(self, "tray"):
            self.tray.showMessage(
                "Cognitive AI",
                "Application minimized to system tray. Intelligent background tracking active.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )


if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cognitive.ai.wellbeing.v1")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Cognitive AI")
    app.setWindowIcon(QIcon("assets/icon.ico"))

    shared_mem = QSharedMemory("CognitiveAI_SingleInstance_Key")
    if not shared_mem.create(1):
        print("Cognitive AI is already running.")
        sys.exit(0)

    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
