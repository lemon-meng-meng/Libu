#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部开发模式：同时启动后端与前端 Vite/Electron
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${LIBU_PYTHON:-python3}"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
fi

if [ ! -d "$ROOT/src/frontend/node_modules" ]; then
  echo "==> 安装前端依赖"
  (cd src/frontend && npm install)
fi

echo "==> 启动后端 (127.0.0.1:8000)"
PYTHONPATH="$ROOT/src" "$PY" -m libu serve --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT INT TERM

echo "==> 启动前端开发服务器 (127.0.0.1:5173)"
cd src/frontend
npm run dev
