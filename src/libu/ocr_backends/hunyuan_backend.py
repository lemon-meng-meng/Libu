# SPDX-License-Identifier: GPL-3.0-or-later
"""腾讯混元 OCR 后端。

通过混元 OpenAI 兼容接口或本地 transformers 推理调用。
未配置时给出明确提示，不影响其它引擎。
"""
from __future__ import annotations

from typing import List

from ..settings import get_provider
from .base import BaseOCRBackend, OCRResult, CATEGORY_LLM, plain_text_to_results
from .registry import register_backend


@register_backend
class HunyuanOCRBackend(BaseOCRBackend):
    name = "hunyuan"
    label = "腾讯混元 OCR"
    category = CATEGORY_LLM
    provider = "腾讯混元"
    local = False
    description = "腾讯混元 OCR / 多模态接口，中文文档与表格表现好；需填写 API Key。"
    url = "https://github.com/Tencent-Hunyuan/HunyuanOCR"
    requires = ["api_key"]

    @classmethod
    def available(cls):
        cfg = get_provider("hunyuan") or {}
        if not cfg.get("api_key"):
            return False, "未配置混元 API Key"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        from ..vision_client import openai_vision_ocr

        cfg = get_provider("hunyuan") or {}
        base_url = cfg.get("base_url") or "https://api.hunyuan.cloud.tencent.com/v1"
        model = cfg.get("model") or "hunyuan-vision"
        text = openai_vision_ocr(
            image_path,
            base_url=base_url,
            api_key=cfg.get("api_key", ""),
            model=model,
            prompt=_PROMPT,
        )
        return plain_text_to_results(text, image_path, lang)


_PROMPT = (
    "请对这张文档图片做 OCR。逐行输出识别到的文字，保持原有阅读顺序，"
    "不要添加任何解释。只输出纯文本。"
)
