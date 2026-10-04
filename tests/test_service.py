# SPDX-License-Identifier: GPL-3.0-or-later
"""业务编排层测试（上传 / 预处理 / 无 OCR 生成 / 最近项目）。"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("LIBU_OUTPUT_DIR", tempfile.mkdtemp(prefix="libu_out_"))

try:
    from PIL import Image

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


@unittest.skipUnless(HAVE_PIL, "需要 Pillow")
class ServiceTests(unittest.TestCase):
    def _png(self):
        buf = io.BytesIO()
        Image.new("RGB", (300, 400), (245, 245, 245)).save(buf, "PNG")
        return buf.getvalue()

    def test_upload_preprocess_hide(self):
        from libu import service

        meta = service.save_upload("t.png", self._png())
        self.assertTrue(Path(meta["path"]).exists())
        self.assertEqual(meta["width"], 300)

        proc = service.preprocess_source(meta["path"], [10, 10, 290, 390], True)
        self.assertTrue(Path(proc["path"]).exists())

        names = [p["source"] for p in service.projects(include_hidden=True)]
        self.assertIn(meta["path"], names)

    def test_generate_without_ocr(self):
        try:
            import pymupdf  # noqa: F401
        except ImportError:
            self.skipTest("需要 PyMuPDF")
        from libu import service

        meta = service.save_upload("t2.png", self._png())
        out = service.generate(
            meta["path"],
            box=[0, 0, 300, 400],
            outputs=["pdf"],
            enable_ocr=False,
            auto_enhance=False,
        )
        self.assertIn("pdf", out)
        self.assertTrue(Path(out["pdf"]).exists())
        service.delete_project(meta["path"])

    def test_delete_project(self):
        from libu import service

        meta = service.save_upload("t3.png", self._png())
        service.delete_project(meta["path"])
        names = [p["source"] for p in service.projects(include_hidden=True)]
        self.assertNotIn(meta["path"], names)


if __name__ == "__main__":
    unittest.main()
