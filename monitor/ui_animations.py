
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget

_RUNNING_ANIMATIONS = []

def animate_panel(widget, start_rect, end_rect):
    """Safe single animation per widget - prevents stacking/ghosting"""
    if hasattr(widget, "_anim") and widget._anim.state() == QPropertyAnimation.State.Running:
        return

    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(250)
    anim.setStartValue(start_rect)
    anim.setEndValue(end_rect)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    widget._anim = anim
    anim.start()

def is_animating(widget=None):
    """Check if any animations are running. widget-specific if provided."""
    return len(_RUNNING_ANIMATIONS) > 0

def slide_in(widget, start_x, end_x, duration=400):
    if hasattr(widget, "_anim") and hasattr(widget, "_anim") and widget._anim.state() == QPropertyAnimation.State.Running:
        return
    start_rect = widget.geometry().translated(start_x, 0)
    end_rect = widget.geometry().translated(end_x, 0)
    animate_panel(widget, start_rect, end_rect)

def fade_in(widget, duration=300):
    if hasattr(widget, "_anim") and widget._anim.state() == QPropertyAnimation.State.Running:
        return
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(1)
    widget._fade_anim = anim  # separate attr for opacity
    anim.start()

