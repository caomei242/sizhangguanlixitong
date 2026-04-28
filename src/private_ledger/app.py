from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
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


def build_app(data_dir: str | Path | None = None) -> tuple[QApplication, MainWindow]:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    apply_application_font(app)
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
