# SPDX-License-Identifier: GPL-3.0-or-later
"""截屏 OCR：屏幕选区截图 → OCR → 写入可编辑的剪贴板。

托盘的区域截屏由 ``libu.tray_helper`` 完成；本模块负责持久化 OCR 文本、
保存截取到的图片、维护多条历史记录，供前端轮询与编辑。
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import service
from .config import (
    SCREENSHOT_DIR,
    SCREENSHOT_FILE,
    SCREENSHOT_REQUEST,
    ensure_dirs,
)

_LOCK = threading.RLock()
_MAX_HISTORY = 50


def _empty() -> Dict[str, Any]:
    return {"text": "", "image": "", "backend": "", "updated_at": 0.0, "history": []}


def _read() -> Dict[str, Any]:
    if SCREENSHOT_FILE.exists():
        try:
            data = json.loads(SCREENSHOT_FILE.read_text("utf-8"))
            if isinstance(data, dict):
                base = _empty()
                base.update(data)
                return base
        except (json.JSONDecodeError, OSError):
            pass
    return _empty()


def _write(state: Dict[str, Any]) -> None:
    ensure_dirs()
    SCREENSHOT_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), "utf-8"
    )


def get_state() -> Dict[str, Any]:
    with _LOCK:
        return _read()


def update_text(text: str) -> Dict[str, Any]:
    with _LOCK:
        state = _read()
        state["text"] = text or ""
        state["updated_at"] = time.time()
        if state["history"]:
            state["history"][0]["text"] = state["text"]
        _write(state)
        return state


def clear() -> Dict[str, Any]:
    with _LOCK:
        state = _empty()
        _write(state)
        return state


def _save_image(content: bytes, filename: str) -> Path:
    ensure_dirs()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower() or ".png"
    dest = SCREENSHOT_DIR / f"{uuid.uuid4().hex[:12]}{suffix}"
    dest.write_bytes(content)
    return dest


def save_uploaded(content: bytes, filename: str = "screenshot.png") -> Path:
    path = _save_image(content, filename)
    try:
        from PIL import Image

        with Image.open(path) as im:
            _ = im.size
    except Exception as exc:  # noqa: BLE001
        path.unlink(missing_ok=True)
        raise ValueError(f"无法解析图片：{exc}") from exc
    return path


def ingest_image(
    source: str,
    backend: Optional[str] = None,
    lang: str = "chi_sim+eng",
) -> Dict[str, Any]:
    """对截图执行 OCR 并写入剪贴板状态。"""
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(source)
    if not backend:
        from .settings import backend_for_feature

        backend = backend_for_feature("screenshot")
    results = service.run_ocr(str(path), backend, lang=lang, auto_enhance=False)
    lines = [r.get("text", "") for r in results if (r.get("text") or "").strip()]
    text = "\n".join(lines)
    with _LOCK:
        state = _read()
        entry = {
            "id": uuid.uuid4().hex[:12],
            "text": text,
            "image": str(path),
            "backend": backend,
            "created_at": time.time(),
        }
        state["text"] = text
        state["image"] = str(path)
        state["backend"] = backend
        state["updated_at"] = time.time()
        state["history"] = ([entry] + list(state.get("history") or []))[:_MAX_HISTORY]
        _write(state)
        return state


def ingest_bytes(
    content: bytes,
    filename: str = "screenshot.png",
    backend: Optional[str] = None,
    lang: str = "chi_sim+eng",
) -> Dict[str, Any]:
    path = save_uploaded(content, filename)
    return ingest_image(str(path), backend=backend, lang=lang)


# --------------------------------------------------------------------------- #
# 托盘助手触发
# --------------------------------------------------------------------------- #
def request_capture() -> None:
    """前端点击「截屏」时写触发文件，托盘助手轮询后开始区域截屏。"""
    ensure_dirs()
    SCREENSHOT_REQUEST.write_text(str(time.time()), "utf-8")


def has_request() -> bool:
    return SCREENSHOT_REQUEST.exists()


def consume_request() -> bool:
    if SCREENSHOT_REQUEST.exists():
        try:
            SCREENSHOT_REQUEST.unlink()
        except OSError:
            pass
        return True
    return False
