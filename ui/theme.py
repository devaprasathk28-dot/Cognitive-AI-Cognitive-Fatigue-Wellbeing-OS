STYLE = """
/* Layer 0: application atmosphere */
QWidget {
    font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #F4F6FB;
    background-color: #080A0F;
    font-size: 14px;
    selection-background-color: rgba(118, 126, 255, 0.42);
}

QWidget#pageSurface {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #0B0E15,
        stop: 0.48 #080A0F,
        stop: 1 #0E1118
    );
}

QFrame#pageContainer {
    background-color: rgba(255, 255, 255, 0.018);
    border: 1px solid rgba(255, 255, 255, 0.035);
    border-radius: 10px;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 10px;
    margin: 6px 3px 6px 3px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.24);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 0px;
}

/* Typography hierarchy */
QLabel#pageTitle {
    font-size: 32px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.4px;
}

QLabel#pageSubtitle {
    color: rgba(224, 229, 240, 0.62);
    font-size: 14px;
    font-weight: 450;
}

QLabel#sectionTitle {
    font-size: 12px;
    font-weight: 800;
    color: rgba(233, 237, 246, 0.62);
    text-transform: uppercase;
    letter-spacing: 0.9px;
}

QLabel#subsectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#mutedLabel {
    color: rgba(224, 229, 240, 0.58);
    font-size: 13px;
    font-weight: 450;
}

QLabel#metadataLabel {
    color: rgba(224, 229, 240, 0.44);
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.7px;
    text-transform: uppercase;
}

QLabel#metricValue {
    color: #FFFFFF;
    font-size: 34px;
    font-weight: 850;
    letter-spacing: -0.4px;
}

QLabel#metricValueLarge {
    color: #FFFFFF;
    font-size: 54px;
    font-weight: 850;
    letter-spacing: -0.5px;
}

QLabel#metricCaption {
    color: rgba(224, 229, 240, 0.48);
    font-size: 12px;
    font-weight: 600;
}

/* Layer 2: cards */
QFrame#card {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 0.072),
        stop: 0.55 rgba(255, 255, 255, 0.038),
        stop: 1 rgba(255, 255, 255, 0.024)
    );
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 10px;
}
QFrame#card:hover {
    border: 1px solid rgba(142, 151, 255, 0.22);
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 0.092),
        stop: 0.55 rgba(255, 255, 255, 0.048),
        stop: 1 rgba(118, 126, 255, 0.045)
    );
}

QFrame#elevatedCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(118, 126, 255, 0.115),
        stop: 0.5 rgba(255, 255, 255, 0.05),
        stop: 1 rgba(126, 231, 198, 0.04)
    );
    border: 1px solid rgba(142, 151, 255, 0.22);
    border-radius: 10px;
}

QFrame#softPanel {
    background-color: rgba(255, 255, 255, 0.032);
    border: 1px solid rgba(255, 255, 255, 0.055);
    border-radius: 8px;
}

QFrame#preferenceRow {
    background-color: rgba(255, 255, 255, 0.022);
    border: 1px solid rgba(255, 255, 255, 0.045);
    border-radius: 8px;
}
QFrame#preferenceRow:hover {
    background-color: rgba(255, 255, 255, 0.04);
    border-color: rgba(142, 151, 255, 0.16);
}

QFrame#pill {
    background-color: rgba(118, 126, 255, 0.13);
    border: 1px solid rgba(118, 126, 255, 0.24);
    border-radius: 8px;
}

QFrame#livePulse {
    background-color: rgba(126, 231, 198, 0.18);
    border: 1px solid rgba(126, 231, 198, 0.35);
    border-radius: 6px;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: #E9EDF6;
    font-size: 13px;
    font-weight: 650;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.083);
    border: 1px solid rgba(142, 151, 255, 0.28);
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.028);
    padding-top: 9px;
    padding-bottom: 7px;
}

QPushButton#primaryButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #7781FF,
        stop: 1 #5D5FEF
    );
    border: 1px solid rgba(177, 182, 255, 0.62);
    color: #FFFFFF;
    font-weight: 800;
}
QPushButton#primaryButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #8D95FF,
        stop: 1 #6D6FF8
    );
}

QPushButton#segmentedButton {
    background-color: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.065);
    border-radius: 8px;
    padding: 7px 12px;
    color: rgba(233, 237, 246, 0.62);
}
QPushButton#segmentedButton:checked {
    background-color: rgba(118, 126, 255, 0.22);
    border-color: rgba(142, 151, 255, 0.42);
    color: #FFFFFF;
}

QPushButton#iconButton {
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
    border-radius: 8px;
    padding: 0px;
}

/* Sidebar */
QFrame#sidebar {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #0E1118,
        stop: 0.52 #090B11,
        stop: 1 #0B0D12
    );
    border-right: 1px solid rgba(255, 255, 255, 0.065);
}

QPushButton#sidebarButton {
    text-align: left;
    padding: 10px 12px;
    min-height: 22px;
    font-size: 13px;
    font-weight: 700;
    color: rgba(224, 229, 240, 0.57);
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
}
QPushButton#sidebarButton:hover {
    background: rgba(255, 255, 255, 0.045);
    color: #EEF2FF;
    border-color: rgba(255, 255, 255, 0.055);
}
QPushButton#sidebarButton:checked {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 rgba(118, 126, 255, 0.27),
        stop: 1 rgba(118, 126, 255, 0.075)
    );
    color: #FFFFFF;
    border: 1px solid rgba(142, 151, 255, 0.26);
    font-weight: 800;
}

QLabel#brandTitle {
    color: #FFFFFF;
    font-size: 18px;
    font-weight: 850;
}
QLabel#brandSubtitle {
    color: rgba(224, 229, 240, 0.48);
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.8px;
}

/* Dividers */
QFrame[frameShape="4"], QFrame#divider {
    color: rgba(255, 255, 255, 0.07);
    background-color: rgba(255, 255, 255, 0.07);
    max-height: 1px;
    min-height: 1px;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox {
    background-color: rgba(255, 255, 255, 0.036);
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 8px;
    padding: 9px 12px;
    color: #FFFFFF;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid rgba(142, 151, 255, 0.62);
    background-color: rgba(255, 255, 255, 0.058);
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background-color: #11151F;
    border: 1px solid rgba(255, 255, 255, 0.10);
    selection-background-color: rgba(118, 126, 255, 0.28);
    outline: 0;
}

/* Checkboxes */
QCheckBox {
    color: #E4E8F2;
    spacing: 10px;
    font-size: 13px;
    font-weight: 650;
}
QCheckBox::indicator {
    width: 34px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background-color: rgba(255, 255, 255, 0.08);
}
QCheckBox::indicator:hover {
    border-color: rgba(142, 151, 255, 0.35);
}
QCheckBox::indicator:checked {
    background-color: #7781FF;
    border-color: rgba(177, 182, 255, 0.75);
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.09);
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #7EE7C6, stop: 1 #7781FF);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
    border: 1px solid rgba(0, 0, 0, 0.25);
}
QSlider::handle:horizontal:hover {
    background: #F5F7FF;
}
"""


def apply_theme(app):
    app.setStyleSheet(STYLE)
