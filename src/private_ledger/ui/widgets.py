from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def refresh_style(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.repaint()


def _apply_properties(widget: QWidget, properties: dict[str, str]) -> None:
    for key, value in properties.items():
        widget.setProperty(key, value)


def _copy_properties(source: QWidget, target: QWidget, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = source.property(key)
        if value:
            target.setProperty(key, value)


def _metric_properties(title: str) -> dict[str, str]:
    normalized = title.strip()
    properties: dict[str, str] = {}
    if normalized.startswith("全年"):
        properties["metricScope"] = "annual"
        properties["metricDensity"] = "compact"
        if "计划" in normalized:
            properties["metricTone"] = "planned"
        elif "实际" in normalized:
            properties["metricTone"] = "actual"
        elif "待确认" in normalized:
            properties["metricTone"] = "pending"
    return properties


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _is_budget_workspace_title(title: str) -> bool:
    return "工作台" in title and "预算" in title


def _is_budget_comparison_title(title: str) -> bool:
    return _contains_any(title, ("预算项对比", "预算对比"))


def _is_budget_ledger_title(title: str) -> bool:
    return title.endswith("收入项") or title.endswith("支出项")


def _is_budget_editor_title(title: str, subtitle: str) -> bool:
    return "编辑" in title and _contains_any(title + subtitle, ("预算", "预算项", "工作台"))


def _is_annual_summary_title(title: str) -> bool:
    return "全年" in title and _contains_any(title, ("十二月", "12月", "月度"))


def _is_annual_detail_title(title: str) -> bool:
    return "年度明细" in title


def _is_scope_reference_title(title: str, subtitle: str) -> bool:
    return "生效" in title and _contains_any(title + subtitle, ("范围", "口径", "预算"))


def _is_reminder_list_title(title: str) -> bool:
    return "提醒" in title and _contains_any(title, ("列表", "清单"))


def _is_reminder_detail_title(title: str, subtitle: str) -> bool:
    return "提醒" in title and _contains_any(title + subtitle, ("详情", "编辑"))


def _is_dashboard_trend_title(title: str) -> bool:
    return "趋势" in title


def _is_dashboard_queue_title(title: str) -> bool:
    return "近期待处理" in title


def _is_dashboard_accounts_title(title: str) -> bool:
    return "账户余额概览" in title


def _is_dashboard_transactions_title(title: str) -> bool:
    return "最近流水" in title


def _is_dashboard_pending_title(title: str) -> bool:
    return "待确认事项" in title


class TagLabel(QLabel):
    def __init__(self, text: str = "", tone: str = "gray") -> None:
        super().__init__(text)
        self.setObjectName("TagLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_tone(tone)

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        refresh_style(self)


class MetricCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("MetricCard")
        metric_properties = _metric_properties(title)
        _apply_properties(self, metric_properties)
        compact = metric_properties.get("metricDensity") == "compact"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12 if compact else 14, 10 if compact else 12, 12 if compact else 14, 10 if compact else 12)
        layout.setSpacing(6 if compact else 8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6 if compact else 8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")
        _copy_properties(self, self.title_label, ("metricScope", "metricDensity", "metricTone"))
        self.tag_label = TagLabel("", "gray")
        _copy_properties(self, self.tag_label, ("metricScope", "metricDensity", "metricTone"))
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)
        top_row.addWidget(self.tag_label)

        self.value_label = QLabel("--")
        self.value_label.setObjectName("MetricValue")
        _copy_properties(self, self.value_label, ("metricScope", "metricDensity", "metricTone"))
        self.note_label = QLabel("")
        self.note_label.setObjectName("MetricNote")
        self.note_label.setWordWrap(True)
        _copy_properties(self, self.note_label, ("metricScope", "metricDensity", "metricTone"))

        layout.addLayout(top_row)
        layout.addWidget(self.value_label)
        layout.addWidget(self.note_label)

    def set_content(self, value: str, note: str = "", tag_text: str = "", tag_tone: str = "gray") -> None:
        self.value_label.setText(value)
        self.note_label.setText(note)
        self.tag_label.setText(tag_text)
        self.tag_label.setVisible(bool(tag_text))
        self.tag_label.set_tone(tag_tone)


class CardFrame(QFrame):
    def childEvent(self, event) -> None:
        super().childEvent(event)
        if self.property("sectionVariant") == "notes-panel":
            QTimer.singleShot(0, self._normalize_notes_panel)

    def _normalize_notes_panel(self) -> None:
        if self.property("sectionVariant") != "notes-panel":
            return
        for text_edit in self.findChildren(QTextEdit):
            text_edit.setMinimumHeight(max(text_edit.minimumHeight(), 260))


def _card_object_name(title: str, subtitle: str) -> str:
    normalized = title.strip()
    if _is_budget_workspace_title(normalized):
        return "ToolbarCard"
    if not normalized and not subtitle:
        return "DetailPane"
    if _is_reminder_detail_title(normalized, subtitle) or any(keyword in normalized for keyword in ("详情", "编辑")):
        return "DetailPane"
    if _is_reminder_list_title(normalized) or any(keyword in normalized for keyword in ("列表", "清单")):
        return "ListPane"
    return "SectionCard"


def _card_properties(title: str, subtitle: str = "") -> dict[str, str]:
    normalized = title.strip()
    properties: dict[str, str] = {}
    if _is_budget_workspace_title(normalized) or _is_annual_summary_title(normalized):
        properties["cardVariant"] = "workspace"
        properties["sectionContext"] = "budget"
    if _is_budget_workspace_title(normalized):
        properties["sectionRole"] = "budget-workbench"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_budget_comparison_title(normalized):
        properties["sectionRole"] = "budget-workbench-primary"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_budget_ledger_title(normalized):
        properties["cardVariant"] = "table"
        properties["sectionRole"] = "budget-ledger"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_budget_editor_title(normalized, subtitle):
        properties["cardVariant"] = "editor"
        properties["sectionRole"] = "budget-workbench-editor"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_annual_summary_title(normalized):
        properties["sectionRole"] = "annual-summary"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_annual_detail_title(normalized):
        properties["sectionRole"] = "annual-detail"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_scope_reference_title(normalized, subtitle):
        properties["sectionRole"] = "scope-reference"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif _is_dashboard_trend_title(normalized):
        properties["cardVariant"] = "workspace"
        properties["sectionRole"] = "dashboard-trend"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "dashboard"
    elif _is_dashboard_queue_title(normalized):
        properties["cardVariant"] = "list"
        properties["sectionRole"] = "dashboard-reminders"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "dashboard"
    elif _is_dashboard_accounts_title(normalized):
        properties["cardVariant"] = "table"
        properties["sectionRole"] = "dashboard-accounts"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "dashboard"
    elif _is_dashboard_transactions_title(normalized):
        properties["cardVariant"] = "table"
        properties["sectionRole"] = "dashboard-transactions"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "dashboard"
    elif _is_dashboard_pending_title(normalized):
        properties["cardVariant"] = "list"
        properties["sectionRole"] = "dashboard-pending"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "dashboard"
    elif _contains_any(normalized + subtitle, ("预算", "工作台")) and _contains_any(normalized, ("月份", "月度")):
        properties["sectionRole"] = "budget-month-switcher"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "budget"
    elif not normalized and not subtitle:
        properties["cardVariant"] = "detail"
        properties["sectionRole"] = "detail-stack"
        properties["sectionVariant"] = "notes-panel"
        properties["sectionDensity"] = "compact"
    elif _is_reminder_detail_title(normalized, subtitle):
        properties["cardVariant"] = "detail"
        properties["sectionRole"] = "reminder-detail"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "reminder"
    elif _is_reminder_list_title(normalized):
        properties["cardVariant"] = "list"
        properties["sectionRole"] = "reminder-list"
        properties["sectionDensity"] = "compact"
        properties["sectionContext"] = "reminder"
    elif any(keyword in normalized for keyword in ("详情", "编辑")):
        properties["cardVariant"] = "detail"
        properties["sectionRole"] = "detail-stack"
        properties["sectionDensity"] = "compact"
    elif any(keyword in normalized for keyword in ("列表", "清单")):
        properties["cardVariant"] = "list"
        properties["sectionRole"] = "stacked-list"
        properties["sectionDensity"] = "compact"
    return properties


def _create_card_frame(title: str, subtitle: str) -> tuple[QFrame, QFrame]:
    properties = _card_properties(title, subtitle)
    if _is_budget_editor_title(title.strip(), subtitle):
        shell = CardFrame()
        shell.setObjectName("SectionCardShell")
        shell.setProperty("cardVariant", "editor-shell")
        _apply_properties(shell, {key: value for key, value in properties.items() if key != "cardVariant"})
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addStretch(1)

        panel = CardFrame()
        panel.setObjectName("DetailPane")
        panel.setProperty("cardVariant", "editor")
        _apply_properties(panel, {key: value for key, value in properties.items() if key != "cardVariant"})
        panel.setMinimumWidth(400)
        panel.setMaximumWidth(520)
        panel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        shell_layout.addWidget(panel, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        return shell, panel

    frame = CardFrame()
    frame.setObjectName(_card_object_name(title, subtitle))
    _apply_properties(frame, properties)
    return frame, frame


def create_card(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame, content_frame = _create_card_frame(title, subtitle)
    compact = content_frame.property("sectionDensity") == "compact"
    section_role = content_frame.property("sectionRole") or ""
    relaxed_panel = section_role in {"budget-workbench-editor", "detail-stack", "stacked-list"}
    layout = QVBoxLayout(content_frame)
    if relaxed_panel:
        layout.setContentsMargins(16, 15, 16, 15)
        layout.setSpacing(12)
    else:
        layout.setContentsMargins(14 if compact else 16, 13 if compact else 15, 14 if compact else 16, 13 if compact else 15)
        layout.setSpacing(10 if compact else 12)
    if title:
        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2 if compact else 3)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        _copy_properties(content_frame, title_label, ("sectionRole", "sectionDensity"))
        header.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("MutedText")
            subtitle_label.setWordWrap(True)
            _copy_properties(content_frame, subtitle_label, ("sectionRole", "sectionDensity"))
            header.addWidget(subtitle_label)
        layout.addLayout(header)
    return frame, layout


def make_secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("SecondaryActionButton")
    return button


def make_danger_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("DangerActionButton")
    return button


def _table_profile(headers: list[str]) -> tuple[str, str, str]:
    annual_summary_headers = ["口径"] + [f"{month}月" for month in range(1, 13)]
    if headers == annual_summary_headers:
        return "dense", "matrix", "annual-summary"
    if headers[:4] == ["预算项", "类型", "标签", "生效月份"] and len(headers) > 20:
        return "dense", "matrix", "annual-detail"
    if headers == ["预算项", "类型", "标签", "生效方式", "开始月份", "结束月份", "计划", "已确认", "待确认", "差额"]:
        return "dense", "ledger", "budget-workbench"
    if headers == ["预算项", "类型", "标签", "备注", "生效月份", "计划", "已确认实际", "待确认", "差额", "进度", "状态"]:
        return "dense", "ledger", "budget-ledger"
    if headers == ["生效方式", "适合场景", "显示口径"]:
        return "regular", "ledger", "scope-reference"
    return ("dense" if len(headers) >= 10 else "regular", "matrix" if len(headers) >= 20 else "ledger", "default")


def prepare_table(table: QTableWidget, headers: list[str]) -> None:
    density, table_role, table_profile = _table_profile(headers)
    table.setProperty("tableDensity", density)
    table.setProperty("tableRole", table_role)
    table.setProperty("tableProfile", table_profile)
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    if table_profile == "annual-summary":
        table.verticalHeader().setDefaultSectionSize(32)
    elif density == "dense":
        table.verticalHeader().setDefaultSectionSize(36)
    else:
        table.verticalHeader().setDefaultSectionSize(40)
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSortingEnabled(False)
    table.setWordWrap(False)
    table.setShowGrid(False)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    header = table.horizontalHeader()
    if table_profile == "annual-summary":
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setMinimumSectionSize(58)
    else:
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setMinimumSectionSize(82 if density == "dense" else 88)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    header.setStretchLastSection(False)
    sync_table_columns(table)


def sync_table_columns(table: QTableWidget) -> None:
    header = table.horizontalHeader()
    metrics = QFontMetrics(header.font())
    density = table.property("tableDensity") or "regular"
    table_role = table.property("tableRole") or "ledger"
    table_profile = table.property("tableProfile") or "default"
    if table_profile == "annual-summary":
        for column in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(column)
            header_text = header_item.text() if header_item is not None else ""
            if column == 0:
                minimum = max(112, metrics.horizontalAdvance(header_text) + 28)
                content_padding = 18
            else:
                minimum = max(58, metrics.horizontalAdvance(header_text) + 14)
                content_padding = 10
            content = table.sizeHintForColumn(column)
            table.setColumnWidth(column, max(minimum, content + content_padding))
        if table.columnCount() > 0:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(table.columnCount() - 1, QHeaderView.ResizeMode.Stretch)
        return

    padding = 36 if density == "dense" else 48
    minimum_width = 84 if density == "dense" else 96
    for column in range(table.columnCount()):
        header_item = table.horizontalHeaderItem(column)
        header_text = header_item.text() if header_item is not None else ""
        minimum = max(minimum_width, metrics.horizontalAdvance(header_text) + padding)
        if table_profile == "annual-detail" and column > 3:
            minimum = max(72, metrics.horizontalAdvance(header_text) + 24)
        elif table_role == "matrix" and column > 0:
            minimum = max(78, metrics.horizontalAdvance(header_text) + 28)
        elif table_profile == "budget-workbench":
            minimum = max(80, metrics.horizontalAdvance(header_text) + 30)
        content = table.sizeHintForColumn(column)
        if table_profile == "annual-detail":
            content_padding = 18
        elif table_profile == "budget-workbench":
            content_padding = 18
        else:
            content_padding = 20 if density == "dense" else 24
        table.setColumnWidth(column, max(minimum, content + content_padding))
    if table.columnCount() > 0:
        if table_profile == "budget-ledger":
            for column in range(table.columnCount()):
                if column in {0, 1}:
                    header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
                    table.setColumnWidth(column, min(table.columnWidth(column), 112))
                elif column >= 2:
                    header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        elif table_profile == "budget-workbench":
            compact_columns = {
                0: 132,
                1: 92,
                2: 126,
                3: 98,
                4: 96,
                5: 96,
            }
            for column in range(table.columnCount()):
                if column in compact_columns:
                    header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
                    table.setColumnWidth(column, min(table.columnWidth(column), compact_columns[column]))
                else:
                    header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(table.columnCount() - 1, QHeaderView.ResizeMode.Stretch)
