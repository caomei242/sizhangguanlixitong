from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from private_ledger.ui.widgets import (
    MetricCard,
    TagLabel,
    create_card,
    make_danger_button,
    make_secondary_button,
    refresh_style,
    prepare_table,
    sync_table_columns,
)


class ReminderListRow(QFrame):
    def __init__(
        self,
        title: str,
        meta: str,
        focus_text: str,
        source_text: str,
        note_text: str,
        light_text: str,
        light_tone: str,
        status: str,
    ) -> None:
        super().__init__()
        self.setObjectName("ReminderRow")
        self.setProperty("selected", False)
        self.setProperty("tone", light_tone)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(5)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ReminderRowTitle")
        self.title_label.setWordWrap(True)
        self.meta_label = QLabel(meta)
        self.meta_label.setObjectName("ReminderRowMeta")
        self.meta_label.setWordWrap(True)
        self.focus_label = QLabel(focus_text)
        self.focus_label.setObjectName("ReminderRowMeta")
        self.focus_label.setWordWrap(True)
        self.source_label = QLabel(source_text)
        self.source_label.setObjectName("ReminderRowMeta")
        self.source_label.setWordWrap(True)
        self.note_label = QLabel(f"备注摘要：{note_text}")
        self.note_label.setObjectName("ReminderRowMeta")
        self.note_label.setWordWrap(True)
        text_box.addWidget(self.title_label)
        text_box.addWidget(self.meta_label)
        text_box.addWidget(self.focus_label)
        text_box.addWidget(self.source_label)
        text_box.addWidget(self.note_label)

        self.light_label = TagLabel(light_text, light_tone)
        self.status_label = QLabel(status)
        self.status_label.setObjectName("ReminderRowStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        right_box = QVBoxLayout()
        right_box.setContentsMargins(0, 0, 0, 0)
        right_box.setSpacing(6)
        right_box.addWidget(self.light_label, 0, Qt.AlignmentFlag.AlignRight)
        right_box.addWidget(self.status_label)

        layout.addLayout(text_box, 1)
        layout.addLayout(right_box)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        refresh_style(self)


class RemindersPage(QWidget):
    save_requested = Signal(object)
    delete_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._reminders = []
        self._accounts = []
        self._current_reminder_id = ""
        self._active_filter = "全部"
        self._row_widgets: dict[str, ReminderListRow] = {}
        self._notes_tab_text = "这里会展示当前提醒的完整备注与来源。"

        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(500)
        self.filter_buttons: dict[str, QPushButton] = {}
        self.tabs = QTabWidget()
        self.tabs.setProperty("sectionRole", "workspace-tabs")
        self.center_tab = QWidget()
        self.lights_tab = QWidget()
        self.subscriptions_tab = QWidget()
        self.notes_tab = QWidget()
        self.new_button = make_secondary_button("新建提醒")
        self.total_card = MetricCard("全部提醒")
        self.red_card = MetricCard("红灯")
        self.amber_card = MetricCard("黄灯")
        self.green_card = MetricCard("绿灯")
        self.detail_title_label = QLabel("提醒详情")
        self.detail_title_label.setObjectName("SectionTitle")
        self.detail_status_label = TagLabel("新建", "gray")
        self.detail_meta_label = QLabel("选择左侧提醒后编辑。黄色从 80% 开始，红色表示已超出或已到期。")
        self.detail_meta_label.setObjectName("MutedText")
        self.detail_meta_label.setWordWrap(True)
        self.list_meta_label = QLabel("0 条提醒 · 当前筛选：全部")
        self.list_meta_label.setObjectName("MutedText")
        self.list_hint_label = QLabel("左侧按标题、类型、进度、来源和备注分行扫读。")
        self.list_hint_label.setObjectName("MutedText")
        self.list_hint_label.setWordWrap(True)
        self.list_header_title_label = QLabel("清单表头")
        self.list_header_title_label.setObjectName("SectionTitle")
        self.list_header_title_label.setProperty("sectionDensity", "compact")
        self.list_header_hint_label = QLabel("标题 / 类型 / 进度 / 来源备注")
        self.list_header_hint_label.setObjectName("MutedText")
        self.list_header_hint_label.setWordWrap(True)
        self.reading_title_label = QLabel("备注与来源")
        self.reading_title_label.setObjectName("SectionTitle")
        self.reading_meta_label = QLabel("保留原有备注编辑与来源填写逻辑，同时把线索阅读区单独放出来。")
        self.reading_meta_label.setObjectName("MutedText")
        self.reading_meta_label.setWordWrap(True)
        self.reading_signal_label = QLabel("灯号提示：未选择提醒")
        self.reading_signal_label.setObjectName("MutedText")
        self.reading_signal_label.setWordWrap(True)
        self.reading_source_label = QLabel("来源阅读：手动录入")
        self.reading_source_label.setObjectName("MutedText")
        self.reading_source_label.setWordWrap(True)
        self.reading_excerpt_label = QLabel("备注摘要：等待选择提醒")
        self.reading_excerpt_label.setObjectName("MutedText")
        self.reading_excerpt_label.setWordWrap(True)
        self.detail_source_label = QLabel("来源摘要：手动录入")
        self.detail_source_label.setObjectName("MutedText")
        self.detail_source_label.setWordWrap(True)
        self.detail_excerpt_label = QLabel("备注摘要：等待选择提醒")
        self.detail_excerpt_label.setObjectName("MutedText")
        self.detail_excerpt_label.setWordWrap(True)
        self.detail_context_label = QLabel("内容提示：选择提醒后可快速定位来源和备注。")
        self.detail_context_label.setObjectName("MutedText")
        self.detail_context_label.setWordWrap(True)
        self.reading_summary_title_label = QLabel("编辑摘要")
        self.reading_summary_title_label.setObjectName("SectionTitle")
        self.reading_summary_title_label.setProperty("sectionDensity", "compact")
        self.reading_summary_hint_label = QLabel("把当前提醒的关键信息先收拢，再进入下方编辑。")
        self.reading_summary_hint_label.setObjectName("MutedText")
        self.reading_summary_hint_label.setWordWrap(True)
        self.lights_table = QTableWidget()
        self.subscriptions_table = QTableWidget()
        self.notes_view = QTextEdit()
        self.notes_view.setReadOnly(True)
        self.notes_view.setMinimumHeight(320)
        self.notes_tab_title_label = QLabel("当前提醒阅读页")
        self.notes_tab_title_label.setObjectName("SectionTitle")
        self.notes_tab_title_label.setProperty("sectionDensity", "compact")
        self.notes_tab_meta_label = QLabel("这里把备注、来源、灯号和处理口径放在同一页阅读。")
        self.notes_tab_meta_label.setObjectName("MutedText")
        self.notes_tab_meta_label.setWordWrap(True)
        self.notes_tab_status_label = QLabel("状态摘要：未选择提醒")
        self.notes_tab_status_label.setObjectName("MutedText")
        self.notes_tab_status_label.setWordWrap(True)
        self.notes_tab_source_label = QLabel("来源摘要：手动录入")
        self.notes_tab_source_label.setObjectName("MutedText")
        self.notes_tab_source_label.setWordWrap(True)
        self.notes_tab_excerpt_label = QLabel("备注摘要：等待选择提醒")
        self.notes_tab_excerpt_label.setObjectName("MutedText")
        self.notes_tab_excerpt_label.setWordWrap(True)
        self.title_edit = QLineEdit()
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["日期提醒", "阈值提醒"])
        self.target_type_combo = QComboBox()
        self.target_type_combo.addItems(["充值", "会员续费", "固定支出", "储蓄计划", "账户余额", "预算进度"])
        self.account_combo = QComboBox()
        self.due_date_edit = QDateEdit(QDate.currentDate())
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.setCalendarPopup(True)
        self.threshold_amount_edit = QLineEdit()
        self.current_value_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["启用", "停用"])
        self.source_edit = QLineEdit("手动录入")
        self.notes_hint_label = QLabel("记录补充说明、回查线索和处理口径，具体数据仍以本地账本为准。")
        self.notes_hint_label.setObjectName("MutedText")
        self.notes_hint_label.setWordWrap(True)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMinimumHeight(192)
        self.save_button = QPushButton("保存提醒")
        self.delete_button = make_danger_button("删除提醒")
        prepare_table(self.lights_table, ["灯号", "提醒项", "类型", "进度/日期", "状态"])
        prepare_table(self.subscriptions_table, ["预计开支/订阅", "提醒类型", "目标", "到期/进度", "状态"])
        self._limit_editor_widths()

        self._build_ui()
        self._connect_signals()

    def _limit_editor_widths(self) -> None:
        self.title_edit.setMaximumWidth(520)
        for widget in (
            self.kind_combo,
            self.target_type_combo,
            self.account_combo,
            self.due_date_edit,
            self.threshold_amount_edit,
            self.current_value_edit,
            self.status_combo,
            self.source_edit,
        ):
            widget.setMaximumWidth(380)

    def _build_ui(self) -> None:
        summary_layout = QGridLayout()
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setHorizontalSpacing(12)
        summary_layout.setVerticalSpacing(12)
        for column, card in enumerate([self.total_card, self.red_card, self.amber_card, self.green_card]):
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            summary_layout.addWidget(card, 0, column)

        list_card, list_layout = create_card("提醒清单", "按预计开支名和订阅名查看，红黄绿灯只做本地提示")
        list_card.setProperty("sectionRole", "reminder-list")
        list_card.setProperty("sectionDensity", "compact")
        refresh_style(list_card)
        list_card.setMinimumWidth(480)
        list_header_frame = QFrame()
        list_header_frame.setObjectName("ReadonlyBox")
        list_header_frame.setProperty("sectionRole", "reminder-list-header")
        list_header_frame.setProperty("sectionDensity", "compact")
        list_header_layout = QVBoxLayout(list_header_frame)
        list_header_layout.setContentsMargins(12, 10, 12, 10)
        list_header_layout.setSpacing(6)
        list_header_top = QHBoxLayout()
        list_header_top.setContentsMargins(0, 0, 0, 0)
        list_header_top.setSpacing(12)
        list_header_top.addWidget(self.list_header_title_label)
        list_header_top.addStretch(1)
        list_header_top.addWidget(self.list_meta_label)
        list_header_top.addWidget(self.new_button)
        list_header_layout.addLayout(list_header_top)
        list_header_layout.addWidget(self.list_header_hint_label)
        list_header_layout.addWidget(self.list_hint_label)
        list_layout.addWidget(list_header_frame)
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        for name in ["全部", "红灯", "黄灯", "绿灯", "启用"]:
            button = make_secondary_button(name)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=name: self._set_filter(value))
            self.filter_buttons[name] = button
            filter_row.addWidget(button)
        filter_row.addStretch(1)
        list_layout.addLayout(filter_row)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setSpacing(10)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setProperty("sectionRole", "reminder-list")
        self.list_widget.setProperty("sectionDensity", "compact")
        list_layout.addWidget(self.list_widget, 1)

        detail_card, detail_layout = create_card("", "")
        detail_card.setProperty("sectionVariant", "")
        detail_card.setProperty("sectionRole", "reminder-detail")
        detail_card.setProperty("sectionDensity", "compact")
        refresh_style(detail_card)
        detail_card.setMinimumWidth(720)
        detail_layout.setSpacing(8)

        detail_editor_frame = QFrame()
        detail_editor_frame.setObjectName("SectionCard")
        detail_editor_frame.setProperty("sectionDensity", "compact")
        detail_editor_frame.setProperty("sectionRole", "reminder-detail-editor")
        detail_editor_frame.setFrameShape(QFrame.Shape.StyledPanel)
        detail_editor_layout = QVBoxLayout(detail_editor_frame)
        detail_editor_layout.setContentsMargins(14, 14, 14, 14)
        detail_editor_layout.setSpacing(10)

        detail_header = QHBoxLayout()
        detail_header.setContentsMargins(0, 0, 0, 0)
        detail_header.setSpacing(16)
        detail_text_box = QVBoxLayout()
        detail_text_box.setContentsMargins(0, 0, 0, 0)
        detail_text_box.setSpacing(4)
        detail_text_box.addWidget(self.detail_title_label)
        detail_text_box.addWidget(self.detail_meta_label)
        detail_header.addLayout(detail_text_box, 1)

        detail_action_box = QVBoxLayout()
        detail_action_box.setContentsMargins(0, 0, 0, 0)
        detail_action_box.setSpacing(8)
        detail_action_box.addWidget(self.detail_status_label, 0, Qt.AlignmentFlag.AlignRight)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.delete_button)
        detail_action_box.addLayout(button_row)
        detail_header.addLayout(detail_action_box)
        detail_editor_layout.addLayout(detail_header)

        detail_summary_frame = QFrame()
        detail_summary_frame.setObjectName("ReadonlyBox")
        detail_summary_frame.setProperty("sectionRole", "reminder-detail-summary")
        detail_summary_frame.setProperty("sectionDensity", "compact")
        detail_summary_layout = QVBoxLayout(detail_summary_frame)
        detail_summary_layout.setContentsMargins(12, 10, 12, 10)
        detail_summary_layout.setSpacing(6)
        detail_summary_title = QLabel("内容摘要")
        detail_summary_title.setObjectName("SectionTitle")
        detail_summary_title.setProperty("sectionDensity", "compact")
        detail_summary_layout.addWidget(detail_summary_title)
        detail_summary_grid = QGridLayout()
        detail_summary_grid.setContentsMargins(0, 0, 0, 0)
        detail_summary_grid.setHorizontalSpacing(12)
        detail_summary_grid.setVerticalSpacing(4)
        detail_summary_grid.addWidget(self.detail_source_label, 0, 0)
        detail_summary_grid.addWidget(self.detail_excerpt_label, 0, 1)
        detail_summary_grid.addWidget(self.detail_context_label, 0, 2)
        detail_summary_grid.setColumnStretch(0, 1)
        detail_summary_grid.setColumnStretch(1, 1)
        detail_summary_grid.setColumnStretch(2, 1)
        detail_summary_layout.addLayout(detail_summary_grid)
        detail_editor_layout.addWidget(detail_summary_frame)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(18)
        form_grid.setVerticalSpacing(8)
        left_form = QFormLayout()
        left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        left_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        left_form.setHorizontalSpacing(12)
        left_form.setVerticalSpacing(8)
        left_form.addRow("提醒标题", self.title_edit)
        left_form.addRow("提醒类型", self.kind_combo)
        left_form.addRow("目标类型", self.target_type_combo)
        left_form.addRow("关联账户", self.account_combo)
        left_form.addRow("状态", self.status_combo)

        right_form = QFormLayout()
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        right_form.setHorizontalSpacing(12)
        right_form.setVerticalSpacing(8)
        right_form.addRow("到期日期", self.due_date_edit)
        right_form.addRow("阈值金额", self.threshold_amount_edit)
        right_form.addRow("当前值", self.current_value_edit)
        form_grid.addLayout(left_form, 0, 0)
        form_grid.addLayout(right_form, 0, 1)
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)
        detail_editor_layout.addLayout(form_grid)

        detail_layout.addWidget(detail_editor_frame)

        reading_frame = QFrame()
        reading_frame.setObjectName("SectionCard")
        reading_frame.setProperty("sectionDensity", "compact")
        reading_frame.setProperty("sectionRole", "reminder-detail-reading")
        reading_frame.setFrameShape(QFrame.Shape.StyledPanel)
        reading_layout = QVBoxLayout(reading_frame)
        reading_layout.setContentsMargins(14, 14, 14, 14)
        reading_layout.setSpacing(6)

        reading_layout.addWidget(self.reading_title_label)
        reading_layout.addWidget(self.reading_meta_label)
        reading_layout.addWidget(self.reading_summary_title_label)
        reading_layout.addWidget(self.reading_summary_hint_label)

        reading_summary_row = QHBoxLayout()
        reading_summary_row.setContentsMargins(0, 0, 0, 0)
        reading_summary_row.setSpacing(12)
        reading_summary_row.addWidget(self.reading_signal_label, 1)
        reading_summary_row.addWidget(self.reading_source_label, 1)
        reading_layout.addLayout(reading_summary_row)
        reading_layout.addWidget(self.reading_excerpt_label)

        source_form = QFormLayout()
        source_form.setContentsMargins(0, 0, 0, 0)
        source_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        source_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        source_form.setHorizontalSpacing(12)
        source_form.setVerticalSpacing(8)
        source_form.addRow("来源", self.source_edit)
        reading_layout.addLayout(source_form)
        reading_layout.addWidget(self.notes_hint_label)
        reading_layout.addWidget(self.notes_edit)

        detail_layout.addWidget(reading_frame)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(list_card)
        splitter.addWidget(detail_card)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([520, 960])

        center_layout = QVBoxLayout(self.center_tab)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        center_layout.addLayout(summary_layout)
        center_layout.addWidget(splitter)

        lights_layout = QVBoxLayout(self.lights_tab)
        lights_layout.setContentsMargins(0, 0, 0, 0)
        lights_layout.setSpacing(12)
        lights_card, lights_card_layout = create_card("红黄绿视图", "把全部提醒按灯号和处理状态集中查看")
        lights_card_layout.addWidget(self.lights_table)
        lights_layout.addWidget(lights_card)

        subscriptions_layout = QVBoxLayout(self.subscriptions_tab)
        subscriptions_layout.setContentsMargins(0, 0, 0, 0)
        subscriptions_layout.setSpacing(12)
        subscriptions_card, subscriptions_card_layout = create_card("订阅服务", "会员续费、日期提醒和需要定期回查的项目")
        subscriptions_card_layout.addWidget(self.subscriptions_table)
        subscriptions_layout.addWidget(subscriptions_card)

        notes_layout = QVBoxLayout(self.notes_tab)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(12)
        notes_card, notes_card_layout = create_card("备注与来源全文", "长备注独立阅读，不再挤在表单中间")
        notes_card.setProperty("sectionRole", "reminder-notes")
        notes_card.setProperty("sectionDensity", "compact")
        notes_overview_frame = QFrame()
        notes_overview_frame.setObjectName("ReadonlyBox")
        notes_overview_frame.setProperty("sectionRole", "reminder-notes-summary")
        notes_overview_frame.setProperty("sectionDensity", "compact")
        notes_overview_layout = QVBoxLayout(notes_overview_frame)
        notes_overview_layout.setContentsMargins(12, 10, 12, 10)
        notes_overview_layout.setSpacing(6)
        notes_overview_layout.addWidget(self.notes_tab_title_label)
        notes_overview_layout.addWidget(self.notes_tab_meta_label)
        notes_overview_row = QHBoxLayout()
        notes_overview_row.setContentsMargins(0, 0, 0, 0)
        notes_overview_row.setSpacing(12)
        notes_overview_row.addWidget(self.notes_tab_status_label, 1)
        notes_overview_row.addWidget(self.notes_tab_source_label, 1)
        notes_overview_row.addWidget(self.notes_tab_excerpt_label, 1)
        notes_overview_layout.addLayout(notes_overview_row)
        notes_card_layout.addWidget(notes_overview_frame)
        notes_text_frame = QFrame()
        notes_text_frame.setObjectName("ReadonlyBox")
        notes_text_frame.setProperty("sectionRole", "reminder-notes-body")
        notes_text_frame.setProperty("sectionDensity", "compact")
        notes_text_layout = QVBoxLayout(notes_text_frame)
        notes_text_layout.setContentsMargins(12, 10, 12, 10)
        notes_text_layout.setSpacing(6)
        notes_text_title = QLabel("完整备注")
        notes_text_title.setObjectName("SectionTitle")
        notes_text_title.setProperty("sectionDensity", "compact")
        notes_text_layout.addWidget(notes_text_title)
        self.notes_view.setProperty("sectionRole", "reminder-notes-text")
        self.notes_view.setProperty("sectionDensity", "compact")
        notes_text_layout.addWidget(self.notes_view)
        notes_card_layout.addWidget(notes_text_frame)
        notes_layout.addWidget(notes_card)

        self.tabs.addTab(self.center_tab, "提醒中心")
        self.tabs.addTab(self.lights_tab, "红黄绿视图")
        self.tabs.addTab(self.subscriptions_tab, "订阅服务")
        self.tabs.addTab(self.notes_tab, "备注与来源")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

    def _connect_signals(self) -> None:
        self.new_button.clicked.connect(self.clear_editor)
        self.save_button.clicked.connect(self._emit_save)
        self.delete_button.clicked.connect(self._emit_delete)
        self.list_widget.itemSelectionChanged.connect(self._handle_selection_changed)
        self.title_edit.textChanged.connect(self._sync_notes_view)
        self.kind_combo.currentTextChanged.connect(self._sync_notes_view)
        self.target_type_combo.currentTextChanged.connect(self._sync_notes_view)
        self.status_combo.currentTextChanged.connect(self._sync_notes_view)
        self.due_date_edit.dateChanged.connect(lambda _date: self._sync_notes_view())
        self.threshold_amount_edit.textChanged.connect(self._sync_notes_view)
        self.current_value_edit.textChanged.connect(self._sync_notes_view)
        self.source_edit.textChanged.connect(self._sync_source_reading)
        self.notes_edit.textChanged.connect(self._sync_notes_view)

    def load_accounts(self, accounts: list) -> None:
        self._accounts = list(accounts)
        self.account_combo.clear()
        self.account_combo.addItem("")
        for account in self._accounts:
            self.account_combo.addItem(account.name)

    def load_reminders(self, reminders: list) -> None:
        self._reminders = list(reminders)
        self._refresh_summary()
        self._refresh_filter_buttons()
        self.list_widget.clear()
        self._row_widgets.clear()
        filtered = [reminder for reminder in self._reminders if self._matches_filter(reminder)]
        self.list_meta_label.setText(f"{len(filtered)} 条提醒 · 当前筛选：{self._active_filter}")
        for reminder in filtered:
            light_text, light_tone, _ = self._traffic_light(reminder)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, reminder.id)
            item.setToolTip(self._tooltip_text(reminder))
            item.setSizeHint(QSize(460, 132))
            self.list_widget.addItem(item)
            row_widget = ReminderListRow(
                self._display_name(reminder),
                f"{reminder.status} · {reminder.reminder_kind} · {reminder.target_type}",
                self._list_focus_text(reminder),
                self._source_summary(reminder.source),
                self._note_excerpt(reminder.notes),
                light_text,
                light_tone,
                self._progress_or_date_text(reminder),
            )
            self._row_widgets[reminder.id] = row_widget
            self.list_widget.setItemWidget(item, row_widget)
        if filtered and not self._current_reminder_id:
            self.list_widget.setCurrentRow(0)
        self._load_lights_table(self._reminders)
        self._load_subscriptions_table(self._reminders)
        self._sync_notes_view()

    def clear_editor(self) -> None:
        self._current_reminder_id = ""
        self.list_widget.clearSelection()
        for row_widget in self._row_widgets.values():
            row_widget.set_selected(False)
        self.detail_title_label.setText("新建提醒")
        self.detail_status_label.setText("新建")
        self.detail_status_label.set_tone("gray")
        self.detail_meta_label.setText("填写预计开支、订阅或回查事项。黄色从 80% 开始，红色表示已超出或已到期。")
        self.reading_signal_label.setText("灯号提示：未选择提醒")
        self.reading_source_label.setText("来源阅读：手动录入")
        self.reading_excerpt_label.setText("备注摘要：等待选择提醒")
        self.detail_source_label.setText("来源摘要：手动录入")
        self.detail_excerpt_label.setText("备注摘要：等待选择提醒")
        self.detail_context_label.setText("内容提示：选择提醒后可快速定位来源和备注。")
        self.notes_tab_status_label.setText("状态摘要：未选择提醒")
        self.notes_tab_source_label.setText("来源摘要：手动录入")
        self.notes_tab_excerpt_label.setText("备注摘要：等待选择提醒")
        self.title_edit.clear()
        self.kind_combo.setCurrentText("日期提醒")
        self.target_type_combo.setCurrentText("充值")
        self.account_combo.setCurrentIndex(0)
        self.due_date_edit.setDate(QDate.currentDate())
        self.threshold_amount_edit.clear()
        self.current_value_edit.clear()
        self.status_combo.setCurrentText("启用")
        self.source_edit.setText("手动录入")
        self.notes_edit.clear()
        self._notes_tab_text = "这里会展示当前提醒的完整备注与来源。"
        self._sync_notes_view()

    def _handle_selection_changed(self) -> None:
        for reminder_id, row_widget in self._row_widgets.items():
            row_widget.set_selected(reminder_id == self._current_reminder_id)
        item = self.list_widget.currentItem()
        if item is None:
            return
        reminder_id = item.data(Qt.ItemDataRole.UserRole)
        reminder = next((value for value in self._reminders if value.id == reminder_id), None)
        if reminder is None:
            return
        self._current_reminder_id = reminder.id
        for row_id, row_widget in self._row_widgets.items():
            row_widget.set_selected(row_id == reminder.id)
        self.title_edit.setText(reminder.title)
        self.kind_combo.setCurrentText(reminder.reminder_kind)
        self.target_type_combo.setCurrentText(reminder.target_type)
        self.account_combo.setCurrentText(self._account_name(reminder.account_id))
        if reminder.due_date:
            due_date = QDate.fromString(reminder.due_date, "yyyy-MM-dd")
            if due_date.isValid():
                self.due_date_edit.setDate(due_date)
        self.threshold_amount_edit.setText(reminder.threshold_amount)
        self.current_value_edit.setText(reminder.current_value)
        self.status_combo.setCurrentText(reminder.status)
        self.source_edit.setText(reminder.source)
        self.notes_edit.setPlainText(reminder.notes)
        light_text, light_tone, light_note = self._traffic_light(reminder)
        self.detail_title_label.setText(self._display_name(reminder))
        self.detail_status_label.setText(light_text)
        self.detail_status_label.set_tone(light_tone)
        self.detail_meta_label.setText(f"{reminder.reminder_kind} · {reminder.target_type} · {light_note}")
        self.reading_signal_label.setText(f"灯号提示：{light_note}")
        self.reading_source_label.setText(self._reading_source_text(reminder.source))
        self.reading_excerpt_label.setText(f"备注摘要：{self._note_excerpt(reminder.notes)}")
        self.detail_source_label.setText(self._source_summary(reminder.source))
        self.detail_excerpt_label.setText(f"备注摘要：{self._note_excerpt(reminder.notes)}")
        self.detail_context_label.setText(
            f"内容提示：{reminder.status} · {reminder.reminder_kind} · {reminder.target_type}"
        )
        self.notes_tab_status_label.setText(f"状态摘要：{reminder.status} · {light_note}")
        self.notes_tab_source_label.setText(self._source_summary(reminder.source))
        self.notes_tab_excerpt_label.setText(f"备注摘要：{self._note_excerpt(reminder.notes)}")
        self._sync_source_reading(reminder.source)
        self._notes_tab_text = self._compose_notes_page_text(reminder, light_note)
        self._sync_notes_view()

    def _account_name(self, account_id: str) -> str:
        account = next((item for item in self._accounts if item.id == account_id), None)
        return account.name if account else ""

    def _account_id(self, account_name: str) -> str:
        account = next((item for item in self._accounts if item.name == account_name), None)
        return account.id if account else ""

    def _emit_save(self) -> None:
        self.save_requested.emit(
            {
                "reminder_id": self._current_reminder_id,
                "title": self.title_edit.text().strip(),
                "reminder_kind": self.kind_combo.currentText().strip(),
                "target_type": self.target_type_combo.currentText().strip(),
                "account_id": self._account_id(self.account_combo.currentText().strip()),
                "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
                "threshold_amount": self.threshold_amount_edit.text().strip(),
                "current_value": self.current_value_edit.text().strip(),
                "status": self.status_combo.currentText().strip(),
                "source": self.source_edit.text().strip(),
                "notes": self.notes_edit.toPlainText().strip(),
            }
        )

    def _emit_delete(self) -> None:
        if self._current_reminder_id:
            self.delete_requested.emit(self._current_reminder_id)

    def _refresh_summary(self) -> None:
        total = len(self._reminders)
        enabled_count = sum(1 for reminder in self._reminders if reminder.status == "启用")
        paused_count = total - enabled_count
        red_count = 0
        amber_count = 0
        green_count = 0
        for reminder in self._reminders:
            _, tone, _ = self._traffic_light(reminder)
            if tone == "red":
                red_count += 1
            elif tone == "amber":
                amber_count += 1
            elif tone == "green":
                green_count += 1

        self.total_card.set_content(
            f"{total} 项",
            f"启用 {enabled_count} 项，停用 {paused_count} 项",
            "本地",
            "gray",
        )
        self.red_card.set_content(f"{red_count} 项", "已超支、低于阈值或已到期", "急", "red")
        self.amber_card.set_content(f"{amber_count} 项", "进度达到 80% 或 7 天内", "80%", "amber")
        self.green_card.set_content(f"{green_count} 项", "仍在正常观察区间", "稳", "green")

    def _set_filter(self, value: str) -> None:
        self._active_filter = value
        self._refresh_filter_buttons()
        self.load_reminders(self._reminders)

    def _refresh_filter_buttons(self) -> None:
        for name, button in self.filter_buttons.items():
            button.setChecked(name == self._active_filter)

    def _matches_filter(self, reminder: object) -> bool:
        if self._active_filter == "全部":
            return True
        if self._active_filter == "启用":
            return getattr(reminder, "status", "") == "启用"
        light_text, _, _ = self._traffic_light(reminder)
        return light_text == self._active_filter

    def _display_name(self, reminder: object) -> str:
        notes_name = self._note_value(getattr(reminder, "notes", ""), "预算项")
        if notes_name:
            return notes_name

        title = str(getattr(reminder, "title", "")).strip()
        title = re.sub(r"^\d{4}-\d{2}\s+", "", title)
        for suffix in ("预算超支提醒", "预算临界提醒", "预算提醒"):
            title = title.replace(suffix, "")
        title = re.sub(r"\s+", " ", title).strip(" ·-")
        return title or "未命名提醒"

    def _traffic_light(self, reminder: object) -> tuple[str, str, str]:
        if getattr(reminder, "reminder_kind", "") == "阈值提醒":
            threshold = self._decimal(getattr(reminder, "threshold_amount", ""))
            current = self._decimal(getattr(reminder, "current_value", ""))
            if threshold <= 0:
                return ("待确认", "gray", "阈值金额待确认")
            ratio = current / threshold
            percent = ratio * Decimal("100")
            if ratio >= Decimal("1"):
                return ("红灯", "red", f"当前 {self._money(current)}，已达 {percent:.1f}%")
            if ratio >= Decimal("0.8"):
                return ("黄灯", "amber", f"当前 {self._money(current)}，已达 {percent:.1f}%")
            return ("绿灯", "green", f"当前 {self._money(current)}，已达 {percent:.1f}%")

        due_date = self._date(getattr(reminder, "due_date", ""))
        if due_date is None:
            return ("待确认", "gray", "到期日期待确认")
        days_left = (due_date - date.today()).days
        if days_left <= 0:
            return ("红灯", "red", f"{due_date.isoformat()} 已到期或今天到期")
        if days_left <= 7:
            return ("黄灯", "amber", f"{due_date.isoformat()}，{days_left} 天后")
        return ("绿灯", "green", f"{due_date.isoformat()}，{days_left} 天后")

    def _progress_or_date_text(self, reminder: object) -> str:
        if getattr(reminder, "reminder_kind", "") == "阈值提醒":
            threshold = self._decimal(getattr(reminder, "threshold_amount", ""))
            current = self._decimal(getattr(reminder, "current_value", ""))
            if threshold <= 0:
                return "阈值待确认"
            percent = current / threshold * Decimal("100")
            return f"{percent:.1f}%"
        due_date = str(getattr(reminder, "due_date", "")).strip()
        return due_date or "日期待确认"

    def _list_focus_text(self, reminder: object) -> str:
        if getattr(reminder, "reminder_kind", "") == "阈值提醒":
            threshold = self._decimal(getattr(reminder, "threshold_amount", ""))
            current = self._decimal(getattr(reminder, "current_value", ""))
            if threshold <= 0:
                return "阈值金额待确认"
            percent = current / threshold * Decimal("100")
            return f"当前 {self._money(current)} / 阈值 {self._money(threshold)} · {percent:.1f}%"

        due_date = self._date(getattr(reminder, "due_date", ""))
        if due_date is None:
            return "到期日期待确认"
        days_left = (due_date - date.today()).days
        if days_left <= 0:
            return f"到期 {due_date.isoformat()} · 已到期或今天到期"
        return f"到期 {due_date.isoformat()} · 还有 {days_left} 天"

    def _sync_source_reading(self, value: str) -> None:
        source_text = self._reading_source_text(value)
        self.reading_source_label.setText(source_text)
        self.detail_source_label.setText(self._source_summary(value))
        self.notes_tab_source_label.setText(self._source_summary(value))
        self._sync_notes_view()

    def _sync_notes_view(self) -> None:
        source_text = self._reading_source_text(self.source_edit.text())
        notes_text = self.notes_edit.toPlainText().strip()
        notes_excerpt = self._note_excerpt(notes_text)
        title_text = self.title_edit.text().strip() or self.detail_title_label.text().strip() or "未命名提醒"
        kind_text = self.kind_combo.currentText().strip() or "未选择"
        target_text = self.target_type_combo.currentText().strip() or "未选择"
        status_text = self.status_combo.currentText().strip() or "待确认"
        due_text = self.due_date_edit.date().toString("yyyy-MM-dd")
        threshold_text = self.threshold_amount_edit.text().strip() or "未填写"
        current_text = self.current_value_edit.text().strip() or "未填写"
        self.notes_tab_title_label.setText(title_text)
        self.notes_tab_meta_label.setText(f"{kind_text} · {target_text} · 到期 {due_text}")
        self.notes_tab_status_label.setText(f"状态摘要：{status_text} · {kind_text} · {target_text}")
        self.notes_tab_source_label.setText(self._source_summary(self.source_edit.text()))
        self.reading_excerpt_label.setText(f"备注摘要：{notes_excerpt}")
        self.detail_excerpt_label.setText(f"备注摘要：{notes_excerpt}")
        self.notes_tab_excerpt_label.setText(f"备注摘要：{notes_excerpt}")
        self.detail_context_label.setText(f"内容提示：{status_text} · {kind_text} · {target_text}")
        parts = [
            "提醒概览",
            f"提醒标题：{title_text}",
            f"提醒类型：{kind_text}",
            f"目标类型：{target_text}",
            f"状态摘要：{status_text}",
            f"到期日期：{due_text}",
            f"阈值金额：{threshold_text}",
            f"当前值：{current_text}",
            source_text.replace("来源阅读：", "来源："),
            "",
            "备注正文",
            notes_text or "暂无备注",
        ]
        self.notes_view.setPlainText("\n".join(parts))

    def _load_lights_table(self, reminders: list) -> None:
        rows = []
        for reminder in reminders:
            light_text, _tone, note = self._traffic_light(reminder)
            rows.append(
                [
                    light_text,
                    self._display_name(reminder),
                    reminder.target_type,
                    self._progress_or_date_text(reminder),
                    reminder.status or note,
                ]
            )
        self.lights_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                self.lights_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.lights_table)

    def _load_subscriptions_table(self, reminders: list) -> None:
        rows = []
        for reminder in reminders:
            if reminder.reminder_kind == "日期提醒" or reminder.target_type in {"会员续费", "充值", "固定支出"}:
                rows.append(
                    [
                        self._display_name(reminder),
                        reminder.reminder_kind,
                        reminder.target_type,
                        self._progress_or_date_text(reminder),
                        reminder.status,
                    ]
                )
        self.subscriptions_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                self.subscriptions_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.subscriptions_table)

    def _tooltip_text(self, reminder: object) -> str:
        parts = [
            str(getattr(reminder, "title", "")).strip(),
            str(getattr(reminder, "notes", "")).strip(),
        ]
        return "\n".join(part for part in parts if part)

    def _reading_source_text(self, value: str) -> str:
        source_text = str(value or "").strip() or "手动录入"
        return f"来源阅读：{source_text}"

    def _source_summary(self, value: str) -> str:
        source_text = str(value or "").strip() or "手动录入"
        return f"来源摘要：{source_text}"

    def _source_value(self, value: str) -> str:
        return str(value or "").strip() or "手动录入"

    def _note_excerpt(self, notes: str) -> str:
        for line in str(notes or "").splitlines():
            text = line.strip()
            if not text:
                continue
            if text.startswith("来源："):
                continue
            return text
        return "等待填写备注"

    def _compose_notes_page_text(self, reminder: object, light_note: str) -> str:
        notes_text = str(getattr(reminder, "notes", "")).strip()
        source_text = self._source_value(getattr(reminder, "source", ""))
        parts = [
            "提醒概览",
            f"提醒标题：{getattr(reminder, 'title', '')}",
            f"提醒类型：{getattr(reminder, 'reminder_kind', '')}",
            f"目标类型：{getattr(reminder, 'target_type', '')}",
            f"状态摘要：{getattr(reminder, 'status', '')} · {light_note}",
            f"来源：{source_text}",
        ]
        if notes_text:
            parts.extend(["", "备注正文", notes_text])
        else:
            parts.extend(["", "备注正文", "暂无备注"])
        return "\n".join(parts)

    def _note_value(self, notes: str, key: str) -> str:
        prefix = f"{key}："
        for line in notes.splitlines():
            text = line.strip()
            if text.startswith(prefix):
                return text.removeprefix(prefix).strip()
        return ""

    def _decimal(self, value: object) -> Decimal:
        text = str(value or "").replace("¥", "").replace(",", "").strip()
        if not text:
            return Decimal("0")
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _date(self, value: object) -> date | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None

    def _money(self, value: Decimal) -> str:
        return f"¥{value:,.2f}"
