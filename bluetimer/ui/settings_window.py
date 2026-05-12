from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import Rule
from ..scheduler import check_rule_conflict
from .log_view import LogView
from .rule_dialog import RuleDialog


class SettingsWindow(QMainWindow):
    rules_changed = pyqtSignal()
    manual_action_requested = pyqtSignal(str)
    adapter_select_requested = pyqtSignal()
    autostart_changed = pyqtSignal(bool)
    calibrate_changed = pyqtSignal(bool)

    def __init__(self, app_state, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app_state = app_state
        self.setWindowTitle("BlueTimer 设置")
        self.status_label = QLabel("当前蓝牙状态：检测中")
        self.adapter_label = QLabel("当前适配器：未选择")
        self.table = QTableWidget(0, 6)
        self.autostart_check = QCheckBox("开机自启")
        self.calibrate_check = QCheckBox("程序启动或电脑唤醒后自动校准蓝牙状态")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.table.setHorizontalHeaderLabels(["启用", "名称", "动作", "时间", "重复", "下次执行"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        open_button = QPushButton("立即开启")
        close_button = QPushButton("立即关闭")
        add_button = QPushButton("新增规则")
        edit_button = QPushButton("编辑")
        delete_button = QPushButton("删除")
        adapter_button = QPushButton("重新选择适配器")
        log_button = QPushButton("查看执行日志")

        open_button.clicked.connect(lambda: self.manual_action_requested.emit("on"))
        close_button.clicked.connect(lambda: self.manual_action_requested.emit("off"))
        add_button.clicked.connect(self._add_rule)
        edit_button.clicked.connect(self._edit_rule)
        delete_button.clicked.connect(self._delete_rule)
        adapter_button.clicked.connect(lambda _checked=False: self.adapter_select_requested.emit())
        log_button.clicked.connect(self._show_logs)
        self.autostart_check.toggled.connect(self.autostart_changed.emit)
        self.calibrate_check.toggled.connect(self.calibrate_changed.emit)

        top_actions = QHBoxLayout()
        top_actions.addWidget(open_button)
        top_actions.addWidget(close_button)
        top_actions.addStretch()

        rule_actions = QHBoxLayout()
        rule_actions.addWidget(add_button)
        rule_actions.addWidget(edit_button)
        rule_actions.addWidget(delete_button)
        rule_actions.addStretch()

        settings_actions = QHBoxLayout()
        settings_actions.addWidget(adapter_button)
        settings_actions.addWidget(log_button)
        settings_actions.addStretch()

        root = QVBoxLayout()
        root.addWidget(self.status_label)
        root.addWidget(self.adapter_label)
        root.addLayout(top_actions)
        root.addWidget(QLabel("定时规则"))
        root.addWidget(self.table)
        root.addLayout(rule_actions)
        root.addWidget(QLabel("设置"))
        root.addWidget(self.autostart_check)
        root.addWidget(self.calibrate_check)
        root.addLayout(settings_actions)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(840, 560)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

    def refresh(self) -> None:
        config = self.app_state.config
        self.adapter_label.setText(f"当前适配器：{config.adapter_name or config.adapter_instance_id or '未选择'}")
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(config.auto_start)
        self.autostart_check.blockSignals(False)
        self.calibrate_check.blockSignals(True)
        self.calibrate_check.setChecked(config.calibrate_on_resume)
        self.calibrate_check.blockSignals(False)
        self._load_rules(config.rules)

    def set_status_text(self, text: str) -> None:
        self.status_label.setText(f"当前蓝牙状态：{text}")

    def _load_rules(self, rules: list[Rule]) -> None:
        self.table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            self.table.setItem(row, 0, QTableWidgetItem("是" if rule.enabled else "否"))
            self.table.setItem(row, 1, QTableWidgetItem(rule.label))
            self.table.setItem(row, 2, QTableWidgetItem(rule.action_label))
            self.table.setItem(row, 3, QTableWidgetItem(rule.time_label))
            self.table.setItem(row, 4, QTableWidgetItem(rule.days_label))
            self.table.setItem(row, 5, QTableWidgetItem("-"))

    def _selected_rule_index(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "请选择规则", "请先在列表中选择一条规则。")
            return None
        return rows[0].row()

    def _add_rule(self) -> None:
        dialog = RuleDialog(self)
        if dialog.exec() != RuleDialog.DialogCode.Accepted:
            return
        rule = dialog.rule()
        conflict = check_rule_conflict(self.app_state.config.rules, rule)
        if conflict:
            QMessageBox.warning(self, "规则冲突", f"这条规则与“{conflict}”在同一时间执行相反动作。")
            return
        self.app_state.config.rules.append(rule)
        self.app_state.save_config()
        self.refresh()
        self.rules_changed.emit()

    def _edit_rule(self) -> None:
        index = self._selected_rule_index()
        if index is None:
            return
        dialog = RuleDialog(self, self.app_state.config.rules[index])
        if dialog.exec() != RuleDialog.DialogCode.Accepted:
            return
        rule = dialog.rule()
        conflict = check_rule_conflict(self.app_state.config.rules, rule)
        if conflict:
            QMessageBox.warning(self, "规则冲突", f"这条规则与“{conflict}”在同一时间执行相反动作。")
            return
        self.app_state.config.rules[index] = rule
        self.app_state.save_config()
        self.refresh()
        self.rules_changed.emit()

    def _delete_rule(self) -> None:
        index = self._selected_rule_index()
        if index is None:
            return
        rule = self.app_state.config.rules[index]
        result = QMessageBox.question(self, "删除规则", f"确定删除“{rule.label}”吗？")
        if result != QMessageBox.StandardButton.Yes:
            return
        del self.app_state.config.rules[index]
        self.app_state.save_config()
        self.refresh()
        self.rules_changed.emit()

    def _show_logs(self) -> None:
        dialog = LogView(self.app_state.storage.recent_history(), self)
        dialog.exec()
