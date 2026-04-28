#!/bin/bash

set -euo pipefail

if [ -n "${PRIVATE_LEDGER_PROJECT_DIR:-}" ] && [ -d "${PRIVATE_LEDGER_PROJECT_DIR}/src/private_ledger" ]; then
  PROJECT_DIR="${PRIVATE_LEDGER_PROJECT_DIR}"
else
  PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

if [ ! -d "${PROJECT_DIR}/src/private_ledger" ]; then
  echo "未找到项目目录：$PROJECT_DIR"
  echo "请确认启动器仍然指向正确的项目位置。"
  read -r -p "按回车关闭..."
  exit 1
fi

cd "$PROJECT_DIR"

if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

if [ -z "${PYTHON_BIN:-}" ]; then
  echo "未找到可用的 Python 3。"
  read -r -p "按回车关闭..."
  exit 1
fi

export PYTHONPATH="$PROJECT_DIR/src"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-cocoa}"

echo "正在启动 草莓私帐管理系统..."
echo "项目目录: $PROJECT_DIR"

if [ "${LAUNCHER_CHECK_ONLY:-0}" = "1" ]; then
  echo "检查模式：启动器配置正常。"
  exit 0
fi

if ! "$PYTHON_BIN" -m private_ledger.app; then
  echo
  echo "启动失败，请把这里的报错截图发给我。"
  read -r -p "按回车关闭..."
  exit 1
fi
