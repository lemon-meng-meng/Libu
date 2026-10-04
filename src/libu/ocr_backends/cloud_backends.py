# SPDX-License-Identifier: GPL-3.0-or-later
"""在线 OCR 引擎：OCR.space、百度云 OCR 与飞桨星河（PaddleOCR）在线服务。

⚠️ 隐私提示：使用云端引擎会把图片上传到第三方服务器，请谨慎处理敏感文档。
"""
from __future__ import annotations

import base64
import json
from typing import List

import requests

from ..settings import get_provider
from .base import BaseOCRBackend, OCRResult, CATEGORY_CLOUD, plain_text_to_results
from .registry import register_backend

TIMEOUT = 120


@register_backend
class OCRSpaceBackend(BaseOCRBackend):
    name = "ocr_space"
    label = "OCR.space"
    category = CATEGORY_CLOUD
    provider = "OCR.space"
    local = False
    description = "免费在线 OCR（有额度限制），支持多语言；返回带坐标的文字层。上传图片到公网，注意隐私。"
    url = "https://ocr.space/"
    requires = ["api_key"]

    @classmethod
    def available(cls):
        cfg = get_provider("ocr_space") or {}
        if not cfg.get("api_key"):
            return False, "未配置 OCR.space API Key"
        return True, ""

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider("ocr_space") or {}
        endpoint = cfg.get("endpoint") or "https://api.ocr.space/parse/image"
        language = cfg.get("language") or ("chs" if "chi" in (lang or "") else "eng")
        with open(image_path, "rb") as fh:
            files = {"file": (str(image_path), fh)}
            data = {
                "apikey": cfg.get("api_key", ""),
                "language": language,
                "isOverlayRequired": "true",
                "OCREngine": "2",
            }
            resp = requests.post(endpoint, files=files, data=data, timeout=TIMEOUT)
        if resp.status_code >= 400:
            raise RuntimeError(f"OCR.space 错误 {resp.status_code}: {resp.text[:200]}")
        payload = resp.json()
        if payload.get("IsErroredOnProcessing"):
            raise RuntimeError(f"OCR.space 处理失败：{payload.get('ErrorMessage')}")

        results: List[OCRResult] = []
        for parsed in payload.get("ParsedResults", []) or []:
            overlay = parsed.get("TextOverlay") or {}
            for line in overlay.get("Lines", []) or []:
                words = line.get("Words", []) or []
                if not words:
                    continue
                text = line.get("LineText") or "".join(w.get("WordText", "") for w in words)
                left = min(float(w.get("Left", 0)) for w in words)
                top = min(float(w.get("Top", 0)) for w in words)
                right = max(float(w.get("Left", 0)) + float(w.get("Width", 0)) for w in words)
                bottom = max(float(w.get("Top", 0)) + float(w.get("Height", 0)) for w in words)
                results.append(
                    OCRResult(text=str(text), box=[left, top, right, bottom], confidence=0.0)
                )
        return results


@register_backend
class BaiduOCRBackend(BaseOCRBackend):
    name = "baidu_ocr"
    label = "百度云 OCR"
    category = CATEGORY_CLOUD
    provider = "百度智能云"
    local = False
    description = "百度通用文字识别，中文准确率高，返回带 location 坐标；需 API Key/Secret。上传图片到公网，注意隐私。"
    url = "https://cloud.baidu.com/product/ocr"
    requires = ["api_key", "secret_key"]

    _TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
    _OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

    @classmethod
    def available(cls):
        cfg = get_provider("baidu_ocr") or {}
        if not (cfg.get("api_key") and cfg.get("secret_key")):
            return False, "未配置百度 API Key/Secret"
        return True, ""

    def _token(self, api_key: str, secret_key: str) -> str:
        resp = requests.post(
            self._TOKEN_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key,
            },
            timeout=TIMEOUT,
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"百度鉴权失败：{data}")
        return data["access_token"]

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider("baidu_ocr") or {}
        token = self._token(cfg.get("api_key", ""), cfg.get("secret_key", ""))
        with open(image_path, "rb") as fh:
            image_b64 = base64.b64encode(fh.read()).decode("ascii")
        resp = requests.post(
            self._OCR_URL,
            params={"access_token": token},
            data={"image": image_b64, "language_guess": "CHN_ENG"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error_code"):
            raise RuntimeError(f"百度 OCR 错误 {data.get('error_code')}: {data.get('error_msg')}")
        results: List[OCRResult] = []
        for item in data.get("words_result", []) or []:
            loc = item.get("location") or {}
            left, top = loc.get("left", 0), loc.get("top", 0)
            w, h = loc.get("width", 0), loc.get("height", 0)
            results.append(
                OCRResult(
                    text=str(item.get("words", "")),
                    box=[left, top, left + w, top + h],
                    confidence=float(item.get("probability", {}).get("average", 0) or 0),
                )
            )
        return results


def _dig_texts(payload) -> str:
    """从各种可能的返回结构里尽力提取文本。"""
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (int, float, bool)):
        return ""
    if isinstance(payload, dict):
        # OpenAI 兼容
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    return "".join(
                        c.get("text", "")
                        for c in content
                        if isinstance(c, dict) and c.get("type") == "text"
                    )
        for key in ("text", "result", "ocr_text", "markdown", "content", "words"):
            if isinstance(payload.get(key), str):
                return payload[key]
        # 列表型字段递归
        for key in ("results", "data", "words_result", "lines", "pages"):
            val = payload.get(key)
            if val is not None:
                got = _dig_texts(val)
                if got:
                    return got
        return ""
    if isinstance(payload, list):
        parts = []
        for item in payload:
            if isinstance(item, dict):
                t = item.get("text") or item.get("words") or item.get("content")
                if isinstance(t, str):
                    parts.append(t)
                else:
                    parts.append(_dig_texts(item))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(p for p in parts if p)
    return ""


@register_backend
class PaddleOCRCloudBackend(BaseOCRBackend):
    name = "paddleocr_cloud"
    label = "PaddleOCR 在线（飞桨星河）"
    category = CATEGORY_CLOUD
    provider = "百度飞桨星河社区"
    local = False
    description = (
        "飞桨星河社区 PaddleOCR 在线服务（PP-OCRv5 / PaddleOCR-VL），"
        "需在 aistudio.baidu.com 获取访问令牌；图片会上传公网，注意隐私。"
    )
    url = "https://aistudio.baidu.com/paddleocr"
    requires = ["api_key"]
    parser = True

    @classmethod
    def available(cls):
        cfg = get_provider("paddleocr_cloud") or {}
        if not cfg.get("api_key"):
            return False, "未配置星河社区访问令牌"
        return True, ""

    def _openai_style(self, image_path, base_url, api_key, model):
        from ..vision_client import openai_vision_ocr

        return openai_vision_ocr(
            image_path,
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=(
                "请识别这张图片中的全部文字，保持阅读顺序，只输出文本，不要解释。"
            ),
        )

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        cfg = get_provider("paddleocr_cloud") or {}
        api_key = (cfg.get("api_key") or "").strip()
        base_url = (cfg.get("base_url") or "").strip().rstrip("/")
        endpoint = (cfg.get("endpoint") or "").strip()
        model = (cfg.get("model") or "PP-OCRv5").strip()

        # 模式一：OpenAI 兼容视觉接口（星河社区 / 自建服务）
        looks_openai = (
            "chat/completions" in endpoint
            or (not endpoint and base_url.endswith("/v1"))
        )
        if looks_openai:
            target = endpoint or (base_url + "/chat/completions")
            base = target[: -len("/chat/completions")] if target.endswith("/chat/completions") else base_url
            text = self._openai_style(image_path, base, api_key, model)
            return plain_text_to_results(text, image_path, lang) or self._fallback_text(
                text, image_path
            )

        # 模式二：通用 HTTP 接口（multipart + JSON 两种尝试）
        target = endpoint or (base_url + "/llm/lmapi/v3/ocr")
        with open(image_path, "rb") as fh:
            raw = fh.read()
        headers = {"Authorization": f"Bearer {api_key}"}
        last_err = None
        # 2a) multipart
        try:
            files = {"image": (str(image_path), raw)}
            data = {"access_token": api_key, "model": model}
            resp = requests.post(target, headers=headers, files=files, data=data, timeout=TIMEOUT)
            if resp.status_code < 400:
                payload = _safe_json(resp)
                text = _dig_texts(payload)
                if text:
                    return plain_text_to_results(text, image_path, lang)
            else:
                last_err = f"{resp.status_code}: {resp.text[:200]}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        # 2b) JSON base64
        try:
            payload = {"image": base64.b64encode(raw).decode("ascii"), "model": model}
            resp = requests.post(
                target,
                headers={**headers, "Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=TIMEOUT,
            )
            if resp.status_code < 400:
                text = _dig_texts(_safe_json(resp))
                if text:
                    return plain_text_to_results(text, image_path, lang)
            else:
                last_err = f"{resp.status_code}: {resp.text[:200]}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        raise RuntimeError(f"PaddleOCR 在线接口调用失败：{last_err}")

    def _fallback_text(self, text, image_path):
        return plain_text_to_results(text, image_path, "")


def _safe_json(resp):
    try:
        return resp.json()
    except ValueError:
        return resp.text
