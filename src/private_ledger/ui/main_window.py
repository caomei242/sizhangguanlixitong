from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from private_ledger.domain.ledger import (
    build_annual_budget_matrix,
    build_budget_comparison,
    build_monthly_trend,
    build_month_summary,
    build_period_summary,
    calculate_account_balance,
    collect_due_reminders,
    format_money,
    period_label,
    period_month_keys,
    parse_decimal,
)
from private_ledger.domain.models import (
    Account,
    AppSettings,
    BalanceSnapshot,
    BudgetLine,
    MonthlyBudget,
    PeriodSelection,
    ReminderItem,
    Transaction,
    new_id,
    now_timestamp,
)
from private_ledger.storage.repository import LedgerRepository
from private_ledger.services.import_recognition import ImportRecognitionService
from private_ledger.services.keychain import KeychainStore
from private_ledger.services.minimax_clients import MiniMaxOcrMcpClient, MiniMaxTextClient
from private_ledger.ui.pages.accounts_page import AccountsPage
from private_ledger.ui.pages.budgets_page import BudgetsPage
from private_ledger.ui.pages.dashboard_page import DashboardPage
from private_ledger.ui.pages.imports_page import ImportsPage
from private_ledger.ui.pages.reminders_page import RemindersPage
from private_ledger.ui.pages.settings_page import SettingsPage
from private_ledger.ui.pages.transactions_page import TransactionsPage
from private_ledger.ui.theme import apply_theme
from private_ledger.ui.widgets import make_secondary_button


def current_month_key() -> str:
    return date.today().strftime("%Y-%m")


class MainWindow(QMainWindow):
    def __init__(self, repository: LedgerRepository) -> None:
        super().__init__()
        self.repository = repository
        self.keychain = KeychainStore()
        self.reference_month = current_month_key()
        self._configure_window_behavior()
        self.setWindowTitle("草莓私帐管理系统")
        self.resize(1460, 980)

        self.nav = QListWidget()
        self.nav.addItems(["月度看板", "私人账户", "流水记录", "预算计划", "充值续费", "数据导入", "设置"])
        self.nav.setFixedWidth(192)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.setSpacing(4)

        self.page_title_label = QLabel("月度看板")
        self.page_title_label.setObjectName("PageTitle")
        self.page_meta_label = QLabel("本地私帐工作台")
        self.page_meta_label.setObjectName("MutedText")
        self.page_meta_label.setWordWrap(False)
        self.page_meta_label.setMinimumWidth(0)
        self.page_meta_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.period_granularity_combo = QComboBox()
        self.period_granularity_combo.addItems(["月", "季", "年"])
        self.period_value_combo = QComboBox()
        self.month_combo = self.period_value_combo
        self.export_button = make_secondary_button("导出 JSON")
        self.quick_action_button = QPushButton("新增流水")

        self.dashboard_page = DashboardPage()
        self.accounts_page = AccountsPage()
        self.transactions_page = TransactionsPage()
        self.budgets_page = BudgetsPage()
        self.reminders_page = RemindersPage()
        self.imports_page = ImportsPage()
        self.settings_page = SettingsPage()

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        for page in (
            self.dashboard_page,
            self.accounts_page,
            self.transactions_page,
            self.budgets_page,
            self.reminders_page,
            self.imports_page,
            self.settings_page,
        ):
            self.stack.addWidget(page)

        self._build_ui()
        self._connect_signals()
        self.refresh_data(reference_month=self.reference_month)
        self.nav.setCurrentRow(0)
        apply_theme(self)
        self._sync_navigation_height()

    def _configure_window_behavior(self) -> None:
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.CustomizeWindowHint, False)
        self.setWindowFlag(Qt.WindowType.WindowTitleHint, True)
        self.setWindowFlag(Qt.WindowType.WindowSystemMenuHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.setWindowModality(Qt.WindowModality.NonModal)

    def _build_ui(self) -> None:
        brand_title = QLabel("草莓私帐管理系统")
        brand_title.setObjectName("BrandTitle")
        brand_subtitle = QLabel("私人账户管理系统")
        brand_subtitle.setObjectName("BrandSubtitle")
        sidebar_note = QLabel("本地优先、保守口径、可追溯。待确认数据不会进入正式统计。")
        sidebar_note.setObjectName("MutedText")
        sidebar_note.setWordWrap(True)

        brand_box = QVBoxLayout()
        brand_box.setContentsMargins(0, 0, 0, 0)
        brand_box.setSpacing(2)
        brand_box.addWidget(brand_title)
        brand_box.addWidget(brand_subtitle)

        sidebar = QFrame()
        sidebar.setObjectName("WindowSidebar")
        sidebar.setFixedWidth(264)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(16)
        sidebar_layout.addLayout(brand_box)
        sidebar_layout.addWidget(self.nav, 0, Qt.AlignmentFlag.AlignTop)
        sidebar_layout.addWidget(sidebar_note)
        sidebar_layout.addStretch(1)

        header = QFrame()
        header.setObjectName("ToolbarCard")
        header_layout = QGridLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setHorizontalSpacing(12)
        header_layout.setVerticalSpacing(6)
        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(10)
        controls_row.addWidget(self.period_granularity_combo)
        controls_row.addWidget(self.period_value_combo)
        controls_row.addWidget(self.export_button)
        controls_row.addWidget(self.quick_action_button)
        header_layout.addWidget(self.page_title_label, 0, 0)
        header_layout.addLayout(controls_row, 0, 1, Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.page_meta_label, 1, 0, 1, 2)
        header_layout.setColumnStretch(0, 1)

        content = QFrame()
        content.setObjectName("WindowContentShell")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(14)
        content_layout.addWidget(header)
        self.content_scroll = QScrollArea()
        self.content_scroll.setObjectName("ContentScroll")
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_scroll.setMinimumSize(0, 0)
        self.content_scroll.setWidget(self.stack)
        content_layout.addWidget(self.content_scroll, 1)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(sidebar)
        body_layout.addWidget(content, 1)

        shell = QFrame()
        shell.setObjectName("WindowShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.addWidget(body)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.addWidget(shell)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.nav.currentRowChanged.connect(self._handle_nav_changed)
        self.period_granularity_combo.currentTextChanged.connect(self._handle_period_granularity_changed)
        self.period_value_combo.currentTextChanged.connect(self._handle_period_value_changed)
        self.export_button.clicked.connect(self._export_json)
        self.quick_action_button.clicked.connect(lambda: self.nav.setCurrentRow(2))

        self.accounts_page.account_save_requested.connect(self._save_account)
        self.accounts_page.account_delete_requested.connect(self._delete_account)
        self.accounts_page.snapshot_save_requested.connect(self._save_snapshot)
        self.accounts_page.snapshot_delete_requested.connect(self._delete_snapshot)

        self.transactions_page.save_requested.connect(self._save_transaction)
        self.transactions_page.delete_requested.connect(self._delete_transaction)

        self.budgets_page.budget_save_requested.connect(self._save_budget)
        self.budgets_page.budget_line_save_requested.connect(self._save_budget_line)
        self.budgets_page.budget_line_delete_requested.connect(self._delete_budget_line)
        self.budgets_page.budget_seed_requested.connect(self._seed_budget_from_actual)
        self.budgets_page.budget_month_changed.connect(lambda month_key: self.refresh_data(reference_month=month_key))
        self.budgets_page.annual_status_change_requested.connect(self._sync_annual_budget_status)

        self.reminders_page.save_requested.connect(self._save_reminder)
        self.reminders_page.delete_requested.connect(self._delete_reminder)

        self.imports_page.choose_image_requested.connect(self._choose_import_image)
        self.imports_page.paste_image_requested.connect(self._paste_import_image)
        self.imports_page.recognize_requested.connect(self._recognize_selected_import_image)
        self.imports_page.confirm_import_requested.connect(self._confirm_import_batch)

        self.settings_page.save_requested.connect(self._save_settings)
        self.settings_page.minimax_key_save_requested.connect(self._save_minimax_key)
        self.settings_page.minimax_test_requested.connect(self._test_minimax_connection)
        self.settings_page.export_requested.connect(self._export_json)
        self.settings_page.backup_requested.connect(self._backup_database)

    def _sync_navigation_height(self) -> None:
        if self.nav.count() == 0:
            return
        frame_height = self.nav.frameWidth() * 2
        row_heights = sum(max(self.nav.sizeHintForRow(index), 56) for index in range(self.nav.count()))
        spacing_height = max(0, self.nav.count() - 1) * self.nav.spacing()
        self.nav.setFixedHeight(frame_height + row_heights + spacing_height + 12)

    def refresh_data(self, reference_month: str | None = None) -> None:
        if reference_month:
            self.reference_month = reference_month
        accounts = self.repository.list_accounts()
        snapshots = self.repository.list_snapshots()
        transactions = self.repository.list_transactions()
        self._refresh_period_choices(transactions)
        selection = self._current_period_selection()
        if selection.granularity == "month":
            self.reference_month = period_label(selection)
        budget = self.repository.get_monthly_budget(self.reference_month)
        budget_lines = self.repository.list_effective_budget_lines(self.reference_month)
        budget_comparison = build_budget_comparison(self.reference_month, budget_lines, transactions)
        annual_budget_matrix = build_annual_budget_matrix(
            int(self.reference_month[:4]),
            self._list_all_budget_lines(),
            transactions,
        )
        reminders = self.repository.list_reminders()
        settings = self.repository.load_settings()
        settings.minimax_key_configured = self.keychain.has_secret()

        balances = {
            account.id: format_money(
                calculate_account_balance(account, snapshots, transactions),
                account.currency,
            )
            for account in accounts
        }
        summary = build_month_summary(
            self.reference_month,
            budget,
            transactions,
            total_budget_override=budget_comparison.summary.planned_expense if budget_lines else None,
        )
        period_summary = build_period_summary(selection, transactions)
        trend_points = build_monthly_trend(selection, transactions)
        due_reminders = collect_due_reminders(
            reminders=reminders,
            accounts=accounts,
            snapshots=snapshots,
            transactions=transactions,
            lead_days=settings.reminder_lead_days,
        )
        selected_month_keys = set(period_month_keys(selection))
        period_transactions = [
            transaction for transaction in transactions
            if transaction.occurred_on[:7] in selected_month_keys
        ]
        self._load_dashboard(
            accounts,
            period_transactions,
            transactions,
            snapshots,
            due_reminders,
            summary,
            budget,
            period_summary,
            trend_points,
            selection,
        )
        self.accounts_page.set_default_currency(settings.default_currency)
        self.accounts_page.load_accounts(accounts, balances, snapshots)
        self.transactions_page.load_accounts(accounts)
        self.transactions_page.load_transactions(transactions)
        self.budgets_page.load_budget(self.reference_month, budget, budget_lines, budget_comparison, annual_budget_matrix)
        self.reminders_page.load_accounts(accounts)
        self.reminders_page.load_reminders(reminders)
        self.imports_page.load_batches(self.repository.list_import_batches())
        self.settings_page.load_settings(settings, str(self.repository.db_path))
        self._update_page_meta(period_summary.label)

    def _update_page_meta(self, period_label_text: str) -> None:
        db_path = Path(self.repository.db_path)
        self.page_meta_label.setText(f"范围：{period_label_text} · 数据库：{db_path.name}")
        self.page_meta_label.setToolTip(f"本地 SQLite：{db_path}")

    def _list_all_budget_lines(self) -> list[BudgetLine]:
        rows = self.repository.connection.execute(
            "SELECT * FROM budget_lines ORDER BY line_kind, name COLLATE NOCASE ASC"
        ).fetchall()
        return [self.repository._row_to_budget_line(row) for row in rows]

    def _refresh_period_choices(self, transactions: list[Transaction]) -> None:
        today = date.today()
        years = {today.year}
        months = {current_month_key(), self.reference_month}
        for transaction in transactions:
            if not transaction.occurred_on:
                continue
            months.add(transaction.occurred_on[:7])
            if transaction.occurred_on[:4].isdigit():
                years.add(int(transaction.occurred_on[:4]))

        granularity_text = self.period_granularity_combo.currentText() or "月"
        current_value = self.period_value_combo.currentText()
        if granularity_text == "月":
            values = sorted(months, reverse=True)
            preferred = self.reference_month
        elif granularity_text == "季":
            values = [
                f"{year} Q{quarter}"
                for year in sorted(years, reverse=True)
                for quarter in (4, 3, 2, 1)
            ]
            current_quarter = (today.month - 1) // 3 + 1
            preferred = current_value if current_value in values else f"{today.year} Q{current_quarter}"
        else:
            values = [str(year) for year in sorted(years, reverse=True)]
            preferred = current_value if current_value in values else str(today.year)

        self.period_value_combo.blockSignals(True)
        self.period_value_combo.clear()
        self.period_value_combo.addItems(values)
        index = self.period_value_combo.findText(preferred)
        self.period_value_combo.setCurrentIndex(index if index >= 0 else 0)
        self.period_value_combo.blockSignals(False)

    def _current_period_selection(self) -> PeriodSelection:
        granularity_text = self.period_granularity_combo.currentText() or "月"
        value = self.period_value_combo.currentText() or self.reference_month
        if granularity_text == "季":
            year_text, quarter_text = value.split(" Q")
            quarter = int(quarter_text)
            return PeriodSelection(
                granularity="quarter",
                year=int(year_text),
                month=(quarter - 1) * 3 + 1,
                quarter=quarter,
            )
        if granularity_text == "年":
            return PeriodSelection(
                granularity="year",
                year=int(value),
                month=1,
                quarter=1,
            )
        year, month = value.split("-")
        month_value = int(month)
        return PeriodSelection(
            granularity="month",
            year=int(year),
            month=month_value,
            quarter=(month_value - 1) // 3 + 1,
        )

    def _load_dashboard(
        self,
        accounts,
        display_transactions,
        all_transactions,
        snapshots,
        due_reminders,
        summary,
        budget,
        period_summary,
        trend_points,
        selection,
    ) -> None:
        account_rows = []
        for account in accounts:
            account_rows.append(
                {
                    "name": account.name,
                    "account_type": account.account_type,
                    "purpose": account.purpose,
                    "balance_text": format_money(
                        calculate_account_balance(account, snapshots, all_transactions),
                        account.currency,
                    ),
                    "status": account.status,
                }
            )
        transaction_rows = []
        for transaction in display_transactions[:8]:
            if transaction.transaction_type in {"转账", "充值"}:
                account_text = self._account_name(transaction.from_account_id, accounts)
                if transaction.to_account_id:
                    account_text = f"{account_text} → {self._account_name(transaction.to_account_id, accounts)}".strip(" →")
            elif transaction.transaction_type == "收入":
                account_text = self._account_name(transaction.to_account_id, accounts)
            elif transaction.transaction_type == "退款":
                account_text = self._account_name(transaction.to_account_id, accounts)
            else:
                account_text = self._account_name(transaction.from_account_id, accounts)
            currency = self._account_currency(transaction.to_account_id or transaction.from_account_id, accounts)
            sign = "+" if transaction.transaction_type in {"收入", "退款"} else ""
            transaction_rows.append(
                {
                    "occurred_on": transaction.occurred_on,
                    "transaction_type": transaction.transaction_type,
                    "category": transaction.category,
                    "account_text": account_text or "-",
                    "status": transaction.status,
                    "amount_text": f"{sign}{format_money(transaction.amount, currency)}",
                }
            )

        pending_items = []
        for transaction in display_transactions:
            if transaction.status != "已确认":
                pending_items.append(f"{transaction.occurred_on} · {transaction.category} · 待确认")
        latest_snapshots = {}
        for snapshot in snapshots:
            if snapshot.status != "已确认":
                continue
            latest_snapshots.setdefault(snapshot.account_id, snapshot)
        today = date.today()
        for account in accounts:
            snapshot = latest_snapshots.get(account.id)
            if snapshot is None:
                pending_items.append(f"{account.name} · 尚未建立已确认余额快照")
                continue
            snap_day = datetime.fromisoformat(snapshot.snapshot_time).date()
            if (today - snap_day).days > 14:
                pending_items.append(f"{account.name} · 余额快照超过 14 天未更新")

        reminder_rows = []
        for reminder in due_reminders:
            when_text = reminder.due_date or reminder.current_value
            reminder_rows.append(
                {
                    "title": reminder.title,
                    "target_type": reminder.target_type,
                    "when_text": when_text,
                    "display_status": reminder.display_status,
                }
            )

        expense_ratio = "0%"
        if summary.total_budget > 0:
            expense_ratio = f"{(summary.actual_expense / summary.total_budget * 100):.1f}%"
        remaining_tag = "充足" if summary.remaining_budget >= 0 else "超支"
        self.dashboard_page.load_snapshot(
            {
                "summary": summary,
                "budget_status": budget.status if budget else "未设置",
                "expense_tag": expense_ratio,
                "remaining_tag": remaining_tag,
                "pending_tag": f"{len([t for t in display_transactions if t.status != '已确认'])} 笔",
                "period_granularity": selection.granularity,
                "period_summary": period_summary,
                "trend_points": trend_points,
                "accounts": account_rows,
                "reminders": reminder_rows,
                "transactions": transaction_rows,
                "pending_items": pending_items,
            }
        )

    def _handle_nav_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        page_title = self.nav.item(index).text() if index >= 0 else ""
        self.page_title_label.setText(page_title)
        is_budget_page = index == 3
        if is_budget_page and self.period_granularity_combo.currentText() != "月":
            self.period_granularity_combo.setCurrentText("月")
        self.period_granularity_combo.setVisible(not is_budget_page)

    def _handle_period_granularity_changed(self, _text: str) -> None:
        self.refresh_data()

    def _handle_period_value_changed(self, value: str) -> None:
        if not value:
            return
        if self.period_granularity_combo.currentText() == "月":
            self.refresh_data(reference_month=value)
        else:
            self.refresh_data()

    def _account_name(self, account_id: str, accounts: list[Account]) -> str:
        account = next((value for value in accounts if value.id == account_id), None)
        return account.name if account else ""

    def _account_currency(self, account_id: str, accounts: list[Account]) -> str:
        account = next((value for value in accounts if value.id == account_id), None)
        return account.currency if account else "CNY"

    def _save_account(self, payload: dict) -> None:
        if not payload["name"] or not payload["account_type"]:
            self._show_warning("账户名称和账户类型不能为空。")
            return
        now = now_timestamp()
        account = Account(
            id=payload["account_id"] or new_id("acc"),
            name=payload["name"],
            account_type=payload["account_type"],
            currency=payload["currency"] or "CNY",
            purpose=payload["purpose"],
            status=payload["status"] or "正常",
            notes=payload["notes"],
            source=payload["source"] or "手动录入",
            created_at=now if not payload["account_id"] else self._created_at_for_account(payload["account_id"]),
            updated_at=now,
        )
        self.repository.upsert_account(account)
        self.refresh_data()

    def _delete_account(self, account_id: str) -> None:
        if self._confirm_delete("确定删除这个账户吗？余额快照会一起删除。"):
            self.repository.delete_account(account_id)
            self.refresh_data()

    def _created_at_for_account(self, account_id: str) -> str:
        account = next((item for item in self.repository.list_accounts() if item.id == account_id), None)
        return account.created_at if account else now_timestamp()

    def _save_snapshot(self, payload: dict) -> None:
        if not payload["amount"]:
            self._show_warning("快照金额不能为空。")
            return
        snapshot = BalanceSnapshot(
            id=new_id("snap"),
            account_id=payload["account_id"],
            snapshot_time=payload["snapshot_time"],
            amount=f"{parse_decimal(payload['amount']):.2f}",
            status=payload["status"] or "已确认",
            source=payload["source"] or "手动对账",
            notes=payload["notes"],
            created_at=now_timestamp(),
        )
        self.repository.add_snapshot(snapshot)
        self.refresh_data()

    def _delete_snapshot(self, snapshot_id: str) -> None:
        if self._confirm_delete("确定删除这条余额快照吗？"):
            self.repository.delete_snapshot(snapshot_id)
            self.refresh_data()

    def _save_transaction(self, payload: dict) -> None:
        if not payload["amount"] or not payload["category"]:
            self._show_warning("流水金额和标签不能为空。")
            return
        now = now_timestamp()
        transaction = Transaction(
            id=payload["transaction_id"] or new_id("txn"),
            occurred_on=payload["occurred_on"],
            transaction_type=payload["transaction_type"],
            category=payload["category"],
            amount=f"{parse_decimal(payload['amount']):.2f}",
            from_account_id=payload["from_account_id"],
            to_account_id=payload["to_account_id"],
            status=payload["status"] or "已确认",
            source=payload["source"] or "手动录入",
            notes=payload["notes"],
            related_transaction_id="",
            created_at=now if not payload["transaction_id"] else self._created_at_for_transaction(payload["transaction_id"]),
            updated_at=now,
        )
        self.repository.upsert_transaction(transaction)
        self.refresh_data()

    def _delete_transaction(self, transaction_id: str) -> None:
        if self._confirm_delete("确定删除这条流水吗？"):
            self.repository.delete_transaction(transaction_id)
            self.refresh_data()

    def _created_at_for_transaction(self, transaction_id: str) -> str:
        transaction = next((item for item in self.repository.list_transactions() if item.id == transaction_id), None)
        return transaction.created_at if transaction else now_timestamp()

    def _save_budget(self, payload: dict) -> None:
        if not payload["month_key"]:
            self._show_warning("预算月份不能为空。")
            return
        existing = self.repository.get_monthly_budget(payload["month_key"])
        now = now_timestamp()
        budget = MonthlyBudget(
            id=existing.id if existing else new_id("budget"),
            month_key=payload["month_key"],
            total_budget=f"{parse_decimal(payload['total_budget'] or '0'):.2f}",
            notes=payload["notes"],
            status="生效中",
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self.repository.upsert_budget(budget)
        self.refresh_data(reference_month=payload["month_key"])

    def _save_budget_line(self, payload: dict) -> None:
        if not payload["name"] or not payload["planned_amount"]:
            self._show_warning("预算项名称和计划金额不能为空。")
            return
        if payload["effective_end_month"] and payload["effective_end_month"] < payload["effective_start_month"]:
            self._show_warning("预算项结束月份不能早于开始月份。")
            return
        budget = self.repository.get_monthly_budget(payload["month_key"])
        now = now_timestamp()
        if budget is None:
            budget = MonthlyBudget(
                id=new_id("budget"),
                month_key=payload["month_key"],
                total_budget="0.00",
                notes="",
                status="生效中",
                created_at=now,
                updated_at=now,
            )
            self.repository.upsert_budget(budget)
        existing = self.repository.get_budget_line(payload["line_id"]) if payload["line_id"] else None
        line = BudgetLine(
            id=payload["line_id"] or new_id("line"),
            budget_id=existing.budget_id if existing else budget.id,
            line_kind=payload["line_kind"],
            name=payload["name"],
            category=payload["category"] or payload["name"],
            planned_amount=f"{parse_decimal(payload['planned_amount']):.2f}",
            day_of_month=payload["day_of_month"],
            is_required=bool(payload["is_required"]),
            reminder_days=int(payload["reminder_days"]),
            notes=payload["notes"],
            created_at=existing.created_at if existing else now,
            updated_at=now,
            effective_start_month=payload["effective_start_month"],
            effective_end_month=payload["effective_end_month"],
        )
        self.repository.upsert_budget_line(line)
        self._sync_budget_total_from_lines(payload["month_key"])
        self.refresh_data(reference_month=payload["month_key"])

    def _sync_annual_budget_status(self, payload: dict) -> None:
        month_key = str(payload.get("month_key") or self.reference_month)
        detail_type = str(payload.get("detail_type") or "")
        category = str(payload.get("category") or "")
        name = str(payload.get("name") or "")
        target_status = str(payload.get("target_status") or "")
        mode = str(payload.get("mode") or "single")
        match_rows = list(payload.get("match_rows") or [])
        if target_status != "已确认":
            return

        matched = []
        for transaction in self.repository.list_transactions():
            if not transaction.occurred_on.startswith(month_key):
                continue
            if transaction.status != "待确认":
                continue
            if mode in {"all_other", "all_panel"}:
                if not any(
                    transaction.transaction_type == str(item.get("detail_type") or "")
                    and transaction.category in {str(item.get("category") or ""), str(item.get("name") or "")}
                    for item in match_rows
                ):
                    continue
            else:
                if transaction.transaction_type != detail_type:
                    continue
                if transaction.category not in {category, name}:
                    continue
            matched.append(transaction)

        if not matched:
            self._show_warning("没有找到可同步确认的待确认流水。")
            return

        now = now_timestamp()
        for transaction in matched:
            transaction.status = "已确认"
            transaction.updated_at = now
            self.repository.upsert_transaction(transaction)
        self.refresh_data(reference_month=month_key)

    def _delete_budget_line(self, budget_line_id: str) -> None:
        if self._confirm_delete("确定删除这条预算项吗？"):
            budget_month = self._month_for_budget_line(budget_line_id)
            self.repository.delete_budget_line(budget_line_id)
            if budget_month:
                self._sync_budget_total_from_lines(budget_month)
            self.refresh_data()

    def _seed_budget_from_actual(self, month_key: str) -> None:
        budget = self.repository.get_monthly_budget(month_key)
        now = now_timestamp()
        if budget is None:
            budget = MonthlyBudget(
                id=new_id("budget"),
                month_key=month_key,
                total_budget="0.00",
                notes="由当月实际生成预算草稿，待手动调整。",
                status="生效中",
                created_at=now,
                updated_at=now,
            )
            self.repository.upsert_budget(budget)

        budget_lines = self.repository.list_effective_budget_lines(month_key)
        comparison = build_budget_comparison(month_key, budget_lines, self.repository.list_transactions())
        created_count = 0
        for row in comparison.rows:
            if row.group_name != "未设预算但本月有实际":
                continue
            if parse_decimal(row.actual_amount) <= 0:
                continue
            notes = "\n".join(
                [
                    "草稿待调整",
                    "来源：按当月实际生成预算草稿",
                    f"生成月份：{month_key}",
                    f"更新时间：{now}",
                ]
            )
            self.repository.upsert_budget_line(
                BudgetLine(
                    id=new_id("line"),
                    budget_id=budget.id,
                    line_kind=row.line_kind,
                    name=row.name,
                    category=row.category or row.name,
                    planned_amount=f"{parse_decimal(row.actual_amount):.2f}",
                    day_of_month=None,
                    is_required=False,
                    reminder_days=0,
                    notes=notes,
                    created_at=now,
                    updated_at=now,
                    effective_start_month=month_key,
                    effective_end_month=month_key,
                )
            )
            created_count += 1

        if created_count == 0:
            self._show_warning("当前月份没有可生成的新增预算草稿。")
            return
        self._sync_budget_total_from_lines(month_key)
        self.refresh_data(reference_month=month_key)

    def _sync_budget_total_from_lines(self, month_key: str) -> None:
        budget = self.repository.get_monthly_budget(month_key)
        if budget is None:
            return
        total = sum(
            parse_decimal(line.planned_amount)
            for line in self.repository.list_effective_budget_lines(month_key)
            if line.line_kind in {"分类预算", "固定支出", "储蓄计划", "支出"}
        )
        budget.total_budget = f"{total:.2f}"
        budget.updated_at = now_timestamp()
        self.repository.upsert_budget(budget)

    def _month_for_budget_line(self, budget_line_id: str) -> str:
        for budget in self.repository.connection.execute("SELECT * FROM monthly_budgets").fetchall():
            lines = self.repository.list_budget_lines(budget["id"])
            if any(line.id == budget_line_id for line in lines):
                return budget["month_key"]
        return ""

    def _save_reminder(self, payload: dict) -> None:
        if not payload["title"]:
            self._show_warning("提醒标题不能为空。")
            return
        now = now_timestamp()
        existing = next((item for item in self.repository.list_reminders() if item.id == payload["reminder_id"]), None)
        reminder = ReminderItem(
            id=payload["reminder_id"] or new_id("rem"),
            title=payload["title"],
            reminder_kind=payload["reminder_kind"],
            target_type=payload["target_type"],
            account_id=payload["account_id"],
            due_date=payload["due_date"] if payload["reminder_kind"] == "日期提醒" else "",
            threshold_amount=f"{parse_decimal(payload['threshold_amount'] or '0'):.2f}" if payload["reminder_kind"] == "阈值提醒" else "",
            current_value=f"{parse_decimal(payload['current_value'] or '0'):.2f}" if payload["reminder_kind"] == "阈值提醒" else "",
            status=payload["status"],
            source=payload["source"] or "手动录入",
            notes=payload["notes"],
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self.repository.upsert_reminder(reminder)
        self.refresh_data()

    def _delete_reminder(self, reminder_id: str) -> None:
        if self._confirm_delete("确定删除这条提醒吗？"):
            self.repository.delete_reminder(reminder_id)
            self.refresh_data()

    def _save_settings(self, payload: dict) -> None:
        settings = AppSettings(
            data_dir=payload["data_dir"] or str(Path(self.repository.db_path).parent),
            export_dir=payload["export_dir"] or str(Path(self.repository.db_path).parent / "exports"),
            backup_dir=payload["backup_dir"] or str(Path(self.repository.db_path).parent / "backups"),
            default_currency=payload["default_currency"] or "CNY",
            reminder_lead_days=int(payload["reminder_lead_days"]),
            obsidian_path=payload["obsidian_path"],
            minimax_api_host=payload["minimax_api_host"] or "https://api.minimaxi.com/v1",
            minimax_model=payload["minimax_model"] or "MiniMax-M2.7",
            minimax_key_configured=self.keychain.has_secret(),
        )
        self.repository.save_settings(settings)
        self.settings_page.set_status("设置已保存。数据目录修改将在下次启动后生效。")
        self.refresh_data()

    def _save_minimax_key(self, api_key: str) -> None:
        if not api_key:
            self._show_warning("MiniMax API Key 不能为空。")
            return
        self.keychain.save_secret(api_key)
        settings = self.repository.load_settings()
        settings.minimax_key_configured = True
        self.repository.save_settings(settings)
        self.settings_page.set_status("MiniMax Key 已保存到 macOS Keychain。")
        self.refresh_data()

    def _test_minimax_connection(self) -> None:
        api_key = self.keychain.load_secret()
        if not api_key:
            self._show_warning("请先保存 MiniMax API Key。")
            return
        settings = self.repository.load_settings()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            MiniMaxTextClient(api_key, settings.minimax_api_host, settings.minimax_model).test_connection()
            self.settings_page.set_status("MiniMax 连接测试通过。")
        except Exception as exc:
            self._show_warning(f"MiniMax 连接测试失败：{exc}")
        finally:
            QApplication.restoreOverrideCursor()

    def _choose_import_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择账单图片",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            self.imports_page.set_selected_image(path)

    def _paste_import_image(self) -> None:
        image = QApplication.clipboard().image()
        if image.isNull():
            self._show_warning("剪贴板里没有可用截图。")
            return
        imports_dir = self.repository.data_dir / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        path = imports_dir / f"clipboard-{now_timestamp().replace(':', '-')}.png"
        image.save(str(path), "PNG")
        self.imports_page.set_selected_image(str(path))

    def _recognize_selected_import_image(self) -> None:
        image_path = self.imports_page.selected_image_path
        if not image_path:
            self._show_warning("请先选择图片或粘贴截图。")
            return
        api_key = self.keychain.load_secret()
        if not api_key:
            self._show_warning("请先在设置页保存 MiniMax API Key。")
            self.nav.setCurrentRow(6)
            return
        settings = self.repository.load_settings()
        self.imports_page.set_status("正在调用 MiniMax OCR MCP 和 M2.7，请稍候...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            service = ImportRecognitionService(
                repository=self.repository,
                ocr_client=MiniMaxOcrMcpClient(api_key, settings.minimax_api_host),
                text_client=MiniMaxTextClient(api_key, settings.minimax_api_host, settings.minimax_model),
            )
            batch = service.recognize_image(image_path)
            self.refresh_data()
            self.imports_page.show_batch(batch)
            if batch.status == "failed":
                self._show_warning(f"识别失败：{batch.error_message}")
            else:
                self.imports_page.set_status("识别完成，请检查草稿后再确认入账。")
        finally:
            QApplication.restoreOverrideCursor()

    def _confirm_import_batch(self, batch_id: str) -> None:
        batch = self.repository.get_import_batch(batch_id)
        if batch is None:
            self._show_warning("导入批次不存在。")
            return
        if batch.status != "ready":
            self._show_warning("只有 ready 状态的批次可以确认入账。")
            return
        self.repository.confirm_import_batch(batch_id)
        self.refresh_data()
        self.imports_page.set_status("已生成待确认流水和提醒草稿。")

    def _export_json(self) -> None:
        path = self.repository.export_json()
        self.settings_page.set_status(f"已导出：{path}")

    def _backup_database(self) -> None:
        path = self.repository.backup_database()
        self.settings_page.set_status(f"已备份：{path}")

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "提示", message)

    def _confirm_delete(self, message: str) -> bool:
        result = QMessageBox.question(self, "确认删除", message)
        return result == QMessageBox.StandardButton.Yes

    def closeEvent(self, event) -> None:  # noqa: N802
        self.repository.close()
        super().closeEvent(event)
