# SPDX-License-Identifier: GPL-3.0-or-later
"""PaddleOCR 本地后端（兼容 PaddleOCR 2.x / 3.x 两套 API）。"""
from __future__ import annotations

from typing import List

from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL
from .registry import register_backend


def _extract_line_from_result(res) -> list:
    """把不同版本 PaddleOCR 的返回统一成 [[box, (text, conf)], ...]。"""
    items = []
    if res is None:
        return items
    # 3.x: res 是对象，含 json / 属性
    if hasattr(res, "json") and res.json:
        data = res.json
        if callable(data):
            data = data()
        texts = data.get("rec_texts") or data.get("texts") or []
        scores = data.get("rec_scores") or data.get("scores") or []
        polys = data.get("rec_polys") or data.get("dt_polys") or data.get("boxes") or []
        for i, text in enumerate(texts):
            box = polys[i] if i < len(polys) else None
            conf = float(scores[i]) if i < len(scores) else 0.0
            items.append([box, (text, conf)])
        return items
    # 2.x: [[box, (text, conf)], ...]
    if isinstance(res, list):
        for line in res:
            if isinstance(line, (list, tuple)) and len(line) == 2 and isinstance(line[1], (list, tuple)):
                items.append([line[0], (line[1][0], float(line[1][1]))])
    return items


def _poly_to_box(poly):
    if poly is None:
        return None
    try:
        if hasattr(poly, "tolist"):
            poly = poly.tolist()
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
    except Exception:
        return None


class _PaddleBase(BaseOCRBackend):
    lang_code = "ch"

    def _build(self, **kwargs):
        from paddleocr import PaddleOCR  # type: ignore

        attempts = [
            lambda: PaddleOCR(**kwargs, lang=self.lang_code, use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False),
            lambda: PaddleOCR(**kwargs, lang=self.lang_code, use_angle_cls=False, show_log=False),
            lambda: PaddleOCR(**kwargs, lang=self.lang_code),
        ]
        last = None
        for attempt in attempts:
            try:
                return attempt()
            except Exception as exc:  # noqa: BLE001
                last = exc
        raise RuntimeError(f"PaddleOCR 初始化失败：{last}")

    def __init__(self, **options):
        super().__init__(**options)
        self.ocr = self._build()

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        output = None
        try:
            output = self.ocr.predict(str(image_path))
        except (AttributeError, TypeError):
            try:
                output = self.ocr.ocr(str(image_path))
            except TypeError:
                output = self.ocr.ocr(str(image_path), cls=False)

        if output is None:
            return []
        if not isinstance(output, list):
            output = [output]

        results: List[OCRResult] = []
        for res in output:
            for box, (text, conf) in _extract_line_from_result(res):
                rect = _poly_to_box(box)
                if not text:
                    continue
                results.append(OCRResult(text=str(text), box=rect, confidence=float(conf)))
        return results


@register_backend
class PaddleOCRBackend(_PaddleBase):
    name = "paddleocr"
    label = "PaddleOCR"
    category = CATEGORY_LOCAL
    provider = "百度 PaddleOCR"
    description = "中文识别最强开源引擎之一，CPU 可跑，自带检测+识别坐标。"
    url = "https://github.com/PaddlePaddle/PaddleOCR"
    requires = ["paddleocr", "paddlepaddle"]

    @classmethod
    def available(cls):
        try:
            import paddleocr  # noqa: F401

            return True, ""
        except ImportError:
            return False, "未安装 paddleocr"
