# SPDX-License-Identifier: GPL-3.0-or-later
"""自定义本地模型后端。

支持：
1. RapidOCR（onnxruntime）作为开箱即用的 ONNX 推理引擎；
2. 用户在 ~/.libu/models/ 放置 PP-OCR 导出的 det/cls/rec ONNX 模型后自动加载。

约定：模型目录内文件名包含 `det`、`rec`、`cls` 关键字即可被识别。
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..config import MODEL_DIR
from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL
from .registry import register_backend


def _find_user_models():
    det = rec = cls = keys = None
    if not MODEL_DIR.exists():
        return det, rec, cls, keys
    for p in MODEL_DIR.rglob("*.onnx"):
        name = p.name.lower()
        if "det" in name and det is None:
            det = p
        elif ("rec" in name or "v4" in name or "v5" in name) and rec is None:
            rec = p
        elif "cls" in name and cls is None:
            cls = p
    # 识别字典（PP-OCRv5 与 v4 的字符集不同，必须配套）
    for pat in ("*dict*.txt", "*keys*.txt", "*charset*.txt"):
        for p in MODEL_DIR.rglob(pat):
            keys = p
            break
        if keys:
            break
    return det, rec, cls, keys


@register_backend
class CustomLocalBackend(BaseOCRBackend):
    name = "custom_local"
    label = "自定义本地模型 (ONNX)"
    category = CATEGORY_LOCAL
    provider = "RapidOCR / 用户导入模型"
    description = "基于 onnxruntime 的离线推理，可自动加载 ~/.libu/models 内用户导入的 det/rec ONNX 模型。"
    url = "https://github.com/RapidAI/RapidOCR"
    requires = ["rapidocr-onnxruntime", "onnxruntime"]

    @classmethod
    def available(cls):
        try:
            import rapidocr_onnxruntime  # noqa: F401

            return True, ""
        except ImportError:
            return False, "未安装 rapidocr-onnxruntime"

    def __init__(self, **options):
        super().__init__(**options)
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        det, rec, cls, keys = _find_user_models()
        kwargs = {}
        if det:
            kwargs["det_model_path"] = str(det)
        if rec:
            kwargs["rec_model_path"] = str(rec)
        if cls:
            kwargs["cls_model_path"] = str(cls)
        if keys:
            kwargs["rec_keys_path"] = str(keys)
        self.engine = RapidOCR(**kwargs)

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        result, _ = self.engine(str(image_path))
        results: List[OCRResult] = []
        for line in result or []:
            try:
                box, text, conf = line
            except (ValueError, TypeError):
                continue
            rect = None
            try:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                rect = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
            except Exception:
                rect = None
            results.append(OCRResult(text=str(text), box=rect, confidence=float(conf)))
        return results
