# SPDX-License-Identifier: GPL-3.0-or-later
"""Tesseract 本地 OCR 后端（保底引擎，支持 hOCR 坐标）。"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL
from .registry import register_backend

try:
    import pytesseract  # type: ignore
except ImportError:  # pragma: no cover
    pytesseract = None


@register_backend
class TesseractBackend(BaseOCRBackend):
    name = "tesseract"
    label = "Tesseract"
    category = CATEGORY_LOCAL
    provider = "Tesseract OCR"
    description = "开源保底引擎，零 GPU，支持 100+ 语言；中文/手写一般，但坐标最稳定。"
    url = "https://github.com/tesseract-ocr/tesseract"
    requires = ["pytesseract", "tesseract-ocr", "tesseract-ocr-chi-sim"]

    @classmethod
    def available(cls):
        if pytesseract is None:
            return False, "未安装 pytesseract"
        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:  # noqa: BLE001
            return False, f"未找到 tesseract 可执行文件：{exc}"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        lang = (lang or "chi_sim+eng").replace("+", "+")
        data = pytesseract.image_to_data(
            str(image_path), lang=lang, output_type=pytesseract.Output.DICT
        )
        # 按 (block, par, line) 聚合成行
        lines: dict[tuple, dict] = {}
        n = len(data.get("text", []))
        for i in range(n):
            word = (data["text"][i] or "").strip()
            if not word:
                continue
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1
            if conf < 0:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            entry = lines.setdefault(key, {"words": [], "x0": x, "y0": y, "x1": x + w, "y1": y + h, "conf": []})
            entry["words"].append(word)
            entry["x0"] = min(entry["x0"], x)
            entry["y0"] = min(entry["y0"], y)
            entry["x1"] = max(entry["x1"], x + w)
            entry["y1"] = max(entry["y1"], y + h)
            entry["conf"].append(conf)

        results: List[OCRResult] = []
        for key in sorted(lines):
            e = lines[key]
            avg = sum(e["conf"]) / max(1, len(e["conf"]))
            results.append(
                OCRResult(
                    text="".join(e["words"]),
                    box=[e["x0"], e["y0"], e["x1"], e["y1"]],
                    confidence=avg / 100.0,
                )
            )
        return results
