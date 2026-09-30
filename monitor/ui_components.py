from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


def create_card(title, value):
    card = QFrame()
    card.setObjectName("card")

    layout = QVBoxLayout()

    t = QLabel(title)
    t.setStyleSheet("color:#9E9E9E; font-size:12px;")

    v = QLabel(value)
    v.setStyleSheet("font-size:20px; font-weight:bold;")

    layout.addWidget(t)
    layout.addWidget(v)

    card.setLayout(layout)
    return card