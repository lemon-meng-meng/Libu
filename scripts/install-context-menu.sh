#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 安装吏部「用吏部打开」右键菜单（Nautilus 扩展 + 脚本兜底）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

EXT_DIR="$HOME/.local/share/nautilus-python/extensions"
SCRIPT_DIR="$HOME/.local/share/nautilus/scripts"
mkdir -p "$EXT_DIR" "$SCRIPT_DIR"

install -m 0644 "$ROOT/nautilus-extension/libu_menu.py" "$EXT_DIR/libu_menu.py"
echo "已安装 Nautilus 扩展：$EXT_DIR/libu_menu.py"

# 脚本兜底：即使没有 nautilus-python 也能使用（放于 Scripts 子菜单）
cat > "$SCRIPT_DIR/用吏部打开" <<'EOF'
#!/usr/bin/env bash
# Nautilus 脚本：把第一个选中的图片交给吏部
set -e
first="$(printf '%s\n' "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS" | head -n1)"
[ -n "$first" ] || exit 0
if command -v libu-app >/dev/null 2>&1; then
  exec libu-app --import "$first"
elif command -v libu >/dev/null 2>&1; then
  exec libu --import "$first"
fi
EOF
chmod 0755 "$SCRIPT_DIR/用吏部打开"
echo "已安装 Nautilus 脚本：$SCRIPT_DIR/用吏部打开"

if command -v nautilus >/dev/null 2>&1; then
  nautilus -q >/dev/null 2>&1 || true
  echo "已请求重启文件管理器以生效。"
fi
echo "完成。若未出现菜单项，请确认已安装 python3-nautilus。"
