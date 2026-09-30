from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

class TopBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.title = QLabel("Cognitive AI")
        self.status = QLabel("● Active")
        self.status.setObjectName("muted")

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("ghost")

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.status)
        layout.addWidget(self.refresh_btn)

