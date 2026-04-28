from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from private_ledger.domain.models import (
    Account,
    AnnualBudgetDetailRow,
    AnnualBudgetMatrix,
    AnnualBudgetMonthPoint,
    BalanceSnapshot,
    BudgetComparison,
    BudgetComparisonSummary,
    BudgetLine,
    BudgetLineComparison,
    MonthlyTrendPoint,
    MonthlyBudget,
    MonthlySummary,
    PeriodSelection,
    PeriodSummary,
    ReminderItem,
    ResolvedReminder,
    Transaction,
)


TWOPLACES = Decimal("0.01")


def parse_decimal(value: str | int | float | Decimal | None) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def format_money(value: str | int | float | Decimal | None, currency: str = "CNY") -> str:
    amount = parse_decimal(value)
    symbol = "$" if currency == "USD" else "¥"
    return f"{symbol}{amount:,.2f}"


def calculate_account_balance(
    account: Account,
    snapshots: list[BalanceSnapshot],
    transactions: list[Transaction],
) -> Decimal:
    confirmed_snapshots = [
        item for item in snapshots
        if item.account_id == account.id and item.status == "已确认"
    ]
    latest_snapshot = max(
        confirmed_snapshots,
        key=lambda item: item.snapshot_time,
        default=None,
    )
    balance = parse_decimal(latest_snapshot.amount if latest_snapshot else "0.00")
    snapshot_day = latest_snapshot.snapshot_time[:10] if latest_snapshot else ""

    for transaction in transactions:
        if transaction.status != "已确认":
            continue
        if snapshot_day and transaction.occurred_on < snapshot_day:
            continue
        amount = parse_decimal(transaction.amount)
        if transaction.transaction_type == "收入" and transaction.to_account_id == account.id:
            balance += amount
        elif transaction.transaction_type == "支出" and transaction.from_account_id == account.id:
            balance -= amount
        elif transaction.transaction_type in {"转账", "充值", "调整"}:
            if transaction.from_account_id == account.id:
                balance -= amount
            if transaction.to_account_id == account.id:
                balance += amount
        elif transaction.transaction_type == "退款" and transaction.to_account_id == account.id:
            balance += amount
    return balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def build_month_summary(
    month_key: str,
    budget: MonthlyBudget | None,
    transactions: list[Transaction],
    total_budget_override: Decimal | None = None,
) -> MonthlySummary:
    total_budget = total_budget_override if total_budget_override is not None else parse_decimal(budget.total_budget if budget else "0.00")
    actual_expense = Decimal("0.00")
    pending_amount = Decimal("0.00")
    by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for transaction in transactions:
        if not transaction.occurred_on.startswith(month_key):
            continue
        amount = parse_decimal(transaction.amount)
        category = transaction.category or "未分类"
        if transaction.status != "已确认":
            if transaction.transaction_type == "支出":
                pending_amount += amount
            continue
        if transaction.transaction_type == "支出":
            actual_expense += amount
            by_category[category] += amount
        elif transaction.transaction_type == "退款":
            actual_expense -= amount
            by_category[category] -= amount

    remaining_budget = total_budget - actual_expense
    return MonthlySummary(
        month_key=month_key,
        total_budget=total_budget.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_expense=actual_expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        remaining_budget=remaining_budget.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        pending_amount=pending_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        by_category={key: value.quantize(TWOPLACES, rounding=ROUND_HALF_UP) for key, value in by_category.items()},
    )


def _budget_match_key(line: BudgetLine) -> str:
    return (line.category or line.name or "未分类").strip() or "未分类"


def _budget_group_name(line_kind: str) -> str:
    if line_kind == "收入":
        return "收入计划"
    if line_kind == "固定支出":
        return "固定支出"
    if line_kind == "储蓄计划":
        return "储蓄计划"
    return "支出预算"


def _is_expense_budget_kind(line_kind: str) -> bool:
    return line_kind in {"分类预算", "固定支出", "储蓄计划", "支出"}


def _budget_status(line_kind: str, planned: Decimal, actual: Decimal, pending: Decimal, notes: str = "") -> str:
    if "草稿待调整" in notes:
        return "草稿待调整"
    if planned <= Decimal("0.00"):
        return "未设预算" if actual or pending else "待设置"
    if pending and not actual:
        return "有待确认"
    ratio = actual / planned if planned else Decimal("0.00")
    if line_kind == "收入":
        if actual >= planned:
            return "已达成"
        if actual > Decimal("0.00"):
            return "进行中"
        return "未发生"
    if actual > planned:
        return "超支"
    if ratio >= Decimal("0.90"):
        return "临界"
    if actual > Decimal("0.00"):
        return "进行中"
    return "未发生"


def _empty_annual_amounts() -> list[Decimal]:
    return [Decimal("0.00") for _ in range(12)]


def _annual_detail_row_key(row: BudgetLineComparison) -> str:
    if row.line_id:
        return row.line_id
    category = (row.category or row.name or "未分类").strip() or "未分类"
    return f"{row.line_kind}:{category}"


def _annual_detail_status(
    line_kind: str,
    planned_total: Decimal,
    actual_total: Decimal,
    pending_total: Decimal,
) -> str:
    if pending_total:
        return "有待确认"
    if planned_total == Decimal("0.00") and (actual_total or pending_total):
        return "未设预算"
    if line_kind == "收入" and planned_total > Decimal("0.00"):
        if actual_total >= planned_total:
            return "已达成"
        if actual_total:
            return "进行中"
        return "未发生"
    if _is_expense_budget_kind(line_kind) and planned_total > Decimal("0.00"):
        if actual_total > planned_total:
            return "超支"
        if actual_total:
            return "进行中"
        return "未发生"
    if actual_total:
        return "进行中"
    return "未发生"


def _annual_detail_delta_total(
    line_kind: str,
    planned_total: Decimal,
    actual_total: Decimal,
) -> Decimal:
    if line_kind == "收入":
        return (actual_total - planned_total).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
    if _is_expense_budget_kind(line_kind):
        return (planned_total - actual_total).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
    return (actual_total - planned_total).quantize(
        TWOPLACES,
        rounding=ROUND_HALF_UP,
    )


def _finalize_annual_detail_rows(
    detail_rows_by_key: dict[str, AnnualBudgetDetailRow],
) -> list[AnnualBudgetDetailRow]:
    group_order = {
        "收入计划": 0,
        "支出预算": 1,
        "固定支出": 2,
        "储蓄计划": 3,
        "未设预算但本月有实际": 4,
    }
    detail_rows = list(detail_rows_by_key.values())
    for row in detail_rows:
        row.planned_total = sum(row.planned_months, Decimal("0.00")).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
        row.actual_total = sum(row.actual_months, Decimal("0.00")).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
        row.pending_total = sum(row.pending_months, Decimal("0.00")).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
        row.delta_total = _annual_detail_delta_total(
            row.line_kind,
            row.planned_total,
            row.actual_total,
        )
        row.status = _annual_detail_status(
            row.line_kind,
            row.planned_total,
            row.actual_total,
            row.pending_total,
        )
    return sorted(
        detail_rows,
        key=lambda row: (
            group_order.get(row.group_name, 99),
            row.line_kind,
            row.name,
            row.row_key,
        ),
    )


def build_budget_comparison(
    month_key: str,
    budget_lines: list[BudgetLine],
    transactions: list[Transaction],
) -> BudgetComparison:
    planned_income = Decimal("0.00")
    planned_expense = Decimal("0.00")
    actual_income = Decimal("0.00")
    actual_expense = Decimal("0.00")
    pending_total = Decimal("0.00")
    actual_by_type_category: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    pending_by_type_category: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))

    for transaction in transactions:
        if not transaction.occurred_on.startswith(month_key):
            continue
        if transaction.transaction_type not in {"收入", "支出", "退款"}:
            continue
        amount = parse_decimal(transaction.amount)
        category = (transaction.category or "未分类").strip() or "未分类"

        if transaction.status != "已确认":
            if transaction.transaction_type in {"收入", "支出"}:
                pending_total += amount
                pending_by_type_category[(transaction.transaction_type, category)] += amount
            continue

        if transaction.transaction_type == "收入":
            actual_income += amount
            actual_by_type_category[("收入", category)] += amount
        elif transaction.transaction_type == "支出":
            actual_expense += amount
            actual_by_type_category[("支出", category)] += amount
        elif transaction.transaction_type == "退款":
            actual_expense -= amount
            actual_by_type_category[("支出", category)] -= amount

    rows: list[BudgetLineComparison] = []
    matched_keys: set[tuple[str, str]] = set()

    for line in budget_lines:
        planned = parse_decimal(line.planned_amount)
        match_type = "收入" if line.line_kind == "收入" else "支出"
        match_key = _budget_match_key(line)
        actual = actual_by_type_category[(match_type, match_key)]
        pending = pending_by_type_category[(match_type, match_key)]
        if line.line_kind == "收入":
            planned_income += planned
        elif _is_expense_budget_kind(line.line_kind):
            planned_expense += planned
        matched_keys.add((match_type, match_key))

        progress = (actual / planned).quantize(TWOPLACES, rounding=ROUND_HALF_UP) if planned else Decimal("0.00")
        rows.append(
            BudgetLineComparison(
                line_id=line.id,
                group_name=_budget_group_name(line.line_kind),
                line_kind=line.line_kind,
                name=line.name,
                category=match_key,
                notes=line.notes,
                effective_start_month=line.effective_start_month,
                effective_end_month=line.effective_end_month,
                planned_amount=planned.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                actual_amount=actual.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                pending_amount=pending.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                delta_amount=(actual - planned).quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                progress_ratio=progress,
                status=_budget_status(line.line_kind, planned, actual, pending, line.notes),
            )
        )

    for (transaction_type, category), actual in sorted(actual_by_type_category.items()):
        pending = pending_by_type_category[(transaction_type, category)]
        if (transaction_type, category) in matched_keys:
            continue
        if actual == Decimal("0.00") and pending == Decimal("0.00"):
            continue
        line_kind = "收入" if transaction_type == "收入" else "分类预算"
        rows.append(
            BudgetLineComparison(
                line_id="",
                group_name="未设预算但本月有实际",
                line_kind=line_kind,
                name=category,
                category=category,
                notes="未设预算，来自本月实际流水。",
                effective_start_month=month_key,
                effective_end_month=month_key,
                planned_amount=Decimal("0.00"),
                actual_amount=actual.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                pending_amount=pending.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                delta_amount=actual.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                progress_ratio=Decimal("0.00"),
                status="未设预算",
            )
        )

    for (transaction_type, category), pending in sorted(pending_by_type_category.items()):
        if (transaction_type, category) in matched_keys or (transaction_type, category) in actual_by_type_category:
            continue
        if pending == Decimal("0.00"):
            continue
        line_kind = "收入" if transaction_type == "收入" else "分类预算"
        rows.append(
            BudgetLineComparison(
                line_id="",
                group_name="未设预算但本月有实际",
                line_kind=line_kind,
                name=category,
                category=category,
                notes="未设预算，仅有待确认流水。",
                effective_start_month=month_key,
                effective_end_month=month_key,
                planned_amount=Decimal("0.00"),
                actual_amount=Decimal("0.00"),
                pending_amount=pending.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
                delta_amount=Decimal("0.00"),
                progress_ratio=Decimal("0.00"),
                status="有待确认",
            )
        )

    group_order = {
        "收入计划": 0,
        "支出预算": 1,
        "固定支出": 2,
        "储蓄计划": 3,
        "未设预算但本月有实际": 4,
    }
    rows.sort(key=lambda row: (group_order.get(row.group_name, 99), row.line_kind, row.name))
    summary = BudgetComparisonSummary(
        month_key=month_key,
        planned_income=planned_income.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_income=actual_income.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        planned_expense=planned_expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_expense=actual_expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        planned_balance=(planned_income - planned_expense).quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_balance=(actual_income - actual_expense).quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        pending_amount=pending_total.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
    )
    return BudgetComparison(month_key=month_key, summary=summary, rows=rows)


def is_budget_line_effective_in_month(line: BudgetLine, month_key: str) -> bool:
    start_month = line.effective_start_month.strip()
    end_month = line.effective_end_month.strip()
    if start_month and month_key < start_month:
        return False
    if end_month and month_key > end_month:
        return False
    return True


def build_annual_budget_matrix(
    year: int,
    budget_lines: list[BudgetLine],
    transactions: list[Transaction],
) -> AnnualBudgetMatrix:
    month_points: list[AnnualBudgetMonthPoint] = []
    detail_rows_by_key: dict[str, AnnualBudgetDetailRow] = {}
    planned_income = Decimal("0.00")
    actual_income = Decimal("0.00")
    planned_expense = Decimal("0.00")
    actual_expense = Decimal("0.00")
    planned_balance = Decimal("0.00")
    actual_balance = Decimal("0.00")
    pending_amount = Decimal("0.00")

    for month in range(1, 13):
        month_key = f"{year:04d}-{month:02d}"
        active_lines = [
            line for line in budget_lines
            if is_budget_line_effective_in_month(line, month_key)
        ]
        comparison = build_budget_comparison(month_key, active_lines, transactions)
        summary = comparison.summary
        month_points.append(
            AnnualBudgetMonthPoint(
                month_key=month_key,
                planned_income=summary.planned_income,
                actual_income=summary.actual_income,
                planned_expense=summary.planned_expense,
                actual_expense=summary.actual_expense,
                planned_balance=summary.planned_balance,
                actual_balance=summary.actual_balance,
                pending_amount=summary.pending_amount,
            )
        )
        for comparison_row in comparison.rows:
            row_key = _annual_detail_row_key(comparison_row)
            detail_row = detail_rows_by_key.get(row_key)
            if detail_row is None:
                detail_row = AnnualBudgetDetailRow(
                    row_key=row_key,
                    group_name=comparison_row.group_name,
                    line_kind=comparison_row.line_kind,
                    name=comparison_row.name,
                    category=comparison_row.category,
                    notes=comparison_row.notes,
                    effective_start_month=comparison_row.effective_start_month,
                    effective_end_month=comparison_row.effective_end_month,
                    planned_months=_empty_annual_amounts(),
                    actual_months=_empty_annual_amounts(),
                    pending_months=_empty_annual_amounts(),
                    planned_total=Decimal("0.00"),
                    actual_total=Decimal("0.00"),
                    pending_total=Decimal("0.00"),
                    delta_total=Decimal("0.00"),
                    status="未发生",
                )
                detail_rows_by_key[row_key] = detail_row

            month_index = month - 1
            detail_row.planned_months[month_index] = (
                detail_row.planned_months[month_index]
                + parse_decimal(comparison_row.planned_amount)
            ).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
            detail_row.actual_months[month_index] = (
                detail_row.actual_months[month_index]
                + parse_decimal(comparison_row.actual_amount)
            ).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
            detail_row.pending_months[month_index] = (
                detail_row.pending_months[month_index]
                + parse_decimal(comparison_row.pending_amount)
            ).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

            if not comparison_row.line_id:
                row_start = comparison_row.effective_start_month or month_key
                row_end = comparison_row.effective_end_month or month_key
                if not detail_row.effective_start_month or row_start < detail_row.effective_start_month:
                    detail_row.effective_start_month = row_start
                if not detail_row.effective_end_month or row_end > detail_row.effective_end_month:
                    detail_row.effective_end_month = row_end
        planned_income += summary.planned_income
        actual_income += summary.actual_income
        planned_expense += summary.planned_expense
        actual_expense += summary.actual_expense
        planned_balance += summary.planned_balance
        actual_balance += summary.actual_balance
        pending_amount += summary.pending_amount

    return AnnualBudgetMatrix(
        year=year,
        months=month_points,
        planned_income=planned_income.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_income=actual_income.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        planned_expense=planned_expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_expense=actual_expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        planned_balance=planned_balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        actual_balance=actual_balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        pending_amount=pending_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        detail_rows=_finalize_annual_detail_rows(detail_rows_by_key),
    )


def period_label(selection: PeriodSelection) -> str:
    if selection.granularity == "month":
        return f"{selection.year:04d}-{selection.month:02d}"
    if selection.granularity == "quarter":
        return f"{selection.year:04d} Q{selection.quarter}"
    return f"{selection.year:04d}"


def period_month_keys(selection: PeriodSelection) -> list[str]:
    if selection.granularity == "month":
        return [f"{selection.year:04d}-{selection.month:02d}"]
    if selection.granularity == "quarter":
        start_month = (selection.quarter - 1) * 3 + 1
        return [f"{selection.year:04d}-{month:02d}" for month in range(start_month, start_month + 3)]
    return [f"{selection.year:04d}-{month:02d}" for month in range(1, 13)]


def build_period_summary(selection: PeriodSelection, transactions: list[Transaction]) -> PeriodSummary:
    month_keys = set(period_month_keys(selection))
    income = Decimal("0.00")
    expense = Decimal("0.00")
    pending_amount = Decimal("0.00")
    transaction_count = 0
    pending_count = 0

    for transaction in transactions:
        if transaction.occurred_on[:7] not in month_keys:
            continue
        transaction_count += 1
        amount = parse_decimal(transaction.amount)
        if transaction.status != "已确认":
            if transaction.transaction_type in {"收入", "支出"}:
                pending_amount += amount
                pending_count += 1
            continue
        if transaction.transaction_type == "收入":
            income += amount
        elif transaction.transaction_type == "支出":
            expense += amount
        elif transaction.transaction_type == "退款":
            expense -= amount

    balance = income - expense
    return PeriodSummary(
        label=period_label(selection),
        income=income.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        expense=expense.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        balance=balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        pending_amount=pending_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        transaction_count=transaction_count,
        pending_count=pending_count,
    )


def build_monthly_trend(selection: PeriodSelection, transactions: list[Transaction]) -> list[MonthlyTrendPoint]:
    points = []
    for month_key in period_month_keys(selection):
        month_selection = PeriodSelection(
            granularity="month",
            year=int(month_key[:4]),
            month=int(month_key[5:7]),
            quarter=(int(month_key[5:7]) - 1) // 3 + 1,
        )
        summary = build_period_summary(month_selection, transactions)
        points.append(
            MonthlyTrendPoint(
                month_key=month_key,
                income=summary.income,
                expense=summary.expense,
                balance=summary.balance,
            )
        )
    return points


def collect_due_reminders(
    reminders: list[ReminderItem],
    accounts: list[Account],
    snapshots: list[BalanceSnapshot],
    transactions: list[Transaction],
    today: str | None = None,
    lead_days: int = 7,
) -> list[ResolvedReminder]:
    today_value = date.fromisoformat(today) if today else date.today()
    due_by = today_value + timedelta(days=max(0, int(lead_days)))
    account_map = {account.id: account for account in accounts}
    balances = {
        account.id: calculate_account_balance(account, snapshots, transactions)
        for account in accounts
    }

    results: list[ResolvedReminder] = []
    for reminder in reminders:
        if reminder.status != "启用":
            continue
        if reminder.reminder_kind == "阈值提醒":
            current = parse_decimal(reminder.current_value)
            if reminder.account_id and reminder.account_id in account_map and not reminder.current_value:
                current = balances.get(reminder.account_id, Decimal("0.00"))
            threshold = parse_decimal(reminder.threshold_amount)
            if current <= threshold:
                results.append(
                    ResolvedReminder(
                        id=reminder.id,
                        title=reminder.title,
                        reminder_kind=reminder.reminder_kind,
                        target_type=reminder.target_type,
                        account_id=reminder.account_id,
                        due_date=reminder.due_date,
                        threshold_amount=f"{threshold:.2f}",
                        current_value=f"{current:.2f}",
                        status=reminder.status,
                        source=reminder.source,
                        notes=reminder.notes,
                        display_status="低余额",
                        tone="red",
                    )
                )
        elif reminder.reminder_kind == "日期提醒" and reminder.due_date:
            due_date = date.fromisoformat(reminder.due_date)
            if due_date <= due_by:
                tone = "amber" if due_date > today_value else "red"
                results.append(
                    ResolvedReminder(
                        id=reminder.id,
                        title=reminder.title,
                        reminder_kind=reminder.reminder_kind,
                        target_type=reminder.target_type,
                        account_id=reminder.account_id,
                        due_date=reminder.due_date,
                        threshold_amount=reminder.threshold_amount,
                        current_value=reminder.current_value,
                        status=reminder.status,
                        source=reminder.source,
                        notes=reminder.notes,
                        display_status="临近到期",
                        tone=tone,
                    )
                )
    return sorted(
        results,
        key=lambda item: (
            0 if item.reminder_kind == "阈值提醒" else 1,
            item.due_date or "9999-99-99",
            item.title,
        ),
    )
