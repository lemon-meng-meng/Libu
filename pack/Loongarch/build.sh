#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · LoongArch（龙芯）一键打包：一次生成 deb 与 AppImage
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
ARCH="loongarch64"

echo "==> LoongArch 打包 ($ARCH)"
echo "提示：在龙芯原生环境（Loongnix / 龙芯 Debian）执行本脚本效果最佳。"

if [ "$(uname -m)" != "loongarch64" ] && [ "${LIBU_FORCE:-0}" != "1" ]; then
  echo "!! 当前架构为 $(uname -m)，非 loongarch64。"
  echo "   若仅需生成目录结构做交叉打包，请设置 LIBU_FORCE=1 后重试。"
  exit 1
fi

bash "$HERE/build-deb.sh"
bash "$HERE/build-appimage.sh"

echo "完成，产物位于 releases/"
ls -1 releases/ | grep -Ei "loongarch|${ARCH}" || true
