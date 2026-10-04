# SPDX-License-Identifier: GPL-3.0-or-later
"""DeepSeek-OCR 本地/接口后端。

- 本地：若 ~/.libu/models 下有 DeepSeek-OCR 权重且安装了 transformers/torch，则本地推理；
- 接口：若无本地模型，则可通过 DeepSeek 兼容视觉接口调用（需 API Key）。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from ..config import MODEL_DIR
from ..settings import get_provider
from .base import BaseOCRBackend, OCRResult, CATEGORY_LLM, plain_text_to_results
from .registry import register_backend

_PROMPT = (
    "请对这张图片执行 OCR，识别全部中英文文本、表格与公式，"
    "按阅读顺序输出 Markdown，不要添加额外说明。"
)


def _local_model_dir() -> Path | None:
    if not MODEL_DIR.exists():
        return None
    for p in MODEL_DIR.iterdir():
        if p.is_dir() and "deepseek" in p.name.lower() and "ocr" in p.name.lower():
            return p
    return None


@register_backend
class DeepSeekOCRBackend(BaseOCRBackend):
    name = "deepseek_ocr"
    label = "DeepSeek-OCR"
    category = CATEGORY_LLM
    provider = "DeepSeek 开源端到端 OCR"
    local = True
    description = "端到端 OCR 大模型，支持中英文+表格+公式；可本地权重推理或走接口。"
    url = "https://github.com/deepseek-ai/DeepSeek-OCR"
    parser = True
    requires = ["transformers", "torch", "或 API Key"]

    @classmethod
    def available(cls):
        if _local_model_dir() is not None:
            try:
                import torch  # noqa: F401
                import transformers  # noqa: F401

                return True, "本地模型已就绪"
            except ImportError:
                return False, "已下载本地模型但缺少 torch/transformers"
        cfg = get_provider("deepseek") or {}
        if cfg.get("api_key"):
            return True, "将调用 DeepSeek 视觉接口"
        return False, "未找到本地模型，也未配置 DeepSeek API Key"

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        model_dir = _local_model_dir()
        if model_dir is not None:
            try:
                return self._recognize_local(model_dir, image_path, lang)
            except Exception:
                pass
        cfg = get_provider("deepseek") or {}
        if cfg.get("api_key"):
            from ..vision_client import openai_vision_ocr

            text = openai_vision_ocr(
                image_path,
                base_url=cfg.get("base_url") or "https://api.deepseek.com/v1",
                api_key=cfg["api_key"],
                model=cfg.get("model") or "deepseek-chat",
                prompt=_PROMPT,
            )
            return plain_text_to_results(text, image_path, lang)
        raise RuntimeError("DeepSeek-OCR 未就绪：请下载本地模型或配置 API Key")

    def _recognize_local(self, model_dir: Path, image_path, lang) -> List[OCRResult]:
        import torch  # type: ignore
        from transformers import AutoModel, AutoTokenizer  # type: ignore

        tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
        model = AutoModel.from_pretrained(
            str(model_dir), trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="auto"
        ).eval()
        prompt = "<image>\n<|grounding|>Convert the document to markdown."
        res = model.infer(tokenizer, prompt=prompt, image_file=str(image_path), output_path=None)
        text = res if isinstance(res, str) else str(res)
        return plain_text_to_results(text, image_path, lang)
