# -*- mode: python ; coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部后端 PyInstaller 打包配置（Windows）
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

# 本 spec 位于 <root>/pack/Windows/，据此定位仓库根目录（与执行时的工作目录无关）
_SPECPATH = os.path.abspath(SPECPATH)
SPEC_DIR = os.path.dirname(_SPECPATH) if _SPECPATH.endswith(".spec") else _SPECPATH
ROOT = os.path.abspath(os.path.join(SPEC_DIR, "..", ".."))
SRC = os.path.join(ROOT, "src")
LAUNCHER = os.path.join(SPEC_DIR, "launcher.py")

datas = []
binaries = []
hiddenimports = []

for pkg in ["uvicorn", "fastapi", "pymupdf", "docx", "PIL", "requests", "numpy"]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += collect_submodules("libu")

a = Analysis(
    [LAUNCHER],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PySide2", "gi", "gi.repository"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="libu-backend",
    console=True,
)
coll = COLLECT(exe, a.binaries, a.datas, name="libu-backend")
