from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class OnboardingPage(QWidget):
    def __init__(self, on_finish):
        super().__init__()

        container = QVBoxLayout()
        container.setContentsMargins(40, 20, 40, 20)

        wrapper = QVBoxLayout()
        wrapper.setAlignment(Qt.AlignmentFlag.AlignTop)

        container.addLayout(wrapper)
        self.setLayout(container)

        wrapper.addWidget(QLabel("👋 Welcome to Cognitive AI"))
        wrapper.addWidget(QLabel("This app helps you track focus & avoid burnout."))

        start_btn = QPushButton("Get Started")
        start_btn.clicked.connect(on_finish)
        wrapper.addWidget(start_btn)
