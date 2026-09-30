from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt6.QtCore import QTimer
from ui.components.core_ui import create_card_frame, install_button_hover, fade_in
from monitor.settings_manager import load_settings, save_settings

try:
    from monitor.memory_engine import save_memory
except ImportError:
    def save_memory(mem):
        pass

class FeaturesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")

        root = QVBoxLayout()
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️ Features & Controls")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        self.settings = load_settings()
        
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(16)

        # 1. Smart Features
        sf_card = create_card_frame()
        sf_layout = QVBoxLayout(sf_card)
        sf_label = QLabel("🎯 Focus & Productivity")
        sf_label.setObjectName("sectionTitle")
        sf_layout.addWidget(sf_label)
        
        self.strict_toggle = QCheckBox("Enable Strict Focus Mode (Blocks distraction apps)")
        self.strict_toggle.setChecked(self.settings.get("strict_mode", False))
        
        self.distraction_toggle = QCheckBox("Enable Distraction AI Detection")
        self.distraction_toggle.setChecked(self.settings.get("distraction_ai", True))
        
        sf_layout.addWidget(self.strict_toggle)
        sf_layout.addWidget(self.distraction_toggle)
        layout.addWidget(sf_card)

        # 2. Wellness
        w_card = create_card_frame()
        w_layout = QVBoxLayout(w_card)
        w_label = QLabel("🧘 Wellness & Health")
        w_label.setObjectName("sectionTitle")
        w_layout.addWidget(w_label)
        
        self.notify_toggle = QCheckBox("Smart Break Reminders (Based on fatigue)")
        self.notify_toggle.setChecked(self.settings.get("notifications", True))
        
        self.eye_toggle = QCheckBox("20-20-20 Eye Rest Rule")
        self.eye_toggle.setChecked(self.settings.get("eye_rest", False))
        
        w_layout.addWidget(self.notify_toggle)
        w_layout.addWidget(self.eye_toggle)
        layout.addWidget(w_card)

        # 3. AI & Privacy
        ai_card = create_card_frame()
        ai_layout = QVBoxLayout(ai_card)
        ai_label = QLabel("🤖 AI & Privacy")
        ai_label.setObjectName("sectionTitle")
        ai_layout.addWidget(ai_label)
        
        self.ai_toggle = QCheckBox("Enable AI Assistant")
        self.ai_toggle.setChecked(self.settings.get("ai_enabled", True))
        
        ai_layout.addWidget(self.ai_toggle)
        
        clear_btn = QPushButton("Clear Local AI Memory")
        clear_btn.clicked.connect(self.clear_memory)
        ai_layout.addWidget(clear_btn)
        layout.addWidget(ai_card)

        save_btn = QPushButton("Save Preferences")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)
        self.setLayout(root)

    def save_settings(self):
        self.settings["strict_mode"] = self.strict_toggle.isChecked()
        self.settings["notifications"] = self.notify_toggle.isChecked()
        self.settings["ai_enabled"] = self.ai_toggle.isChecked()
        self.settings["distraction_ai"] = self.distraction_toggle.isChecked()
        self.settings["eye_rest"] = self.eye_toggle.isChecked()
        save_settings(self.settings)

    def clear_memory(self):
        save_memory([])
