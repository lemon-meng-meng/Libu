# SPDX-License-Identifier: GPL-3.0-or-later
"""吏部设置持久化：主题、默认引擎、各提供商 API Key。

设置保存于 ~/.config/libu/settings.json，API Key 仅存放于本机，
不会写入仓库，也不会随项目分发。
"""
from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from .config import SETTINGS_FILE

_LOCK = threading.RLock()

DEFAULTS: Dict[str, Any] = {
    "version": 2,
    "theme": "system",              # system | light | dark
    "background": "aurora-blue",    # 渐变底色预设
    "view_mode": "grid",            # grid | list
    "default_backend": "wechat",    # 默认 OCR 引擎（文档扫描仪）
    "default_output": "pdf",        # pdf | word_hidden | word_text
    "ocr_lang": "chi_sim+eng",
    "auto_enhance": True,           # 导入后自动做去阴影/白底增强
    "privacy_ack": False,           # 是否已知悉云端引擎隐私风险
    # 各功能可独立选择的 OCR 供应商（空串表示回退到 default_backend）
    "feature_backends": {
        "scanner": "",       # 主界面文档扫描仪
        "viewer": "",        # 图片查看器
        "screenshot": "",    # 截屏 OCR
    },
    # 截屏 OCR
    "screenshot_hotkey": "Ctrl+Alt+O",
    "screenshot_autostart": True,
    # 云端 / 大模型 / Agent 提供商配置
    "providers": {
        # 微信 OCR 运行时配置
        "wechat_ocr": {"enabled": True, "lib_dirs": [], "command": None},
        # 专用 OCR 线上引擎
        "ocr_space": {"enabled": False, "api_key": "", "endpoint": "https://api.ocr.space/parse/image"},
        "baidu_ocr": {"enabled": False, "api_key": "", "secret_key": ""},
        "paddleocr_cloud": {
            "enabled": False,
            "api_key": "",
            "base_url": "https://aistudio.baidu.com/paddleocr",
            "endpoint": "https://aistudio.baidu.com/llm/lmapi/v3/ocr",
            "model": "PP-OCRv5",
        },
        "hunyuan": {"enabled": False, "api_key": "", "base_url": "https://api.hunyuan.cloud.tencent.com/v1", "model": "hunyuan-vision"},
        # 大模型 API（OpenAI 兼容视觉接口）
        "deepseek": {"enabled": False, "api_key": "", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "models": []},
        "glm": {"enabled": False, "api_key": "", "base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4v", "models": []},
        "kimi": {"enabled": False, "api_key": "", "base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k-vision-preview", "models": []},
        "minimax": {"enabled": False, "api_key": "", "base_url": "https://api.minimax.chat/v1", "model": "abab6.5s-chat", "models": []},
        "stepfun": {"enabled": False, "api_key": "", "base_url": "https://api.stepfun.com/v1", "model": "step-1v-8k", "models": []},
        "qwen": {"enabled": False, "api_key": "", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-vl-max", "models": []},
        "yi": {"enabled": False, "api_key": "", "base_url": "https://api.lingyiwanwu.com/v1", "model": "yi-vision", "models": []},
        "nvidia": {"enabled": False, "api_key": "", "base_url": "https://integrate.api.nvidia.com/v1", "model": "meta/llama-3.2-90b-vision-instruct", "models": []},
        # Agent / 本地 AI 助手
        "opencode": {"enabled": False, "base_url": "http://localhost:4096", "api_key": "", "model": "", "models": []},
        "deepseek_harness": {"enabled": False, "base_url": "http://localhost:8000", "api_key": "", "model": "", "models": []},
        "claude_code": {"enabled": False, "base_url": "http://localhost:3000", "api_key": "", "model": "", "models": []},
        "codex": {"enabled": False, "base_url": "http://localhost:3001", "api_key": "", "model": "", "models": []},
        "cherry_studio": {"enabled": False, "base_url": "http://localhost:23333", "api_key": "", "model": "", "models": []},
        "ollama": {"enabled": False, "base_url": "http://localhost:11434", "api_key": "", "model": "llama3.2-vision", "models": []},
        "lmstudio": {"enabled": False, "base_url": "http://localhost:1234/v1", "api_key": "", "model": "local-model", "models": []},
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_settings() -> Dict[str, Any]:
    with _LOCK:
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}
        return _deep_merge(DEFAULTS, data)


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        merged = _deep_merge(DEFAULTS, settings or {})
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), "utf-8"
        )
        return merged


def update_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    current = load_settings()
    return save_settings(_deep_merge(current, patch or {}))


def get_provider(name: str) -> Dict[str, Any]:
    return load_settings().get("providers", {}).get(name, {})


def backend_for_feature(feature: str) -> str:
    """返回某功能应使用的 OCR 引擎名。

    feature ∈ {scanner, viewer, screenshot}。若未单独指定则回退默认引擎。
    """
    data = load_settings()
    feature_backends = data.get("feature_backends", {}) or {}
    name = (feature_backends.get(feature) or "").strip()
    if name:
        return name
    return data.get("default_backend") or "wechat"
