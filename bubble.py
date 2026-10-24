from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QTextLayout,
    QTextOption,
)
from PySide6.QtWidgets import QWidget


def _clamp(value, low, high):
    if high < low:
        return low
    return low if value < low else high if value > high else value


class BubbleWindow(QWidget):
    PADDING_X = 12
    PADDING_Y = 8
    MAX_TEXT_WIDTH = 260

    def __init__(self):
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._text = ""
        self._font = QFont("Segoe UI", 10)
        self._font.setBold(True)
        self._layout = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text, seconds=3.5):
        text = str(text or "").strip()
        if not text:
            return
        self._text = text
        self._resize_to_text()
        self.show()
        self.raise_()
        self._timer.start(int(max(0.8, seconds) * 1000))
        self.update()

    def _resize_to_text(self):
        layout = QTextLayout(self._text, self._font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        layout.beginLayout()
        width = max(1.0, float(self.MAX_TEXT_WIDTH - self.PADDING_X * 2))
        y = 0.0
        max_width = 0.0
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            line.setPosition(QPointF(0.0, y))
            max_width = max(max_width, line.naturalTextWidth())
            y += line.height()
        layout.endLayout()
        self._layout = layout
        bubble_width = int(max_width) + self.PADDING_X * 2 + 6
        bubble_height = int(y) + self.PADDING_Y * 2 + 4
        self.setFixedSize(
            max(70, min(self.MAX_TEXT_WIDTH + self.PADDING_X * 2 + 6, bubble_width)),
            max(36, bubble_height),
        )

    def place_near(self, pet_rect, screen_rect):
        width = self.width()
        height = self.height()
        x = pet_rect.x() + pet_rect.width() // 2 - width // 2
        y = pet_rect.y() - height - 6
        if y < screen_rect.top():
            y = pet_rect.y() + pet_rect.height() + 6
        x = _clamp(x, screen_rect.left() + 4, screen_rect.right() - width - 4)
        y = _clamp(y, screen_rect.top() + 4, screen_rect.bottom() - height - 4)
        self.move(int(x), int(y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.setBrush(QColor(28, 28, 30, 235))
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
        painter.drawRoundedRect(rect, 12.0, 12.0)
        if self._layout is not None:
            painter.setPen(QColor(245, 245, 245))
            painter.setFont(self._font)
            self._layout.draw(painter, QPointF(self.PADDING_X, self.PADDING_Y + 2))
        painter.end()
