from __future__ import annotations

from pathlib import Path

from private_ledger.services.obsidian_sync import (
    ObsidianLedgerSyncService,
    parse_daily_note,
    parse_monthly_budget,
)
from private_ledger.domain.models import BudgetLine, MonthlyBudget
from private_ledger.storage.repository import LedgerRepository


def write_private_ledger_files(root: Path, daily_content: str, monthly_content: str) -> None:
    daily_dir = root / "财务" / "私帐" / "每日收集"
    monthly_dir = root / "财务" / "私帐" / "预期与实际"
    daily_dir.mkdir(parents=True, exist_ok=True)
    monthly_dir.mkdir(parents=True, exist_ok=True)
    (daily_dir / "2026-04-21.md").write_text(daily_content, encoding="utf-8")
    (monthly_dir / "2026-04-预期与实际.md").write_text(monthly_content, encoding="utf-8")


def test_parse_daily_note_extracts_transactions_and_attachment(tmp_path) -> None:
    note_path = tmp_path / "2026-04-21.md"
    note_path.write_text(
        """日期：2026年04月21日 周二

## 收入明细

**标签：店铺保证金**

- 今日合计：100.00 元
- 10:00｜100.00 元｜支付宝

## 支出明细

**标签：日常零花**

- 今日合计：12.34 元
- 09:00｜12.34 元｜花小猪打车

## 金额变动

- 回扫命中：`2026-04-21`

## 备注

- 数据来源：备忘录 `账单_202604220941.xlsx`
""",
        encoding="utf-8",
    )

    parsed = parse_daily_note(note_path)

    assert parsed.source_attachment == "账单_202604220941.xlsx"
    assert len(parsed.transactions) == 2
    assert parsed.transactions[0].transaction_type == "收入"
    assert parsed.transactions[1].category == "日常零花"
    assert parsed.transactions[1].has_rescan is True
    assert parsed.skipped_lines == []


def test_parse_monthly_budget_skips_non_numeric_expected_rows(tmp_path) -> None:
    note_path = tmp_path / "2026-04-预期与实际.md"
    note_path.write_text(
        """日期：2026年04月21日 截止

## 总览

- 预期收入：15741.00 元
- 实际收入：20531.19 元
- 预期支出：11900.00 元
- 实际支出：16944.03 元
- 预期结余：3841.00 元
- 实际结余：3587.16 元

## 收入预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 工资 | 1000.00 | 1000.00 | 0.00 |
| 其他 | - | 100.00 | - |
| 合计 | 1000.00 | 1100.00 | +100.00 |

## 支出预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 日常零花 | 3000.00 | 3324.64 | +324.64 |
| 约会 | 1000.00 | 471.18 | -528.82 |
| 其他提前知道的开支2 | - | 0.00 | - |
| 合计 | 4000.00 | 3795.82 | -204.18 |
""",
        encoding="utf-8",
    )

    parsed = parse_monthly_budget(note_path)

    assert parsed.total_budget == "11900.00"
    assert [item.name for item in parsed.income_lines] == ["工资"]
    assert [item.name for item in parsed.expense_lines] == ["日常零花", "约会"]


def test_obsidian_sync_is_idempotent_updates_changed_rows_and_reports_deletion_candidates(tmp_path) -> None:
    obsidian_root = tmp_path / "obsidian"
    db_dir = tmp_path / "db"
    repo = LedgerRepository(db_dir)
    service = ObsidianLedgerSyncService(repo)

    daily_content = """日期：2026年04月21日 周二

## 收入明细

- 今日无收入流水

## 支出明细

**标签：日常零花**

- 今日合计：20.00 元
- 09:00｜12.00 元｜花小猪打车
- 10:00｜8.00 元｜Valve

## 红灯预警

- 日常零花：已超预算｜当前 3324.64 / 3000.00 元｜已花 110.82%

## 备注

- 数据来源：备忘录 `账单_202604220941.xlsx`
"""
    monthly_content = """日期：2026年04月21日 截止

## 总览

- 预期收入：15741.00 元
- 实际收入：20531.19 元
- 预期支出：11900.00 元
- 实际支出：16944.03 元
- 预期结余：3841.00 元
- 实际结余：3587.16 元

## 收入预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 工资 | 1000.00 | 1000.00 | 0.00 |
| 合计 | 1000.00 | 1000.00 | 0.00 |

## 支出预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 日常零花 | 3000.00 | 3324.64 | +324.64 |
| 约会 | 1000.00 | 950.00 | -50.00 |
| 合计 | 4000.00 | 4274.64 | +274.64 |
"""
    write_private_ledger_files(obsidian_root, daily_content, monthly_content)

    first_report = service.sync(obsidian_root=obsidian_root)
    first_transactions = repo.list_transactions()
    first_budget = repo.get_monthly_budget("2026-04")
    first_budget_lines = repo.list_budget_lines("2026-04")
    first_reminders = repo.list_reminders()

    assert first_report.transactions_added == 2
    assert first_report.transactions_updated == 0
    assert first_report.budgets_synced == 1
    assert len(first_transactions) == 2
    assert all(item.status == "待确认" for item in first_transactions)
    assert all(item.source == "Obsidian 私帐自动同步" for item in first_transactions)
    assert first_budget is not None
    assert first_budget.total_budget == "11900.00"
    assert {item.line_kind for item in first_budget_lines} == {"收入", "支出"}
    assert {item.title for item in first_reminders} == {
        "2026-04 日常零花 预算超支提醒",
        "2026-04 约会 预算临界提醒",
    }

    updated_daily_content = """日期：2026年04月21日 周二

## 收入明细

- 今日无收入流水

## 支出明细

**标签：个人成长投资**

- 今日合计：15.00 元
- 09:00｜15.00 元｜花小猪打车

## 备注

- 数据来源：备忘录 `账单_202604220941.xlsx`
"""
    write_private_ledger_files(obsidian_root, updated_daily_content, monthly_content)

    second_report = service.sync(obsidian_root=obsidian_root, dates=["2026-04-21"], months=["2026-04"])
    second_transactions = sorted(repo.list_transactions(), key=lambda item: item.occurred_on)

    assert second_report.transactions_added == 0
    assert second_report.transactions_updated == 1
    assert len(second_report.deletion_candidates) == 1
    assert len(second_transactions) == 2
    assert second_transactions[0].category == "个人成长投资"
    assert second_transactions[0].amount == "15.00"

    repo.close()


def test_obsidian_sync_reuses_existing_budget_and_preserves_manual_budget_lines(tmp_path) -> None:
    obsidian_root = tmp_path / "obsidian"
    db_path = tmp_path / "custom-ledger.sqlite"
    repo = LedgerRepository(db_path=db_path)
    repo.upsert_budget(
        MonthlyBudget(
            id="manual-budget-2026-04",
            month_key="2026-04",
            total_budget="1.00",
            notes="手动预算",
            status="生效中",
            created_at="2026-04-01T00:00:00",
            updated_at="2026-04-01T00:00:00",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="manual-line",
            budget_id="manual-budget-2026-04",
            line_kind="分类预算",
            name="手工项目",
            category="手工项目",
            planned_amount="88.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="不要被 Obsidian 同步删除",
            created_at="2026-04-01T00:00:00",
            updated_at="2026-04-01T00:00:00",
        )
    )
    write_private_ledger_files(
        obsidian_root,
        """日期：2026年04月21日 周二

## 收入明细

- 今日无收入流水

## 支出明细

- 今日无支出流水
""",
        """日期：2026年04月21日 截止

## 总览

- 预期支出：11900.00 元

## 收入预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 工资 | 1000.00 | 1000.00 | 0.00 |

## 支出预期与实际

| 项目 | 预期 | 实际 | 偏差 |
| --- | ---: | ---: | ---: |
| 日常零花 | 3000.00 | 3324.64 | +324.64 |
""",
    )

    report = ObsidianLedgerSyncService(repo).sync(obsidian_root=obsidian_root, months=["2026-04"])
    budget = repo.get_monthly_budget("2026-04")
    lines = repo.list_budget_lines("2026-04")

    assert repo.db_path == db_path
    assert budget is not None
    assert budget.id == "manual-budget-2026-04"
    assert report.budget_lines_removed == 0
    assert {item.id for item in lines} >= {"manual-line"}
    assert {item.name for item in lines} >= {"手工项目", "工资", "日常零花"}

    repo.close()
