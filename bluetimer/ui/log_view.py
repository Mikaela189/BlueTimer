from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class LogView(QDialog):
    def __init__(self, records: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("执行日志")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["时间", "来源", "动作", "结果", "详情"])
        root = QVBoxLayout()
        root.addWidget(self.table)
        self.setLayout(root)
        self.resize(760, 420)
        self.load(records)

    def load(self, records: list[dict]) -> None:
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(record.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("rule_label") or "手动/校准"))
            self.table.setItem(row, 2, QTableWidgetItem("开启" if record.get("action") == "on" else "关闭"))
            self.table.setItem(row, 3, QTableWidgetItem("成功" if record.get("success") else "失败"))
            self.table.setItem(row, 4, QTableWidgetItem(record.get("detail") or ""))
        self.table.resizeColumnsToContents()
