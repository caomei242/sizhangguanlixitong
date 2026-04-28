from __future__ import annotations

from private_ledger.services.minimax_recognition import (
    MiniMaxRecognitionResult,
    parse_structured_response,
)


def test_parse_structured_response_accepts_json_in_code_fence() -> None:
    content = """
```json
{
  "raw_summary": "支付宝账单截图",
  "transactions": [
    {
      "occurred_on": "2026-04-20",
      "transaction_type": "支出",
      "category": "餐饮",
      "amount": "42.00",
      "from_account_name": "支付宝",
      "to_account_name": "",
      "notes": "午餐",
      "source_snippet": "餐饮 42.00"
    }
  ],
  "reminders": [],
  "warnings": ["账户待确认"],
  "missing_fields": ["付款账户"]
}
```
"""

    result = parse_structured_response(content)

    assert isinstance(result, MiniMaxRecognitionResult)
    assert result.transactions[0]["amount"] == "42.00"
    assert result.warnings == ["账户待确认"]
    assert result.missing_fields == ["付款账户"]


def test_parse_structured_response_normalizes_missing_sections() -> None:
    result = parse_structured_response('{"transactions": []}')

    assert result.raw_summary == ""
    assert result.transactions == []
    assert result.reminders == []
    assert result.warnings == []
    assert result.missing_fields == []
