from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


def now_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass
class Account:
    id: str
    name: str
    account_type: str
    currency: str
    purpose: str
    status: str
    notes: str
    source: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BalanceSnapshot:
    id: str
    account_id: str
    snapshot_time: str
    amount: str
    status: str
    source: str
    notes: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Transaction:
    id: str
    occurred_on: str
    transaction_type: str
    category: str
    amount: str
    from_account_id: str
    to_account_id: str
    status: str
    source: str
    notes: str
    related_transaction_id: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonthlyBudget:
    id: str
    month_key: str
    total_budget: str
    notes: str
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetLine:
    id: str
    budget_id: str
    line_kind: str
    name: str
    category: str
    planned_amount: str
    day_of_month: int | None
    is_required: bool
    reminder_days: int
    notes: str
    created_at: str
    updated_at: str
    effective_start_month: str = ""
    effective_end_month: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReminderItem:
    id: str
    title: str
    reminder_kind: str
    target_type: str
    account_id: str
    due_date: str
    threshold_amount: str
    current_value: str
    status: str
    source: str
    notes: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AppSettings:
    data_dir: str
    export_dir: str
    backup_dir: str
    default_currency: str
    reminder_lead_days: int
    obsidian_path: str
    minimax_api_host: str = "https://api.minimaxi.com/v1"
    minimax_model: str = "MiniMax-M2.7"
    minimax_key_configured: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportBatch:
    id: str
    source_file_path: str
    original_file_name: str
    raw_ocr_text: str
    structured_json: str
    status: str
    error_message: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonthlySummary:
    month_key: str
    total_budget: Any
    actual_expense: Any
    remaining_budget: Any
    pending_amount: Any
    by_category: dict[str, Any]


@dataclass
class BudgetLineComparison:
    line_id: str
    group_name: str
    line_kind: str
    name: str
    category: str
    notes: str
    effective_start_month: str
    effective_end_month: str
    planned_amount: Any
    actual_amount: Any
    pending_amount: Any
    delta_amount: Any
    progress_ratio: Any
    status: str


@dataclass
class BudgetComparisonSummary:
    month_key: str
    planned_income: Any
    actual_income: Any
    planned_expense: Any
    actual_expense: Any
    planned_balance: Any
    actual_balance: Any
    pending_amount: Any


@dataclass
class BudgetComparison:
    month_key: str
    summary: BudgetComparisonSummary
    rows: list[BudgetLineComparison]


@dataclass
class AnnualBudgetMonthPoint:
    month_key: str
    planned_income: Any
    actual_income: Any
    planned_expense: Any
    actual_expense: Any
    planned_balance: Any
    actual_balance: Any
    pending_amount: Any


@dataclass
class AnnualBudgetDetailRow:
    row_key: str
    group_name: str
    line_kind: str
    name: str
    category: str
    notes: str
    effective_start_month: str
    effective_end_month: str
    planned_months: list[Any]
    actual_months: list[Any]
    pending_months: list[Any]
    planned_total: Any
    actual_total: Any
    pending_total: Any
    delta_total: Any
    status: str


@dataclass
class AnnualBudgetMatrix:
    year: int
    months: list[AnnualBudgetMonthPoint]
    planned_income: Any
    actual_income: Any
    planned_expense: Any
    actual_expense: Any
    planned_balance: Any
    actual_balance: Any
    pending_amount: Any
    detail_rows: list[AnnualBudgetDetailRow] = field(default_factory=list)


@dataclass
class PeriodSelection:
    granularity: str
    year: int
    month: int
    quarter: int


@dataclass
class PeriodSummary:
    label: str
    income: Any
    expense: Any
    balance: Any
    pending_amount: Any
    transaction_count: int
    pending_count: int


@dataclass
class MonthlyTrendPoint:
    month_key: str
    income: Any
    expense: Any
    balance: Any


@dataclass
class ResolvedReminder:
    id: str
    title: str
    reminder_kind: str
    target_type: str
    account_id: str
    due_date: str
    threshold_amount: str
    current_value: str
    status: str
    source: str
    notes: str
    display_status: str
    tone: str
