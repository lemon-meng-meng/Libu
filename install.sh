#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · 用户级一键安装脚本（无需 root）。
# 安装位置：~/.local/share/libu
# 可执行入口：~/.local/bin/libu、~/.local/bin/libu-app
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
APP_DIR="$PREFIX/share/libu"
BIN_DIR="$PREFIX/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "==> 安装吏部到 $APP_DIR"

command -v python3 >/dev/null 2>&1 || { echo "缺少 python3" >&2; exit 1; }

# 1) 前端构建（若缺失）
if [ ! -f "$ROOT/src/frontend/dist/index.html" ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "==> 构建前端"
    (cd "$ROOT/src/frontend" && npm install --no-audit --no-fund && npm run build)
  else
    echo "!! 未找到 npm 且缺少已构建前端，界面可能无法显示" >&2
  fi
fi

# 2) 复制文件
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR" "$APP_DIR/web" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
cp -r "$ROOT/src" "$APP_DIR/src"
if [ -d "$ROOT/src/frontend/dist" ]; then
  cp -r "$ROOT/src/frontend/dist/." "$APP_DIR/web/"
fi
rm -rf "$APP_DIR/src/frontend/node_modules" \
       "$APP_DIR/src/frontend/dist" \
       "$APP_DIR/src/frontend/build"
find "$APP_DIR/src" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
cp -r "$ROOT/data" "$APP_DIR/data"
cp -r "$ROOT/bin" "$APP_DIR/bin"
cp "$ROOT/requirements.txt" "$ROOT/README.md" "$ROOT/LICENSE" "$APP_DIR/" 2>/dev/null || true
[ -f "$ROOT/THIRD-PARTY-NOTICES.md" ] && cp "$ROOT/THIRD-PARTY-NOTICES.md" "$APP_DIR/"

# 3) 虚拟环境
echo "==> 创建 Python 虚拟环境（需要网络）"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip >/dev/null
"$APP_DIR/venv/bin/pip" install -r "$ROOT/requirements.txt"

# 4) 入口与桌面项
ln -sf "$APP_DIR/bin/libu" "$BIN_DIR/libu"
ln -sf "$APP_DIR/bin/libu-app" "$BIN_DIR/libu-app"
install -m 0644 "$ROOT/packaging/libu.desktop" "$DESKTOP_DIR/libu.desktop"
install -m 0644 "$ROOT/data/icons/libu_256.png" "$ICON_DIR/libu.png"

echo "==> 完成"
echo "启动：$BIN_DIR/libu-app"
echo "如果 $BIN_DIR 不在 PATH 中，请将其加入 PATH 后重试。"
