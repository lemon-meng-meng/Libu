# SPDX-License-Identifier: GPL-3.0-or-later
"""OCR 后端注册表与发现。"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Type

from .base import BaseOCRBackend, BackendMeta, CATEGORY_LABELS

BACKENDS: Dict[str, Type[BaseOCRBackend]] = {}

_MODULES = [
    "tesseract_backend",
    "paddleocr_backend",
    "pp_ocr_v5_backend",
    "paddleocr_vl_backend",
    "wechat_backend",
    "custom_local_backend",
    "hunyuan_backend",
    "modernvbert_backend",
    "monkeyocr_backend",
    "deepseek_ocr_backend",
    "cloud_backends",
    "llm_backends",
    "agent_backends",
]

_loaded = False


def register_backend(cls: Type[BaseOCRBackend]) -> Type[BaseOCRBackend]:
    BACKENDS[cls.name] = cls
    return cls


def _load() -> None:
    global _loaded
    if _loaded:
        return
    for mod in _MODULES:
        try:
            importlib.import_module(f"{__package__}.{mod}")
        except Exception as exc:  # noqa: BLE001
            # 单个引擎导入失败不应影响其它引擎
            import logging

            logging.getLogger("libu.ocr").warning("引擎模块 %s 加载失败: %s", mod, exc)
    _loaded = True


def get_backend(name: str, **options) -> BaseOCRBackend:
    _load()
    cls = BACKENDS.get(name)
    if not cls:
        raise ValueError(f"未知 OCR 引擎：{name}")
    return cls(**options)


def list_backends() -> List[dict]:
    _load()
    out = []
    for cls in BACKENDS.values():
        meta: BackendMeta = cls.meta()
        ok, reason = cls.available()
        item = meta.__dict__.copy()
        item["available"] = ok
        item["unavailable_reason"] = reason
        item["category_label"] = CATEGORY_LABELS.get(meta.category, meta.category)
        out.append(item)
    order = {"local": 0, "cloud": 1, "llm": 2, "agent": 3}
    out.sort(key=lambda x: (order.get(x["category"], 9), x["label"]))
    return out


__all__ = [
    "BACKENDS",
    "register_backend",
    "get_backend",
    "list_backends",
    "BaseOCRBackend",
    "BackendMeta",
]
