# SPDX-License-Identifier: GPL-3.0-or-later
"""最近项目索引持久化。"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from .config import RECENT_FILE, ensure_dirs

_LOCK = threading.RLock()


def _read() -> List[Dict[str, Any]]:
    if RECENT_FILE.exists():
        try:
            return json.loads(RECENT_FILE.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _write(items: List[Dict[str, Any]]) -> None:
    ensure_dirs()
    RECENT_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), "utf-8"
    )


def list_recent() -> List[Dict[str, Any]]:
    with _LOCK:
        items = [it for it in _read() if Path(it.get("source", "")).exists()]
        return items


def add_recent(
    source: str,
    title: str | None = None,
    outputs: Dict[str, str] | None = None,
    thumbnail: str | None = None,
    hidden: bool = False,
) -> Dict[str, Any]:
    with _LOCK:
        items = _read()
        sid = str(source)
        items = [it for it in items if it.get("source") != sid]
        entry = {
            "id": sid,
            "source": sid,
            "title": title or Path(sid).stem,
            "outputs": outputs or {},
            "thumbnail": thumbnail,
            "hidden": hidden,
            "updated_at": time.time(),
        }
        items.insert(0, entry)
        _write(items[:200])
        return entry


def remove_recent(source: str) -> None:
    with _LOCK:
        items = [it for it in _read() if it.get("source") != source]
        _write(items)


def hide_recent(source: str) -> None:
    with _LOCK:
        items = _read()
        for it in items:
            if it.get("source") == source:
                it["hidden"] = True
        _write(items)
