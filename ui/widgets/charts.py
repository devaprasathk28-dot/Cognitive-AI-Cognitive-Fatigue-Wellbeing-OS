from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFontMetrics, QPainterPath, QLinearGradient
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty

class NativeBarChart(QWidget):
    barClicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(180)
        self.labels = []
        self.values = []
        self._from_values = []
        self._to_values = []
        self._progress = 1.0
        self.max_val = 1
        self.hovered_index = -1
        self.setMouseTracking(True)
        self.bar_rects = []
        self.setMinimumHeight(220)

    def setData(self, labels, values):
        old_values = self._current_values()
        self.labels = labels
        self.values = values
        self._from_values = self._normalize_length(old_values, len(values))
        self._to_values = self._normalize_length(values, len(values))
        self._progress = 0.0
        self.max_val = max(values) if values else 1
        if self.max_val == 0: self.max_val = 1
        animation = QPropertyAnimation(self, b"progress", self)
        animation.setDuration(420)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._anim = animation

    def _normalize_length(self, values, length):
        normalized = list(values[:length])
        while len(normalized) < length:
            normalized.append(0)
        return normalized

    def _current_values(self):
        if not self._to_values:
            return self.values
        return [
            self._from_values[i] + (self._to_values[i] - self._from_values[i]) * self._progress
            for i in range(len(self._to_values))
        ]

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = float(value)
        self.update()

    progress = pyqtProperty(float, fget=get_progress, fset=set_progress)

    def mouseMoveEvent(self, event):
        idx = -1
        pos = event.position()
        for i, rect in enumerate(self.bar_rects):
            if rect.contains(pos):
                idx = i
                break
        if idx != self.hovered_index:
            self.hovered_index = idx
            self.setCursor(Qt.CursorShape.PointingHandCursor if idx != -1 else Qt.CursorShape.ArrowCursor)
            if idx != -1 and idx < len(self.labels) and idx < len(self.values):
                self.setToolTip(f"{self.labels[idx]}: {int(self.values[idx])} min")
            else:
                self.setToolTip("")
            self.update()

    def mousePressEvent(self, event):
        if self.hovered_index != -1 and self.hovered_index < len(self.labels):
            self.barClicked.emit(self.labels[self.hovered_index])

    def leaveEvent(self, event):
        self.hovered_index = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        pad_b = 34
        pad_t = 28
        pad_x = 16
        
        available_w = w - 2 * pad_x
        available_h = h - pad_b - pad_t
        
        display_values = self._current_values()
        n = len(display_values)
        if n == 0:
            painter.setPen(QColor(255, 255, 255, 105))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No activity data yet")
            painter.end()
            return
            
        bar_w = min(40, available_w / n * 0.6)
        spacing = (available_w - (n * bar_w)) / (n + 1)
        
        self.bar_rects = []
        
        fm = QFontMetrics(self.font())
        
        grid_pen = QPen(QColor(255, 255, 255, 18))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for ratio in (0.25, 0.5, 0.75, 1.0):
            y = pad_t + available_h * (1 - ratio)
            painter.drawLine(int(pad_x), int(y), int(w - pad_x), int(y))

        for i in range(n):
            val = display_values[i]
            lbl = self.labels[i]
            
            x = pad_x + spacing + i * (bar_w + spacing)
            bar_h = (val / self.max_val) * available_h
            y = h - pad_b - bar_h
            
            rect = QRectF(x, y, bar_w, bar_h)
            self.bar_rects.append(rect)
            
            # Draw Bar
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if i == self.hovered_index:
                gradient.setColorAt(0, QColor("#A7FFF0"))
                gradient.setColorAt(1, QColor("#8D95FF"))
            elif i == n - 1:
                gradient.setColorAt(0, QColor("#7EE7C6"))
                gradient.setColorAt(1, QColor("#35B894"))
            else:
                gradient.setColorAt(0, QColor("#8D95FF"))
                gradient.setColorAt(1, QColor("#5D5FEF"))
            color = QColor("#7C83FF")
            if i == self.hovered_index:
                color = color.lighter(120)
                
            path = QPainterPath()
            path.addRoundedRect(rect, 5, 5)
            painter.fillPath(path, QBrush(gradient))
            
            # Draw Label
            painter.setPen(QColor("#B7B7C2"))
            lbl_w = fm.horizontalAdvance(lbl)
            painter.drawText(int(x + bar_w/2 - lbl_w/2), h - 10, lbl)

            # Draw Value on Hover
            if i == self.hovered_index:
                val_str = f"{int(self.values[i])}m"
                val_w = fm.horizontalAdvance(val_str)
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(int(x + bar_w/2 - val_w/2), int(y - 6), val_str)
                
        painter.end()
