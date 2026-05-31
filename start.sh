#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WX_DIR="$ROOT/wx_part/PawPause-dodong-worker-pet-merge-20260531"
ZYJ_DIR="$ROOT/zyj_part"
VENV="$ZYJ_DIR/.venv"

## 添加自己的API KEY
export STEP_API_KEY="5TjSyZtGW4XvKKsPXqxoRza0fsGqACXXS6jExsrIX05gFk1yKVeqGM4Qcu2b7PNe9"

WX_PID=""
ZYJ_PID=""

cleanup() {
  local code="${1:-$?}"
  [[ -n "$WX_PID" ]] && kill "$WX_PID" 2>/dev/null || true
  [[ -n "$ZYJ_PID" ]] && kill "$ZYJ_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  exit "$code"
}

trap 'cleanup 130' INT
trap 'cleanup 143' TERM

if [[ ! -d "$WX_DIR" ]]; then
  echo "找不到 wx_part 目录: $WX_DIR" >&2
  exit 1
fi

if [[ ! -f "$VENV/bin/activate" ]]; then
  echo "找不到 Python 虚拟环境: $VENV" >&2
  echo "请先在 zyj_part 下执行:" >&2
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

echo ">>> 启动 wx_part (Electron + localhost:5173) ..."
cd "$WX_DIR"
if [[ ! -d node_modules ]]; then
  corepack pnpm install
fi
corepack pnpm dev &
WX_PID=$!

echo ">>> 启动 zyj_part (Flask + localhost:5001) ..."
cd "$ZYJ_DIR"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python browser_photo.py &
ZYJ_PID=$!

echo ""
echo "两个服务已在后台运行。"
echo "  wx:  http://localhost:5173  (桌宠由 Electron 窗口展示)"
echo "  zyj: http://127.0.0.1:5001  (browser_photo.py 会自动打开浏览器)"
echo "按 Ctrl+C 停止全部进程。"
echo ""

wait "$WX_PID" "$ZYJ_PID"
cleanup $?
