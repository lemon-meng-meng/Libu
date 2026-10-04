# SPDX-License-Identifier: GPL-3.0-or-later
"""PaddleOCR-VL 多模态文档解析后端。

优先使用 paddlex / paddleocr 提供的 PaddleOCR-VL 流水线；
若不可用则回退到结构化版面解析，最终仍返回带坐标的行结果。
"""
from __future__ import annotations

from typing import List

from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL
from .registry import register_backend


@register_backend
class PaddleOCRVLBackend(BaseOCRBackend):
    name = "paddleocr_vl"
    label = "PaddleOCR-VL"
    category = CATEGORY_LOCAL
    provider = "百度 PaddleOCR-VL 0.9B"
    description = "0.9B 多模态文档解析模型，擅长复杂版面、表格、公式，输出结构化 Markdown/JSON。"
    url = "https://huggingface.co/PaddlePaddle/PaddleOCR-VL-0.9B"
    requires = ["paddleocr[doc-parser]", "paddlepaddle"]
    parser = True

    def __init__(self, **options):
        super().__init__(**options)
        self.pipeline = None
        try:
            from paddlex import create_pipeline  # type: ignore

            self.pipeline = create_pipeline("PaddleOCR-VL")
        except Exception:
            try:
                from paddleocr import PaddleOCRVL  # type: ignore

                self.pipeline = PaddleOCRVL()
            except Exception as exc:  # noqa: BLE001
                self._init_error = str(exc)

    @classmethod
    def available(cls):
        try:
            import paddleocr  # noqa: F401

            return True, "将尝试加载 PaddleOCR-VL 流水线"
        except ImportError:
            return False, "未安装 paddleocr / paddlex"

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        if self.pipeline is None:
            raise RuntimeError(
                "PaddleOCR-VL 未就绪，请安装 paddlepaddle + paddleocr[doc-parser]"
            )
        # 结果可能为 Markdown/JSON；提取带坐标的文本块
        try:
            outputs = self.pipeline.predict(str(image_path))
        except TypeError:
            outputs = self.pipeline(str(image_path))

        results: List[OCRResult] = []
        for out in outputs or []:
            data = getattr(out, "json", None) or {}
            if callable(data):
                data = data()
            # 常见字段：parsing_res_list / layout_det_res / rec_texts
            for block in data.get("parsing_res_list", []) or []:
                text = block.get("content") or block.get("text")
                bbox = block.get("bbox") or block.get("box")
                if text:
                    results.append(OCRResult(text=str(text), box=_rect(bbox), confidence=0.0))
            for text, box in zip(data.get("rec_texts", []) or [], data.get("rec_polys", []) or []):
                results.append(OCRResult(text=str(text), box=_rect(box), confidence=0.0))
        return results


def _rect(box):
    if not box:
        return None
    try:
        if isinstance(box, (list, tuple)) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box):
            return [float(v) for v in box]
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        return [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
    except Exception:
        return None
