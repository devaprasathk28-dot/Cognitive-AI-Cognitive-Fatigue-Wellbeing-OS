from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QEvent, QPointF, QObject, QTimer

_ACTIVE_ANIMATIONS = set()

def _run_animation(animation):
    _ACTIVE_ANIMATIONS.add(animation)
    def done():
        _ACTIVE_ANIMATIONS.discard(animation)
    animation.finished.connect(done)
    animation.start()

def _has_graphics_effect_tree(widget):
    if widget is None:
        return False
    if widget.graphicsEffect() is not None:
        return True
    return any(child.graphicsEffect() is not None for child in widget.findChildren(QWidget))

def _has_graphics_effect_ancestor(widget):
    parent = widget.parentWidget() if widget is not None else None
    while parent is not None:
        if parent.graphicsEffect() is not None:
            return True
        parent = parent.parentWidget()
    return False

def apply_shadow(widget, blur=15, y=6, alpha=80):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)
    return shadow

def fade_in(widget, duration=220):
    if widget is None:
        return None
    if _has_graphics_effect_tree(widget) or _has_graphics_effect_ancestor(widget):
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    return _run_animation(animation)


class HoverGlowFilter(QObject):
    def __init__(self, base_blur=20, hover_blur=34, base_alpha=80, hover_alpha=142, parent=None):
        super().__init__(parent)
        self.base_blur = base_blur
        self.hover_blur = hover_blur
        self.base_alpha = base_alpha
        self.hover_alpha = hover_alpha

    def eventFilter(self, a0, a1):
        obj = a0
        event = a1
        if not isinstance(obj, QWidget) or event is None:
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.Enter:
            self._animate(obj, self.hover_blur, self.hover_alpha, 10)
        elif event.type() == QEvent.Type.Leave:
            self._animate(obj, self.base_blur, self.base_alpha, 8)
        return super().eventFilter(obj, event)

    def _animate(self, obj, blur, alpha, y):
        effect = obj.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            effect = apply_shadow(obj, self.base_blur, 8, self.base_alpha)
        color = QColor(87, 92, 165, alpha)
        blur_anim = QPropertyAnimation(effect, b"blurRadius", obj)
        blur_anim.setDuration(150)
        blur_anim.setStartValue(effect.blurRadius())
        blur_anim.setEndValue(blur)
        blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        offset_anim = QPropertyAnimation(effect, b"offset", obj)
        offset_anim.setDuration(150)
        offset_anim.setStartValue(effect.offset())
        offset_anim.setEndValue(QPointF(0, y))
        offset_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        color_anim = QPropertyAnimation(effect, b"color", obj)
        color_anim.setDuration(150)
        color_anim.setStartValue(effect.color())
        color_anim.setEndValue(color)
        color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        _run_animation(blur_anim)
        _run_animation(offset_anim)
        _run_animation(color_anim)

def animate_scroll_to_bottom(scroll_area, duration=240):
    bar = scroll_area.verticalScrollBar()
    if not bar:
        return None
    animation = QPropertyAnimation(bar, b"value", scroll_area)
    animation.setDuration(duration)
    animation.setStartValue(bar.value())
    animation.setEndValue(bar.maximum())
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    return _run_animation(animation)

class HoverScaleFilter(QObject):
    def __init__(self, grow=2, parent=None):
        super().__init__(parent)
        self.grow = grow
        self.base_geometry = None

    def eventFilter(self, a0, a1):
        obj = a0
        event = a1
        if not isinstance(obj, QWidget):
            return super().eventFilter(obj, event)

        if event is not None and event.type() == QEvent.Type.Enter:
            if self.base_geometry is None:
                self.base_geometry = obj.geometry()
            target_geo = self.base_geometry.adjusted(-self.grow, -self.grow, self.grow, self.grow)
            self._animate(obj, target_geo)
        elif event is not None and event.type() == QEvent.Type.Leave and self.base_geometry is not None:
            self._animate(obj, self.base_geometry)
            self.base_geometry = None

        return super().eventFilter(obj, event)

    def _animate(self, obj, target):
        animation = QPropertyAnimation(obj, b"geometry", obj)
        animation.setDuration(130)
        animation.setStartValue(obj.geometry())
        animation.setEndValue(QRect(target))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        _run_animation(animation)



def slide_in(widget, direction="left", duration=280):
    if _has_graphics_effect_tree(widget):
        return None
    end_geo = widget.geometry()
    width = widget.width()
    if direction == "left":
        start_geo = QRect(end_geo.x() + int(width * 0.15), end_geo.y(), end_geo.width(), end_geo.height())
    else:
        start_geo = QRect(end_geo.x() - int(width * 0.15), end_geo.y(), end_geo.width(), end_geo.height())
    widget.setGeometry(start_geo)
    slide_anim = QPropertyAnimation(widget, b"geometry", widget)
    slide_anim.setDuration(duration)
    slide_anim.setStartValue(start_geo)
    slide_anim.setEndValue(end_geo)
    slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return _run_animation(slide_anim)

def slide_out(widget, direction="right", duration=280):
    if _has_graphics_effect_tree(widget):
        return None
    start_geo = widget.geometry()
    width = widget.width()
    if direction == "left":
        end_geo = QRect(start_geo.x() - int(width * 0.15), start_geo.y(), start_geo.width(), start_geo.height())
    else:
        end_geo = QRect(start_geo.x() + int(width * 0.15), start_geo.y(), start_geo.width(), start_geo.height())
    slide_anim = QPropertyAnimation(widget, b"geometry", widget)
    slide_anim.setDuration(duration)
    slide_anim.setStartValue(start_geo)
    slide_anim.setEndValue(end_geo)
    slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
    return _run_animation(slide_anim)

class ButtonPressFilter(QObject):
    def __init__(self, scale=0.96, parent=None):
        super().__init__(parent)
        self.scale = scale
        self.base_geometry = None
    
    def eventFilter(self, a0, a1):
        obj = a0
        event = a1
        if not isinstance(obj, QPushButton):
            return super().eventFilter(obj, event)
        if event is None:
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.MouseButtonPress:
            self.base_geometry = obj.geometry()
            w, h = self.base_geometry.width(), self.base_geometry.height()
            new_w, new_h = w * self.scale, h * self.scale
            x_offset, y_offset = (w - new_w) / 2, (h - new_h) / 2
            target_geo = self.base_geometry.adjusted(int(x_offset), int(y_offset), -int(x_offset), -int(y_offset))
            self._animate(obj, target_geo)
        elif event.type() == QEvent.Type.MouseButtonRelease and self.base_geometry is not None:
            self._animate(obj, self.base_geometry)
            self.base_geometry = None
        return super().eventFilter(obj, event)
    
    def _animate(self, obj, target):
        animation = QPropertyAnimation(obj, b"geometry", obj)
        animation.setDuration(100)
        animation.setStartValue(obj.geometry())
        animation.setEndValue(QRect(target))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        _run_animation(animation)

def animate_value_change(label, start_val, end_val, duration=400, prefix="", suffix=""):
    steps = 20
    step_time = duration // steps
    step_size = (end_val - start_val) / steps if steps > 0 else 0
    current = [start_val]
    step_vals = [step_size]
    step_times = [step_time]
    end_vals = [end_val]
    def update():
        current[0] += step_vals[0]
        if current[0] >= end_vals[0]:
            label.setText(f"{prefix}{int(end_vals[0])}{suffix}")
        else:
            label.setText(f"{prefix}{int(current[0])}{suffix}")
            QTimer.singleShot(step_times[0], update)
    QTimer.singleShot(0, update)

def install_button_hover(widget):
    hover_filter = HoverScaleFilter(parent=widget)
    widget.installEventFilter(hover_filter)
    widget._hover_scale_filter = hover_filter

def install_button_press(widget):
    press_filter = ButtonPressFilter(parent=widget)
    widget.installEventFilter(press_filter)
    widget._press_filter = press_filter

def install_button_animations(widget):
    install_button_hover(widget)
    install_button_press(widget)

from PyQt6.QtWidgets import QSizePolicy

def install_card_interactions(widget):
    apply_shadow(widget, blur=20, y=8, alpha=78)
    glow_filter = HoverGlowFilter(parent=widget)
    widget.installEventFilter(glow_filter)
    widget._hover_glow_filter = glow_filter


def create_card_frame(object_name="card", elevated=False):
    card = QFrame()
    card.setObjectName("elevatedCard" if elevated else object_name)
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    install_card_interactions(card)
    return card

def create_divider():
    d = QFrame()
    d.setObjectName("divider")
    d.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    return d

def create_card(title, value):
    card = create_card_frame()
    layout = QVBoxLayout()
    layout.setSpacing(6)
    layout.setContentsMargins(18, 16, 18, 16)
    title_label = QLabel(title)
    title_label.setObjectName("mutedLabel")
    value_label = QLabel(value)
    value_label.setObjectName("metricValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    card.setLayout(layout)
    return card, value_label

def create_stat_card(title, value):
    card = create_card_frame()
    layout = QVBoxLayout()
    layout.setSpacing(6)
    layout.setContentsMargins(18, 16, 18, 16)
    t = QLabel(title)
    t.setObjectName("mutedLabel")
    v = QLabel(value)
    v.setObjectName("metricValue")
    layout.addWidget(t)
    layout.addWidget(v)
    card.setLayout(layout)
    return card, v


def create_badge(text, accent="#7781FF"):
    badge = QFrame()
    badge.setObjectName("pill")
    badge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    layout = QHBoxLayout(badge)
    layout.setContentsMargins(10, 5, 10, 5)
    label = QLabel(text)
    label.setStyleSheet(f"color: {accent}; font-size: 12px; font-weight: 800;")
    layout.addWidget(label)
    return badge


def create_progress_bar(value=0, color="#7781FF"):
    outer = QFrame()
    outer.setObjectName("softPanel")
    outer.setFixedHeight(8)
    outer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    outer_layout = QHBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)
    fill = QFrame()
    fill.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
    fill.setFixedHeight(8)
    outer_layout.addWidget(fill)
    outer_layout.addStretch(max(1, 100 - int(value)))
    outer_layout.setStretch(0, max(1, int(value)))
    outer._fill = fill
    return outer
