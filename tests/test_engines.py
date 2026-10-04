# SPDX-License-Identifier: GPL-3.0-or-later
"""OCR 引擎注册表测试。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class EngineRegistryTests(unittest.TestCase):
    def test_backends_registered(self):
        from libu.ocr_backends import list_backends

        engines = list_backends()
        self.assertGreaterEqual(len(engines), 20)
        names = {e["name"] for e in engines}
        for required in [
            "tesseract",
            "paddleocr",
            "pp_ocr_v5",
            "wechat",
            "ocr_space",
            "baidu_ocr",
            "deepseek",
            "glm",
            "kimi",
            "qwen",
            "ollama",
            "lmstudio",
        ]:
            self.assertIn(required, names, f"缺少引擎 {required}")

    def test_categories(self):
        from libu.ocr_backends import list_backends

        cats = {e["category"] for e in list_backends()}
        self.assertTrue({"local", "cloud", "llm", "agent"}.issubset(cats))

    def test_get_unknown_backend(self):
        from libu.ocr_backends import get_backend

        with self.assertRaises(ValueError):
            get_backend("not_a_real_engine")


if __name__ == "__main__":
    unittest.main()
