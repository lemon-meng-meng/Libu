# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenAI 兼容的视觉大模型调用工具。

统一封装「图片 + 提示词 -> 文本」与「图片 + 提示词 -> 带坐标行」两种调用，
供混元、DeepSeek、GLM、Kimi、MiniMax、阶跃、Qwen、零一万物、英伟达等使用。
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests

from .ocr_backends.base import OCRResult, image_size, plain_text_to_results

DEFAULT_TIMEOUT = 180


def _data_url(image_path: str | Path) -> str:
    path = Path(image_path)
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _headers(api_key: str) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    # 去掉首尾空白，避免复制 API Key 时带入换行/空格导致 401
    key = (api_key or "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def openai_vision_ocr(
    image_path: str | Path,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """返回模型输出的纯文本。"""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _data_url(image_path)}},
                ],
            }
        ],
        "temperature": 0,
    }
    resp = requests.post(url, headers=_headers(api_key), json=payload, timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"大模型接口错误 {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"无法解析模型返回：{json.dumps(data, ensure_ascii=False)[:300]}")


BOX_PROMPT = (
    "你是 OCR 引擎。请识别图片中的全部文字，并按行输出严格的 JSON 数组，"
    '格式为 [{"text": "文字", "box": [x0, y0, x1, y1]}, ...]。'
    "坐标使用 0-1000 的相对整数（相对图像宽高）。不要输出 JSON 之外的任何内容。"
)


def _parse_box_json(text: str, image_path: str | Path) -> List[OCRResult]:
    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    w, h = image_size(image_path)
    results: List[OCRResult] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        t = item.get("text") or item.get("word") or ""
        box = item.get("box") or item.get("bbox")
        if not t:
            continue
        rect = None
        if isinstance(box, (list, tuple)) and len(box) == 4:
            try:
                x0, y0, x1, y1 = (float(v) for v in box)
                # 判断是否归一化 (0-1) 或 0-1000
                if max(x0, y0, x1, y1) <= 1.5:
                    x0, x1 = x0 * w, x1 * w
                    y0, y1 = y0 * h, y1 * h
                elif max(x0, y0, x1, y1) > max(w, h) * 1.5:
                    x0, x1 = x0 / 1000 * w, x1 / 1000 * w
                    y0, y1 = y0 / 1000 * h, y1 / 1000 * h
                rect = [x0, y0, x1, y1]
            except (TypeError, ValueError):
                rect = None
        results.append(OCRResult(text=str(t), box=rect, confidence=0.0))
    return results


def openai_vision_ocr_with_boxes(
    image_path: str | Path,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> List[OCRResult]:
    text = openai_vision_ocr(
        image_path, base_url=base_url, api_key=api_key, model=model, prompt=BOX_PROMPT, timeout=timeout
    )
    results = _parse_box_json(text, image_path)
    if not results and text.strip():
        results = plain_text_to_results(text.strip(), image_path, "")
    return results
