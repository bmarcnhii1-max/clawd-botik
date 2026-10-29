from urllib.parse import urlsplit

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import sprite
from i18n import ui

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
    def __init__(self, pet_name="Clawd", parent=None, on_clear=None, lang="ru"):
        super().__init__(parent)
        self.on_clear = on_clear
        self.t = ui(lang)
        self.setWindowTitle(pet_name)
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(STYLE)
        self.text = ""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.t["chat_title"] + pet_name))
        self.input = QLineEdit(self)
        self.input.setPlaceholderText(self.t["chat_placeholder"])
        layout.addWidget(self.input)
        buttons = QHBoxLayout()
        self.clear_button = QPushButton(self.t["chat_clear"], self)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        self.cancel_button = QPushButton(self.t["cancel"], self)
        self.send_button = QPushButton(self.t["chat_send"], self)
        self.send_button.setObjectName("primary")
        self.send_button.setDefault(True)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)
        self.clear_button.clicked.connect(self._clear_history)
        self.cancel_button.clicked.connect(self.reject)
        self.send_button.clicked.connect(self._submit)
        self.input.returnPressed.connect(self._submit)

    def _clear_history(self):
        if callable(self.on_clear):
            self.on_clear()

    def _submit(self):
        value = self.input.text().strip()
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
        size_index = int(config.get("size", 1))
        self.size_combo.setCurrentIndex(size_index if 0 <= size_index < len(sprite.SIZE_UNITS) else 1)

        self.color_combo = QComboBox(self)
        for index, (_name, body, _eye) in enumerate(sprite.PALETTES):
            self.color_combo.addItem(color_icon(body), self.t["colors"][index])
        color_index = int(config.get("color", 0))
        self.color_combo.setCurrentIndex(color_index if 0 <= color_index < len(sprite.PALETTES) else 0)

        self.lang_combo = QComboBox(self)
        for code, key in (("ru", "language_ru"), ("uk", "language_uk"), ("en", "language_en")):
            self.lang_combo.addItem(self.t[key], code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(str(config.get("lang", "ru")))))

        self.sleep_combo = QComboBox(self)
        for key, seconds in self.SLEEP_ITEMS:
            self.sleep_combo.addItem(self.t[key], seconds)
        sleep_value = int(config.get("sleep_seconds", 180) or 0)
        sleep_index = 1
        for index, (_key, seconds) in enumerate(self.SLEEP_ITEMS):
            if seconds == sleep_value:
                sleep_index = index
                break
        self.sleep_combo.setCurrentIndex(sleep_index)

        self.gravity_box = QCheckBox(self.t["gravity"])
        self.gravity_box.setChecked(bool(config.get("gravity", False)))
        self.wander_box = QCheckBox(self.t["wander"])
        self.wander_box.setChecked(bool(config.get("wander", True)))
        self.phrases_box = QCheckBox(self.t["phrases"])
        self.phrases_box.setChecked(bool(config.get("phrases", True)))

        form.addRow(self.t["size"], self.size_combo)
        form.addRow(self.t["color"], self.color_combo)
        form.addRow(self.t["language"], self.lang_combo)
        form.addRow(self.t["sleep"], self.sleep_combo)
        form.addRow("", self.gravity_box)
        form.addRow("", self.wander_box)
        form.addRow("", self.phrases_box)
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
        self.config["lang"] = self.lang_combo.currentData()
        self.config["sleep_seconds"] = int(self.sleep_combo.currentData())
        self.config["gravity"] = bool(self.gravity_box.isChecked())
        self.config["wander"] = bool(self.wander_box.isChecked())
        self.config["phrases"] = bool(self.phrases_box.isChecked())


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
        self.timeout_spin.setValue(int(config.get("ai_timeout", 120) or 120))
        self.persona_edit = QPlainTextEdit(str(config.get("ai_persona", "")))
        self.persona_edit.setPlaceholderText(self.t["persona_hint"])
        self.persona_edit.setFixedHeight(90)
        layout.addWidget(QLabel(self.t["ai_mode_hint"]))
        form.addRow("", self.enabled_box)
        form.addRow("", self.thoughts_box)
        form.addRow(self.t["api_url"], self.url_edit)
        form.addRow(self.t["api_key"], self.key_edit)
        form.addRow(self.t["model"], self.model_edit)
        form.addRow(self.t["timeout"], self.timeout_spin)
        form.addRow(self.t["persona"], self.persona_edit)
        layout.addLayout(form)

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
                    and host not in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
                    and not host.startswith("127.")
                )
            except ValueError:
                insecure = False
        self.url_warning.setText(self.t["insecure_url"] if insecure else "")
        self.url_warning.setVisible(insecure)

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
        self._set_value("ai_persona", self.persona_edit.toPlainText().strip())
