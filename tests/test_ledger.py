from __future__ import annotations

from decimal import Decimal

from private_ledger.domain.ledger import (
    build_annual_budget_matrix,
    build_budget_comparison,
    build_daily_trend,
    build_monthly_trend,
    build_month_summary,
    build_period_summary,
    calculate_account_balance,
    collect_due_reminders,
    is_budget_line_effective_in_month,
)
from private_ledger.domain.models import (
    Account,
    BalanceSnapshot,
    BudgetLine,
    MonthlyBudget,
    PeriodSelection,
    ReminderItem,
    Transaction,
)


def test_calculate_account_balance_uses_latest_confirmed_snapshot_and_confirmed_transactions() -> None:
    account = Account(
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
    snapshots = [
        BalanceSnapshot(
            id="snap-old",
            account_id="acc-main",
            snapshot_time="2026-04-01T09:00:00",
            amount="900.00",
            status="已确认",
            source="月初校准",
            notes="",
            created_at="2026-04-01T09:00:00",
        ),
        BalanceSnapshot(
            id="snap-latest",
            account_id="acc-main",
            snapshot_time="2026-04-10T09:00:00",
            amount="1000.00",
            status="已确认",
            source="手动对账",
            notes="",
            created_at="2026-04-10T09:00:00",
        ),
        BalanceSnapshot(
            id="snap-pending",
            account_id="acc-main",
            snapshot_time="2026-04-20T09:00:00",
            amount="9999.00",
            status="待确认",
            source="手动对账",
            notes="",
            created_at="2026-04-20T09:00:00",
        ),
    ]
    transactions = [
        Transaction(
            id="txn-expense",
            occurred_on="2026-04-12",
            transaction_type="支出",
            category="餐饮",
            amount="120.00",
            from_account_id="acc-main",
            to_account_id="",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-12T10:00:00",
            updated_at="2026-04-12T10:00:00",
        ),
        Transaction(
            id="txn-income",
            occurred_on="2026-04-15",
            transaction_type="收入",
            category="工资",
            amount="300.00",
            from_account_id="",
            to_account_id="acc-main",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-15T10:00:00",
            updated_at="2026-04-15T10:00:00",
        ),
        Transaction(
            id="txn-transfer",
            occurred_on="2026-04-16",
            transaction_type="转账",
            category="储蓄计划",
            amount="50.00",
            from_account_id="acc-main",
            to_account_id="acc-save",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-16T10:00:00",
            updated_at="2026-04-16T10:00:00",
        ),
        Transaction(
            id="txn-topup",
            occurred_on="2026-04-17",
            transaction_type="充值",
            category="API 余额",
            amount="20.00",
            from_account_id="acc-main",
            to_account_id="acc-api",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-17T10:00:00",
            updated_at="2026-04-17T10:00:00",
        ),
        Transaction(
            id="txn-pending",
            occurred_on="2026-04-18",
            transaction_type="支出",
            category="娱乐",
            amount="100.00",
            from_account_id="acc-main",
            to_account_id="",
            status="待确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-18T10:00:00",
            updated_at="2026-04-18T10:00:00",
        ),
    ]

    balance = calculate_account_balance(account, snapshots, transactions)

    assert balance == Decimal("1110.00")


def test_build_month_summary_counts_confirmed_expense_and_refund_only() -> None:
    budget = MonthlyBudget(
        id="budget-2026-04",
        month_key="2026-04",
        total_budget="8000.00",
        notes="",
        status="生效中",
        created_at="2026-04-01T08:00:00",
        updated_at="2026-04-01T08:00:00",
    )
    transactions = [
        Transaction(
            id="expense-food",
            occurred_on="2026-04-03",
            transaction_type="支出",
            category="餐饮",
            amount="120.00",
            from_account_id="acc-main",
            to_account_id="",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-03T12:00:00",
            updated_at="2026-04-03T12:00:00",
        ),
        Transaction(
            id="expense-pending",
            occurred_on="2026-04-04",
            transaction_type="支出",
            category="餐饮",
            amount="70.00",
            from_account_id="acc-main",
            to_account_id="",
            status="待确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-04T12:00:00",
            updated_at="2026-04-04T12:00:00",
        ),
        Transaction(
            id="refund-food",
            occurred_on="2026-04-05",
            transaction_type="退款",
            category="餐饮",
            amount="20.00",
            from_account_id="",
            to_account_id="acc-main",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="expense-food",
            created_at="2026-04-05T12:00:00",
            updated_at="2026-04-05T12:00:00",
        ),
        Transaction(
            id="expense-traffic",
            occurred_on="2026-04-06",
            transaction_type="支出",
            category="交通",
            amount="50.00",
            from_account_id="acc-main",
            to_account_id="",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-06T12:00:00",
            updated_at="2026-04-06T12:00:00",
        ),
        Transaction(
            id="transfer",
            occurred_on="2026-04-07",
            transaction_type="转账",
            category="储蓄计划",
            amount="100.00",
            from_account_id="acc-main",
            to_account_id="acc-save",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-07T12:00:00",
            updated_at="2026-04-07T12:00:00",
        ),
    ]

    summary = build_month_summary("2026-04", budget, transactions)

    assert summary.total_budget == Decimal("8000.00")
    assert summary.actual_expense == Decimal("150.00")
    assert summary.remaining_budget == Decimal("7850.00")
    assert summary.pending_amount == Decimal("70.00")
    assert summary.by_category["餐饮"] == Decimal("100.00")
    assert summary.by_category["交通"] == Decimal("50.00")


def _budget_line(
    line_id: str,
    line_kind: str,
    name: str,
    category: str,
    planned_amount: str,
    notes: str = "",
    effective_start_month: str = "",
    effective_end_month: str = "",
) -> BudgetLine:
    return BudgetLine(
        id=line_id,
        budget_id="budget-2026-04",
        line_kind=line_kind,
        name=name,
        category=category,
        planned_amount=planned_amount,
        day_of_month=None,
        is_required=False,
        reminder_days=0,
        notes=notes,
        created_at="2026-04-01T00:00:00",
        updated_at="2026-04-01T00:00:00",
        effective_start_month=effective_start_month,
        effective_end_month=effective_end_month,
    )


def _budget_txn(
    txn_id: str,
    transaction_type: str,
    category: str,
    amount: str,
    status: str = "已确认",
    occurred_on: str = "2026-04-10",
) -> Transaction:
    return Transaction(
        id=txn_id,
        occurred_on=occurred_on,
        transaction_type=transaction_type,
        category=category,
        amount=amount,
        from_account_id="acc-main" if transaction_type == "支出" else "",
        to_account_id="acc-main" if transaction_type in {"收入", "退款"} else "",
        status=status,
        source="测试",
        notes="",
        related_transaction_id="",
        created_at="2026-04-10T00:00:00",
        updated_at="2026-04-10T00:00:00",
    )


def test_build_budget_comparison_matches_lines_and_unbudgeted_actuals() -> None:
    budget_lines = [
        _budget_line("line-income", "收入", "工资", "工资", "1000.00"),
        _budget_line("line-food", "分类预算", "日常餐饮", "餐饮", "300.00"),
        _budget_line("line-rent", "固定支出", "房租", "房租", "2000.00", "草稿待调整"),
    ]
    transactions = [
        _budget_txn("income-wage", "收入", "工资", "1200.00"),
        _budget_txn("income-bonus", "收入", "奖金", "200.00"),
        _budget_txn("expense-food", "支出", "餐饮", "350.00"),
        _budget_txn("refund-food", "退款", "餐饮", "20.00"),
        _budget_txn("pending-food", "支出", "餐饮", "50.00", "待确认"),
        _budget_txn("expense-traffic", "支出", "交通", "80.00"),
        _budget_txn("transfer", "转账", "储蓄计划", "999.00"),
        _budget_txn("other-month", "支出", "餐饮", "999.00", occurred_on="2026-05-01"),
    ]

    comparison = build_budget_comparison("2026-04", budget_lines, transactions)

    assert comparison.summary.planned_income == Decimal("1000.00")
    assert comparison.summary.actual_income == Decimal("1400.00")
    assert comparison.summary.planned_expense == Decimal("2300.00")
    assert comparison.summary.actual_expense == Decimal("410.00")
    assert comparison.summary.planned_balance == Decimal("-1300.00")
    assert comparison.summary.actual_balance == Decimal("990.00")
    assert comparison.summary.pending_amount == Decimal("50.00")

    food = next(row for row in comparison.rows if row.line_id == "line-food")
    assert food.actual_amount == Decimal("330.00")
    assert food.pending_amount == Decimal("50.00")
    assert food.delta_amount == Decimal("30.00")
    assert food.status == "超支"

    rent = next(row for row in comparison.rows if row.line_id == "line-rent")
    assert rent.status == "草稿待调整"

    unbudgeted_rows = {
        (row.name, row.group_name)
        for row in comparison.rows
        if row.group_name in {"当期收入", "当期支出"} and not row.line_id
    }
    assert unbudgeted_rows == {("交通", "当期支出"), ("奖金", "当期收入")}


def test_build_budget_comparison_matches_known_budget_aliases() -> None:
    budget_lines = [
        _budget_line("line-rent-subsidy", "收入", "房租补贴（当月）", "房租补贴", "1800.00"),
        _budget_line("line-tirzepatide", "支出", "提尔", "提尔", "600.00"),
        _budget_line("line-tax", "支出", "税务相关", "税务相关", "500.00"),
    ]
    transactions = [
        _budget_txn("income-fund", "收入", "公积金收入", "1800.00"),
        _budget_txn("expense-tirzepatide", "支出", "替尔泊肽", "576.20"),
        _budget_txn("expense-tax-city", "支出", "佛山税务", "200.00"),
        _budget_txn("expense-tax-common", "支出", "税务", "426.04"),
        _budget_txn("income-other-a", "收入", "其他", "100.00"),
        _budget_txn("income-other-b", "收入", "其他收入", "100.00"),
    ]

    comparison = build_budget_comparison("2026-04", budget_lines, transactions)

    subsidy = next(row for row in comparison.rows if row.line_id == "line-rent-subsidy")
    assert subsidy.category == "房租补贴"
    assert subsidy.actual_amount == Decimal("1800.00")
    assert subsidy.delta_amount == Decimal("0.00")
    assert not [row for row in comparison.rows if not row.line_id and row.name == "公积金收入"]

    tirzepatide = next(row for row in comparison.rows if row.line_id == "line-tirzepatide")
    assert tirzepatide.category == "提尔"
    assert tirzepatide.actual_amount == Decimal("576.20")
    assert tirzepatide.delta_amount == Decimal("-23.80")
    assert not [row for row in comparison.rows if not row.line_id and row.name == "替尔泊肽"]

    tax = next(row for row in comparison.rows if row.line_id == "line-tax")
    assert tax.category == "税务相关"
    assert tax.actual_amount == Decimal("626.04")
    assert tax.delta_amount == Decimal("126.04")
    assert not [row for row in comparison.rows if not row.line_id and row.name in {"佛山税务", "税务"}]

    other = next(row for row in comparison.rows if not row.line_id and row.name == "其他收入")
    assert other.actual_amount == Decimal("200.00")
    assert other.category == "其他收入"
    assert not [row for row in comparison.rows if not row.line_id and row.name == "其他"]


def test_is_budget_line_effective_in_month_uses_inclusive_string_month_range() -> None:
    limited_line = _budget_line(
        "line-limited",
        "分类预算",
        "季度预算",
        "餐饮",
        "300.00",
        effective_start_month="2026-04",
        effective_end_month="2026-06",
    )
    open_ended_line = _budget_line(
        "line-open-ended",
        "固定支出",
        "长期房租",
        "房租",
        "2000.00",
        effective_start_month="2026-05",
    )
    no_start_line = _budget_line(
        "line-no-start",
        "收入",
        "长期收入",
        "工资",
        "1000.00",
        effective_end_month="2026-03",
    )

    assert not is_budget_line_effective_in_month(limited_line, "2026-03")
    assert is_budget_line_effective_in_month(limited_line, "2026-04")
    assert is_budget_line_effective_in_month(limited_line, "2026-06")
    assert not is_budget_line_effective_in_month(limited_line, "2026-07")
    assert not is_budget_line_effective_in_month(open_ended_line, "2026-04")
    assert is_budget_line_effective_in_month(open_ended_line, "2026-12")
    assert is_budget_line_effective_in_month(no_start_line, "2026-01")
    assert not is_budget_line_effective_in_month(no_start_line, "2026-04")


def test_build_annual_budget_matrix_returns_12_months_and_reuses_monthly_budget_rules() -> None:
    budget_lines = [
        _budget_line(
            "line-income",
            "收入",
            "工资",
            "工资",
            "1000.00",
            effective_start_month="2026-01",
            effective_end_month="2026-12",
        ),
        _budget_line(
            "line-food",
            "分类预算",
            "日常餐饮",
            "餐饮",
            "300.00",
            effective_start_month="2026-04",
            effective_end_month="2026-06",
        ),
        _budget_line(
            "line-rent",
            "固定支出",
            "房租",
            "房租",
            "2000.00",
            effective_start_month="2026-05",
        ),
    ]
    transactions = [
        _budget_txn("jan-income", "收入", "工资", "1000.00", occurred_on="2026-01-05"),
        _budget_txn("mar-food", "支出", "餐饮", "90.00", occurred_on="2026-03-10"),
        _budget_txn("apr-income", "收入", "工资", "1200.00", occurred_on="2026-04-05"),
        _budget_txn("apr-food", "支出", "餐饮", "350.00", occurred_on="2026-04-10"),
        _budget_txn("apr-refund", "退款", "餐饮", "20.00", occurred_on="2026-04-12"),
        _budget_txn("apr-pending-income", "收入", "工资", "500.00", "待确认", "2026-04-13"),
        _budget_txn("apr-pending-food", "支出", "餐饮", "70.00", "待确认", "2026-04-14"),
        _budget_txn("apr-transfer", "转账", "储蓄计划", "999.00", occurred_on="2026-04-15"),
        _budget_txn("apr-topup", "充值", "API 余额", "888.00", occurred_on="2026-04-16"),
        _budget_txn("may-rent", "支出", "房租", "2000.00", occurred_on="2026-05-05"),
        _budget_txn("may-pending-food", "支出", "餐饮", "80.00", "待确认", "2026-05-06"),
        _budget_txn("other-year", "收入", "工资", "9999.00", occurred_on="2027-01-01"),
    ]

    matrix = build_annual_budget_matrix(2026, budget_lines, transactions)

    assert [point.month_key for point in matrix.months] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
        "2026-12",
    ]

    march = matrix.months[2]
    april = matrix.months[3]
    may = matrix.months[4]
    july = matrix.months[6]

    assert march.planned_income == Decimal("1000.00")
    assert march.planned_expense == Decimal("0.00")
    assert march.actual_expense == Decimal("90.00")

    assert april.planned_income == Decimal("1000.00")
    assert april.actual_income == Decimal("1200.00")
    assert april.planned_expense == Decimal("300.00")
    assert april.actual_expense == Decimal("330.00")
    assert april.planned_balance == Decimal("700.00")
    assert april.actual_balance == Decimal("870.00")
    assert april.pending_amount == Decimal("570.00")

    assert may.planned_expense == Decimal("2300.00")
    assert may.actual_expense == Decimal("2000.00")
    assert may.pending_amount == Decimal("80.00")
    assert july.planned_income == Decimal("1000.00")
    assert july.planned_expense == Decimal("2000.00")

    assert matrix.planned_income == Decimal("12000.00")
    assert matrix.actual_income == Decimal("2200.00")
    assert matrix.planned_expense == Decimal("16900.00")
    assert matrix.actual_expense == Decimal("2420.00")
    assert matrix.planned_balance == Decimal("-4900.00")
    assert matrix.actual_balance == Decimal("-220.00")
    assert matrix.pending_amount == Decimal("650.00")


def test_build_annual_budget_matrix_builds_budget_line_and_unbudgeted_detail_rows() -> None:
    budget_lines = [
        _budget_line(
            "line-food",
            "分类预算",
            "日常餐饮",
            "餐饮",
            "300.00",
            effective_start_month="2026-04",
            effective_end_month="2026-06",
        ),
    ]
    transactions = [
        _budget_txn("feb-unbudgeted-fun", "支出", "娱乐", "40.00", occurred_on="2026-02-10"),
        _budget_txn("apr-food", "支出", "餐饮", "350.00", occurred_on="2026-04-10"),
        _budget_txn("apr-food-refund", "退款", "餐饮", "20.00", occurred_on="2026-04-11"),
        _budget_txn("may-pending-food", "支出", "餐饮", "80.00", "待确认", "2026-05-06"),
        _budget_txn("jun-pending-traffic", "支出", "交通", "30.00", "待确认", "2026-06-06"),
    ]

    matrix = build_annual_budget_matrix(2026, budget_lines, transactions)

    zero_months = [Decimal("0.00")] * 12
    food = next(row for row in matrix.detail_rows if row.row_key == "line-food")
    assert food.group_name == "长期支出"
    assert food.line_kind == "分类预算"
    assert food.name == "日常餐饮"
    assert food.category == "餐饮"
    assert food.effective_start_month == "2026-04"
    assert food.effective_end_month == "2026-06"
    assert food.planned_months == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("300.00"),
        Decimal("300.00"),
        Decimal("300.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]
    assert food.actual_months == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("330.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]
    assert food.pending_months == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("80.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]
    assert food.planned_total == Decimal("900.00")
    assert food.actual_total == Decimal("330.00")
    assert food.pending_total == Decimal("80.00")
    assert food.delta_total == Decimal("570.00")
    assert food.status == "有待确认"

    unbudgeted_actual = next(row for row in matrix.detail_rows if row.row_key == "分类预算:娱乐")
    assert unbudgeted_actual.group_name == "当期支出"
    assert unbudgeted_actual.planned_months == zero_months
    assert unbudgeted_actual.actual_months == [
        Decimal("0.00"),
        Decimal("40.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]
    assert unbudgeted_actual.pending_months == zero_months
    assert unbudgeted_actual.planned_total == Decimal("0.00")
    assert unbudgeted_actual.actual_total == Decimal("40.00")
    assert unbudgeted_actual.pending_total == Decimal("0.00")
    assert unbudgeted_actual.delta_total == Decimal("-40.00")
    assert unbudgeted_actual.status == "未设预算"

    unbudgeted_pending = next(row for row in matrix.detail_rows if row.row_key == "分类预算:交通")
    assert unbudgeted_pending.group_name == "当期支出"
    assert unbudgeted_pending.actual_months == zero_months
    assert unbudgeted_pending.pending_months == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("30.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]
    assert unbudgeted_pending.planned_total == Decimal("0.00")
    assert unbudgeted_pending.actual_total == Decimal("0.00")
    assert unbudgeted_pending.pending_total == Decimal("30.00")
    assert unbudgeted_pending.delta_total == Decimal("0.00")
    assert unbudgeted_pending.status == "有待确认"


def test_build_annual_budget_matrix_uses_delta_total_semantics_by_line_kind() -> None:
    budget_lines = [
        _budget_line(
            "line-income",
            "收入",
            "工资",
            "工资",
            "1000.00",
            effective_start_month="2026-01",
            effective_end_month="2026-01",
        ),
        _budget_line(
            "line-food",
            "分类预算",
            "日常餐饮",
            "餐饮",
            "300.00",
            effective_start_month="2026-01",
            effective_end_month="2026-01",
        ),
        _budget_line(
            "line-rent",
            "固定支出",
            "房租",
            "房租",
            "2000.00",
            effective_start_month="2026-01",
            effective_end_month="2026-01",
        ),
    ]
    transactions = [
        _budget_txn("jan-income", "收入", "工资", "1200.00", occurred_on="2026-01-05"),
        _budget_txn("jan-food", "支出", "餐饮", "350.00", occurred_on="2026-01-10"),
        _budget_txn("jan-rent", "支出", "房租", "1800.00", occurred_on="2026-01-12"),
    ]

    matrix = build_annual_budget_matrix(2026, budget_lines, transactions)

    income = next(row for row in matrix.detail_rows if row.row_key == "line-income")
    food = next(row for row in matrix.detail_rows if row.row_key == "line-food")
    rent = next(row for row in matrix.detail_rows if row.row_key == "line-rent")

    assert income.planned_total == Decimal("1000.00")
    assert income.actual_total == Decimal("1200.00")
    assert income.delta_total == Decimal("200.00")

    assert food.planned_total == Decimal("300.00")
    assert food.actual_total == Decimal("350.00")
    assert food.delta_total == Decimal("-50.00")

    assert rent.planned_total == Decimal("2000.00")
    assert rent.actual_total == Decimal("1800.00")
    assert rent.delta_total == Decimal("200.00")


def _period_txn(
    txn_id: str,
    occurred_on: str,
    transaction_type: str,
    amount: str,
    status: str = "已确认",
) -> Transaction:
    return Transaction(
        id=txn_id,
        occurred_on=occurred_on,
        transaction_type=transaction_type,
        category="测试分类",
        amount=amount,
        from_account_id="acc-main" if transaction_type == "支出" else "",
        to_account_id="acc-main" if transaction_type == "收入" else "",
        status=status,
        source="测试",
        notes="",
        related_transaction_id="",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


def test_build_period_summary_counts_year_confirmed_and_pending_separately() -> None:
    selection = PeriodSelection(granularity="year", year=2026, month=1, quarter=1)
    transactions = [
        _period_txn("jan-income", "2026-01-05", "收入", "1000.00"),
        _period_txn("jan-expense", "2026-01-06", "支出", "300.00"),
        _period_txn("feb-expense", "2026-02-06", "支出", "900.00"),
        _period_txn("pending-income", "2026-02-07", "收入", "500.00", "待确认"),
        _period_txn("pending-expense", "2026-03-07", "支出", "120.00", "待确认"),
        _period_txn("other-year", "2025-12-31", "支出", "999.00"),
    ]

    summary = build_period_summary(selection, transactions)

    assert summary.income == Decimal("1000.00")
    assert summary.expense == Decimal("1200.00")
    assert summary.balance == Decimal("-200.00")
    assert summary.pending_amount == Decimal("620.00")
    assert summary.transaction_count == 5


def test_build_monthly_trend_uses_natural_quarter_and_excludes_pending() -> None:
    selection = PeriodSelection(granularity="quarter", year=2026, month=4, quarter=2)
    transactions = [
        _period_txn("apr-income", "2026-04-05", "收入", "800.00"),
        _period_txn("apr-expense", "2026-04-06", "支出", "300.00"),
        _period_txn("may-expense", "2026-05-06", "支出", "900.00"),
        _period_txn("may-pending", "2026-05-08", "支出", "400.00", "待确认"),
        _period_txn("jul-expense", "2026-07-01", "支出", "999.00"),
    ]

    trend = build_monthly_trend(selection, transactions)

    assert [point.month_key for point in trend] == ["2026-04", "2026-05", "2026-06"]
    assert [point.income for point in trend] == [Decimal("800.00"), Decimal("0.00"), Decimal("0.00")]
    assert [point.expense for point in trend] == [Decimal("300.00"), Decimal("900.00"), Decimal("0.00")]
    assert [point.balance for point in trend] == [Decimal("500.00"), Decimal("-900.00"), Decimal("0.00")]


def test_build_daily_trend_uses_each_day_and_separates_pending() -> None:
    selection = PeriodSelection(granularity="day", year=2026, month=4, quarter=2)
    transactions = [
        _period_txn("apr-income", "2026-04-05", "收入", "800.00"),
        _period_txn("apr-expense", "2026-04-05", "支出", "300.00"),
        _period_txn("apr-refund", "2026-04-06", "退款", "80.00"),
        _period_txn("apr-pending", "2026-04-07", "支出", "400.00", "待确认"),
        _period_txn("may-expense", "2026-05-01", "支出", "999.00"),
    ]

    trend = build_daily_trend(selection, transactions)

    assert len(trend) == 30
    assert trend[0].month_key == "2026-04-01"
    assert trend[0].label == "1日"
    assert trend[4].income == Decimal("800.00")
    assert trend[4].expense == Decimal("300.00")
    assert trend[4].balance == Decimal("500.00")
    assert trend[5].expense == Decimal("-80.00")
    assert trend[6].expense == Decimal("0.00")
    assert trend[6].pending_amount == Decimal("400.00")


def test_collect_due_reminders_supports_threshold_and_date_rules() -> None:
    accounts = [
        Account(
            id="acc-api",
            name="OpenAI API",
            account_type="API 余额",
            currency="USD",
            purpose="AI 工具",
            status="正常",
            notes="",
            source="手动录入",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    ]
    snapshots = [
        BalanceSnapshot(
            id="snap-api",
            account_id="acc-api",
            snapshot_time="2026-04-15T18:00:00",
            amount="8.50",
            status="已确认",
            source="手动回查",
            notes="",
            created_at="2026-04-15T18:00:00",
        )
    ]
    reminders = [
        ReminderItem(
            id="rem-threshold",
            title="API 余额充值",
            reminder_kind="阈值提醒",
            target_type="账户余额",
            account_id="acc-api",
            due_date="",
            threshold_amount="10.00",
            current_value="",
            status="启用",
            source="手动录入",
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        ),
        ReminderItem(
            id="rem-date-due",
            title="iCloud 会员续费",
            reminder_kind="日期提醒",
            target_type="会员续费",
            account_id="",
            due_date="2026-04-26",
            threshold_amount="",
            current_value="",
            status="启用",
            source="手动录入",
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        ),
        ReminderItem(
            id="rem-date-late",
            title="云服务续费",
            reminder_kind="日期提醒",
            target_type="云服务",
            account_id="",
            due_date="2026-05-15",
            threshold_amount="",
            current_value="",
            status="启用",
            source="手动录入",
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        ),
    ]

    due = collect_due_reminders(
        reminders=reminders,
        accounts=accounts,
        snapshots=snapshots,
        transactions=[],
        today="2026-04-20",
        lead_days=7,
    )

    assert [item.title for item in due] == ["API 余额充值", "iCloud 会员续费"]
