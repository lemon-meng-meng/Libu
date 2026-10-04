# SPDX-License-Identifier: GPL-3.0-or-later
"""本地 OCR 模型管理：导入 zip、解压、列举。"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from typing import Dict, List

from .config import MODEL_DIR

# 项目根目录（src/libu/model_manager.py -> ../../..）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_WECHAT_ZIP = PROJECT_ROOT / "OCR Model" / "wechat_ocr.zip"
WECHAT_DIR = MODEL_DIR / "wechat_ocr"


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in zf.infolist():
        target = (dest / member.filename).resolve()
        if not str(target).startswith(str(dest)):
            raise RuntimeError(f"压缩包包含非法路径：{member.filename}")
    zf.extractall(dest)


def import_model_zip(zip_path: str | Path, name: str | None = None) -> Dict[str, object]:
    """导入一个本地模型压缩包到 ~/.libu/models/<name>。"""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    name = name or zip_path.stem
    target = MODEL_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        _safe_extract(zf, target)
    # 若解压后只有一个顶层目录，则将其内容上提一层
    entries = [p for p in target.iterdir() if not p.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for child in inner.iterdir():
            shutil.move(str(child), str(target / child.name))
        inner.rmdir()
    return describe_model(target)


def find_wechat_runtime() -> Path | None:
    """定位可用的 wxocr 可执行文件。"""
    candidates = [
        WECHAT_DIR / "wxocr",
        WECHAT_DIR / "wechat_ocr_pkg" / "wxocr",
    ]
    for c in candidates:
        if c.exists():
            return c
    for c in MODEL_DIR.rglob("wxocr"):
        return c
    return None


def ensure_wechat_extracted() -> Path | None:
    """若未导入微信 OCR，且项目内置了 wechat_ocr.zip，则自动导入。"""
    if find_wechat_runtime():
        return WECHAT_DIR
    if BUNDLED_WECHAT_ZIP.exists():
        import_model_zip(BUNDLED_WECHAT_ZIP, name="wechat_ocr")
        return WECHAT_DIR
    return None


def describe_model(path: Path) -> Dict[str, object]:
    path = Path(path)
    files = [p for p in path.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    kind = "unknown"
    names = {p.name for p in files}
    if "wxocr" in names or "libwxocr.so" in names:
        kind = "wechat_ocr"
    elif any(p.suffix.lower() == ".onnx" for p in files):
        kind = "onnx"
    return {
        "name": path.name,
        "path": str(path),
        "kind": kind,
        "file_count": len(files),
        "size": total,
        "files": sorted(p.name for p in files)[:50],
    }


def list_models() -> List[Dict[str, object]]:
    if not MODEL_DIR.exists():
        return []
    return [describe_model(p) for p in sorted(MODEL_DIR.iterdir()) if p.is_dir()]


def delete_model(name: str) -> bool:
    target = MODEL_DIR / name
    if target.exists() and target.is_dir():
        shutil.rmtree(target)
        return True
    return False
