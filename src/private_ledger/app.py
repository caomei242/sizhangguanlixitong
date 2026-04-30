from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from private_ledger.storage.repository import LedgerRepository
from private_ledger.ui.app_icon import load_app_icon
from private_ledger.ui.main_window import MainWindow


PREFERRED_FONT_FAMILIES = (
    "PingFang SC",
    "Hiragino Sans GB",
    "Helvetica Neue",
    "Arial Unicode MS",
    "Arial",
)


def apply_application_font(app: QApplication) -> None:
    available = set(QFontDatabase.families())
    for family in PREFERRED_FONT_FAMILIES:
        if family in available:
            app.setFont(QFont(family, 14))
            return


def apply_light_appearance(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: QColor("#F5F7FB"),
        QPalette.ColorRole.WindowText: QColor("#24324A"),
        QPalette.ColorRole.Base: QColor("#FFFFFF"),
        QPalette.ColorRole.AlternateBase: QColor("#EDF2FA"),
        QPalette.ColorRole.ToolTipBase: QColor("#FFFFFF"),
        QPalette.ColorRole.ToolTipText: QColor("#24324A"),
        QPalette.ColorRole.Text: QColor("#24324A"),
        QPalette.ColorRole.Button: QColor("#EEF3FB"),
        QPalette.ColorRole.ButtonText: QColor("#24324A"),
        QPalette.ColorRole.BrightText: QColor("#FFFFFF"),
        QPalette.ColorRole.Highlight: QColor("#E88FA6"),
        QPalette.ColorRole.HighlightedText: QColor("#FFFFFF"),
        QPalette.ColorRole.PlaceholderText: QColor("#8A94A6"),
    }
    for role, color in colors.items():
        palette.setColor(QPalette.ColorGroup.Active, role, color)
        palette.setColor(QPalette.ColorGroup.Inactive, role, color)

    disabled_colors = {
        QPalette.ColorRole.WindowText: QColor("#8A94A6"),
        QPalette.ColorRole.Text: QColor("#98A2B3"),
        QPalette.ColorRole.ButtonText: QColor("#98A2B3"),
        QPalette.ColorRole.Highlight: QColor("#F2C7D3"),
        QPalette.ColorRole.HighlightedText: QColor("#FFFFFF"),
        QPalette.ColorRole.PlaceholderText: QColor("#B3BAC7"),
    }
    for role, color in disabled_colors.items():
        palette.setColor(QPalette.ColorGroup.Disabled, role, color)

    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor("#F5F7FB"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor("#F6F8FC"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor("#EEF2F8"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor("#EEF2F8"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, QColor("#8A94A6"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, QColor("#FFFFFF"))

    app.setPalette(palette)


def build_app(data_dir: str | Path | None = None) -> tuple[QApplication, MainWindow]:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    apply_application_font(app)
    apply_light_appearance(app)
    app.setApplicationDisplayName("草莓私帐管理系统")
    app.setWindowIcon(load_app_icon())
    repository = LedgerRepository(data_dir=data_dir)
    window = MainWindow(repository=repository)
    window.setWindowIcon(load_app_icon())
    return app, window


def main() -> int:
    app, window = build_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
