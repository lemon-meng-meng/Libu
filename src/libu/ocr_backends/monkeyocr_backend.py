# SPDX-License-Identifier: GPL-3.0-or-later
"""MonkeyOCR 本地后端。

MonkeyOCR 采用「结构识别 + 识别」两阶段方案。此处通过其 transformers
权重在本地推理；需要用户将权重导入 ~/.libu/models/MonkeyOCR。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from ..config import MODEL_DIR
from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL, plain_text_to_results
from .registry import register_backend


def _model_dir() -> Path | None:
    if not MODEL_DIR.exists():
        return None
    for p in MODEL_DIR.iterdir():
        if p.is_dir() and "monkey" in p.name.lower():
            return p
    return None


@register_backend
class MonkeyOCRBackend(BaseOCRBackend):
    name = "monkeyocr"
    label = "MonkeyOCR"
    category = CATEGORY_LOCAL
    provider = "MonkeyOCR"
    description = "结构识别 + 识别两阶段文档解析，擅长多栏排版与结构化输出。"
    url = "https://github.com/Yuliang-Liu/MonkeyOCR"
    parser = True
    requires = ["transformers", "torch", "MonkeyOCR 权重"]

    @classmethod
    def available(cls):
        if _model_dir() is None:
            return False, "未在 ~/.libu/models 找到 MonkeyOCR 权重"
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401

            return True, ""
        except ImportError:
            return False, "缺少 transformers/torch"

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        model_dir = _model_dir()
        if model_dir is None:
            raise RuntimeError("未找到 MonkeyOCR 本地模型")
        # MonkeyOCR 官方提供 ModelScope 推理脚本；此处调用其 transformers 接口
        from transformers import AutoProcessor, AutoModelForVision2Seq  # type: ignore
        from PIL import Image

        processor = AutoProcessor.from_pretrained(str(model_dir), trust_remote_code=True)
        model = AutoModelForVision2Seq.from_pretrained(str(model_dir), trust_remote_code=True)
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=4096)
        text = processor.batch_decode(out, skip_special_tokens=True)[0]
        return plain_text_to_results(text, image_path, lang)
