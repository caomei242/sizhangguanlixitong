from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QComboBox, QFrame, QHeaderView, QSizePolicy, QTableWidget

from private_ledger.app import build_app
from private_ledger.domain.models import (
    Account,
    BalanceSnapshot,
    BudgetLine,
    MonthlyBudget,
    ReminderItem,
    Transaction,
)
from private_ledger.storage.repository import LedgerRepository
from private_ledger.ui import main_window as main_window_module
from private_ledger.ui.pages.budgets_page import BudgetsPage
from private_ledger.ui.pages.dashboard_page import PeriodTrendChart
from private_ledger.ui.theme import APP_STYLESHEET


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


def _select_row_by_key(table: QTableWidget, row_key: str, *, key_column: int = 0) -> bool:
    for row in range(table.rowCount()):
        key_item = table.item(row, key_column)
        if key_item is None or key_item.text() != row_key:
            continue
        table.selectRow(row)
        return True
    return False


def _assert_compact_budget_ledger(
    table: QTableWidget,
) -> None:
    assert table.columnCount() == 6
    assert 88 <= table.columnWidth(0) <= 112
    assert 88 <= table.columnWidth(1) <= 112
    for column in range(2, table.columnCount()):
        assert table.horizontalHeader().sectionResizeMode(column) == QHeaderView.ResizeMode.Stretch


def test_application_forces_light_appearance(tmp_path, qapp) -> None:
    app, window = build_app(data_dir=tmp_path)
    palette = app.palette()

    assert app.style().objectName().lower() == "fusion"
    assert palette.color(QPalette.ColorRole.Window).name().lower() == "#f5f7fb"
    assert palette.color(QPalette.ColorRole.Base).name().lower() == "#ffffff"
    assert palette.color(QPalette.ColorRole.ToolTipBase).name().lower() == "#ffffff"
    assert palette.color(QPalette.ColorRole.ToolTipText).name().lower() == "#24324a"

    window.close()


def test_period_trend_chart_keeps_light_background(qapp) -> None:
    chart = PeriodTrendChart()

    assert chart.frameShape() == QFrame.Shape.NoFrame
    assert chart.chart.isBackgroundVisible()
    assert chart.chart.backgroundBrush().color().name().lower() == "#f7f9fc"
    assert chart.viewport().autoFillBackground()


def test_app_stylesheet_keeps_light_workspace_shell_rules() -> None:
    required_fragments = (
        'QWidget[sectionRole="workspace-tabs"]',
        "QTabWidget::pane",
        "QSplitter::handle",
        "QAbstractScrollArea::viewport",
        "QToolTip",
    )

    for fragment in required_fragments:
        assert fragment in APP_STYLESHEET

    assert "QTabWidget QWidget" not in APP_STYLESHEET


def test_annual_month_status_keeps_pending_rows_actionable(qapp) -> None:
    page = BudgetsPage()

    assert page._annual_month_item_status("收入", Decimal("100.00"), Decimal("120.00"), Decimal("10.00"), "") == "待确认"
    assert page._annual_month_item_status("支出", Decimal("100.00"), Decimal("80.00"), Decimal("5.00"), "") == "待确认"
    assert page._is_actionable_pending_row({"pending": Decimal("1.00"), "status": "已达成"})


def test_annual_month_detail_rows_merge_salary_aliases(qapp) -> None:
    page = BudgetsPage()
    page._annual_matrix = SimpleNamespace(year=2026)

    salary_rows = [
        SimpleNamespace(
            name="工资",
            category="工资",
            notes="",
            line_kind="收入",
            group_name="当期收入",
            status="未设预算",
            planned_total=Decimal("0.00"),
            planned_months={"2026-03": Decimal("0.00")},
            actual_months={"2026-03": Decimal("11632.22")},
            pending_months={"2026-03": Decimal("0.00")},
            effective_start_month="2026-03",
            effective_end_month="2026-03",
        ),
        SimpleNamespace(
            name="工资（上个月）",
            category="工资（上个月）",
            notes="",
            line_kind="收入",
            group_name="当期收入",
            status="未发生",
            planned_total=Decimal("11642.00"),
            planned_months={"2026-03": Decimal("11642.00")},
            actual_months={"2026-03": Decimal("0.00")},
            pending_months={"2026-03": Decimal("0.00")},
            effective_start_month="2026-03",
            effective_end_month="2026-03",
        ),
    ]

    rows = page._annual_month_detail_rows(salary_rows, 3, "收入")

    assert len(rows) == 1
    merged = rows[0]
    assert merged["name"] == "工资（上个月）"
    assert merged["category"] == "工资（上个月）"
    assert merged["planned"] == Decimal("11642.00")
    assert merged["actual"] == Decimal("11632.22")
    assert merged["delta"] == Decimal("-9.78")
    assert merged["bucket_other"] is False
    assert merged["match_names"] == {"工资", "工资（上个月）"}
    assert merged["match_categories"] == {"工资", "工资（上个月）"}


def test_sync_annual_budget_status_matches_alias_categories(tmp_path, qapp) -> None:
    _app, window = build_app(data_dir=tmp_path)
    repo = window.repository
    repo.upsert_transaction(
        Transaction(
            id="txn-salary-pending",
            occurred_on="2026-03-10",
            transaction_type="收入",
            category="工资",
            amount="11632.22",
            from_account_id="",
            to_account_id="",
            status="待确认",
            source="测试",
            notes="",
            related_transaction_id="",
            created_at="2026-03-10T10:00:00",
            updated_at="2026-03-10T10:00:00",
        )
    )

    window._sync_annual_budget_status(
        {
            "month_key": "2026-03",
            "detail_type": "收入",
            "category": "工资（上个月）",
            "name": "工资（上个月）",
            "aliases": ["工资", "工资（上个月）"],
            "target_status": "已确认",
            "mode": "single",
        }
    )

    updated = next(txn for txn in repo.list_transactions() if txn.id == "txn-salary-pending")
    assert updated.status == "已确认"

    window.close()


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
    repo.upsert_transaction(
        Transaction(
            id="txn-pending",
            occurred_on="2026-04-19",
            transaction_type="支出",
            category="待确认",
            amount="30.00",
            from_account_id="acc-main",
            to_account_id="",
            status="待确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-19T19:00:00",
            updated_at="2026-04-19T19:00:00",
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
    assert window.period_granularity_combo.currentText() == "日"
    assert window.period_value_combo.currentText() == "2026-04"
    assert window.dashboard_page.trend_chart.chart.title() == "按日趋势"
    assert window.dashboard_page.trend_chart.series_count_for_test() == 4
    assert window.dashboard_page.trend_table.rowCount() == 30
    hover_summary = window.dashboard_page.trend_chart.hover_summary_for_test(17)
    assert "18日" in hover_summary
    assert "收入：" in hover_summary
    assert "支出：" in hover_summary
    assert "结余：" in hover_summary
    assert "待确认：" in hover_summary
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
    assert window.dashboard_page.trend_chart.series_count_for_test() == 4
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
    window.nav.setCurrentRow(1)
    page = window.budgets_page

    assert window.period_granularity_combo.isHidden()
    assert page.month_edit.parent() is not None
    assert not page.month_edit.isHidden()
    assert isinstance(page.month_edit, QComboBox)
    assert page.month_edit.count() == 12
    assert page.month_edit.itemText(0) == "2026-01"
    assert page.month_edit.itemText(11) == "2026-12"
    tab_texts = [page.tabs.tabText(index) for index in range(page.tabs.count())]
    assert tab_texts == ["预算工作台", "全年十二月", "生效范围"]
    assert "工作台" in page.tabs.tabText(page.tabs.currentIndex())
    assert page.workbench_splitter.orientation() == Qt.Orientation.Horizontal
    assert page.workbench_splitter.count() == 0
    assert _section_frames(page, "budget-workbench")
    assert _section_frames(page, "budget-comparison-panel")
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
    assert page.comparison_table.horizontalHeaderItem(3).text() == "生效方式"
    assert page.comparison_table.horizontalHeaderItem(4).text() == "开始月份"
    assert page.comparison_table.horizontalHeaderItem(5).text() == "结束月份"
    assert page.link_same_budget_checkbox.text() == "联动同名项目"
    group_rows = [
        page.comparison_table.item(row, 0).text().strip()
        for row in range(page.comparison_table.rowCount())
        if page.comparison_table.item(row, 0)
        and page.comparison_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        and page.comparison_table.item(row, 0).data(Qt.ItemDataRole.UserRole).get("is_group")
    ]
    assert [text.split("】", 1)[0].lstrip("【") for text in group_rows[:5]] == [
        "长期收入",
        "当期收入",
        "长期支出",
        "当期支出",
        "储蓄",
    ]
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
    window.nav.setCurrentRow(1)
    page = window.budgets_page

    page.kind_combo.setCurrentText("固定支出")
    page.name_edit.setText("房租")
    page.category_edit.setText("房租")
    page.planned_amount_edit.setText("2500")
    page.effective_mode_combo.setCurrentText("每月持续")
    page.save_line_button.click()
    qapp.processEvents()

    lines = window.repository.list_effective_budget_lines("2026-05")
    assert len(lines) == 1
    assert lines[0].name == "房租"
    assert lines[0].effective_start_month == "2026-04"
    assert lines[0].effective_end_month == ""

    window.close()


def test_budget_page_supports_inline_workbench_editing(tmp_path, qapp) -> None:
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
            id="line-salary",
            budget_id="budget-2026-04",
            line_kind="收入",
            name="工资（上个月）",
            category="工资（上个月）",
            planned_amount="11642.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="每月十号发上个月工资",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
            effective_start_month="2026-04",
            effective_end_month="2026-04",
        )
    )
    repo.upsert_budget(
        MonthlyBudget(
            id="budget-2026-05",
            month_key="2026-05",
            total_budget="0.00",
            notes="",
            status="生效中",
            created_at="2026-05-01T09:00:00",
            updated_at="2026-05-01T09:00:00",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="line-salary-may",
            budget_id="budget-2026-05",
            line_kind="收入",
            name="工资",
            category="工资",
            planned_amount="11642.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="五月工资草稿",
            created_at="2026-05-01T09:00:00",
            updated_at="2026-05-01T09:00:00",
            effective_start_month="2026-05",
            effective_end_month="2026-05",
        )
    )

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(1)
    page = window.budgets_page

    assert _select_row_by_key(page.comparison_table, "工资（上个月）")
    current_row = page.comparison_table.currentRow()
    planned_item = page.comparison_table.item(current_row, 6)
    actual_item = page.comparison_table.item(current_row, 7)
    type_item = page.comparison_table.item(current_row, 1)
    mode_item = page.comparison_table.item(current_row, 3)
    assert planned_item.flags() & Qt.ItemFlag.ItemIsEditable
    assert type_item.flags() & Qt.ItemFlag.ItemIsEditable
    assert mode_item.flags() & Qt.ItemFlag.ItemIsEditable
    assert not (actual_item.flags() & Qt.ItemFlag.ItemIsEditable)
    assert page.comparison_table.itemDelegateForColumn(1) is not None
    assert page.comparison_table.itemDelegateForColumn(3) is not None

    planned_item.setText("12000")
    qapp.processEvents()
    assert repo.get_budget_line("line-salary").planned_amount == "12000.00"
    assert repo.get_budget_line("line-salary-may").planned_amount == "11642.00"

    assert _select_row_by_key(page.comparison_table, "工资（上个月）")
    current_row = page.comparison_table.currentRow()
    category_item = page.comparison_table.item(current_row, 2)
    category_item.setText("工资")
    qapp.processEvents()
    assert repo.get_budget_line("line-salary").category == "工资"

    assert _select_row_by_key(page.comparison_table, "工资（上个月）")
    current_row = page.comparison_table.currentRow()
    page.link_same_budget_checkbox.setChecked(True)
    effective_item = page.comparison_table.item(current_row, 3)
    effective_item.setText("每月持续")
    qapp.processEvents()
    updated_line = repo.get_budget_line("line-salary")
    assert updated_line.effective_start_month == "2026-04"
    assert updated_line.effective_end_month == ""
    assert repo.get_budget_line("line-salary-may") is None
    assert len([line for line in repo.list_effective_budget_lines("2026-05") if line.category == "工资"]) == 1
    assert _select_row_by_key(page.comparison_table, "工资（上个月）")
    assert page.comparison_table.item(page.comparison_table.currentRow() - 1, 0).text().strip().startswith("【长期收入】")

    current_row = page.comparison_table.currentRow()
    page.comparison_table.item(current_row, 3).setText("仅当前月")
    qapp.processEvents()
    updated_line = repo.get_budget_line("line-salary")
    assert updated_line.effective_start_month == "2026-04"
    assert updated_line.effective_end_month == "2026-04"
    assert _select_row_by_key(page.comparison_table, "工资（上个月）")
    assert page.comparison_table.item(page.comparison_table.currentRow() - 1, 0).text().strip().startswith("【当期收入】")

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
                    group_name="长期收入",
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
                    group_name="长期收入",
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
                    group_name="当期收入",
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
                    group_name="当期收入",
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
                    group_name="长期支出",
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
                    group_name="长期支出",
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
                    group_name="当期支出",
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
                    group_name="当期支出",
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
                    group_name="当期支出",
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
    window.nav.setCurrentRow(1)
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
    assert income_panel["confirm_selected_button"].text() == "确认选中项"
    assert income_panel["confirm_selected_button"].isEnabled()
    assert income_panel["confirm_all_button"].text() == "确认本区待确认"
    assert income_panel["confirm_all_button"].isEnabled()
    assert expense_panel["planned_label"].text() == "计划 ¥920.00"
    assert expense_panel["actual_label"].text() == "实际 ¥780.00"
    assert expense_panel["pending_label"].text() == "待确认 ¥300.00"
    assert expense_panel["confirm_selected_button"].text() == "确认选中项"
    assert expense_panel["confirm_selected_button"].isEnabled()
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
    assert income_rows["工资"] == ["工资", "工资", "¥1,000.00", "¥1,300.00", "¥0.00", "+¥300.00"]
    assert income_rows["网店收入"] == ["网店收入", "网店收入", "¥300.00", "¥260.00", "¥0.00", "¥-40.00"]
    assert income_rows["房租补贴（当月）"] == ["房租补贴（当月）", "房租补贴（当月）", "¥1,800.00", "¥0.00", "¥1,800.00", "¥-1,800.00"]
    assert set(expense_rows) == {"其他杂费", "日常餐饮", "话费充值"}
    assert expense_rows["日常餐饮"] == ["日常餐饮", "餐饮", "¥500.00", "¥680.00", "¥0.00", "¥-180.00"]
    assert expense_rows["其他杂费"] == ["其他杂费", "其他支出", "¥120.00", "¥100.00", "¥0.00", "+¥20.00"]
    assert expense_rows["话费充值"] == ["话费充值", "话费", "¥300.00", "¥0.00", "¥300.00", "+¥300.00"]
    assert set(temp_income_rows) == {"兼职奖金"}
    assert temp_income_rows["兼职奖金"] == ["兼职奖金", "奖金", "¥200.00", "¥240.00", "¥0.00", "+¥40.00"]
    assert set(temp_expense_rows) == {"临时交通"}
    assert temp_expense_rows["临时交通"] == ["临时交通", "交通", "¥0.00", "¥60.00", "¥20.00", "¥-60.00"]
    assert {"工资", "房租补贴（当月）", "网店收入"}.isdisjoint(temp_income_rows)
    assert {"其他杂费", "日常餐饮", "话费充值"}.isdisjoint(temp_expense_rows)
    for table in (
        income_panel["table"],
        expense_panel["table"],
        temp_income_panel["table"],
        temp_expense_panel["table"],
    ):
        _assert_table_has_no_vertical_scroll(table)

    _assert_compact_budget_ledger(income_panel["table"])
    _assert_compact_budget_ledger(expense_panel["table"])
    _assert_compact_budget_ledger(temp_income_panel["table"])
    _assert_compact_budget_ledger(temp_expense_panel["table"])

    expense_panel["confirm_selected_button"].click()
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
    assert _select_row_by_key(temp_expense_panel["table"], "临时交通")
    assert temp_expense_panel["confirm_same_button"].isEnabled()
    temp_expense_panel["confirm_same_button"].click()
    qapp.processEvents()
    assert next(txn for txn in repo.list_transactions() if txn.id == "txn-apr-traffic-pending").status == "已确认"

    assert _select_row_by_key(income_panel["table"], "房租补贴（当月）")
    assert income_panel["confirm_selected_button"].isEnabled()
    income_panel["confirm_selected_button"].click()
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
    page.kind_combo.setCurrentText("分类支出")
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
            occurred_on="2026-04-09 09:00",
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
        Transaction(
            id="txn-income",
            occurred_on="2026-04-10",
            transaction_type="收入",
            category="工资",
            amount="1200.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="测试",
            notes="工资备注",
            related_transaction_id="",
            created_at="2026-04-10T12:00:00",
            updated_at="2026-04-10T12:00:00",
        ),
        Transaction(
            id="txn-obsidian",
            occurred_on="2026-04-10",
            transaction_type="支出",
            category="日常零花",
            amount="19.52",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="Obsidian 私帐自动同步",
            notes=(
                "同步来源：Obsidian 私帐自动同步\n"
                "Obsidian 文件：/Users/gd/Library/Mobile Documents/私帐/2026-04-29.md\n"
                "标签：日常零花\n"
                "商户/备注：好邻居超市(思明店)\n"
                "来源行：02:47｜19.52 元｜好邻居超市(思明店)\n"
                "采集批次：2026-04-30T10:33:03"
            ),
            related_transaction_id="",
            created_at="2026-04-10T12:00:00",
            updated_at="2026-04-10T12:00:00",
        ),
        Transaction(
            id="txn-system-notes",
            occurred_on="2026-04-11",
            transaction_type="支出",
            category="系统备注",
            amount="20.04",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="Excel 导入",
            notes=(
                "来源文件：账单_202604261854.xlsx\n"
                "原始行号：2\n"
                "账期口径：按 Excel 日期列原样导入\n"
                "金额口径：按收支类型保留方向，入库金额统一存正数\n"
                "账户：源文件为空，待确认\n"
                "原始分类：购物消费/其他\n"
                "原始备注：好邻居超市(思明店)"
            ),
            related_transaction_id="",
            created_at="2026-04-11T12:00:00",
            updated_at="2026-04-11T12:00:00",
        ),
        Transaction(
            id="txn-system-only",
            occurred_on="2026-04-12",
            transaction_type="支出",
            category="纯系统备注",
            amount="9.90",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source="Excel 导入",
            notes=(
                "来源文件：账单_202604261854.xlsx\n"
                "原始行号：3\n"
                "账期口径：按 Excel 日期列原样导入\n"
                "金额口径：按收支类型保留方向，入库金额统一存正数\n"
                "账户：源文件为空，待确认"
            ),
            related_transaction_id="",
            created_at="2026-04-12T12:00:00",
            updated_at="2026-04-12T12:00:00",
        ),
    ]:
        repo.upsert_transaction(transaction)

    window.refresh_data(reference_month="2026-04")
    window.nav.setCurrentRow(3)
    page = window.transactions_page

    assert page.table.horizontalHeaderItem(0).text() == "选择"
    assert page.table.horizontalHeaderItem(3).text() == "标签"
    assert page.table.horizontalHeaderItem(4).text() == "备注"
    assert page.type_filter_combo.currentText() == "全部类型"
    assert page.tag_filter_combo.findText("餐饮") >= 0
    assert page.tag_filter_combo.findText("交通") >= 0

    page.tag_filter_combo.setCurrentText("餐饮")
    assert page.table.rowCount() == 1
    assert page.table.item(0, 3).text() == "餐饮"
    assert page.table.item(0, 4).text() == "午餐备注"

    page.clear_filter_button.click()
    qapp.processEvents()
    assert page.table.rowCount() == 6
    page.type_filter_combo.setCurrentText("只看收入")
    qapp.processEvents()
    assert page.table.rowCount() == 1
    assert page.table.item(0, 2).text() == "收入"
    page.type_filter_combo.setCurrentText("只看支出")
    qapp.processEvents()
    assert page.table.rowCount() == 5
    assert all(page.table.item(row, 2).text() == "支出" for row in range(page.table.rowCount()))
    page.clear_filter_button.click()
    qapp.processEvents()
    assert page.type_filter_combo.currentText() == "全部类型"
    assert page.table.rowCount() == 6
    assert _select_row_by_key(page.table, "日常零花", key_column=3)
    assert page.table.item(page.table.currentRow(), 4).text() == "好邻居超市(思明店)"
    assert "Obsidian 文件" in page.table.item(page.table.currentRow(), 4).toolTip()
    assert _select_row_by_key(page.table, "系统备注", key_column=3)
    assert page.table.item(page.table.currentRow(), 4).text() == "好邻居超市(思明店)"
    assert "账单_202604261854.xlsx" in page.table.item(page.table.currentRow(), 4).toolTip()
    assert _select_row_by_key(page.table, "纯系统备注", key_column=3)
    assert page.table.item(page.table.currentRow(), 4).text() == ""
    assert "金额口径" in page.table.item(page.table.currentRow(), 4).toolTip()
    assert _select_row_by_key(page.table, "交通", key_column=3)
    assert page.date_edit.date().toString("yyyy-MM-dd") == "2026-04-09"
    page.status_combo.setCurrentText("已确认")
    qapp.processEvents()
    traffic = {item.id: item for item in repo.list_transactions()}["txn-traffic"]
    assert traffic.status == "已确认"
    assert traffic.occurred_on == "2026-04-09 09:00"

    for row in range(page.table.rowCount()):
        checkbox_item = page.table.item(row, 0)
        if checkbox_item is not None:
            checkbox_item.setCheckState(Qt.CheckState.Checked)
    page.batch_status_combo.setCurrentText("批量改为待确认")
    page.batch_status_button.click()
    qapp.processEvents()
    statuses = {item.id: item.status for item in repo.list_transactions()}
    assert statuses["txn-food"] == "待确认"
    assert statuses["txn-traffic"] == "待确认"

    window.close()


def test_repairs_obsidian_transaction_dates_from_source_notes(tmp_path) -> None:
    repo = LedgerRepository(data_dir=tmp_path)
    repo.upsert_transaction(
        Transaction(
            id="txn-wrong-date",
            occurred_on="2026-04-30",
            transaction_type="支出",
            category="佛山税务",
            amount="200.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source=main_window_module.SYNC_SOURCE,
            notes=(
                "同步来源：Obsidian 私帐自动同步\n"
                "Obsidian 文件：/Users/gd/个人日志/财务/私帐/每日收集/2026-04-28.md\n"
                "标签：佛山税务\n"
                "商户/备注：缴税业务\n"
                "来源行：15:30｜200.00 元｜缴税业务"
            ),
            related_transaction_id="",
            created_at="2026-04-29T10:00:00",
            updated_at="2026-04-30T10:00:00",
        )
    )
    repo.upsert_transaction(
        Transaction(
            id="txn-unclear-date",
            occurred_on="2026-04-30",
            transaction_type="支出",
            category="日常零花",
            amount="20.00",
            from_account_id="",
            to_account_id="",
            status="已确认",
            source=main_window_module.SYNC_SOURCE,
            notes="Obsidian 文件：/Users/gd/个人日志/财务/私帐/每日收集/2026-04-27.md\n来源行：缺少时间",
            related_transaction_id="",
            created_at="2026-04-29T10:00:00",
            updated_at="2026-04-30T10:00:00",
        )
    )

    result = main_window_module.repair_obsidian_transaction_dates(repo)
    transactions = {item.id: item for item in repo.list_transactions()}

    assert result.repaired_count == 1
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert transactions["txn-wrong-date"].occurred_on == "2026-04-28 15:30"
    assert transactions["txn-unclear-date"].occurred_on == "2026-04-30"

    second_result = main_window_module.repair_obsidian_transaction_dates(repo)
    assert second_result.repaired_count == 0
    assert second_result.backup_path is None
    repo.close()


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
