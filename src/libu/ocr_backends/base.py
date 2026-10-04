# SPDX-License-Identifier: GPL-3.0-or-later
"""OCR 后端统一接口与元数据。

所有后端必须实现 `recognize(image_path, lang) -> List[OCRResult]`。
为支持"隐形文字精确覆盖"，本地结构化引擎应尽量返回带坐标的结果；
大模型 / Agent 类引擎若无法给出坐标，可返回无坐标结果，此时 PDF 将退化为
整页文字层，而 Word 纯文本模式不受影响。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# 引擎类别
CATEGORY_LOCAL = "local"
CATEGORY_CLOUD = "cloud"
CATEGORY_LLM = "llm"
CATEGORY_AGENT = "agent"

CATEGORY_LABELS = {
    CATEGORY_LOCAL: "本地模型",
    CATEGORY_CLOUD: "在线 OCR 引擎",
    CATEGORY_LLM: "大模型 API",
    CATEGORY_AGENT: "Agent / 本地 AI 助手",
}


@dataclass
class OCRResult:
    text: str
    box: Optional[List[float]] = None  # [x0, y0, x1, y1]，可为 None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {"text": self.text, "box": self.box, "confidence": self.confidence}


@dataclass
class BackendMeta:
    name: str
    label: str
    category: str
    provider: str = ""
    local: bool = True
    description: str = ""
    url: str = ""
    requires: List[str] = field(default_factory=list)
    parser: bool = False  # 是否支持版面/表格解析


class BaseOCRBackend:
    name: str = "base"
    label: str = "Base"
    category: str = CATEGORY_LOCAL
    provider: str = ""
    local: bool = True
    description: str = ""
    url: str = ""
    requires: List[str] = []
    parser: bool = False

    def __init__(self, **options):
        self.options = options

    # -- 可用性 ---------------------------------------------------------- #
    @classmethod
    def available(cls) -> tuple[bool, str]:
        return True, ""

    # -- 核心 ------------------------------------------------------------ #
    def recognize(self, image_path: str | Path, lang: str = "chi_sim+eng") -> List[OCRResult]:
        raise NotImplementedError

    # -- 元数据 ---------------------------------------------------------- #
    @classmethod
    def meta(cls) -> BackendMeta:
        ok, reason = cls.available()
        return BackendMeta(
            name=cls.name,
            label=cls.label,
            category=cls.category,
            provider=cls.provider or cls.label,
            local=cls.local,
            description=cls.description,
            url=cls.url,
            requires=list(cls.requires),
            parser=cls.parser,
        )


def image_size(image_path: str | Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(image_path) as im:
            return im.size
    except Exception:
        return (1000, 1414)


def plain_text_to_results(text: str, image_path: str | Path, lang: str = "") -> List[OCRResult]:
    """把无坐标的纯文本按行均匀铺满页面，生成伪坐标。

    用于大模型 / Agent 引擎：虽然没有真实坐标，仍可输出可搜索 PDF 与 Word。
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []
    w, h = image_size(image_path)
    results: List[OCRResult] = []
    line_h = h / (len(lines) + 0.5)
    for i, line in enumerate(lines):
        y0 = i * line_h
        results.append(
            OCRResult(
                text=line,
                box=[w * 0.05, y0, w * 0.95, y0 + line_h * 0.9],
                confidence=0.0,
            )
        )
    return results
