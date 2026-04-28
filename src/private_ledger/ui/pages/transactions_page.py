from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from private_ledger.ui.widgets import create_card, make_danger_button, make_secondary_button, prepare_table, sync_table_columns


class TransactionsPage(QWidget):
    save_requested = Signal(object)
    delete_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._transactions = []
        self._accounts = []
        self._current_transaction_id = ""

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索日期、类型、标签、备注或账户")
        self.month_filter_combo = QComboBox()
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("全部标签")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["全部状态", "已确认", "待确认"])
        self.apply_filter_button = make_secondary_button("应用筛选")
        self.clear_filter_button = make_secondary_button("清空")

        self.table = QTableWidget()
        prepare_table(self.table, ["日期", "类型", "标签", "备注", "付款账户", "收款账户", "状态", "金额"])

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出", "转账", "充值", "退款"])
        self.category_edit = QLineEdit()
        self.amount_edit = QLineEdit()
        self.from_account_combo = QComboBox()
        self.to_account_combo = QComboBox()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["已确认", "待确认"])
        self.source_edit = QLineEdit("手动录入")
        self.notes_edit = QTextEdit()
        self.new_button = make_secondary_button("新建流水")
        self.save_button = QPushButton("保存流水")
        self.delete_button = make_danger_button("删除流水")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        filter_card, filter_layout = create_card("流水筛选", "按月份、状态和关键词过滤")
        filter_row = QHBoxLayout()
        filter_row.addWidget(self.search_edit, 2)
        filter_row.addWidget(self.month_filter_combo, 1)
        filter_row.addWidget(self.tag_filter_combo, 1)
        filter_row.addWidget(self.status_filter_combo, 1)
        filter_row.addWidget(self.apply_filter_button)
        filter_row.addWidget(self.clear_filter_button)
        filter_layout.addLayout(filter_row)
        filter_layout.addWidget(self.table)

        detail_card, detail_layout = create_card("流水编辑", "收入、支出、转账、充值、退款")
        form = QFormLayout()
        form.addRow("发生日期", self.date_edit)
        form.addRow("类型", self.type_combo)
        form.addRow("标签", self.category_edit)
        form.addRow("金额", self.amount_edit)
        form.addRow("付款账户", self.from_account_combo)
        form.addRow("收款账户", self.to_account_combo)
        form.addRow("确认状态", self.status_combo)
        form.addRow("来源", self.source_edit)
        form.addRow("备注", self.notes_edit)
        detail_layout.addLayout(form)
        button_row = QHBoxLayout()
        button_row.addWidget(self.new_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.delete_button)
        detail_layout.addLayout(button_row)

        splitter = QSplitter()
        splitter.addWidget(filter_card)
        splitter.addWidget(detail_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.new_button.clicked.connect(self.clear_editor)
        self.save_button.clicked.connect(self._emit_save)
        self.delete_button.clicked.connect(self._emit_delete)
        self.apply_filter_button.clicked.connect(self._apply_filters)
        self.clear_filter_button.clicked.connect(self._clear_filters)
        self.tag_filter_combo.currentTextChanged.connect(self._apply_filters)
        self.table.itemSelectionChanged.connect(self._handle_selection_changed)

    def load_accounts(self, accounts: list) -> None:
        self._accounts = list(accounts)
        entries = [""] + [account.name for account in self._accounts]
        self.from_account_combo.clear()
        self.to_account_combo.clear()
        self.from_account_combo.addItems(entries)
        self.to_account_combo.addItems(entries)

    def load_transactions(self, transactions: list) -> None:
        self._transactions = list(transactions)
        months = sorted({transaction.occurred_on[:7] for transaction in transactions if transaction.occurred_on}, reverse=True)
        tags = sorted({transaction.category for transaction in transactions if transaction.category})
        current_month = self.month_filter_combo.currentText()
        current_tag = self.tag_filter_combo.currentText()
        self.month_filter_combo.blockSignals(True)
        self.month_filter_combo.clear()
        self.month_filter_combo.addItem("全部月份")
        self.month_filter_combo.addItems(months)
        if current_month:
            index = self.month_filter_combo.findText(current_month)
            self.month_filter_combo.setCurrentIndex(index if index >= 0 else 0)
        self.month_filter_combo.blockSignals(False)

        self.tag_filter_combo.blockSignals(True)
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("全部标签")
        self.tag_filter_combo.addItems(tags)
        if current_tag:
            index = self.tag_filter_combo.findText(current_tag)
            self.tag_filter_combo.setCurrentIndex(index if index >= 0 else 0)
        self.tag_filter_combo.blockSignals(False)
        self._apply_filters()

    def clear_editor(self) -> None:
        self._current_transaction_id = ""
        self.date_edit.setDate(QDate.currentDate())
        self.type_combo.setCurrentText("支出")
        self.category_edit.clear()
        self.amount_edit.clear()
        self.from_account_combo.setCurrentIndex(0)
        self.to_account_combo.setCurrentIndex(0)
        self.status_combo.setCurrentText("已确认")
        self.source_edit.setText("手动录入")
        self.notes_edit.clear()

    def _clear_filters(self) -> None:
        self.search_edit.clear()
        self.month_filter_combo.setCurrentIndex(0)
        self.tag_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.setCurrentIndex(0)
        self._apply_filters()

    def _apply_filters(self) -> None:
        keyword = self.search_edit.text().strip()
        month_key = self.month_filter_combo.currentText().strip()
        tag_key = self.tag_filter_combo.currentText().strip()
        status_key = self.status_filter_combo.currentText().strip()
        rows = []
        for transaction in self._transactions:
            if month_key and month_key != "全部月份" and not transaction.occurred_on.startswith(month_key):
                continue
            if tag_key and tag_key != "全部标签" and transaction.category != tag_key:
                continue
            if status_key and status_key != "全部状态" and transaction.status != status_key:
                continue
            searchable = " ".join(
                [
                    transaction.occurred_on,
                    transaction.transaction_type,
                    transaction.category,
                    transaction.status,
                    transaction.notes,
                    self._account_name(transaction.from_account_id),
                    self._account_name(transaction.to_account_id),
                ]
            )
            if keyword and keyword not in searchable:
                continue
            rows.append(transaction)
        self.table.setRowCount(len(rows))
        for row_index, transaction in enumerate(rows):
            values = [
                transaction.occurred_on,
                transaction.transaction_type,
                transaction.category,
                self._one_line_note(transaction.notes),
                self._account_name(transaction.from_account_id),
                self._account_name(transaction.to_account_id),
                transaction.status,
                transaction.amount,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, transaction.id)
                if column_index == 3 and transaction.notes:
                    item.setToolTip(transaction.notes)
                self.table.setItem(row_index, column_index, item)
        sync_table_columns(self.table)

    def _one_line_note(self, notes: str) -> str:
        return "；".join(part.strip() for part in notes.splitlines() if part.strip())

    def _account_name(self, account_id: str) -> str:
        account = next((item for item in self._accounts if item.id == account_id), None)
        return account.name if account else ""

    def _find_account_id(self, name: str) -> str:
        account = next((item for item in self._accounts if item.name == name), None)
        return account.id if account else ""

    def _handle_selection_changed(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is None:
            return
        transaction_id = item.data(Qt.ItemDataRole.UserRole)
        transaction = next((value for value in self._transactions if value.id == transaction_id), None)
        if transaction is None:
            return
        self._current_transaction_id = transaction.id
        self.date_edit.setDate(QDate.fromString(transaction.occurred_on, "yyyy-MM-dd"))
        self.type_combo.setCurrentText(transaction.transaction_type)
        self.category_edit.setText(transaction.category)
        self.amount_edit.setText(transaction.amount)
        self.from_account_combo.setCurrentText(self._account_name(transaction.from_account_id))
        self.to_account_combo.setCurrentText(self._account_name(transaction.to_account_id))
        self.status_combo.setCurrentText(transaction.status)
        self.source_edit.setText(transaction.source)
        self.notes_edit.setPlainText(transaction.notes)

    def _emit_save(self) -> None:
        self.save_requested.emit(
            {
                "transaction_id": self._current_transaction_id,
                "occurred_on": self.date_edit.date().toString("yyyy-MM-dd"),
                "transaction_type": self.type_combo.currentText().strip(),
                "category": self.category_edit.text().strip(),
                "amount": self.amount_edit.text().strip(),
                "from_account_id": self._find_account_id(self.from_account_combo.currentText().strip()),
                "to_account_id": self._find_account_id(self.to_account_combo.currentText().strip()),
                "status": self.status_combo.currentText().strip(),
                "source": self.source_edit.text().strip(),
                "notes": self.notes_edit.toPlainText().strip(),
            }
        )

    def _emit_delete(self) -> None:
        if self._current_transaction_id:
            self.delete_requested.emit(self._current_transaction_id)
