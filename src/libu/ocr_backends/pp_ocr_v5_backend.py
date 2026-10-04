# SPDX-License-Identifier: GPL-3.0-or-later
"""PP-OCRv5 本地后端（PaddleOCR 3.x 默认模型）。"""
from __future__ import annotations

from .base import CATEGORY_LOCAL
from .paddleocr_backend import _PaddleBase
from .registry import register_backend


@register_backend
class PPOCRv5Backend(_PaddleBase):
    name = "pp_ocr_v5"
    label = "PP-OCRv5"
    category = CATEGORY_LOCAL
    provider = "百度 PaddleOCR"
    description = "PaddleOCR 3.x 的 PP-OCRv5 通用模型，中文/英文/手写工整体表现优秀。"
    url = "https://github.com/PaddlePaddle/PaddleOCR"
    requires = ["paddleocr>=3", "paddlepaddle"]

    @classmethod
    def available(cls):
        try:
            import paddleocr  # noqa: F401

            return True, ""
        except ImportError:
            return False, "未安装 paddleocr"
