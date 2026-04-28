from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from private_ledger.domain.models import ImportBatch
from private_ledger.ui.widgets import create_card, make_secondary_button, prepare_table, sync_table_columns


class ImportsPage(QWidget):
    choose_image_requested = Signal()
    paste_image_requested = Signal()
    recognize_requested = Signal()
    confirm_import_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.selected_image_path = ""
        self.current_batch_id = ""
        self._batches: list[ImportBatch] = []

        self.choose_button = QPushButton("选择图片")
        self.paste_button = make_secondary_button("粘贴截图")
        self.recognize_button = QPushButton("开始识别")
        self.confirm_button = QPushButton("确认入账")
        self.status_label = QLabel("请先选择图片或粘贴截图。")
        self.status_label.setObjectName("MutedText")
        self.image_label = QLabel("暂无图片")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(220)
        self.image_label.setObjectName("ReadonlyBox")

        self.batch_table = QTableWidget()
        prepare_table(self.batch_table, ["状态", "文件", "更新时间"])

        self.ocr_text = QPlainTextEdit()
        self.ocr_text.setReadOnly(True)
        self.structured_text = QPlainTextEdit()
        self.structured_text.setReadOnly(True)
        self.transaction_table = QTableWidget()
        prepare_table(self.transaction_table, ["日期", "类型", "标签", "金额", "依据"])
        self.reminder_table = QTableWidget()
        prepare_table(self.reminder_table, ["标题", "类型", "日期/阈值", "依据"])

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        input_card, input_layout = create_card("图片识别入口", "本地图片或剪贴板截图，识别结果只生成待确认草稿")
        button_row = QHBoxLayout()
        button_row.addWidget(self.choose_button)
        button_row.addWidget(self.paste_button)
        button_row.addWidget(self.recognize_button)
        button_row.addStretch(1)
        input_layout.addLayout(button_row)
        input_layout.addWidget(self.image_label)
        input_layout.addWidget(self.status_label)

        batch_card, batch_layout = create_card("导入批次", "保留 OCR 文本、结构化结果和处理状态")
        batch_layout.addWidget(self.batch_table)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)
        left_layout.addWidget(input_card)
        left_layout.addWidget(batch_card)

        ocr_card, ocr_layout = create_card("OCR 原文", "由 MiniMax OCR MCP 识别")
        ocr_layout.addWidget(self.ocr_text)
        structured_card, structured_layout = create_card("结构化 JSON", "由 MiniMax-M2.7 保守抽取")
        structured_layout.addWidget(self.structured_text)

        draft_card, draft_layout = create_card("待确认草稿", "确认后流水为待确认，提醒默认停用")
        draft_layout.addWidget(QLabel("流水草稿"))
        draft_layout.addWidget(self.transaction_table)
        draft_layout.addWidget(QLabel("提醒草稿"))
        draft_layout.addWidget(self.reminder_table)
        draft_layout.addWidget(self.confirm_button)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.addWidget(ocr_card)
        right_layout.addWidget(structured_card)
        right_layout.addWidget(draft_card)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.choose_button.clicked.connect(self.choose_image_requested.emit)
        self.paste_button.clicked.connect(self.paste_image_requested.emit)
        self.recognize_button.clicked.connect(self.recognize_requested.emit)
        self.confirm_button.clicked.connect(self._emit_confirm)
        self.batch_table.itemSelectionChanged.connect(self._handle_batch_selection)

    def set_selected_image(self, image_path: str) -> None:
        self.selected_image_path = image_path
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setText(Path(image_path).name)
            return
        self.image_label.setPixmap(
            pixmap.scaled(380, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        self.status_label.setText(f"已选择：{image_path}")

    def load_batches(self, batches: list[ImportBatch]) -> None:
        self._batches = list(batches)
        self.batch_table.setRowCount(len(self._batches))
        for row_index, batch in enumerate(self._batches):
            values = [batch.status, batch.original_file_name, batch.updated_at]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, batch.id)
                self.batch_table.setItem(row_index, column_index, item)
        sync_table_columns(self.batch_table)
        if self._batches and not self.current_batch_id:
            self.batch_table.setCurrentCell(0, 0)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def show_batch(self, batch: ImportBatch | None) -> None:
        if batch is None:
            self.current_batch_id = ""
            self.ocr_text.clear()
            self.structured_text.clear()
            self.transaction_table.setRowCount(0)
            self.reminder_table.setRowCount(0)
            return
        self.current_batch_id = batch.id
        self.ocr_text.setPlainText(batch.raw_ocr_text)
        self.structured_text.setPlainText(batch.structured_json)
        self.set_selected_image(batch.source_file_path)
        self.status_label.setText(f"批次状态：{batch.status}" + (f" · {batch.error_message}" if batch.error_message else ""))
        self._render_drafts(batch.structured_json)

    def _render_drafts(self, structured_json: str) -> None:
        try:
            payload = json.loads(structured_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        transactions = payload.get("transactions") or []
        self.transaction_table.setRowCount(len(transactions))
        for row_index, draft in enumerate(transactions):
            values = [
                str(draft.get("occurred_on") or ""),
                str(draft.get("transaction_type") or ""),
                str(draft.get("category") or ""),
                str(draft.get("amount") or ""),
                str(draft.get("source_snippet") or ""),
            ]
            for column_index, value in enumerate(values):
                self.transaction_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.transaction_table)

        reminders = payload.get("reminders") or []
        self.reminder_table.setRowCount(len(reminders))
        for row_index, draft in enumerate(reminders):
            when_text = str(draft.get("due_date") or draft.get("threshold_amount") or "")
            values = [
                str(draft.get("title") or ""),
                str(draft.get("target_type") or ""),
                when_text,
                str(draft.get("source_snippet") or ""),
            ]
            for column_index, value in enumerate(values):
                self.reminder_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.reminder_table)

    def _handle_batch_selection(self) -> None:
        row = self.batch_table.currentRow()
        if row < 0:
            return
        item = self.batch_table.item(row, 0)
        if item is None:
            return
        batch_id = item.data(Qt.ItemDataRole.UserRole)
        batch = next((item for item in self._batches if item.id == batch_id), None)
        self.show_batch(batch)

    def _emit_confirm(self) -> None:
        if self.current_batch_id:
            self.confirm_import_requested.emit(self.current_batch_id)
