from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

GRID_W = 18
GRID_H = 13

SIZE_UNITS = [6, 8, 10, 4]

PALETTES = [
    ("Claude", 0xFFD97757, 0xFF1A1A1A),
    ("Мятный", 0xFF4FBF98, 0xFF12241D),
    ("Лавандовый", 0xFF9B8AEE, 0xFF1B1631),
    ("Небесный", 0xFF4FA8E8, 0xFF0E1C29),
    ("Розовый", 0xFFEE85AE, 0xFF2A1220),
    ("Графит", 0xFF5E6670, 0xFFF2F2F2),
]

HEART_COLOR = 0xFFFF5C7A
ZZZ_COLOR = 0xFF8FA3BF
SPARK_COLOR = 0xFFFFC94D

PARTICLE_COLORS = {
    "heart": HEART_COLOR,
    "zzz": ZZZ_COLOR,
    "spark": SPARK_COLOR,
}

PATTERNS = {
    "heart": (
        ".XX.XX.",
        "XXXXXXX",
        "XXXXXXX",
        ".XXXXX.",
        "..XXX..",
        "...X...",
    ),
    "zzz": (
        "XXXXX",
        "...X.",
        "..X..",
        ".X...",
        "XXXXX",
    ),
    "spark": (
        "..X..",
        "..X..",
        "XX.XX",
        "..X..",
        "..X..",
    ),
}


def _qc(color):
    return QColor.fromRgba(int(color) & 0xFFFFFFFF)


def mix_color(a, b, t):
    out = 0xFF000000
    for shift in (16, 8, 0):
        ca = (a >> shift) & 0xFF
        cb = (b >> shift) & 0xFF
        out |= int(ca + (cb - ca) * t) << shift
    return out


def palette(index):
    return PALETTES[int(index) % len(PALETTES)]


def sprite_size(unit):
    return GRID_W * unit, GRID_H * unit


def render_frame(key, unit, body_color, eye_color):
    eyes, look, arms, legs, squash, blush, mouth = key
    blush_color = mix_color(body_color, 0xFFFF4F79, 0.5)
    width, height = sprite_size(unit)
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)

    def px(x0, y0, x1, y1, color):
        painter.fillRect(
            int(x0 * unit),
            int(y0 * unit),
            int((x1 - x0) * unit),
            int((y1 - y0) * unit),
            _qc(color),
        )

    left, right, top, bottom = 3, 15, 3, 10
    if squash > 0:
        left, right, top = 2, 16, 5
    elif squash < 0:
        left, right, top = 4, 14, 2
    if legs == "tuck":
        top += 1
        bottom += 1

    heights = {
        "stand": (2, 2, 2, 2),
        "walk1": (1, 2, 1, 2),
        "walk2": (2, 1, 2, 1),
        "dangle": (3, 3, 3, 3),
        "tuck": (1, 1, 1, 1),
    }.get(legs, (2, 2, 2, 2))
    for col, leg_height in zip((left + 1, left + 3, right - 4, right - 2), heights):
        px(col, bottom, col + 1, bottom + leg_height, body_color)

    def arm(side, style):
        if style == "up":
            if side < 0:
                px(left - 2, top - 1, left - 1, top + 3, body_color)
                px(left - 1, top + 2, left, top + 3, body_color)
            else:
                px(right + 1, top - 1, right + 2, top + 3, body_color)
                px(right, top + 2, right + 1, top + 3, body_color)
        elif style == "tuck":
            if side < 0:
                px(left - 1, top + 3, left, top + 5, body_color)
            else:
                px(right, top + 3, right + 1, top + 5, body_color)
        else:
            if side < 0:
                px(left - 2, top + 3, left, top + 5, body_color)
            else:
                px(right, top + 3, right + 2, top + 5, body_color)

    left_arm = right_arm = arms
    if arms == "wave1":
        left_arm, right_arm = "up", "normal"
    elif arms == "wave2":
        left_arm, right_arm = "normal", "up"
    arm(-1, left_arm)
    arm(1, right_arm)

    px(left, top, right, bottom, body_color)

    ey = top + 2
    for side, cx in ((-1, left + 3 + look), (1, right - 4 + look)):
        if eyes == "blink":
            px(cx, ey + 1, cx + 1, ey + 2, eye_color)
        elif eyes == "happy":
            px(cx - 1, ey + 1, cx, ey + 2, eye_color)
            px(cx, ey, cx + 1, ey + 1, eye_color)
            px(cx + 1, ey + 1, cx + 2, ey + 2, eye_color)
        elif eyes == "surprised":
            px(cx, ey - 1, cx + 1, ey + 2, eye_color)
        elif eyes == "dizzy":
            for dx, dy in ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)):
                px(cx + dx, ey + dy, cx + dx + 1, ey + dy + 1, eye_color)
        elif eyes == "sleep":
            px(cx - 1, ey + 1, cx + 2, ey + 2, eye_color)
        elif eyes == "angry":
            px(cx, ey, cx + 1, ey + 2, eye_color)
            brow = cx - 1 if side < 0 else cx + 1
            px(brow, ey - 1, brow + 1, ey, eye_color)
        else:
            px(cx, ey, cx + 1, ey + 2, eye_color)
        if blush:
            if side < 0:
                px(cx - 2, ey + 2, cx, ey + 3, blush_color)
            else:
                px(cx + 1, ey + 2, cx + 3, ey + 3, blush_color)

    if mouth:
        mx = (left + right) // 2
        my = ey + 2
        if mouth == "open":
            px(mx - 1, my, mx + 1, max(my + 1, min(my + 2, bottom)), eye_color)
        else:
            px(mx - 1, my, mx + 1, my + 1, eye_color)

    painter.end()
    return QPixmap.fromImage(image)


def particle_pixmap(kind, unit):
    rows = PATTERNS[kind]
    color = PARTICLE_COLORS[kind]
    scale = max(2, int(unit * 0.75))
    width = len(rows[0]) * scale
    height = len(rows) * scale
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == "X":
                painter.fillRect(x * scale, y * scale, scale, scale, _qc(color))
    painter.end()
    return QPixmap.fromImage(image)
