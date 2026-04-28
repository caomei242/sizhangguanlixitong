from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import re
from pathlib import Path

from private_ledger.domain.ledger import parse_decimal
from private_ledger.domain.models import BudgetLine, MonthlyBudget, ReminderItem, Transaction, now_timestamp
from private_ledger.storage.repository import LedgerRepository


SYNC_SOURCE = "Obsidian 私帐自动同步"
SYNC_NOTE_MARKER = "同步来源：Obsidian 私帐自动同步"
DEFAULT_OBSIDIAN_ROOT = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~md~obsidian"
    / "Documents"
    / "个人日志"
)
PRIVATE_LEDGER_RELATIVE_DIR = Path("财务") / "私帐"
DAILY_RELATIVE_DIR = Path("每日收集")
MONTHLY_RELATIVE_DIR = Path("预期与实际")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
LABEL_RE = re.compile(r"^\*\*标签：(.+?)\*\*$")
TRANSACTION_RE = re.compile(r"^-\s*(\d{1,2}:\d{2})｜([0-9]+(?:\.[0-9]+)?)\s*元｜(.+?)\s*$")
TRANSACTION_CANDIDATE_RE = re.compile(r"^-\s*\d{1,2}:\d{2}｜")
OVERVIEW_RE = re.compile(r"^-\s*([^：]+)：\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class ParsedTransaction:
    transaction_id: str
    occurred_on: str
    transaction_type: str
    category: str
    amount: str
    merchant: str
    file_date: str
    file_path: Path
    source_line: str
    source_attachment: str
    has_rescan: bool

    def to_model(self, synced_at: str) -> Transaction:
        notes_lines = [
            SYNC_NOTE_MARKER,
            f"Obsidian 文件：{self.file_path}",
            f"标签：{self.category}",
            f"商户/备注：{self.merchant}",
            f"来源行：{self.source_line}",
            f"采集批次：{synced_at}",
            f"来源附件：{self.source_attachment or '未识别'}",
            f"回扫标记：{'是' if self.has_rescan else '否'}",
        ]
        return Transaction(
            id=self.transaction_id,
            occurred_on=self.occurred_on,
            transaction_type=self.transaction_type,
            category=self.category,
            amount=self.amount,
            from_account_id="",
            to_account_id="",
            status="待确认",
            source=SYNC_SOURCE,
            notes="\n".join(notes_lines),
            related_transaction_id="",
            created_at=synced_at,
            updated_at=synced_at,
        )


@dataclass
class ParsedDailyNote:
    note_date: str
    path: Path
    transactions: list[ParsedTransaction]
    source_attachment: str
    skipped_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedBudgetLine:
    line_id: str
    line_kind: str
    name: str
    category: str
    planned_amount: str
    actual_amount: str
    delta_amount: str

    def to_model(self, budget_id: str, month_key: str, source_file: Path, updated_at: str) -> BudgetLine:
        notes = "\n".join(
            [
                SYNC_NOTE_MARKER,
                f"来源文件：{source_file}",
                f"实际：{self.actual_amount}",
                f"偏差：{self.delta_amount}",
                f"更新时间：{updated_at}",
            ]
        )
        return BudgetLine(
            id=self.line_id,
            budget_id=budget_id,
            line_kind=self.line_kind,
            name=self.name,
            category=self.category,
            planned_amount=self.planned_amount,
            day_of_month=None,
            is_required=False,
            reminder_days=0,
            notes=notes,
            created_at=updated_at,
            updated_at=updated_at,
            effective_start_month=month_key,
            effective_end_month=month_key,
        )


@dataclass
class ParsedMonthlyBudget:
    month_key: str
    source_file: Path
    total_budget: str
    summary_values: dict[str, str]
    income_lines: list[ParsedBudgetLine]
    expense_lines: list[ParsedBudgetLine]

    @property
    def budget_id(self) -> str:
        return stable_hash("budget", self.month_key)

    def to_model(self, updated_at: str) -> MonthlyBudget:
        summary_lines = [
            SYNC_NOTE_MARKER,
            f"来源文件：{self.source_file}",
            f"更新时间：{updated_at}",
        ]
        for key in (
            "预期收入",
            "实际收入",
            "预期支出",
            "实际支出",
            "预期结余",
            "实际结余",
        ):
            if key in self.summary_values:
                summary_lines.append(f"{key}：{self.summary_values[key]}")
        return MonthlyBudget(
            id=self.budget_id,
            month_key=self.month_key,
            total_budget=self.total_budget,
            notes="\n".join(summary_lines),
            status="待确认",
            created_at=updated_at,
            updated_at=updated_at,
        )


@dataclass
class SyncReport:
    synced_dates: list[str] = field(default_factory=list)
    synced_months: list[str] = field(default_factory=list)
    transactions_added: int = 0
    transactions_updated: int = 0
    transactions_skipped: int = 0
    deletion_candidates: list[str] = field(default_factory=list)
    budgets_synced: int = 0
    budget_lines_synced: int = 0
    budget_lines_removed: int = 0
    reminders_upserted: int = 0
    reminders_disabled: int = 0
    skipped_details: list[str] = field(default_factory=list)

    def render_text(self) -> str:
        lines = [
            "Obsidian 私帐同步结果",
            f"- 同步日期：{', '.join(self.synced_dates) if self.synced_dates else '无'}",
            f"- 同步月份：{', '.join(self.synced_months) if self.synced_months else '无'}",
            f"- 交易新增：{self.transactions_added}",
            f"- 交易更新：{self.transactions_updated}",
            f"- 交易跳过：{self.transactions_skipped}",
            f"- 删除候选：{len(self.deletion_candidates)}",
            f"- 月预算同步：{self.budgets_synced}",
            f"- 预算项同步：{self.budget_lines_synced}",
            f"- 预算项移除：{self.budget_lines_removed}",
            f"- 提醒写入：{self.reminders_upserted}",
            f"- 提醒停用：{self.reminders_disabled}",
        ]
        if self.deletion_candidates:
            lines.append(f"- 删除候选明细：{'; '.join(self.deletion_candidates)}")
        if self.skipped_details:
            lines.append(f"- 跳过明细：{'; '.join(self.skipped_details)}")
        return "\n".join(lines)


def stable_hash(prefix: str, *parts: str) -> str:
    raw = "||".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def resolve_private_ledger_root(obsidian_root: str | Path) -> Path:
    candidate = Path(obsidian_root).expanduser()
    if (candidate / PRIVATE_LEDGER_RELATIVE_DIR).exists():
        return candidate / PRIVATE_LEDGER_RELATIVE_DIR
    if (candidate / DAILY_RELATIVE_DIR).exists() and (candidate / MONTHLY_RELATIVE_DIR).exists():
        return candidate
    raise FileNotFoundError(f"Cannot locate 财务/私帐 under: {candidate}")


def read_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip()] = text[start:end].strip()
    return sections


def extract_source_attachment(text: str) -> str:
    attachment_matches = re.findall(r"(账单_[0-9]{12}\.(?:xlsx|csv))", text)
    if attachment_matches:
        return " / ".join(dict.fromkeys(attachment_matches))
    matches = re.findall(r"`([^`]+)`", text)
    return " / ".join(dict.fromkeys(matches))


def parse_money(value: str) -> str | None:
    cleaned = value.replace("元", "").replace(",", "").strip()
    if cleaned in {"", "-", "待回填"}:
        return None
    try:
        return f"{parse_decimal(cleaned):.2f}"
    except Exception:
        return None


def parse_markdown_table(section_text: str) -> list[dict[str, str]]:
    rows = [line.strip() for line in section_text.splitlines() if line.strip().startswith("|")]
    if len(rows) < 2:
        return []
    headers = [cell.strip() for cell in rows[0].strip("|").split("|")]
    payload: list[dict[str, str]] = []
    for row in rows[2:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        payload.append(dict(zip(headers, cells)))
    return payload


def parse_daily_note(path: Path) -> ParsedDailyNote:
    text = path.read_text(encoding="utf-8")
    sections = read_sections(text)
    remarks_text = sections.get("备注", "")
    collection_text = sections.get("本次采集情况", "")
    amount_change_text = sections.get("金额变动", "")
    source_attachment = extract_source_attachment("\n".join([remarks_text, collection_text, amount_change_text]))
    has_rescan = "回扫" in text or "金额变动" in text
    transactions: list[ParsedTransaction] = []
    skipped_lines: list[str] = []

    for transaction_type, section_name in (("收入", "收入明细"), ("支出", "支出明细")):
        section_text = sections.get(section_name, "")
        current_label = ""
        occurrence_counts: dict[str, int] = {}
        for raw_line in section_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            label_match = LABEL_RE.match(line)
            if label_match:
                current_label = label_match.group(1).strip()
                continue
            transaction_match = TRANSACTION_RE.match(line)
            if transaction_match and current_label:
                time_text = transaction_match.group(1)
                amount_text = transaction_match.group(2)
                merchant = transaction_match.group(3).strip()
                base_key = f"{path.stem}|{time_text}|{transaction_type}|{merchant}"
                occurrence_index = occurrence_counts.get(base_key, 0) + 1
                occurrence_counts[base_key] = occurrence_index
                transaction_id = stable_hash("txn-obs", base_key, str(occurrence_index))
                transactions.append(
                    ParsedTransaction(
                        transaction_id=transaction_id,
                        occurred_on=f"{path.stem} {time_text}",
                        transaction_type=transaction_type,
                        category=current_label,
                        amount=f"{parse_decimal(amount_text):.2f}",
                        merchant=merchant,
                        file_date=path.stem,
                        file_path=path,
                        source_line=line.removeprefix("- ").strip(),
                        source_attachment=source_attachment,
                        has_rescan=has_rescan,
                    )
                )
            elif TRANSACTION_CANDIDATE_RE.match(line) and not current_label:
                skipped_lines.append(f"{path.name}: 缺少标签上下文 -> {line}")
            elif TRANSACTION_CANDIDATE_RE.match(line) and not TRANSACTION_RE.match(line):
                skipped_lines.append(f"{path.name}: 无法识别明细 -> {line}")

    return ParsedDailyNote(
        note_date=path.stem,
        path=path,
        transactions=transactions,
        source_attachment=source_attachment,
        skipped_lines=skipped_lines,
    )


def parse_monthly_budget(path: Path) -> ParsedMonthlyBudget:
    text = path.read_text(encoding="utf-8")
    sections = read_sections(text)
    overview_pairs = {
        key.strip(): value.strip()
        for key, value in OVERVIEW_RE.findall(sections.get("总览", ""))
    }
    income_rows = parse_markdown_table(sections.get("收入预期与实际", ""))
    expense_rows = parse_markdown_table(sections.get("支出预期与实际", ""))
    month_key = path.stem.replace("-预期与实际", "")
    total_budget = parse_money(overview_pairs.get("预期支出", "")) or "0.00"

    def build_lines(rows: list[dict[str, str]], line_kind: str) -> list[ParsedBudgetLine]:
        parsed: list[ParsedBudgetLine] = []
        for row in rows:
            name = row.get("项目", "").strip()
            if not name or name == "合计":
                continue
            planned_amount = parse_money(row.get("预期", "") or "")
            if planned_amount is None:
                continue
            parsed.append(
                ParsedBudgetLine(
                    line_id=stable_hash("bline-obs", month_key, line_kind, name),
                    line_kind=line_kind,
                    name=name,
                    category=name,
                    planned_amount=planned_amount,
                    actual_amount=(row.get("实际", "") or "").strip(),
                    delta_amount=(row.get("偏差", "") or "").strip(),
                )
            )
        return parsed

    return ParsedMonthlyBudget(
        month_key=month_key,
        source_file=path,
        total_budget=total_budget,
        summary_values=overview_pairs,
        income_lines=build_lines(income_rows, "收入"),
        expense_lines=build_lines(expense_rows, "支出"),
    )


def build_budget_reminders(monthly_budget: ParsedMonthlyBudget, synced_at: str) -> list[ReminderItem]:
    reminders: list[ReminderItem] = []
    for line in monthly_budget.expense_lines:
        planned = parse_money(line.planned_amount)
        actual = parse_money(line.actual_amount)
        if planned is None or actual is None:
            continue
        planned_amount = parse_decimal(planned)
        if planned_amount <= Decimal("0.00"):
            continue
        actual_amount = parse_decimal(actual)
        ratio = actual_amount / planned_amount if planned_amount else Decimal("0.00")
        if ratio < Decimal("0.90"):
            continue
        alert_level = "预算超支提醒" if actual_amount > planned_amount else "预算临界提醒"
        title = f"{monthly_budget.month_key} {line.name} {alert_level}"
        notes = "\n".join(
            [
                SYNC_NOTE_MARKER,
                f"同步月份：{monthly_budget.month_key}",
                f"预算项：{line.name}",
                f"预算：{planned}",
                f"实际：{actual}",
                f"进度：{(ratio * Decimal('100')).quantize(Decimal('0.01'))}%",
                f"来源文件：{monthly_budget.source_file}",
                f"更新时间：{synced_at}",
            ]
        )
        reminders.append(
            ReminderItem(
                id=stable_hash("rem-obs", monthly_budget.month_key, line.name),
                title=title,
                reminder_kind="阈值提醒",
                target_type="预算进度",
                account_id="",
                due_date="",
                threshold_amount=planned,
                current_value=actual,
                status="停用",
                source=SYNC_SOURCE,
                notes=notes,
                created_at=synced_at,
                updated_at=synced_at,
            )
        )
    return reminders


class ObsidianLedgerSyncService:
    def __init__(self, repository: LedgerRepository) -> None:
        self.repository = repository

    def resolve_obsidian_root(self, obsidian_root: str | Path | None = None) -> Path:
        if obsidian_root:
            return resolve_private_ledger_root(obsidian_root)
        settings = self.repository.load_settings()
        if settings.obsidian_path:
            try:
                return resolve_private_ledger_root(settings.obsidian_path)
            except FileNotFoundError:
                pass
        return resolve_private_ledger_root(DEFAULT_OBSIDIAN_ROOT)

    def sync(
        self,
        obsidian_root: str | Path | None = None,
        dates: list[str] | None = None,
        months: list[str] | None = None,
    ) -> SyncReport:
        synced_at = now_timestamp()
        report = SyncReport()
        private_root = self.resolve_obsidian_root(obsidian_root)
        daily_dir = private_root / DAILY_RELATIVE_DIR
        monthly_dir = private_root / MONTHLY_RELATIVE_DIR

        daily_paths = sorted(daily_dir.glob("*.md"))
        target_dates = set(dates or [])
        if target_dates:
            daily_paths = [path for path in daily_paths if path.stem in target_dates]

        month_filters = set(months or [])
        if not month_filters and target_dates:
            month_filters = {value[:7] for value in target_dates}
        monthly_paths = sorted(monthly_dir.glob("????-??-预期与实际.md"))
        if month_filters:
            monthly_paths = [path for path in monthly_paths if path.stem.replace("-预期与实际", "") in month_filters]

        report.synced_dates = [path.stem for path in daily_paths]
        report.synced_months = [path.stem.replace("-预期与实际", "") for path in monthly_paths]

        self._sync_transactions(daily_paths=daily_paths, synced_at=synced_at, report=report)
        self._sync_budgets(monthly_paths=monthly_paths, synced_at=synced_at, report=report)
        return report

    def _sync_transactions(self, daily_paths: list[Path], synced_at: str, report: SyncReport) -> None:
        existing_by_id = {item.id: item for item in self.repository.list_transactions()}
        grouped_existing: dict[str, set[str]] = {}
        for item in existing_by_id.values():
            if item.source != SYNC_SOURCE:
                continue
            date_key = item.occurred_on[:10]
            grouped_existing.setdefault(date_key, set()).add(item.id)

        for path in daily_paths:
            parsed = parse_daily_note(path)
            current_ids: set[str] = set()
            for skipped in parsed.skipped_lines:
                report.transactions_skipped += 1
                report.skipped_details.append(skipped)
            for transaction in parsed.transactions:
                current_ids.add(transaction.transaction_id)
                existing = existing_by_id.get(transaction.transaction_id)
                model = transaction.to_model(synced_at=synced_at)
                if existing is None:
                    report.transactions_added += 1
                else:
                    report.transactions_updated += 1
                    model.created_at = existing.created_at
                self.repository.upsert_transaction(model)
            stale_ids = sorted(grouped_existing.get(parsed.note_date, set()) - current_ids)
            for transaction_id in stale_ids:
                existing = existing_by_id.get(transaction_id)
                if existing is None:
                    continue
                report.deletion_candidates.append(
                    f"{parsed.note_date}｜{existing.transaction_type}｜{existing.category}｜{existing.amount} 元"
                )

    def _sync_budgets(self, monthly_paths: list[Path], synced_at: str, report: SyncReport) -> None:
        existing_reminders = {item.id: item for item in self.repository.list_reminders()}
        for path in monthly_paths:
            parsed = parse_monthly_budget(path)
            budget = parsed.to_model(updated_at=synced_at)
            existing_budget = self.repository.get_monthly_budget(parsed.month_key)
            if existing_budget is not None:
                budget.id = existing_budget.id
                budget.created_at = existing_budget.created_at
            self.repository.upsert_budget(budget)
            report.budgets_synced += 1

            expected_line_ids = {item.line_id for item in parsed.income_lines + parsed.expense_lines}
            existing_lines = self.repository.list_budget_lines(budget.id)
            for stale_line in existing_lines:
                if stale_line.id not in expected_line_ids and stale_line.notes.startswith(SYNC_NOTE_MARKER):
                    self.repository.delete_budget_line(stale_line.id)
                    report.budget_lines_removed += 1

            for line in parsed.income_lines + parsed.expense_lines:
                existing_line = next((item for item in existing_lines if item.id == line.line_id), None)
                model = line.to_model(budget_id=budget.id, month_key=parsed.month_key, source_file=path, updated_at=synced_at)
                if existing_line is not None:
                    model.created_at = existing_line.created_at
                self.repository.upsert_budget_line(model)
                report.budget_lines_synced += 1

            generated_reminders = build_budget_reminders(parsed, synced_at=synced_at)
            current_reminder_ids = {item.id for item in generated_reminders}
            for reminder in generated_reminders:
                existing = existing_reminders.get(reminder.id)
                if existing is not None:
                    reminder.created_at = existing.created_at
                self.repository.upsert_reminder(reminder)
                report.reminders_upserted += 1

            for existing in self.repository.list_reminders():
                if existing.source != SYNC_SOURCE:
                    continue
                if f"同步月份：{parsed.month_key}" not in existing.notes:
                    continue
                if existing.id in current_reminder_ids:
                    continue
                disabled = ReminderItem(
                    id=existing.id,
                    title=existing.title,
                    reminder_kind=existing.reminder_kind,
                    target_type=existing.target_type,
                    account_id=existing.account_id,
                    due_date=existing.due_date,
                    threshold_amount=existing.threshold_amount,
                    current_value=existing.current_value,
                    status="停用",
                    source=existing.source,
                    notes=existing.notes,
                    created_at=existing.created_at,
                    updated_at=synced_at,
                )
                self.repository.upsert_reminder(disabled)
                report.reminders_disabled += 1
