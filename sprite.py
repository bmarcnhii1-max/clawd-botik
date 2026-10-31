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
        if x1 <= x0 or y1 <= y0:
            return
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

    def ell(cx, cy, rx, ry, color, y_from=None, y_to=None):
        y = cy - ry if y_from is None else max(y_from, cy - ry)
        end_y = cy + ry if y_to is None else min(y_to, cy + ry)
        while y < end_y - 1e-9:
            t = (y + 0.25 - cy) / ry if ry > 0 else 0.0
            dx = rx * (max(0.0, 1.0 - t * t) ** 0.5)
            px(cx - dx, y + dy, cx + dx, y + 0.5 + dy, color)
            y += 0.5

    def disc(cx, cy, rx, ry, color):
        ell(cx, cy, rx, ry, color)

    # Sprout: thin stem with a small leaf leaning right.
    px(8.2, 0.8 + dy, 9.8, 2.4 + dy, outline)
    px(8.7, 0.8 + dy, 9.3, 2.4 + dy, body_color)
    disc(10.1, 0.9 + dy, 1.0, 0.65, outline)
    disc(10.1, 0.9 + dy, 0.6, 0.35, body_color)

    # Round head with a dark rim and a shaded belly.
    head = (9.0, 6.5, 6.5 + widen, 4.5)
    ell(head[0], head[1], head[2] + 0.6, head[3] + 0.6, outline)
    ell(head[0], head[1], head[2], head[3], body_color)
    ell(head[0], head[1], head[2], head[3], shade, y_from=8.3)

    # Stubby feet.
    if legs == "walk1":
        feet = ((5.0, 7.0, 12.6), (11.0, 13.0, 11.8))
    elif legs == "walk2":
        feet = ((5.0, 7.0, 11.8), (11.0, 13.0, 12.6))
    elif legs == "tuck":
        feet = ()
    else:
        feet = ((5.0, 7.0, 12.6), (11.0, 13.0, 12.6))
    for fx0, fx1, fy1 in feet:
        px(fx0 - 0.5 - widen * 0.5, 10.3 + dy, fx1 + 0.5 + widen * 0.5, fy1 + dy, outline)
        px(fx0 - widen * 0.5, 10.8 + dy, fx1 + widen * 0.5, fy1 - 0.5 + dy, body_color)

    # Big signature eyes.
    look = max(-1.0, min(1.0, float(look or 0)))
    eye_scale = 1.15 if eyes == "surprised" else 1.0
    left_eye = (6.2 - widen * 0.5, 5.0, 2.5 * eye_scale, 2.2 * eye_scale)
    right_eye = (11.8 + widen * 0.5, 5.0, 2.5 * eye_scale, 2.2 * eye_scale)

    def eye_ball(box):
        ecx, ecy, erx, ery = box
        disc(ecx, ecy + dy, erx + 0.4, ery + 0.4, outline)
        disc(ecx, ecy + dy, erx, ery, white)

    def eye_pupils(box, inner=False):
        ecx, ecy, _erx, _ery = box
        side = 1.0 if ecx < 9.0 else -1.0
        disc(ecx + side * 1.2 + look, ecy + dy, 0.6, 1.0, pupil)

    if eyes in ("sleep", "blink"):
        for box in (left_eye, right_eye):
            ecx, ecy, erx, _ery = box
            px(ecx - erx * 0.6, ecy - 0.1 + dy, ecx + erx * 0.6, ecy + 0.5 + dy, pupil)
    elif eyes == "happy":
        for box in (left_eye, right_eye):
            ecx, ecy, erx, ery = box
            px(ecx - erx + 0.3, ecy + dy, ecx - erx + 1.1, ecy + ery - 0.4 + dy, pupil)
            px(ecx + erx - 1.1, ecy + dy, ecx + erx - 0.3, ecy + ery - 0.4 + dy, pupil)
            px(ecx - erx + 0.3, ecy + ery - 0.8 + dy, ecx + erx - 0.3, ecy + ery + dy, pupil)
    elif eyes == "dizzy":
        for box in (left_eye, right_eye):
            eye_ball(box)
            ecx, ecy, erx, ery = box
            for step in range(5):
                t = -1.6 + step * 0.8
                px(ecx + t, ecy + t * 0.8 + dy, ecx + t + 0.8, ecy + t * 0.8 + 0.8 + dy, pupil)
                px(ecx - t, ecy + t * 0.8 + dy, ecx - t + 0.8, ecy + t * 0.8 + 0.8 + dy, pupil)
    else:
        for box in (left_eye, right_eye):
            eye_ball(box)
        for box in (left_eye, right_eye):
            eye_pupils(box)
        if eyes == "angry":
            (lx, ly, lrx, _lry), (rx, _ry, rrx, _rry) = (left_eye, right_eye)
            px(lx - lrx - 0.2, ly - 2.6 + dy, lx - 0.5, ly - 1.8 + dy, pupil)
            px(rx + 0.5, ly - 2.6 + dy, rx + rrx + 0.2, ly - 1.8 + dy, pupil)

    # Wide toothy mouth. Asleep Om Nom keeps his mouth shut.
    if eyes == "sleep":
        px(6.5, 8.5 + dy, 11.5, 9.3 + dy, outline)
        px(7.0, 8.7 + dy, 11.0, 9.1 + dy, mouth_dark)
        painter.end()
        return QPixmap.fromImage(image)
    my1 = 10.8 if mouth == "open" else 9.8
    mx0, mx1, my0 = 4.0 - widen * 0.5, 14.0 + widen * 0.5, 7.8
    px(mx0 - 0.5, my0 - 0.5 + dy, mx1 + 0.5, my1 + 0.5 + dy, outline)
    px(mx0, my0 + dy, mx1, my1 + dy, mouth_dark)
    for tx0, tx1 in ((5.0, 6.5), (8.2, 9.8), (11.5, 13.0)):
        px(tx0, my0 + dy, tx1, my0 + 1.2 + dy, white)
    for tx0, tx1 in ((6.5, 8.0), (10.0, 11.5)):
        px(tx0, my1 - 0.7 + dy, tx1, my1 + dy, white)

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
