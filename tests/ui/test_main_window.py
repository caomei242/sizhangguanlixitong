from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractButton, QComboBox, QFrame, QLabel, QSizePolicy, QTableWidget

from private_ledger.app import build_app
from private_ledger.domain.models import (
    Account,
    BalanceSnapshot,
    BudgetLine,
    MonthlyBudget,
    ReminderItem,
    Transaction,
)
from private_ledger.ui import main_window as main_window_module
from private_ledger.ui.pages.budgets_page import BudgetsPage


def _section_frames(widget, role: str) -> list[QFrame]:
    return [
        frame
        for frame in widget.findChildren(QFrame)
        if frame.property("sectionRole") == role
    ]


def _table_texts(table: QTableWidget) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in range(table.rowCount()):
        rows.append(
            [
                table.item(row, column).text() if table.item(row, column) is not None else ""
                for column in range(table.columnCount())
            ]
        )
    return rows


def _table_rows_by_name(table: QTableWidget) -> dict[str, list[str]]:
    return {row[0]: row for row in _table_texts(table) if row and row[0]}


def _table_rows_by_column(table: QTableWidget, key_column: int) -> dict[str, list[str]]:
    return {
        row[key_column]: row
        for row in _table_texts(table)
        if len(row) > key_column and row[key_column]
    }


def _assert_table_has_no_vertical_scroll(table: QTableWidget) -> None:
    assert table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert table.verticalScrollBar().maximum() == 0


def _annual_aux_panel(month_widgets: dict[str, object], kind: str) -> dict[str, object]:
    key_options = {
        "income": ("temp_income_panel", "temporary_income_panel", "other_income_panel"),
        "expense": ("temp_expense_panel", "temporary_expense_panel", "other_expense_panel"),
    }
    for key in key_options[kind]:
        panel = month_widgets.get(key)
        if isinstance(panel, dict):
            return panel
    raise AssertionError(f"Missing annual auxiliary {kind} panel in keys: {sorted(month_widgets)}")


def _status_cell_text(table: QTableWidget, row: int) -> str:
    status_column = table.columnCount() - 1
    texts: list[str] = []
    status_item = table.item(row, status_column)
    if status_item is not None and status_item.text():
        texts.append(status_item.text())
    cell_widget = table.cellWidget(row, status_column)
    if cell_widget is not None:
        if isinstance(cell_widget, QLabel) and cell_widget.text():
            texts.append(cell_widget.text())
        texts.extend(
            label.text()
            for label in cell_widget.findChildren(QLabel)
            if label.text()
        )
        texts.extend(
            button.text()
            for button in cell_widget.findChildren(QAbstractButton)
            if button.text()
        )
    return " ".join(dict.fromkeys(texts))


def _status_cell_buttons(table: QTableWidget, row: int) -> list[QAbstractButton]:
    status_column = table.columnCount() - 1
    cell_widget = table.cellWidget(row, status_column)
    if cell_widget is None:
        return []
    assert not isinstance(cell_widget, QComboBox)
    assert not cell_widget.findChildren(QComboBox)
    buttons: list[QAbstractButton] = []
    if isinstance(cell_widget, QAbstractButton):
        buttons.append(cell_widget)
    buttons.extend(cell_widget.findChildren(QAbstractButton))
    return buttons


def _row_has_enabled_confirm_action(table: QTableWidget, row: int) -> bool:
    return any(button.isEnabled() for button in _status_cell_buttons(table, row))


def _click_confirm_action_for_row(table: QTableWidget, row_key: str, *, key_column: int = 0) -> bool:
    rows = _table_rows_by_column(table, key_column)
    row_values = rows.get(row_key)
    if row_values is None:
        return False
    for row in range(table.rowCount()):
        key_item = table.item(row, key_column)
        if key_item is None or key_item.text() != row_key:
            continue
        for button in _status_cell_buttons(table, row):
            if button.isEnabled():
                button.click()
                return True
    return False


def _assert_compact_status_column(
    table: QTableWidget,
    *,
    pending_names: set[str],
    key_column: int = 0,
) -> None:
    assert 88 <= table.columnWidth(0) <= 132
    assert 88 <= table.columnWidth(1) <= 132
    status_column = table.columnCount() - 1
    assert 110 <= table.columnWidth(status_column) <= 150
    for row in range(table.rowCount()):
        key_item = table.item(row, key_column)
        assert key_item is not None
        key_name = key_item.text()
        status_text = _status_cell_text(table, row)
        has_confirm_action = _row_has_enabled_confirm_action(table, row)
        if key_name in pending_names:
            assert "待确认" in status_text
            assert has_confirm_action
        else:
            assert not has_confirm_action


def _click_pending_confirm_action(table: QTableWidget) -> bool:
    for row in range(table.rowCount()):
        if "待确认" not in _status_cell_text(table, row):
            continue
        for button in _status_cell_buttons(table, row):
            if button.isEnabled():
                button.click()
                return True
    return False


def test_annual_month_status_keeps_pending_rows_actionable(qapp) -> None:
    page = BudgetsPage()

    assert page._annual_month_item_status("收入", Decimal("100.00"), Decimal("120.00"), Decimal("10.00"), "") == "待确认"
    assert page._annual_month_item_status("支出", Decimal("100.00"), Decimal("80.00"), Decimal("5.00"), "") == "待确认"
    assert page._is_actionable_pending_row({"pending": Decimal("1.00"), "status": "已达成"})


def test_main_window_shows_navigation_and_loaded_dashboard_data(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository

    repo.upsert_account(
        Account(
            id="acc-main",
            name="招商银行卡",
            account_type="银行卡",
            currency="CNY",
            purpose="生活主账户",
            status="正常",
            notes="",
            source="手动录入",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.add_snapshot(
        BalanceSnapshot(
            id="snap-main",
            account_id="acc-main",
            snapshot_time="2026-04-18T18:00:00",
            amount="12860.00",
            status="已确认",
            source="手动对账",
            notes="",
            created_at="2026-04-18T18:00:00",
        )
    )
    repo.upsert_transaction(
        Transaction(
            id="txn-expense",
            occurred_on="2026-04-18",
            transaction_type="支出",
            category="餐饮",
            amount="86.50",
            from_account_id="acc-main",
            to_account_id="",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-18T19:00:00",
            updated_at="2026-04-18T19:00:00",
        )
    )
    repo.upsert_budget(
        MonthlyBudget(
            id="budget-2026-04",
            month_key="2026-04",
            total_budget="8000.00",
            notes="",
            status="生效中",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.upsert_reminder(
        ReminderItem(
            id="rem-api",
            title="API 余额充值",
            reminder_kind="日期提醒",
            target_type="充值",
            account_id="",
            due_date="2026-04-21",
            threshold_amount="",
            current_value="",
            status="启用",
            source="手动录入",
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )

    window.refresh_data(reference_month="2026-04")

    assert window.windowTitle() == "草莓私帐管理系统"
    assert not _app.windowIcon().isNull()
    assert window.nav.verticalScrollBar().maximum() == 0
    assert window.nav.count() == 7
    assert window.nav.item(0).text() == "月度看板"
    assert window.nav.item(5).text() == "数据导入"
    assert [window.dashboard_page.tabs.tabText(index) for index in range(window.dashboard_page.tabs.count())] == [
        "总览",
        "账户余额",
        "近期待处理",
        "最近流水",
    ]
    assert "8,000.00" in window.dashboard_page.total_budget_card.value_label.text()
    assert window.dashboard_page.overview_accounts_table.rowCount() == 1
    assert window.dashboard_page.overview_reminders_list.count() == 1
    assert window.dashboard_page.accounts_table.rowCount() == 1
    assert window.dashboard_page.reminders_table.rowCount() == 1

    window.close()


def test_dashboard_period_controls_show_year_summary(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    for transaction in [
        Transaction(
            id="income-jan",
            occurred_on="2026-01-05",
            transaction_type="收入",
            category="工资",
            amount="1000.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-01-05T10:00:00",
            updated_at="2026-01-05T10:00:00",
        ),
        Transaction(
            id="expense-feb",
            occurred_on="2026-02-05",
            transaction_type="支出",
            category="日常零花",
            amount="600.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-02-05T10:00:00",
            updated_at="2026-02-05T10:00:00",
        ),
        Transaction(
            id="pending-mar",
            occurred_on="2026-03-05",
            transaction_type="支出",
            category="待确认",
            amount="200.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-03-05T10:00:00",
            updated_at="2026-03-05T10:00:00",
        ),
    ]:
        repo.upsert_transaction(transaction)

    window.period_granularity_combo.setCurrentText("年")
    window.period_value_combo.setCurrentText("2026")

    assert window.dashboard_page.income_card.value_label.text() == "¥1,000.00"
    assert window.dashboard_page.expense_card.value_label.text() == "¥600.00"
    assert window.dashboard_page.balance_card.value_label.text() == "¥400.00"
    assert window.dashboard_page.pending_amount_card.value_label.text() == "¥200.00"
    assert window.dashboard_page.trend_chart.series_count_for_test() == 3
    assert window.dashboard_page.trend_table.rowCount() == 12
    assert window.dashboard_page.trend_chart.minimumHeight() >= 340
    assert window.dashboard_page.trend_table.isHidden()

    window.close()


def test_budget_page_shows_comparison_and_generates_draft_lines(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    for transaction in [
        Transaction(
            id="income-wage",
            occurred_on="2026-04-05",
            transaction_type="收入",
            category="工资",
            amount="1200.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="工资备注",
            related_transaction_id="",
            created_at="2026-04-05T10:00:00",
            updated_at="2026-04-05T10:00:00",
        ),
        Transaction(
            id="expense-food",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="餐饮",
            amount="300.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="午餐备注",
            related_transaction_id="",
            created_at="2026-04-06T10:00:00",
            updated_at="2026-04-06T10:00:00",
        ),
        Transaction(
            id="pending-food",
            occurred_on="2026-04-07",
            transaction_type="支出",
            category="餐饮",
            amount="80.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-07T10:00:00",
            updated_at="2026-04-07T10:00:00",
        ),
    ]:
        repo.upsert_transaction(transaction)

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(3)
    page = window.budgets_page

    assert window.period_granularity_combo.isHidden()
    assert page.month_edit.parent() is not None
    assert not page.month_edit.isHidden()
    tab_texts = [page.tabs.tabText(index) for index in range(page.tabs.count())]
    assert len(tab_texts) == 5
    assert any("工作台" in text for text in tab_texts)
    assert any("全年" in text for text in tab_texts)
    assert any("收入" in text for text in tab_texts)
    assert any("支出" in text for text in tab_texts)
    assert any("生效" in text for text in tab_texts)
    assert "工作台" in page.tabs.tabText(page.tabs.currentIndex())
    assert page.workbench_splitter.orientation() == Qt.Orientation.Horizontal
    assert page.workbench_splitter.count() == 2
    assert _section_frames(page, "budget-workbench")
    assert _section_frames(page, "budget-workbench-primary")
    assert len(_section_frames(page, "budget-ledger")) >= 2
    assert _section_frames(page, "budget-workbench-editor")
    assert _section_frames(page, "annual-summary")
    assert _section_frames(page, "annual-accordion")
    assert _section_frames(page, "scope-reference")
    assert page.comparison_table.horizontalHeaderItem(0).text() == "预算项"
    assert page.comparison_table.rowCount() >= 3
    assert page.effective_scope_table.rowCount() == 3
    assert not page.effective_scope_table.isVisible()
    assert page.effective_scope_table.item(0, 0).text() == "仅当前月"
    assert len(page.effective_scope_rows) == 3
    assert page.income_table.rowCount() >= 2
    assert page.expense_table.rowCount() >= 2
    assert page.income_table.horizontalHeaderItem(2).text() == "标签"
    assert page.income_table.horizontalHeaderItem(3).text() == "备注"
    assert page.income_table.horizontalHeaderItem(4).text() == "生效月份"
    assert page.tag_filter_combo.findText("工资") >= 0
    assert page.tag_filter_combo.findText("餐饮") >= 0
    assert page.seed_from_actual_button.isEnabled()
    assert "¥1,200.00" in page.planned_income_card.note_label.text()
    assert "¥80.00" in page.pending_card.value_label.text()

    page.tag_filter_combo.setCurrentText("工资")
    assert page.income_table.rowCount() >= 2
    assert page.expense_table.item(0, 0).text() == "当前月份还没有预计支出项。"
    page.tag_filter_combo.setCurrentText("全部标签")

    page.seed_from_actual_button.click()
    qapp.processEvents()

    budget = repo.get_monthly_budget("2026-04")
    assert budget is not None
    lines = repo.list_budget_lines(budget.id)
    assert {(line.line_kind, line.category, line.planned_amount) for line in lines} == {
        ("收入", "工资", "1200.00"),
        ("分类预算", "餐饮", "300.00"),
    }
    assert all("草稿待调整" in line.notes for line in lines)
    assert {(line.effective_start_month, line.effective_end_month) for line in lines} == {("2026-04", "2026-04")}
    assert budget.total_budget == "300.00"
    statuses = set()
    for table in (page.income_table, page.expense_table):
        statuses.update(
            table.item(row, 10).text()
            for row in range(table.rowCount())
            if table.item(row, 10) is not None
        )
    assert "草稿待调整" in statuses

    window.close()


def test_dashboard_and_budget_page_use_effective_budget_lines_across_months(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    repo.upsert_budget(
        MonthlyBudget(
            id="budget-2026-04",
            month_key="2026-04",
            total_budget="0.00",
            notes="",
            status="生效中",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="line-rent",
            budget_id="budget-2026-04",
            line_kind="固定支出",
            name="房租",
            category="房租",
            planned_amount="2500.00",
            day_of_month=None,
            is_required=True,
            reminder_days=3,
            notes="每月固定",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
            effective_start_month="2026-04",
            effective_end_month="",
        )
    )

    window.refresh_data(reference_month="2026-05")

    assert "2,500.00" in window.dashboard_page.total_budget_card.value_label.text()
    assert "2,500.00" in window.budgets_page.planned_expense_card.value_label.text()
    assert any(
        window.budgets_page.expense_table.item(row, 0)
        and window.budgets_page.expense_table.item(row, 0).text() == "房租"
        for row in range(window.budgets_page.expense_table.rowCount())
    )

    window.close()


def test_budget_page_saves_effective_mode_from_editor(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(3)
    page = window.budgets_page

    page.kind_combo.setCurrentText("固定支出")
    page.name_edit.setText("房租")
    page.category_edit.setText("房租")
    page.planned_amount_edit.setText("2500")
    page.effective_mode_combo.setCurrentText("从当前月起")
    page.save_line_button.click()
    qapp.processEvents()

    lines = window.repository.list_effective_budget_lines("2026-05")
    assert len(lines) == 1
    assert lines[0].name == "房租"
    assert lines[0].effective_start_month == "2026-04"
    assert lines[0].effective_end_month == ""

    window.close()


def test_budget_page_shows_readonly_annual_matrix_without_breaking_monthly_editor(tmp_path, qapp, monkeypatch) -> None:
    annual_calls = []

    def fake_build_annual_budget_matrix(year: int, budget_lines: list[BudgetLine], transactions: list[Transaction]):
        def transaction_total(month_key: str, transaction_type: str, category: str, status: str) -> Decimal:
            total = Decimal("0.00")
            for transaction in transactions:
                if not transaction.occurred_on.startswith(month_key):
                    continue
                if transaction.transaction_type != transaction_type:
                    continue
                if transaction.category != category:
                    continue
                if transaction.status != status:
                    continue
                total += Decimal(transaction.amount)
            return total

        def pending_total_for_year() -> Decimal:
            total = Decimal("0.00")
            for transaction in transactions:
                if not transaction.occurred_on.startswith(f"{year:04d}-"):
                    continue
                if transaction.status == "已确认":
                    continue
                total += Decimal(transaction.amount)
            return total

        april_pending_amount = sum(
            (
                transaction_total("2026-04", "收入", "房租补贴（当月）", "待确认"),
                transaction_total("2026-04", "支出", "话费", "待确认"),
                transaction_total("2026-04", "支出", "交通", "待确认"),
            ),
            Decimal("0.00"),
        )
        annual_calls.append(
            {
                "year": year,
                "line_ids": {line.id for line in budget_lines},
                "transaction_ids": {transaction.id for transaction in transactions},
            }
        )
        months = []
        for month in range(1, 13):
            if month == 4:
                planned_income = Decimal("3300.00")
                actual_income = Decimal("1800.00")
                planned_expense = Decimal("920.00")
                actual_expense = Decimal("840.00")
                planned_balance = Decimal("2380.00")
                actual_balance = Decimal("960.00")
                pending_amount = april_pending_amount
            elif month == 5:
                planned_income = Decimal("1300.00")
                actual_income = Decimal("0.00")
                planned_expense = Decimal("920.00")
                actual_expense = Decimal("0.00")
                planned_balance = Decimal("380.00")
                actual_balance = Decimal("0.00")
                pending_amount = Decimal("0.00")
            else:
                planned_income = Decimal("0.00")
                actual_income = Decimal("0.00")
                planned_expense = Decimal("0.00")
                actual_expense = Decimal("0.00")
                planned_balance = Decimal("0.00")
                actual_balance = Decimal("0.00")
                pending_amount = Decimal("0.00")
            months.append(
                SimpleNamespace(
                    month_key=f"{year}-{month:02d}",
                    planned_income=planned_income,
                    actual_income=actual_income,
                    planned_expense=planned_expense,
                    actual_expense=actual_expense,
                    planned_balance=planned_balance,
                    actual_balance=actual_balance,
                    pending_amount=pending_amount,
                )
            )
        return SimpleNamespace(
            year=year,
            months=months,
            detail_rows=[
                SimpleNamespace(
                    group_name="收入计划",
                    line_kind="收入",
                    name="工资",
                    category="工资",
                    effective_start_month="2026-01",
                    effective_end_month="",
                    planned_months={
                        "2026-04": Decimal("1000.00"),
                        "04": Decimal("1000.00"),
                        "2026-05": Decimal("1000.00"),
                        "05": Decimal("1000.00"),
                    },
                    actual_months={"2026-04": transaction_total("2026-04", "收入", "工资", "已确认"), "04": transaction_total("2026-04", "收入", "工资", "已确认")},
                    pending_months={},
                    planned_total=Decimal("2000.00"),
                    actual_total=transaction_total("2026-04", "收入", "工资", "已确认"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("-700.00"),
                    status="进行中",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="收入计划",
                    line_kind="收入",
                    name="网店收入",
                    category="网店收入",
                    effective_start_month="2026-04",
                    effective_end_month="2026-05",
                    planned_months={
                        "2026-04": Decimal("300.00"),
                        "04": Decimal("300.00"),
                        "2026-05": Decimal("300.00"),
                        "05": Decimal("300.00"),
                    },
                    actual_months={"2026-04": transaction_total("2026-04", "收入", "网店收入", "已确认"), "04": transaction_total("2026-04", "收入", "网店收入", "已确认")},
                    pending_months={},
                    planned_total=Decimal("600.00"),
                    actual_total=transaction_total("2026-04", "收入", "网店收入", "已确认"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("-340.00"),
                    status="进行中",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="收入计划",
                    line_kind="收入",
                    name="兼职奖金",
                    category="奖金",
                    effective_start_month="2026-04",
                    effective_end_month="2026-04",
                    planned_months={"2026-04": Decimal("200.00"), "04": Decimal("200.00")},
                    actual_months={"2026-04": transaction_total("2026-04", "收入", "奖金", "已确认"), "04": transaction_total("2026-04", "收入", "奖金", "已确认")},
                    pending_months={},
                    planned_total=Decimal("200.00"),
                    actual_total=transaction_total("2026-04", "收入", "奖金", "已确认"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("40.00"),
                    status="未设预算",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="收入计划",
                    line_kind="收入",
                    name="房租补贴（当月）",
                    category="房租补贴（当月）",
                    effective_start_month="2026-04",
                    effective_end_month="2026-04",
                    planned_months={"2026-04": Decimal("1800.00"), "04": Decimal("1800.00")},
                    actual_months={},
                    pending_months={"2026-04": transaction_total("2026-04", "收入", "房租补贴（当月）", "待确认"), "04": transaction_total("2026-04", "收入", "房租补贴（当月）", "待确认")},
                    planned_total=Decimal("1800.00"),
                    actual_total=Decimal("0.00"),
                    pending_total=transaction_total("2026-04", "收入", "房租补贴（当月）", "待确认"),
                    delta_total=Decimal("-1800.00"),
                    status="待确认",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="支出预算",
                    line_kind="分类预算",
                    name="日常餐饮",
                    category="餐饮",
                    effective_start_month="2026-01",
                    effective_end_month="",
                    planned_months={
                        "2026-04": Decimal("500.00"),
                        "04": Decimal("500.00"),
                        "2026-05": Decimal("500.00"),
                        "05": Decimal("500.00"),
                    },
                    actual_months={"2026-04": transaction_total("2026-04", "支出", "餐饮", "已确认"), "04": transaction_total("2026-04", "支出", "餐饮", "已确认")},
                    pending_months={},
                    planned_total=Decimal("1000.00"),
                    actual_total=transaction_total("2026-04", "支出", "餐饮", "已确认"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("320.00"),
                    status="超支",
                ),
                SimpleNamespace(
                    group_name="支出预算",
                    line_kind="分类预算",
                    name="其他杂费",
                    category="其他支出",
                    effective_start_month="2026-04",
                    effective_end_month="2026-05",
                    planned_months={
                        "2026-04": Decimal("120.00"),
                        "04": Decimal("120.00"),
                        "2026-05": Decimal("120.00"),
                        "05": Decimal("120.00"),
                    },
                    actual_months={"2026-04": transaction_total("2026-04", "支出", "其他支出", "已确认"), "04": transaction_total("2026-04", "支出", "其他支出", "已确认")},
                    pending_months={},
                    planned_total=Decimal("240.00"),
                    actual_total=transaction_total("2026-04", "支出", "其他支出", "已确认"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("140.00"),
                    status="进行中",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="支出预算",
                    line_kind="分类预算",
                    name="话费充值",
                    category="话费",
                    effective_start_month="2026-04",
                    effective_end_month="2026-04",
                    planned_months={"2026-04": Decimal("300.00"), "04": Decimal("300.00")},
                    actual_months={},
                    pending_months={"2026-04": transaction_total("2026-04", "支出", "话费", "待确认"), "04": transaction_total("2026-04", "支出", "话费", "待确认")},
                    planned_total=Decimal("300.00"),
                    actual_total=Decimal("0.00"),
                    pending_total=transaction_total("2026-04", "支出", "话费", "待确认"),
                    delta_total=Decimal("300.00"),
                    status="待确认",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="未设预算",
                    line_kind="分类预算",
                    name="临时交通",
                    category="交通",
                    effective_start_month="2026-04",
                    effective_end_month="2026-04",
                    planned_months={},
                    actual_months={"2026-04": transaction_total("2026-04", "支出", "交通", "已确认"), "04": transaction_total("2026-04", "支出", "交通", "已确认")},
                    pending_months={"2026-04": transaction_total("2026-04", "支出", "交通", "待确认"), "04": transaction_total("2026-04", "支出", "交通", "待确认")},
                    planned_total=Decimal("0.00"),
                    actual_total=transaction_total("2026-04", "支出", "交通", "已确认"),
                    pending_total=transaction_total("2026-04", "支出", "交通", "待确认"),
                    delta_total=Decimal("-60.00"),
                    status="未设预算",
                    notes="",
                ),
                SimpleNamespace(
                    group_name="固定支出",
                    line_kind="固定支出",
                    name="年末支出",
                    category="年末支出",
                    effective_start_month="2026-12",
                    effective_end_month="2026-12",
                    planned_months={"2026-12": Decimal("1000.00"), "12": Decimal("1000.00")},
                    actual_months={"2026-12": Decimal("300.00"), "12": Decimal("300.00")},
                    pending_months={},
                    planned_total=Decimal("1000.00"),
                    actual_total=Decimal("300.00"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("700.00"),
                    status="进行中",
                    notes="",
                ),
            ],
            planned_income=Decimal("12000.00"),
            actual_income=Decimal("1800.00"),
            planned_expense=Decimal("6500.00"),
            actual_expense=Decimal("1140.00"),
            planned_balance=Decimal("5500.00"),
            actual_balance=Decimal("660.00"),
            pending_amount=pending_total_for_year(),
        )

    monkeypatch.setattr(main_window_module, "build_annual_budget_matrix", fake_build_annual_budget_matrix, raising=False)

    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    for budget in [
        MonthlyBudget(
            id="budget-2026-04",
            month_key="2026-04",
            total_budget="0.00",
            notes="",
            status="生效中",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        ),
        MonthlyBudget(
            id="budget-2026-12",
            month_key="2026-12",
            total_budget="0.00",
            notes="",
            status="生效中",
            created_at="2026-12-01T09:00:00",
            updated_at="2026-12-01T09:00:00",
        ),
    ]:
        repo.upsert_budget(budget)
    for line in [
        BudgetLine(
            id="line-income-year",
            budget_id="budget-2026-04",
            line_kind="收入",
            name="工资",
            category="工资",
            planned_amount="1000.00",
            day_of_month=None,
            is_required=True,
            reminder_days=0,
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
            effective_start_month="2026-01",
            effective_end_month="",
        ),
        BudgetLine(
            id="line-december-only",
            budget_id="budget-2026-12",
            line_kind="固定支出",
            name="年末支出",
            category="年末支出",
            planned_amount="500.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="",
            created_at="2026-12-01T09:00:00",
            updated_at="2026-12-01T09:00:00",
            effective_start_month="2026-12",
            effective_end_month="2026-12",
        ),
    ]:
        repo.upsert_budget_line(line)
    for transaction in [
        Transaction(
            id="txn-apr-income",
            occurred_on="2026-04-05",
            transaction_type="收入",
            category="工资",
            amount="1300.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-05T10:00:00",
            updated_at="2026-04-05T10:00:00",
        ),
        Transaction(
            id="txn-apr-store",
            occurred_on="2026-04-05",
            transaction_type="收入",
            category="网店收入",
            amount="260.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-05T10:30:00",
            updated_at="2026-04-05T10:30:00",
        ),
        Transaction(
            id="txn-apr-bonus",
            occurred_on="2026-04-05",
            transaction_type="收入",
            category="奖金",
            amount="240.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-05T11:00:00",
            updated_at="2026-04-05T11:00:00",
        ),
        Transaction(
            id="txn-apr-rent-subsidy",
            occurred_on="2026-04-06",
            transaction_type="收入",
            category="房租补贴（当月）",
            amount="1800.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T09:00:00",
            updated_at="2026-04-06T09:00:00",
        ),
        Transaction(
            id="txn-apr-food",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="餐饮",
            amount="680.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T10:00:00",
            updated_at="2026-04-06T10:00:00",
        ),
        Transaction(
            id="txn-apr-misc",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="其他支出",
            amount="100.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T10:30:00",
            updated_at="2026-04-06T10:30:00",
        ),
        Transaction(
            id="txn-apr-phone-pending",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="话费",
            amount="300.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T11:00:00",
            updated_at="2026-04-06T11:00:00",
        ),
        Transaction(
            id="txn-apr-traffic-confirmed",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="交通",
            amount="60.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T11:30:00",
            updated_at="2026-04-06T11:30:00",
        ),
        Transaction(
            id="txn-apr-traffic-pending",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="交通",
            amount="20.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T12:00:00",
            updated_at="2026-04-06T12:00:00",
        ),
    ]:
        repo.upsert_transaction(transaction)

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(3)
    page = window.budgets_page

    assert page.tabs.tabText(page.tabs.currentIndex()) == "预算工作台"
    assert {"line-income-year", "line-december-only"} <= annual_calls[-1]["line_ids"]
    assert {
        "txn-apr-income",
        "txn-apr-store",
        "txn-apr-bonus",
        "txn-apr-rent-subsidy",
        "txn-apr-food",
        "txn-apr-misc",
        "txn-apr-phone-pending",
        "txn-apr-traffic-confirmed",
        "txn-apr-traffic-pending",
    } <= annual_calls[-1]["transaction_ids"]

    annual_index = page.tabs.indexOf(page.annual_tab)
    page.tabs.setCurrentIndex(annual_index)
    qapp.processEvents()

    assert page.tabs.tabText(page.tabs.currentIndex()) == "全年十二月"
    assert page.annual_overview_badge.text() == "2026 年预算板"
    assert "展开该月查看详细项目" in page.annual_overview_summary.text()
    assert page.annual_actual_summary_label.text() == "2026 年实际回看"
    assert page.annual_planned_income_card.value_label.text() == "¥12,000.00"
    assert page.annual_pending_card.value_label.text() == "¥2,120.00"
    assert len(page.annual_quarter_sections) == 4
    assert len(page.annual_month_cards) == 12
    assert len(_section_frames(page.annual_tab, "annual-quarter-group")) == 4
    assert len(_section_frames(page.annual_tab, "annual-month-row")) == 12
    assert page._expanded_annual_month == 4
    april_widgets = page.annual_month_cards[4]
    march_widgets = page.annual_month_cards[3]
    may_widgets = page.annual_month_cards[5]
    assert april_widgets["month_label"].text() == "4月"
    assert "收入 3 项 · 支出 3 项 · 其他 2 项" in april_widgets["month_note"].text()
    assert not april_widgets["detail_panel"].isHidden()
    assert april_widgets["toggle_button"].isChecked()
    assert march_widgets["detail_panel"].isHidden()
    assert may_widgets["detail_panel"].isHidden()
    assert april_widgets["status_tag"].text() == "待确认"
    income_panel = april_widgets["income_panel"]
    expense_panel = april_widgets["expense_panel"]
    temp_income_panel = _annual_aux_panel(april_widgets, "income")
    temp_expense_panel = _annual_aux_panel(april_widgets, "expense")
    assert income_panel["frame"].sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum
    assert expense_panel["frame"].sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum
    assert income_panel["planned_label"].text() == "计划 ¥3,100.00"
    assert income_panel["actual_label"].text() == "实际 ¥1,560.00"
    assert income_panel["pending_label"].text() == "待确认 ¥1,800.00"
    assert income_panel["confirm_all_button"].text() == "确认本区待确认"
    assert income_panel["confirm_all_button"].isEnabled()
    assert expense_panel["planned_label"].text() == "计划 ¥920.00"
    assert expense_panel["actual_label"].text() == "实际 ¥780.00"
    assert expense_panel["pending_label"].text() == "待确认 ¥300.00"
    assert expense_panel["confirm_all_button"].text() == "确认本区待确认"
    assert expense_panel["confirm_all_button"].isEnabled()
    assert "临时" in temp_income_panel["title"].text()
    assert "收入" in temp_income_panel["title"].text()
    assert temp_income_panel["summary"].text() == "1 项 · 计划 ¥200.00 · 实际 ¥240.00 · 待确认 ¥0.00"
    assert not temp_income_panel["toggle"].isChecked()
    assert temp_income_panel["table"].isHidden()
    assert "临时" in temp_expense_panel["title"].text()
    assert "支出" in temp_expense_panel["title"].text()
    assert temp_expense_panel["summary"].text() == "1 项 · 计划 ¥0.00 · 实际 ¥60.00 · 待确认 ¥20.00"
    assert not temp_expense_panel["toggle"].isChecked()
    assert temp_expense_panel["table"].isHidden()
    income_rows = _table_rows_by_name(income_panel["table"])
    expense_rows = _table_rows_by_name(expense_panel["table"])
    temp_income_rows = _table_rows_by_name(temp_income_panel["table"])
    temp_expense_rows = _table_rows_by_name(temp_expense_panel["table"])
    assert set(income_rows) == {"工资", "房租补贴（当月）", "网店收入"}
    assert income_rows["工资"] == ["工资", "工资", "¥1,000.00", "¥1,300.00", "¥0.00", "+¥300.00", "已达成"]
    assert income_rows["网店收入"] == ["网店收入", "网店收入", "¥300.00", "¥260.00", "¥0.00", "¥-40.00", "进行中"]
    assert income_rows["房租补贴（当月）"] == ["房租补贴（当月）", "房租补贴（当月）", "¥1,800.00", "¥0.00", "¥1,800.00", "¥-1,800.00", "待确认"]
    assert set(expense_rows) == {"其他杂费", "日常餐饮", "话费充值"}
    assert expense_rows["日常餐饮"] == ["日常餐饮", "餐饮", "¥500.00", "¥680.00", "¥0.00", "¥-180.00", "超支"]
    assert expense_rows["其他杂费"] == ["其他杂费", "其他支出", "¥120.00", "¥100.00", "¥0.00", "+¥20.00", "已达成"]
    assert expense_rows["话费充值"] == ["话费充值", "话费", "¥300.00", "¥0.00", "¥300.00", "+¥300.00", "待确认"]
    assert set(temp_income_rows) == {"兼职奖金"}
    assert temp_income_rows["兼职奖金"] == ["兼职奖金", "奖金", "¥200.00", "¥240.00", "¥0.00", "+¥40.00", "已达成"]
    assert set(temp_expense_rows) == {"临时交通"}
    assert temp_expense_rows["临时交通"] == ["临时交通", "交通", "¥0.00", "¥60.00", "¥20.00", "¥-60.00", "待确认"]
    assert {"工资", "房租补贴（当月）", "网店收入"}.isdisjoint(temp_income_rows)
    assert {"其他杂费", "日常餐饮", "话费充值"}.isdisjoint(temp_expense_rows)
    for table in (
        income_panel["table"],
        expense_panel["table"],
        temp_income_panel["table"],
        temp_expense_panel["table"],
    ):
        _assert_table_has_no_vertical_scroll(table)

    _assert_compact_status_column(income_panel["table"], pending_names={"房租补贴（当月）"})
    _assert_compact_status_column(expense_panel["table"], pending_names={"话费充值"})
    _assert_compact_status_column(temp_income_panel["table"], pending_names=set())
    _assert_compact_status_column(temp_expense_panel["table"], pending_names={"临时交通"})

    expense_panel["confirm_all_button"].click()
    qapp.processEvents()
    assert next(txn for txn in repo.list_transactions() if txn.id == "txn-apr-phone-pending").status == "已确认"

    april_widgets = page.annual_month_cards[4]
    income_panel = april_widgets["income_panel"]
    expense_panel = april_widgets["expense_panel"]
    temp_income_panel = _annual_aux_panel(april_widgets, "income")
    temp_expense_panel = _annual_aux_panel(april_widgets, "expense")

    temp_income_panel["toggle"].click()
    temp_expense_panel["toggle"].click()
    qapp.processEvents()
    assert temp_income_panel["toggle"].isChecked()
    assert not temp_income_panel["table"].isHidden()
    assert temp_expense_panel["toggle"].isChecked()
    assert not temp_expense_panel["table"].isHidden()
    _assert_table_has_no_vertical_scroll(temp_income_panel["table"])
    _assert_table_has_no_vertical_scroll(temp_expense_panel["table"])
    assert _click_confirm_action_for_row(temp_expense_panel["table"], "临时交通")
    qapp.processEvents()
    assert next(txn for txn in repo.list_transactions() if txn.id == "txn-apr-traffic-pending").status == "已确认"

    if any(
        _click_pending_confirm_action(table)
        for table in (
            income_panel["table"],
            expense_panel["table"],
            temp_income_panel["table"],
            temp_expense_panel["table"],
        )
    ):
        qapp.processEvents()
        assert next(txn for txn in repo.list_transactions() if txn.id == "txn-apr-rent-subsidy").status == "已确认"

    temp_income_panel["toggle"].click()
    temp_expense_panel["toggle"].click()
    qapp.processEvents()
    assert not temp_income_panel["toggle"].isChecked()
    assert temp_income_panel["table"].isHidden()
    assert not temp_expense_panel["toggle"].isChecked()
    assert temp_expense_panel["table"].isHidden()

    may_widgets["toggle_button"].click()
    qapp.processEvents()
    assert april_widgets["detail_panel"].isHidden()
    assert not may_widgets["detail_panel"].isHidden()

    assert page.name_edit.text() == ""

    page.tabs.setCurrentIndex(0)
    page.kind_combo.setCurrentText("标签预算")
    page.name_edit.setText("咖啡")
    page.category_edit.setText("餐饮")
    page.planned_amount_edit.setText("120")
    page.save_line_button.click()
    qapp.processEvents()

    assert any(
        line.name == "咖啡"
        for line in repo.list_effective_budget_lines("2026-04")
    )

    window.close()


def test_transactions_page_filters_by_tag_and_shows_notes(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    for transaction in [
        Transaction(
            id="txn-food",
            occurred_on="2026-04-08",
            transaction_type="支出",
            category="餐饮",
            amount="45.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="午餐备注",
            related_transaction_id="",
            created_at="2026-04-08T12:00:00",
            updated_at="2026-04-08T12:00:00",
        ),
        Transaction(
            id="txn-traffic",
            occurred_on="2026-04-09",
            transaction_type="支出",
            category="交通",
            amount="12.00",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="打车备注",
            related_transaction_id="",
            created_at="2026-04-09T12:00:00",
            updated_at="2026-04-09T12:00:00",
        ),
    ]:
        repo.upsert_transaction(transaction)

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(2)
    page = window.transactions_page

    assert page.table.horizontalHeaderItem(2).text() == "标签"
    assert page.table.horizontalHeaderItem(3).text() == "备注"
    assert page.tag_filter_combo.findText("餐饮") >= 0
    assert page.tag_filter_combo.findText("交通") >= 0

    page.tag_filter_combo.setCurrentText("餐饮")
    assert page.table.rowCount() == 1
    assert page.table.item(0, 2).text() == "餐饮"
    assert page.table.item(0, 3).text() == "午餐备注"

    page.clear_filter_button.click()
    qapp.processEvents()
    assert page.table.rowCount() == 2

    window.close()


def test_reminders_page_shows_expected_names_and_traffic_lights(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository

    for reminder in [
        ReminderItem(
            id="rem-budget-amber",
            title="2026-04 日常零花 预算临界提醒",
            reminder_kind="阈值提醒",
            target_type="预算进度",
            account_id="",
            due_date="",
            threshold_amount="100.00",
            current_value="80.00",
            status="停用",
            source="测试",
            notes="预算项：日常零花\n进度：80.00%",
            created_at="2026-04-24T10:00:00",
            updated_at="2026-04-24T10:00:00",
        ),
        ReminderItem(
            id="rem-budget-red",
            title="2026-04 房租 预算超支提醒",
            reminder_kind="阈值提醒",
            target_type="预算进度",
            account_id="",
            due_date="",
            threshold_amount="100.00",
            current_value="120.00",
            status="启用",
            source="测试",
            notes="预算项：房租\n进度：120.00%",
            created_at="2026-04-24T10:00:00",
            updated_at="2026-04-24T10:00:00",
        ),
        ReminderItem(
            id="rem-minimax",
            title="MiniMax Max-极速版月度套餐续费",
            reminder_kind="日期提醒",
            target_type="会员续费",
            account_id="",
            due_date="2026-05-03",
            threshold_amount="",
            current_value="",
            status="启用",
            source="测试",
            notes="",
            created_at="2026-04-24T10:00:00",
            updated_at="2026-04-24T10:00:00",
        ),
    ]:
        repo.upsert_reminder(reminder)

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(4)
    page = window.reminders_page

    assert [page.tabs.tabText(index) for index in range(page.tabs.count())] == [
        "提醒中心",
        "红黄绿视图",
        "订阅服务",
        "备注与来源",
    ]
    assert page.list_widget.count() == 3
    assert set(page.filter_buttons) == {"全部", "红灯", "黄灯", "绿灯", "启用"}
    assert page.total_card.value_label.text() == "3 项"
    assert page.list_meta_label.text().startswith("3 条提醒")
    assert "全部" in page.list_meta_label.text()
    assert _section_frames(page, "reminder-list") or _section_frames(page, "stacked-list")
    assert _section_frames(page, "reminder-detail")

    lights_by_name = {
        row_widget.title_label.text(): row_widget.light_label.text()
        for row_widget in page._row_widgets.values()
    }
    assert lights_by_name["日常零花"] == "黄灯"
    assert lights_by_name["房租"] == "红灯"
    assert "2026-04 日常零花 预算临界提醒" not in lights_by_name

    budget_row = next(
        row
        for row in range(page.list_widget.count())
        if page._row_widgets[page.list_widget.item(row).data(Qt.ItemDataRole.UserRole)].title_label.text() == "日常零花"
    )
    page.list_widget.setCurrentRow(budget_row)
    qapp.processEvents()

    assert page.detail_title_label.text() == "日常零花"
    assert page.detail_status_label.text() == "黄灯"
    assert page.title_edit.text() == "2026-04 日常零花 预算临界提醒"
    assert page._row_widgets["rem-budget-amber"].meta_label.text()
    assert page._row_widgets["rem-budget-amber"].status_label.text()
    assert "当前 ¥80.00 / 阈值 ¥100.00" in page._row_widgets["rem-budget-amber"].focus_label.text()
    assert page.list_widget.item(budget_row).toolTip()
    assert page.notes_edit.minimumHeight() >= 180
    assert "阈值提醒" in page.detail_meta_label.text()
    assert "灯号提示" in page.reading_signal_label.text()
    assert "测试" in page.reading_source_label.text()
    assert page.lights_table.rowCount() == 3
    assert page.subscriptions_table.rowCount() >= 1
    assert "日常零花" in page.notes_view.toPlainText()

    page.filter_buttons["红灯"].click()
    qapp.processEvents()
    assert page.list_widget.count() == 1
    assert page.list_meta_label.text().startswith("1 条提醒")
    assert "红灯" in page.list_meta_label.text()
    assert next(iter(page._row_widgets.values())).title_label.text() == "房租"

    window.close()
