from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any

from private_ledger.domain.models import (
    Account,
    AppSettings,
    BalanceSnapshot,
    BudgetLine,
    ImportBatch,
    MonthlyBudget,
    ReminderItem,
    Transaction,
    now_timestamp,
    new_id,
)
from private_ledger.storage.schema import SCHEMA_VERSION, initialize_schema
from private_ledger.domain.ledger import parse_decimal


def default_data_dir() -> Path:
    app_support_dir = Path.home() / "Library" / "Application Support"
    preferred = app_support_dir / "草莓私帐管理系统"
    legacy = app_support_dir / "草莓私帐"
    if preferred.exists():
        return preferred
    if legacy.exists():
        try:
            shutil.move(str(legacy), str(preferred))
            return preferred
        except OSError:
            return legacy
    return preferred


class LedgerRepository:
    def __init__(self, data_dir: str | Path | None = None, db_path: str | Path | None = None) -> None:
        if db_path is not None:
            self.db_path = Path(db_path).expanduser()
            self.data_dir = self.db_path.parent
        else:
            self.data_dir = Path(data_dir) if data_dir is not None else default_data_dir()
            self.db_path = self.data_dir / "private-ledger.db"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        initialize_schema(self.connection)

    def close(self) -> None:
        self.connection.close()

    def list_accounts(self) -> list[Account]:
        rows = self.connection.execute(
            "SELECT * FROM accounts ORDER BY name COLLATE NOCASE ASC"
        ).fetchall()
        return [self._row_to_account(row) for row in rows]

    def upsert_account(self, account: Account) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO accounts (
                id, name, account_type, currency, purpose, status, notes, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account.id,
                account.name,
                account.account_type,
                account.currency,
                account.purpose,
                account.status,
                account.notes,
                account.source,
                account.created_at,
                account.updated_at,
            ),
        )
        self.connection.commit()

    def delete_account(self, account_id: str) -> None:
        self.connection.execute("DELETE FROM balance_snapshots WHERE account_id = ?", (account_id,))
        self.connection.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.connection.commit()

    def list_snapshots(self, account_id: str = "") -> list[BalanceSnapshot]:
        if account_id:
            rows = self.connection.execute(
                "SELECT * FROM balance_snapshots WHERE account_id = ? ORDER BY snapshot_time DESC, created_at DESC",
                (account_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM balance_snapshots ORDER BY snapshot_time DESC, created_at DESC"
            ).fetchall()
        return [self._row_to_snapshot(row) for row in rows]

    def add_snapshot(self, snapshot: BalanceSnapshot) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO balance_snapshots (
                id, account_id, snapshot_time, amount, status, source, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.id,
                snapshot.account_id,
                snapshot.snapshot_time,
                snapshot.amount,
                snapshot.status,
                snapshot.source,
                snapshot.notes,
                snapshot.created_at,
            ),
        )
        self.connection.commit()

    def delete_snapshot(self, snapshot_id: str) -> None:
        self.connection.execute("DELETE FROM balance_snapshots WHERE id = ?", (snapshot_id,))
        self.connection.commit()

    def list_transactions(self) -> list[Transaction]:
        rows = self.connection.execute(
            "SELECT * FROM transactions ORDER BY occurred_on DESC, updated_at DESC"
        ).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def upsert_transaction(self, transaction: Transaction) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO transactions (
                id, occurred_on, transaction_type, category, amount, from_account_id, to_account_id,
                status, source, notes, related_transaction_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.id,
                transaction.occurred_on,
                transaction.transaction_type,
                transaction.category,
                transaction.amount,
                transaction.from_account_id,
                transaction.to_account_id,
                transaction.status,
                transaction.source,
                transaction.notes,
                transaction.related_transaction_id,
                transaction.created_at,
                transaction.updated_at,
            ),
        )
        self.connection.commit()

    def delete_transaction(self, transaction_id: str) -> None:
        self.connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.connection.commit()

    def get_monthly_budget(self, month_key: str) -> MonthlyBudget | None:
        row = self.connection.execute(
            "SELECT * FROM monthly_budgets WHERE month_key = ? LIMIT 1",
            (month_key,),
        ).fetchone()
        return self._row_to_budget(row) if row else None

    def upsert_budget(self, budget: MonthlyBudget) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO monthly_budgets (
                id, month_key, total_budget, notes, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                budget.id,
                budget.month_key,
                budget.total_budget,
                budget.notes,
                budget.status,
                budget.created_at,
                budget.updated_at,
            ),
        )
        self.connection.commit()

    def list_budget_lines(self, budget_ref: str) -> list[BudgetLine]:
        budget_id = budget_ref
        maybe_budget = self.get_monthly_budget(budget_ref)
        if maybe_budget is not None:
            budget_id = maybe_budget.id
        rows = self.connection.execute(
            "SELECT * FROM budget_lines WHERE budget_id = ? ORDER BY line_kind, name COLLATE NOCASE ASC",
            (budget_id,),
        ).fetchall()
        return [self._row_to_budget_line(row) for row in rows]

    def list_effective_budget_lines(self, month_key: str) -> list[BudgetLine]:
        rows = self.connection.execute(
            """
            SELECT * FROM budget_lines
            WHERE effective_start_month <= ?
              AND (effective_end_month = '' OR effective_end_month >= ?)
            ORDER BY line_kind, name COLLATE NOCASE ASC
            """,
            (month_key, month_key),
        ).fetchall()
        return [self._row_to_budget_line(row) for row in rows]

    def get_budget_line(self, budget_line_id: str) -> BudgetLine | None:
        row = self.connection.execute(
            "SELECT * FROM budget_lines WHERE id = ? LIMIT 1",
            (budget_line_id,),
        ).fetchone()
        return self._row_to_budget_line(row) if row else None

    def upsert_budget_line(self, budget_line: BudgetLine) -> None:
        effective_start_month = budget_line.effective_start_month
        effective_end_month = budget_line.effective_end_month
        if not effective_start_month and not effective_end_month:
            budget_month = self._month_key_for_budget_id(budget_line.budget_id)
            effective_start_month = budget_month
            effective_end_month = budget_month
        self.connection.execute(
            """
            INSERT OR REPLACE INTO budget_lines (
                id, budget_id, line_kind, name, category, planned_amount, day_of_month,
                is_required, reminder_days, notes, created_at, updated_at,
                effective_start_month, effective_end_month
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                budget_line.id,
                budget_line.budget_id,
                budget_line.line_kind,
                budget_line.name,
                budget_line.category,
                budget_line.planned_amount,
                budget_line.day_of_month,
                1 if budget_line.is_required else 0,
                budget_line.reminder_days,
                budget_line.notes,
                budget_line.created_at,
                budget_line.updated_at,
                effective_start_month,
                effective_end_month,
            ),
        )
        self.connection.commit()

    def delete_budget_line(self, budget_line_id: str) -> None:
        self.connection.execute("DELETE FROM budget_lines WHERE id = ?", (budget_line_id,))
        self.connection.commit()

    def list_reminders(self) -> list[ReminderItem]:
        rows = self.connection.execute(
            "SELECT * FROM reminder_items ORDER BY due_date ASC, title COLLATE NOCASE ASC"
        ).fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def upsert_reminder(self, reminder: ReminderItem) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO reminder_items (
                id, title, reminder_kind, target_type, account_id, due_date, threshold_amount,
                current_value, status, source, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reminder.id,
                reminder.title,
                reminder.reminder_kind,
                reminder.target_type,
                reminder.account_id,
                reminder.due_date,
                reminder.threshold_amount,
                reminder.current_value,
                reminder.status,
                reminder.source,
                reminder.notes,
                reminder.created_at,
                reminder.updated_at,
            ),
        )
        self.connection.commit()

    def delete_reminder(self, reminder_id: str) -> None:
        self.connection.execute("DELETE FROM reminder_items WHERE id = ?", (reminder_id,))
        self.connection.commit()

    def load_settings(self) -> AppSettings:
        stored = {
            row["key"]: row["value"]
            for row in self.connection.execute("SELECT key, value FROM app_settings").fetchall()
        }
        export_dir = stored.get("export_dir", str(self.data_dir / "exports"))
        backup_dir = stored.get("backup_dir", str(self.data_dir / "backups"))
        return AppSettings(
            data_dir=stored.get("data_dir", str(self.data_dir)),
            export_dir=export_dir,
            backup_dir=backup_dir,
            default_currency=stored.get("default_currency", "CNY"),
            reminder_lead_days=int(stored.get("reminder_lead_days", "7")),
            obsidian_path=stored.get("obsidian_path", ""),
            minimax_api_host=stored.get("minimax_api_host", "https://api.minimaxi.com/v1"),
            minimax_model=stored.get("minimax_model", "MiniMax-M2.7"),
            minimax_key_configured=stored.get("minimax_key_configured", "False") == "True",
        )

    def save_settings(self, settings: AppSettings) -> None:
        for key, value in settings.to_dict().items():
            if key == "minimax_api_key":
                continue
            self.connection.execute(
                "INSERT OR REPLACE INTO app_settings(key, value) VALUES (?, ?)",
                (key, str(value)),
            )
        self.connection.commit()

    def list_import_batches(self) -> list[ImportBatch]:
        rows = self.connection.execute(
            "SELECT * FROM import_batches ORDER BY updated_at DESC, created_at DESC"
        ).fetchall()
        return [self._row_to_import_batch(row) for row in rows]

    def get_import_batch(self, batch_id: str) -> ImportBatch | None:
        row = self.connection.execute(
            "SELECT * FROM import_batches WHERE id = ? LIMIT 1",
            (batch_id,),
        ).fetchone()
        return self._row_to_import_batch(row) if row else None

    def upsert_import_batch(self, batch: ImportBatch) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO import_batches (
                id, source_file_path, original_file_name, raw_ocr_text, structured_json,
                status, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch.id,
                batch.source_file_path,
                batch.original_file_name,
                batch.raw_ocr_text,
                batch.structured_json,
                batch.status,
                batch.error_message,
                batch.created_at,
                batch.updated_at,
            ),
        )
        self.connection.commit()

    def confirm_import_batch(self, batch_id: str) -> None:
        batch = self.get_import_batch(batch_id)
        if batch is None:
            raise ValueError(f"Import batch not found: {batch_id}")
        payload = json.loads(batch.structured_json or "{}")
        accounts = self.list_accounts()
        now = now_timestamp()
        for draft in payload.get("transactions", []):
            transaction = Transaction(
                id=new_id("txn"),
                occurred_on=str(draft.get("occurred_on") or now[:10]),
                transaction_type=str(draft.get("transaction_type") or "支出"),
                category=str(draft.get("category") or "待确认分类"),
                amount=f"{parse_decimal(str(draft.get('amount') or '0')):.2f}",
                from_account_id=self._account_id_by_name(str(draft.get("from_account_name") or ""), accounts),
                to_account_id=self._account_id_by_name(str(draft.get("to_account_name") or ""), accounts),
                status="待确认",
                source="MiniMax OCR",
                notes=self._draft_notes(draft),
                related_transaction_id="",
                created_at=now,
                updated_at=now,
            )
            self.upsert_transaction(transaction)
        for draft in payload.get("reminders", []):
            reminder_kind = str(draft.get("reminder_kind") or "日期提醒")
            reminder = ReminderItem(
                id=new_id("rem"),
                title=str(draft.get("title") or "待确认提醒"),
                reminder_kind=reminder_kind,
                target_type=str(draft.get("target_type") or "充值"),
                account_id=self._account_id_by_name(str(draft.get("account_name") or ""), accounts),
                due_date=str(draft.get("due_date") or "") if reminder_kind == "日期提醒" else "",
                threshold_amount=str(draft.get("threshold_amount") or "") if reminder_kind == "阈值提醒" else "",
                current_value=str(draft.get("current_value") or "") if reminder_kind == "阈值提醒" else "",
                status="停用",
                source="MiniMax OCR",
                notes=self._draft_notes(draft),
                created_at=now,
                updated_at=now,
            )
            self.upsert_reminder(reminder)
        self.upsert_import_batch(
            ImportBatch(
                id=batch.id,
                source_file_path=batch.source_file_path,
                original_file_name=batch.original_file_name,
                raw_ocr_text=batch.raw_ocr_text,
                structured_json=batch.structured_json,
                status="imported",
                error_message="",
                created_at=batch.created_at,
                updated_at=now,
            )
        )

    def export_json(self, export_dir: str | Path | None = None) -> Path:
        settings = self.load_settings()
        target_dir = Path(export_dir or settings.export_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "exported_at": now_timestamp(),
            "accounts": [item.to_dict() for item in self.list_accounts()],
            "balance_snapshots": [item.to_dict() for item in self.list_snapshots()],
            "transactions": [item.to_dict() for item in self.list_transactions()],
            "monthly_budgets": [self._row_to_budget(row).to_dict() for row in self.connection.execute("SELECT * FROM monthly_budgets").fetchall()],
            "budget_lines": [self._row_to_budget_line(row).to_dict() for row in self.connection.execute("SELECT * FROM budget_lines").fetchall()],
            "reminder_items": [item.to_dict() for item in self.list_reminders()],
            "import_batches": [item.to_dict() for item in self.list_import_batches()],
            "settings": settings.to_dict(),
        }
        path = target_dir / f"private-ledger-export-{now_timestamp().replace(':', '-')}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def backup_database(self, backup_dir: str | Path | None = None) -> Path:
        settings = self.load_settings()
        target_dir = Path(backup_dir or settings.backup_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"private-ledger-backup-{now_timestamp().replace(':', '-')}.db"
        with sqlite3.connect(target) as backup_connection:
            self.connection.backup(backup_connection)
        return target

    def _row_to_account(self, row: sqlite3.Row) -> Account:
        return Account(**dict(row))

    def _row_to_snapshot(self, row: sqlite3.Row) -> BalanceSnapshot:
        return BalanceSnapshot(**dict(row))

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        return Transaction(**dict(row))

    def _row_to_budget(self, row: sqlite3.Row) -> MonthlyBudget:
        return MonthlyBudget(**dict(row))

    def _row_to_budget_line(self, row: sqlite3.Row) -> BudgetLine:
        payload = dict(row)
        payload["is_required"] = bool(payload["is_required"])
        return BudgetLine(**payload)

    def _month_key_for_budget_id(self, budget_id: str) -> str:
        row = self.connection.execute(
            "SELECT month_key FROM monthly_budgets WHERE id = ? LIMIT 1",
            (budget_id,),
        ).fetchone()
        return row["month_key"] if row else ""

    def _row_to_reminder(self, row: sqlite3.Row) -> ReminderItem:
        return ReminderItem(**dict(row))

    def _row_to_import_batch(self, row: sqlite3.Row) -> ImportBatch:
        return ImportBatch(**dict(row))

    def _account_id_by_name(self, account_name: str, accounts: list[Account]) -> str:
        if not account_name:
            return ""
        account = next((item for item in accounts if item.name == account_name), None)
        return account.id if account else ""

    def _draft_notes(self, draft: dict[str, Any]) -> str:
        notes = str(draft.get("notes") or "").strip()
        snippet = str(draft.get("source_snippet") or "").strip()
        if snippet:
            return f"{notes}\n识别依据：{snippet}".strip()
        return notes
