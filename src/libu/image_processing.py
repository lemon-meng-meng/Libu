# SPDX-License-Identifier: GPL-3.0-or-later
"""图像预处理：裁剪、纠偏、去阴影、白底增强。

设计目标：生成"接近原生电子版"的观感。
所有函数在缺少 OpenCV/NumPy 时自动降级为纯 Pillow 实现。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("需要 Pillow：pip install pillow") from exc

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


Box = Tuple[int, int, int, int]  # x0, y0, x1, y1


def load_image(image_path: str | Path) -> "Image.Image":
    img = Image.open(image_path)
    return ImageOps.exif_transpose(img)


def crop_image(image: "Image.Image", box: Optional[Box]) -> "Image.Image":
    """按像素坐标裁剪，坐标越界时自动收敛。"""
    if not box:
        return image
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    w, h = image.size
    x0 = max(0, min(w, min(x0, x1)))
    x1 = max(0, min(w, max(x0, x1)))
    y0 = max(0, min(h, min(y0, y1)))
    y1 = max(0, min(h, max(y0, y1)))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return image
    return image.crop((x0, y0, x1, y1))


def deskew(image: "Image.Image", max_angle: float = 15.0) -> "Image.Image":
    """基于最小外接矩形的角度估计做纠偏。"""
    if cv2 is None or np is None:
        return image
    try:
        arr = np.array(image.convert("L"))
        arr = cv2.medianBlur(arr, 5)
        thr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thr > 0))
        if len(coords) < 50:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if angle > 45:
            angle = angle - 90
        if abs(angle) < 0.05 or abs(angle) > max_angle:
            return image
        fill = (255, 255, 255) if image.mode == "RGB" else 255
        return image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=fill)
    except Exception:
        return image


def remove_shadow(image: "Image.Image") -> "Image.Image":
    """形态学背景估计去阴影。缺 OpenCV 时用 Pillow 的除法归一化近似。"""
    if cv2 is not None and np is not None:
        try:
            arr = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
            bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            bg = cv2.GaussianBlur(bg, (0, 0), 15)
            normalized = cv2.divide(gray, bg, scale=255)
            return Image.fromarray(normalized).convert(image.mode)
        except Exception:
            pass
    # Pillow 降级：高通近似
    try:
        gray = image.convert("L")
        blur = gray.filter(ImageFilter.GaussianBlur(15))
        # 背景减除
        from PIL import ImageChops
        diff = ImageChops.subtract(gray, blur, scale=1.0, offset=128)
        return diff.convert(image.mode)
    except Exception:
        return image


def whiten_background(image: "Image.Image", threshold: int = 200) -> "Image.Image":
    """白底化：将接近白的背景拉纯白，提升"电子版"观感。"""
    if cv2 is not None and np is not None:
        try:
            arr = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            mask = gray >= threshold
            arr[mask] = [255, 255, 255]
            return Image.fromarray(arr)
        except Exception:
            pass
    return image


def enhance(image: "Image.Image") -> "Image.Image":
    """增强对比度与锐度。"""
    image = ImageEnhance.Contrast(image).enhance(1.15)
    image = ImageEnhance.Sharpness(image).enhance(1.2)
    return image


def preprocess(
    image_path: str | Path,
    box: Optional[Box] = None,
    do_deskew: bool = True,
    do_shadow: bool = True,
    do_whiten: bool = True,
    do_enhance: bool = True,
) -> "Image.Image":
    """完整预处理流水线：裁剪 → 纠偏 → 去阴影 → 白底 → 增强。"""
    img = load_image(image_path)
    img = crop_image(img, box)
    if do_deskew:
        img = deskew(img)
    if do_shadow:
        img = remove_shadow(img)
    if do_whiten:
        img = whiten_background(img)
    if do_enhance:
        img = enhance(img)
    return img


def save_image(image: "Image.Image", out_path: str | Path, quality: int = 95) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        image.convert("RGB").save(out_path, quality=quality)
    else:
        image.save(out_path)
    return out_path


def processed_image_for_ocr(
    image_path: str | Path, box: Optional[Box], cache_path: str | Path
) -> Path:
    """生成用于 OCR 与输出的预处理图像，并写入缓存。"""
    img = preprocess(image_path, box)
    return save_image(img, cache_path, quality=95)
