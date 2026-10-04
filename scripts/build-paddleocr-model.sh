#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · 构建可导入的 PaddleOCR（PP-OCRv5）ONNX 模型压缩包
#
# 产物：OCR Model/paddleocr_ppocrv5.zip
# 该 zip 可直接在软件「设置 → 本地 OCR 模型 → 导入模型 zip」中导入，
# 之后选择本地引擎「自定义本地模型 (ONNX)」即可离线识别。
#
# 依赖：curl、zip。模型来自 Hugging Face 镜像（bukuroo/PPOCRv5-ONNX）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/OCR Model"
STAGE="${TMPDIR:-/tmp}/paddleocr_ppocrv5"
BASE="${LIBU_PADDLE_MODEL_BASE:-https://hf-mirror.com/bukuroo/PPOCRv5-ONNX/resolve/main}"

echo "==> 下载 PP-OCRv5 ONNX 模型（mobile det / rec / cls + 字典）"
rm -rf "$STAGE"
mkdir -p "$STAGE"
for f in ppocrv5-mobile-det.onnx ppocrv5-mobile-rec.onnx ppocrv5-cls.onnx ppocrv5_dict.txt; do
  echo "    - $f"
  curl -fL --retry 3 --connect-timeout 20 -o "$STAGE/$f" "$BASE/$f"
done

echo "==> 打包"
mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR/paddleocr_ppocrv5.zip"
( cd "$(dirname "$STAGE")" && zip -r -q "$OUT_DIR/paddleocr_ppocrv5.zip" "$(basename "$STAGE")" )
echo "完成：$OUT_DIR/paddleocr_ppocrv5.zip"
