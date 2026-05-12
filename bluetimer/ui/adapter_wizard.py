from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AdapterDialog(QDialog):
    def __init__(self, adapters: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择蓝牙适配器")
        self.adapters = adapters
        self.list_widget = QListWidget()
        self.refresh_button = QPushButton("重新检测")
        self._selected: dict | None = None
        self._build_ui()
        self._load_adapters(adapters)

    def _build_ui(self) -> None:
        intro = QLabel("选择 BlueTimer 要管理的蓝牙适配器。列表已优先过滤为真实适配器；若看到“可能不是适配器”，通常是耳机、手机或蓝牙服务项，不建议选择。")
        intro.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout()
        root.addWidget(intro)
        root.addWidget(self.list_widget)
        root.addWidget(buttons)
        self.setLayout(root)
        self.resize(640, 360)

    def _load_adapters(self, adapters: list[dict]) -> None:
        self.list_widget.clear()
        for adapter in adapters:
            details = [adapter["instance_id"]]
            if adapter.get("service"):
                details.append(f"Service={adapter['service']}")
            if adapter.get("enumerator"):
                details.append(f"Enumerator={adapter['enumerator']}")
            item = QListWidgetItem(f"{adapter['name']}  |  状态：{adapter.get('status', 'Unknown')}\n{'  |  '.join(details)}")
            item.setData(Qt.ItemDataRole.UserRole, adapter)
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _accept_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "未选择适配器", "请先选择一个蓝牙适配器。")
            return
        self._selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def selected_adapter(self) -> dict | None:
        return self._selected
