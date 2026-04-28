from __future__ import annotations

import json

from private_ledger.domain.models import AppSettings, ImportBatch
from private_ledger.storage.repository import LedgerRepository


def test_import_batch_round_trip_and_export_keeps_minimax_key_out(tmp_path) -> None:
    repo = LedgerRepository(tmp_path)
    repo.save_settings(
        AppSettings(
            data_dir=str(tmp_path),
            export_dir=str(tmp_path / "exports"),
            backup_dir=str(tmp_path / "backups"),
            default_currency="CNY",
            reminder_lead_days=7,
            obsidian_path="",
            minimax_api_host="https://api.minimaxi.com/v1",
            minimax_model="MiniMax-M2.7",
            minimax_key_configured=True,
        )
    )
    repo.upsert_import_batch(
        ImportBatch(
            id="batch-001",
            source_file_path=str(tmp_path / "imports" / "receipt.png"),
            original_file_name="receipt.png",
            raw_ocr_text="账单金额 42.00，会员续费 2026-05-01",
            structured_json=json.dumps(
                {
                    "transactions": [{"amount": "42.00"}],
                    "reminders": [{"title": "会员续费"}],
                },
                ensure_ascii=False,
            ),
            status="ready",
            error_message="",
            created_at="2026-04-20T10:00:00",
            updated_at="2026-04-20T10:00:00",
        )
    )

    batches = repo.list_import_batches()
    export_path = repo.export_json()
    payload = json.loads(export_path.read_text(encoding="utf-8"))

    assert len(batches) == 1
    assert batches[0].status == "ready"
    assert payload["settings"]["minimax_key_configured"] is True
    assert "sk-cp-secret" not in export_path.read_text(encoding="utf-8")
    assert "minimax_api_key" not in payload["settings"]


def test_confirm_import_batch_creates_pending_transaction_and_disabled_reminder(tmp_path) -> None:
    repo = LedgerRepository(tmp_path)
    repo.upsert_import_batch(
        ImportBatch(
            id="batch-002",
            source_file_path=str(tmp_path / "imports" / "phone.png"),
            original_file_name="phone.png",
            raw_ocr_text="话费充值 100 元，下次回查 2026-05-20",
            structured_json=json.dumps(
                {
                    "transactions": [
                        {
                            "occurred_on": "2026-04-20",
                            "transaction_type": "充值",
                            "category": "话费充值",
                            "amount": "100.00",
                            "from_account_name": "",
                            "to_account_name": "",
                            "notes": "识别自话费截图",
                            "source_snippet": "话费充值 100 元",
                        }
                    ],
                    "reminders": [
                        {
                            "title": "话费回查",
                            "reminder_kind": "日期提醒",
                            "target_type": "充值",
                            "due_date": "2026-05-20",
                            "threshold_amount": "",
                            "current_value": "",
                            "notes": "识别自话费截图",
                            "source_snippet": "下次回查 2026-05-20",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            status="ready",
            error_message="",
            created_at="2026-04-20T10:00:00",
            updated_at="2026-04-20T10:00:00",
        )
    )

    repo.confirm_import_batch("batch-002")

    transactions = repo.list_transactions()
    reminders = repo.list_reminders()
    batch = repo.get_import_batch("batch-002")

    assert transactions[0].status == "待确认"
    assert transactions[0].source == "MiniMax OCR"
    assert reminders[0].status == "停用"
    assert reminders[0].source == "MiniMax OCR"
    assert batch is not None
    assert batch.status == "imported"
