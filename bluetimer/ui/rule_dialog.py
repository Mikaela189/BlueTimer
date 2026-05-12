from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..models import DAYS, DAY_LABELS, Rule


class RuleDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, rule: Rule | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑规则" if rule else "新增规则")
        self._rule = rule
        self.label_edit = QLineEdit(rule.label if rule else "")
        self.on_radio = QRadioButton("开启蓝牙")
        self.off_radio = QRadioButton("关闭蓝牙")
        self.hour_spin = QSpinBox()
        self.minute_spin = QSpinBox()
        self.enabled_check = QCheckBox("启用此规则")
        self.day_checks: dict[str, QCheckBox] = {}
        self._build_ui()
        self._load_rule(rule)

    def _build_ui(self) -> None:
        self.hour_spin.setRange(0, 23)
        self.minute_spin.setRange(0, 59)
        self.hour_spin.setDisplayIntegerBase(10)
        self.minute_spin.setDisplayIntegerBase(10)

        action_row = QHBoxLayout()
        action_row.addWidget(self.on_radio)
        action_row.addWidget(self.off_radio)
        action_row.addStretch()

        time_row = QHBoxLayout()
        time_row.addWidget(self.hour_spin)
        time_row.addWidget(self.minute_spin)
        time_wrap = QWidget()
        time_wrap.setLayout(time_row)

        days_row = QHBoxLayout()
        for day in DAYS:
            checkbox = QCheckBox(DAY_LABELS[day])
            self.day_checks[day] = checkbox
            days_row.addWidget(checkbox)
        days_wrap = QWidget()
        days_wrap.setLayout(days_row)

        form = QFormLayout()
        form.addRow("规则名称", self.label_edit)
        form.addRow("执行动作", action_row)
        form.addRow("执行时间", time_wrap)
        form.addRow("重复日期", days_wrap)
        form.addRow("", self.enabled_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self._validate_accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addWidget(buttons)
        self.setLayout(root)
        self.resize(520, 220)

    def _load_rule(self, rule: Rule | None) -> None:
        self.off_radio.setChecked(True)
        self.enabled_check.setChecked(True)
        for day in ("mon", "tue", "wed", "thu", "fri"):
            self.day_checks[day].setChecked(True)
        if not rule:
            self.hour_spin.setValue(9)
            self.minute_spin.setValue(0)
            return
        self.on_radio.setChecked(rule.action == "on")
        self.off_radio.setChecked(rule.action == "off")
        self.hour_spin.setValue(rule.hour)
        self.minute_spin.setValue(rule.minute)
        self.enabled_check.setChecked(rule.enabled)
        for checkbox in self.day_checks.values():
            checkbox.setChecked(False)
        for day in rule.days:
            self.day_checks[day].setChecked(True)

    def _validate_accept(self) -> None:
        if not self.label_edit.text().strip():
            QMessageBox.warning(self, "缺少名称", "请填写规则名称。")
            return
        if not any(checkbox.isChecked() for checkbox in self.day_checks.values()):
            QMessageBox.warning(self, "缺少日期", "请至少选择一个重复日期。")
            return
        self.accept()

    def rule(self) -> Rule:
        source = self._rule
        rule = Rule(
            label=self.label_edit.text().strip(),
            action="on" if self.on_radio.isChecked() else "off",
            hour=self.hour_spin.value(),
            minute=self.minute_spin.value(),
            days=[day for day, checkbox in self.day_checks.items() if checkbox.isChecked()],  # type: ignore[list-item]
            enabled=self.enabled_check.isChecked(),
        )
        if source:
            rule.id = source.id
            rule.created_at = source.created_at
        return rule
