from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from private_ledger.ui.widgets import create_card, make_danger_button, make_secondary_button, prepare_table, sync_table_columns


class AccountsPage(QWidget):
    account_save_requested = Signal(object)
    account_delete_requested = Signal(str)
    snapshot_save_requested = Signal(object)
    snapshot_delete_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._accounts = []
        self._balances: dict[str, str] = {}
        self._snapshots_by_account: dict[str, list[dict]] = defaultdict(list)
        self._current_account_id = ""
        self.default_currency = "CNY"

        self.list_widget = QListWidget()
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["银行卡", "支付宝", "微信", "现金", "API 余额", "话费", "会员账户", "储蓄账户"])
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["CNY", "USD"])
        self.purpose_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["正常", "需关注", "停用"])
        self.source_edit = QLineEdit("手动录入")
        self.notes_edit = QTextEdit()
        self.balance_preview = QLabel("当前余额：--")
        self.balance_preview.setObjectName("MutedText")

        self.new_button = make_secondary_button("新建账户")
        self.save_button = QPushButton("保存账户")
        self.delete_button = make_danger_button("删除账户")

        self.snapshot_table = QTableWidget()
        prepare_table(self.snapshot_table, ["时间", "金额", "状态", "来源"])
        self.snapshot_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.snapshot_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.snapshot_amount_edit = QLineEdit()
        self.snapshot_status_combo = QComboBox()
        self.snapshot_status_combo.addItems(["已确认", "待确认"])
        self.snapshot_source_edit = QLineEdit("手动对账")
        self.snapshot_notes_edit = QLineEdit()
        self.save_snapshot_button = QPushButton("新增快照")
        self.delete_snapshot_button = make_danger_button("删除快照")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        list_card, list_layout = create_card("账户列表", "左侧选择账户，右侧维护详情与快照")
        list_layout.addWidget(self.new_button)
        list_layout.addWidget(self.list_widget)

        detail_card, detail_layout = create_card("账户详情", "账户状态、用途与来源")
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        form.addRow("账户名称", self.name_edit)
        form.addRow("账户类型", self.type_combo)
        form.addRow("币种", self.currency_combo)
        form.addRow("主要用途", self.purpose_edit)
        form.addRow("状态", self.status_combo)
        form.addRow("来源", self.source_edit)
        form.addRow("备注", self.notes_edit)
        detail_layout.addLayout(form)
        detail_layout.addWidget(self.balance_preview)
        button_row = QHBoxLayout()
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.delete_button)
        detail_layout.addLayout(button_row)

        snapshot_card, snapshot_layout = create_card("余额快照", "用于校准余额")
        snapshot_layout.addWidget(self.snapshot_table)
        snapshot_form = QFormLayout()
        snapshot_form.setContentsMargins(0, 0, 0, 0)
        snapshot_form.addRow("快照时间", self.snapshot_time_edit)
        snapshot_form.addRow("快照金额", self.snapshot_amount_edit)
        snapshot_form.addRow("确认状态", self.snapshot_status_combo)
        snapshot_form.addRow("来源", self.snapshot_source_edit)
        snapshot_form.addRow("备注", self.snapshot_notes_edit)
        snapshot_layout.addLayout(snapshot_form)
        snapshot_button_row = QHBoxLayout()
        snapshot_button_row.addWidget(self.save_snapshot_button)
        snapshot_button_row.addWidget(self.delete_snapshot_button)
        snapshot_layout.addLayout(snapshot_button_row)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.addWidget(detail_card)
        right_layout.addWidget(snapshot_card)

        splitter = QSplitter()
        splitter.addWidget(list_card)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.new_button.clicked.connect(self.clear_editor)
        self.save_button.clicked.connect(self._emit_account_save)
        self.delete_button.clicked.connect(self._emit_account_delete)
        self.save_snapshot_button.clicked.connect(self._emit_snapshot_save)
        self.delete_snapshot_button.clicked.connect(self._emit_snapshot_delete)
        self.list_widget.currentItemChanged.connect(self._handle_current_item_changed)

    def load_accounts(self, accounts: list, balances: dict[str, str], snapshots: list) -> None:
        self._accounts = list(accounts)
        self._balances = dict(balances)
        self._snapshots_by_account = defaultdict(list)
        for snapshot in snapshots:
            self._snapshots_by_account[snapshot.account_id].append(snapshot)

        selected_id = self._current_account_id
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for account in self._accounts:
            balance_text = self._balances.get(account.id, "--")
            item = QListWidgetItem(f"{account.name}\n{account.account_type} · {balance_text}")
            item.setData(Qt.ItemDataRole.UserRole, account.id)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        if self.list_widget.count() == 0:
            self.clear_editor()
            self.snapshot_table.setRowCount(0)
            return
        index = 0
        if selected_id:
            for row in range(self.list_widget.count()):
                if self.list_widget.item(row).data(Qt.ItemDataRole.UserRole) == selected_id:
                    index = row
                    break
        self.list_widget.setCurrentRow(index)

    def set_default_currency(self, currency: str) -> None:
        self.default_currency = currency or "CNY"
        index = self.currency_combo.findText(self.default_currency)
        if index >= 0 and not self._current_account_id:
            self.currency_combo.setCurrentIndex(index)

    def clear_editor(self) -> None:
        self._current_account_id = ""
        self.name_edit.clear()
        self.purpose_edit.clear()
        self.status_combo.setCurrentText("正常")
        self.source_edit.setText("手动录入")
        self.notes_edit.clear()
        index = self.currency_combo.findText(self.default_currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        self.balance_preview.setText("当前余额：--")

    def _handle_current_item_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        account_id = current.data(Qt.ItemDataRole.UserRole)
        account = next((item for item in self._accounts if item.id == account_id), None)
        if account is None:
            return
        self._current_account_id = account.id
        self.name_edit.setText(account.name)
        self.type_combo.setCurrentText(account.account_type)
        self.currency_combo.setCurrentText(account.currency)
        self.purpose_edit.setText(account.purpose)
        self.status_combo.setCurrentText(account.status)
        self.source_edit.setText(account.source)
        self.notes_edit.setPlainText(account.notes)
        self.balance_preview.setText(f"当前余额：{self._balances.get(account.id, '--')}")
        self._render_snapshots(account.id)

    def _render_snapshots(self, account_id: str) -> None:
        snapshots = self._snapshots_by_account.get(account_id, [])
        self.snapshot_table.setRowCount(len(snapshots))
        for row_index, snapshot in enumerate(snapshots):
            self.snapshot_table.setItem(row_index, 0, QTableWidgetItem(snapshot.snapshot_time))
            self.snapshot_table.setItem(row_index, 1, QTableWidgetItem(snapshot.amount))
            self.snapshot_table.setItem(row_index, 2, QTableWidgetItem(snapshot.status))
            self.snapshot_table.setItem(row_index, 3, QTableWidgetItem(snapshot.source))
            self.snapshot_table.item(row_index, 0).setData(Qt.ItemDataRole.UserRole, snapshot.id)
        sync_table_columns(self.snapshot_table)

    def _emit_account_save(self) -> None:
        self.account_save_requested.emit(
            {
                "account_id": self._current_account_id,
                "name": self.name_edit.text().strip(),
                "account_type": self.type_combo.currentText().strip(),
                "currency": self.currency_combo.currentText().strip(),
                "purpose": self.purpose_edit.text().strip(),
                "status": self.status_combo.currentText().strip(),
                "source": self.source_edit.text().strip(),
                "notes": self.notes_edit.toPlainText().strip(),
            }
        )

    def _emit_account_delete(self) -> None:
        if self._current_account_id:
            self.account_delete_requested.emit(self._current_account_id)

    def _emit_snapshot_save(self) -> None:
        if not self._current_account_id:
            return
        self.snapshot_save_requested.emit(
            {
                "account_id": self._current_account_id,
                "snapshot_time": self.snapshot_time_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss"),
                "amount": self.snapshot_amount_edit.text().strip(),
                "status": self.snapshot_status_combo.currentText().strip(),
                "source": self.snapshot_source_edit.text().strip(),
                "notes": self.snapshot_notes_edit.text().strip(),
            }
        )

    def _emit_snapshot_delete(self) -> None:
        current_row = self.snapshot_table.currentRow()
        if current_row < 0:
            return
        item = self.snapshot_table.item(current_row, 0)
        if item is not None:
            snapshot_id = item.data(Qt.ItemDataRole.UserRole)
            if snapshot_id:
                self.snapshot_delete_requested.emit(str(snapshot_id))
