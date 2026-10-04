# SPDX-License-Identifier: GPL-3.0-or-later
"""业务编排层：上传 → 预处理 → OCR → 输出，以及缩略图/最近项目。"""
from __future__ import annotations

import base64
import hashlib
import io
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image, ImageOps

from . import model_manager
from .config import CACHE_DIR, MODEL_DIR, OUTPUT_DIR, SUPPORTED_IMAGE_SUFFIXES, ensure_dirs
from .image_processing import crop_image, load_image, preprocess, save_image
from .ocr_backends import get_backend, list_backends
from .pdf_word_generator import process_image_to_outputs, process_pages_to_outputs
from .recent import add_recent, hide_recent, list_recent, remove_recent

UPLOAD_DIR = CACHE_DIR / "uploads"
PROCESSED_DIR = CACHE_DIR / "processed"
THUMB_DIR = CACHE_DIR / "thumbnails"


def _init() -> None:
    ensure_dirs()
    for d in (UPLOAD_DIR, PROCESSED_DIR, THUMB_DIR):
        d.mkdir(parents=True, exist_ok=True)


_init()


def _safe_name(name: str) -> str:
    return Path(name).name.replace("\x00", "")


def save_upload(filename: str, content: bytes) -> Dict[str, object]:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"不支持的图片格式：{suffix}")
    uid = uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{uid}_{_safe_name(filename)}"
    dest.write_bytes(content)
    with Image.open(dest) as im:
        w, h = im.size
    meta = add_recent(str(dest), title=Path(filename).stem)
    return {"id": str(dest), "path": str(dest), "width": w, "height": h, "project": meta}


def save_upload_from_path(source: str) -> Dict[str, object]:
    """导入本机已存在的图片路径（Electron 文件选择器场景）。"""
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(source)
    suffix = src.suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"不支持的图片格式：{suffix}")
    uid = uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{uid}_{_safe_name(src.name)}"
    shutil.copyfile(src, dest)
    with Image.open(dest) as im:
        w, h = im.size
    meta = add_recent(str(dest), title=src.stem)
    return {"id": str(dest), "path": str(dest), "width": w, "height": h, "project": meta}


def preprocess_source(
    source: str,
    box: Optional[List[float]] = None,
    auto_enhance: bool = True,
) -> Dict[str, object]:
    """裁剪 + 增强，返回处理后的图片路径。"""
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(source)
    uid = uuid.uuid4().hex[:12]
    out = PROCESSED_DIR / f"{uid}_{src.stem}.png"
    img = preprocess(
        src,
        box=box,
        do_deskew=auto_enhance,
        do_shadow=auto_enhance,
        do_whiten=auto_enhance,
        do_enhance=auto_enhance,
    )
    save_image(img, out)
    return {"path": str(out), "width": img.width, "height": img.height}


def run_ocr(
    source: str,
    backend_name: str,
    box: Optional[List[float]] = None,
    lang: str = "chi_sim+eng",
    auto_enhance: bool = True,
) -> List[dict]:
    """对（可选的）裁剪区域执行 OCR。"""
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(source)
    target = src
    if box or auto_enhance:
        processed = preprocess_source(str(src), box, auto_enhance)
        target = Path(processed["path"])
    backend = get_backend(backend_name)
    results = backend.recognize(target, lang=lang)
    return [r.to_dict() for r in results]


def generate(
    source: str,
    backend: str = "wechat",
    box: Optional[List[float]] = None,
    ocr_results: Optional[List[dict]] = None,
    outputs: Optional[List[str]] = None,
    base_name: Optional[str] = None,
    auto_enhance: bool = True,
    enable_ocr: bool = True,
    register: bool = True,
) -> Dict[str, str]:
    """生成输出文件。

    - ocr_results 提供时：直接使用（已校正结果）；
    - ocr_results 为 None 且 enable_ocr=True：先执行 OCR；
    - enable_ocr=False：不进行 OCR，直接输出图像 PDF。
    """
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(source)

    processed = preprocess_source(str(src), box, auto_enhance)
    target = Path(processed["path"])
    base_name = base_name or src.stem

    if ocr_results is not None:
        results = ocr_results
    elif enable_ocr:
        results = run_ocr(str(src), backend, box=box, auto_enhance=auto_enhance)
    else:
        results = []

    paths = process_image_to_outputs(
        target,
        ocr_results=results or None,
        base_name=base_name,
        output_dir=OUTPUT_DIR,
        outputs=outputs or ("pdf", "word_hidden", "word_text"),
    )
    out_map = {k: str(v) for k, v in paths.items()}
    if register:
        add_recent(str(src), title=base_name, outputs=out_map, thumbnail=str(thumbnail_for(str(src))))
    return out_map


def generate_batch(
    pages: List[dict],
    backend: str = "wechat",
    outputs: Optional[List[str]] = None,
    base_name: Optional[str] = None,
    auto_enhance: bool = True,
    enable_ocr: bool = True,
    register: bool = True,
) -> Dict[str, str]:
    """批量生成：把多张图片按顺序合成为一个多页 PDF / Word。

    pages: [{"source": 路径, "box": [...], "ocr_results": [...]}, ...]
    """
    if not pages:
        raise ValueError("没有可处理的页面")

    prepared: List[tuple] = []
    first_source = None
    for page in pages:
        source = page.get("source")
        if not source:
            continue
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(source)
        box = page.get("box")
        results = page.get("ocr_results")

        processed = preprocess_source(str(src), box, auto_enhance)
        target = Path(processed["path"])
        if results is None and enable_ocr:
            results = run_ocr(str(src), backend, box=box, auto_enhance=auto_enhance)
        prepared.append((target, results or []))
        first_source = first_source or str(src)

    if not prepared:
        raise ValueError("没有有效的页面")

    if not base_name:
        base_name = Path(first_source).stem if first_source else "吏部文档"

    paths = process_pages_to_outputs(
        prepared,
        base_name=base_name,
        output_dir=OUTPUT_DIR,
        outputs=outputs or ("pdf", "word_hidden", "word_text"),
    )
    out_map = {k: str(v) for k, v in paths.items()}
    if register and first_source:
        try:
            add_recent(
                first_source,
                title=base_name,
                outputs=out_map,
                thumbnail=str(thumbnail_for(first_source)),
            )
        except Exception:
            pass
    return out_map


# --------------------------------------------------------------------------- #
# 缩略图
# --------------------------------------------------------------------------- #
def _thumb_path(source: str) -> Path:
    key = hashlib.md5(str(source).encode("utf-8")).hexdigest()
    return THUMB_DIR / f"{key}.png"


def thumbnail_for(source: str, size: int = 480) -> Path:
    path = _thumb_path(source)
    if path.exists() and path.stat().st_mtime >= Path(source).stat().st_mtime:
        return path
    try:
        img = load_image(source)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((size, size), Image.LANCZOS)
        img.convert("RGB").save(path, "PNG")
    except Exception:
        # 生成占位
        Image.new("RGB", (size, int(size * 1.3)), (40, 40, 60)).save(path, "PNG")
    return path


def thumbnail_data_url(source: str) -> str:
    path = thumbnail_for(source)
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# --------------------------------------------------------------------------- #
# 项目 / 模型
# --------------------------------------------------------------------------- #
def projects(include_hidden: bool = False) -> List[Dict[str, object]]:
    items = list_recent()
    out = []
    for it in items:
        if it.get("hidden") and not include_hidden:
            continue
        item = dict(it)
        try:
            item["thumbnail"] = thumbnail_data_url(it["source"])
        except Exception:
            item["thumbnail"] = None
        out.append(item)
    return out


def hide_project(source: str) -> None:
    hide_recent(source)


def delete_project(source: str) -> None:
    remove_recent(source)
    try:
        p = Path(source)
        if p.exists() and UPLOAD_DIR in p.parents:
            p.unlink()
    except Exception:
        pass


def import_model(zip_path: str, name: Optional[str] = None) -> Dict[str, object]:
    return model_manager.import_model_zip(zip_path, name)


def models() -> List[Dict[str, object]]:
    return model_manager.list_models()


def delete_model(name: str) -> bool:
    return model_manager.delete_model(name)


def engines() -> List[dict]:
    return list_backends()
