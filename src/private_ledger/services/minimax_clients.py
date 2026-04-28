from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
from urllib import error, request

from private_ledger.services.minimax_recognition import parse_structured_response, MiniMaxRecognitionResult


class MiniMaxOcrMcpClient:
    def __init__(self, api_key: str, api_host: str, command: list[str] | None = None, timeout_seconds: int = 90) -> None:
        self.api_key = api_key
        self.api_host = api_host
        self.command = command or ["uvx", "minimax-coding-plan-mcp", "-y"]
        self.timeout_seconds = timeout_seconds

    def understand_image(self, image_path: str | Path) -> str:
        image_uri = Path(image_path).resolve().as_uri()
        try:
            return self._call_understand_image({"image_url": image_uri})
        except Exception:
            return self._call_understand_image({"image_source": image_uri})

    def _call_understand_image(self, arguments: dict[str, str]) -> str:
        env = os.environ.copy()
        env["MINIMAX_API_KEY"] = self.api_key
        env["MINIMAX_API_HOST"] = self.api_host
        process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        try:
            self._send(process, 1, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "private-ledger", "version": "0.1.0"},
            })
            self._read_response(process, 1)
            self._send_notification(process, "notifications/initialized", {})
            self._send(process, 2, "tools/call", {"name": "understand_image", "arguments": arguments})
            payload = self._read_response(process, 2)
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            return _extract_mcp_text(payload.get("result", {}))
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()

    def _send(self, process: subprocess.Popen, message_id: int, method: str, params: dict[str, Any]) -> None:
        self._write(process, {"jsonrpc": "2.0", "id": message_id, "method": method, "params": params})

    def _send_notification(self, process: subprocess.Popen, method: str, params: dict[str, Any]) -> None:
        self._write(process, {"jsonrpc": "2.0", "method": method, "params": params})

    def _write(self, process: subprocess.Popen, payload: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("MCP process stdin is not available.")
        process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def _read_response(self, process: subprocess.Popen, expected_id: int) -> dict[str, Any]:
        if process.stdout is None:
            raise RuntimeError("MCP process stdout is not available.")
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            line = process.stdout.readline()
            if not line:
                break
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("id") == expected_id:
                return payload
        stderr = ""
        if process.stderr is not None:
            stderr = process.stderr.read()
        raise RuntimeError(f"MiniMax OCR MCP did not return a response. {stderr}".strip())


class MiniMaxTextClient:
    def __init__(self, api_key: str, api_host: str, model: str = "MiniMax-M2.7", timeout_seconds: int = 90) -> None:
        self.api_key = api_key
        self.api_host = api_host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def structure_ledger_text(self, ocr_text: str) -> MiniMaxRecognitionResult:
        prompt = _build_structuring_prompt(ocr_text)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个保守的中文私帐账单识别助手，只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.api_host}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"MiniMax M2.7 request failed: {exc.code} {detail}") from exc
        content = response_payload["choices"][0]["message"]["content"]
        return parse_structured_response(content)

    def test_connection(self) -> None:
        result = self.structure_ledger_text("连接测试：无账单数据。")
        if not isinstance(result, MiniMaxRecognitionResult):
            raise RuntimeError("MiniMax connection test returned an unexpected response.")


def _extract_mcp_text(result: dict[str, Any]) -> str:
    content = result.get("content") or []
    texts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            texts.append(str(item.get("text") or ""))
    if texts:
        return "\n".join(texts).strip()
    return json.dumps(result, ensure_ascii=False)


def _build_structuring_prompt(ocr_text: str) -> str:
    return f"""
请把下面 OCR 文本转成严格 JSON。不要输出解释、Markdown 或额外文字。

字段格式：
{{
  "raw_summary": "一句话摘要",
  "transactions": [
    {{
      "occurred_on": "YYYY-MM-DD，缺失则留空",
      "transaction_type": "收入/支出/转账/充值/退款",
      "category": "中文标签",
      "amount": "金额数字，两位小数",
      "from_account_name": "付款账户名，缺失留空",
      "to_account_name": "收款账户名，缺失留空",
      "notes": "备注",
      "source_snippet": "对应 OCR 原文片段"
    }}
  ],
  "reminders": [
    {{
      "title": "提醒标题",
      "reminder_kind": "日期提醒/阈值提醒",
      "target_type": "充值/会员续费/固定支出/储蓄计划/账户余额",
      "account_name": "关联账户名，缺失留空",
      "due_date": "YYYY-MM-DD，非日期提醒留空",
      "threshold_amount": "阈值金额，非阈值提醒留空",
      "current_value": "当前值，非阈值提醒留空",
      "notes": "备注",
      "source_snippet": "对应 OCR 原文片段"
    }}
  ],
  "warnings": ["保守口径警告"],
  "missing_fields": ["缺失字段"]
}}

保守规则：
- 不确定金额、日期、账户、标签时，字段留空并写入 missing_fields。
- 只有出现明确充值、续费、到期、低余额、回查等语义时，才生成 reminders。
- 不要猜测没有出现在文本里的数据。

OCR 文本：
{ocr_text}
""".strip()
