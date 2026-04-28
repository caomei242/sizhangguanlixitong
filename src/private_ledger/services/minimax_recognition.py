from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any


@dataclass
class MiniMaxRecognitionResult:
    raw_summary: str = ""
    transactions: list[dict[str, Any]] = field(default_factory=list)
    reminders: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_summary": self.raw_summary,
            "transactions": self.transactions,
            "reminders": self.reminders,
            "warnings": self.warnings,
            "missing_fields": self.missing_fields,
        }


def parse_structured_response(content: str) -> MiniMaxRecognitionResult:
    payload = _load_json_payload(content)
    return MiniMaxRecognitionResult(
        raw_summary=str(payload.get("raw_summary") or ""),
        transactions=list(payload.get("transactions") or []),
        reminders=list(payload.get("reminders") or []),
        warnings=[str(item) for item in payload.get("warnings") or []],
        missing_fields=[str(item) for item in payload.get("missing_fields") or []],
    )


def _load_json_payload(content: str) -> dict[str, Any]:
    text = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("MiniMax structured response must be a JSON object.")
    return payload
