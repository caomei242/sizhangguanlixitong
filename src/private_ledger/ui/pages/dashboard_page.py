from __future__ import annotations

from PySide6.QtCharts import QBarCategoryAxis, QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsLineItem,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from private_ledger.domain.ledger import format_money
from private_ledger.domain.models import MonthlyTrendPoint
from private_ledger.ui.widgets import create_card, prepare_table, sync_table_columns, MetricCard


class PeriodTrendChart(QChartView):
    def __init__(self) -> None:
        self.chart = QChart()
        super().__init__(self.chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMouseTracking(True)
        self.setMinimumHeight(360)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWidth(0)
        self.setStyleSheet("QChartView { background: #f7f9fc; border: none; }")
        self.setAutoFillBackground(True)
        self.viewport().setAutoFillBackground(True)
        self.viewport().setStyleSheet("background: transparent; border: none;")
        self.chart.legend().setVisible(True)
        self.chart.setBackgroundVisible(True)
        self.chart.setBackgroundBrush(QColor("#f7f9fc"))
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.setPlotAreaBackgroundBrush(QColor(255, 255, 255, 0))
        self.chart.setPlotAreaBackgroundPen(QPen(QColor(255, 255, 255, 0), 0))
        self._points: list[MonthlyTrendPoint] = []
        self._trend_granularity = "month"
        hover_pen = QPen(QColor("#8b99b1"), 1.2)
        hover_pen.setStyle(Qt.PenStyle.DashLine)
        self._hover_line = QGraphicsLineItem(self.chart)
        self._hover_line.setPen(hover_pen)
        self._hover_line.setZValue(20)
        self._hover_line.hide()

    def load_points(self, points: list[MonthlyTrendPoint], trend_granularity: str = "month") -> None:
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        self._points = points
        self._trend_granularity = trend_granularity
        self._hide_hover_line()
        if not points:
            self.chart.setTitle("当前范围暂无已确认流水")
            return

        is_daily_trend = trend_granularity == "day"
        self.chart.setTitle("按日趋势" if is_daily_trend else "按月趋势")
        series_specs = [
            ("收入", [point.income for point in points], QColor("#1f9f72")),
            ("支出", [point.expense for point in points], QColor("#3f67d9")),
            ("结余", [point.balance for point in points], QColor("#e24b64")),
        ]
        if any(float(getattr(point, "pending_amount", 0) or 0) for point in points):
            series_specs.append(
                ("待确认", [getattr(point, "pending_amount", 0) for point in points], QColor("#d9901f"))
            )
        values = []
        for name, amounts, color in series_specs:
            series = QLineSeries()
            series.setName(name)
            series.setPen(QPen(color, 2.4))
            for index, amount in enumerate(amounts):
                value = float(amount)
                series.append(index, value)
                values.append(value)
            self.chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append([
            point.label or (f"{int(point.month_key[-2:])}日" if is_daily_trend else f"{int(point.month_key[5:7])}月")
            for point in points
        ])
        axis_x.setTitleText("日期" if is_daily_trend else "月份")

        minimum = min(values) if values else 0
        maximum = max(values) if values else 0
        padding = max(100.0, (maximum - minimum) * 0.12)
        axis_y = QValueAxis()
        axis_y.setRange(minimum - padding, maximum + padding)
        axis_y.setLabelFormat("%.0f")
        axis_y.setTitleText("金额")

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in self.chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

    def series_count_for_test(self) -> int:
        return len(self.chart.series())

    def hover_summary_for_test(self, index: int) -> str:
        return self._hover_summary(index)

    def _nearest_point_index(self, x: float) -> int | None:
        if not self._points:
            return None
        plot_area = self.chart.plotArea()
        if not plot_area.contains(x, plot_area.center().y()):
            return None
        if len(self._points) == 1:
            return 0
        ratio = (x - plot_area.left()) / max(1.0, plot_area.width())
        return max(0, min(len(self._points) - 1, round(ratio * (len(self._points) - 1))))

    def _hover_x_for_index(self, index: int) -> float:
        plot_area = self.chart.plotArea()
        if len(self._points) <= 1:
            return plot_area.center().x()
        step = plot_area.width() / max(1, len(self._points) - 1)
        return plot_area.left() + index * step

    def _hover_summary(self, index: int) -> str:
        point = self._points[index]
        label = point.label or point.month_key
        return "\n".join(
            [
                label,
                f"收入：{format_money(point.income)}",
                f"支出：{format_money(point.expense)}",
                f"结余：{format_money(point.balance)}",
                f"待确认：{format_money(getattr(point, 'pending_amount', '0.00'))}",
            ]
        )

    def _show_hover_line(self, index: int) -> None:
        plot_area = self.chart.plotArea()
        x = self._hover_x_for_index(index)
        self._hover_line.setLine(x, plot_area.top(), x, plot_area.bottom())
        self._hover_line.show()

    def _hide_hover_line(self) -> None:
        self._hover_line.hide()
        QToolTip.hideText()

    def mouseMoveEvent(self, event) -> None:  # noqa: ANN001
        position = event.position()
        plot_area = self.chart.plotArea()
        if not plot_area.contains(position):
            self._hide_hover_line()
            super().mouseMoveEvent(event)
            return
        index = self._nearest_point_index(position.x())
        if index is None:
            self._hide_hover_line()
            super().mouseMoveEvent(event)
            return
        self._show_hover_line(index)
        QToolTip.showText(event.globalPosition().toPoint(), self._hover_summary(index), self)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._hide_hover_line()
        super().leaveEvent(event)


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.total_budget_card = MetricCard("本月预算")
        self.actual_expense_card = MetricCard("已确认支出")
        self.remaining_budget_card = MetricCard("剩余预算")
        self.pending_amount_card = MetricCard("待确认金额")
        self.income_card = MetricCard("收入")
        self.expense_card = MetricCard("支出")
        self.balance_card = MetricCard("结余")
        self.period_pending_amount_card = MetricCard("待确认")
        self.trend_chart = PeriodTrendChart()
        self.trend_table = QTableWidget()

        self.tabs = QTabWidget()
        self.tabs.setProperty("sectionRole", "workspace-tabs")
        self.overview_tab = QWidget()
        self.accounts_tab = QWidget()
        self.reminders_tab = QWidget()
        self.transactions_tab = QWidget()

        self.overview_reminders_list = QListWidget()
        self.overview_pending_list = QListWidget()
        self.overview_accounts_table = QTableWidget()
        self.overview_transactions_table = QTableWidget()

        self.accounts_table = QTableWidget()
        self.reminders_table = QTableWidget()
        self.transactions_table = QTableWidget()
        self.pending_list = QListWidget()

        prepare_table(self.trend_table, ["月份", "收入", "支出", "结余", "待确认"])
        prepare_table(self.overview_accounts_table, ["账户", "当前余额", "状态"])
        prepare_table(self.overview_transactions_table, ["日期", "标签", "状态", "金额"])
        prepare_table(self.accounts_table, ["账户", "类型", "用途", "当前余额", "状态"])
        prepare_table(self.reminders_table, ["提醒", "类型", "日期/阈值", "状态"])
        prepare_table(self.transactions_table, ["日期", "类型", "标签", "账户", "状态", "金额"])

        self._build_ui()

    def _tag_section(self, widget: QWidget, role: str, variant: str, density: str) -> None:
        widget.setProperty("sectionRole", role)
        widget.setProperty("cardVariant", variant)
        widget.setProperty("sectionDensity", density)

    def _tag_preview_widget(self, widget: QWidget, role: str, density: str) -> None:
        widget.setProperty("sectionRole", role)
        widget.setProperty("sectionDensity", density)

    def _build_ui(self) -> None:
        overview_layout = QVBoxLayout(self.overview_tab)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.setSpacing(14)

        self.month_metrics = QWidget()
        self._tag_section(self.month_metrics, "metric-strip", "summary-strip", "cozy")
        month_metrics_layout = QGridLayout(self.month_metrics)
        month_metrics_layout.setContentsMargins(0, 0, 0, 0)
        month_metrics_layout.setHorizontalSpacing(12)
        month_metrics_layout.setVerticalSpacing(12)
        for index, card in enumerate(
            (
                self.total_budget_card,
                self.actual_expense_card,
                self.remaining_budget_card,
                self.pending_amount_card,
            )
        ):
            month_metrics_layout.addWidget(card, 0, index)
        overview_layout.addWidget(self.month_metrics)

        self.period_cockpit = QWidget()
        self._tag_section(self.period_cockpit, "metric-strip", "summary-strip", "cozy")
        period_layout = QGridLayout(self.period_cockpit)
        period_layout.setContentsMargins(0, 0, 0, 0)
        period_layout.setHorizontalSpacing(12)
        period_layout.setVerticalSpacing(12)
        for index, card in enumerate(
            (
                self.income_card,
                self.expense_card,
                self.balance_card,
                self.period_pending_amount_card,
            )
        ):
            period_layout.addWidget(card, 0, index)
        overview_layout.addWidget(self.period_cockpit)
        self.period_cockpit.hide()

        overview_workspace = QWidget()
        self._tag_section(overview_workspace, "workspace-band", "workspace", "spacious")
        workspace_layout = QHBoxLayout(overview_workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(12)

        trend_card, trend_layout = create_card("收支趋势", "默认按日查看，切到季/年时自动按月汇总")
        self._tag_section(trend_card, "workspace-main", "workspace", "spacious")
        self._tag_preview_widget(self.trend_chart, "trend-canvas", "spacious")
        self.trend_chart.setMinimumHeight(390)
        trend_layout.addWidget(self.trend_chart)
        trend_layout.addWidget(self.trend_table)
        self.trend_table.hide()
        workspace_layout.addWidget(trend_card, 3)

        reminder_preview_card, reminder_preview_layout = create_card("近期待处理", "红黄绿灯、本地提示与预算关注项")
        self._tag_section(reminder_preview_card, "workspace-sidebar", "compact-preview", "compact")
        reminder_preview_label = QLabel("仅展示最近事项，便于快速扫一眼。")
        reminder_preview_label.setObjectName("MutedText")
        reminder_preview_label.setWordWrap(True)
        reminder_preview_layout.addWidget(reminder_preview_label)
        reminder_preview_layout.addWidget(self.overview_reminders_list)
        self.overview_reminders_list.setMaximumHeight(228)
        self.overview_reminders_list.setSpacing(4)
        workspace_layout.addWidget(reminder_preview_card, 2)
        overview_layout.addWidget(overview_workspace)

        detail_grid = QGridLayout()
        detail_grid.setContentsMargins(0, 0, 0, 0)
        detail_grid.setHorizontalSpacing(12)
        detail_grid.setVerticalSpacing(12)

        accounts_preview_card, accounts_preview_layout = create_card("账户余额概览", "最近快照 + 已确认流水净变化")
        self._tag_section(accounts_preview_card, "preview-panel", "preview-table", "compact")
        accounts_preview_note = QLabel("保留最近 5 条账户快照，作为查看入口。")
        accounts_preview_note.setObjectName("MutedText")
        accounts_preview_note.setWordWrap(True)
        accounts_preview_layout.addWidget(accounts_preview_note)
        accounts_preview_layout.addWidget(self.overview_accounts_table)
        self.overview_accounts_table.setMaximumHeight(220)
        detail_grid.addWidget(accounts_preview_card, 0, 0)

        transactions_preview_card, transactions_preview_layout = create_card("最近流水", "收入、支出、转账、充值、退款")
        self._tag_section(transactions_preview_card, "preview-panel", "preview-table", "compact")
        transactions_preview_note = QLabel("仅保留最近 5 条记录，方便快速复核。")
        transactions_preview_note.setObjectName("MutedText")
        transactions_preview_note.setWordWrap(True)
        transactions_preview_layout.addWidget(transactions_preview_note)
        transactions_preview_layout.addWidget(self.overview_transactions_table)
        self.overview_transactions_table.setMaximumHeight(220)
        detail_grid.addWidget(transactions_preview_card, 0, 1)

        pending_preview_card, pending_preview_layout = create_card("待确认事项", "不会混入正式统计")
        self._tag_section(pending_preview_card, "preview-panel", "preview-list", "compact")
        pending_preview_note = QLabel("待确认项只做提醒，不影响正式统计。")
        pending_preview_note.setObjectName("MutedText")
        pending_preview_note.setWordWrap(True)
        pending_preview_layout.addWidget(pending_preview_note)
        pending_preview_layout.addWidget(self.overview_pending_list)
        self.overview_pending_list.setMaximumHeight(180)
        self.overview_pending_list.setSpacing(4)
        detail_grid.addWidget(pending_preview_card, 1, 0, 1, 2)
        overview_layout.addLayout(detail_grid)

        accounts_layout = QVBoxLayout(self.accounts_tab)
        accounts_layout.setContentsMargins(0, 0, 0, 0)
        accounts_card, accounts_card_layout = create_card("账户余额概览", "最近快照 + 已确认流水净变化")
        accounts_card_layout.addWidget(self.accounts_table)
        accounts_layout.addWidget(accounts_card)

        reminders_layout = QVBoxLayout(self.reminders_tab)
        reminders_layout.setContentsMargins(0, 0, 0, 0)
        reminders_card, reminders_card_layout = create_card("近期待处理队列", "可以作为充值续费页入口")
        reminders_note = QLabel("红黄绿灯、本地提示和回查事项集中展示。")
        reminders_note.setObjectName("MutedText")
        reminders_note.setWordWrap(True)
        reminders_card_layout.addWidget(reminders_note)
        reminders_card_layout.addWidget(self.reminders_table)
        reminders_layout.addWidget(reminders_card)

        transactions_layout = QVBoxLayout(self.transactions_tab)
        transactions_layout.setContentsMargins(0, 0, 0, 0)
        transactions_card, transactions_card_layout = create_card("最近流水", "收入、支出、转账、充值、退款")
        transactions_card_layout.addWidget(self.transactions_table)
        pending_card, pending_layout = create_card("待确认事项", "不会混入正式统计")
        pending_layout.addWidget(self.pending_list)
        transactions_layout.addWidget(transactions_card)
        transactions_layout.addWidget(pending_card)

        self.tabs.addTab(self.overview_tab, "总览")
        self.tabs.addTab(self.accounts_tab, "账户余额")
        self.tabs.addTab(self.reminders_tab, "近期待处理")
        self.tabs.addTab(self.transactions_tab, "最近流水")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

    def load_snapshot(self, payload: dict) -> None:
        period_summary = payload.get("period_summary")
        trend_points = payload.get("trend_points", [])
        trend_granularity = payload.get("trend_granularity", "month")
        is_period_mode = payload.get("period_granularity") in {"quarter", "year"} and period_summary is not None
        self.month_metrics.setVisible(not is_period_mode)
        self.period_cockpit.setVisible(is_period_mode)

        summary = payload["summary"]
        if is_period_mode:
            balance_tone = "green" if period_summary.balance >= 0 else "red"
            self.income_card.set_content(
                format_money(period_summary.income),
                period_summary.label,
                f"{period_summary.transaction_count} 笔",
                "green",
            )
            self.expense_card.set_content(
                format_money(period_summary.expense),
                "已确认支出",
                "",
                "green",
            )
            self.balance_card.set_content(
                format_money(period_summary.balance),
                "收入 - 支出",
                "结余" if period_summary.balance >= 0 else "超支",
                balance_tone,
            )
            self.period_pending_amount_card.set_content(
                format_money(period_summary.pending_amount),
                "待确认，不计入趋势",
                f"{period_summary.pending_count} 笔",
                "amber" if period_summary.pending_amount > 0 else "gray",
            )
            self.pending_amount_card.set_content(
                format_money(period_summary.pending_amount),
                "待确认，不计入趋势",
                f"{period_summary.pending_count} 笔",
                "amber" if period_summary.pending_amount > 0 else "gray",
            )
        else:
            self.total_budget_card.set_content(
                format_money(summary.total_budget),
                "当月生效预算项自动合计",
                payload.get("budget_status", ""),
                "gray",
            )
            self.actual_expense_card.set_content(
                format_money(summary.actual_expense),
                "支出与退款净额",
                payload.get("expense_tag", ""),
                "green",
            )
            self.remaining_budget_card.set_content(
                format_money(summary.remaining_budget),
                "预算 - 已确认支出",
                payload.get("remaining_tag", ""),
                "green" if summary.remaining_budget >= 0 else "red",
            )
            self.pending_amount_card.set_content(
                format_money(summary.pending_amount),
                "不进入正式预算消耗",
                payload.get("pending_tag", ""),
                "amber" if summary.pending_amount > 0 else "gray",
            )

        self.trend_chart.load_points(trend_points, trend_granularity)
        self._load_trend_table(trend_points, trend_granularity)

        accounts = payload.get("accounts", [])
        self._load_accounts_table(self.accounts_table, accounts)
        self._load_accounts_preview(accounts)

        reminders = payload.get("reminders", [])
        self._load_reminders_table(reminders)
        self._load_reminder_preview(reminders)

        transactions = payload.get("transactions", [])
        self._load_transactions_table(transactions)
        self._load_transactions_preview(transactions)

        pending_items = payload.get("pending_items", [])
        self._load_pending_lists(pending_items)

    def _load_accounts_table(self, table: QTableWidget, accounts: list[dict]) -> None:
        table.setRowCount(len(accounts))
        for row_index, row in enumerate(accounts):
            values = [
                row["name"],
                row["account_type"],
                row["purpose"],
                row["balance_text"],
                row["status"],
            ]
            for column_index, value in enumerate(values):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(table)

    def _load_accounts_preview(self, accounts: list[dict]) -> None:
        rows = accounts[:5]
        self.overview_accounts_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [row["name"], row["balance_text"], row["status"]]
            for column_index, value in enumerate(values):
                self.overview_accounts_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.overview_accounts_table)

    def _load_reminders_table(self, reminders: list[dict]) -> None:
        self.reminders_table.setRowCount(len(reminders))
        for row_index, row in enumerate(reminders):
            values = [row["title"], row["target_type"], row["when_text"], row["display_status"]]
            for column_index, value in enumerate(values):
                self.reminders_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.reminders_table)

    def _load_reminder_preview(self, reminders: list[dict]) -> None:
        self.overview_reminders_list.clear()
        for row in reminders[:6]:
            self.overview_reminders_list.addItem(
                f"{row['title']} · {row['target_type']} · {row['display_status']} · {row['when_text']}"
            )

    def _load_transactions_table(self, transactions: list[dict]) -> None:
        self.transactions_table.setRowCount(len(transactions))
        for row_index, row in enumerate(transactions):
            values = [
                row["occurred_on"],
                row["transaction_type"],
                row["category"],
                row["account_text"],
                row["status"],
                row["amount_text"],
            ]
            for column_index, value in enumerate(values):
                self.transactions_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.transactions_table)

    def _load_transactions_preview(self, transactions: list[dict]) -> None:
        rows = transactions[:5]
        self.overview_transactions_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [row["occurred_on"], row["category"], row["status"], row["amount_text"]]
            for column_index, value in enumerate(values):
                self.overview_transactions_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.overview_transactions_table)

    def _load_pending_lists(self, pending_items: list[str]) -> None:
        self.pending_list.clear()
        self.overview_pending_list.clear()
        for item in pending_items:
            self.pending_list.addItem(item)
            self.overview_pending_list.addItem(item)

    def _load_trend_table(self, points: list[MonthlyTrendPoint], trend_granularity: str = "month") -> None:
        headers = ["日期" if trend_granularity == "day" else "月份", "收入", "支出", "结余", "待确认"]
        self.trend_table.setColumnCount(len(headers))
        self.trend_table.setHorizontalHeaderLabels(headers)
        self.trend_table.setRowCount(len(points))
        for row_index, point in enumerate(points):
            values = [
                point.label or point.month_key,
                format_money(point.income),
                format_money(point.expense),
                format_money(point.balance),
                format_money(getattr(point, "pending_amount", "0.00")),
            ]
            for column_index, value in enumerate(values):
                self.trend_table.setItem(row_index, column_index, QTableWidgetItem(value))
        sync_table_columns(self.trend_table)
