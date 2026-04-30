from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
    status_update_requested = Signal(object)
    batch_status_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._transactions = []
        self._accounts = []
        self._current_transaction_id = ""
        self._current_occurred_on = ""
        self._loading_editor = False

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索日期、类型、标签、备注或账户")
        self.month_filter_combo = QComboBox()
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(["全部类型", "只看收入", "只看支出", "转账", "充值", "退款"])
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("全部标签")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["全部状态", "已确认", "待确认"])
        self.apply_filter_button = make_secondary_button("应用筛选")
        self.clear_filter_button = make_secondary_button("清空")
        self.batch_status_combo = QComboBox()
        self.batch_status_combo.addItems(["批量改为已确认", "批量改为待确认"])
        self.batch_status_button = make_secondary_button("应用批量状态")
        self.batch_hint_label = QLabel("勾选流水后可批量修改确认状态。")
        self.batch_hint_label.setObjectName("MutedText")

        self.table = QTableWidget()
        prepare_table(self.table, ["选择", "日期", "类型", "标签", "备注", "付款账户", "收款账户", "状态", "金额"])
        self.table.horizontalHeader().setMinimumSectionSize(48)

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
        filter_row.addWidget(self.type_filter_combo, 1)
        filter_row.addWidget(self.tag_filter_combo, 1)
        filter_row.addWidget(self.status_filter_combo, 1)
        filter_row.addWidget(self.apply_filter_button)
        filter_row.addWidget(self.clear_filter_button)
        filter_layout.addLayout(filter_row)
        batch_row = QHBoxLayout()
        batch_row.addWidget(QLabel("批量状态"))
        batch_row.addWidget(self.batch_status_combo, 0)
        batch_row.addWidget(self.batch_status_button)
        batch_row.addWidget(self.batch_hint_label, 1)
        filter_layout.addLayout(batch_row)
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
        self.type_filter_combo.currentTextChanged.connect(self._apply_filters)
        self.tag_filter_combo.currentTextChanged.connect(self._apply_filters)
        self.status_combo.currentTextChanged.connect(self._emit_status_quick_save)
        self.batch_status_button.clicked.connect(self._emit_batch_status)
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
        self._loading_editor = True
        self._current_transaction_id = ""
        self._current_occurred_on = ""
        self.date_edit.setDate(QDate.currentDate())
        self.type_combo.setCurrentText("支出")
        self.category_edit.clear()
        self.amount_edit.clear()
        self.from_account_combo.setCurrentIndex(0)
        self.to_account_combo.setCurrentIndex(0)
        self.status_combo.setCurrentText("已确认")
        self.source_edit.setText("手动录入")
        self.notes_edit.clear()
        self._loading_editor = False

    def _clear_filters(self) -> None:
        self.search_edit.clear()
        self.month_filter_combo.setCurrentIndex(0)
        self.type_filter_combo.setCurrentIndex(0)
        self.tag_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.setCurrentIndex(0)
        self._apply_filters()

    def _apply_filters(self) -> None:
        keyword = self.search_edit.text().strip()
        month_key = self.month_filter_combo.currentText().strip()
        type_key = self.type_filter_combo.currentText().strip()
        tag_key = self.tag_filter_combo.currentText().strip()
        status_key = self.status_filter_combo.currentText().strip()
        rows = []
        for transaction in self._transactions:
            if month_key and month_key != "全部月份" and not transaction.occurred_on.startswith(month_key):
                continue
            if type_key and type_key != "全部类型":
                expected_type = {"只看收入": "收入", "只看支出": "支出"}.get(type_key, type_key)
                if transaction.transaction_type != expected_type:
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
            selection_item = QTableWidgetItem("")
            selection_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            selection_item.setCheckState(Qt.CheckState.Unchecked)
            selection_item.setData(Qt.ItemDataRole.UserRole, transaction.id)
            self.table.setItem(row_index, 0, selection_item)
            values = [
                transaction.occurred_on,
                transaction.transaction_type,
                transaction.category,
                self._display_note_summary(transaction.notes),
                self._account_name(transaction.from_account_id),
                self._account_name(transaction.to_account_id),
                transaction.status,
                transaction.amount,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, transaction.id)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table_column = column_index + 1
                if table_column == 4 and transaction.notes:
                    item.setToolTip(transaction.notes)
                self.table.setItem(row_index, table_column, item)
        self._sync_transaction_table_columns()

    def _sync_transaction_table_columns(self) -> None:
        sync_table_columns(self.table)
        header = self.table.horizontalHeader()
        fixed_widths = {
            0: 54,
            1: 132,
            2: 72,
            3: 126,
            5: 112,
            6: 112,
            7: 92,
            8: 96,
        }
        for column, width in fixed_widths.items():
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(column, width)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

    def _display_note_summary(self, notes: str) -> str:
        lines = [part.strip() for part in notes.splitlines() if part.strip()]
        for label in ("商户/备注", "原始备注", "备注", "商户"):
            for line in lines:
                value = self._extract_labeled_note_value(line, label)
                if value:
                    return value
        for line in lines:
            if not self._is_system_note_line(line):
                return line
        return ""

    def _extract_labeled_note_value(self, line: str, label: str) -> str:
        for separator in ("：", ":"):
            prefix = f"{label}{separator}"
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip()
        return ""

    def _is_system_note_line(self, line: str) -> bool:
        normalized = line.replace("：", ":").replace(" ", "")
        system_prefixes = (
            "同步来源:",
            "Obsidian文件:",
            "来源文件:",
            "来源行:",
            "来源附件:",
            "采集批次:",
            "回扫标记:",
            "标签:",
            "同步月份:",
            "源文件:",
            "原始行号:",
            "原始分类:",
            "原始账户:",
            "账户:",
            "账期口径:",
            "金额口径:",
            "更新日期:",
            "预算项:",
            "预算:",
            "实际:",
            "进度:",
        )
        return normalized.startswith(system_prefixes)

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
        self._loading_editor = True
        self._current_transaction_id = transaction.id
        self._current_occurred_on = transaction.occurred_on
        date_value = QDate.fromString(transaction.occurred_on[:10], "yyyy-MM-dd")
        self.date_edit.setDate(date_value if date_value.isValid() else QDate.currentDate())
        self.type_combo.setCurrentText(transaction.transaction_type)
        self.category_edit.setText(transaction.category)
        self.amount_edit.setText(transaction.amount)
        self.from_account_combo.setCurrentText(self._account_name(transaction.from_account_id))
        self.to_account_combo.setCurrentText(self._account_name(transaction.to_account_id))
        self.status_combo.setCurrentText(transaction.status)
        self.source_edit.setText(transaction.source)
        self.notes_edit.setPlainText(transaction.notes)
        self._loading_editor = False

    def _emit_save(self) -> None:
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        occurred_on = selected_date
        if self._current_occurred_on and self._current_occurred_on[:10] == selected_date:
            occurred_on = self._current_occurred_on
        self.save_requested.emit(
            {
                "transaction_id": self._current_transaction_id,
                "occurred_on": occurred_on,
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

    def _emit_status_quick_save(self, *_args) -> None:
        if self._loading_editor or not self._current_transaction_id:
            return
        self.status_update_requested.emit(
            {
                "transaction_id": self._current_transaction_id,
                "status": self.status_combo.currentText().strip() or "已确认",
            }
        )

    def _emit_batch_status(self) -> None:
        transaction_ids = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None or item.checkState() != Qt.CheckState.Checked:
                continue
            transaction_id = item.data(Qt.ItemDataRole.UserRole)
            if transaction_id:
                transaction_ids.append(transaction_id)
        if not transaction_ids:
            self.batch_hint_label.setText("先勾选要修改状态的流水。")
            return
        status = "已确认" if "已确认" in self.batch_status_combo.currentText() else "待确认"
        self.batch_hint_label.setText(f"已提交 {len(transaction_ids)} 条改为{status}。")
        self.batch_status_requested.emit({"transaction_ids": transaction_ids, "status": status})
