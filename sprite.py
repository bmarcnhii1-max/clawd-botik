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
    ("Om Nom", 0xFF58B368, 0xFF2B1B12),
]

OMNOM_INDEX = len(PALETTES) - 1

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


def body_shape(index):
    return "omnom" if int(index) % len(PALETTES) == OMNOM_INDEX else "claw"


def sprite_size(unit):
    return GRID_W * unit, GRID_H * unit


def _render_omnom_frame(key, unit, body_color, eye_color):
    eyes, look, arms, legs, squash, blush, mouth = key
    outline = 0xFF23331F
    mouth_dark = 0xFF2A4223
    white = 0xFFFFFFFF
    pupil = 0xFF1A1A1A
    shade = mix_color(body_color, 0xFF1E3A1A, 0.22)
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

    widen = 0
    dy = 0
    if squash > 0:
        widen, dy = 1, 1
    elif squash < 0:
        widen, dy = -1, -1
    if legs == "tuck":
        dy += 1
    if legs == "dangle":
        dy -= 1

    def row(y, x0, x1, color, edge=0):
        px(x0 - widen - edge, y + dy, x1 + widen + edge, y + 1 + dy, color)

    # Sprout on top of the head.
    row(0, 7, 11, outline)
    row(0, 8, 10, body_color)
    row(1, 8, 10, outline)
    row(1, 9, 10, body_color)

    # Round bean body with a dark rim and shaded belly.
    body_rows = (
        (2, 3, 15),
        (3, 3, 15),
        (4, 2, 16),
        (5, 2, 16),
        (6, 2, 16),
        (7, 2, 16),
        (8, 2, 16),
        (9, 2, 16),
        (10, 3, 15),
    )
    for y, x0, x1 in body_rows:
        row(y, x0, x1, outline, edge=1)
    for index, (y, x0, x1) in enumerate(body_rows):
        fill = shade if index >= len(body_rows) - 2 else body_color
        row(y, x0, x1, fill)

    # Stubby feet.
    if legs == "walk1":
        feet = ((4, 7, 2), (11, 14, 1))
    elif legs == "walk2":
        feet = ((4, 7, 1), (11, 14, 2))
    elif legs == "tuck":
        feet = ()
    else:
        feet = ((4, 7, 2), (11, 14, 2))
    for fx0, fx1, foot_height in feet:
        for step in range(foot_height):
            row(11 + step, fx0, fx1, outline, edge=1)
        for step in range(foot_height):
            row(11 + step, fx0, fx1, body_color)

    # Tiny side arms.
    def arm(side, style):
        if style == "tuck":
            return
        if style == "up":
            y0, y1 = 5, 7
        else:
            y0, y1 = 8, 10
        if side < 0:
            ax0, ax1 = 1, 3
        else:
            ax0, ax1 = 15, 17
        for y in range(y0, y1):
            row(y, ax0, ax1, outline, edge=1)
        for y in range(y0, y1):
            row(y, ax0, ax1, body_color)

    left_arm = right_arm = arms
    if arms == "wave1":
        left_arm, right_arm = "up", "normal"
    elif arms == "wave2":
        left_arm, right_arm = "normal", "up"
    arm(-1, left_arm)
    arm(1, right_arm)

    # Huge signature eyes.
    look = max(-1, min(1, int(look or 0)))
    boxes = ((3 - widen, 3, 8, 8), (10, 3, 15 + widen, 8))

    def eye_rim(box):
        bx0, by0, bx1, by1 = box
        px(bx0 - 1, by0 - 1 + dy, bx1 + 1, by1 + 1 + dy, outline)

    def eye_white(box):
        bx0, by0, bx1, by1 = box
        px(bx0, by0 + dy, bx1, by1 + dy, white)

    def pupils(box, py0=5, py1=7):
        bx0, _by0, bx1, _by1 = box
        qx0 = min(max(6 + look if box[0] < 9 else 10 + look, bx0), bx1 - 2)
        px(qx0, py0 + dy, qx0 + 2, py1 + dy, pupil)

    if eyes in ("sleep", "blink"):
        for box in boxes:
            bx0, _by0, bx1, _by1 = box
            px(bx0, 5 + dy, bx1, 6 + dy, pupil)
    elif eyes == "happy":
        for box in boxes:
            bx0, _by0, bx1, by1 = box
            px(bx0, by1 - 2 + dy, bx0 + 1, by1 - 1 + dy, pupil)
            px(bx1 - 1, by1 - 2 + dy, bx1, by1 - 1 + dy, pupil)
            px(bx0, by1 - 1 + dy, bx1, by1 + dy, pupil)
    elif eyes == "dizzy":
        for box in boxes:
            eye_rim(box)
            eye_white(box)
            bx0, by0, bx1, by1 = box
            for step in range(5):
                px(bx0 + step, by0 + step + dy, bx0 + step + 1, by0 + step + 1 + dy, pupil)
                px(bx1 - 1 - step, by0 + step + dy, bx1 - step, by0 + step + 1 + dy, pupil)
    else:
        for box in boxes:
            eye_rim(box)
        if eyes == "surprised":
            for (bx0, by0, bx1, by1) in boxes:
                px(bx0 - 1, by0 - 1 + dy, bx1 + 1, by1 + 1 + dy, outline)
                px(bx0, by0 + dy, bx1, by1 + dy, white)
            for box in boxes:
                bx0, _by0, bx1, _by1 = box
                cx = (bx0 + bx1) // 2
                px(cx - 1, 5 + dy, cx + 1, 7 + dy, pupil)
        else:
            for box in boxes:
                eye_white(box)
            for box in boxes:
                pupils(box)
        if eyes == "angry":
            (l0, ly0, _l1, _ly1), (_r0, _ry0, r1, _ry1) = boxes
            px(l0 - 1, ly0 - 1 + dy, l0 + 2, ly0 + dy, pupil)
            px(r1 - 2, ly0 - 1 + dy, r1 + 1, ly0 + dy, pupil)

    # Wide toothy grin.
    mx0, mx1, my0, my1 = 3 - widen, 15 + widen, 8, 11
    px(mx0 - 1, my0 - 1 + dy, mx1 + 1, my1 + 1 + dy, outline)
    px(mx0, my0 + dy, mx1, my1 + dy, mouth_dark)
    for tx in (mx0 + 1, mx0 + 5, mx0 + 9):
        px(tx, my0 + dy, tx + 2, my0 + 1 + dy, white)
    for tx in (mx0 + 3, mx0 + 7):
        px(tx, my1 - 1 + dy, tx + 2, my1 + dy, white)
    if mouth == "open":
        px(mx0 + 4, my1 + dy, mx1 - 4, my1 + 1 + dy, mouth_dark)

    painter.end()
    return QPixmap.fromImage(image)


def render_frame(key, unit, body_color, eye_color, body_shape="claw"):
    if body_shape == "omnom":
        return _render_omnom_frame(key, unit, body_color, eye_color)

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
