from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from private_ledger.domain.models import AppSettings
from private_ledger.ui.widgets import create_card, make_secondary_button


class SettingsPage(QWidget):
    save_requested = Signal(object)
    export_requested = Signal()
    backup_requested = Signal()
    minimax_key_save_requested = Signal(str)
    minimax_test_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.db_path_label = QLabel("--")
        self.db_path_label.setObjectName("MutedText")
        self.data_dir_edit = QLineEdit()
        self.export_dir_edit = QLineEdit()
        self.backup_dir_edit = QLineEdit()
        self.default_currency_combo = QComboBox()
        self.default_currency_combo.addItems(["CNY", "USD"])
        self.reminder_days_spin = QSpinBox()
        self.reminder_days_spin.setRange(0, 30)
        self.obsidian_path_edit = QLineEdit()
        self.minimax_host_combo = QComboBox()
        self.minimax_host_combo.addItems(["中国站 https://api.minimaxi.com/v1", "国际站 https://api.minimax.io/v1"])
        self.minimax_model_edit = QLineEdit("MiniMax-M2.7")
        self.minimax_key_edit = QLineEdit()
        self.minimax_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.minimax_key_edit.setPlaceholderText("粘贴 MiniMax API Key，保存后不会明文显示")
        self.minimax_key_state_label = QLabel("Key 状态：未配置")
        self.minimax_key_state_label.setObjectName("MutedText")
        self.status_label = QLabel("")
        self.status_label.setObjectName("MutedText")
        self.save_button = QPushButton("保存设置")
        self.save_key_button = QPushButton("保存 MiniMax Key")
        self.test_minimax_button = make_secondary_button("测试 MiniMax 连接")
        self.export_button = make_secondary_button("导出 JSON")
        self.backup_button = make_secondary_button("备份数据库")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        settings_card, settings_layout = create_card("本地数据与口径设置", "导出和备份路径会直接显示在这里")
        settings_layout.addWidget(self.db_path_label)
        form = QFormLayout()
        form.addRow("数据目录", self.data_dir_edit)
        form.addRow("导出目录", self.export_dir_edit)
        form.addRow("备份目录", self.backup_dir_edit)
        form.addRow("默认币种", self.default_currency_combo)
        form.addRow("提醒提前天数", self.reminder_days_spin)
        form.addRow("Obsidian 私帐路径", self.obsidian_path_edit)
        settings_layout.addLayout(form)
        button_row = QHBoxLayout()
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.export_button)
        button_row.addWidget(self.backup_button)
        settings_layout.addLayout(button_row)
        settings_layout.addWidget(self.status_label)

        minimax_card, minimax_layout = create_card("MiniMax 识别设置", "API Key 存入 macOS Keychain，不进入导出和备份")
        minimax_form = QFormLayout()
        minimax_form.addRow("API Host", self.minimax_host_combo)
        minimax_form.addRow("模型", self.minimax_model_edit)
        minimax_form.addRow("API Key", self.minimax_key_edit)
        minimax_layout.addLayout(minimax_form)
        minimax_layout.addWidget(self.minimax_key_state_label)
        minimax_button_row = QHBoxLayout()
        minimax_button_row.addWidget(self.save_key_button)
        minimax_button_row.addWidget(self.test_minimax_button)
        minimax_layout.addLayout(minimax_button_row)

        note_card, note_layout = create_card("后续接入", "本轮先做图片与截图识别")
        note_layout.addWidget(QLabel("PDF 账单、批量导入、Obsidian 同步、外部余额查询将在后续版本接入。"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(settings_card)
        layout.addWidget(minimax_card)
        layout.addWidget(note_card)

    def _connect_signals(self) -> None:
        self.save_button.clicked.connect(self._emit_save)
        self.save_key_button.clicked.connect(self._emit_key_save)
        self.test_minimax_button.clicked.connect(self.minimax_test_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.backup_button.clicked.connect(self.backup_requested.emit)

    def load_settings(self, settings: AppSettings, db_path: str) -> None:
        self.db_path_label.setText(f"数据库文件：{db_path}")
        self.data_dir_edit.setText(settings.data_dir)
        self.export_dir_edit.setText(settings.export_dir)
        self.backup_dir_edit.setText(settings.backup_dir)
        self.default_currency_combo.setCurrentText(settings.default_currency)
        self.reminder_days_spin.setValue(settings.reminder_lead_days)
        self.obsidian_path_edit.setText(settings.obsidian_path)
        host_label = "中国站 https://api.minimaxi.com/v1"
        if settings.minimax_api_host == "https://api.minimax.io/v1":
            host_label = "国际站 https://api.minimax.io/v1"
        self.minimax_host_combo.setCurrentText(host_label)
        self.minimax_model_edit.setText(settings.minimax_model)
        self.minimax_key_edit.clear()
        self.minimax_key_state_label.setText("Key 状态：已配置" if settings.minimax_key_configured else "Key 状态：未配置")

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _emit_save(self) -> None:
        self.save_requested.emit(
            {
                "data_dir": self.data_dir_edit.text().strip(),
                "export_dir": self.export_dir_edit.text().strip(),
                "backup_dir": self.backup_dir_edit.text().strip(),
                "default_currency": self.default_currency_combo.currentText().strip(),
                "reminder_lead_days": self.reminder_days_spin.value(),
                "obsidian_path": self.obsidian_path_edit.text().strip(),
                "minimax_api_host": self._selected_minimax_host(),
                "minimax_model": self.minimax_model_edit.text().strip() or "MiniMax-M2.7",
            }
        )

    def _emit_key_save(self) -> None:
        self.minimax_key_save_requested.emit(self.minimax_key_edit.text().strip())

    def _selected_minimax_host(self) -> str:
        text = self.minimax_host_combo.currentText()
        if "api.minimax.io" in text:
            return "https://api.minimax.io/v1"
        return "https://api.minimaxi.com/v1"
