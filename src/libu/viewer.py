# SPDX-License-Identifier: GPL-3.0-or-later
"""OCR 图片查看器：记忆已打开的图片，并支持对图片做 OCR 以便随时复制文字。

与"文档扫描仪"不同，查看器不改变原图、不做增强，只做识别与展示。
索引持久化于 ~/.libu/viewer.json；只要文件未被移动或删除，重新打开软件后依旧显示。
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import service
from .config import SUPPORTED_IMAGE_SUFFIXES, VIEWER_DIR, VIEWER_FILE, ensure_dirs

_LOCK = threading.RLock()


def _read() -> List[Dict[str, Any]]:
    if VIEWER_FILE.exists():
        try:
            data = json.loads(VIEWER_FILE.read_text("utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _write(items: List[Dict[str, Any]]) -> None:
    ensure_dirs()
    VIEWER_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), "utf-8")


def _exists(source: str) -> bool:
    try:
        return Path(source).is_file()
    except OSError:
        return False


def list_images() -> List[Dict[str, Any]]:
    """返回仍然存在的图片（按最近打开时间排序）。"""
    with _LOCK:
        items = [it for it in _read() if _exists(it.get("source", ""))]
        return items


def add(source: str, title: Optional[str] = None) -> Dict[str, Any]:
    source = str(Path(source))
    with _LOCK:
        items = [it for it in _read() if it.get("source") != source]
        entry = {
            "id": source,
            "source": source,
            "title": title or Path(source).stem,
            "added_at": time.time(),
        }
        items.insert(0, entry)
        _write(items[:500])
        return entry


def add_path(source: str) -> Dict[str, Any]:
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(source)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"不支持的图片格式：{suffix}")
    return add(str(path), title=path.stem)


def save_pasted(content: bytes, filename: str = "clipboard.png") -> Dict[str, Any]:
    """保存从剪贴板粘贴的图片，落盘后加入查看器。"""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        suffix = ".png"
        filename = "clipboard.png"
    ensure_dirs()
    VIEWER_DIR.mkdir(parents=True, exist_ok=True)
    dest = VIEWER_DIR / f"{uuid.uuid4().hex[:12]}_{Path(filename).name}"
    dest.write_bytes(content)
    try:
        from PIL import Image

        with Image.open(dest) as im:
            _ = im.size
    except Exception as exc:  # noqa: BLE001
        dest.unlink(missing_ok=True)
        raise ValueError(f"无法解析剪贴板图片：{exc}") from exc
    return add(str(dest), title=Path(filename).stem)


def remove(source: str) -> None:
    with _LOCK:
        items = [it for it in _read() if it.get("source") != source]
        _write(items)


def ocr(source: str, backend: Optional[str] = None, lang: str = "chi_sim+eng") -> List[dict]:
    """对查看器中的图片做 OCR（不增强、不裁剪）。"""
    if backend is None:
        from .settings import backend_for_feature

        backend = backend_for_feature("viewer")
    return service.run_ocr(source, backend, lang=lang, auto_enhance=False)
