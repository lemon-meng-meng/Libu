# SPDX-License-Identifier: GPL-3.0-or-later
# -*- coding: utf-8 -*-
"""吏部 Nautilus 右键菜单扩展。

在文件管理器中右键图片时增加「用吏部打开」，直接把该图片送入吏部的处理向导。
依赖 python3-nautilus（Nautilus 3 与 4 均兼容）。
安装：bash scripts/install-context-menu.sh
"""
import os
import subprocess

try:
    from gi.repository import Nautilus, GObject
except Exception:  # pragma: no cover - 未安装 nautilus-python 时静默跳过
    Nautilus = None
    GObject = object

IMAGE_EXT = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".gif",
}


def _file_path(file_info):
    try:
        loc = file_info.get_location()
        return loc.get_path() if loc else None
    except Exception:
        return None


if Nautilus is not None:

    class LibuMenuProvider(GObject.GObject, Nautilus.MenuProvider):
        def get_file_items(self, *args):
            # Nautilus 3: (window, files)   Nautilus 4: (files)
            files = args[-1] if args else []
            selected = []
            for f in files:
                if f.is_directory():
                    continue
                if os.path.splitext(f.get_name())[1].lower() not in IMAGE_EXT:
                    continue
                path = _file_path(f)
                if path:
                    selected.append(path)
            if not selected:
                return []
            item = Nautilus.MenuItem(
                name="Libu::process",
                label="用吏部打开",
                tip="将选中的图片送入吏部，转换为可搜索 PDF / Word",
            )
            item.connect("activate", lambda _i: self._launch(selected[0]))
            return [item]

        @staticmethod
        def _launch(path):
            launcher = os.environ.get("LIBU_LAUNCHER", "libu-app")
            try:
                subprocess.Popen([launcher, "--import", path])
            except FileNotFoundError:
                subprocess.Popen(["libu", "--import", path])

        def get_background_items(self, *args):
            return []
