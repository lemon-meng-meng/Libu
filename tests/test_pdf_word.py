# SPDX-License-Identifier: GPL-3.0-or-later
"""双层 PDF / Word 生成测试。可用 `python -m unittest` 或 pytest 运行。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from PIL import Image, ImageDraw  # noqa: F401

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

try:
    import pymupdf  # noqa: F401

    HAVE_FITZ = True
except ImportError:
    try:
        import fitz  # noqa: F401

        HAVE_FITZ = True
    except ImportError:
        HAVE_FITZ = False

try:
    import docx  # noqa: F401

    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False


RESULTS = [
    {"text": "Hello Libu 2026", "box": [58, 78, 330, 104], "confidence": 0.9},
    {"text": "第二行测试文字", "box": [58, 156, 300, 188], "confidence": 0.9},
    {"text": "Third line OCR", "box": [58, 236, 280, 262], "confidence": 0.9},
]


@unittest.skipUnless(HAVE_PIL, "需要 Pillow")
class PdfWordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="libu_test_"))
        self.img = self.tmp / "sample.png"
        img = Image.new("RGB", (800, 1000), (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((60, 80), "Hello Libu 2026", fill=(0, 0, 0))
        d.text((60, 160), "Second line", fill=(0, 0, 0))
        img.save(self.img)

    @unittest.skipUnless(HAVE_FITZ, "需要 PyMuPDF")
    def test_double_layer_pdf_has_extractable_text(self):
        from libu.pdf_word_generator import process_image_to_outputs

        paths = process_image_to_outputs(
            self.img, RESULTS, base_name="sample", output_dir=self.tmp
        )
        self.assertIn("pdf", paths)
        import pymupdf

        doc = pymupdf.open(paths["pdf"])
        text = doc[0].get_text()
        doc.close()
        self.assertIn("Hello Libu 2026", text)
        self.assertIn("第二行测试文字", text)

    @unittest.skipUnless(HAVE_FITZ, "需要 PyMuPDF")
    def test_no_ocr_pdf(self):
        from libu.pdf_word_generator import process_image_to_outputs

        paths = process_image_to_outputs(
            self.img, None, base_name="noocr", output_dir=self.tmp
        )
        self.assertIn("pdf", paths)
        self.assertNotIn("word_text", paths)

    @unittest.skipUnless(HAVE_DOCX, "需要 python-docx")
    def test_word_text_only(self):
        from libu.pdf_word_generator import create_word_text_only

        out = self.tmp / "text.docx"
        create_word_text_only(RESULTS, out, title="测试")
        import docx

        doc = docx.Document(str(out))
        text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("Hello Libu 2026", text)
        self.assertIn("第二行测试文字", text)

    def test_group_lines(self):
        from libu.pdf_word_generator import _group_lines, _normalize_results

        lines = _group_lines(_normalize_results(RESULTS))
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "Hello Libu 2026")


if __name__ == "__main__":
    unittest.main()
