from __future__ import annotations

import sys

from PyQt6.QtCore import QObject, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox

from . import bluetooth_ctrl
from .autostart import set_autostart
from .models import AppConfig, Rule
from .power_monitor import PowerMonitor
from .scheduler import RuleScheduler
from .storage import Storage
from .tray import BlueTimerTray
from .ui.adapter_wizard import AdapterDialog
from .ui.settings_window import SettingsWindow
from .worker import Worker


class AppState(QObject):
    action_done = pyqtSignal(str, bool, str)
    status_changed = pyqtSignal(str)

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.storage = Storage()
        self.config: AppConfig = self.storage.load_config()
        self.thread_pool = QThreadPool.globalInstance()
        self.scheduler = RuleScheduler(self._scheduled_action)
        self.settings_window: SettingsWindow | None = None
        self.tray = BlueTimerTray(app, self)
        self.power_monitor = PowerMonitor(self._on_resume)
        self._workers: list[Worker] = []
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_status_async)
        self.action_done.connect(self._on_action_done)
        self.status_changed.connect(self._on_status_changed)

    def start(self) -> None:
        self.tray.setIcon(self._make_icon("#2f80ed"))
        self.tray.show()
        self.scheduler.start()
        self.reload_scheduler()
        self.power_monitor.start()
        self.status_timer.start(5000)
        self.ensure_adapter_selected()
        self.refresh_status_async()
        if self.config.calibrate_on_resume:
            QTimer.singleShot(1200, self.calibrate_now)

    def show_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
            self.settings_window.rules_changed.connect(self.reload_scheduler)
            self.settings_window.manual_action_requested.connect(
                lambda action: self.request_bluetooth_action(action, None, "manual")
            )
            self.settings_window.adapter_select_requested.connect(lambda: self.select_adapter(force_dialog=True))
            self.settings_window.autostart_changed.connect(self.update_autostart)
            self.settings_window.calibrate_changed.connect(self.update_calibrate)
        self.settings_window.refresh()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def quit(self) -> None:
        self.scheduler.shutdown()
        self.app.quit()

    def save_config(self) -> None:
        self.storage.save_config(self.config)

    def reload_scheduler(self) -> None:
        self.scheduler.reload(self.config.rules)

    def ensure_adapter_selected(self) -> None:
        if not self.config.adapter_instance_id:
            self.select_adapter(force_dialog=False)

    def select_adapter(self, force_dialog: bool = True) -> None:
        if self.settings_window:
            self.settings_window.statusBar().showMessage("正在检测蓝牙适配器...", 5000)
        worker = Worker(bluetooth_ctrl.discover_bluetooth_adapters)
        worker.signals.finished.connect(lambda adapters: self._show_adapter_dialog(adapters, force_dialog))
        worker.signals.error.connect(self._show_adapter_error)
        worker.signals.finished.connect(lambda _result, worker=worker: self._forget_worker(worker))
        worker.signals.error.connect(lambda _message, worker=worker: self._forget_worker(worker))
        self._workers.append(worker)
        self.thread_pool.start(worker)

    def _forget_worker(self, worker: Worker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    def _show_adapter_dialog(self, adapters: object, force_dialog: bool) -> None:
        if self.settings_window:
            self.settings_window.statusBar().clearMessage()
        adapter_list = adapters if isinstance(adapters, list) else []
        if not adapter_list:
            QMessageBox.warning(self.settings_window, "未检测到蓝牙设备", "没有检测到可用的蓝牙设备。请确认蓝牙驱动正常，或稍后在设置里重新选择。")
            return
        if not force_dialog and len(adapter_list) == 1 and adapter_list[0].get("is_adapter"):
            self._save_adapter(adapter_list[0])
            self.tray.notify("已选择蓝牙适配器", adapter_list[0].get("name", "蓝牙适配器"))
            return
        dialog = AdapterDialog(adapter_list)
        if dialog.exec() != AdapterDialog.DialogCode.Accepted:
            return
        adapter = dialog.selected_adapter()
        if not adapter:
            return
        self._save_adapter(adapter)

    def _show_adapter_error(self, message: str) -> None:
        if self.settings_window:
            self.settings_window.statusBar().clearMessage()
            QMessageBox.warning(self.settings_window, "检测蓝牙失败", message)
        self.tray.notify("检测蓝牙失败", message)

    def _save_adapter(self, adapter: dict) -> None:
        self.config.adapter_instance_id = adapter["instance_id"]
        self.config.adapter_name = adapter["name"]
        self.save_config()
        if self.settings_window:
            self.settings_window.refresh()
        self.refresh_status_async()

    def request_bluetooth_action(self, action: str, rule: Rule | None, source: str) -> None:
        if not self.config.adapter_instance_id:
            self.tray.notify("未选择适配器", "请先在设置中选择要管理的蓝牙适配器。")
            self.select_adapter(force_dialog=True)
            return

        def run() -> tuple[str, bool, str, str | None, str | None]:
            enable = action == "on"
            success, detail = bluetooth_ctrl.set_bluetooth_verified(self.config.adapter_instance_id or "", enable)
            return action, success, detail, rule.id if rule else None, rule.label if rule else source

        worker = Worker(run)
        worker.signals.finished.connect(self._record_action_result)
        worker.signals.error.connect(lambda message: self._record_action_result((action, False, message, rule.id if rule else None, rule.label if rule else source)))
        worker.signals.finished.connect(lambda _result, worker=worker: self._forget_worker(worker))
        worker.signals.error.connect(lambda _message, worker=worker: self._forget_worker(worker))
        self._workers.append(worker)
        self.thread_pool.start(worker)

    def _record_action_result(self, result: object) -> None:
        action, success, detail, rule_id, rule_label = result  # type: ignore[misc]
        self.storage.add_history(action, success, detail, rule_id, rule_label)
        self.action_done.emit(action, success, detail)
        self.refresh_status_async()

    def _scheduled_action(self, rule: Rule | None, source: str) -> None:
        if not rule:
            return
        self.request_bluetooth_action(rule.action, rule, source)

    def calibrate_now(self) -> None:
        self.scheduler.calibrate_now()

    def _on_resume(self) -> None:
        if self.config.calibrate_on_resume:
            QTimer.singleShot(1000, self.calibrate_now)

    def update_autostart(self, enabled: bool) -> None:
        ok, detail = set_autostart(enabled)
        if ok:
            self.config.auto_start = enabled
            self.save_config()
        elif self.settings_window:
            self.settings_window.refresh()
        self.tray.notify("开机自启", detail)

    def update_calibrate(self, enabled: bool) -> None:
        self.config.calibrate_on_resume = enabled
        self.save_config()

    def refresh_status_async(self) -> None:
        if not self.config.adapter_instance_id:
            self.status_changed.emit("未选择适配器")
            return
        worker = Worker(bluetooth_ctrl.get_bluetooth_status, self.config.adapter_instance_id)
        worker.signals.finished.connect(lambda enabled: self.status_changed.emit("已开启" if enabled else "已关闭"))
        worker.signals.error.connect(lambda message: self.status_changed.emit(f"检测失败：{message}"))
        worker.signals.finished.connect(lambda _result, worker=worker: self._forget_worker(worker))
        worker.signals.error.connect(lambda _message, worker=worker: self._forget_worker(worker))
        self._workers.append(worker)
        self.thread_pool.start(worker)

    def _on_action_done(self, action: str, success: bool, detail: str) -> None:
        title = "蓝牙操作成功" if success else "蓝牙操作失败"
        action_label = "开启" if action == "on" else "关闭"
        self.tray.notify(title, f"{action_label}蓝牙：{detail}")

    def _on_status_changed(self, text: str) -> None:
        color = "#2f80ed" if text == "已开启" else "#8a8f98"
        self.tray.setIcon(self._make_icon(color))
        self.tray.setToolTip(f"BlueTimer - {text}")
        if self.settings_window:
            self.settings_window.set_status_text(text)

    def _make_icon(self, color: str) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)


def run() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    state = AppState(app)
    state.start()
    return app.exec()
