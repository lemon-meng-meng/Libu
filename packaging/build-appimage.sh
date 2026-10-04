#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · 构建 AppImage
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCH="${1:-x86_64}"
VER="$(python3 -c "import re,pathlib;print(re.search(r'__version__ = \"([^\"]+)\"', pathlib.Path('src/libu/__init__.py').read_text()).group(1))")"
RELEASE_DIR="$ROOT/releases"
APPDIR="$ROOT/build/libu.AppDir"
TOOL="${APPIMAGETOOL:-/tmp/appimagetool.AppImage}"
INCLUDE_WECHAT="${LIBU_INCLUDE_WECHAT:-0}"

echo "==> 构建吏部 AppImage v$VER ($ARCH)"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/libu" "$APPDIR/usr/bin" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$RELEASE_DIR"

# 构建前端
if [ ! -f src/frontend/dist/index.html ] && command -v npm >/dev/null 2>&1; then
  echo "==> 构建前端"
  (cd src/frontend && npm install --no-audit --no-fund && npm run build)
fi

echo "==> 复制程序文件"
cp -r src "$APPDIR/usr/lib/libu/src"
mkdir -p "$APPDIR/usr/lib/libu/web"
[ -d src/frontend/dist ] && cp -r src/frontend/dist/. "$APPDIR/usr/lib/libu/web/"
rm -rf "$APPDIR/usr/lib/libu/src/frontend/node_modules" \
       "$APPDIR/usr/lib/libu/src/frontend/dist" \
       "$APPDIR/usr/lib/libu/src/frontend/build"
find "$APPDIR/usr/lib/libu/src" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
cp -r data "$APPDIR/usr/lib/libu/data"
cp -r bin "$APPDIR/usr/lib/libu/bin"
[ -d scripts ] && cp -r scripts "$APPDIR/usr/lib/libu/scripts"
cp requirements.txt README.md LICENSE "$APPDIR/usr/lib/libu/" 2>/dev/null || true
[ -f THIRD-PARTY-NOTICES.md ] && cp THIRD-PARTY-NOTICES.md "$APPDIR/usr/lib/libu/"
mkdir -p "$APPDIR/usr/lib/libu/OCR Model"
if [ "$INCLUDE_WECHAT" = "1" ] && [ -f "OCR Model/wechat_ocr.zip" ]; then
  cp "OCR Model/wechat_ocr.zip" "$APPDIR/usr/lib/libu/OCR Model/"
fi
if [ "${LIBU_INCLUDE_PADDLE:-1}" = "1" ] && [ -f "OCR Model/paddleocr_ppocrv5.zip" ]; then
  cp "OCR Model/paddleocr_ppocrv5.zip" "$APPDIR/usr/lib/libu/OCR Model/"
fi
[ -f "OCR Model/MODEL_DOWNLOADS.md" ] && cp "OCR Model/MODEL_DOWNLOADS.md" "$APPDIR/usr/lib/libu/OCR Model/"

echo "==> 准备虚拟环境"
REUSE_VENV="$ROOT/build/deb/libu_${VER}_amd64/opt/libu/venv"
if [ -d "$REUSE_VENV" ]; then
  echo "    复用 deb 构建的虚拟环境"
  cp -a "$REUSE_VENV" "$APPDIR/usr/lib/libu/venv"
else
  python3 -m venv "$APPDIR/usr/lib/libu/venv"
  "$APPDIR/usr/lib/libu/venv/bin/pip" install --upgrade pip >/dev/null
  "$APPDIR/usr/lib/libu/venv/bin/pip" install -r requirements.txt
fi

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
export LIBU_WEB_DIR="$HERE/usr/lib/libu/web"
export PYTHONPATH="$HERE/usr/lib/libu/src${PYTHONPATH:+:$PYTHONPATH}"
export LIBU_PYTHON="$HERE/usr/lib/libu/venv/bin/python"
exec "$HERE/usr/lib/libu/bin/libu" "$@"
EOF
chmod 0755 "$APPDIR/AppRun"

install -m 0644 packaging/libu.desktop "$APPDIR/libu.desktop"
install -m 0644 packaging/libu.desktop "$APPDIR/usr/share/applications/libu.desktop"
install -m 0644 data/icons/libu_256.png "$APPDIR/libu.png"
install -m 0644 data/icons/libu_256.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/libu.png"

OUT="$RELEASE_DIR/libu-${ARCH}.AppImage"

build_with_appimagetool() {
  if [ ! -x "$TOOL" ]; then
    echo "==> 下载 appimagetool"
    curl -fL -o "$TOOL" \
      "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" || return 1
    chmod +x "$TOOL"
  fi
  ARCH="$ARCH" "$TOOL" "$APPDIR" "$OUT"
}

build_manual() {
  # 无 appimagetool 时，使用 type2 runtime + mksquashfs 手动组装
  local RUNTIME="${APPIMAGE_RUNTIME:-$ROOT/build/runtime-${ARCH}}"
  if [ ! -f "$RUNTIME" ]; then
    echo "==> 下载 AppImage type2 runtime"
    curl -fL -o "$RUNTIME" \
      "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${ARCH}"
  fi
  command -v mksquashfs >/dev/null 2>&1 || {
    echo "!! 未找到 mksquashfs，无法手动生成 AppImage" >&2
    return 1
  }
  echo "==> mksquashfs 打包 AppDir"
  rm -f "$ROOT/build/libu.squashfs"
  mksquashfs "$APPDIR" "$ROOT/build/libu.squashfs" -root-owned -noappend -comp zstd -b 262144 >/dev/null
  echo "==> 拼接 runtime + squashfs"
  cat "$RUNTIME" "$ROOT/build/libu.squashfs" > "$OUT"
  chmod 0755 "$OUT"
}

echo "==> 生成 AppImage"
if [ -n "${APPIMAGETOOL:-}" ] && [ -x "${APPIMAGETOOL:-}" ]; then
  build_with_appimagetool
elif command -v mksquashfs >/dev/null 2>&1; then
  echo "    使用 type2 runtime + mksquashfs 组装（无需 appimagetool）"
  build_manual
else
  echo "    mksquashfs 不可用，尝试 appimagetool"
  build_with_appimagetool
fi
echo "完成：$OUT"
