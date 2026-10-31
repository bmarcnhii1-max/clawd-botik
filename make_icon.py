import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter

import sprite
from config import load_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(BASE_DIR, "clawd-icon.png")
ICO_PATH = os.path.join(BASE_DIR, "clawd.ico")

app = QGuiApplication([])
config = load_config()
color_index = int(config.get("color", 0))
_, body, eye = sprite.palette(color_index)
key = ("open", 0, "normal", "stand", 0, False, None)
pixmap = sprite.render_frame(key, 13, body, eye, sprite.body_shape(color_index))

canvas = QImage(256, 256, QImage.Format.Format_ARGB32_Premultiplied)
canvas.fill(Qt.GlobalColor.transparent)
painter = QPainter(canvas)
painter.drawPixmap((256 - pixmap.width()) // 2, (256 - pixmap.height()) // 2, pixmap)
painter.end()
canvas.save(PNG_PATH, "PNG")

image = Image.open(PNG_PATH)
image.save(ICO_PATH, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon", ICO_PATH)
