from __future__ import annotations

import json
import sqlite3

from private_ledger.domain.models import (
    Account,
    AppSettings,
    BalanceSnapshot,
    BudgetLine,
    MonthlyBudget,
    ReminderItem,
    Transaction,
)
from private_ledger.storage.repository import LedgerRepository


def test_repository_round_trip_export_and_backup(tmp_path) -> None:
    repo = LedgerRepository(tmp_path)

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
            id="txn-income",
            occurred_on="2026-04-15",
            transaction_type="收入",
            category="工资",
            amount="18500.00",
            from_account_id="",
            to_account_id="acc-main",
            status="已确认",
            source="手动录入",
            notes="",
            related_transaction_id="",
            created_at="2026-04-15T09:00:00",
            updated_at="2026-04-15T09:00:00",
        )
    )
    repo.upsert_budget(
        MonthlyBudget(
            id="budget-2026-04",
            month_key="2026-04",
            total_budget="8000.00",
            notes="测试预算",
            status="生效中",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="line-food",
            budget_id="budget-2026-04",
            line_kind="分类预算",
            name="餐饮",
            category="餐饮",
            planned_amount="2000.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.upsert_reminder(
        ReminderItem(
            id="rem-api",
            title="API 余额充值",
            reminder_kind="阈值提醒",
            target_type="账户余额",
            account_id="acc-main",
            due_date="",
            threshold_amount="100.00",
            current_value="80.00",
            status="启用",
            source="手动录入",
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
        )
    )
    repo.save_settings(
        AppSettings(
            data_dir=str(tmp_path),
            export_dir=str(tmp_path / "exports"),
            backup_dir=str(tmp_path / "backups"),
            default_currency="CNY",
            reminder_lead_days=7,
            obsidian_path="",
        )
    )

    assert len(repo.list_accounts()) == 1
    assert len(repo.list_snapshots("acc-main")) == 1
    assert len(repo.list_transactions()) == 1
    assert repo.get_monthly_budget("2026-04") is not None
    assert len(repo.list_budget_lines("budget-2026-04")) == 1
    assert len(repo.list_reminders()) == 1
    assert repo.load_settings().default_currency == "CNY"

    export_path = repo.export_json()
    backup_path = repo.backup_database()

    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 3
    assert payload["accounts"][0]["name"] == "招商银行卡"
    assert payload["budget_lines"][0]["effective_start_month"] == "2026-04"
    assert payload["budget_lines"][0]["effective_end_month"] == "2026-04"
    assert backup_path.exists()


def test_repository_filters_budget_lines_by_effective_month(tmp_path) -> None:
    repo = LedgerRepository(tmp_path)
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
            id="budget-2026-05",
            month_key="2026-05",
            total_budget="0.00",
            notes="",
            status="生效中",
            created_at="2026-05-01T09:00:00",
            updated_at="2026-05-01T09:00:00",
        ),
    ]:
        repo.upsert_budget(budget)

    repo.upsert_budget_line(
        BudgetLine(
            id="line-april-only",
            budget_id="budget-2026-04",
            line_kind="分类预算",
            name="四月活动",
            category="四月活动",
            planned_amount="500.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
            effective_start_month="2026-04",
            effective_end_month="2026-04",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="line-long-term",
            budget_id="budget-2026-05",
            line_kind="固定支出",
            name="房租",
            category="房租",
            planned_amount="2500.00",
            day_of_month=None,
            is_required=True,
            reminder_days=3,
            notes="",
            created_at="2026-05-01T09:00:00",
            updated_at="2026-05-01T09:00:00",
            effective_start_month="2026-05",
            effective_end_month="",
        )
    )
    repo.upsert_budget_line(
        BudgetLine(
            id="line-range",
            budget_id="budget-2026-04",
            line_kind="储蓄计划",
            name="短期储蓄",
            category="短期储蓄",
            planned_amount="300.00",
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes="",
            created_at="2026-04-01T09:00:00",
            updated_at="2026-04-01T09:00:00",
            effective_start_month="2026-04",
            effective_end_month="2026-05",
        )
    )

    assert {line.id for line in repo.list_effective_budget_lines("2026-04")} == {
        "line-april-only",
        "line-range",
    }
    assert {line.id for line in repo.list_effective_budget_lines("2026-05")} == {
        "line-long-term",
        "line-range",
    }
    assert {line.id for line in repo.list_effective_budget_lines("2026-06")} == {"line-long-term"}

    repo.close()
    reopened = LedgerRepository(tmp_path)
    long_term = reopened.get_budget_line("line-long-term")
    assert long_term is not None
    assert long_term.effective_end_month == ""
    assert {line.id for line in reopened.list_effective_budget_lines("2026-06")} == {"line-long-term"}


def test_schema_migration_backfills_legacy_budget_line_effective_month(tmp_path) -> None:
    db_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE schema_info (version INTEGER NOT NULL);
        INSERT INTO schema_info(version) VALUES (2);

        CREATE TABLE monthly_budgets (
            id TEXT PRIMARY KEY,
            month_key TEXT NOT NULL UNIQUE,
            total_budget TEXT NOT NULL,
            notes TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO monthly_budgets VALUES (
            'budget-2026-04', '2026-04', '8000.00', '', '生效中',
            '2026-04-01T09:00:00', '2026-04-01T09:00:00'
        );

        CREATE TABLE budget_lines (
            id TEXT PRIMARY KEY,
            budget_id TEXT NOT NULL,
            line_kind TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            planned_amount TEXT NOT NULL,
            day_of_month INTEGER,
            is_required INTEGER NOT NULL,
            reminder_days INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO budget_lines VALUES (
            'line-food', 'budget-2026-04', '分类预算', '餐饮', '餐饮',
            '2000.00', NULL, 0, 0, '', '2026-04-01T09:00:00', '2026-04-01T09:00:00'
        );
        """
    )
    connection.commit()
    connection.close()

    repo = LedgerRepository(db_path=db_path)

    line = repo.list_budget_lines("2026-04")[0]
    assert line.effective_start_month == "2026-04"
    assert line.effective_end_month == "2026-04"
    assert [item.id for item in repo.list_effective_budget_lines("2026-04")] == ["line-food"]
    assert repo.list_effective_budget_lines("2026-05") == []
