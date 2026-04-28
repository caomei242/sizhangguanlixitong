from __future__ import annotations

import sqlite3


SCHEMA_VERSION = 3


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            currency TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS balance_snapshots (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            snapshot_time TEXT NOT NULL,
            amount TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            occurred_on TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount TEXT NOT NULL,
            from_account_id TEXT NOT NULL,
            to_account_id TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            notes TEXT NOT NULL,
            related_transaction_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS monthly_budgets (
            id TEXT PRIMARY KEY,
            month_key TEXT NOT NULL UNIQUE,
            total_budget TEXT NOT NULL,
            notes TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budget_lines (
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
            updated_at TEXT NOT NULL,
            effective_start_month TEXT NOT NULL DEFAULT '',
            effective_end_month TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS reminder_items (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            reminder_kind TEXT NOT NULL,
            target_type TEXT NOT NULL,
            account_id TEXT NOT NULL,
            due_date TEXT NOT NULL,
            threshold_amount TEXT NOT NULL,
            current_value TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS import_batches (
            id TEXT PRIMARY KEY,
            source_file_path TEXT NOT NULL,
            original_file_name TEXT NOT NULL,
            raw_ocr_text TEXT NOT NULL,
            structured_json TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    budget_line_columns = _column_names(connection, "budget_lines")
    should_backfill_effective_months = (
        "effective_start_month" not in budget_line_columns
        or "effective_end_month" not in budget_line_columns
    )
    _ensure_column(connection, "budget_lines", "effective_start_month", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "budget_lines", "effective_end_month", "TEXT NOT NULL DEFAULT ''")
    if should_backfill_effective_months:
        connection.execute(
            """
            UPDATE budget_lines
            SET effective_start_month = COALESCE(
                (SELECT monthly_budgets.month_key FROM monthly_budgets WHERE monthly_budgets.id = budget_lines.budget_id LIMIT 1),
                substr(created_at, 1, 7),
                ''
            )
            WHERE effective_start_month = ''
            """
        )
        connection.execute(
            """
            UPDATE budget_lines
            SET effective_end_month = COALESCE(
                (SELECT monthly_budgets.month_key FROM monthly_budgets WHERE monthly_budgets.id = budget_lines.budget_id LIMIT 1),
                effective_start_month
            )
            WHERE effective_end_month = ''
            """
        )
    row = connection.execute("SELECT version FROM schema_info LIMIT 1").fetchone()
    if row is None:
        connection.execute("INSERT INTO schema_info(version) VALUES (?)", (SCHEMA_VERSION,))
    else:
        connection.execute("UPDATE schema_info SET version = ?", (SCHEMA_VERSION,))
    connection.commit()


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_sql: str) -> None:
    columns = _column_names(connection, table_name)
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}
