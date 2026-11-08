from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap

GRID_W = 18
GRID_H = 13

SIZE_UNITS = [6, 8, 10, 12]

PALETTES = [
    ("Claude", 0xFFD97757, 0xFF1A1A1A),
    ("Мятный", 0xFF4FBF98, 0xFF12241D),
    ("Лавандовый", 0xFF9B8AEE, 0xFF1B1631),
    ("Небесный", 0xFF4FA8E8, 0xFF0E1C29),
    ("Розовый", 0xFFEE85AE, 0xFF2A1220),
    ("Графит", 0xFF5E6670, 0xFFF2F2F2),
    ("Om Nom", 0xFF58B368, 0xFF2B1B12),
    ("Зимний", 0xFF7FB3D5, 0xFF1A2E3B),
    ("Лунный", 0xFF3A445E, 0xFFE8ECF5),
]

OMNOM_INDEX = 6

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


OMNOM_MAP = (
    ".........GG.......",
    "........GGGG......",
    ".......GGGGGO.....",
    ".....OOOOOOOO.....",
    "...OOWWWWWWWOO....",
    "..OWWWWWWWWWWWWO..",
    "..OWWWWWWWWWWWWO..",
    "..OOWWWWWWWWWWOO..",
    "...OOWWWWWWWWO....",
    "....OOOMMMMOOO....",
    ".....OMMMMMSOO....",
    "....OOO..OOO......",
    ".....OO..OO.......",
)


def _render_omnom_frame(key, unit, body_color, eye_color):
    from PySide6.QtCore import Qt as _Qt, QRectF

    eyes, look, arms, legs, squash, blush, mouth = key
    u = float(unit)
    W = 18 * u
    H = 13 * u
    outline_col = _qc(0xFF2A4223)
    outline_soft = QColor(35, 51, 31, 255)
    body_col = _qc(body_color)
    shade_col = _qc(mix_color(body_color, 0xFF1E3A1A, 0.22))
    white_col = _qc(0xFFFFFFFF)
    pupil_col = _qc(0xFF1A1A1A)
    mouth_col = _qc(0xFF3E2A1A)
    leaf_col = _qc(mix_color(body_color, 0xFFFFFFFF, 0.25))
    look = max(-1, min(1, int(look or 0)))

    canvas = QImage(int(W), int(H), QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(QColor(0, 0, 0, 0))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    def sq(vx, vy, vw, vh):
        return QRectF(vx * u, vy * u, vw * u, vh * u)

    # squash geometry
    if squash > 0:
        bw, bh = 15.0, 8.2
        by = 2.8
    elif squash < 0:
        bw, bh = 13.0, 10.0
        by = 1.8
    else:
        bw, bh = 14.0, 9.2
        by = 2.2
    bx = (18.0 - bw) / 2.0
    foot_dy = 0.0
    if legs == "tuck":
        foot_dy = 0.5
    elif legs == "dangle":
        foot_dy = -0.5

    # feet (behind body, small ovals)
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    painter.setBrush(body_col)
    for fx in (5.0, 10.6):
        painter.drawEllipse(sq(fx, 11.0 + foot_dy, 2.8, 1.6))

    # sprout: thin stem + single leaf (Om Nom style)
    painter.setBrush(body_col)
    painter.drawRect(sq(8.7, 0.6, 0.6, 1.9))
    painter.save()
    painter.translate(9.0 * u, 0.7 * u)
    painter.rotate(-18)
    painter.setBrush(leaf_col)
    painter.drawEllipse(sq(-1.5, -0.6, 3.0, 1.2))
    painter.restore()

    # body
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    painter.setBrush(body_col)
    painter.drawEllipse(sq(bx, by, bw, bh))
    # bottom shade under mouth
    painter.setBrush(shade_col)
    painter.save()
    painter.setClipRect(sq(bx, by + bh * 0.55, bw, bh * 0.45))
    painter.drawEllipse(sq(bx, by + bh * 0.55, bw, bh))
    painter.restore()

    # outline
    painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    pen = QPen(outline_soft)
    pen.setWidth(max(1, int(0.55 * u)))
    painter.setPen(pen)
    painter.drawEllipse(sq(bx, by, bw, bh))

    # eyes
    ew, eh = 4.9, 3.9
    if eyes == "surprised":
        ew, eh = 5.4, 4.4
    centers = [(6.4, 5.2), (11.6, 5.2)]
    for cx, cy in centers:
        ex, ey = cx - ew / 2, cy - eh / 2
        if eyes in ("sleep", "blink"):
            painter.setBrush(pupil_col)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(sq(cx - 2.2, cy - 0.28, 4.4, 0.56))
        elif eyes == "happy":
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            p = QPen(outline_col)
            p.setWidth(max(1, int(0.5 * u)))
            p.setCapStyle(_Qt.PenCapStyle.RoundCap)
            painter.setPen(p)
            painter.drawArc(sq(cx - 2.2, cy - 0.9, 4.4, 2.6), 200 * 16, 140 * 16)
        elif eyes == "dizzy":
            painter.setBrush(white_col)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(sq(ex, ey, ew, eh))
            kp = QPen(pupil_col)
            kp.setWidth(max(1, int(0.55 * u)))
            painter.setPen(kp)
            s = 1.5
            painter.drawLine(int((cx - s) * u), int((cy - s) * u), int((cx + s) * u), int((cy + s) * u))
            painter.drawLine(int((cx + s) * u), int((cy - s) * u), int((cx - s) * u), int((cy + s) * u))
        else:
            painter.setBrush(white_col)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(sq(ex, ey, ew, eh))
            px = cx + look * 0.65
            py = cy - 0.35
            pr = 1.18
            painter.setBrush(pupil_col)
            painter.drawEllipse(sq(px - pr, py - pr, pr * 2, pr * 2))
            if eyes == "angry":
                bp = QPen(outline_col)
                bp.setWidth(max(1, int(0.7 * u)))
                painter.setPen(bp)
                if cx < 9:
                    painter.drawLine(int((cx - 2.4) * u), int((cy - 2.6) * u), int((cx + 2.2) * u), int((cy - 1.6) * u))
                else:
                    painter.drawLine(int((cx - 2.2) * u), int((cy - 1.6) * u), int((cx + 2.4) * u), int((cy - 2.6) * u))

    # mouth with teeth (closed when sleeping)
    if eyes == "sleep":
        pass
    else:
        mx, my, mw, mh = 5.0, 8.2, 8.0, 2.6
        painter.setBrush(mouth_col)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(sq(mx, my, mw, mh), 1.2 * u, 1.2 * u)
        # teeth
        painter.setBrush(white_col)
        teeth = [(5.7, 8.5, 1.6, 1.0), (7.5, 8.5, 1.6, 1.0), (9.3, 8.5, 1.6, 1.0), (11.1, 8.5, 1.5, 1.0)]
        for tx, ty, tw, th in teeth:
            painter.drawRoundedRect(sq(tx, ty, tw, th), 0.25 * u, 0.25 * u)
        # lower teeth hints
        painter.setBrush(white_col)
        painter.drawRoundedRect(sq(7.2, 10.0, 1.6, 0.55), 0.2 * u, 0.2 * u)
        painter.drawRoundedRect(sq(9.2, 10.0, 1.6, 0.55), 0.2 * u, 0.2 * u)
        # outline lip
        lp = QPen(outline_soft)
        lp.setWidth(max(1, int(0.5 * u)))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.setPen(lp)
        painter.drawRoundedRect(sq(mx, my, mw, mh), 1.2 * u, 1.2 * u)

    painter.end()
    return QPixmap.fromImage(canvas)


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
    pix = QPixmap.fromImage(image)
    return apply_accessory(pix, "none", unit) if False else pix


def apply_accessory(pixmap, accessory, unit):
    if accessory == "none" or pixmap.isNull():
        return pixmap
    from PySide6.QtGui import QColor as _QC

    out = QPixmap(pixmap.size())
    out.fill(_QC(0, 0, 0, 0))
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.drawPixmap(0, 0, pixmap)
    u = float(unit)
    if accessory == "hat":
        painter.setBrush(_qc(0xFFE0B341))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(QRectF(6.2 * u, 0.4 * u, 5.6 * u, 1.6 * u), 0.4 * u, 0.4 * u)
        painter.drawRoundedRect(QRectF(5.4 * u, 1.7 * u, 7.2 * u, 0.7 * u), 0.3 * u, 0.3 * u)
    elif accessory == "bow":
        painter.setBrush(_qc(0xFFFF5C7A))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(QRectF(7.2 * u, 0.8 * u, 1.8 * u, 1.4 * u))
        painter.drawEllipse(QRectF(9.0 * u, 0.8 * u, 1.8 * u, 1.4 * u))
        painter.setBrush(_qc(0xFFE0B341))
        painter.drawEllipse(QRectF(8.4 * u, 1.0 * u, 1.2 * u, 1.0 * u))
    painter.end()
    return out


def list_custom_skins(skins_dir):
    """Return list of skin names found under assets/skins/<name>/ (each needs at least frame.png or skin.json)."""
    import os

    if not skins_dir or not os.path.isdir(skins_dir):
        return []
    names = []
    for name in sorted(os.listdir(skins_dir)):
        base = os.path.join(skins_dir, name)
        if os.path.isdir(base) and (os.path.exists(os.path.join(base, "frame.png")) or os.path.exists(os.path.join(base, "skin.json"))):
            names.append(name)
    return names


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
