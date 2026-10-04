# SPDX-License-Identifier: GPL-3.0-or-later
"""大模型 API OCR 后端（OpenAI 兼容视觉接口）。

支持：DeepSeek、GLM、Kimi、MiniMax、阶跃星辰、Qwen、零一万物、英伟达、OpenAI。
这些引擎通常无法给出精确坐标，会自动把文本按行铺回页面，保证可搜索/可复制。
"""
from __future__ import annotations

from typing import List

from ..settings import get_provider
from ..vision_client import openai_vision_ocr_with_boxes
from .base import BaseOCRBackend, OCRResult, CATEGORY_LLM
from .registry import register_backend

_PROMPT = (
    "请对这张文档图片做 OCR，识别全部文字（含中英文、数字、标点），"
    "保持阅读顺序，不要解释。"
)


class _LLMVisionBackend(BaseOCRBackend):
    category = CATEGORY_LLM
    local = False
    provider_key = ""
    requires = ["api_key"]
    use_boxes = True

    @classmethod
    def available(cls):
        cfg = get_provider(cls.provider_key) or {}
        if not cfg.get("api_key"):
            return False, f"未配置 {cls.label} API Key"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider(self.provider_key) or {}
        model = (cfg.get("model") or "").strip()
        if not model:
            models = cfg.get("models") or []
            model = models[0] if models else ""
        base_url = (cfg.get("base_url") or "").strip()
        if not base_url:
            raise RuntimeError(f"{self.label} 未配置服务地址")
        return openai_vision_ocr_with_boxes(
            image_path,
            base_url=base_url,
            api_key=cfg.get("api_key", ""),
            model=model,
        )


@register_backend
class DeepSeekLLMBackend(_LLMVisionBackend):
    name = "deepseek"
    label = "DeepSeek"
    provider = "DeepSeek"
    provider_key = "deepseek"
    description = "DeepSeek 大模型视觉接口，中文理解强。"
    url = "https://www.deepseek.com/"


@register_backend
class GLMBackend(_LLMVisionBackend):
    name = "glm"
    label = "智谱 GLM"
    provider = "智谱 AI"
    provider_key = "glm"
    description = "GLM-4V 系列，中文文档与图表理解好。"
    url = "https://open.bigmodel.cn/"


@register_backend
class KimiBackend(_LLMVisionBackend):
    name = "kimi"
    label = "Kimi (月之暗面)"
    provider = "Moonshot AI"
    provider_key = "kimi"
    description = "Kimi 视觉模型，长文档友好。"
    url = "https://www.moonshot.cn/"


@register_backend
class MiniMaxBackend(_LLMVisionBackend):
    name = "minimax"
    label = "MiniMax"
    provider = "MiniMax"
    provider_key = "minimax"
    description = "MiniMax 多模态接口。"
    url = "https://www.minimaxi.com/"


@register_backend
class StepFunBackend(_LLMVisionBackend):
    name = "stepfun"
    label = "阶跃星辰"
    provider = "StepFun"
    provider_key = "stepfun"
    description = "阶跃星辰 Step-1V 视觉模型。"
    url = "https://www.stepfun.com/"


@register_backend
class QwenBackend(_LLMVisionBackend):
    name = "qwen"
    label = "通义千问 Qwen"
    provider = "阿里云"
    provider_key = "qwen"
    description = "Qwen-VL 系列，中文 OCR 与版面理解强。"
    url = "https://dashscope.aliyun.com/"


@register_backend
class YiBackend(_LLMVisionBackend):
    name = "yi"
    label = "零一万物 Yi"
    provider = "零一万物"
    provider_key = "yi"
    description = "Yi-Vision 多模态模型。"
    url = "https://www.lingyiwanwu.com/"


@register_backend
class NvidiaBackend(_LLMVisionBackend):
    name = "nvidia"
    label = "英伟达 NIM"
    provider = "NVIDIA"
    provider_key = "nvidia"
    description = "NVIDIA NIM 视觉模型接口（Llama 3.2 Vision 等）。"
    url = "https://build.nvidia.com/"
