from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTextEdit

from private_ledger.ui.widgets import create_card, prepare_table


def test_prepare_table_keeps_header_columns_readable_without_rows(qapp) -> None:
    table = QTableWidget()
    prepare_table(table, ["账户", "类型", "用途", "当前余额", "状态"])

    widths = [table.columnWidth(index) for index in range(table.columnCount())]

    assert widths[0] >= 88
    assert widths[3] >= 96


def test_create_card_assigns_budget_semantics_by_structure(qapp) -> None:
    workspace_card, _workspace_layout = create_card("预算月度工作台", "先看预算，再看差额。")
    ledger_card, _ledger_layout = create_card("计划支出项", "拆开看每类支出。")
    editor_shell, editor_layout = create_card("预算编辑", "预算项会和当月工作台联动。")

    assert workspace_card.objectName() == "ToolbarCard"
    assert workspace_card.property("sectionRole") == "budget-workbench"
    assert workspace_card.property("sectionContext") == "budget"
    assert ledger_card.objectName() == "SectionCard"
    assert ledger_card.property("sectionRole") == "budget-ledger"
    assert ledger_card.property("cardVariant") == "table"

    editor_panel = editor_layout.parentWidget()
    assert editor_shell.objectName() == "SectionCardShell"
    assert editor_panel is not None
    assert editor_panel.objectName() == "DetailPane"
    assert editor_panel.property("sectionRole") == "budget-workbench-editor"
    assert editor_panel.property("sectionContext") == "budget"


def test_create_card_assigns_reminder_list_semantics_and_normalizes_notes_panel(qapp) -> None:
    list_card, _list_layout = create_card("提醒列表", "按状态查看提醒。")
    detail_card, detail_layout = create_card("", "")
    notes_edit = QTextEdit()
    notes_edit.setMinimumHeight(120)
    detail_layout.addWidget(notes_edit)
    qapp.processEvents()

    assert list_card.objectName() == "ListPane"
    assert list_card.property("sectionRole") == "reminder-list"
    assert list_card.property("sectionContext") == "reminder"
    assert detail_card.objectName() == "DetailPane"
    assert detail_card.property("sectionRole") == "detail-stack"
    assert detail_card.property("sectionVariant") == "notes-panel"
    assert notes_edit.minimumHeight() >= 260
