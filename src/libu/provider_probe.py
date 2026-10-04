# SPDX-License-Identifier: GPL-3.0-or-later
"""提供商连通性探测与模型自动检测。

用于「大模型 API」「Agent / 本地 AI 助手」设置项：
- 自动从 Ollama / LM Studio / OpenAI 兼容服务拉取可用模型列表；
- 提供「测试连接」能力，把真实的网络/鉴权错误原样返回给界面，便于排查。
"""
from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse

import requests

DEFAULT_TIMEOUT = 12

# 使用 OpenAI 兼容 /models 接口的平台（base_url 一般以 /v1 结尾）
_OPENAI_COMPATIBLE = {
    "deepseek", "glm", "kimi", "minimax", "stepfun", "qwen", "yi",
    "nvidia", "hunyuan", "lmstudio", "opencode", "deepseek_harness",
    "claude_code", "codex", "cherry_studio",
}


def _host_root(base_url: str) -> str:
    """去掉路径（如 /v1），只保留 scheme://host:port。"""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return base
    if "://" not in base:
        base = "http://" + base
    parsed = urlparse(base)
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def _headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    key = (cfg.get("api_key") or "").strip()
    headers = {"Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _get(url: str, cfg: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    return requests.get(url, headers=_headers(cfg), timeout=timeout)


def list_models(provider_key: str, cfg: Dict[str, Any] | None = None) -> List[str]:
    """返回该提供商可用的模型名列表；失败时抛出 RuntimeError（含具体原因）。"""
    cfg = cfg or {}
    base = (cfg.get("base_url") or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("未填写服务地址（Base URL）")

    if provider_key == "ollama":
        url = f"{_host_root(base)}/api/tags"
        try:
            resp = _get(url, cfg)
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"无法连接 Ollama：{url}\n请确认 Ollama 已启动（ollama serve），"
                f"且地址与端口正确。原始错误：{exc}"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(f"连接 Ollama 超时：{url}") from exc
        if resp.status_code >= 400:
            raise RuntimeError(f"Ollama 返回 {resp.status_code}：{resp.text[:200]}")
        data = resp.json()
        names = [m.get("name") or m.get("model") for m in data.get("models", [])]
        return sorted({n for n in names if n})

    # OpenAI 兼容：GET {base}/models
    url = f"{base}/models"
    try:
        resp = _get(url, cfg)
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"无法连接：{url}\n请确认本地服务已启动、地址与端口正确。原始错误：{exc}"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(f"连接超时：{url}") from exc
    if resp.status_code >= 400:
        raise RuntimeError(f"接口返回 {resp.status_code}：{resp.text[:200]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"返回内容不是 JSON：{resp.text[:200]}") from exc
    items = data.get("data") if isinstance(data, dict) else data
    names: List[str] = []
    for it in items or []:
        if isinstance(it, dict):
            name = it.get("id") or it.get("name") or it.get("model")
            if name:
                names.append(str(name))
        elif isinstance(it, str):
            names.append(it)
    return sorted(set(names))


def test_provider(provider_key: str, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """测试连通性，返回 {ok, message, models}。不抛异常。"""
    try:
        models = list_models(provider_key, cfg)
        if models:
            return {
                "ok": True,
                "message": f"连接成功，检测到 {len(models)} 个模型",
                "models": models,
            }
        return {"ok": True, "message": "连接成功（未返回模型列表）", "models": []}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": str(exc), "models": []}
