from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from private_ledger.domain.models import ImportBatch, new_id, now_timestamp
from private_ledger.services.minimax_clients import MiniMaxOcrMcpClient, MiniMaxTextClient
from private_ledger.storage.repository import LedgerRepository


class ImportRecognitionService:
    def __init__(
        self,
        repository: LedgerRepository,
        ocr_client: MiniMaxOcrMcpClient,
        text_client: MiniMaxTextClient,
    ) -> None:
        self.repository = repository
        self.ocr_client = ocr_client
        self.text_client = text_client

    def recognize_image(self, image_path: str | Path) -> ImportBatch:
        source_path = Path(image_path)
        stored_path = self._copy_to_imports(source_path)
        now = now_timestamp()
        batch = ImportBatch(
            id=new_id("batch"),
            source_file_path=str(stored_path),
            original_file_name=source_path.name,
            raw_ocr_text="",
            structured_json="{}",
            status="processing",
            error_message="",
            created_at=now,
            updated_at=now,
        )
        self.repository.upsert_import_batch(batch)
        try:
            raw_text = self.ocr_client.understand_image(stored_path)
            structured = self.text_client.structure_ledger_text(raw_text)
            ready = ImportBatch(
                id=batch.id,
                source_file_path=batch.source_file_path,
                original_file_name=batch.original_file_name,
                raw_ocr_text=raw_text,
                structured_json=json.dumps(structured.to_dict(), ensure_ascii=False, indent=2),
                status="ready",
                error_message="",
                created_at=batch.created_at,
                updated_at=now_timestamp(),
            )
            self.repository.upsert_import_batch(ready)
            return ready
        except Exception as exc:
            failed = ImportBatch(
                id=batch.id,
                source_file_path=batch.source_file_path,
                original_file_name=batch.original_file_name,
                raw_ocr_text=batch.raw_ocr_text,
                structured_json=batch.structured_json,
                status="failed",
                error_message=str(exc),
                created_at=batch.created_at,
                updated_at=now_timestamp(),
            )
            self.repository.upsert_import_batch(failed)
            return failed

    def _copy_to_imports(self, source_path: Path) -> Path:
        imports_dir = self.repository.data_dir / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:16]
        suffix = source_path.suffix or ".png"
        target = imports_dir / f"{digest}{suffix}"
        if not target.exists():
            shutil.copy2(source_path, target)
        return target
