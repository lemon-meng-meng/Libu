#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""生成吏部应用图标（无需字体，纯绘制）。"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "icons"


def gradient(size: int):
    img = Image.new("RGB", (size, size))
    px = img.load()
    c1 = (110, 168, 255)
    c2 = (124, 240, 200)
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = (
                int(c1[0] * (1 - t) + c2[0] * t),
                int(c1[1] * (1 - t) + c2[1] * t),
                int(c1[2] * (1 - t) + c2[2] * t),
            )
    return img


def rounded_mask(size: int, radius: int):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_page(draw: ImageDraw.ImageDraw, size: int):
    s = size / 256.0
    left, top, right, bottom = 72 * s, 52 * s, 184 * s, 208 * s
    draw.rounded_rectangle([left, top, right, bottom], radius=14 * s, fill=(255, 255, 255, 235))
    # 文本行
    y = top + 26 * s
    widths = [0.72, 0.86, 0.6, 0.8, 0.66]
    for w in widths:
        draw.rounded_rectangle(
            [left + 16 * s, y, left + 16 * s + (right - left - 32 * s) * w, y + 9 * s],
            radius=4 * s,
            fill=(90, 120, 180, 220),
        )
        y += 24 * s
    # 扫描线
    draw.rounded_rectangle(
        [left - 8 * s, y + 6 * s, right + 8 * s, y + 16 * s],
        radius=5 * s,
        fill=(110, 168, 255, 255),
    )


def build(size: int) -> Image.Image:
    base = gradient(size).convert("RGBA")
    mask = rounded_mask(size, int(size * 0.22))
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw_page(draw, size)
    base = Image.alpha_composite(Image.new("RGBA", (size, size), (0, 0, 0, 0)), base)
    base.alpha_composite(layer)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 48, 64, 128, 256, 512]
    imgs = []
    for s in sizes:
        im = build(s)
        im.save(OUT / f"libu_{s}.png")
        imgs.append(im)
    imgs[-1].save(OUT / "libu.png")
    try:
        imgs[5].save(OUT / "libu.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except Exception:
        pass
    print(f"图标已生成到 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
