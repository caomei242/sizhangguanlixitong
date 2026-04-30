# Dashboard Period Trend Implementation Plan

## Status

Implemented and superseded by later dashboard refinements. The original plan added `月 / 季 / 年` period switching; the current application also supports `日` range selection and daily trend points. Confirmed income, expense, and balance remain conservative; pending transactions are shown separately and do not enter formal totals. For current architecture, see `docs/architecture.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `月 / 季 / 年` period switching to the existing dashboard and show a quarter/year monthly trend cockpit with confirmed income, expense, balance, and pending totals.

**Architecture:** Add pure period aggregation functions in `private_ledger.domain.ledger`, then render the results in `DashboardPage` using `PySide6.QtCharts`. `MainWindow` owns period selection state and adapts existing dashboard loading without changing storage schema.

**Tech Stack:** Python 3.9, PySide6, PySide6.QtCharts, SQLite-backed repository, pytest with `QT_QPA_PLATFORM=offscreen`.

---

## Files

- Modify: `src/private_ledger/domain/models.py`
  - Add `PeriodSelection`, `PeriodSummary`, `MonthlyTrendPoint`.
- Modify: `src/private_ledger/domain/ledger.py`
  - Add period range and aggregation helpers.
- Modify: `src/private_ledger/ui/pages/dashboard_page.py`
  - Add trend chart area and support period summary payloads.
- Modify: `src/private_ledger/ui/main_window.py`
  - Add `月 / 季 / 年` selector behavior and wire period summary into dashboard.
- Modify: `src/private_ledger/ui/theme.py`
  - Add minimal chart/card spacing style if needed.
- Test: `tests/test_ledger.py`
  - Add period aggregation tests.
- Test: `tests/ui/test_main_window.py`
  - Add UI smoke tests for period selector and year dashboard values.

---

### Task 1: Period Aggregation Domain Layer

**Files:**
- Modify: `src/private_ledger/domain/models.py`
- Modify: `src/private_ledger/domain/ledger.py`
- Test: `tests/test_ledger.py`

- [ ] **Step 1: Write failing tests**

Append tests to `tests/test_ledger.py`:

```python
from private_ledger.domain.ledger import build_monthly_trend, build_period_summary
from private_ledger.domain.models import PeriodSelection


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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_ledger.py -q
```

Expected: import failure for `build_period_summary`, `build_monthly_trend`, or `PeriodSelection`.

- [ ] **Step 3: Add dataclasses**

Add to `src/private_ledger/domain/models.py`:

```python
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
```

- [ ] **Step 4: Add period helper implementation**

Add functions to `src/private_ledger/domain/ledger.py`:

```python
def period_month_keys(selection: PeriodSelection) -> list[str]:
    if selection.granularity == "month":
        return [f"{selection.year:04d}-{selection.month:02d}"]
    if selection.granularity == "quarter":
        start_month = (selection.quarter - 1) * 3 + 1
        return [f"{selection.year:04d}-{month:02d}" for month in range(start_month, start_month + 3)]
    return [f"{selection.year:04d}-{month:02d}" for month in range(1, 13)]
```

Then implement:

```python
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
```

Also implement `build_monthly_trend(selection, transactions)` returning one `MonthlyTrendPoint` per selected month.

- [ ] **Step 5: Run domain tests to verify GREEN**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_ledger.py -q
```

Expected: all tests in `tests/test_ledger.py` pass.

---

### Task 2: Dashboard Trend UI

**Files:**
- Modify: `src/private_ledger/ui/pages/dashboard_page.py`
- Test: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write failing UI smoke test**

Append to `tests/ui/test_main_window.py`:

```python
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

    window.close()
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_main_window.py::test_dashboard_period_controls_show_year_summary -q
```

Expected: failure because `period_granularity_combo`, `income_card`, or trend widgets do not exist.

- [ ] **Step 3: Add trend widgets**

In `src/private_ledger/ui/pages/dashboard_page.py`:

- Import QtCharts classes.
- Add four cards:
  - `income_card`
  - `expense_card`
  - `balance_card`
  - `pending_amount_card`
- Keep budget cards only for month mode if needed, or replace visible dashboard cards with the new period cards.
- Add a `PeriodTrendChart` wrapper widget with:

```python
def load_points(self, points: list[MonthlyTrendPoint]) -> None:
    ...

def series_count_for_test(self) -> int:
    return len(self.chart.series())
```

- Add `trend_table` with headers `月份 / 收入 / 支出 / 结余`.

- [ ] **Step 4: Add DashboardPage loader support**

Add `load_period_snapshot(payload)` or extend `load_snapshot(payload)` so the dashboard can set:

- top cards from `period_summary`
- trend chart and trend table from `trend_points`
- existing accounts/reminders/transactions/pending sections unchanged

- [ ] **Step 5: Run UI test to verify widgets still fail only on wiring**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_main_window.py::test_dashboard_period_controls_show_year_summary -q
```

Expected: remaining failure should be in `MainWindow` period controls or data wiring, not missing dashboard attributes.

---

### Task 3: MainWindow Period Selection Wiring

**Files:**
- Modify: `src/private_ledger/ui/main_window.py`
- Test: `tests/ui/test_main_window.py`

- [ ] **Step 1: Add period controls to MainWindow**

Add:

```python
self.period_granularity_combo = QComboBox()
self.period_granularity_combo.addItems(["月", "季", "年"])
self.period_value_combo = QComboBox()
```

Place them in the header before export.

- [ ] **Step 2: Add selection conversion helpers**

Implement:

```python
def _current_period_selection(self) -> PeriodSelection:
    ...

def _refresh_period_choices(self, transactions: list[Transaction], budget: MonthlyBudget | None) -> None:
    ...

def _handle_period_granularity_changed(self, text: str) -> None:
    ...

def _handle_period_value_changed(self, text: str) -> None:
    ...
```

Rules:

- `月`: choices are `YYYY-MM`, same behavior as old month combo.
- `季`: choices are `YYYY Q1` through `YYYY Q4` for years seen in transactions and current year.
- `年`: choices are years seen in transactions and current year.
- Default remains current month.

- [ ] **Step 3: Wire refresh_data**

In `refresh_data`:

- Build `selection = self._current_period_selection()`.
- Use `build_period_summary(selection, transactions)`.
- Use `build_monthly_trend(selection, transactions)`.
- Use monthly budget only when `selection.granularity == "month"`.
- Keep existing month budget page behavior based on selected month.

- [ ] **Step 4: Run UI smoke test to verify GREEN**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_main_window.py::test_dashboard_period_controls_show_year_summary -q
```

Expected: test passes.

- [ ] **Step 5: Run full UI tests**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Expected: all UI tests pass.

---

### Task 4: Verification and Development Log

**Files:**
- Modify: `/Users/gd/Library/Mobile Documents/iCloud~md~obsidian/Documents/项目管理/草莓私帐管理系统--个人/开发/2026-04-23.md`

- [ ] **Step 1: Run full tests**

Run:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run:

```bash
PYTHONPATH=src python3 -m compileall -q src tests
```

Expected: exit code 0.

- [ ] **Step 3: Run offscreen dashboard smoke**

Run:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - <<'PY'
from private_ledger.app import build_app
app, window = build_app()
window.period_granularity_combo.setCurrentText("年")
window.period_value_combo.setCurrentText("2026")
app.processEvents()
print("title", window.windowTitle())
print("granularity", window.period_granularity_combo.currentText())
print("period", window.period_value_combo.currentText())
print("income", window.dashboard_page.income_card.value_label.text())
print("expense", window.dashboard_page.expense_card.value_label.text())
print("balance", window.dashboard_page.balance_card.value_label.text())
print("pending", window.dashboard_page.pending_amount_card.value_label.text())
print("trend_rows", window.dashboard_page.trend_table.rowCount())
window.close()
PY
```

Expected:

- title is `草莓私帐管理系统`
- granularity is `年`
- period is `2026`
- trend_rows is `12`

- [ ] **Step 4: Update development log**

Append the implementation result to:

```text
/Users/gd/Library/Mobile Documents/iCloud~md~obsidian/Documents/项目管理/草莓私帐管理系统--个人/开发/2026-04-23.md
```

Include:

- implemented `月 / 季 / 年` dashboard switch
- `B 趋势驾驶舱` layout
- tests/compile/offscreen smoke results
- any known limitations
