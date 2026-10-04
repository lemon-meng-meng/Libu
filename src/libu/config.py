# SPDX-License-Identifier: GPL-3.0-or-later
"""吏部全局路径与常量配置。"""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "libu"
DISPLAY_NAME = "吏部"

HOME = Path.home()

# 处理结果输出目录：~/文档/吏部
DOCUMENTS = HOME / "文档"
if not DOCUMENTS.exists():
    # 英文系统回退
    xdg = os.environ.get("XDG_DOCUMENTS_DIR")
    if xdg:
        DOCUMENTS = Path(xdg)
    else:
        DOCUMENTS = HOME / "Documents"

OUTPUT_DIR = Path(os.environ.get("LIBU_OUTPUT_DIR", DOCUMENTS / "吏部"))

# 用户配置目录
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / APP_NAME
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# 数据目录 ~/.libu
DATA_DIR = HOME / ".libu"
# 用户导入的本地 OCR 模型
MODEL_DIR = DATA_DIR / "models"
# 最近项目索引
RECENT_FILE = DATA_DIR / "recent.json"
# 图片查看器记忆的图片索引
VIEWER_FILE = DATA_DIR / "viewer.json"
# 截屏 OCR 剪贴板状态
SCREENSHOT_FILE = DATA_DIR / "screenshot.json"
# 截屏临时目录（托盘助手截取后写入此处）
SCREENSHOT_DIR = DATA_DIR / "screenshots"
# 截屏捕获触发文件（前端请求托盘助手开始截屏）
SCREENSHOT_REQUEST = DATA_DIR / "screenshot.request"
# 应用缓存（裁剪后的临时图等）
CACHE_DIR = DATA_DIR / "cache"
# 图片查看器从剪贴板粘贴/导入时落盘的位置
VIEWER_DIR = CACHE_DIR / "viewer"

# 图片查看器兼容格式（尽可能广；无法解码的文件会被安全跳过）
SUPPORTED_IMAGE_SUFFIXES = {
    ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".bmp", ".dib", ".tif",
    ".tiff", ".webp", ".gif", ".ico", ".tga", ".avif", ".heic", ".heif",
    ".jp2", ".j2k", ".pbm", ".pgm", ".ppm", ".pnm", ".pcx", ".dcx",
    ".sgi", ".ras", ".xbm",
}

# 渐变底色预设（前端据此切换 --bg-a/b/c 变量）
BACKGROUND_PRESETS = [
    "aurora-blue",
    "midnight-purple",
    "sunset-rose",
    "emerald-night",
    "graphite",
    "dawn",
    "ocean",
    "forest",
]

# 图层/输出模式
OUTPUT_PDF = "pdf"
OUTPUT_WORD_HIDDEN = "word_hidden"
OUTPUT_WORD_TEXT = "word_text"


def ensure_dirs() -> None:
    for d in (
        OUTPUT_DIR, CONFIG_DIR, MODEL_DIR, DATA_DIR, CACHE_DIR,
        VIEWER_DIR, SCREENSHOT_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()
