import math
import random
import time

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QPainter, QRegion
from PySide6.QtWidgets import QApplication, QWidget

import sprite
from bubble import BubbleWindow
from config import save_config
from i18n import ui
from phrases import get_default_persona, get_phrases


def clamp(value, low, high):
    if high < low:
        return low
    return low if value < low else high if value > high else value


class PetWindow(QWidget):
    HOP_GRAVITY = 3200.0
    FLY_GRAVITY = 2600.0
    WALK_SPEED = 8.0
    EDGE_STEP = 10.0

    def __init__(self, config, ai_client):
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.cfg = config
        self.ai = ai_client
        self.chat_callback = None
        self.context_callback = None
        self.language_callback = None
        self.visibility_callback = None
        self.notify_callback = None
        self.bubble = BubbleWindow()

        self._frames = {}
        self._particle_cache = {}
        self._particles = []
        self._pixmap = None
        self._frame_key = None
        self._last_wx = None
        self._last_wy = None

        self._now = time.monotonic()
        self._last_tick = self._now
        self._last_interaction = self._now
        self._next_action = self._now + 4.0
        self._next_blink = self._now + 2.0
        self._blink_until = 0.0
        self._next_z = 0.0
        self._next_dream = 0.0
        self._next_thought = 0.0
        self._thought_out = False
        self._last_ai_reply = 0.0
        self._look = 0
        self._expr = None
        self._expr_until = 0.0
        self._squash_until = 0.0
        self._wave_until = 0.0
        self._hop_active = False
        self._hop_off = 0.0
        self._hop_vy = 0.0
        self._walk_target = 0.0
        self._walk_in = False
        self._next_heart = 0.0
        self._touch = None
        self._last_tap = 0.0
        self._tap_streak = []
        self._lang_cooldown = 0.0
        self._recent_taps = []
        self._ai_history = self._load_history()
        self._pending_user = ""
        self._ai_inflight = False
        self._ai_queue = []
        self._mask_key = None
        self._state = "idle"
        self._vx = 0.0
        self._vy = 0.0
        self._x = 0.0
        self._y = 0.0

        self._size_index = 0
        self._color_index = 0
        self._unit = 6
        self._sw = 1
        self._sh = 1
        self._margin = 10
        self._apply_metrics()

        self.ai.finished.connect(self._on_ai_finished)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def _apply_metrics(self):
        self._size_index = int(clamp(int(self.cfg.get("size", 1)), 0, len(sprite.SIZE_UNITS) - 1))
        self._color_index = int(self.cfg.get("color", 0)) % len(sprite.PALETTES)
        self._unit = sprite.SIZE_UNITS[self._size_index]
        self._sw, self._sh = sprite.sprite_size(self._unit)
        self._margin = int(max(self._sw, self._sh) * 0.25) + 4
        self.setFixedSize(self._sw + self._margin * 2, self._sh + self._margin * 2)
        self._frames.clear()
        self._particle_cache.clear()
        self._frame_key = None
        self._pixmap = None
        self._last_wx = None
        self._last_wy = None
        self._mask_key = None
        self._update_mask()

    def _update_mask(self):
        pad = max(6, int(self._unit * 3.0))
        region = QRegion(
            self._margin - pad,
            self._margin - pad,
            self._sw + pad * 2,
            self._sh + pad * 2,
        )
        win_x = self._x - self._margin
        win_y = self._y + self._hop_off - self._margin
        positions = []
        for part in self._particles:
            px = int((part["x"] - win_x) // 4) * 4 - 2
            py = int((part["y"] - win_y) // 4) * 4 - 2
            positions.append((px, py, part["pix"].width(), part["pix"].height()))
            region = region.united(
                QRegion(px, py, part["pix"].width() + 4, part["pix"].height() + 4)
            )
        key = (self.width(), self.height(), tuple(positions))
        if key == self._mask_key:
            return
        self._mask_key = key
        self.setMask(region)

    def _screen_geo(self):
        center = QPoint(int(self._x + self._sw / 2), int(self._y + self._sh / 2))
        screen = QApplication.screenAt(center)
        if screen is None:
            screen = self.screen() or QApplication.primaryScreen()
        return screen.availableGeometry()

    def _screen_geo_at(self, x, y):
        screen = QApplication.screenAt(QPoint(int(x), int(y)))
        if screen is None:
            screen = QApplication.primaryScreen()
        return screen.availableGeometry()

    def _bounds(self, geo):
        return (
            float(geo.left()),
            float(geo.right() - self._sw + 1),
            float(geo.top()),
            float(geo.bottom() - self._sh + 1),
        )

    def _restore_position(self):
        px = self.cfg.get("pos_x")
        py = self.cfg.get("pos_y")
        if px is None or py is None:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry()
            min_x, max_x, min_y, max_y = self._bounds(geo)
            self._x = max_x - self._unit * 3
            self._y = max_y
            return
        geo = self._screen_geo_at(px, py)
        min_x, max_x, min_y, max_y = self._bounds(geo)
        self._x = clamp(float(px), min_x, max_x)
        self._y = clamp(float(py), min_y, max_y)

    def _save_position(self):
        self.cfg["pos_x"] = int(self._x)
        self.cfg["pos_y"] = int(self._y)
        save_config(self.cfg)

    def start(self):
        self._restore_position()
        self.show_pet()
        QTimer.singleShot(700, self._greet)

    def show_pet(self):
        self.show()
        self.raise_()

    def _notify_visibility(self, visible):
        if callable(self.visibility_callback):
            self.visibility_callback(bool(visible))

    def _notify(self, text):
        if callable(self.notify_callback):
            self.notify_callback(str(text))

    def _greet(self):
        if not self.isVisible():
            return
        self._hop(self._unit * 55)
        self._say("hello")

    def apply_config(self):
        center_x = self._x + self._sw / 2.0
        center_y = self._y + self._sh / 2.0
        self._apply_metrics()
        self._x = center_x - self._sw / 2.0
        self._y = center_y - self._sh / 2.0
        self._clamp_to_screen()
        self.update()

    def _clamp_to_screen(self):
        geo = self._screen_geo()
        min_x, max_x, min_y, max_y = self._bounds(geo)
        self._x = clamp(self._x, min_x, max_x)
        self._y = clamp(self._y, min_y, max_y)

    def _sleep_timeout(self):
        return max(0, int(self.cfg.get("sleep_seconds", 180) or 0))

    def _tick(self):
        now = time.monotonic()
        dt = clamp(now - self._last_tick, 0.0, 0.05)
        self._last_tick = now
        self._now = now
        try:
            touch = self._touch
            if self._state == "press" and touch is not None and now - touch["t0"] >= 0.4:
                self._start_pet(now)
            if self._state == "pet":
                if now >= self._next_heart:
                    self._next_heart = now + 0.45
                    self._spawn_particle("heart")
            elif self._state == "fly":
                self._step_fly(dt, now)
            elif self._state in ("idle", "walk", "sleep"):
                self._step_ground(dt, now)
            self._step_hop(dt, now)
            self._step_particles(dt)
            self._refresh()
        except Exception:
            pass

    def _step_hop(self, dt, now):
        if not self._hop_active:
            return
        self._hop_off += self._hop_vy * dt
        self._hop_vy += self.HOP_GRAVITY * dt
        if self._hop_off >= 0.0:
            self._hop_off = 0.0
            self._hop_vy = 0.0
            self._hop_active = False
            self._squash_until = now + 0.1

    def _start_fall(self):
        self._state = "fly"
        self._vx = 0.0
        self._vy = 0.0

    def _step_ground(self, dt, now):
        geo = self._screen_geo()
        min_x, max_x, min_y, max_y = self._bounds(geo)

        self._walk_in = False
        if self._state != "walk":
            if self._x < min_x or self._x > max_x:
                step = self._unit * self.EDGE_STEP * dt
                if self._x < min_x:
                    self._x = min(min_x, self._x + step)
                    self._look = 1
                else:
                    self._x = max(max_x, self._x - step)
                    self._look = -1
                self._walk_in = True
            else:
                self._x = clamp(self._x, min_x, max_x)

        if self.cfg.get("gravity"):
            if self._y < max_y - 0.5 and not self._hop_active:
                self._start_fall()
                return
            self._y = min(self._y, max_y)
        else:
            self._y = clamp(self._y, min_y, max_y)

        if self._state == "walk":
            direction = 1 if self._walk_target > self._x else -1
            self._look = direction
            self._x += direction * self._unit * self.WALK_SPEED * dt
            reached = (direction > 0 and self._x >= self._walk_target) or (
                direction < 0 and self._x <= self._walk_target
            )
            hit_edge = (direction < 0 and self._x <= min_x) or (direction > 0 and self._x >= max_x)
            if reached or hit_edge:
                self._x = clamp(self._x, min_x, max_x)
                self._state = "idle"
                self._next_action = now + random.uniform(2.5, 6.0)
                self._save_position()
            return

        if self._state == "sleep":
            if now >= self._next_z:
                self._next_z = now + 1.6
                self._spawn_particle("zzz")
            if now >= self._next_dream:
                self._next_dream = now + random.uniform(24.0, 42.0)
                self._dream()
            return

        if now >= self._next_blink:
            self._blink_until = now + 0.13
            self._next_blink = now + (0.35 if random.random() < 0.15 else random.uniform(2.0, 5.5))

        timeout = self._sleep_timeout()
        if (
            timeout
            and now - self._last_interaction > timeout
            and not self._hop_active
            and not self._walk_in
            and not self._ai_inflight
        ):
            self._state = "sleep"
            self._look = 0
            self._next_z = now + 0.6
            self._next_dream = now + random.uniform(10.0, 18.0)
            self._hide_bubble()
            return

        if now < self._next_action or self._hop_active or self._walk_in:
            return
        self._next_action = now + random.uniform(3.5, 9.0)
        self._maybe_think_aloud(now)

        if not self.cfg.get("wander", True):
            self._look = random.choice((-1, 0, 1))
            return

        roll = random.random()
        if roll < 0.45:
            distance = random.uniform(self._unit * 10, self._unit * 35) * random.choice((-1, 1))
            target = clamp(self._x + distance, min_x, max_x)
            if abs(target - self._x) > self._unit * 2:
                self._walk_target = target
                self._state = "walk"
        elif roll < 0.65:
            self._look = random.choice((-1, 0, 1))
        elif roll < 0.8:
            self._say("idle")
        elif roll < 0.92:
            self._hop(self._unit * 50)
        else:
            self._wave_until = now + 1.6

    def _step_fly(self, dt, now):
        geo = self._screen_geo()
        min_x, max_x, min_y, max_y = self._bounds(geo)
        self._x += self._vx * dt
        self._y += self._vy * dt
        gravity = self.cfg.get("gravity")

        if gravity:
            self._vy += self.FLY_GRAVITY * dt
            self._vx *= math.exp(-0.4 * dt)
        else:
            friction = math.exp(-2.0 * dt)
            self._vx *= friction
            self._vy *= friction

        if self._x < min_x:
            self._x = min_x
            self._vx = abs(self._vx) * 0.55
            self._squash_until = now + 0.08
        elif self._x > max_x:
            self._x = max_x
            self._vx = -abs(self._vx) * 0.55
            self._squash_until = now + 0.08

        if self._y < min_y:
            self._y = min_y
            self._vy = abs(self._vy) * 0.55
        elif self._y > max_y:
            self._y = max_y
            if gravity and self._vy < 700:
                self._land(now)
            else:
                self._vy = -abs(self._vy) * 0.45
                self._vx *= 0.8
                self._squash_until = now + 0.1

        if self._state == "fly" and not gravity and math.hypot(self._vx, self._vy) < 60:
            self._land(now)

    def _land(self, now):
        self._state = "idle"
        self._vx = 0.0
        self._vy = 0.0
        self._squash_until = now + 0.14
        self._next_action = now + random.uniform(2.0, 5.0)
        self._save_position()

    def _hop(self, strength):
        if self._state not in ("idle", "walk"):
            return
        self._hop_active = True
        self._hop_vy = -float(strength)
        if self._hop_off > 0:
            self._hop_off = 0.0

    def _set_expr(self, expr, duration):
        self._expr = expr
        self._expr_until = time.monotonic() + duration

    def _start_pet(self, now):
        self._state = "pet"
        self._next_heart = now + 0.1

    def _stroke(self):
        self._spawn_particle("heart")
        if random.random() < 0.25:
            self._say("pet")

    def _end_pet(self, now):
        self._state = "idle"
        self._set_expr("happy", 2.2)
        self._next_action = now + random.uniform(3.0, 6.0)
        if random.random() < 0.6:
            self._say("pet")

    def _tap(self, now):
        self._tap_streak = [t for t in self._tap_streak if now - t < 0.9] + [now]
        if len(self._tap_streak) >= 3:
            self._tap_streak = []
            self._last_tap = 0.0
            self._recent_taps = []
            self._open_chat()
            return
        if now - self._last_tap < 0.32:
            self._last_tap = 0.0
            self._hop(self._unit * 80)
            self._set_expr("happy", 1.3)
            for _ in range(3):
                self._spawn_particle("spark")
            if random.random() < 0.4:
                self._say("jump")
            return
        self._last_tap = now
        self._recent_taps = [t for t in self._recent_taps if now - t < 2.5] + [now]
        if len(self._recent_taps) >= 6:
            self._recent_taps = []
            self._set_expr("angry", 2.5)
            self._say("annoyed")
            return
        self._squash_until = now + 0.12
        self._set_expr("surprised", 0.45)
        self._hop(self._unit * 40)
        if random.random() < 0.35:
            self._say("tap")

    def language(self):
        code = str(self.cfg.get("lang", "ru"))
        return code if code in ("ru", "uk", "en") else "ru"

    def set_language(self, code, announce=True):
        code = str(code)
        if code not in ("ru", "uk", "en"):
            code = "ru"
        if code == self.language():
            return
        self.cfg["lang"] = code
        save_config(self.cfg)
        now = time.monotonic()
        self._expr = "dizzy"
        self._expr_until = now + 1.4
        for _ in range(3):
            self._spawn_particle("spark")
        if announce:
            self._say_raw(ui(code)["language_switched"], 2.6)
        if callable(self.language_callback):
            self.language_callback(code)

    def _toggle_language(self, now):
        if now < self._lang_cooldown:
            return
        self._lang_cooldown = now + 1.5
        self._last_interaction = now
        order = ("ru", "uk", "en")
        self.set_language(order[(order.index(self.language()) + 1) % len(order)])

    def _note_shake(self, touch, dx, now):
        if abs(dx) < 5:
            return
        direction = 1 if dx > 0 else -1
        last = touch.get("shake_dir") or 0
        if last and direction != last:
            hits = [t for t in touch.get("shake_hits") or [] if now - t < 0.8]
            hits.append(now)
            touch["shake_hits"] = hits
            if len(hits) >= 4:
                touch["shake_hits"] = []
                self._toggle_language(now)
        touch["shake_dir"] = direction

    def _open_chat(self):
        if callable(self.chat_callback):
            self.chat_callback()

    def ask_ai(self, text):
        text = str(text or "").strip()
        if not text:
            return
        text = text[:1000]
        if not self.ai.ready():
            message = random.choice(get_phrases(self.language())["ai_off"])
            if self.isVisible():
                self._say_raw(message, 4.0)
            else:
                self._notify(message)
            return
        if not self.isVisible():
            self.show_pet()
        if self._state == "sleep":
            self._state = "idle"
            self._hide_bubble()
        self._last_interaction = time.monotonic()
        if self._ai_inflight:
            if len(self._ai_queue) < 4:
                self._ai_queue.append(text)
            return
        self._dispatch_ai(text)

    def _maybe_think_aloud(self, now):
        if self._next_thought <= 0.0:
            self._next_thought = now + random.uniform(1200.0, 1800.0)
            return
        if now < self._next_thought:
            return
        self._next_thought = now + random.uniform(1200.0, 2700.0)
        if self._state != "idle":
            return
        if not self.cfg.get("ai_thoughts", True):
            return
        if not self.isVisible() or not self.ai.ready():
            return
        if self._ai_inflight or self._ai_queue:
            return
        if now - self._last_ai_reply < 600.0:
            return
        self._think_aloud()

    def _think_aloud(self):
        t = ui(self.language())
        self._ai_inflight = True
        self._thought_out = True
        self._pending_user = ""
        self._last_interaction = time.monotonic()
        messages = [{"role": "system", "content": self._persona()}]
        messages.extend(self._ai_history[-6:])
        messages.append({"role": "user", "content": t["thought_prompt"]})
        self.ai.ask(messages, max_tokens=90)

    def _dispatch_ai(self, text):
        self._ai_inflight = True
        self._pending_user = text
        self._set_expr("happy", 1.5)
        self._say_raw(
            ui(self.language())["thinking"],
            float(self.cfg.get("ai_timeout", 120) or 120) + 5.0,
        )
        messages = [{"role": "system", "content": self._persona()}]
        messages.extend(self._ai_history[-8:])
        messages.append({"role": "user", "content": text})
        self.ai.ask(messages, max_tokens=int(self.cfg.get("ai_max_tokens", 220)))

    def _process_ai_queue(self):
        if self._ai_inflight or not self._ai_queue:
            return
        if not self.ai.ready():
            self._ai_queue.clear()
            return
        self._dispatch_ai(self._ai_queue.pop(0))

    def _persona(self):
        text = str(self.cfg.get("ai_persona", "") or "").strip()
        return text or get_default_persona(self.language())

    def _on_ai_finished(self, reply, error):
        self._ai_inflight = False
        thought = self._thought_out
        self._thought_out = False
        t = ui(self.language())
        visible = self.isVisible()
        if not reply:
            if thought:
                return
            message = t["ai_prefix"] + str(error or t["no_reply"])[:140]
            if visible:
                self._say_raw(message, 6.0)
            else:
                self._notify(message)
        else:
            self._last_ai_reply = time.monotonic()
            if thought:
                self._ai_history.append({"role": "assistant", "content": reply})
                if len(self._ai_history) > 12:
                    del self._ai_history[:-12]
                self._save_history()
            elif self._pending_user:
                self._ai_history.append({"role": "user", "content": self._pending_user})
                self._ai_history.append({"role": "assistant", "content": reply})
                if len(self._ai_history) > 12:
                    del self._ai_history[:-12]
                self._save_history()
            self._set_expr("happy", 2.0)
            self._spawn_particle("spark")
            if visible:
                self._say_raw(reply[:400], clamp(3.0 + len(reply) * 0.05, 3.0, 12.0))
            else:
                self._notify(reply[:400])
        self._pending_user = ""
        if self._ai_queue:
            if reply:
                delay = clamp(3.0 + len(reply) * 0.05, 2.5, 8.0)
            else:
                delay = 2.5
            QTimer.singleShot(int(delay * 1000), self._process_ai_queue)

    def _load_history(self):
        raw = self.cfg.get("ai_history")
        if not isinstance(raw, list):
            return []
        history = []
        for item in raw[-12:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                history.append({"role": role, "content": content[:1000]})
        return history

    def _save_history(self):
        self.cfg["ai_history"] = [dict(item) for item in self._ai_history]
        save_config(self.cfg)

    def clear_history(self):
        self._ai_history = []
        self._pending_user = ""
        self._ai_queue.clear()
        self.cfg["ai_history"] = []
        save_config(self.cfg)
        self._set_expr("happy", 1.2)
        self._spawn_particle("spark")
        self._say_raw(ui(self.language())["history_cleared"], 2.5)

    def _say(self, category):
        if not self.cfg.get("phrases", True) or self._ai_inflight:
            return
        options = get_phrases(self.language()).get(category)
        if not options:
            return
        self._say_raw(random.choice(options))

    def _dream(self):
        if not self.cfg.get("phrases", True) or self._ai_inflight:
            return
        options = get_phrases(self.language()).get("dream") or []
        if not options:
            return
        text = random.choice(options)
        self._say_raw(text, clamp(4.0 + len(text) * 0.06, 4.5, 9.0))

    def _say_raw(self, text, seconds=None):
        text = str(text or "").strip()
        if not text:
            return
        if not self.isVisible():
            self._hide_bubble()
            return
        if seconds is None:
            seconds = 2.0 + len(text) * 0.05
        self.bubble.show_message(text, seconds)
        self._update_bubble_position()

    def _hide_bubble(self):
        self.bubble.hide()

    def _update_bubble_position(self):
        if not self.bubble.isVisible():
            return
        geo = self._screen_geo()
        rect = QRect(int(self._x), int(self._y + self._hop_off), self._sw, self._sh)
        self.bubble.place_near(rect, geo)

    def _particle_pixmap(self, kind):
        key = (kind, self._unit)
        pixmap = self._particle_cache.get(key)
        if pixmap is None:
            pixmap = sprite.particle_pixmap(kind, self._unit)
            self._particle_cache[key] = pixmap
        return pixmap

    def _spawn_particle(self, kind, origin=None):
        if len(self._particles) >= 18:
            return
        try:
            pixmap = self._particle_pixmap(kind)
        except Exception:
            return
        pw = pixmap.width()
        ph = pixmap.height()
        if origin is not None:
            sx = origin[0] - pw / 2.0 + random.uniform(-8, 8)
            sy = origin[1] - ph
            drift = random.uniform(-16, 16)
        elif kind == "zzz":
            sx = self._x + self._sw * 0.72
            sy = self._y + self._hop_off + self._unit * 2
            drift = self._unit * 3
        else:
            sx = self._x + self._sw / 2.0 - pw / 2.0 + random.uniform(-self._sw * 0.25, self._sw * 0.25)
            sy = self._y + self._hop_off + self._unit * 2 - ph
            drift = random.uniform(-16, 16)
        ttl = 1.6 if kind == "zzz" else 1.1
        self._particles.append(
            {
                "pix": pixmap,
                "x": sx,
                "y": sy,
                "vx": drift / 1.1,
                "vy": -random.uniform(40, 60),
                "life": 0.0,
                "ttl": ttl,
                "alpha": 1.0,
            }
        )

    def _step_particles(self, dt):
        alive = []
        for part in self._particles:
            part["life"] += dt
            if part["life"] >= part["ttl"]:
                continue
            part["x"] += part["vx"] * dt
            part["y"] += part["vy"] * dt
            part["vy"] *= math.exp(-1.5 * dt)
            part["alpha"] = max(0.0, 1.0 - part["life"] / part["ttl"])
            alive.append(part)
        self._particles = alive

    def _get_frame(self, key):
        cache_key = (key, self._unit, self._color_index)
        pixmap = self._frames.get(cache_key)
        if pixmap is None:
            _, body, eye = sprite.palette(self._color_index)
            pixmap = sprite.render_frame(key, self._unit, body, eye)
            if len(self._frames) > 96:
                self._frames.clear()
            self._frames[cache_key] = pixmap
        return pixmap

    def _compose(self, now):
        eyes = "open"
        look = self._look
        arms = "normal"
        legs = "stand"
        squash = 0
        blush = False
        mouth = None
        state = self._state

        if state in ("drag", "fly"):
            eyes, arms, legs = "surprised", "up", "dangle"
        elif state == "pet":
            eyes, blush = "happy", True
            squash = 1 if int(now * 3) % 2 else 0
            look = 0
        elif state == "sleep":
            eyes, arms, legs, look = "sleep", "tuck", "tuck", 0
        elif state == "walk":
            legs = "walk1" if int(now * 7) % 2 else "walk2"
        elif state == "press":
            squash = 1

        if self._walk_in and state == "idle":
            legs = "walk1" if int(now * 7) % 2 else "walk2"

        if state in ("idle", "walk") and now < self._wave_until:
            arms = "wave1" if int(now * 5) % 2 else "wave2"

        if self._hop_active and state in ("idle", "walk"):
            legs = "dangle"
            if self._hop_vy < 0:
                squash = -1
                arms = "up"

        if now < self._expr_until and self._expr and state != "sleep":
            eyes = self._expr
            if self._expr == "happy":
                blush = True
        if now < self._squash_until and squash == 0:
            squash = 1
        if eyes == "open" and state in ("idle", "walk") and now < self._blink_until:
            eyes = "blink"
        if legs == "tuck" and squash:
            squash = 0
        return (eyes, look, arms, legs, squash, blush, mouth)

    def _rotation_value(self):
        now = self._now
        if self._state == "fly":
            return clamp(self._vx / 45.0, -25.0, 25.0)
        if self._expr == "dizzy" and now < self._expr_until:
            return math.sin(now * 10.0) * 7.0
        if self._state == "drag" and self._touch is not None:
            hist = self._touch.get("hist") or []
            if hist and now - hist[-1][0] < 0.08:
                return clamp(float(self._touch.get("drag_vx", 0.0)) / 45.0, -18.0, 18.0)
        return 0.0

    def _refresh(self):
        now = self._now
        key = self._compose(now)
        if key != self._frame_key:
            self._frame_key = key
            self._pixmap = self._get_frame(key)
        wx = int(self._x - self._margin)
        wy = int(self._y + self._hop_off - self._margin)
        if wx != self._last_wx or wy != self._last_wy:
            self.move(wx, wy)
            self._last_wx = wx
            self._last_wy = wy
        self._update_mask()
        if self.bubble.isVisible():
            self._update_bubble_position()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            if self._pixmap is not None:
                center_x = self._margin + self._sw / 2.0
                center_y = self._margin + self._sh / 2.0
                angle = self._rotation_value()
                painter.save()
                if abs(angle) > 0.01:
                    painter.translate(center_x, center_y)
                    painter.rotate(angle)
                    painter.drawPixmap(int(-self._sw / 2), int(-self._sh / 2), self._pixmap)
                else:
                    painter.drawPixmap(self._margin, self._margin, self._pixmap)
                painter.restore()

            win_x = self._x - self._margin
            win_y = self._y + self._hop_off - self._margin
            for part in self._particles:
                painter.setOpacity(part["alpha"])
                painter.drawPixmap(
                    int(part["x"] - win_x),
                    int(part["y"] - win_y),
                    part["pix"],
                )
            painter.setOpacity(1.0)
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            if callable(self.context_callback):
                self.context_callback(event.globalPosition().toPoint())
            event.accept()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._begin_press(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._begin_press(event)

    def _begin_press(self, event):
        point = event.globalPosition().toPoint()
        now = time.monotonic()
        was_sleeping = self._state == "sleep"
        self._last_interaction = now
        self._touch = {
            "x0": point.x(),
            "y0": point.y(),
            "ox": point.x() - self._x,
            "oy": point.y() - self._y,
            "t0": now,
            "hist": [(now, point.x(), point.y())],
            "anchor": point.x(),
            "dir": 0,
            "drag_vx": 0.0,
            "sample_x": point.x(),
            "shake_dir": 0,
            "shake_hits": [],
        }
        self._hop_active = False
        self._hop_off = 0.0
        self._hop_vy = 0.0
        self._vx = 0.0
        self._vy = 0.0
        self._state = "press"
        if was_sleeping:
            self._hide_bubble()
            self._set_expr("surprised", 0.9)
            self._say("wake")
        self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        touch = self._touch
        if touch is None:
            return
        point = event.globalPosition().toPoint()
        now = time.monotonic()
        hist = touch["hist"]
        hist.append((now, point.x(), point.y()))
        while len(hist) > 2 and now - hist[0][0] > 0.1:
            hist.pop(0)

        distance = math.hypot(point.x() - touch["x0"], point.y() - touch["y0"])
        sample_x = touch.get("sample_x", touch["x0"])
        dx_sample = point.x() - sample_x
        touch["sample_x"] = point.x()
        if self._state == "press" and distance > 8:
            self._state = "drag"
            if random.random() < 0.25:
                self._say("drag")

        if self._state == "drag":
            self._x = point.x() - touch["ox"]
            self._y = point.y() - touch["oy"]
            self._clamp_to_screen()
            t0, x0, _ = hist[0]
            if now - t0 > 0.005:
                touch["drag_vx"] = (point.x() - x0) / (now - t0)
            self._note_shake(touch, dx_sample, now)
        elif self._state == "pet":
            dx = point.x() - touch["anchor"]
            if abs(dx) > 12:
                direction = 1 if dx > 0 else -1
                if touch["dir"] and direction != touch["dir"]:
                    self._stroke()
                touch["dir"] = direction
                touch["anchor"] = point.x()
        event.accept()

    def mouseReleaseEvent(self, event):
        touch = self._touch
        self._touch = None
        self._last_interaction = time.monotonic()
        if touch is None:
            return
        if self._state == "drag":
            self._release_drag(touch)
        elif self._state == "pet":
            self._end_pet(time.monotonic())
        elif self._state == "press":
            self._state = "idle"
            self._tap(time.monotonic())
        self.update()
        event.accept()

    def _release_drag(self, touch):
        now = time.monotonic()
        vx = 0.0
        vy = 0.0
        hist = touch["hist"]
        if len(hist) >= 2:
            t0, x0, y0 = hist[0]
            t1, x1, y1 = hist[-1]
            if t1 - t0 > 0.005 and now - t1 < 0.12:
                vx = (x1 - x0) / (t1 - t0)
                vy = (y1 - y0) / (t1 - t0)
        limit = 6000.0
        vx = clamp(vx, -limit, limit)
        vy = clamp(vy, -limit, limit)
        speed = math.hypot(vx, vy)
        geo = self._screen_geo()
        min_x, max_x, min_y, max_y = self._bounds(geo)
        if speed > 700:
            self._state = "fly"
            self._vx = vx
            self._vy = vy
            if speed > 2500:
                self._say("throw")
        elif self.cfg.get("gravity") and self._y < max_y - 1:
            self._state = "fly"
            self._vx = vx
            self._vy = vy
        else:
            self._state = "idle"
            self._squash_until = now + 0.12
            self._next_action = now + random.uniform(2.0, 5.0)
            self._save_position()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._last_tick = time.monotonic()
            self._timer.start()
        self._notify_visibility(True)

    def hideEvent(self, event):
        self._hide_bubble()
        self._timer.stop()
        self._notify_visibility(False)
        super().hideEvent(event)

    def closeEvent(self, event):
        self._save_position()
        self._timer.stop()
        self.bubble.hide()
        super().closeEvent(event)
