#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · 构建 Debian 安装包
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCH="${1:-amd64}"
VER="$(python3 -c "import re,pathlib;print(re.search(r'__version__ = \"([^\"]+)\"', pathlib.Path('src/libu/__init__.py').read_text()).group(1))")"
RELEASE_DIR="$ROOT/releases"
BUILD="$ROOT/build/deb"
PKG="$BUILD/libu_${VER}_${ARCH}"
INCLUDE_WECHAT="${LIBU_INCLUDE_WECHAT:-0}"

echo "==> 构建吏部 deb v$VER ($ARCH)"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" \
         "$PKG/opt/libu" \
         "$PKG/usr/bin" \
         "$PKG/usr/share/applications" \
         "$PKG/usr/share/icons/hicolor/256x256/apps" \
         "$RELEASE_DIR"

# 1) 构建前端
if [ -f src/frontend/package.json ]; then
  if [ ! -f src/frontend/dist/index.html ]; then
    if command -v npm >/dev/null 2>&1; then
      echo "==> 构建前端 (npm)"
      (cd src/frontend && npm install --no-audit --no-fund && npm run build)
    else
      echo "!! 未安装 npm，且 src/frontend/dist 不存在，跳过前端构建" >&2
    fi
  fi
fi

# 2) 复制程序文件
echo "==> 复制文件"
cp -r src "$PKG/opt/libu/src"
mkdir -p "$PKG/opt/libu/web"
if [ -d src/frontend/dist ]; then
  cp -r src/frontend/dist/. "$PKG/opt/libu/web/"
fi
# 清理不应打包的内容
rm -rf "$PKG/opt/libu/src/frontend/node_modules" \
       "$PKG/opt/libu/src/frontend/dist" \
       "$PKG/opt/libu/src/frontend/build"
find "$PKG/opt/libu/src" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
cp -r data "$PKG/opt/libu/data"
cp -r bin "$PKG/opt/libu/bin"
cp -r packaging "$PKG/opt/libu/packaging"
[ -d scripts ] && cp -r scripts "$PKG/opt/libu/scripts"
cp requirements.txt README.md LICENSE "$PKG/opt/libu/" 2>/dev/null || true
[ -f THIRD-PARTY-NOTICES.md ] && cp THIRD-PARTY-NOTICES.md "$PKG/opt/libu/"
mkdir -p "$PKG/opt/libu/OCR Model"
if [ "$INCLUDE_WECHAT" = "1" ] && [ -f "OCR Model/wechat_ocr.zip" ]; then
  cp "OCR Model/wechat_ocr.zip" "$PKG/opt/libu/OCR Model/"
fi
if [ "${LIBU_INCLUDE_PADDLE:-1}" = "1" ] && [ -f "OCR Model/paddleocr_ppocrv5.zip" ]; then
  cp "OCR Model/paddleocr_ppocrv5.zip" "$PKG/opt/libu/OCR Model/"
fi
[ -f "OCR Model/MODEL_DOWNLOADS.md" ] && cp "OCR Model/MODEL_DOWNLOADS.md" "$PKG/opt/libu/OCR Model/"

# 3) 构建自带虚拟环境（含运行依赖）
echo "==> 创建虚拟环境并安装依赖（需要网络）"
python3 -m venv "$PKG/opt/libu/venv"
"$PKG/opt/libu/venv/bin/pip" install --upgrade pip >/dev/null
"$PKG/opt/libu/venv/bin/pip" install -r requirements.txt

# 4) 启动器 / 桌面项 / 图标
install -m 0755 bin/libu "$PKG/usr/bin/libu"
install -m 0755 bin/libu-app "$PKG/usr/bin/libu-app"
install -m 0644 packaging/libu.desktop "$PKG/usr/share/applications/libu.desktop"
install -m 0644 data/icons/libu_256.png \
  "$PKG/usr/share/icons/hicolor/256x256/apps/libu.png"

# 5) 控制信息
SIZE="$(du -sk "$PKG" | cut -f1)"
cat > "$PKG/DEBIAN/control" <<EOF
Package: libu
Version: $VER
Section: graphics
Priority: optional
Architecture: $ARCH
Maintainer: lemon-meng-meng <https://github.com/lemon-meng-meng/Libu>
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1
Recommends: tesseract-ocr, tesseract-ocr-chi-sim, gir1.2-appindicator3-0.1, python3-xlib, gir1.2-keybinder-3.0
Description: 吏部 Libu - 图片转电子文档工具
 将图片 / 扫描件转换为可搜索的双层 PDF 与 Word。
 支持多种本地 OCR 模型、在线 OCR 与大模型 API。
Installed-Size: $SIZE
Homepage: https://github.com/lemon-meng-meng/Libu
License: GPL-3.0-or-later
EOF

cat > "$PKG/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ -x /usr/bin/gtk-update-icon-cache ] && [ -d /usr/share/icons/hicolor ]; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
echo "吏部已安装。可执行 libu-app 启动，处理结果保存在 ~/文档/吏部"
exit 0
EOF
chmod 0755 "$PKG/DEBIAN/postinst"

echo "==> 打包"
dpkg-deb --build --root-owner-group "$PKG" "$RELEASE_DIR/libu_${VER}_${ARCH}.deb"
echo "完成：$RELEASE_DIR/libu_${VER}_${ARCH}.deb"
