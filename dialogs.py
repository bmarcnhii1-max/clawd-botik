from urllib.parse import urlsplit

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import sprite
from i18n import ui


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default

STYLE = """
QDialog { background: #202225; }
QLabel { color: #cfcfcf; font-size: 12px; }
QLineEdit, QPlainTextEdit, QSpinBox {
    background: #2b2d31; color: #f2f2f2; border: 1px solid #3a3d42;
    border-radius: 8px; padding: 8px; selection-background-color: #d97757;
}
QCheckBox { color: #cfcfcf; font-size: 12px; }
QComboBox {
    background: #2b2d31; color: #f2f2f2; border: 1px solid #3a3d42;
    border-radius: 8px; padding: 6px 10px;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #2b2d31; color: #f2f2f2; border: 1px solid #3a3d42;
    selection-background-color: #d97757;
}
QPushButton {
    background: #3a3d42; color: #e8e8e8; border: none; border-radius: 8px;
    padding: 8px 16px;
}
QPushButton:hover { background: #4a4d52; }
QPushButton#primary { background: #d97757; color: #ffffff; }
QPushButton#primary:hover { background: #e2876a; }
"""


class ChatDialog(QDialog):
    def __init__(self, pet_name="Clawd", parent=None, on_clear=None, lang="ru", history=None):
        super().__init__(parent)
        self.on_clear = on_clear
        self.t = ui(lang)
        self.setWindowTitle(pet_name)
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setMinimumHeight(480)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(STYLE)
        self.text = ""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.t["chat_title"] + pet_name))
        self.history_view = QListWidget(self)
        self.history_view.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.history_view.setMinimumHeight(180)
        layout.addWidget(self.history_view)
        for item in (history or [])[-50:]:
            if isinstance(item, dict) and item.get("content"):
                role = str(item.get("role", ""))
                content = str(item["content"])[:400]
                self.history_view.addItem(f"{role}: {content}")
        self.input = QPlainTextEdit(self)
        self.input.setPlaceholderText(self.t["chat_placeholder"])
        self.input.setMaximumHeight(96)
        self.input.setTabChangesFocus(True)
        layout.addWidget(self.input)
        buttons = QHBoxLayout()
        self.clear_button = QPushButton(self.t["chat_clear"], self)
        self.copy_button = QPushButton(self.t.get("copy", "Copy"), self)
        buttons.addWidget(self.clear_button)
        buttons.addWidget(self.copy_button)
        buttons.addStretch(1)
        self.cancel_button = QPushButton(self.t["cancel"], self)
        self.send_button = QPushButton(self.t["chat_send"], self)
        self.send_button.setObjectName("primary")
        self.send_button.setDefault(True)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)
        self.clear_button.clicked.connect(self._clear_history)
        self.copy_button.clicked.connect(self._copy_history)
        self.cancel_button.clicked.connect(self.reject)
        self.send_button.clicked.connect(self._submit)
        from PySide6.QtWidgets import QShortcut

        QShortcut(self.t["chat_send"], self, activated=self._submit)

    def _clear_history(self):
        self.input.clear()
        self.history_view.clear()
        if callable(self.on_clear):
            self.on_clear()

    def _copy_history(self):
        from PySide6.QtWidgets import QApplication

        items = [self.history_view.item(r).text() for r in range(self.history_view.count())]
        QApplication.clipboard().setText("\n".join(items))

    def _submit(self):
        value = self.input.toPlainText().strip()
        if not value:
            return
        self.text = value
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus()

    def get_text(self):
        return self.text


def color_icon(body_color):
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor.fromRgba(int(body_color) & 0xFFFFFFFF))
    painter.setPen(QPen(QColor(255, 255, 255, 70), 1.0))
    painter.drawRoundedRect(QRectF(1.5, 1.5, 15.0, 15.0), 4.0, 4.0)
    painter.end()
    return QIcon(pixmap)


class PetSettingsDialog(QDialog):
    SLEEP_ITEMS = [
        ("sleep_1m", 60),
        ("sleep_3m", 180),
        ("sleep_10m", 600),
        ("sleep_never", 0),
    ]

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.t = ui(config.get("lang", "ru"))
        self.setWindowTitle(self.t["pet_settings"])
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(STYLE)
        self.config = config

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.size_combo = QComboBox(self)
        self.size_combo.addItems(self.t["sizes"])
        size_index = _safe_int(config.get("size", 1), 1)
        self.size_combo.setCurrentIndex(size_index if 0 <= size_index < len(sprite.SIZE_UNITS) else 1)

        self.color_combo = QComboBox(self)
        for index, (_name, body, _eye) in enumerate(sprite.PALETTES):
            self.color_combo.addItem(color_icon(body), self.t["colors"][index])
        color_index = _safe_int(config.get("color", 0), 0)
        self.color_combo.setCurrentIndex(color_index if 0 <= color_index < len(sprite.PALETTES) else 0)

        self.lang_combo = QComboBox(self)
        for code, key in (("ru", "language_ru"), ("uk", "language_uk"), ("en", "language_en")):
            self.lang_combo.addItem(self.t[key], code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(str(config.get("lang", "ru")))))

        self.sleep_combo = QComboBox(self)
        for key, seconds in self.SLEEP_ITEMS:
            self.sleep_combo.addItem(self.t[key], seconds)
        try:
            sleep_value = int(float(config.get("sleep_seconds", 180) or 0))
        except (TypeError, ValueError, OverflowError):
            sleep_value = 180
        sleep_index = 1
        for index, (_key, seconds) in enumerate(self.SLEEP_ITEMS):
            if seconds == sleep_value:
                sleep_index = index
                break
        else:
            if sleep_value != 180:
                self.sleep_combo.addItem("%s с" % sleep_value, sleep_value)
                sleep_index = self.sleep_combo.count() - 1
        self.sleep_combo.setCurrentIndex(sleep_index)

        self.gravity_box = QCheckBox(self.t["gravity"])
        self.gravity_box.setChecked(bool(config.get("gravity", False)))
        self.wander_box = QCheckBox(self.t["wander"])
        self.wander_box.setChecked(bool(config.get("wander", True)))
        self.phrases_box = QCheckBox(self.t["phrases"])
        self.phrases_box.setChecked(bool(config.get("phrases", True)))
        self.autostart_box = QCheckBox(self.t.get("autostart", "Autostart"))
        self.autostart_box.setChecked(bool(config.get("autostart", False)))
        self.click_box = QCheckBox(self.t.get("click_through", "Click-through"))
        self.click_box.setChecked(bool(config.get("click_through", False)))
        self.mute_box = QCheckBox(self.t.get("mute", "Mute"))
        self.mute_box.setChecked(bool(config.get("mute", False)))
        self.opacity_spin = QDoubleSpinBox(self)
        self.opacity_spin.setRange(0.2, 1.0)
        self.opacity_spin.setSingleStep(0.1)
        try:
            self.opacity_spin.setValue(float(config.get("opacity", 1.0) or 1.0))
        except (TypeError, ValueError, OverflowError):
            self.opacity_spin.setValue(1.0)

        form.addRow(self.t["size"], self.size_combo)
        form.addRow(self.t["color"], self.color_combo)
        form.addRow(self.t["language"], self.lang_combo)
        form.addRow(self.t["sleep"], self.sleep_combo)
        form.addRow("", self.gravity_box)
        form.addRow("", self.wander_box)
        form.addRow("", self.phrases_box)
        form.addRow("", self.autostart_box)
        form.addRow("", self.click_box)
        form.addRow("", self.mute_box)
        form.addRow(self.t.get("opacity", "Opacity"), self.opacity_spin)
        layout.addLayout(form)

        hint = QLabel(self.t["settings_hint"], self)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton(self.t["cancel"], self)
        save_button = QPushButton(self.t["save"], self)
        save_button.setObjectName("primary")
        save_button.setDefault(True)
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.accept)

    def apply_to_config(self):
        self.config["size"] = self.size_combo.currentIndex()
        self.config["color"] = self.color_combo.currentIndex()
        self.config["lang"] = self.lang_combo.currentData() or "ru"
        try:
            self.config["sleep_seconds"] = int(self.sleep_combo.currentData() or 0)
        except (TypeError, ValueError):
            self.config["sleep_seconds"] = 180
        self.config["gravity"] = bool(self.gravity_box.isChecked())
        self.config["wander"] = bool(self.wander_box.isChecked())
        self.config["phrases"] = bool(self.phrases_box.isChecked())
        self.config["autostart"] = bool(self.autostart_box.isChecked())
        self.config["click_through"] = bool(self.click_box.isChecked())
        self.config["mute"] = bool(self.mute_box.isChecked())
        try:
            self.config["opacity"] = float(self.opacity_spin.value())
        except (TypeError, ValueError):
            self.config["opacity"] = 1.0


class AISettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.t = ui(config.get("lang", "ru"))
        self.setWindowTitle(self.t["ai_settings_title"])
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(STYLE)
        self.config = config

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.enabled_box = QCheckBox(self.t["ai_enabled"])
        self.enabled_box.setChecked(bool(config.get("ai_enabled", True)))
        self.thoughts_box = QCheckBox(self.t["ai_thoughts"])
        self.thoughts_box.setChecked(bool(config.get("ai_thoughts", True)))
        self.url_edit = QLineEdit(str(config.get("ai_base_url", "")))
        self.url_edit.setPlaceholderText("https://api.example.com/v1")
        self._env_key = "ai_key" in getattr(config, "env_overrides", ())
        self.key_edit = QLineEdit("")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        if self._env_key:
            self.key_edit.setPlaceholderText(self.t["key_from_env"])
        else:
            self.key_edit.setText(str(config.get("ai_key", "")))
            self.key_edit.setPlaceholderText("sk-…")
        self.model_edit = QLineEdit(str(config.get("ai_model", "")))
        self.model_edit.setPlaceholderText("model-name")
        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setSingleStep(10)
        self.timeout_spin.setSuffix(self.t["timeout_suffix"])
        try:
            timeout_val = int(float(config.get("ai_timeout", 120) or 120))
        except (TypeError, ValueError, OverflowError):
            timeout_val = 120
        self.timeout_spin.setValue(timeout_val)
        self.max_tokens_spin = QSpinBox(self)
        self.max_tokens_spin.setRange(16, 4096)
        self.max_tokens_spin.setSingleStep(16)
        try:
            self.max_tokens_spin.setValue(int(float(config.get("ai_max_tokens", 220) or 220)))
        except (TypeError, ValueError, OverflowError):
            self.max_tokens_spin.setValue(220)
        self.temp_spin = QDoubleSpinBox(self)
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        try:
            self.temp_spin.setValue(float(config.get("ai_temperature", 0.9) or 0.9))
        except (TypeError, ValueError, OverflowError):
            self.temp_spin.setValue(0.9)
        self.interval_spin = QSpinBox(self)
        self.interval_spin.setRange(5, 720)
        try:
            self.interval_spin.setValue(int(float(config.get("ai_thought_interval", 40) or 40)))
        except (TypeError, ValueError, OverflowError):
            self.interval_spin.setValue(40)
        self.persona_combo = QComboBox(self)
        self.persona_combo.addItem("", data="")
        from phrases import list_persona_presets

        for name in list_persona_presets(config.get("lang", "ru")):
            self.persona_combo.addItem(name, name)
        self.persona_edit = QPlainTextEdit(str(config.get("ai_persona", "")))
        self.persona_edit.setPlaceholderText(self.t["persona_hint"])
        self.persona_edit.setFixedHeight(90)
        self.persona_combo.currentIndexChanged.connect(self._apply_preset)
        layout.addWidget(QLabel(self.t["ai_mode_hint"]))
        form.addRow("", self.enabled_box)
        form.addRow("", self.thoughts_box)
        form.addRow(self.t["api_url"], self.url_edit)
        form.addRow(self.t["api_key"], self.key_edit)
        form.addRow(self.t["model"], self.model_edit)
        form.addRow(self.t["timeout"], self.timeout_spin)
        form.addRow(self.t["max_tokens"], self.max_tokens_spin)
        form.addRow(self.t["temperature"], self.temp_spin)
        form.addRow(self.t["thought_interval"], self.interval_spin)
        form.addRow("Persona", self.persona_combo)
        form.addRow(self.t["persona"], self.persona_edit)
        layout.addLayout(form)
        self.test_button = QPushButton(self.t.get("test_connection", "Test connection"), self)
        self.test_label = QLabel(self)
        self.test_button.clicked.connect(self._test_connection)
        layout.addWidget(self.test_button)
        layout.addWidget(self.test_label)

        self.url_warning = QLabel(self)
        self.url_warning.setWordWrap(True)
        self.url_warning.setStyleSheet("color: #e0b35a;")
        layout.addWidget(self.url_warning)
        self.url_edit.textChanged.connect(self._update_url_warning)
        self._update_url_warning()

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton(self.t["cancel"], self)
        save_button = QPushButton(self.t["save"], self)
        save_button.setObjectName("primary")
        save_button.setDefault(True)
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.accept)

    def _update_url_warning(self):
        url = self.url_edit.text().strip()
        insecure = False
        if url:
            try:
                parts = urlsplit(url)
                host = (parts.hostname or "").lower()
                insecure = (
                    parts.scheme == "http"
                    and host not in ("localhost", "127.0.0.1", "::1")
                    and not host.startswith("127.")
                )
            except ValueError:
                insecure = False
        self.url_warning.setText(self.t["insecure_url"] if insecure else "")
        self.url_warning.setVisible(insecure)

    def _apply_preset(self, index):
        name = self.persona_combo.itemData(index) or ""
        if name:
            from phrases import get_persona_preset

            text = get_persona_preset(name, self.config.get("lang", "ru"))
            if text:
                self.persona_edit.setPlainText(text)
                self._set_value("ai_persona", text)

    def _test_connection(self):
        base = self.url_edit.text().strip().rstrip("/")
        key = self.key_edit.text().strip() or str(self.config.get("ai_key", ""))
        model = self.model_edit.text().strip() or str(self.config.get("ai_model", ""))
        if not base or not model:
            self.test_label.setText("✗ " + self.t.get("ai_not_configured", ""))
            return
        try:
            import requests

            r = requests.get(base + "/models", headers={"Authorization": f"Bearer {key}"} if key else {}, timeout=10)
            ok = r.status_code in (200, 401, 403, 404, 422)
            self.test_label.setText(("✓ " if ok else "✗ ") + f"HTTP {r.status_code} — {self.t.get('connection_ok', 'OK') if ok else ''}")
        except Exception as exc:
            self.test_label.setText("✗ " + type(exc).__name__)

    def _set_value(self, key, value):
        setter = getattr(self.config, "set_user_value", None)
        if callable(setter):
            setter(key, value)
        else:
            self.config[key] = value

    def _set_if_changed(self, key, value):
        if str(self.config.get(key, "")) != str(value):
            self._set_value(key, value)

    def apply_to_config(self):
        self._set_value("ai_enabled", bool(self.enabled_box.isChecked()))
        self._set_value("ai_thoughts", bool(self.thoughts_box.isChecked()))
        self._set_if_changed("ai_base_url", self.url_edit.text().strip())
        key = self.key_edit.text().strip()
        if key:
            self._set_value("ai_key", key)
        elif not self._env_key:
            self._set_if_changed("ai_key", "")
        self._set_if_changed("ai_model", self.model_edit.text().strip())
        self._set_value("ai_timeout", int(self.timeout_spin.value()))
        self._set_value("ai_max_tokens", int(self.max_tokens_spin.value()))
        self._set_value("ai_temperature", float(self.temp_spin.value()))
        self._set_value("ai_thought_interval", int(self.interval_spin.value()))
        self._set_value("ai_persona", self.persona_edit.toPlainText().strip())
