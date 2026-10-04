# SPDX-License-Identifier: GPL-3.0-or-later
"""微信 OCR 后端。

微信 OCR 由微信客户端自带的 ocr_model（.xnet 权重，跨平台通用）与平台运行库组成。
用户可导入 `wechat_ocr.zip`（含 wxocr 启动器 + libwxocr.so + ocr_model）。
注意：`wxocr` 依赖微信运行时的 `libmmmojo.so` 等库，需要本机安装微信客户端，
或由用户在设置中指定运行库目录 / 自定义命令模板。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import List

from .. import model_manager
from ..settings import get_provider
from .base import BaseOCRBackend, OCRResult, CATEGORY_LOCAL, plain_text_to_results
from .registry import register_backend

_SYSTEM_LIB_DIRS = [
    "/opt/wechat",
    "/opt/wechat-beta",
    "/opt/wechat-universal",
    "/usr/lib/wechat",
]


@register_backend
class WeChatOCRBackend(BaseOCRBackend):
    name = "wechat"
    label = "微信 OCR"
    category = CATEGORY_LOCAL
    provider = "微信客户端内置 OCR"
    description = "微信自带的轻量 OCR 模型，中文识别质量高、离线、速度快；需导入 wechat_ocr.zip 并具备运行时。"
    url = "https://github.com/lemon-meng-meng/Libu"
    requires = ["wechat_ocr.zip", "微信运行时 libmmmojo"]

    @classmethod
    def available(cls):
        runtime = model_manager.find_wechat_runtime()
        if runtime is None:
            return False, "尚未导入 wechat_ocr.zip"
        if not _runtime_libs_available():
            return False, "缺少微信运行时库（libmmmojo.so），请安装微信或指定运行库目录"
        return True, ""

    def _lib_dirs(self) -> List[str]:
        cfg = get_provider("wechat_ocr") or {}
        dirs = []
        for d in cfg.get("lib_dirs", []) or []:
            dirs.append(str(d))
        runtime = model_manager.find_wechat_runtime()
        if runtime:
            dirs.append(str(runtime.parent))
        dirs.extend(_SYSTEM_LIB_DIRS)
        return [d for d in dirs if d and Path(d).exists()]

    def _run_command(self, cmd: List[str], env: dict) -> str:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )
        if proc.returncode != 0 and not proc.stdout.strip():
            raise RuntimeError(proc.stderr.strip() or f"wxocr 退出码 {proc.returncode}")
        return proc.stdout

    def recognize(self, image_path, lang="chi_sim+eng") -> List[OCRResult]:
        runtime = model_manager.find_wechat_runtime()
        if runtime is None:
            model_manager.ensure_wechat_extracted()
            runtime = model_manager.find_wechat_runtime()
        if runtime is None:
            raise FileNotFoundError("未找到微信 OCR，请先导入 wechat_ocr.zip")

        cfg = get_provider("wechat_ocr") or {}
        env = dict(os.environ)
        lib_dirs = self._lib_dirs()
        if lib_dirs:
            env["LD_LIBRARY_PATH"] = ":".join(lib_dirs) + ":" + env.get("LD_LIBRARY_PATH", "")

        model_dir = runtime.parent / "ocr_model"
        if not model_dir.exists():
            model_dir = runtime.parent

        template = cfg.get("command")
        if template:
            cmd = [
                part.format(
                    wxocr=str(runtime),
                    image=str(image_path),
                    model_dir=str(model_dir),
                    lang=lang,
                )
                for part in template
            ]
            out = self._run_command(cmd, env)
        else:
            last_err = None
            for cmd in (
                [str(runtime), "--model", str(model_dir), "--image", str(image_path), "--json"],
                [str(runtime), str(model_dir), str(image_path)],
                [str(runtime), str(image_path)],
            ):
                try:
                    out = self._run_command(cmd, env)
                    if out.strip():
                        break
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
            else:
                raise RuntimeError(
                    "微信 OCR 运行失败（需要微信运行时环境）。"
                    f"最后错误：{last_err}"
                )

        results = self._parse_output(out)
        if not results and out.strip():
            results = plain_text_to_results(out.strip(), image_path, lang)
        return results

    @staticmethod
    def _parse_output(out: str) -> List[OCRResult]:
        out = (out or "").strip()
        if not out:
            return []
        # 尝试整体 JSON
        for candidate in (out, out[out.find("[") : out.rfind("]") + 1] if "[" in out else ""):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
            except Exception:
                continue
            if isinstance(data, dict):
                data = data.get("data") or data.get("result") or data.get("items") or []
            results = []
            for item in data or []:
                if not isinstance(item, dict):
                    continue
                text = item.get("text") or item.get("word") or item.get("content") or ""
                box = (
                    item.get("box")
                    or item.get("bbox")
                    or _box_from_ltrb(item)
                )
                if not text:
                    continue
                results.append(
                    OCRResult(text=str(text), box=box, confidence=float(item.get("conf", item.get("confidence", 0)) or 0))
                )
            if results:
                return results
        # 解析 "text\tx\ty\tw\th" 之类的行
        results = []
        for line in out.splitlines():
            m = re.match(r"^(.*?)\t+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", line)
            if m:
                text, x, y, w, h = m.groups()
                results.append(
                    OCRResult(
                        text=text,
                        box=[int(x), int(y), int(x) + int(w), int(y) + int(h)],
                    )
                )
        return results


def _box_from_ltrb(item: dict):
    keys = ("left", "top", "width", "height")
    if all(k in item for k in keys):
        l, t, w, h = (item[k] for k in keys)
        return [l, t, l + w, t + h]
    keys2 = ("x", "y", "w", "h")
    if all(k in item for k in keys2):
        x, y, w, h = (item[k] for k in keys2)
        return [x, y, x + w, y + h]
    return None


def _runtime_libs_available() -> bool:
    for d in _SYSTEM_LIB_DIRS:
        if Path(d, "libmmmojo.so").exists():
            return True
    runtime = model_manager.find_wechat_runtime()
    if runtime and (runtime.parent / "libmmmojo.so").exists():
        return True
    # 允许用户通过配置了 lib_dirs 的情况
    cfg = get_provider("wechat_ocr") or {}
    for d in cfg.get("lib_dirs", []) or []:
        if Path(d, "libmmmojo.so").exists():
            return True
    return False
