from __future__ import annotations

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class BlueTimerTray(QSystemTrayIcon):
    def __init__(self, app: QApplication, app_state) -> None:
        super().__init__()
        self.app = app
        self.app_state = app_state
        self.setToolTip("BlueTimer")
        self.setIcon(QIcon.fromTheme("bluetooth"))
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_menu(self) -> None:
        menu = QMenu()
        open_settings = QAction("打开设置", self)
        enable = QAction("立即开启蓝牙", self)
        disable = QAction("立即关闭蓝牙", self)
        quit_app = QAction("退出", self)

        open_settings.triggered.connect(self.app_state.show_settings)
        enable.triggered.connect(lambda: self.app_state.request_bluetooth_action("on", None, "manual"))
        disable.triggered.connect(lambda: self.app_state.request_bluetooth_action("off", None, "manual"))
        quit_app.triggered.connect(self.app_state.quit)

        menu.addAction(open_settings)
        menu.addSeparator()
        menu.addAction(enable)
        menu.addAction(disable)
        menu.addSeparator()
        menu.addAction(quit_app)
        self.setContextMenu(menu)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.app_state.show_settings()

    def notify(self, title: str, message: str) -> None:
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
