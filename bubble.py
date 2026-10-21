from PySide6.QtCore import QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
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
        metrics = QFontMetrics(self._font)
        flags = int(Qt.TextFlag.TextWordWrap) | int(Qt.AlignmentFlag.AlignLeft)
        rect = metrics.boundingRect(QRect(0, 0, self.MAX_TEXT_WIDTH, 2000), flags, self._text)
        width = rect.width() + self.PADDING_X * 2 + 4
        height = rect.height() + self.PADDING_Y * 2 + 4
        self.setFixedSize(max(70, width), max(36, height))

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
        painter.setPen(QColor(245, 245, 245))
        painter.setFont(self._font)
        text_rect = QRect(
            self.PADDING_X,
            self.PADDING_Y,
            self.width() - self.PADDING_X * 2,
            self.height() - self.PADDING_Y * 2,
        )
        flags = int(Qt.TextFlag.TextWordWrap) | int(Qt.AlignmentFlag.AlignLeft) | int(Qt.AlignmentFlag.AlignVCenter)
        painter.drawText(text_rect, flags, self._text)
        painter.end()
