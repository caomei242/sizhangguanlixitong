from __future__ import annotations

APP_STYLESHEET = """
QWidget {
    color: #20304a;
    font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Microsoft YaHei", "Helvetica Neue";
    font-size: 14px;
}

QMainWindow {
    background: #e9eef5;
}

QFrame#WindowShell {
    background: #f4f7fb;
    border: 1px solid #d8e1ef;
    border-radius: 16px;
}

QFrame#WindowSidebar {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
    border-bottom-left-radius: 16px;
}

QFrame#WindowContentShell {
    background: #f6f8fc;
    border-top-right-radius: 16px;
    border-bottom-right-radius: 16px;
}

QFrame#ToolbarCard,
QFrame#SectionCard,
QFrame#ListPane,
QFrame#DetailPane,
QFrame#MetricCard,
QFrame#ReadonlyBox,
QFrame#StatusNote {
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid #dbe4f2;
    border-radius: 22px;
}

QFrame#SectionCardShell {
    background: transparent;
    border: none;
}

QFrame#ToolbarCard {
    background: rgba(255, 255, 255, 0.98);
}

QFrame#ToolbarCard[cardVariant="workspace"] {
    border-color: #d7e1f0;
}

QFrame#ToolbarCard[sectionRole="budget-workbench"] {
    background: #fcfdff;
    border-color: #d3ddeb;
    border-radius: 20px;
}

QFrame#SectionCard {
    background: rgba(255, 255, 255, 0.97);
}

QFrame#SectionCard[cardVariant="workspace"] {
    background: #ffffff;
    border-color: #d8e1ef;
}

QFrame#SectionCard[cardVariant="table"],
QFrame#ListPane {
    background: #fbfcff;
    border-color: #dbe4f2;
    border-radius: 20px;
}

QFrame#SectionCard[sectionDensity="compact"],
QFrame#ListPane[sectionDensity="compact"],
QFrame#DetailPane[sectionDensity="compact"] {
    border-radius: 18px;
}

QFrame#ListPane[sectionRole="stacked-list"] {
    background: #ffffff;
    border-color: #d6e0ef;
}

QFrame#SectionCard[sectionRole="budget-workbench-primary"] {
    background: #fcfdff;
    border-color: #d5dfef;
}

QFrame#SectionCard[sectionRole="budget-ledger"] {
    background: #fbfcff;
    border-color: #d7e1ef;
}

QFrame#SectionCard[sectionRole="annual-summary"] {
    background: #fcfdff;
    border-color: #d4deee;
}

QFrame#SectionCard[sectionRole="annual-detail"] {
    background: #fbfcff;
    border-color: #d8e1ef;
}

QFrame#SectionCard[sectionRole="scope-reference"] {
    background: #fcfdff;
    border-color: #dce5f2;
}

QWidget[sectionRole="metric-strip"] {
    background: transparent;
}

QWidget[sectionRole="workspace-band"] {
    background: transparent;
}

QFrame#SectionCard[sectionRole="workspace-main"],
QFrame#SectionCard[sectionRole="dashboard-trend"] {
    background: #fcfdff;
    border-color: #d2deef;
    border-radius: 22px;
}

QFrame#ListPane[sectionRole="workspace-sidebar"],
QFrame#ListPane[sectionRole="dashboard-reminders"] {
    background: #ffffff;
    border-color: #d9e3f1;
    border-radius: 22px;
}

QFrame#SectionCard[sectionRole="preview-panel"],
QFrame#SectionCard[sectionRole="dashboard-accounts"],
QFrame#SectionCard[sectionRole="dashboard-transactions"] {
    background: #fbfcff;
    border-color: #dbe4f2;
    border-radius: 20px;
}

QFrame#ListPane[sectionRole="preview-panel"],
QFrame#ListPane[sectionRole="dashboard-pending"] {
    background: #fbfcff;
    border-color: #dce5f3;
    border-radius: 20px;
}

QFrame#SectionCard[sectionRole="budget-month-switcher"] {
    background: #fcfdff;
    border-color: #d4dfef;
    border-radius: 18px;
}

QFrame#ToolbarCard[sectionRole="budget-workbench-shell"],
QFrame#SectionCard[sectionRole="budget-annual-overview"] {
    background: #fbfdff;
    border-color: #d2deee;
}

QFrame#SectionCard[sectionRole="budget-comparison-panel"],
QFrame#SectionCard[sectionRole="budget-income-panel"],
QFrame#SectionCard[sectionRole="budget-expense-panel"] {
    background: #fcfdff;
    border-color: #d8e1ef;
    border-radius: 20px;
}

QFrame#SectionCard[sectionRole="annual-read-guide"],
QFrame#SectionCard[sectionRole="annual-master-sheet"],
QFrame#SectionCard[sectionRole="annual-quarter-brief"],
QFrame#SectionCard[sectionRole="annual-quarter-summary"],
QFrame#SectionCard[sectionRole="annual-detail-panel"],
QFrame#SectionCard[sectionRole="budget-effective-scope"] {
    background: #fdfdff;
    border-color: #d8e2f0;
    border-radius: 20px;
}

QFrame#SectionCard[sectionRole="annual-accordion"] {
    background: #f8fbff;
    border-color: #d6e0ee;
    border-radius: 20px;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"] {
    background: #f7f9fd;
    border-color: #dfe6f1;
    border-radius: 20px;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"][quarterTone="q1"] {
    background: #f5f8fe;
    border-color: #d7e2f2;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"][quarterTone="q2"] {
    background: #f5fbfc;
    border-color: #d7e7ee;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"][quarterTone="q3"] {
    background: #f8f6fc;
    border-color: #e1dbee;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"][quarterTone="q4"] {
    background: #fdf9f3;
    border-color: #ecdfcb;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"] {
    border-radius: 20px;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right-width: 1px;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"][quarterTone="q1"] {
    background: #eaf1fd;
    border-color: #ccdaef;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"][quarterTone="q2"] {
    background: #eaf6f8;
    border-color: #cddfe5;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"][quarterTone="q3"] {
    background: #f2eef9;
    border-color: #dcd3ec;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"][quarterTone="q4"] {
    background: #fff3e5;
    border-color: #e8d4b8;
}

QFrame#SectionCard[sectionRole="annual-quarter-badge"] QLabel#SectionTitle {
    color: #435b7b;
    font-size: 15px;
}

QFrame#SectionCard[sectionRole="annual-month-row"] {
    background: #ffffff;
    border: 0;
    border-top: 1px solid #e7edf6;
    border-radius: 0;
}

QFrame#SectionCard[sectionRole="annual-quarter-group"] QFrame#SectionCard[sectionRole="annual-month-row"]:first-child {
    border-top: 0;
}

QFrame#SectionCard[sectionRole="annual-month-row"] QLabel#SectionTitle {
    color: #1f304c;
}

QFrame#SectionCard[sectionRole="annual-month-row"] QLabel#MutedText {
    color: #5f7492;
}

QFrame#SectionCard[sectionRole="annual-month-metric"] QLabel#SectionTitle {
    color: #20324d;
    font-size: 15px;
}

QFrame#SectionCard[sectionRole="annual-month-metric"] QLabel#MutedText {
    color: #5f7694;
    font-size: 11px;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-toggle"] {
    min-width: 72px;
    padding: 6px 12px;
    background: #f7f9fd;
    color: #4b607c;
    border: 1px solid #d5deeb;
    border-radius: 12px;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-toggle"]:hover {
    background: #edf3fb;
    color: #355172;
    border-color: #c8d5e7;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-toggle"]:checked {
    background: #e8effb;
    color: #26466f;
    border: 1px solid #bfd1ea;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-toggle"]:checked:hover {
    background: #dee8f8;
}

QFrame#SectionCard[sectionRole="annual-month-detail"] {
    background: #eff4fb;
    border: 1px solid #d2deee;
    border-radius: 18px;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] {
    background: #fdfefe;
    border: 1px solid #c9d8eb;
    border-radius: 16px;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"][panelTone="income"] {
    background: #fdfefe;
    border-color: #c8dbef;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"][panelTone="expense"] {
    background: #fffefd;
    border-color: #d5deeb;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#SectionTitle {
    color: #1f3656;
    font-size: 16px;
    font-weight: 700;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#MutedText {
    color: #587191;
    font-size: 12px;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QTableWidget[tableProfile="budget-ledger"] {
    background: #fcfdff;
    border-color: #d4dfed;
}

QFrame#SectionCard[sectionRole="annual-month-other"] {
    background: #f7f9fc;
    border-color: #dfe6f0;
    border-radius: 12px;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="income"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="income"] {
    background: #f7fbff;
    border-color: #d8e5f4;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="expense"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="expense"] {
    background: #faf9fd;
    border-color: #e1e4ef;
}

QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#SectionTitle {
    color: #526a88;
    font-size: 14px;
    font-weight: 600;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="income"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="income"] QLabel#SectionTitle {
    color: #4b6892;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="expense"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="expense"] QLabel#SectionTitle {
    color: #5d667f;
}

QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#MutedText {
    color: #7789a0;
    font-size: 12px;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="income"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="income"] QLabel#MutedText {
    color: #7b8ea7;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="expense"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="expense"] QLabel#MutedText {
    color: #848aa0;
}

QFrame#SectionCard[sectionRole="annual-month-other"] QTableWidget[tableProfile="budget-ledger"] {
    background: #fbfcff;
    border-color: #e2e9f2;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="income"] QTableWidget[tableProfile="budget-ledger"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="income"] QTableWidget[tableProfile="budget-ledger"] {
    background: #fcfdff;
    border-color: #dce7f3;
}

QFrame#SectionCard[sectionRole="annual-month-other"][panelTone="expense"] QTableWidget[tableProfile="budget-ledger"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"][panelTone="expense"] QTableWidget[tableProfile="budget-ledger"] {
    background: #fcfcff;
    border-color: #e3e6f0;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-other-action"] {
    min-width: 96px;
    padding: 6px 10px;
    background: #f7f9fc;
    color: #5d7089;
    border: 1px solid #d8e1ec;
    border-radius: 11px;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-other-action"]:hover {
    background: #eef3f8;
    color: #425973;
    border-color: #cfd9e5;
}

QPushButton#SecondaryActionButton[sectionRole="annual-month-other-action"]:disabled {
    background: #fafbfd;
    color: #a1aec0;
    border-color: #e6ebf2;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#TagLabel[sectionRole="status-badge"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#TagLabel[sectionRole="status-badge"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#TagLabel[sectionRole="status-badge"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge,
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge,
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge {
    border-radius: 9px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="green"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#TagLabel[sectionRole="status-badge"][tone="green"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="green"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge[statusTone="done"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge[statusTone="done"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge[statusTone="done"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge[statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge[statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge[statusTone="confirmed"] {
    background: #edf9f3;
    color: #2d8e64;
    border: 1px solid #ccebd9;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="amber"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#TagLabel[sectionRole="status-badge"][tone="amber"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="amber"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge[statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge[statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge[statusTone="pending"] {
    background: #fff6e8;
    color: #b37317;
    border: 1px solid #f0ddbb;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="red"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#TagLabel[sectionRole="status-badge"][tone="red"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="red"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge[statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge[statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge[statusTone="alert"] {
    background: #fff1f3;
    color: #c04f64;
    border: 1px solid #f1cad1;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="gray"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#TagLabel[sectionRole="status-badge"][tone="gray"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#TagLabel[sectionRole="status-badge"][tone="gray"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QLabel#StatusBadge[statusTone="idle"],
QFrame#SectionCard[sectionRole="annual-month-other"] QLabel#StatusBadge[statusTone="idle"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QLabel#StatusBadge[statusTone="idle"] {
    background: #f3f6fb;
    color: #6d7f99;
    border: 1px solid #dce5f1;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other"] QPushButton#SecondaryActionButton[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QToolButton[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other"] QToolButton[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QToolButton[sectionRole="status-action"] {
    min-width: 0;
    min-height: 24px;
    padding: 3px 8px;
    background: #f4f7fc;
    color: #5a6e8c;
    border: 1px solid #d7e0ec;
    border-radius: 9px;
    font-size: 11px;
    font-weight: 700;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"]:hover,
QFrame#SectionCard[sectionRole="annual-month-other"] QPushButton#SecondaryActionButton[sectionRole="status-action"]:hover,
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"]:hover,
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QToolButton[sectionRole="status-action"]:hover,
QFrame#SectionCard[sectionRole="annual-month-other"] QToolButton[sectionRole="status-action"]:hover,
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QToolButton[sectionRole="status-action"]:hover {
    background: #eaf0f8;
    color: #415975;
    border-color: #c9d5e4;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QToolButton[sectionRole="status-action"][statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other"] QToolButton[sectionRole="status-action"][statusTone="pending"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QToolButton[sectionRole="status-action"][statusTone="pending"] {
    background: #fff6ea;
    color: #aa6f1c;
    border-color: #ead8ba;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QToolButton[sectionRole="status-action"][statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other"] QToolButton[sectionRole="status-action"][statusTone="confirmed"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QToolButton[sectionRole="status-action"][statusTone="confirmed"] {
    background: #eef8f2;
    color: #2f825e;
    border-color: #cde6d8;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QPushButton#SecondaryActionButton[sectionRole="status-action"][statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QToolButton[sectionRole="status-action"][statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other"] QToolButton[sectionRole="status-action"][statusTone="alert"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QToolButton[sectionRole="status-action"][statusTone="alert"] {
    background: #fff2f4;
    color: #bf5668;
    border-color: #efcbd2;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QComboBox[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other"] QComboBox[sectionRole="status-action"],
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QComboBox[sectionRole="status-action"] {
    min-height: 24px;
    padding: 3px 24px 3px 8px;
    background: #f6f8fc;
    color: #5d708d;
    border: 1px solid #d7e0ec;
    border-radius: 9px;
    font-size: 11px;
    font-weight: 700;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QComboBox[sectionRole="status-action"]:focus,
QFrame#SectionCard[sectionRole="annual-month-other"] QComboBox[sectionRole="status-action"]:focus,
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QComboBox[sectionRole="status-action"]:focus {
    border: 1px solid #b8cae1;
}

QFrame#SectionCard[sectionRole="annual-month-detail-panel"] QComboBox[sectionRole="status-action"]::drop-down,
QFrame#SectionCard[sectionRole="annual-month-other"] QComboBox[sectionRole="status-action"]::drop-down,
QFrame#SectionCard[sectionRole="annual-month-other-panel"] QComboBox[sectionRole="status-action"]::drop-down {
    width: 18px;
    border: none;
}

QFrame#DetailPane[sectionRole="budget-fill-desk"] {
    background: #fcfdff;
    border-color: #d4dfed;
    border-radius: 22px;
}

QFrame#SectionCard[sectionRole="scope-row"] {
    background: #fbfcff;
    border-color: #d8e1f2;
    border-radius: 16px;
}

QFrame#SectionCard[sectionRole="annual-summary"] QFrame#SectionCard {
    background: #f7faff;
    border: 1px solid #dce6f5;
    border-radius: 16px;
}

QFrame#DetailPane {
    background: #ffffff;
    border-color: #d9e2ef;
    border-radius: 18px;
}

QFrame#DetailPane[cardVariant="editor"] {
    border-color: #d5dfea;
}

QFrame#DetailPane[sectionRole="detail-stack"] {
    background: #ffffff;
    border-color: #d7e1ef;
    border-radius: 20px;
}

QFrame#ListPane[sectionRole="reminder-list"] {
    background: #ffffff;
    border-color: #d8e2f0;
    border-radius: 20px;
}

QFrame#DetailPane[sectionRole="reminder-detail"] {
    background: #ffffff;
    border-color: #d7e1ef;
    border-radius: 22px;
}

QFrame#SectionCard[sectionRole="reminder-detail-editor"],
QFrame#SectionCard[sectionRole="reminder-detail-reading"] {
    background: #fbfdff;
    border: 1px solid #dde6f4;
    border-radius: 18px;
}

QFrame#ReadonlyBox[sectionRole="reminder-list-header"],
QFrame#ReadonlyBox[sectionRole="reminder-detail-summary"],
QFrame#ReadonlyBox[sectionRole="reminder-notes-summary"],
QFrame#ReadonlyBox[sectionRole="reminder-notes-body"] {
    background: #fbfdff;
    border: 1px solid #dde6f4;
    border-radius: 16px;
}

QFrame#SectionCard[sectionRole="reminder-notes"] {
    background: #ffffff;
    border-color: #d7e1ef;
    border-radius: 22px;
}

QFrame#DetailPane[sectionRole="reminder-detail"] QFrame#SectionCard,
QFrame#DetailPane[sectionRole="detail-stack"][sectionVariant="notes-panel"] QFrame#SectionCard {
    background: #fbfdff;
    border: 1px solid #dde6f4;
    border-radius: 16px;
}

QFrame#DetailPane[sectionRole="budget-workbench-editor"] {
    background: #fcfdff;
    border-color: #d2ddeb;
    border-radius: 22px;
}

QFrame#DetailPane[sectionRole="budget-fill-desk"] QLineEdit,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QTextEdit,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QComboBox,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QDateEdit,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QDateTimeEdit,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QSpinBox {
    background: #ffffff;
    border-color: #d7e2f2;
    border-radius: 12px;
}

QFrame#DetailPane[sectionRole="budget-workbench-editor"] QLineEdit,
QFrame#DetailPane[sectionRole="budget-workbench-editor"] QTextEdit,
QFrame#DetailPane[sectionRole="budget-workbench-editor"] QComboBox,
QFrame#DetailPane[sectionRole="budget-workbench-editor"] QDateEdit,
QFrame#DetailPane[sectionRole="budget-workbench-editor"] QDateTimeEdit,
QFrame#DetailPane[sectionRole="budget-workbench-editor"] QSpinBox {
    background: #ffffff;
    border-color: #d7e2f2;
    border-radius: 12px;
}

QFrame#DetailPane[sectionRole="detail-stack"] QLineEdit,
QFrame#DetailPane[sectionRole="detail-stack"] QTextEdit,
QFrame#DetailPane[sectionRole="detail-stack"] QComboBox,
QFrame#DetailPane[sectionRole="detail-stack"] QDateEdit,
QFrame#DetailPane[sectionRole="detail-stack"] QDateTimeEdit,
QFrame#DetailPane[sectionRole="detail-stack"] QSpinBox {
    background: #ffffff;
    border-color: #d9e3f1;
    border-radius: 12px;
}

QFrame#DetailPane[sectionRole="reminder-detail"] QLineEdit,
QFrame#DetailPane[sectionRole="reminder-detail"] QTextEdit,
QFrame#DetailPane[sectionRole="reminder-detail"] QComboBox,
QFrame#DetailPane[sectionRole="reminder-detail"] QDateEdit,
QFrame#DetailPane[sectionRole="reminder-detail"] QDateTimeEdit,
QFrame#DetailPane[sectionRole="reminder-detail"] QSpinBox {
    background: #ffffff;
    border-color: #d9e3f1;
    border-radius: 12px;
}

QFrame#DetailPane[sectionVariant="notes-panel"] QTextEdit {
    background: #fbfdff;
    border-color: #dce5f2;
    border-radius: 16px;
    padding: 11px 12px;
}

QFrame#ReadonlyBox {
    border-radius: 12px;
}

QLabel#BrandTitle {
    color: #ff4b6e;
    font-size: 26px;
    font-weight: 800;
}

QLabel#BrandSubtitle {
    color: #7e8aa5;
    font-size: 12px;
    font-weight: 600;
}

QLabel#PageTitle {
    color: #1c2740;
    font-size: 20px;
    font-weight: 800;
}

QLabel#SectionTitle {
    color: #1f2b44;
    font-size: 16px;
    font-weight: 800;
}

QLabel#SectionTitle[sectionDensity="compact"] {
    font-size: 15px;
}

QFrame#ListPane[sectionRole="stacked-list"] QLabel#SectionTitle,
QFrame#DetailPane[sectionRole="detail-stack"] QLabel#SectionTitle,
QFrame#ListPane[sectionRole="reminder-list"] QLabel#SectionTitle,
QFrame#DetailPane[sectionRole="reminder-detail"] QLabel#SectionTitle {
    font-size: 16px;
}

QFrame#SectionCard[sectionRole="dashboard-trend"] QLabel#SectionTitle,
QFrame#ListPane[sectionRole="dashboard-reminders"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="dashboard-accounts"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="dashboard-transactions"] QLabel#SectionTitle,
QFrame#ListPane[sectionRole="dashboard-pending"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="workspace-main"] QLabel#SectionTitle,
QFrame#ListPane[sectionRole="workspace-sidebar"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="preview-panel"] QLabel#SectionTitle,
QFrame#ListPane[sectionRole="preview-panel"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="reminder-notes"] QLabel#SectionTitle,
QFrame#ToolbarCard[sectionRole="budget-workbench-shell"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="budget-annual-overview"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-master-sheet"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-quarter-brief"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-quarter-summary"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="annual-detail-panel"] QLabel#SectionTitle,
QFrame#SectionCard[sectionRole="budget-effective-scope"] QLabel#SectionTitle,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QLabel#SectionTitle {
    font-size: 16px;
}

QFrame#SectionCard[sectionRole="annual-summary"] QFrame#SectionCard QLabel#SectionTitle {
    color: #34558f;
    font-size: 15px;
}

QLabel#MutedText,
QLabel#FieldLabel,
QLabel#MetricNote {
    color: #74829a;
}

QLabel#MutedText[sectionDensity="compact"] {
    color: #6d7c96;
    font-size: 12px;
}

QFrame#ListPane[sectionRole="stacked-list"] QLabel#MutedText,
QFrame#DetailPane[sectionRole="detail-stack"] QLabel#MutedText,
QFrame#ListPane[sectionRole="reminder-list"] QLabel#MutedText,
QFrame#DetailPane[sectionRole="reminder-detail"] QLabel#MutedText {
    color: #6a7a95;
}

QFrame#SectionCard[sectionRole="dashboard-trend"] QLabel#MutedText,
QFrame#ListPane[sectionRole="dashboard-reminders"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="dashboard-accounts"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="dashboard-transactions"] QLabel#MutedText,
QFrame#ListPane[sectionRole="dashboard-pending"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="workspace-main"] QLabel#MutedText,
QFrame#ListPane[sectionRole="workspace-sidebar"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="preview-panel"] QLabel#MutedText,
QFrame#ListPane[sectionRole="preview-panel"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="reminder-notes"] QLabel#MutedText,
QFrame#ToolbarCard[sectionRole="budget-workbench-shell"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="budget-annual-overview"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-master-sheet"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-quarter-brief"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-quarter-summary"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="annual-detail-panel"] QLabel#MutedText,
QFrame#SectionCard[sectionRole="budget-effective-scope"] QLabel#MutedText,
QFrame#DetailPane[sectionRole="budget-fill-desk"] QLabel#MutedText {
    color: #6c7c97;
}

QFrame#SectionCard[sectionRole="annual-summary"] QFrame#SectionCard QLabel#MutedText {
    color: #667995;
    font-size: 12px;
}

QLabel#FieldLabel {
    font-size: 12px;
    font-weight: 700;
}

QLabel#MetricTitle {
    color: #7a89a6;
    font-size: 12px;
    font-weight: 700;
}

QLabel#MetricValue {
    color: #1b2a45;
    font-size: 24px;
    font-weight: 800;
}

QFrame#MetricCard {
    min-height: 104px;
    border-radius: 18px;
}

QFrame#MetricCard[metricScope="annual"] {
    min-height: 96px;
    border-radius: 16px;
    background: #fcfdff;
    border-color: #d7e1ee;
}

QFrame#MetricCard[metricTone="pending"] {
    background: #fffdf9;
    border-color: #eadfb9;
}

QLabel#MetricNote {
    font-size: 12px;
    line-height: 1.4;
}

QLabel#MetricTitle[metricScope="annual"] {
    color: #677893;
    font-size: 11px;
}

QLabel#MetricValue[metricScope="annual"] {
    font-size: 22px;
}

QLabel#MetricNote[metricScope="annual"] {
    color: #75849f;
    font-size: 11px;
}

QLabel#TagLabel {
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    background: #eef4ff;
    color: #3f67d9;
    border: 1px solid #d5e1ff;
}

QLabel#TagLabel[tone="green"] {
    background: #e8f8f1;
    color: #1f7d5b;
    border: 1px solid #bfe8d6;
}

QLabel#TagLabel[tone="amber"] {
    background: #fff6df;
    color: #9d6d16;
    border: 1px solid #f1dca6;
}

QLabel#TagLabel[tone="red"] {
    background: #fff0f2;
    color: #bd3650;
    border: 1px solid #f2c3cb;
}

QLabel#TagLabel[tone="gray"] {
    background: #f1f5fb;
    color: #66758f;
    border: 1px solid #dce5f2;
}

QPushButton {
    background: #4a7cff;
    color: #ffffff;
    border: none;
    border-radius: 14px;
    padding: 7px 11px;
    font-weight: 700;
}

QPushButton:hover {
    background: #3d70f0;
}

QPushButton:disabled {
    background: #c9d4ea;
    color: #f7f9fd;
}

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

QPushButton#DangerActionButton {
    background: #fff0f2;
    color: #d6455d;
    border: 1px solid #f2c3cb;
}

QPushButton#DangerActionButton:hover {
    background: #ffe3e8;
}

QLineEdit,
QTextEdit,
QComboBox,
QDateEdit,
QDateTimeEdit,
QSpinBox {
    background: #ffffff;
    border: 1px solid #d9e2f1;
    border-radius: 10px;
    padding: 7px 10px;
    color: #20304a;
    selection-background-color: #4a7cff;
    selection-color: #ffffff;
}

QLineEdit:focus,
QTextEdit:focus,
QComboBox:focus,
QDateEdit:focus,
QDateTimeEdit:focus,
QSpinBox:focus {
    border: 1px solid #7aa2ff;
}

QComboBox,
QDateEdit,
QDateTimeEdit,
QSpinBox {
    padding-right: 24px;
}

QListWidget {
    background: rgba(255, 255, 255, 0.98);
    border: 1px solid #dbe4f2;
    border-radius: 18px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    padding: 9px 11px;
    margin: 2px 0;
    border-radius: 12px;
}

QListWidget::item:selected {
    background: #eef4ff;
    color: #ffffff;
}

QFrame#ListPane[sectionRole="stacked-list"] QListWidget {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
}

QFrame#ListPane[sectionRole="reminder-list"] QListWidget {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
}

QFrame#ListPane[sectionRole="dashboard-reminders"] QListWidget,
QFrame#ListPane[sectionRole="dashboard-pending"] QListWidget,
QFrame#ListPane[sectionRole="workspace-sidebar"] QListWidget,
QFrame#ListPane[sectionRole="preview-panel"] QListWidget {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 2px 0;
}

QFrame#ListPane[sectionRole="stacked-list"] QListWidget::item {
    padding: 0;
    margin: 0 0 10px 0;
    border-radius: 0;
}

QFrame#ListPane[sectionRole="reminder-list"] QListWidget::item {
    padding: 0;
    margin: 0 0 10px 0;
    border-radius: 0;
}

QFrame#ListPane[sectionRole="dashboard-reminders"] QListWidget::item,
QFrame#ListPane[sectionRole="dashboard-pending"] QListWidget::item,
QFrame#ListPane[sectionRole="workspace-sidebar"] QListWidget::item,
QFrame#ListPane[sectionRole="preview-panel"] QListWidget::item {
    padding: 8px 4px;
    margin: 0;
    border-bottom: 1px solid #edf2fb;
    border-radius: 0;
}

QFrame#ListPane[sectionRole="dashboard-reminders"] QListWidget::item:selected,
QFrame#ListPane[sectionRole="dashboard-pending"] QListWidget::item:selected,
QFrame#ListPane[sectionRole="workspace-sidebar"] QListWidget::item:selected,
QFrame#ListPane[sectionRole="preview-panel"] QListWidget::item:selected {
    background: #eef4ff;
    color: #20304a;
    border-radius: 8px;
}

QFrame#ReminderRow {
    background: #ffffff;
    border: 1px solid #dfe8f6;
    border-left: 5px solid #cfd8e8;
    border-radius: 16px;
}

QFrame#ReminderRow[selected="true"] {
    background: #f4f8ff;
    border: 1px solid #bcd0ff;
    border-left: 5px solid #4a7cff;
}

QFrame#ReminderRow[tone="red"] {
    border-left: 5px solid #ef6a7d;
}

QFrame#ReminderRow[tone="amber"] {
    border-left: 5px solid #e6b34c;
}

QFrame#ReminderRow[tone="green"] {
    border-left: 5px solid #46b989;
}

QLabel#ReminderRowTitle {
    color: #1f2b44;
    font-size: 14px;
    font-weight: 800;
}

QLabel#ReminderRowMeta,
QLabel#ReminderRowStatus {
    color: #7a89a6;
    font-size: 12px;
}

QLabel#ReminderRowStatus {
    font-weight: 700;
}

QHeaderView::section {
    background: #f8fbff;
    color: #6f809c;
    border: none;
    border-right: 1px solid #edf2fb;
    border-bottom: 1px solid #dde6f3;
    padding: 9px 12px;
    font-weight: 700;
}

QTableCornerButton::section {
    background: #f8fbff;
    border: none;
    border-right: 1px solid #edf2fb;
    border-bottom: 1px solid #dde6f3;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #dbe4f2;
    border-radius: 16px;
    gridline-color: transparent;
    selection-background-color: #eef4ff;
    selection-color: #20304a;
    alternate-background-color: #fbfcff;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #edf2fb;
}

QTableWidget::item:selected {
    color: #20304a;
}

QTableWidget[tableDensity="dense"] {
    font-size: 13px;
}

QTableWidget[tableDensity="dense"]::item {
    padding: 5px 8px;
}

QTableWidget[tableDensity="dense"] QHeaderView::section {
    padding: 8px 10px;
}

QTableWidget[tableRole="matrix"] {
    font-size: 12px;
}

QTableWidget[tableRole="matrix"] QHeaderView::section {
    padding: 7px 8px;
}

QTableWidget[tableProfile="budget-workbench"] {
    border-radius: 15px;
}

QTableWidget[tableProfile="budget-workbench"]::item {
    padding: 5px 8px;
}

QTableWidget[tableProfile="budget-workbench"] QHeaderView::section {
    padding: 8px 10px;
}

QTableWidget[tableProfile="monthly-workbench"],
QTableWidget[tableProfile="monthly-income"],
QTableWidget[tableProfile="monthly-expense"] {
    border-radius: 15px;
}

QTableWidget[tableProfile="monthly-workbench"]::item,
QTableWidget[tableProfile="monthly-income"]::item,
QTableWidget[tableProfile="monthly-expense"]::item {
    padding: 5px 8px;
}

QTableWidget[tableProfile="monthly-workbench"] QHeaderView::section,
QTableWidget[tableProfile="monthly-income"] QHeaderView::section,
QTableWidget[tableProfile="monthly-expense"] QHeaderView::section {
    padding: 8px 10px;
}

QTableWidget[tableProfile="budget-ledger"] {
    border-radius: 15px;
}

QTableWidget[tableProfile="annual-summary"] {
    background: #fcfdff;
    border-color: #d4deee;
    border-radius: 18px;
    font-size: 12px;
    selection-background-color: #e9f1ff;
    alternate-background-color: #f8fbff;
}

QTableWidget[tableProfile="annual-summary"]::item {
    padding: 4px 8px;
    border-bottom: 1px solid #e7eef8;
}

QTableWidget[tableProfile="annual-summary"] QHeaderView::section,
QTableWidget[tableProfile="annual-summary"] QTableCornerButton::section {
    background: #edf4ff;
    color: #556f96;
    border-right: 1px solid #d8e3f4;
    border-bottom: 1px solid #cfdbed;
    padding: 7px 10px;
}

QTableWidget[tableProfile="annual-month-sheet"] {
    background: #fcfdff;
    border-color: #d5e0ef;
    border-radius: 18px;
    font-size: 12px;
    selection-background-color: #edf4ff;
    alternate-background-color: #f9fbff;
}

QTableWidget[tableProfile="annual-month-sheet"]::item {
    padding: 4px 7px;
    border-bottom: 1px solid #e7eef8;
}

QTableWidget[tableProfile="annual-month-sheet"] QHeaderView::section,
QTableWidget[tableProfile="annual-month-sheet"] QTableCornerButton::section {
    background: #eef5ff;
    color: #587094;
    border-right: 1px solid #dbe5f5;
    border-bottom: 1px solid #d1dcef;
    padding: 7px 8px;
}

QTableWidget[tableProfile="annual-detail"] {
    background: #fcfdff;
    border-color: #d8e2ef;
    border-radius: 16px;
    font-size: 12px;
    selection-background-color: #eef4ff;
    alternate-background-color: #fafcff;
}

QTableWidget[tableProfile="annual-detail"]::item {
    padding: 4px 6px;
    border-bottom: 1px solid #ebf1fa;
}

QTableWidget[tableProfile="annual-detail"] QHeaderView::section,
QTableWidget[tableProfile="annual-detail"] QTableCornerButton::section {
    background: #f4f7ff;
    color: #61718e;
    border-right: 1px solid #e0e7f4;
    border-bottom: 1px solid #d6e1f0;
    padding: 6px 8px;
}

QTableWidget[tableProfile="scope-reference"] {
    background: #fcfdff;
    border-radius: 14px;
}

QTableWidget[tableProfile="scope-reference"]::item {
    padding: 5px 8px;
}

QTableWidget[tableProfile="scope-guide"] {
    background: #fcfdff;
    border-radius: 14px;
}

QTableWidget[tableProfile="scope-guide"]::item {
    padding: 5px 8px;
}

QFrame#SectionCard[sectionRole="dashboard-accounts"] QTableWidget,
QFrame#SectionCard[sectionRole="dashboard-transactions"] QTableWidget {
    border-radius: 14px;
}

QFrame#SectionCard[sectionRole="dashboard-accounts"] QTableWidget::item,
QFrame#SectionCard[sectionRole="dashboard-transactions"] QTableWidget::item {
    padding: 6px 8px;
}

QSplitter::handle {
    background: transparent;
}

QSplitter::handle:horizontal {
    width: 10px;
}

QSplitter::handle:horizontal:hover {
    background: #e8eef8;
}

QScrollArea,
QAbstractScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    background: #edf2fb;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #b8c7e6;
    min-height: 44px;
    border-radius: 6px;
}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {
    background: transparent;
    border: none;
}

QTabWidget::pane {
    border: none;
}

QTabBar {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #d8e1ef;
    border-radius: 16px;
    padding: 4px;
}

QTabBar::tab {
    min-height: 32px;
    padding: 6px 12px;
    margin-right: 4px;
    background: transparent;
    color: #5a6b87;
    border: none;
    border-radius: 10px;
    font-weight: 800;
}

QTabBar::tab:hover:!selected {
    background: #eef4ff;
    color: #3159c8;
}

QTabBar::tab:selected {
    background: #4a7cff;
    color: #ffffff;
}
"""


def apply_theme(widget) -> None:
    widget.setStyleSheet(APP_STYLESHEET)
