# SPDX-License-Identifier: GPL-3.0-or-later
"""ModernVBERT 社区版后端。

ModernVBERT 是面向文档的视觉语言编码器（250M）。它本身偏检索/文档理解，
这里通过其视觉-语言接口做文本抽取；需要 transformers 与权重。
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
        if p.is_dir() and "vbert" in p.name.lower():
            return p
    return None


@register_backend
class ModernVBERTBackend(BaseOCRBackend):
    name = "modernvbert"
    label = "ModernVBERT (社区版)"
    category = CATEGORY_LOCAL
    provider = "ModernVBERT-250M"
    description = "250M 文档视觉语言模型，适合文档理解/抽取；需搭配 transformers 权重。"
    url = "https://huggingface.co/ModernVBERT/ModernVBERT-250M"
    requires = ["transformers", "torch", "权重文件"]

    @classmethod
    def available(cls):
        if _model_dir() is None:
            return False, "未在 ~/.libu/models 找到 ModernVBERT 权重"
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401

            return True, ""
        except ImportError:
            return False, "缺少 transformers/torch"

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        model_dir = _model_dir()
        if model_dir is None:
            raise RuntimeError("未找到 ModernVBERT 本地模型")
        from transformers import AutoProcessor, AutoModelForVision2Seq  # type: ignore
        from PIL import Image

        processor = AutoProcessor.from_pretrained(str(model_dir), trust_remote_code=True)
        model = AutoModelForVision2Seq.from_pretrained(str(model_dir), trust_remote_code=True)
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, text="OCR", return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=2048)
        text = processor.batch_decode(out, skip_special_tokens=True)[0]
        return plain_text_to_results(text, image_path, lang)
