from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from private_ledger.domain.ledger import format_money, parse_decimal
from private_ledger.ui.widgets import (
    MetricCard,
    TagLabel,
    create_card,
    make_danger_button,
    make_secondary_button,
    prepare_table,
    refresh_style,
    sync_table_columns,
)

ANNUAL_QUARTER_PALETTES = (
    {
        "quarter": "#e5efff",
        "month_rows": ("#eef4ff", "#eaf2ff", "#e6efff"),
        "sheet_headers": ("#e3eeff", "#deebff", "#d9e8ff"),
        "sheet_cells": ("#f3f7ff", "#eef4ff", "#e9f1ff"),
        "detail_headers": ("#e3eeff", "#deebff", "#d9e8ff"),
        "detail_cells": ("#f1f6ff", "#edf3ff", "#e8f0ff"),
        "detail_boundary": "#edf4ff",
    },
    {
        "quarter": "#e5f6ff",
        "month_rows": ("#edfaff", "#e8f8ff", "#e2f5ff"),
        "sheet_headers": ("#def4ff", "#d8f1ff", "#d1edff"),
        "sheet_cells": ("#f1fbff", "#ebf8ff", "#e4f6ff"),
        "detail_headers": ("#def4ff", "#d8f1ff", "#d1edff"),
        "detail_cells": ("#eef9ff", "#e7f6ff", "#dff3ff"),
        "detail_boundary": "#eaf8ff",
    },
    {
        "quarter": "#f2ebff",
        "month_rows": ("#f7f2ff", "#f3edff", "#eee7ff"),
        "sheet_headers": ("#ede2ff", "#e8dcff", "#e1d3ff"),
        "sheet_cells": ("#faf7ff", "#f6f1ff", "#f0ebff"),
        "detail_headers": ("#ede2ff", "#e8dcff", "#e1d3ff"),
        "detail_cells": ("#f5efff", "#f0e9ff", "#e8e0ff"),
        "detail_boundary": "#f4efff",
    },
    {
        "quarter": "#fff0de",
        "month_rows": ("#fff6eb", "#fff2e2", "#ffedd7"),
        "sheet_headers": ("#ffe8cb", "#ffe1be", "#ffd9af"),
        "sheet_cells": ("#fffaf4", "#fff5ea", "#ffefde"),
        "detail_headers": ("#ffe8cb", "#ffe1be", "#ffd9af"),
        "detail_cells": ("#fff7ef", "#fff1e5", "#ffe8d7"),
        "detail_boundary": "#fff4e8",
    },
)


class BudgetsPage(QWidget):
    budget_save_requested = Signal(object)
    budget_line_save_requested = Signal(object)
    budget_line_delete_requested = Signal(str)
    budget_seed_requested = Signal(str)
    budget_month_changed = Signal(str)
    annual_status_change_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._budget = None
        self._budget_lines = []
        self._comparison = None
        self._annual_matrix = None
        self._current_line_id = ""
        self._current_month_key = QDate.currentDate().toString("yyyy-MM")
        self._expanded_annual_month = QDate.currentDate().month()
        self._annual_detail_quick_view = "全部"
        self._annual_detail_hide_single_month = False
        self._loading = False

        self.month_edit = QDateEdit(QDate.currentDate())
        self.month_edit.setDisplayFormat("yyyy-MM")
        self.month_edit.setCalendarPopup(True)
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("全部标签")
        self.scope_label = QLabel("预算项自动合计；待确认金额单独展示。")
        self.scope_label.setObjectName("MutedText")
        self.scope_label.setWordWrap(True)
        self.budget_notes_edit = QLineEdit()
        self.budget_notes_edit.setPlaceholderText("预算口径说明，例如：本月先保守控制日常支出")
        self.save_budget_button = make_secondary_button("保存预算说明")
        self.seed_from_actual_button = make_secondary_button("从实际生成预算草稿")
        self.new_line_button = QPushButton("新增预算项")

        self.planned_income_card = MetricCard("计划收入")
        self.planned_expense_card = MetricCard("计划支出")
        self.balance_card = MetricCard("计划结余")
        self.pending_card = MetricCard("待确认金额")
        self.annual_planned_income_card = MetricCard("全年计划收入")
        self.annual_actual_income_card = MetricCard("全年实际收入")
        self.annual_planned_expense_card = MetricCard("全年计划支出")
        self.annual_actual_expense_card = MetricCard("全年实际支出")
        self.annual_planned_balance_card = MetricCard("全年计划结余")
        self.annual_actual_balance_card = MetricCard("全年实际结余")
        self.annual_pending_card = MetricCard("全年待确认")

        self.income_table = QTableWidget()
        self.expense_table = QTableWidget()
        self.comparison_table = QTableWidget()
        self.annual_table = QTableWidget()
        self.annual_sheet_table = QTableWidget()
        self.annual_detail_table = QTableWidget()
        self.effective_scope_table = QTableWidget()
        self.annual_detail_kind_filter_combo = QComboBox()
        self.annual_detail_kind_filter_combo.addItem("全部类型")
        self.annual_detail_tag_filter_combo = QComboBox()
        self.annual_detail_tag_filter_combo.addItem("全部标签")
        self.annual_detail_status_filter_combo = QComboBox()
        self.annual_detail_status_filter_combo.addItem("全部状态")
        self.annual_detail_quick_view_buttons: dict[str, QPushButton] = {}
        for label in ("全部", "有实际", "超支", "未设预算"):
            button = make_secondary_button(label)
            button.setCheckable(True)
            button.setStyleSheet(
                """
                QPushButton#SecondaryActionButton {
                    background: #eef4ff;
                    color: #3f67d9;
                    border: 1px solid #cddcff;
                }
                QPushButton#SecondaryActionButton:hover {
                    background: #e3ecff;
                }
                QPushButton#SecondaryActionButton:checked {
                    background: #3f67d9;
                    color: #ffffff;
                    border: 1px solid #3156bf;
                }
                QPushButton#SecondaryActionButton:checked:hover {
                    background: #365ecf;
                }
                """
            )
            self.annual_detail_quick_view_buttons[label] = button
        self.annual_detail_single_month_button = make_secondary_button("收起单月项")
        self.annual_detail_single_month_button.setCheckable(True)
        self.annual_detail_single_month_button.setStyleSheet(
            """
            QPushButton#SecondaryActionButton {
                background: #eef4ff;
                color: #3f67d9;
                border: 1px solid #cddcff;
            }
            QPushButton#SecondaryActionButton:hover {
                background: #e3ecff;
            }
            QPushButton#SecondaryActionButton:checked {
                background: #3f67d9;
                color: #ffffff;
                border: 1px solid #3156bf;
            }
            QPushButton#SecondaryActionButton:checked:hover {
                background: #365ecf;
            }
            """
        )
        self.annual_detail_single_month_button.setToolTip("隐藏全年里只有 1 个月有预期/实际/待确认数值的项目。")
        self.annual_detail_show_all_button = make_secondary_button("显示全部")
        self.annual_month_cards: dict[int, dict[str, object]] = {}
        self.annual_quarter_sections: dict[int, dict[str, object]] = {}
        self._expanded_annual_other_buckets: set[tuple[int, str]] = set()
        comparison_headers = ["预算项", "类型", "标签", "生效月份", "计划", "已确认", "待确认", "差额", "状态"]
        table_headers = ["预算项", "类型", "标签", "备注", "生效月份", "计划", "已确认实际", "待确认", "差额", "进度", "状态"]
        annual_detail_headers = ["预算项", "类型", "标签", "生效月份"]
        for month in range(1, 13):
            annual_detail_headers.extend([f"{month}月预期", f"{month}月实际"])
        annual_detail_headers.extend(["合计预期", "合计实际", "待确认", "差额", "状态"])
        prepare_table(self.comparison_table, comparison_headers)
        prepare_table(self.income_table, table_headers)
        prepare_table(self.expense_table, table_headers)
        prepare_table(
            self.annual_table,
            ["季度 / 月份", "收入预期", "收入实际", "支出预期", "支出实际", "结余预期", "结余实际", "待确认"],
        )
        annual_sheet_headers = ["项目"]
        for month in range(1, 13):
            annual_sheet_headers.extend([f"{month}月预期", f"{month}月实际"])
        prepare_table(self.annual_sheet_table, annual_sheet_headers)
        self.annual_table.setProperty("tableDensity", "dense")
        self.annual_table.setProperty("tableRole", "matrix")
        self.annual_table.setProperty("tableProfile", "annual-summary")
        refresh_style(self.annual_table)
        self.annual_sheet_table.setProperty("tableDensity", "dense")
        self.annual_sheet_table.setProperty("tableRole", "matrix")
        self.annual_sheet_table.setProperty("tableProfile", "annual-month-sheet")
        refresh_style(self.annual_sheet_table)
        prepare_table(self.annual_detail_table, annual_detail_headers)
        self.annual_detail_table.setProperty("tableProfile", "annual-detail")
        prepare_table(self.effective_scope_table, ["生效方式", "适合场景", "显示口径"])
        self.effective_scope_table.setProperty("tableProfile", "scope-guide")
        self.comparison_table.setProperty("tableProfile", "monthly-workbench")
        self.income_table.setProperty("tableProfile", "monthly-income")
        self.expense_table.setProperty("tableProfile", "monthly-expense")
        self.annual_detail_table.horizontalHeaderItem(31).setToolTip(
            "年度差额沿用新口径：收入看实际减预期，支出看预期减实际。"
        )
        self.comparison_table.setMinimumHeight(420)
        self.income_table.setMinimumHeight(170)
        self.expense_table.setMinimumHeight(280)
        self.annual_table.setMinimumHeight(600)
        self.annual_sheet_table.setMinimumHeight(260)
        self.annual_detail_table.setMinimumHeight(320)
        self.effective_scope_table.setMinimumHeight(180)
        self.line_table = self.comparison_table
        self.tabs = QTabWidget()
        self.tabs.setProperty("sectionRole", "workspace-tabs")
        self.monthly_tab = QWidget()
        self.annual_tab = QWidget()
        self.income_tab = QWidget()
        self.expense_tab = QWidget()
        self.effective_tab = QWidget()
        self.annual_sections_tabs = QTabWidget()
        self.annual_sections_tabs.setProperty("sectionRole", "workspace-tabs")
        self.annual_detail_tab = QWidget()
        self.annual_summary_tab = QWidget()
        self.annual_quarter_tab = QWidget()
        self.workbench_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.annual_overview_badge = QLabel("季度 / 月度")
        self.annual_overview_badge.setObjectName("SectionTitle")
        self.annual_overview_summary = QLabel("先看季度合计，再顺着 1-12 月读每个月的预期 / 实际，主表直接承担全年阅读节奏。")
        self.annual_overview_summary.setObjectName("MutedText")
        self.annual_overview_summary.setWordWrap(True)
        self.annual_overview_summary.setToolTip("季度合计在前，月度明细在后；待确认和压力月仍会在主表里单独提示。")
        self.annual_sheet_focus_label = QLabel("季度先收口，月度再回看；主表保留待确认和压力月份，方便像手工全年预算大表那样顺着读。")
        self.annual_sheet_focus_label.setObjectName("MutedText")
        self.annual_sheet_focus_label.setWordWrap(True)
        self.annual_actual_summary_label = QLabel("实际回看")
        self.annual_actual_summary_label.setObjectName("SectionTitle")
        self.effective_scope_hint_label = QLabel("当前编辑器里的生效方式仍以右侧“快速编辑”为准，这里只做口径对照。")
        self.effective_scope_hint_label.setObjectName("MutedText")
        self.effective_scope_hint_label.setWordWrap(True)
        self.effective_scope_summary_label = QLabel("先认生效方式，再回到预算工作台编辑；当前选中的口径会在下面高亮。")
        self.effective_scope_summary_label.setObjectName("MutedText")
        self.effective_scope_summary_label.setWordWrap(True)
        self.effective_scope_rows: list[dict[str, QFrame | QLabel]] = []
        self.annual_quarter_cards: list[dict[str, QLabel | TagLabel]] = []
        self.annual_overview_badge.setProperty("sectionRole", "annual-read-guide")
        self.annual_overview_summary.setProperty("sectionRole", "annual-read-guide")
        self.annual_sheet_focus_label.setProperty("sectionRole", "annual-read-guide")
        self.annual_actual_summary_label.setProperty("sectionRole", "annual-read-guide")

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["标签预算", "固定支出", "储蓄计划", "收入", "支出"])
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：餐饮预算 / 房租 / 项目奖金")
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("优先填要归到的标签")
        self.planned_amount_edit = QLineEdit()
        self.planned_amount_edit.setPlaceholderText("填写本项计划金额")
        self.effective_mode_combo = QComboBox()
        self.effective_mode_combo.addItems(["仅当前月", "从当前月起", "指定月份范围"])
        self.effective_start_edit = QDateEdit(QDate.currentDate())
        self.effective_start_edit.setDisplayFormat("yyyy-MM")
        self.effective_start_edit.setCalendarPopup(True)
        self.effective_end_edit = QDateEdit(QDate.currentDate())
        self.effective_end_edit.setDisplayFormat("yyyy-MM")
        self.effective_end_edit.setCalendarPopup(True)
        self.day_spin = QSpinBox()
        self.day_spin.setRange(0, 31)
        self.day_spin.setSpecialValueText("无")
        self.required_checkbox = QCheckBox("刚性项目")
        self.reminder_days_spin = QSpinBox()
        self.reminder_days_spin.setRange(0, 30)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("补充预算口径、调整原因，或记录这项预算的执行备注。")
        self.notes_edit.setMinimumHeight(132)
        self.notes_edit.setMaximumHeight(168)
        self.save_line_button = QPushButton("保存预算项")
        self.delete_line_button = make_danger_button("删除预算项")
        self.delete_line_button.setEnabled(False)
        self.editor_context_label = QLabel("新预算项")
        self.editor_context_label.setObjectName("SectionTitle")
        self.editor_hint_label = QLabel("按 生效方式 -> 标签 -> 金额 -> 备注 的顺序连续填写；左侧未设预算行会自动带入建议金额。")
        self.editor_hint_label.setObjectName("MutedText")
        self.editor_hint_label.setWordWrap(True)
        self.effective_mode_hint_label = QLabel("当前生效方式：仅当前月，适合活动、一次性购买或当月临时预算。")
        self.effective_mode_hint_label.setObjectName("MutedText")
        self.effective_mode_hint_label.setWordWrap(True)
        self.editor_followup_hint_label = QLabel("计划日、提醒和刚性项目放在最后补充，保存后仍会回到左侧当月主表对比。")
        self.editor_followup_hint_label.setObjectName("MutedText")
        self.editor_followup_hint_label.setWordWrap(True)
        self.month_edit.setMinimumWidth(132)
        self.effective_start_edit.setMinimumWidth(132)
        self.effective_end_edit.setMinimumWidth(132)
        self.kind_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        top_card, top_layout = create_card("预算工作台", "先切月份和筛选，再读指标卡；主表仍保留当月预算对比。")
        top_card.setProperty("sectionRole", "budget-workbench-shell")
        top_card.setProperty("sectionDensity", "comfortable")
        month_strip = QFrame()
        month_strip.setObjectName("SectionCard")
        month_strip.setProperty("sectionRole", "budget-month-switcher")
        month_strip.setProperty("sectionDensity", "compact")
        month_strip_layout = QVBoxLayout(month_strip)
        month_strip_layout.setContentsMargins(14, 12, 14, 12)
        month_strip_layout.setSpacing(10)

        month_row = QHBoxLayout()
        month_row.setContentsMargins(0, 0, 0, 0)
        month_row.setSpacing(10)
        month_row.addWidget(QLabel("预算月份"))
        month_row.addWidget(self.month_edit, 0)
        month_row.addSpacing(8)
        month_row.addWidget(QLabel("标签"))
        month_row.addWidget(self.tag_filter_combo, 0)
        month_row.addStretch(1)
        month_row.addWidget(self.seed_from_actual_button)
        month_row.addWidget(self.new_line_button)
        month_strip_layout.addLayout(month_row)

        month_strip_layout.addWidget(self.scope_label)

        notes_row = QHBoxLayout()
        notes_row.setContentsMargins(0, 0, 0, 0)
        notes_row.setSpacing(10)
        notes_row.addWidget(QLabel("口径说明"))
        notes_row.addWidget(self.budget_notes_edit, 1)
        notes_row.addWidget(self.save_budget_button)
        month_strip_layout.addLayout(notes_row)
        top_layout.addWidget(month_strip)

        metric_grid = QGridLayout()
        metric_grid.setContentsMargins(0, 0, 0, 0)
        metric_grid.setHorizontalSpacing(12)
        metric_grid.setVerticalSpacing(12)
        for index, card in enumerate(
            (
                self.planned_income_card,
                self.planned_expense_card,
                self.balance_card,
                self.pending_card,
            )
        ):
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            metric_grid.addWidget(card, 0, index)
        top_layout.addLayout(metric_grid)

        comparison_card, comparison_layout = create_card("当月预算项对比", "工作台主视图只保留当月对比，收入项和支出项拆到独立页。")
        comparison_card.setProperty("sectionRole", "budget-comparison-panel")
        comparison_layout.addWidget(self.comparison_table)

        income_card, income_layout = create_card("预计收入项", "收入预期与实际，单独看工资、其他收入等来源。")
        income_card.setProperty("sectionRole", "budget-income-panel")
        income_layout.addWidget(self.income_table)

        expense_card, expense_layout = create_card("预计支出项", "支出预期与实际，包含标签预算、固定支出和储蓄计划。")
        expense_card.setProperty("sectionRole", "budget-expense-panel")
        expense_layout.addWidget(self.expense_table)

        editor_card, editor_layout = create_card("快速编辑", "预算项会和同名标签流水做对比。")
        editor_card.setProperty("sectionRole", "budget-fill-desk")
        editor_card.setProperty("sectionDensity", "comfortable")
        editor_layout.addWidget(self.editor_context_label)
        editor_layout.addWidget(self.editor_hint_label)
        editor_fill_title = QLabel("填写台")
        editor_fill_title.setObjectName("SectionTitle")
        editor_fill_title.setProperty("sectionDensity", "compact")
        editor_layout.addWidget(editor_fill_title)
        editor_grid = QGridLayout()
        editor_grid.setContentsMargins(0, 0, 0, 0)
        editor_grid.setHorizontalSpacing(12)
        editor_grid.setVerticalSpacing(10)

        def add_editor_cell(row: int, column: int, label_text: str, widget) -> None:
            cell_layout = QVBoxLayout()
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(4)
            cell_label = QLabel(label_text)
            cell_label.setObjectName("MutedText")
            cell_label.setWordWrap(True)
            cell_layout.addWidget(cell_label)
            cell_layout.addWidget(widget)
            editor_grid.addLayout(cell_layout, row, column)

        add_editor_cell(0, 0, "标签", self.category_edit)
        add_editor_cell(0, 1, "名称", self.name_edit)
        add_editor_cell(1, 0, "类型", self.kind_combo)
        add_editor_cell(1, 1, "计划金额", self.planned_amount_edit)
        add_editor_cell(2, 0, "生效方式", self.effective_mode_combo)
        add_editor_cell(2, 1, "开始月份", self.effective_start_edit)
        add_editor_cell(3, 0, "结束月份", self.effective_end_edit)
        add_editor_cell(3, 1, "计划日", self.day_spin)
        add_editor_cell(4, 0, "提醒提前", self.reminder_days_spin)
        add_editor_cell(4, 1, "执行约束", self.required_checkbox)
        editor_layout.addLayout(editor_grid)
        editor_layout.addWidget(self.effective_mode_hint_label)

        notes_section_label = QLabel("备注")
        notes_section_label.setObjectName("SectionTitle")
        notes_section_label.setProperty("sectionDensity", "compact")
        editor_layout.addWidget(notes_section_label)
        self.notes_edit.setMinimumHeight(96)
        self.notes_edit.setMaximumHeight(132)
        editor_layout.addWidget(self.notes_edit)
        editor_layout.addWidget(self.editor_followup_hint_label)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        button_row.addWidget(self.save_line_button)
        button_row.addWidget(self.delete_line_button)
        button_row.addStretch(1)
        editor_layout.addLayout(button_row)

        annual_card, annual_layout = create_card("全年十二月", "先看每个月汇总，需要时再点开该月明细，不再直接摊全年宽表。")
        annual_card.setProperty("sectionRole", "budget-annual-overview")
        annual_card.setProperty("sectionDensity", "comfortable")
        annual_overview_strip = QFrame()
        annual_overview_strip.setObjectName("SectionCard")
        annual_overview_strip.setProperty("sectionRole", "annual-read-guide")
        annual_overview_strip.setProperty("sectionDensity", "compact")
        annual_overview_layout = QHBoxLayout(annual_overview_strip)
        annual_overview_layout.setContentsMargins(14, 12, 14, 12)
        annual_overview_layout.setSpacing(12)
        annual_overview_layout.addWidget(self.annual_overview_badge, 0, Qt.AlignmentFlag.AlignTop)
        annual_overview_layout.addWidget(self.annual_overview_summary, 1)
        annual_layout.addWidget(annual_overview_strip)
        annual_months_shell = QFrame()
        annual_months_shell.setObjectName("SectionCard")
        annual_months_shell.setProperty("sectionRole", "annual-accordion")
        annual_months_shell.setProperty("sectionDensity", "comfortable")
        annual_months_layout = QVBoxLayout(annual_months_shell)
        annual_months_layout.setContentsMargins(12, 12, 12, 12)
        annual_months_layout.setSpacing(10)
        for quarter_number in range(1, 5):
            annual_months_layout.addWidget(self._create_annual_quarter_section(quarter_number))
        annual_months_layout.addStretch(1)
        annual_layout.addWidget(annual_months_shell, 1)

        effective_scope_card, effective_scope_layout = create_card("生效范围", "和 HTML 优化稿一样，单独说明三种预算生效口径。")
        effective_scope_card.setProperty("sectionRole", "budget-effective-scope")
        effective_scope_layout.addWidget(self.effective_scope_hint_label)
        effective_scope_layout.addWidget(self.effective_scope_summary_label)
        for mode, scene, summary in (
            ("仅当前月", "活动、一次性购买、临时预算", "只在当前预算月生效，适合按月试跑或一次性支出。"),
            ("从当前月起", "房租、话费、会员、长期储蓄", "从开始月持续生效，不额外设置结束月。"),
            ("指定月份范围", "课程、阶段性计划、短周期专项", "按开始月到结束月生效，适合阶段型预算。"),
        ):
            effective_scope_layout.addWidget(self._create_effective_scope_row(mode, scene, summary))
        self.effective_scope_table.hide()

        self.workbench_splitter.addWidget(comparison_card)
        self.workbench_splitter.addWidget(editor_card)
        self.workbench_splitter.setStretchFactor(0, 3)
        self.workbench_splitter.setStretchFactor(1, 2)
        self.workbench_splitter.setSizes([860, 560])

        monthly_layout = QVBoxLayout(self.monthly_tab)
        monthly_layout.setContentsMargins(0, 0, 0, 0)
        monthly_layout.setSpacing(14)
        monthly_layout.addWidget(top_card)
        monthly_layout.addWidget(self.workbench_splitter, 1)

        annual_tab_layout = QVBoxLayout(self.annual_tab)
        annual_tab_layout.setContentsMargins(0, 0, 0, 0)
        annual_tab_layout.setSpacing(14)
        annual_tab_layout.addWidget(annual_card, 1)

        income_tab_layout = QVBoxLayout(self.income_tab)
        income_tab_layout.setContentsMargins(0, 0, 0, 0)
        income_tab_layout.addWidget(income_card)

        expense_tab_layout = QVBoxLayout(self.expense_tab)
        expense_tab_layout.setContentsMargins(0, 0, 0, 0)
        expense_tab_layout.addWidget(expense_card)

        effective_tab_layout = QVBoxLayout(self.effective_tab)
        effective_tab_layout.setContentsMargins(0, 0, 0, 0)
        effective_tab_layout.addWidget(effective_scope_card)

        self.tabs.addTab(self.monthly_tab, "预算工作台")
        self.tabs.addTab(self.annual_tab, "全年十二月")
        self.tabs.addTab(self.income_tab, "预计收入项")
        self.tabs.addTab(self.expense_tab, "预计支出项")
        self.tabs.addTab(self.effective_tab, "生效范围")

        self._populate_effective_scope_table()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

    def _connect_signals(self) -> None:
        self.month_edit.dateChanged.connect(self._emit_month_changed)
        self.save_budget_button.clicked.connect(self._emit_budget_save)
        self.seed_from_actual_button.clicked.connect(self._emit_budget_seed)
        self.new_line_button.clicked.connect(self.clear_line_editor)
        self.save_line_button.clicked.connect(self._emit_budget_line_save)
        self.delete_line_button.clicked.connect(self._emit_budget_line_delete)
        self.tag_filter_combo.currentTextChanged.connect(lambda *_args: self._load_comparison_tables(self._comparison) if self._comparison else None)
        self.annual_detail_kind_filter_combo.currentTextChanged.connect(self._apply_annual_detail_filters)
        self.annual_detail_tag_filter_combo.currentTextChanged.connect(self._apply_annual_detail_filters)
        self.annual_detail_status_filter_combo.currentTextChanged.connect(self._apply_annual_detail_filters)
        for label, button in self.annual_detail_quick_view_buttons.items():
            button.clicked.connect(lambda _checked=False, value=label: self._set_annual_detail_quick_view(value))
        self.annual_detail_single_month_button.toggled.connect(self._set_annual_detail_single_month_hidden)
        self.annual_detail_show_all_button.clicked.connect(self._clear_annual_detail_filters)
        self.effective_mode_combo.currentTextChanged.connect(self._sync_effective_controls)
        self.comparison_table.itemSelectionChanged.connect(lambda: self._handle_selection_changed(self.comparison_table))
        self.income_table.itemSelectionChanged.connect(lambda: self._handle_selection_changed(self.income_table))
        self.expense_table.itemSelectionChanged.connect(lambda: self._handle_selection_changed(self.expense_table))
        self._sync_annual_detail_quick_view_buttons()
        self._sync_effective_scope_table()
        self._sync_effective_mode_hint()

    def _create_effective_scope_row(self, mode: str, scene: str, summary: str) -> QFrame:
        row = QFrame()
        row.setObjectName("SectionCard")
        row.setProperty("sectionRole", "scope-row")
        row.setProperty("sectionDensity", "compact")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        title = QLabel(mode)
        title.setObjectName("SectionTitle")
        title.setProperty("sectionDensity", "compact")
        title.setMinimumWidth(96)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(4)
        scene_label = QLabel(f"适合场景：{scene}")
        scene_label.setWordWrap(True)
        summary_label = QLabel(summary)
        summary_label.setObjectName("MutedText")
        summary_label.setWordWrap(True)
        text_column.addWidget(scene_label)
        text_column.addWidget(summary_label)

        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_column, 1)
        self.effective_scope_rows.append(
            {
                "mode": mode,
                "frame": row,
                "title": title,
                "scene": scene_label,
                "summary": summary_label,
            }
        )
        return row

    def _create_annual_quarter_section(self, quarter_number: int) -> QFrame:
        palette = self._annual_quarter_palette(quarter_number)
        section = QFrame()
        section.setObjectName("SectionCard")
        section.setProperty("sectionRole", "annual-quarter-group")
        section.setProperty("quarterTone", f"q{quarter_number}")
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        badge = QFrame()
        badge.setObjectName("SectionCard")
        badge.setProperty("sectionRole", "annual-quarter-badge")
        badge.setProperty("quarterTone", f"q{quarter_number}")
        badge.setFixedWidth(58)
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 16, 0, 16)
        badge_layout.setSpacing(6)
        badge_label = QLabel(f"Q{quarter_number}")
        badge_label.setObjectName("SectionTitle")
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addStretch(1)
        badge_layout.addWidget(badge_label)
        badge_layout.addStretch(1)

        months_column = QVBoxLayout()
        months_column.setContentsMargins(0, 0, 0, 0)
        months_column.setSpacing(0)
        for month in range((quarter_number - 1) * 3 + 1, quarter_number * 3 + 1):
            months_column.addWidget(self._create_annual_month_row(month, palette["quarter"]))

        layout.addWidget(badge)
        layout.addLayout(months_column, 1)
        self.annual_quarter_sections[quarter_number] = {
            "frame": section,
            "badge": badge,
            "label": badge_label,
        }
        return section

    def _create_annual_month_row(self, month: int, quarter_color: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SectionCard")
        frame.setProperty("sectionRole", "annual-month-row")
        frame.setProperty("monthTone", f"m{month}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(14)

        month_column = QVBoxLayout()
        month_column.setContentsMargins(0, 0, 0, 0)
        month_column.setSpacing(4)
        month_label = QLabel(f"{month}月")
        month_label.setObjectName("SectionTitle")
        month_note = QLabel("展开查看当月详细预算项目。")
        month_note.setObjectName("MutedText")
        month_note.setWordWrap(True)
        month_note.setMinimumWidth(108)
        month_column.addWidget(month_label)
        month_column.addWidget(month_note)

        metrics_layout = QHBoxLayout()
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(14)
        metric_labels: dict[str, QLabel] = {}
        for key, title in (
            ("planned_income", "计划收入"),
            ("actual_income", "实际收入"),
            ("planned_expense", "计划支出"),
            ("actual_expense", "实际支出"),
            ("planned_balance", "计划结余"),
            ("actual_balance", "实际结余"),
            ("pending_amount", "待确认"),
        ):
            metric_frame = QFrame()
            metric_frame.setObjectName("SectionCard")
            metric_frame.setProperty("sectionRole", "annual-month-metric")
            metric_frame.setStyleSheet(f"QFrame#SectionCard[sectionRole=\"annual-month-metric\"] {{ background: {quarter_color}; border: 1px solid transparent; border-radius: 12px; }}")
            metric_box = QVBoxLayout(metric_frame)
            metric_box.setContentsMargins(10, 8, 10, 8)
            metric_box.setSpacing(2)
            title_label = QLabel(title)
            title_label.setObjectName("MutedText")
            value_label = QLabel("--")
            value_label.setObjectName("SectionTitle")
            metric_box.addWidget(title_label)
            metric_box.addWidget(value_label)
            metrics_layout.addWidget(metric_frame)
            metric_labels[key] = value_label

        status_column = QVBoxLayout()
        status_column.setContentsMargins(0, 0, 0, 0)
        status_column.setSpacing(8)
        status_title = QLabel("状态")
        status_title.setObjectName("MutedText")
        status_tag = TagLabel("待载入", "gray")
        toggle_button = QPushButton("展开")
        toggle_button.setObjectName("SecondaryActionButton")
        toggle_button.setCheckable(True)
        toggle_button.setProperty("sectionRole", "annual-month-toggle")
        status_column.addWidget(status_title, 0, Qt.AlignmentFlag.AlignRight)
        status_column.addWidget(status_tag, 0, Qt.AlignmentFlag.AlignRight)
        status_column.addWidget(toggle_button, 0, Qt.AlignmentFlag.AlignRight)
        status_column.addStretch(1)

        summary_row.addLayout(month_column)
        summary_row.addLayout(metrics_layout, 1)
        summary_row.addLayout(status_column)
        layout.addLayout(summary_row)

        detail_panel = QFrame()
        detail_panel.setObjectName("SectionCard")
        detail_panel.setProperty("sectionRole", "annual-month-detail")
        detail_panel.setVisible(False)
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(12)

        primary_row = QHBoxLayout()
        primary_row.setContentsMargins(0, 0, 0, 0)
        primary_row.setSpacing(12)
        income_panel = self._create_annual_month_detail_panel("固定收入", month, "收入")
        expense_panel = self._create_annual_month_detail_panel("固定支出", month, "支出")
        primary_row.addWidget(income_panel["frame"], 1, Qt.AlignmentFlag.AlignTop)
        primary_row.addWidget(expense_panel["frame"], 1, Qt.AlignmentFlag.AlignTop)
        detail_layout.addLayout(primary_row)

        auxiliary_row = QHBoxLayout()
        auxiliary_row.setContentsMargins(0, 0, 0, 0)
        auxiliary_row.setSpacing(12)
        temp_income_panel = self._create_annual_month_other_panel("临时收入 / 其他收入", month, "收入")
        temp_expense_panel = self._create_annual_month_other_panel("临时支出 / 其他支出", month, "支出")
        auxiliary_row.addWidget(temp_income_panel["frame"], 1, Qt.AlignmentFlag.AlignTop)
        auxiliary_row.addWidget(temp_expense_panel["frame"], 1, Qt.AlignmentFlag.AlignTop)
        detail_layout.addLayout(auxiliary_row)
        layout.addWidget(detail_panel)

        toggle_button.clicked.connect(lambda checked=False, value=month: self._set_expanded_annual_month(value, checked))

        self.annual_month_cards[month] = {
            "frame": frame,
            "month_label": month_label,
            "month_note": month_note,
            "metrics": metric_labels,
            "status_tag": status_tag,
            "toggle_button": toggle_button,
            "detail_panel": detail_panel,
            "income_panel": income_panel,
            "expense_panel": expense_panel,
            "temp_income_panel": temp_income_panel,
            "temp_expense_panel": temp_expense_panel,
        }
        return frame

    def _create_annual_month_detail_panel(self, title: str, month: int, detail_type: str) -> dict[str, object]:
        frame, layout = create_card(title, "")
        frame.setProperty("sectionRole", "annual-month-detail-panel")
        frame.setProperty("panelTone", "income" if detail_type == "收入" else "expense")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)
        planned_label = QLabel("计划 ¥0.00")
        actual_label = QLabel("实际 ¥0.00")
        pending_label = QLabel("待确认 ¥0.00")
        for label in (planned_label, actual_label, pending_label):
            label.setObjectName("MutedText")
            header_row.addWidget(label)
        header_row.addStretch(1)
        confirm_all_button = make_secondary_button("确认本区待确认")
        confirm_all_button.setProperty("sectionRole", "annual-month-other-action")
        confirm_all_button.setEnabled(False)
        header_row.addWidget(confirm_all_button)
        layout.addLayout(header_row)
        table = QTableWidget()
        prepare_table(table, ["项目", "标签", "计划", "实际", "待确认", "差额", "状态"])
        table.setProperty("tableProfile", "budget-ledger")
        table.setMinimumHeight(210)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        refresh_style(table)
        layout.addWidget(table)
        panel = {
            "frame": frame,
            "table": table,
            "planned_label": planned_label,
            "actual_label": actual_label,
            "pending_label": pending_label,
            "confirm_all_button": confirm_all_button,
            "month": month,
            "detail_type": detail_type,
            "rows": [],
        }
        confirm_all_button.clicked.connect(
            lambda checked=False, panel_ref=panel: self._confirm_all_annual_detail_panel(panel_ref)
        )
        return panel

    def _create_annual_month_other_panel(self, title_text: str, month: int, detail_type: str) -> dict[str, object]:
        frame = QFrame()
        frame.setObjectName("SectionCard")
        frame.setProperty("sectionRole", "annual-month-other-panel")
        frame.setProperty("sectionDensity", "compact")
        frame.setProperty("panelTone", "income" if detail_type == "收入" else "expense")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("SectionTitle")
        title.setProperty("sectionDensity", "compact")
        summary = QLabel("0 项 · 计划 ¥0.00 · 实际 ¥0.00 · 待确认 ¥0.00")
        summary.setObjectName("MutedText")
        toggle = make_secondary_button("展开明细")
        toggle.setCheckable(True)
        toggle.setProperty("sectionRole", "annual-month-toggle")
        header_row.addWidget(title)
        header_row.addWidget(summary, 1)
        header_row.addWidget(toggle)
        layout.addLayout(header_row)

        note = QLabel(
            "单月型、未设预算或真正零散的收入收在这里，避免主收入表过满。"
            if detail_type == "收入"
            else "单月型、未设预算或真正零散的支出收在这里，避免主支出表过满。"
        )
        note.setObjectName("MutedText")
        note.setWordWrap(True)
        layout.addWidget(note)

        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(8)
        actions_row.addStretch(1)
        confirm_same_button = make_secondary_button("确认同类待确认")
        confirm_same_button.setProperty("sectionRole", "annual-month-other-action")
        confirm_same_button.setEnabled(False)
        confirm_all_button = make_secondary_button("确认全部待确认")
        confirm_all_button.setProperty("sectionRole", "annual-month-other-action")
        confirm_all_button.setEnabled(False)
        actions_row.addWidget(confirm_same_button)
        actions_row.addWidget(confirm_all_button)
        layout.addLayout(actions_row)

        table = QTableWidget()
        prepare_table(table, ["项目", "标签", "计划", "实际", "待确认", "差额", "状态"])
        table.setProperty("tableProfile", "budget-ledger")
        table.setMinimumHeight(132)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVisible(False)
        refresh_style(table)
        layout.addWidget(table)
        frame.setVisible(False)

        panel = {
            "frame": frame,
            "month": month,
            "title": title,
            "summary": summary,
            "toggle": toggle,
            "note": note,
            "table": table,
            "detail_type": detail_type,
            "bucket_key": f"{detail_type}-其他",
            "confirm_same_button": confirm_same_button,
            "confirm_all_button": confirm_all_button,
            "rows": [],
        }
        toggle.toggled.connect(lambda checked=False, panel_ref=panel: self._set_annual_other_bucket_expanded(panel_ref, checked))
        table.itemSelectionChanged.connect(lambda panel_ref=panel: self._sync_annual_other_action_buttons(panel_ref))
        confirm_same_button.clicked.connect(lambda checked=False, panel_ref=panel: self._confirm_selected_annual_other_bucket(panel_ref))
        confirm_all_button.clicked.connect(lambda checked=False, panel_ref=panel: self._confirm_all_annual_other_bucket(panel_ref))
        return panel

    def load_budget(self, month_key: str, budget, budget_lines: list, comparison, annual_matrix=None) -> None:
        self._loading = True
        self._current_month_key = month_key
        self._expanded_annual_month = int(month_key[5:7])
        self._budget = budget
        self._budget_lines = list(budget_lines)
        self._comparison = comparison
        month = QDate.fromString(f"{month_key}-01", "yyyy-MM-dd")
        if month.isValid():
            self.month_edit.setDate(month)
            self.effective_start_edit.setDate(month)
            self.effective_end_edit.setDate(month)
        self.budget_notes_edit.setText(budget.notes if budget else "")
        self.scope_label.setText(f"{month_key} · 计划金额来自预算项自动合计；实际只统计已确认流水。")
        self._refresh_tag_filter(comparison.rows)
        self._load_summary_cards(comparison)
        self._load_comparison_tables(comparison)
        if annual_matrix is not None:
            self.load_annual_matrix(annual_matrix)
        self.clear_line_editor()
        self._loading = False

    def load_annual_matrix(self, annual_matrix) -> None:
        self._annual_matrix = annual_matrix
        self.annual_overview_badge.setText(f"{annual_matrix.year} 年预算板")
        self.annual_actual_summary_label.setText(f"{annual_matrix.year} 年实际回看")
        self.annual_planned_income_card.set_content(
            format_money(annual_matrix.planned_income),
            f"{annual_matrix.year} 年计划收入合计",
            "预期",
            "green",
        )
        self.annual_actual_income_card.set_content(
            format_money(annual_matrix.actual_income),
            "只统计已确认收入流水",
            "实际",
            "green",
        )
        self.annual_planned_expense_card.set_content(
            format_money(annual_matrix.planned_expense),
            "标签预算、固定支出、储蓄计划自动合计",
            "预期",
            "gray",
        )
        self.annual_actual_expense_card.set_content(
            format_money(annual_matrix.actual_expense),
            "只统计已确认支出，退款冲减",
            "实际",
            "gray",
        )
        balance_tone = "green" if annual_matrix.planned_balance >= 0 else "red"
        self.annual_planned_balance_card.set_content(
            format_money(annual_matrix.planned_balance),
            "计划收入 - 计划支出",
            "计划",
            balance_tone,
        )
        actual_balance_tone = "green" if annual_matrix.actual_balance >= 0 else "red"
        self.annual_actual_balance_card.set_content(
            format_money(annual_matrix.actual_balance),
            "已确认收入 - 已确认支出",
            "实际",
            actual_balance_tone,
        )
        pending_tone = "amber" if annual_matrix.pending_amount else "gray"
        self.annual_pending_card.set_content(
            format_money(annual_matrix.pending_amount),
            "待确认金额单独列，不进入正式统计",
            "单独列",
            pending_tone,
        )
        self._load_annual_quarter_cards(annual_matrix)
        self._load_annual_sheet_table(annual_matrix)
        self._load_annual_table(annual_matrix)
        self._refresh_annual_detail_filters(getattr(annual_matrix, "detail_rows", []) or [])
        self._load_annual_detail_table(annual_matrix)
        self._load_annual_month_sections(annual_matrix)

    def clear_line_editor(self) -> None:
        self._current_line_id = ""
        self.editor_context_label.setText("新预算项")
        self.editor_hint_label.setText("按 生效方式 -> 标签 -> 金额 -> 备注 的顺序连续填写；左侧未设预算行会自动带入建议金额。")
        self.kind_combo.setCurrentText("标签预算")
        self.name_edit.clear()
        self.category_edit.clear()
        self.planned_amount_edit.clear()
        self.day_spin.setValue(0)
        self.required_checkbox.setChecked(False)
        self.reminder_days_spin.setValue(0)
        self.notes_edit.clear()
        self._set_effective_range(self._current_month_key, self._current_month_key)
        self.effective_mode_combo.setCurrentText("仅当前月")
        self.delete_line_button.setEnabled(False)
        self._sync_effective_controls()

    def _populate_effective_scope_table(self) -> None:
        rows = [
            ("仅当前月", "活动、一次性购买、临时预算", "当前月单独生效"),
            ("从当前月起", "房租、话费、会员、长期储蓄", "从开始月持续生效"),
            ("指定月份范围", "课程、阶段性计划、短周期专项", "开始月到结束月之间生效"),
        ]
        self.effective_scope_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.effective_scope_table.setItem(row_index, column_index, item)
        sync_table_columns(self.effective_scope_table)
        self.effective_scope_table.resizeRowsToContents()

    def _sync_effective_scope_table(self) -> None:
        mode = self.effective_mode_combo.currentText().strip()
        row_by_mode = {
            "仅当前月": 0,
            "从当前月起": 1,
            "指定月份范围": 2,
        }
        row = row_by_mode.get(mode)
        if row is None:
            self.effective_scope_table.clearSelection()
        else:
            self.effective_scope_table.selectRow(row)

        for index, widgets in enumerate(self.effective_scope_rows):
            frame = widgets["frame"]
            title = widgets["title"]
            is_active = index == row
            frame.setStyleSheet(
                (
                    "QFrame#SectionCard { border: 1px solid #b8cbff; background: #eef4ff; }"
                    if is_active
                    else "QFrame#SectionCard { border: 1px solid #d8e1f2; background: #fbfcff; }"
                )
            )
            title.setText(str(widgets["mode"]))
            if is_active:
                title.setText(f"当前使用 · {title.text()}")

    def _load_annual_month_sections(self, annual_matrix) -> None:
        months = list(getattr(annual_matrix, "months", []) or [])
        expanded_month = self._expanded_annual_month if 1 <= self._expanded_annual_month <= 12 else int(self._current_month_key[5:7])
        self._expanded_annual_month = expanded_month
        self.annual_overview_summary.setText(
            f"范围：{annual_matrix.year} 年。每个月先看一行汇总，需要时再展开该月查看详细项目。"
        )
        for month in range(1, 13):
            widgets = self.annual_month_cards.get(month)
            if widgets is None:
                continue
            month_point = months[month - 1] if month - 1 < len(months) else None
            self._fill_annual_month_summary(month, widgets, month_point)
            self._fill_annual_month_details(month, widgets, annual_matrix)
        self._sync_annual_month_expansion()

    def _fill_annual_month_summary(self, month: int, widgets: dict[str, object], month_point) -> None:
        metrics: dict[str, QLabel] = widgets["metrics"]  # type: ignore[assignment]
        if month_point is None:
            for label in metrics.values():
                label.setText("--")
            widgets["month_note"].setText("当月还没有预算或流水。")  # type: ignore[index]
            widgets["status_tag"].setText("待载入")  # type: ignore[index]
            widgets["status_tag"].set_tone("gray")  # type: ignore[index]
            return

        values = {
            "planned_income": parse_decimal(getattr(month_point, "planned_income", Decimal("0.00"))),
            "actual_income": parse_decimal(getattr(month_point, "actual_income", Decimal("0.00"))),
            "planned_expense": parse_decimal(getattr(month_point, "planned_expense", Decimal("0.00"))),
            "actual_expense": parse_decimal(getattr(month_point, "actual_expense", Decimal("0.00"))),
            "planned_balance": parse_decimal(getattr(month_point, "planned_balance", Decimal("0.00"))),
            "actual_balance": parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00"))),
            "pending_amount": parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00"))),
        }
        for key, label in metrics.items():
            label.setText(format_money(values[key]))

        detail_counts = self._annual_month_detail_counts(month)
        widgets["month_note"].setText(  # type: ignore[index]
            f"收入 {detail_counts['income']} 项 · 支出 {detail_counts['expense']} 项 · 其他 {detail_counts['other']} 项"
        )
        status_text, tone = self._annual_month_card_status(values)
        widgets["status_tag"].setText(status_text)  # type: ignore[index]
        widgets["status_tag"].set_tone(tone)  # type: ignore[index]

    def _annual_month_detail_counts(self, month: int) -> dict[str, int]:
        rows = list(getattr(self._annual_matrix, "detail_rows", []) or [])
        counts = {"income": 0, "expense": 0, "other": 0}
        year = getattr(self._annual_matrix, "year", None)
        month_key = f"{year:04d}-{month:02d}" if year else f"{month:02d}"
        for detail_row in rows:
            planned = parse_decimal(self._annual_month_value(detail_row, "planned_months", month_key, month))
            actual = parse_decimal(self._annual_month_value(detail_row, "actual_months", month_key, month))
            pending = parse_decimal(self._annual_month_value(detail_row, "pending_months", month_key, month))
            has_value = planned != Decimal("0.00") or actual != Decimal("0.00") or pending != Decimal("0.00")
            is_other_bucket = self._is_annual_month_other_bucket_item(detail_row)
            if is_other_bucket:
                if has_value:
                    counts["other"] += 1
                continue
            if not has_value and not self._annual_detail_effective_in_month(detail_row, month_key):
                continue
            if self._stored_line_kind(getattr(detail_row, "line_kind", "") or "") == "收入":
                counts["income"] += 1
            else:
                counts["expense"] += 1
        return counts

    def _annual_month_card_status(self, values: dict[str, Decimal]) -> tuple[str, str]:
        planned_expense = values["planned_expense"]
        actual_expense = values["actual_expense"]
        planned_balance = values["planned_balance"]
        actual_balance = values["actual_balance"]
        pending_amount = values["pending_amount"]
        if all(value == Decimal("0.00") for value in values.values()):
            return "未预算", "amber"
        if pending_amount > Decimal("0.00") and actual_balance < Decimal("0.00"):
            return "收入支出", "red"
        if pending_amount > Decimal("0.00"):
            return "待确认", "amber"
        if actual_balance < Decimal("0.00") or (
            planned_expense > Decimal("0.00") and actual_expense > planned_expense
        ):
            return "收入支出", "red"
        if planned_balance > Decimal("0.00") and actual_balance >= Decimal("0.00"):
            return "计划盈余", "green"
        return "已达成", "green"

    def _fill_annual_month_details(self, month: int, widgets: dict[str, object], annual_matrix) -> None:
        detail_rows = list(getattr(annual_matrix, "detail_rows", []) or [])
        income_rows = self._annual_month_detail_rows(detail_rows, month, "收入")
        expense_rows = self._annual_month_detail_rows(detail_rows, month, "支出")
        income_main_rows = [row for row in income_rows if not row["bucket_other"]]
        income_other_rows = [row for row in income_rows if row["bucket_other"]]
        expense_main_rows = [row for row in expense_rows if not row["bucket_other"]]
        expense_other_rows = [row for row in expense_rows if row["bucket_other"]]
        self._populate_annual_month_detail_table(widgets["income_panel"], income_main_rows, "收入")
        self._populate_annual_month_detail_table(widgets["expense_panel"], expense_main_rows, "支出")
        self._populate_annual_month_other_panel(
            widgets["temp_income_panel"],
            sorted(income_other_rows, key=lambda row: row["name"]),
        )
        self._populate_annual_month_other_panel(
            widgets["temp_expense_panel"],
            sorted(expense_other_rows, key=lambda row: row["name"]),
        )

    def _annual_month_detail_rows(self, detail_rows: list, month: int, detail_type: str) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        year = getattr(self._annual_matrix, "year", None)
        month_key = f"{year:04d}-{month:02d}" if year else f"{month:02d}"
        for detail_row in detail_rows:
            normalized_kind = self._stored_line_kind(getattr(detail_row, "line_kind", "") or "")
            if detail_type == "收入" and normalized_kind != "收入":
                continue
            if detail_type == "支出" and normalized_kind == "收入":
                continue
            planned = parse_decimal(self._annual_month_value(detail_row, "planned_months", month_key, month))
            actual = parse_decimal(self._annual_month_value(detail_row, "actual_months", month_key, month))
            pending = parse_decimal(self._annual_month_value(detail_row, "pending_months", month_key, month))
            has_value = planned != Decimal("0.00") or actual != Decimal("0.00") or pending != Decimal("0.00")
            bucket_other = self._is_annual_month_other_bucket_item(detail_row)
            is_effective_in_month = self._annual_detail_effective_in_month(detail_row, month_key)
            if bucket_other:
                if not has_value:
                    continue
            elif not has_value and not is_effective_in_month:
                continue
            delta = (actual - planned) if normalized_kind == "收入" else (planned - actual)
            rows.append(
                {
                    "name": getattr(detail_row, "name", "") or "",
                    "category": getattr(detail_row, "category", "") or "",
                    "detail_type": detail_type,
                    "line_kind": normalized_kind,
                    "month": month,
                    "planned": planned.quantize(Decimal("0.01")),
                    "actual": actual.quantize(Decimal("0.01")),
                    "pending": pending.quantize(Decimal("0.01")),
                    "delta": delta.quantize(Decimal("0.01")),
                    "status": self._annual_month_item_status(normalized_kind, planned, actual, pending, getattr(detail_row, "notes", "") or ""),
                    "bucket_other": bucket_other,
                }
            )
        return sorted(rows, key=lambda row: (row["name"] == "其他", row["name"]))

    def _annual_month_item_status(self, line_kind: str, planned: Decimal, actual: Decimal, pending: Decimal, notes: str) -> str:
        if "草稿待调整" in notes:
            return "草稿待调整"
        if pending > Decimal("0.00"):
            return "待确认"
        if planned <= Decimal("0.00"):
            return "未预算"
        if line_kind == "收入":
            if actual >= planned:
                return "已达成"
            if actual > Decimal("0.00"):
                return "进行中"
            return "未发生"
        if actual > planned:
            return "超支"
        if actual > Decimal("0.00"):
            return "已达成"
        return "未发生"

    def _is_other_annual_detail_item(self, detail_row) -> bool:
        name = (getattr(detail_row, "name", "") or "").strip()
        category = (getattr(detail_row, "category", "") or "").strip()
        group_name = (getattr(detail_row, "group_name", "") or "").strip()
        status = (getattr(detail_row, "status", "") or "").strip()
        return (
            "其他" in name
            or "其他" in category
            or group_name == "未设预算但本月有实际"
            or status in {"未设预算", "有待确认"}
        )

    def _is_annual_month_other_bucket_item(self, detail_row) -> bool:
        if not self._is_single_month_annual_detail_row(detail_row):
            return False
        planned_total = parse_decimal(getattr(detail_row, "planned_total", Decimal("0.00")))
        status = (getattr(detail_row, "status", "") or "").strip()
        group_name = (getattr(detail_row, "group_name", "") or "").strip()
        return (
            planned_total <= Decimal("0.00")
            or status in {"未设预算", "有待确认"}
            or group_name == "未设预算但本月有实际"
            or self._is_other_annual_detail_item(detail_row)
        )

    def _populate_annual_month_detail_table(
        self,
        panel: dict[str, object],
        rows: list[dict[str, object]],
        detail_type: str,
    ) -> None:
        table: QTableWidget = panel["table"]  # type: ignore[assignment]
        planned_total = sum((parse_decimal(row["planned"]) for row in rows), Decimal("0.00"))
        actual_total = sum((parse_decimal(row["actual"]) for row in rows), Decimal("0.00"))
        pending_total = sum((parse_decimal(row["pending"]) for row in rows), Decimal("0.00"))
        panel["planned_label"].setText(f"计划 {format_money(planned_total)}")  # type: ignore[index]
        panel["actual_label"].setText(f"实际 {format_money(actual_total)}")  # type: ignore[index]
        panel["pending_label"].setText(f"待确认 {format_money(pending_total)}")  # type: ignore[index]
        panel["rows"] = list(rows)
        table.clearSpans()
        table.setRowCount(0)
        if not rows:
            empty_text = f"这个月还没有{detail_type}主项目。"
            self._append_empty_row(table, empty_text)
            sync_table_columns(table)
            table.resizeRowsToContents()
            self._fit_annual_detail_table_height(table)
            self._sync_annual_detail_action_button(panel)
        else:
            for row_values in rows:
                row = table.rowCount()
                table.insertRow(row)
                values = [
                    row_values["name"],
                    row_values["category"],
                    format_money(row_values["planned"]),
                    format_money(row_values["actual"]),
                    format_money(row_values["pending"]),
                    self._format_signed_money(row_values["delta"]),
                    row_values["status"],
                ]
                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    if column_index in {2, 3, 4, 5}:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    if column_index == 5:
                        brush_kind = "收入" if detail_type == "收入" else "支出"
                        item.setForeground(self._annual_detail_delta_brush(brush_kind, parse_decimal(row_values["delta"])))
                    table.setItem(row, column_index, item)
                self._set_annual_status_cell_widget(table, row, 6, row_values)
            sync_table_columns(table)
            table.resizeRowsToContents()
            self._fit_annual_detail_table_height(table)
            self._sync_annual_detail_action_button(panel)
    def _populate_annual_month_other_panel(
        self,
        panel: dict[str, object],
        rows: list[dict[str, object]],
    ) -> None:
        other_frame: QFrame = panel["frame"]  # type: ignore[assignment]
        other_toggle: QPushButton = panel["toggle"]  # type: ignore[assignment]
        other_table: QTableWidget = panel["table"]  # type: ignore[assignment]
        other_summary: QLabel = panel["summary"]  # type: ignore[assignment]
        panel["rows"] = list(rows)
        if not rows:
            other_summary.setText("0 项 · 计划 ¥0.00 · 实际 ¥0.00 · 待确认 ¥0.00")
            other_toggle.blockSignals(True)
            other_toggle.setChecked(False)
            other_toggle.setEnabled(False)
            other_toggle.setText("暂无明细")
            other_toggle.blockSignals(False)
            other_table.setVisible(False)
            other_table.setRowCount(0)
            other_frame.setVisible(True)
            self._fit_annual_detail_table_height(other_table)
            self._sync_annual_other_action_buttons(panel)
            return

        planned_total = sum((parse_decimal(row["planned"]) for row in rows), Decimal("0.00"))
        actual_total = sum((parse_decimal(row["actual"]) for row in rows), Decimal("0.00"))
        pending_total = sum((parse_decimal(row["pending"]) for row in rows), Decimal("0.00"))
        other_summary.setText(
            f"{len(rows)} 项 · 计划 {format_money(planned_total)} · 实际 {format_money(actual_total)} · 待确认 {format_money(pending_total)}"
        )
        other_frame.setVisible(True)
        other_toggle.setEnabled(True)

        other_table.clearSpans()
        other_table.setRowCount(0)
        for row_values in rows:
            row = other_table.rowCount()
            other_table.insertRow(row)
            values = [
                row_values["name"],
                row_values["category"],
                format_money(row_values["planned"]),
                format_money(row_values["actual"]),
                format_money(row_values["pending"]),
                self._format_signed_money(row_values["delta"]),
                row_values["status"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if column_index in {2, 3, 4, 5}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if column_index == 5:
                    item.setForeground(self._annual_detail_delta_brush(str(row_values["detail_type"]), parse_decimal(row_values["delta"])))
                other_table.setItem(row, column_index, item)
            self._set_annual_status_cell_widget(other_table, row, 6, row_values)
        sync_table_columns(other_table)
        other_table.resizeRowsToContents()
        self._fit_annual_detail_table_height(other_table)
        if other_table.rowCount() > 0:
            target_row = 0
            for index, row_values in enumerate(rows):
                if self._is_actionable_pending_row(row_values):
                    target_row = index
                    break
            other_table.selectRow(target_row)
        self._sync_annual_other_bucket(panel)
        self._sync_annual_other_action_buttons(panel)

    def _is_actionable_pending_row(self, row_values: dict[str, object]) -> bool:
        pending = parse_decimal(row_values.get("pending", Decimal("0.00")))
        return pending > Decimal("0.00")

    def _set_annual_status_cell_widget(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        row_values: dict[str, object],
    ) -> None:
        status_text = str(row_values.get("status") or "")
        cell = QWidget()
        cell.setProperty("sectionRole", "status-cell")
        cell.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(3, 2, 3, 2)
        layout.setSpacing(4)
        if self._is_actionable_pending_row(row_values):
            confirm_button = make_secondary_button("待确认 · 确认")
            confirm_button.setProperty("sectionRole", "status-action")
            confirm_button.setProperty("statusTone", "pending")
            confirm_button.setToolTip("确认并同步这条预算项对应的待确认流水。")
            confirm_button.clicked.connect(
                lambda checked=False, month_key=self._month_key_for_annual_row(row_values), detail_type=str(row_values.get("detail_type") or ""), category=str(row_values.get("category") or ""), name=str(row_values.get("name") or ""): self._confirm_annual_status_row(
                    month_key,
                    detail_type,
                    category,
                    name,
                )
            )
            layout.addWidget(confirm_button, 1)
            table.setRowHeight(row, max(table.rowHeight(row), 36))
        else:
            badge = TagLabel(status_text or "未发生", self._status_tone(status_text))
            badge.setProperty("sectionRole", "status-badge")
            badge.setToolTip("状态按预算与流水自动计算；没有待确认金额的行保持只读。")
            layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setCellWidget(row, column, cell)

    def _confirm_annual_status_row(
        self,
        month_key: str,
        detail_type: str,
        category: str,
        name: str,
    ) -> None:
        self._emit_annual_status_change(
            {
                "month_key": month_key,
                "detail_type": detail_type,
                "category": category,
                "name": name,
                "target_status": "已确认",
                "mode": "single",
            }
        )

    def _status_tone(self, status: str) -> str:
        normalized = status.strip()
        if normalized in {"已达成", "进行中", "未发生"}:
            return "green"
        if normalized in {"临界", "有待确认", "草稿待调整", "未设预算", "待确认"}:
            return "amber"
        if normalized == "超支":
            return "red"
        return "gray"

    def _emit_annual_status_change(self, payload: dict[str, object]) -> None:
        self.annual_status_change_requested.emit(payload)

    def _sync_annual_detail_action_button(self, panel: dict[str, object]) -> None:
        confirm_all_button: QPushButton = panel["confirm_all_button"]  # type: ignore[assignment]
        rows: list[dict[str, object]] = panel.get("rows", [])  # type: ignore[assignment]
        confirm_all_button.setEnabled(any(self._is_actionable_pending_row(row) for row in rows))

    def _confirm_all_annual_detail_panel(self, panel: dict[str, object]) -> None:
        rows: list[dict[str, object]] = panel.get("rows", [])  # type: ignore[assignment]
        pending_rows = [row for row in rows if self._is_actionable_pending_row(row)]
        if not pending_rows:
            return
        self._emit_annual_status_change(
            {
                "month_key": self._month_key_for_annual_row(pending_rows[0]),
                "target_status": "已确认",
                "mode": "all_panel",
                "match_rows": [
                    {
                        "detail_type": str(row.get("detail_type") or ""),
                        "category": str(row.get("category") or ""),
                        "name": str(row.get("name") or ""),
                    }
                    for row in pending_rows
                ],
            }
        )

    def _fit_annual_detail_table_height(self, table: QTableWidget) -> None:
        header_height = table.horizontalHeader().height() if table.horizontalHeader() is not None else 0
        row_heights = sum(table.rowHeight(row) for row in range(table.rowCount()))
        frame_padding = table.frameWidth() * 2
        horizontal_scroll_height = table.horizontalScrollBar().sizeHint().height() if table.horizontalScrollBar() is not None else 0
        extra_padding = 18
        minimum_height = 96
        target_height = max(
            minimum_height,
            header_height + row_heights + frame_padding + horizontal_scroll_height + extra_padding,
        )
        table.setFixedHeight(target_height)

    def _set_expanded_annual_month(self, month: int, checked: bool) -> None:
        if checked:
            self._expanded_annual_month = month
        elif self._expanded_annual_month == month:
            self._expanded_annual_month = 0
        self._sync_annual_month_expansion()

    def _set_annual_other_bucket_expanded(self, panel: dict[str, object], checked: bool) -> None:
        month = int(panel["month"])
        key = (month, str(panel["bucket_key"]))
        if checked:
            self._expanded_annual_other_buckets.add(key)
        else:
            self._expanded_annual_other_buckets.discard(key)
        self._sync_annual_other_bucket(panel)

    def _sync_annual_other_bucket(self, panel: dict[str, object]) -> None:
        month = int(panel["month"])
        expanded = (month, str(panel["bucket_key"])) in self._expanded_annual_other_buckets
        toggle: QPushButton = panel["toggle"]  # type: ignore[assignment]
        table: QTableWidget = panel["table"]  # type: ignore[assignment]
        toggle.blockSignals(True)
        toggle.setChecked(expanded)
        toggle.setText("收起明细" if expanded else "展开明细")
        toggle.blockSignals(False)
        table.setVisible(expanded)
        self._sync_annual_other_action_buttons(panel)

    def _sync_annual_other_action_buttons(self, panel: dict[str, object]) -> None:
        table: QTableWidget = panel["table"]  # type: ignore[assignment]
        confirm_same_button: QPushButton = panel["confirm_same_button"]  # type: ignore[assignment]
        confirm_all_button: QPushButton = panel["confirm_all_button"]  # type: ignore[assignment]
        rows: list[dict[str, object]] = panel.get("rows", [])  # type: ignore[assignment]
        expanded = not table.isHidden()
        pending_rows = [row for row in rows if self._is_actionable_pending_row(row)]
        confirm_all_button.setEnabled(expanded and bool(pending_rows))

        selected_row_values = self._selected_annual_other_row(panel)
        confirm_same_button.setEnabled(
            expanded and selected_row_values is not None and self._is_actionable_pending_row(selected_row_values)
        )

    def _selected_annual_other_row(self, panel: dict[str, object]) -> dict[str, object] | None:
        table: QTableWidget = panel["table"]  # type: ignore[assignment]
        rows: list[dict[str, object]] = panel.get("rows", [])  # type: ignore[assignment]
        current_row = table.currentRow()
        if current_row < 0 or current_row >= len(rows):
            return None
        return rows[current_row]

    def _confirm_selected_annual_other_bucket(self, panel: dict[str, object]) -> None:
        row_values = self._selected_annual_other_row(panel)
        if row_values is None or not self._is_actionable_pending_row(row_values):
            return
        self._emit_annual_status_change(
            {
                "month_key": self._month_key_for_annual_row(row_values),
                "detail_type": str(row_values.get("detail_type") or ""),
                "category": str(row_values.get("category") or ""),
                "name": str(row_values.get("name") or ""),
                "target_status": "已确认",
                "mode": "same_category",
            }
        )

    def _confirm_all_annual_other_bucket(self, panel: dict[str, object]) -> None:
        rows: list[dict[str, object]] = panel.get("rows", [])  # type: ignore[assignment]
        pending_rows = [row for row in rows if self._is_actionable_pending_row(row)]
        if not pending_rows:
            return
        self._emit_annual_status_change(
            {
                "month_key": self._month_key_for_annual_row(pending_rows[0]),
                "target_status": "已确认",
                "mode": "all_other",
                "match_rows": [
                    {
                        "detail_type": str(row.get("detail_type") or ""),
                        "category": str(row.get("category") or ""),
                        "name": str(row.get("name") or ""),
                    }
                    for row in pending_rows
                ],
            }
        )

    def _month_key_for_annual_row(self, row_values: dict[str, object]) -> str:
        year = getattr(self._annual_matrix, "year", QDate.currentDate().year())
        month = row_values.get("month")
        detail_month = int(month) if month else int(self._current_month_key[5:7])
        return f"{year:04d}-{detail_month:02d}"

    def _sync_annual_month_expansion(self) -> None:
        for month, widgets in self.annual_month_cards.items():
            expanded = month == self._expanded_annual_month
            toggle_button: QPushButton = widgets["toggle_button"]  # type: ignore[assignment]
            toggle_button.blockSignals(True)
            toggle_button.setChecked(expanded)
            toggle_button.setText("收起" if expanded else "展开")
            toggle_button.blockSignals(False)
            widgets["detail_panel"].setVisible(expanded)  # type: ignore[index]

    def _load_summary_cards(self, comparison) -> None:
        summary = comparison.summary
        self.planned_income_card.set_content(
            format_money(summary.planned_income),
            f"实际 {format_money(summary.actual_income)}",
            "收入计划",
            "green",
        )
        self.planned_expense_card.set_content(
            format_money(summary.planned_expense),
            f"已确认支出 {format_money(summary.actual_expense)}",
            "自动合计",
            "gray",
        )
        balance_tone = "green" if summary.actual_balance >= 0 else "red"
        self.balance_card.set_content(
            format_money(summary.planned_balance),
            f"实际结余 {format_money(summary.actual_balance)}",
            "收入-支出",
            balance_tone,
        )
        pending_tone = "amber" if summary.pending_amount else "gray"
        self.pending_card.set_content(
            format_money(summary.pending_amount),
            "待确认，不进入正式预算消耗",
            "单独列",
            pending_tone,
        )

    def _load_comparison_tables(self, comparison) -> None:
        all_rows = comparison.rows
        rows = self._filtered_rows(all_rows)
        income_rows = [
            row for row in rows
            if row.line_kind == "收入" or (row.group_name == "未设预算但本月有实际" and row.line_kind == "收入")
        ]
        expense_rows = [row for row in rows if row not in income_rows]
        self._load_workbench_table(rows)
        self._load_table(self.income_table, income_rows, "当前月份还没有预计收入项。")
        self._load_table(self.expense_table, expense_rows, "当前月份还没有预计支出项。")
        self.seed_from_actual_button.setEnabled(any(row.group_name == "未设预算但本月有实际" for row in all_rows))

    def _load_workbench_table(self, rows: list) -> None:
        self.comparison_table.clearSpans()
        self.comparison_table.setRowCount(0)
        current_group = ""
        for comparison_row in rows:
            if comparison_row.group_name != current_group:
                current_group = comparison_row.group_name
                self._append_group_row(self.comparison_table, current_group)
            self._append_workbench_row(comparison_row)
        if not rows:
            self._append_empty_row(self.comparison_table, "当前月份还没有预算项对比。")
        sync_table_columns(self.comparison_table)
        self.comparison_table.resizeRowsToContents()

    def _append_workbench_row(self, comparison_row) -> None:
        row = self.comparison_table.rowCount()
        self.comparison_table.insertRow(row)
        values = [
            comparison_row.name,
            self._display_line_kind(comparison_row.line_kind),
            comparison_row.category,
            self._effective_text(comparison_row.effective_start_month, comparison_row.effective_end_month),
            format_money(comparison_row.planned_amount),
            format_money(comparison_row.actual_amount),
            format_money(comparison_row.pending_amount),
            self._format_signed_money(comparison_row.delta_amount),
            comparison_row.status,
        ]
        payload = {
            "is_group": False,
            "line_id": comparison_row.line_id,
            "line_kind": comparison_row.line_kind,
            "name": comparison_row.name,
            "category": comparison_row.category,
            "notes": comparison_row.notes,
            "effective_start_month": comparison_row.effective_start_month,
            "effective_end_month": comparison_row.effective_end_month,
            "suggested_amount": f"{parse_decimal(comparison_row.actual_amount):.2f}",
            "status": comparison_row.status,
        }
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column_index == 0:
                item.setData(Qt.ItemDataRole.UserRole, payload)
                if comparison_row.notes:
                    item.setToolTip(self._one_line_note(comparison_row.notes))
            if column_index in {4, 5, 6, 7}:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if column_index == 8:
                item.setForeground(self._status_brush(comparison_row.status))
            self.comparison_table.setItem(row, column_index, item)

    def _load_annual_table(self, annual_matrix) -> None:
        self.annual_table.clearSpans()
        self.annual_table.setRowCount(0)
        months = list(getattr(annual_matrix, "months", []) or [])
        quarter_labels = ("Q1 一季度", "Q2 二季度", "Q3 三季度", "Q4 四季度")

        for quarter_index, quarter_label in enumerate(quarter_labels):
            start = quarter_index * 3
            quarter_months = months[start : start + 3]
            quarter_palette = self._annual_quarter_palette(quarter_index + 1)
            self._append_annual_summary_row(
                f"{quarter_label}合计",
                quarter_months,
                quarter_palette["quarter"],
                is_quarter=True,
            )
            for month_offset, month_point in enumerate(quarter_months, start=1):
                month_number = start + month_offset
                month_palette = self._annual_month_palette(month_number)
                self._append_annual_summary_row(
                    f"    {month_number}月",
                    [month_point],
                    month_palette["month_row"],
                    is_quarter=False,
                )
        sync_table_columns(self.annual_table)
        self.annual_table.resizeRowsToContents()

    def _load_annual_sheet_table(self, annual_matrix) -> None:
        months = list(getattr(annual_matrix, "months", []) or [])
        rows = [
            (
                "收入",
                "planned_income",
                "actual_income",
            ),
            (
                "支出",
                "planned_expense",
                "actual_expense",
            ),
            (
                "结余",
                "planned_balance",
                "actual_balance",
            ),
            (
                "待确认",
                "",
                "pending_amount",
            ),
        ]
        self.annual_sheet_table.setRowCount(len(rows))
        self._apply_annual_sheet_header_colors()
        for row_index, (label, planned_field, actual_field) in enumerate(rows):
            label_item = QTableWidgetItem(label)
            label_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            label_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font = label_item.font()
            font.setBold(True)
            label_item.setFont(font)
            label_item.setBackground(QColor("#f8fbff"))
            self.annual_sheet_table.setItem(row_index, 0, label_item)
            for month_index in range(12):
                month_point = months[month_index] if month_index < len(months) else None
                month_palette = self._annual_month_palette(month_index + 1)
                planned_value = (
                    format_money(getattr(month_point, planned_field))
                    if month_point is not None and planned_field
                    else "—"
                )
                actual_value = (
                    format_money(getattr(month_point, actual_field))
                    if month_point is not None and actual_field
                    else "—"
                )
                planned_item = QTableWidgetItem(planned_value)
                actual_item = QTableWidgetItem(actual_value)
                planned_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                actual_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                planned_item.setBackground(QColor(month_palette["sheet_cell"]))
                actual_item.setBackground(QColor(month_palette["sheet_cell"]))
                if label == "结余" and month_point is not None:
                    planned_balance = parse_decimal(getattr(month_point, "planned_balance", Decimal("0.00")))
                    actual_balance = parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00")))
                    planned_item.setForeground(self._status_brush("已达成" if planned_balance >= 0 else "超支"))
                    actual_item.setForeground(self._status_brush("已达成" if actual_balance >= 0 else "超支"))
                if label == "待确认" and month_point is not None:
                    pending_amount = parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00")))
                    if pending_amount > Decimal("0.00"):
                        actual_item.setForeground(self._status_brush("有待确认"))
                self.annual_sheet_table.setItem(row_index, month_index * 2 + 1, planned_item)
                self.annual_sheet_table.setItem(row_index, month_index * 2 + 2, actual_item)
        sync_table_columns(self.annual_sheet_table)
        self.annual_sheet_table.resizeRowsToContents()

    def _append_annual_summary_row(
        self,
        label: str,
        month_points: list,
        background: str,
        *,
        is_quarter: bool,
    ) -> None:
        row = self.annual_table.rowCount()
        self.annual_table.insertRow(row)
        self.annual_table.setRowHeight(row, 38 if is_quarter else 34)
        label_item = QTableWidgetItem(label)
        label_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        label_item.setBackground(QColor(background))
        label_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if is_quarter:
            label_item.setForeground(self._annual_quarter_brush(month_points))
            label_item.setToolTip(self._annual_quarter_tooltip(month_points))
        else:
            label_item.setForeground(self._annual_month_label_brush(month_points[0] if month_points else None))
            label_item.setToolTip(self._annual_month_tooltip(month_points[0] if month_points else None))
        font = label_item.font()
        font.setBold(is_quarter)
        label_item.setFont(font)
        self.annual_table.setItem(row, 0, label_item)

        field_names = (
            "planned_income",
            "actual_income",
            "planned_expense",
            "actual_expense",
            "planned_balance",
            "actual_balance",
            "pending_amount",
        )
        for column_index, field_name in enumerate(field_names, start=1):
            total = sum(
                (parse_decimal(getattr(month_point, field_name, Decimal("0.00"))) for month_point in month_points),
                Decimal("0.00"),
            )
            item = QTableWidgetItem(format_money(total))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item.setBackground(QColor(background))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if field_name in {"planned_balance", "actual_balance"}:
                item.setForeground(self._status_brush("已达成" if total >= Decimal("0.00") else "超支"))
            elif field_name == "pending_amount" and total > Decimal("0.00"):
                item.setForeground(self._status_brush("有待确认"))
            if is_quarter:
                value_font = item.font()
                value_font.setBold(True)
                item.setFont(value_font)
            self.annual_table.setItem(row, column_index, item)

    def _load_annual_quarter_cards(self, annual_matrix) -> None:
        months = list(getattr(annual_matrix, "months", []) or [])
        focus_labels = []
        for quarter_index, widgets in enumerate(self.annual_quarter_cards):
            quarter_months = months[quarter_index * 3 : quarter_index * 3 + 3]
            if not quarter_months:
                widgets["status"].setText("空")
                widgets["status"].set_tone("gray")
                widgets["planned"].setText("计划结余 --")
                widgets["actual"].setText("实际结余 --")
                widgets["note"].setText("这个季度还没有年度数据。")
                continue

            planned_balance = sum(
                (parse_decimal(getattr(month_point, "planned_balance", Decimal("0.00"))) for month_point in quarter_months),
                Decimal("0.00"),
            )
            actual_balance = sum(
                (parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00"))) for month_point in quarter_months),
                Decimal("0.00"),
            )
            planned_expense = sum(
                (parse_decimal(getattr(month_point, "planned_expense", Decimal("0.00"))) for month_point in quarter_months),
                Decimal("0.00"),
            )
            actual_expense = sum(
                (parse_decimal(getattr(month_point, "actual_expense", Decimal("0.00"))) for month_point in quarter_months),
                Decimal("0.00"),
            )
            pending_amount = sum(
                (parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00"))) for month_point in quarter_months),
                Decimal("0.00"),
            )
            month_start = quarter_index * 3 + 1
            month_end = month_start + len(quarter_months) - 1
            status_text, tone = self._annual_quarter_status(actual_balance, pending_amount)
            widgets["status"].setText(status_text)
            widgets["status"].set_tone(tone)
            widgets["planned"].setText(f"计划结余 {format_money(planned_balance)}")
            widgets["actual"].setText(f"实际结余 {format_money(actual_balance)}")
            if pending_amount > Decimal("0.00"):
                widgets["note"].setText(f"{month_start}-{month_end}月 · 待确认 {format_money(pending_amount)}，适合先回查本季度流水。")
                focus_labels.append(f"Q{quarter_index + 1}")
            elif actual_balance < Decimal("0.00"):
                widgets["note"].setText(
                    f"{month_start}-{month_end}月 · 支出 {format_money(actual_expense)} / {format_money(planned_expense)}，这个季度已经出现结余压力。"
                )
                focus_labels.append(f"Q{quarter_index + 1}")
            else:
                widgets["note"].setText(
                    f"{month_start}-{month_end}月 · 支出 {format_money(actual_expense)} / {format_money(planned_expense)}，季度节奏整体平稳。"
                )
        if focus_labels:
            joined_labels = "、".join(focus_labels)
            self.annual_overview_summary.setText(
                f"{joined_labels} 需要先看季度合计，再顺着 1-12 月检查预期 / 实际和待确认；主表已经把季度放在月度前面。"
            )
            self.annual_sheet_focus_label.setText(
                f"优先回看 {joined_labels}，再按月份查看差额和待确认金额，读法会更接近手工全年预算大表。"
            )
        else:
            self.annual_overview_summary.setText(
                "先看季度合计，再顺着 1-12 月读每个月的预期 / 实际；主表已经把全年十二月整理成手工预算大表的阅读节奏。"
            )
            self.annual_sheet_focus_label.setText(
                "季度先收口，月度再回看；主表保留待确认和压力月份，方便像手工全年预算大表那样顺着读。"
            )

    def _annual_quarter_status(self, actual_balance: Decimal, pending_amount: Decimal) -> tuple[str, str]:
        if pending_amount > Decimal("0.00"):
            return "待确认", "amber"
        if actual_balance < Decimal("0.00"):
            return "回看", "red"
        return "平稳", "green"

    def _annual_quarter_brush(self, month_points: list) -> QBrush:
        pending_amount = sum(
            (parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00"))) for month_point in month_points),
            Decimal("0.00"),
        )
        actual_balance = sum(
            (parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00"))) for month_point in month_points),
            Decimal("0.00"),
        )
        if pending_amount > Decimal("0.00"):
            return QBrush(QColor("#9d6d16"))
        if actual_balance < Decimal("0.00"):
            return QBrush(QColor("#bd3650"))
        return QBrush(QColor("#1f3b73"))

    def _annual_quarter_tooltip(self, month_points: list) -> str:
        pending_amount = sum(
            (parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00"))) for month_point in month_points),
            Decimal("0.00"),
        )
        actual_balance = sum(
            (parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00"))) for month_point in month_points),
            Decimal("0.00"),
        )
        if pending_amount > Decimal("0.00"):
            return "这个季度还有待确认金额，适合先核对季度合计，再顺着月份回看。"
        if actual_balance < Decimal("0.00"):
            return "这个季度实际结余为负，适合先看季度合计，再逐月定位压力。"
        return "季度合计先收口，再顺着月份查看预期、实际和待确认。"

    def _annual_month_label_brush(self, month_point) -> QBrush:
        if month_point is None:
            return QBrush(QColor("#5f6f8c"))
        if parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00"))) > Decimal("0.00"):
            return QBrush(QColor("#9d6d16"))
        if parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00"))) < Decimal("0.00"):
            return QBrush(QColor("#bd3650"))
        return QBrush(QColor("#5f6f8c"))

    def _annual_month_tooltip(self, month_point) -> str:
        if month_point is None:
            return "按月查看预期、实际和待确认。"
        pending_amount = parse_decimal(getattr(month_point, "pending_amount", Decimal("0.00")))
        actual_balance = parse_decimal(getattr(month_point, "actual_balance", Decimal("0.00")))
        if pending_amount > Decimal("0.00"):
            return "这个月还有待确认金额，主表里单独保留提醒。"
        if actual_balance < Decimal("0.00"):
            return "这个月实际结余为负，适合回头查看明细原因。"
        return "按月查看预期、实际和待确认。"

    def _load_annual_detail_table(self, annual_matrix) -> None:
        all_rows = list(getattr(annual_matrix, "detail_rows", []) or [])
        rows = self._filtered_annual_detail_rows(all_rows)
        self.annual_detail_table.clearSpans()
        self.annual_detail_table.setRowCount(0)
        current_group = ""
        for detail_row in rows:
            group_name = (getattr(detail_row, "group_name", "") or "其他预算项").strip()
            if group_name != current_group:
                current_group = group_name
                self._append_group_row(self.annual_detail_table, current_group)
            self._append_annual_detail_row(
                self.annual_detail_table,
                detail_row,
                getattr(annual_matrix, "year", None),
            )
        if not all_rows:
            self._append_empty_row(self.annual_detail_table, "年度明细会在预算项和标签统计准备好后显示。")
        elif not rows:
            self._append_empty_row(self.annual_detail_table, "没有符合筛选的年度明细，点“显示全部”看看完整清单。")
        self._apply_annual_detail_header_colors()
        sync_table_columns(self.annual_detail_table)
        self.annual_detail_table.resizeRowsToContents()

    def _apply_annual_detail_filters(self, *_args) -> None:
        if self._annual_matrix is None:
            return
        self._load_annual_detail_table(self._annual_matrix)

    def _clear_annual_detail_filters(self) -> None:
        self.annual_detail_kind_filter_combo.blockSignals(True)
        self.annual_detail_tag_filter_combo.blockSignals(True)
        self.annual_detail_status_filter_combo.blockSignals(True)
        self.annual_detail_kind_filter_combo.setCurrentIndex(0)
        self.annual_detail_tag_filter_combo.setCurrentIndex(0)
        self.annual_detail_status_filter_combo.setCurrentIndex(0)
        self.annual_detail_kind_filter_combo.blockSignals(False)
        self.annual_detail_tag_filter_combo.blockSignals(False)
        self.annual_detail_status_filter_combo.blockSignals(False)
        self._annual_detail_quick_view = "全部"
        self._annual_detail_hide_single_month = False
        self.annual_detail_single_month_button.blockSignals(True)
        self.annual_detail_single_month_button.setChecked(False)
        self.annual_detail_single_month_button.blockSignals(False)
        self._sync_annual_detail_quick_view_buttons()
        self._apply_annual_detail_filters()

    def _set_annual_detail_quick_view(self, quick_view: str) -> None:
        self._annual_detail_quick_view = quick_view
        self._sync_annual_detail_quick_view_buttons()
        self._apply_annual_detail_filters()

    def _set_annual_detail_single_month_hidden(self, checked: bool) -> None:
        self._annual_detail_hide_single_month = checked
        self._apply_annual_detail_filters()

    def _sync_annual_detail_quick_view_buttons(self) -> None:
        active_view = self._annual_detail_quick_view
        for label, button in self.annual_detail_quick_view_buttons.items():
            button.blockSignals(True)
            button.setChecked(label == active_view)
            button.blockSignals(False)

    def _refresh_annual_detail_filters(self, detail_rows: list) -> None:
        kinds = sorted(
            {
                self._display_line_kind(getattr(row, "line_kind", "") or "")
                for row in detail_rows
                if getattr(row, "line_kind", "") or ""
            }
        )
        tags = sorted(
            {
                getattr(row, "category", "") or ""
                for row in detail_rows
                if getattr(row, "category", "") or ""
            }
        )
        statuses = sorted(
            {
                getattr(row, "status", "") or ""
                for row in detail_rows
                if getattr(row, "status", "") or ""
            }
        )
        self._refresh_combo_options(self.annual_detail_kind_filter_combo, "全部类型", kinds)
        self._refresh_combo_options(self.annual_detail_tag_filter_combo, "全部标签", tags)
        self._refresh_combo_options(self.annual_detail_status_filter_combo, "全部状态", statuses)

    def _refresh_combo_options(self, combo: QComboBox, default_label: str, options: list[str]) -> None:
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(default_label)
        combo.addItems(options)
        if current:
            index = combo.findText(current)
            combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _filtered_annual_detail_rows(self, rows: list) -> list:
        kind_filter = self.annual_detail_kind_filter_combo.currentText().strip()
        tag_filter = self.annual_detail_tag_filter_combo.currentText().strip()
        status_filter = self.annual_detail_status_filter_combo.currentText().strip()
        quick_view = self._annual_detail_quick_view
        filtered_rows = []
        for row in rows:
            line_kind = self._display_line_kind(getattr(row, "line_kind", "") or "")
            category = getattr(row, "category", "") or ""
            status = getattr(row, "status", "") or ""
            actual_total = parse_decimal(getattr(row, "actual_total", Decimal("0.00")))
            pending_total = parse_decimal(getattr(row, "pending_total", Decimal("0.00")))
            delta_total = parse_decimal(getattr(row, "delta_total", Decimal("0.00")))
            normalized_kind = self._stored_line_kind(getattr(row, "line_kind", "") or "")
            if kind_filter and kind_filter != "全部类型" and line_kind != kind_filter:
                continue
            if tag_filter and tag_filter != "全部标签" and category != tag_filter:
                continue
            if status_filter and status_filter != "全部状态" and status != status_filter:
                continue
            if quick_view == "有实际" and actual_total <= Decimal("0.00") and pending_total <= Decimal("0.00"):
                continue
            if quick_view == "超支" and status != "超支" and not (
                normalized_kind != "收入" and delta_total < Decimal("0.00")
            ):
                continue
            if quick_view == "未设预算" and status != "未设预算":
                continue
            if self._annual_detail_hide_single_month and self._is_single_month_annual_detail_row(row):
                continue
            filtered_rows.append(row)
        return filtered_rows

    def _is_single_month_annual_detail_row(self, detail_row) -> bool:
        active_month_count = 0
        for month in range(1, 13):
            if any(
                self._annual_month_has_value(detail_row, field_name, month)
                for field_name in ("planned_months", "actual_months", "pending_months")
            ):
                active_month_count += 1
                if active_month_count > 1:
                    return False
        return active_month_count == 1

    def _annual_month_has_value(self, detail_row, field_name: str, month: int) -> bool:
        month_values = getattr(detail_row, field_name, {}) or {}
        if isinstance(month_values, dict):
            keys = [f"{month:02d}", str(month), month]
            year = getattr(self._annual_matrix, "year", None)
            if year:
                keys.insert(0, f"{year:04d}-{month:02d}")
            for key in keys:
                if key in month_values and parse_decimal(month_values[key]) != Decimal("0.00"):
                    return True
            return False
        if isinstance(month_values, (list, tuple)) and len(month_values) >= month:
            return parse_decimal(month_values[month - 1]) != Decimal("0.00")
        return False

    def _annual_detail_effective_in_month(self, detail_row, month_key: str) -> bool:
        start_month = (getattr(detail_row, "effective_start_month", "") or "").strip()
        end_month = (getattr(detail_row, "effective_end_month", "") or "").strip()
        if start_month and month_key < start_month:
            return False
        if end_month and month_key > end_month:
            return False
        return True

    def _append_annual_detail_row(self, table: QTableWidget, detail_row, year: int | None) -> None:
        row = table.rowCount()
        table.insertRow(row)
        line_kind = getattr(detail_row, "line_kind", "") or ""
        delta_total = parse_decimal(getattr(detail_row, "delta_total", Decimal("0.00")))
        values = [
            getattr(detail_row, "name", "") or "",
            self._display_line_kind(line_kind),
            getattr(detail_row, "category", "") or "",
            self._effective_text(
                getattr(detail_row, "effective_start_month", "") or "",
                getattr(detail_row, "effective_end_month", "") or "",
            ),
        ]
        for month in range(1, 13):
            month_key = f"{year:04d}-{month:02d}" if year else f"{month:02d}"
            values.extend(
                [
                    format_money(self._annual_month_value(detail_row, "planned_months", month_key, month)),
                    format_money(self._annual_month_value(detail_row, "actual_months", month_key, month)),
                ]
            )
        values.extend(
            [
                format_money(getattr(detail_row, "planned_total", Decimal("0.00"))),
                format_money(getattr(detail_row, "actual_total", Decimal("0.00"))),
                format_money(getattr(detail_row, "pending_total", Decimal("0.00"))),
                self._format_signed_money(delta_total),
                getattr(detail_row, "status", "") or "",
            ]
        )
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            if 4 <= column_index <= 31:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if 4 <= column_index <= 27:
                month = ((column_index - 4) // 2) + 1
                month_palette = self._annual_month_palette(month)
                item.setBackground(QColor(month_palette["detail_cell"]))
                if ((column_index - 4) // 2) in {0, 3, 6, 9}:
                    item.setBackground(QColor(month_palette["detail_boundary"]))
            if column_index == 31:
                item.setForeground(self._annual_detail_delta_brush(line_kind, delta_total))
                item.setToolTip(self._annual_detail_delta_tooltip(line_kind))
            elif column_index == 32:
                item.setForeground(self._status_brush(getattr(detail_row, "status", "") or ""))
            table.setItem(row, column_index, item)

    def _annual_month_value(self, detail_row, field_name: str, month_key: str, month: int):
        month_values = getattr(detail_row, field_name, None)
        if isinstance(month_values, dict):
            for key in (month_key, month_key[-2:], str(month), month):
                if key in month_values:
                    return month_values[key]
            return Decimal("0.00")
        if isinstance(month_values, (list, tuple)) and len(month_values) >= month:
            return month_values[month - 1]
        return Decimal("0.00")

    def _refresh_tag_filter(self, rows: list) -> None:
        current = self.tag_filter_combo.currentText()
        tags = sorted({row.category for row in rows if row.category})
        self.tag_filter_combo.blockSignals(True)
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("全部标签")
        self.tag_filter_combo.addItems(tags)
        if current:
            index = self.tag_filter_combo.findText(current)
            self.tag_filter_combo.setCurrentIndex(index if index >= 0 else 0)
        self.tag_filter_combo.blockSignals(False)

    def _filtered_rows(self, rows: list) -> list:
        tag = self.tag_filter_combo.currentText().strip()
        if not tag or tag == "全部标签":
            return list(rows)
        return [row for row in rows if row.category == tag]

    def _load_table(self, table: QTableWidget, rows: list, empty_text: str) -> None:
        table.clearSpans()
        table.setRowCount(0)
        current_group = ""
        for comparison_row in rows:
            if comparison_row.group_name != current_group:
                current_group = comparison_row.group_name
                self._append_group_row(table, current_group)
            self._append_comparison_row(table, comparison_row)
        if not rows:
            self._append_empty_row(table, empty_text)
        sync_table_columns(table)
        table.resizeRowsToContents()

    def _append_group_row(self, table: QTableWidget, group_name: str) -> None:
        row = table.rowCount()
        table.insertRow(row)
        item = QTableWidgetItem(f"  {group_name}")
        item.setData(Qt.ItemDataRole.UserRole, {"is_group": True})
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setBackground(QColor("#f4f7fb"))
        item.setForeground(QBrush(QColor("#5f6f8c")))
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, 0, item)
        table.setSpan(row, 0, 1, table.columnCount())

    def _append_empty_row(self, table: QTableWidget, empty_text: str) -> None:
        row = table.rowCount()
        table.insertRow(row)
        item = QTableWidgetItem(empty_text)
        item.setData(Qt.ItemDataRole.UserRole, {"is_group": True})
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setForeground(QBrush(QColor("#7a89a6")))
        table.setItem(row, 0, item)
        table.setSpan(row, 0, 1, table.columnCount())

    def _append_comparison_row(self, table: QTableWidget, comparison_row) -> None:
        row = table.rowCount()
        table.insertRow(row)
        progress = ""
        if comparison_row.planned_amount > Decimal("0.00"):
            progress = f"{(comparison_row.progress_ratio * Decimal('100')).quantize(Decimal('0.1'))}%"
        notes = self._one_line_note(comparison_row.notes)
        values = [
            comparison_row.name,
            self._display_line_kind(comparison_row.line_kind),
            comparison_row.category,
            notes,
            self._effective_text(comparison_row.effective_start_month, comparison_row.effective_end_month),
            format_money(comparison_row.planned_amount),
            format_money(comparison_row.actual_amount),
            format_money(comparison_row.pending_amount),
            self._format_signed_money(comparison_row.delta_amount),
            progress,
            comparison_row.status,
        ]
        payload = {
            "is_group": False,
            "line_id": comparison_row.line_id,
            "line_kind": comparison_row.line_kind,
            "name": comparison_row.name,
            "category": comparison_row.category,
            "notes": comparison_row.notes,
            "effective_start_month": comparison_row.effective_start_month,
            "effective_end_month": comparison_row.effective_end_month,
            "suggested_amount": f"{parse_decimal(comparison_row.actual_amount):.2f}",
            "status": comparison_row.status,
        }
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column_index == 0:
                item.setData(Qt.ItemDataRole.UserRole, payload)
            if column_index == 3 and comparison_row.notes:
                item.setToolTip(comparison_row.notes)
            if column_index in {5, 6, 7, 8, 9}:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if column_index == 10:
                item.setForeground(self._status_brush(comparison_row.status))
            table.setItem(row, column_index, item)

    def _handle_selection_changed(self, table: QTableWidget) -> None:
        if table is self.comparison_table and self.comparison_table.hasFocus():
            self.income_table.clearSelection()
            self.expense_table.clearSelection()
        elif table is self.income_table and self.income_table.hasFocus():
            self.comparison_table.clearSelection()
            self.expense_table.clearSelection()
        elif table is self.expense_table and self.expense_table.hasFocus():
            self.comparison_table.clearSelection()
            self.income_table.clearSelection()
        if not table.selectedItems():
            return
        row = table.currentRow()
        if row < 0:
            return
        item = table.item(row, 0)
        if item is None:
            return
        payload = item.data(Qt.ItemDataRole.UserRole)
        if not payload or payload.get("is_group"):
            return
        line_id = payload.get("line_id", "")
        if not line_id:
            self._prefill_unbudgeted_line(payload)
            return
        line = next((value for value in self._budget_lines if value.id == line_id), None)
        if line is None:
            return
        self._current_line_id = line.id
        line_meta = [self._display_line_kind(line.line_kind)]
        if line.category:
            line_meta.append(line.category)
        line_meta.append(self._effective_text(line.effective_start_month, line.effective_end_month))
        self.editor_context_label.setText(f"编辑：{line.name}")
        self.editor_hint_label.setText(" · ".join(part for part in line_meta if part))
        self.kind_combo.setCurrentText(self._display_line_kind(line.line_kind))
        self.name_edit.setText(line.name)
        self.category_edit.setText(line.category)
        self.planned_amount_edit.setText(line.planned_amount)
        self._set_effective_mode_for_line(line.effective_start_month, line.effective_end_month)
        self.day_spin.setValue(line.day_of_month or 0)
        self.required_checkbox.setChecked(line.is_required)
        self.reminder_days_spin.setValue(line.reminder_days)
        self.notes_edit.setPlainText(line.notes)
        self.delete_line_button.setEnabled(True)

    def _prefill_unbudgeted_line(self, payload: dict) -> None:
        self._current_line_id = ""
        self.editor_context_label.setText(f"从实际预填：{payload.get('name', '新预算项')}")
        self.editor_hint_label.setText("已带入标签、生效月份和建议金额；补齐预算口径与备注后就能直接保存。")
        self.kind_combo.setCurrentText(self._display_line_kind(payload.get("line_kind") or "分类预算"))
        self.name_edit.setText(payload.get("name", ""))
        self.category_edit.setText(payload.get("category", ""))
        self.planned_amount_edit.setText(payload.get("suggested_amount", ""))
        self._set_effective_range(payload.get("effective_start_month") or self._current_month_key, payload.get("effective_end_month") or self._current_month_key)
        self.effective_mode_combo.setCurrentText("仅当前月")
        self._sync_effective_controls()
        self.day_spin.setValue(0)
        self.required_checkbox.setChecked(False)
        self.reminder_days_spin.setValue(0)
        self.notes_edit.setPlainText(payload.get("notes") or "草稿待调整\n来源：未设预算但本月有实际")
        self.delete_line_button.setEnabled(False)

    def _emit_month_changed(self, *_args) -> None:
        if self._loading:
            return
        self.budget_month_changed.emit(self.month_edit.date().toString("yyyy-MM"))

    def _emit_budget_save(self) -> None:
        total_budget = "0.00"
        if self._comparison is not None:
            total_budget = f"{parse_decimal(self._comparison.summary.planned_expense):.2f}"
        self.budget_save_requested.emit(
            {
                "month_key": self.month_edit.date().toString("yyyy-MM"),
                "total_budget": total_budget,
                "notes": self.budget_notes_edit.text().strip(),
            }
        )

    def _emit_budget_seed(self) -> None:
        self.budget_seed_requested.emit(self.month_edit.date().toString("yyyy-MM"))

    def _emit_budget_line_save(self) -> None:
        self.budget_line_save_requested.emit(
            {
                "line_id": self._current_line_id,
                "month_key": self.month_edit.date().toString("yyyy-MM"),
                "line_kind": self._stored_line_kind(self.kind_combo.currentText().strip()),
                "name": self.name_edit.text().strip(),
                "category": self.category_edit.text().strip(),
                "planned_amount": self.planned_amount_edit.text().strip(),
                "effective_start_month": self._effective_start_month(),
                "effective_end_month": self._effective_end_month(),
                "day_of_month": self.day_spin.value() or None,
                "is_required": self.required_checkbox.isChecked(),
                "reminder_days": self.reminder_days_spin.value(),
                "notes": self.notes_edit.toPlainText().strip(),
            }
        )

    def _emit_budget_line_delete(self) -> None:
        if self._current_line_id:
            self.budget_line_delete_requested.emit(self._current_line_id)

    def _effective_start_month(self) -> str:
        mode = self.effective_mode_combo.currentText().strip()
        if mode == "仅当前月":
            return self._current_month_key
        return self.effective_start_edit.date().toString("yyyy-MM")

    def _effective_end_month(self) -> str:
        mode = self.effective_mode_combo.currentText().strip()
        if mode == "仅当前月":
            return self._current_month_key
        if mode == "从当前月起":
            return ""
        return self.effective_end_edit.date().toString("yyyy-MM")

    def _set_effective_mode_for_line(self, start_month: str, end_month: str) -> None:
        start = start_month or self._current_month_key
        self._set_effective_range(start, end_month or start)
        if start == self._current_month_key and end_month == self._current_month_key:
            self.effective_mode_combo.setCurrentText("仅当前月")
        elif not end_month:
            self.effective_mode_combo.setCurrentText("从当前月起")
        else:
            self.effective_mode_combo.setCurrentText("指定月份范围")
        self._sync_effective_controls()

    def _set_effective_range(self, start_month: str, end_month: str) -> None:
        start = QDate.fromString(f"{start_month}-01", "yyyy-MM-dd")
        end = QDate.fromString(f"{end_month}-01", "yyyy-MM-dd")
        current = QDate.fromString(f"{self._current_month_key}-01", "yyyy-MM-dd")
        self.effective_start_edit.setDate(start if start.isValid() else current)
        self.effective_end_edit.setDate(end if end.isValid() else current)

    def _sync_effective_controls(self, *_args) -> None:
        mode = self.effective_mode_combo.currentText().strip()
        if mode == "仅当前月":
            self._set_effective_range(self._current_month_key, self._current_month_key)
            self.effective_start_edit.setEnabled(False)
            self.effective_end_edit.setEnabled(False)
        elif mode == "从当前月起":
            self.effective_start_edit.setEnabled(True)
            self.effective_end_edit.setEnabled(False)
        else:
            self.effective_start_edit.setEnabled(True)
            self.effective_end_edit.setEnabled(True)
        self._sync_effective_scope_table()
        self._sync_effective_mode_hint()

    def _sync_effective_mode_hint(self) -> None:
        mode = self.effective_mode_combo.currentText().strip()
        hint_by_mode = {
            "仅当前月": "当前生效方式：仅当前月，适合活动、一次性购买或当月临时预算。",
            "从当前月起": "当前生效方式：从当前月起，适合房租、话费、会员和长期储蓄计划。",
            "指定月份范围": "当前生效方式：指定月份范围，适合课程、阶段性计划或短周期专项预算。",
        }
        self.effective_mode_hint_label.setText(hint_by_mode.get(mode, "根据预算口径选择对应的生效方式。"))

    def _effective_text(self, start_month: str, end_month: str) -> str:
        start = start_month or self._current_month_key
        if not end_month:
            return f"{start} 起"
        if start == end_month:
            return start
        return f"{start} 至 {end_month}"

    def _format_signed_money(self, value) -> str:
        amount = parse_decimal(value)
        prefix = "+" if amount > Decimal("0.00") else ""
        return f"{prefix}{format_money(amount)}"

    def _annual_detail_delta_brush(self, line_kind: str, delta_total: Decimal) -> QBrush:
        amount = parse_decimal(delta_total)
        if amount == Decimal("0.00"):
            return QBrush(QColor("#66758f"))
        normalized_kind = self._stored_line_kind(line_kind)
        if normalized_kind == "收入":
            return QBrush(QColor("#1f7d5b")) if amount > 0 else QBrush(QColor("#bd3650"))
        if normalized_kind in {"分类预算", "固定支出", "储蓄计划", "支出"}:
            return QBrush(QColor("#1f7d5b")) if amount > 0 else QBrush(QColor("#bd3650"))
        return QBrush(QColor("#1f7d5b")) if amount > 0 else QBrush(QColor("#bd3650"))

    def _annual_detail_delta_tooltip(self, line_kind: str) -> str:
        normalized_kind = self._stored_line_kind(line_kind)
        if normalized_kind == "收入":
            return "差额口径：实际收入 - 预期收入。正数表示高于预期，负数表示低于预期。"
        if normalized_kind in {"分类预算", "固定支出", "储蓄计划", "支出"}:
            return "差额口径：预期支出 - 实际支出。正数表示仍有余额，负数表示已经超支。"
        return "差额口径沿用年度明细口径。"

    def _display_line_kind(self, line_kind: str) -> str:
        return "标签预算" if line_kind == "分类预算" else line_kind

    def _stored_line_kind(self, line_kind: str) -> str:
        return "分类预算" if line_kind == "标签预算" else line_kind

    def _one_line_note(self, notes: str) -> str:
        return "；".join(part.strip() for part in notes.splitlines() if part.strip())

    def _annual_quarter_palette(self, quarter_number: int) -> dict[str, str | tuple[str, ...]]:
        quarter_index = max(1, min(4, quarter_number)) - 1
        return ANNUAL_QUARTER_PALETTES[quarter_index]

    def _annual_month_palette(self, month: int) -> dict[str, str]:
        month_index = max(1, min(12, month)) - 1
        quarter_palette = self._annual_quarter_palette(month_index // 3 + 1)
        month_offset = month_index % 3
        return {
            "quarter": quarter_palette["quarter"],
            "month_row": quarter_palette["month_rows"][month_offset],
            "sheet_header": quarter_palette["sheet_headers"][month_offset],
            "sheet_cell": quarter_palette["sheet_cells"][month_offset],
            "detail_header": quarter_palette["detail_headers"][month_offset],
            "detail_cell": quarter_palette["detail_cells"][month_offset],
            "detail_boundary": quarter_palette["detail_boundary"],
        }

    def _apply_annual_sheet_header_colors(self) -> None:
        corner_item = self.annual_sheet_table.horizontalHeaderItem(0)
        if corner_item is not None:
            corner_item.setBackground(QColor("#f4f8ff"))
            corner_item.setForeground(QBrush(QColor("#5f6f8c")))
        for month in range(1, 13):
            month_palette = self._annual_month_palette(month)
            for column in (month * 2 - 1, month * 2):
                header_item = self.annual_sheet_table.horizontalHeaderItem(column)
                if header_item is None:
                    continue
                header_item.setBackground(QColor(month_palette["sheet_header"]))
                header_item.setForeground(QBrush(QColor("#556884")))

    def _apply_annual_detail_header_colors(self) -> None:
        neutral_columns = (0, 1, 2, 3, 28, 29, 30, 31, 32)
        for column in neutral_columns:
            header_item = self.annual_detail_table.horizontalHeaderItem(column)
            if header_item is None:
                continue
            header_item.setBackground(QColor("#f7faff"))
            header_item.setForeground(QBrush(QColor("#5f6f8c")))
        for month in range(1, 13):
            month_palette = self._annual_month_palette(month)
            start_column = 4 + (month - 1) * 2
            for column in (start_column, start_column + 1):
                header_item = self.annual_detail_table.horizontalHeaderItem(column)
                if header_item is None:
                    continue
                header_item.setBackground(QColor(month_palette["detail_header"]))
                header_item.setForeground(QBrush(QColor("#556884")))

    def _status_brush(self, status: str) -> QBrush:
        if status in {"已达成", "进行中", "未发生"}:
            return QBrush(QColor("#1f7d5b"))
        if status in {"临界", "有待确认", "草稿待调整", "未设预算"}:
            return QBrush(QColor("#9d6d16"))
        if status == "超支":
            return QBrush(QColor("#bd3650"))
        return QBrush(QColor("#66758f"))
