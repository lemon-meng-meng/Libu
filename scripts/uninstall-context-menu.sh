#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 卸载吏部右键菜单。
set -euo pipefail

rm -f "$HOME/.local/share/nautilus-python/extensions/libu_menu.py"
rm -f "$HOME/.local/share/nautilus/scripts/用吏部打开"

if command -v nautilus >/dev/null 2>&1; then
  nautilus -q >/dev/null 2>&1 || true
fi
echo "已移除吏部右键菜单。"
