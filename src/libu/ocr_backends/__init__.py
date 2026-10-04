# SPDX-License-Identifier: GPL-3.0-or-later
"""OCR 后端包：本地模型 / 在线 API / 大模型 / Agent 四类引擎。"""
from .base import (  # noqa: F401
    BaseOCRBackend,
    OCRResult,
    BackendMeta,
    CATEGORY_AGENT,
    CATEGORY_CLOUD,
    CATEGORY_LLM,
    CATEGORY_LOCAL,
    CATEGORY_LABELS,
    plain_text_to_results,
)
from .registry import (  # noqa: F401
    BACKENDS,
    get_backend,
    list_backends,
    register_backend,
)

__all__ = [
    "BaseOCRBackend",
    "OCRResult",
    "BackendMeta",
    "CATEGORY_LOCAL",
    "CATEGORY_CLOUD",
    "CATEGORY_LLM",
    "CATEGORY_AGENT",
    "CATEGORY_LABELS",
    "plain_text_to_results",
    "BACKENDS",
    "get_backend",
    "list_backends",
    "register_backend",
]
