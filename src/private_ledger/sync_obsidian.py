from __future__ import annotations

import argparse
from pathlib import Path

from private_ledger.services.obsidian_sync import ObsidianLedgerSyncService
from private_ledger.storage.repository import LedgerRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步 Obsidian 私帐到草莓私帐管理系统")
    parser.add_argument("--obsidian-root", help="Obsidian 根目录或财务/私帐目录")
    parser.add_argument("--db-path", help="SQLite 数据库路径")
    parser.add_argument("--data-dir", help="应用数据目录，默认取系统设置或默认路径")
    parser.add_argument("--date", action="append", default=[], help="仅同步指定日账，可重复传入 YYYY-MM-DD")
    parser.add_argument("--month", action="append", default=[], help="仅同步指定月账，可重复传入 YYYY-MM")
    return parser


def repository_from_args(data_dir: str | None, db_path: str | None) -> LedgerRepository:
    if data_dir:
        return LedgerRepository(data_dir=data_dir)
    if db_path:
        return LedgerRepository(db_path=Path(db_path).expanduser())
    return LedgerRepository()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repository = repository_from_args(args.data_dir, args.db_path)
    try:
        service = ObsidianLedgerSyncService(repository)
        report = service.sync(
            obsidian_root=args.obsidian_root,
            dates=args.date,
            months=args.month,
        )
        print(report.render_text())
        return 0
    finally:
        repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
