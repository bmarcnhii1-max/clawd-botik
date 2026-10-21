import os
import sys
import traceback

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon

import sprite
from ai_client import AIClient
from config import APP_DIR, load_config, save_config
from dialogs import AISettingsDialog, ChatDialog, PetSettingsDialog, color_icon
from i18n import ui
from pet_window import PetWindow

SINGLE_INSTANCE_NAME = "ClawdDesktopPet"


def log_exception(exc_type, exc_value, exc_tb):
    try:
        with open(os.path.join(APP_DIR, "clawd-error.log"), "a", encoding="utf-8") as handle:
            handle.write("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    except Exception:
        pass


sys.excepthook = log_exception


def build_icon(config):
    _, body, eye = sprite.palette(int(config.get("color", 0)))
    key = ("open", 0, "normal", "stand", 0, False, None)
    pixmap = sprite.render_frame(key, 8, body, eye)
    return QIcon(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clawd")
    app.setQuitOnLastWindowClosed(False)

    instance_socket = QLocalSocket()
    instance_socket.connectToServer(SINGLE_INSTANCE_NAME)
    if instance_socket.waitForConnected(300):
        instance_socket.write(b"show")
        instance_socket.flush()
        instance_socket.waitForBytesWritten(300)
        instance_socket.disconnectFromServer()
        return

    server = QLocalServer(app)
    QLocalServer.removeServer(SINGLE_INSTANCE_NAME)
    server.listen(SINGLE_INSTANCE_NAME)

    config = load_config()
    ai = AIClient(config)
    pet = PetWindow(config, ai)

    def dialog_parent():
        return pet if pet.isVisible() else None

    def open_chat():
        dialog = ChatDialog(
            "Clawd",
            dialog_parent(),
            on_clear=pet.clear_history,
            lang=pet.language(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pet.ask_ai(dialog.get_text())

    pet.chat_callback = open_chat

    tray = QSystemTrayIcon(build_icon(config))
    tray.setToolTip("Clawd")

    menu = QMenu()
    t = ui(pet.language())
    show_action = QAction(t["show"], menu)
    show_action.setCheckable(True)
    show_action.setChecked(True)
    ask_action = QAction(t["ask"], menu)
    menu.addAction(show_action)
    menu.addAction(ask_action)
    menu.addSeparator()

    size_menu = menu.addMenu(t["size"])
    size_group = QActionGroup(size_menu)
    size_group.setExclusive(True)
    size_actions = []
    for index, label in enumerate(t["sizes"]):
        action = QAction(label, size_menu)
        action.setCheckable(True)
        action.setChecked(index == int(config.get("size", 1)))
        size_group.addAction(action)
        size_menu.addAction(action)
        size_actions.append(action)

    color_menu = menu.addMenu(t["color"])
    color_group = QActionGroup(color_menu)
    color_group.setExclusive(True)
    color_actions = []
    for index, palette in enumerate(sprite.PALETTES):
        action = QAction(color_icon(palette[1]), t["colors"][index], color_menu)
        action.setCheckable(True)
        action.setChecked(index == int(config.get("color", 0)))
        color_group.addAction(action)
        color_menu.addAction(action)
        color_actions.append(action)

    lang_menu = menu.addMenu(t["language"])
    lang_group = QActionGroup(lang_menu)
    lang_group.setExclusive(True)
    lang_actions = {}
    for code, label in (
        ("ru", t["language_ru"]),
        ("uk", t["language_uk"]),
        ("en", t["language_en"]),
    ):
        action = QAction(label, lang_menu)
        action.setCheckable(True)
        action.setChecked(config.get("lang", "ru") == code)
        lang_group.addAction(action)
        lang_menu.addAction(action)
        lang_actions[code] = action

    ai_menu = menu.addMenu(t["ai_model"])
    ai_mode_group = QActionGroup(ai_menu)
    ai_mode_group.setExclusive(True)
    cloud_action = QAction(t["ai_cloud"], ai_menu)
    local_action = QAction(t["ai_local"], ai_menu)
    for action, mode in ((cloud_action, "cloud"), (local_action, "local")):
        action.setCheckable(True)
        action.setChecked(str(config.get("ai_mode", "cloud")) == mode)
        ai_mode_group.addAction(action)
        ai_menu.addAction(action)

    menu.addSeparator()
    gravity_action = QAction(t["gravity"], menu)
    gravity_action.setCheckable(True)
    gravity_action.setChecked(bool(config.get("gravity", False)))
    wander_action = QAction(t["wander"], menu)
    wander_action.setCheckable(True)
    wander_action.setChecked(bool(config.get("wander", True)))
    phrases_action = QAction(t["phrases"], menu)
    phrases_action.setCheckable(True)
    phrases_action.setChecked(bool(config.get("phrases", True)))
    menu.addAction(gravity_action)
    menu.addAction(wander_action)
    menu.addAction(phrases_action)

    menu.addSeparator()
    pet_settings_action = QAction(t["settings"], menu)
    clear_history_action = QAction(t["clear_history"], menu)
    ai_action = QAction(t["ai_settings"], menu)
    quit_action = QAction(t["quit"], menu)
    menu.addAction(pet_settings_action)
    menu.addAction(clear_history_action)
    menu.addAction(ai_action)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    def retranslate():
        t = ui(pet.language())
        show_action.setText(t["show"])
        ask_action.setText(t["ask"])
        size_menu.setTitle(t["size"])
        for action, label in zip(size_actions, t["sizes"]):
            action.setText(label)
        color_menu.setTitle(t["color"])
        for action, label in zip(color_actions, t["colors"]):
            action.setText(label)
        lang_menu.setTitle(t["language"])
        lang_actions["ru"].setText(t["language_ru"])
        lang_actions["uk"].setText(t["language_uk"])
        lang_actions["en"].setText(t["language_en"])
        ai_menu.setTitle(t["ai_model"])
        cloud_action.setText(t["ai_cloud"])
        local_action.setText(t["ai_local"])
        gravity_action.setText(t["gravity"])
        wander_action.setText(t["wander"])
        phrases_action.setText(t["phrases"])
        pet_settings_action.setText(t["settings"])
        clear_history_action.setText(t["clear_history"])
        ai_action.setText(t["ai_settings"])
        quit_action.setText(t["quit"])
        menu.update()

    def sync_menu():
        retranslate()
        size_index = max(0, min(len(size_actions) - 1, int(config.get("size", 1))))
        size_actions[size_index].setChecked(True)
        color_index = max(0, min(len(color_actions) - 1, int(config.get("color", 0))))
        color_actions[color_index].setChecked(True)
        lang_actions[pet.language()].setChecked(True)
        mode = str(config.get("ai_mode", "cloud"))
        for action, action_mode in ((cloud_action, "cloud"), (local_action, "local")):
            action.blockSignals(True)
            action.setChecked(mode == action_mode)
            action.blockSignals(False)
        for action, key in ((gravity_action, "gravity"), (wander_action, "wander"), (phrases_action, "phrases")):
            action.blockSignals(True)
            action.setChecked(bool(config.get(key, True)))
            action.blockSignals(False)

    def set_size(index):
        config["size"] = index
        save_config(config)
        pet.apply_config()

    def set_color(index):
        config["color"] = index
        save_config(config)
        pet.apply_config()
        tray.setIcon(build_icon(config))
        t = ui(pet.language())
        pet._say_raw(t["color_prefix"] + t["colors"][index], 2.2)

    def set_language(code):
        pet.set_language(code)
        QTimer.singleShot(0, sync_menu)

    def set_ai_mode(mode):
        if str(config.get("ai_mode", "cloud")) == mode:
            return
        config["ai_mode"] = mode
        save_config(config)
        sync_menu()
        t = ui(pet.language())
        pet._say_raw(t["ai_local_on"] if mode == "local" else t["ai_cloud_on"], 3.0)

    for index, action in enumerate(size_actions):
        action.triggered.connect(lambda checked=False, i=index: set_size(i))
    for index, action in enumerate(color_actions):
        action.triggered.connect(lambda checked=False, i=index: set_color(i))
    for code, action in lang_actions.items():
        action.triggered.connect(lambda checked=False, c=code: set_language(c))
    cloud_action.triggered.connect(lambda checked=False: set_ai_mode("cloud"))
    local_action.triggered.connect(lambda checked=False: set_ai_mode("local"))

    def toggle_visible(checked):
        if checked:
            pet.show()
            pet.raise_()
        else:
            pet.bubble.hide()
            pet.hide()

    def set_gravity(checked):
        config["gravity"] = bool(checked)
        save_config(config)

    def set_wander(checked):
        config["wander"] = bool(checked)
        save_config(config)

    def set_phrases(checked):
        config["phrases"] = bool(checked)
        save_config(config)

    def open_pet_settings():
        dialog = PetSettingsDialog(config, dialog_parent())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_lang = config.get("lang", "ru")
            dialog.apply_to_config()
            save_config(config)
            pet.apply_config()
            if config.get("lang", "ru") != old_lang:
                pet.set_language(config.get("lang", "ru"), announce=False)
            tray.setIcon(build_icon(config))
            sync_menu()
            pet._say_raw(ui(pet.language())["settings_saved"], 2.5)

    def open_ai_settings():
        dialog = AISettingsDialog(config, dialog_parent())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.apply_to_config()
            save_config(config)
            pet._say_raw(ui(pet.language())["ai_settings_saved"], 3.0)

    show_action.toggled.connect(toggle_visible)
    ask_action.triggered.connect(open_chat)
    gravity_action.toggled.connect(set_gravity)
    wander_action.toggled.connect(set_wander)
    phrases_action.toggled.connect(set_phrases)
    pet_settings_action.triggered.connect(open_pet_settings)
    clear_history_action.triggered.connect(pet.clear_history)
    ai_action.triggered.connect(open_ai_settings)
    quit_action.triggered.connect(app.quit)

    def show_context_menu(pos):
        QTimer.singleShot(0, lambda: menu.exec(pos))

    pet.context_callback = show_context_menu
    pet.language_callback = lambda code: sync_menu()

    def activate_instance():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            if connection is not None:
                connection.deleteLater()
        show_action.setChecked(True)
        pet.show()
        pet.raise_()

    server.newConnection.connect(activate_instance)
    if server.hasPendingConnections():
        activate_instance()

    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            show_action.setChecked(not show_action.isChecked())

    tray.activated.connect(on_tray_activated)
    tray.show()

    app.aboutToQuit.connect(pet.close)
    pet.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
