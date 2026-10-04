# SPDX-License-Identifier: GPL-3.0-or-later
"""Agent / 本地 AI 助手 OCR 后端。

支持连接：OpenCode、DeepSeek Harness、Claude Code、Codex、Cherry Studio、
Ollama、LM Studio。通过其本地 HTTP 接口把图片交给本地模型识别。
"""
from __future__ import annotations

import base64

import requests

from ..settings import get_provider
from ..vision_client import openai_vision_ocr
from .base import BaseOCRBackend, OCRResult, CATEGORY_AGENT, plain_text_to_results
from .registry import register_backend

_PROMPT = "请识别这张文档图片中的全部文字，保持阅读顺序，只输出文本。"


class _AgentBackend(BaseOCRBackend):
    category = CATEGORY_AGENT
    provider_key = ""
    requires = ["本地服务地址"]

    @classmethod
    def available(cls):
        cfg = get_provider(cls.provider_key) or {}
        if not cfg.get("enabled"):
            return False, "未启用"
        if not cfg.get("base_url"):
            return False, "未配置本地服务地址"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider(self.provider_key) or {}
        base_url = (cfg.get("base_url") or "").strip()
        if not base_url:
            raise RuntimeError(f"{self.label} 未配置服务地址")
        model = (cfg.get("model") or "").strip()
        if not model:
            models = cfg.get("models") or []
            model = models[0] if models else "local-model"
        text = openai_vision_ocr(
            image_path,
            base_url=base_url,
            api_key=cfg.get("api_key", "") or "not-needed",
            model=model,
            prompt=_PROMPT,
        )
        return plain_text_to_results(text, image_path, lang)


@register_backend
class OpenCodeBackend(_AgentBackend):
    name = "opencode"
    label = "OpenCode"
    provider = "OpenCode"
    provider_key = "opencode"
    description = "连接本地 OpenCode 服务的对话接口。"
    url = "https://opencode.ai/"


@register_backend
class DeepSeekHarnessBackend(_AgentBackend):
    name = "deepseek_harness"
    label = "DeepSeek Harness"
    provider = "DeepSeek Harness"
    provider_key = "deepseek_harness"
    description = "连接本地 DeepSeek Harness 服务。"
    url = "https://github.com/deepseek-ai"


@register_backend
class ClaudeCodeBackend(_AgentBackend):
    name = "claude_code"
    label = "Claude Code"
    provider = "Anthropic Claude Code"
    provider_key = "claude_code"
    description = "连接本地 Claude Code 服务。"
    url = "https://docs.anthropic.com/en/docs/claude-code"


@register_backend
class CodexBackend(_AgentBackend):
    name = "codex"
    label = "Codex"
    provider = "OpenAI Codex"
    provider_key = "codex"
    description = "连接本地 Codex 服务。"
    url = "https://openai.com/codex/"


@register_backend
class CherryStudioBackend(_AgentBackend):
    name = "cherry_studio"
    label = "Cherry Studio"
    provider = "Cherry Studio"
    provider_key = "cherry_studio"
    description = "连接本地 Cherry Studio 的接口。"
    url = "https://cherry-ai.com/"


@register_backend
class LMStudioBackend(_AgentBackend):
    name = "lmstudio"
    label = "LM Studio"
    provider = "LM Studio"
    provider_key = "lmstudio"
    description = "连接 LM Studio 的 OpenAI 兼容本地服务（默认 :1234）。"
    url = "https://lmstudio.ai/"


@register_backend
class OllamaBackend(BaseOCRBackend):
    name = "ollama"
    label = "Ollama"
    category = CATEGORY_AGENT
    provider = "Ollama"
    provider_key = "ollama"
    description = "连接本地 Ollama（默认 :11434），使用支持视觉的模型如 llava / llama3.2-vision。"
    url = "https://ollama.com/"
    requires = ["本地服务地址", "视觉模型"]

    @classmethod
    def available(cls):
        cfg = get_provider("ollama") or {}
        if not cfg.get("enabled"):
            return False, "未启用"
        if not cfg.get("base_url"):
            return False, "未配置 Ollama 地址"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider("ollama") or {}
        base = (cfg.get("base_url") or "http://localhost:11434").strip().rstrip("/")
        # 允许填写 http://host:11434/v1 的 OpenAI 兼容地址
        if base.endswith("/v1"):
            base = base[:-3].rstrip("/")
        model = (cfg.get("model") or "").strip()
        if not model:
            models = cfg.get("models") or []
            model = models[0] if models else "llama3.2-vision"
        with open(image_path, "rb") as fh:
            img_b64 = base64.b64encode(fh.read()).decode("ascii")
        try:
            resp = requests.post(
                f"{base}/api/generate",
                json={"model": model, "prompt": _PROMPT, "images": [img_b64], "stream": False},
                timeout=300,
            )
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"无法连接 Ollama：{base}\n请确认 Ollama 已启动（ollama serve），"
                f"且端口正确（默认 11434）。原始错误：{exc}"
            ) from exc
        if resp.status_code >= 400:
            raise RuntimeError(f"Ollama 错误 {resp.status_code}: {resp.text[:200]}")
        text = resp.json().get("response", "")
        return plain_text_to_results(text, image_path, lang)
