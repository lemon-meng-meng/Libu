# SPDX-License-Identifier: GPL-3.0-or-later
"""双层 PDF / Word 生成模块。

- 双层 PDF：原图作为页面背景，OCR 文本以 *不可见渲染模式* 精确覆盖在原坐标，
  因此在阅读器中不可见、但可搜索、可复制、可选中。
- Word 模式一：原图 + 悬浮透明文本框（文字可复制、位置覆盖原图）。
- Word 模式二：按阅读顺序重排的纯文本 Word（去除图片等多余元素）。

依赖：PyMuPDF (fitz)、python-docx、Pillow。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .config import OUTPUT_DIR

try:  # PyMuPDF（新版模块名为 pymupdf）
    import pymupdf as fitz  # type: ignore
except ImportError:  # pragma: no cover
    try:
        import fitz  # type: ignore
    except ImportError:
        fitz = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml.ns import qn
    from docx.oxml import parse_xml
except ImportError:  # pragma: no cover
    Document = None


# --------------------------------------------------------------------------- #
# 通用工具
# --------------------------------------------------------------------------- #
def _require_fitz() -> None:
    if fitz is None:
        raise RuntimeError("未安装 PyMuPDF，请执行：pip install pymupdf")


def _require_docx() -> None:
    if Document is None:
        raise RuntimeError("未安装 python-docx，请执行：pip install python-docx")


def _normalize_results(ocr_results: Sequence[dict] | None) -> List[dict]:
    out: List[dict] = []
    for r in ocr_results or []:
        text = str(r.get("text", "")).strip()
        box = r.get("box") or r.get("bbox") or []
        if not text or len(box) != 4:
            continue
        try:
            x0, y0, x1, y1 = (float(v) for v in box)
        except (TypeError, ValueError):
            continue
        out.append(
            {
                "text": text,
                "box": [x0, y0, x1, y1],
                "confidence": float(r.get("confidence", 0) or 0),
            }
        )
    return out


def _fit_fontsize(text: str, box_w: float, box_h: float, fontname: str) -> float:
    """让文本宽度尽量铺满识别框宽度，并受框高约束。"""
    box_w = max(1.0, box_w)
    base = 12.0
    try:
        length = fitz.get_text_length(text, fontname=fontname, fontsize=base)
    except Exception:
        length = 0.0
    if length <= 0:
        # 粗略估算：中文按 1em，拉丁按 0.5em
        cjk = sum(1 for ch in text if ord(ch) > 0x2E80)
        length = base * (cjk + (len(text) - cjk) * 0.5)
    size = base * box_w / length
    # 约束：不超过框高的 1.15 倍，不小于 4pt
    return max(4.0, min(size, max(6.0, box_h * 1.15)))


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def image_to_pdf(image_path: str | Path, pdf_path: str | Path) -> Path:
    """把单张图片封装为单页 PDF（无 OCR 层）。"""
    _require_fitz()
    image_path = Path(image_path)
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if Image is not None:
        with Image.open(image_path) as im:
            w, h = im.size
    else:
        w = h = 1000
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    page.insert_image(page.rect, filename=str(image_path))
    doc.save(pdf_path, garbage=4, deflate=True)
    doc.close()
    return pdf_path


def _insert_text_layer(page, ocr_results: Sequence[dict], w: float, h: float) -> None:
    """在已有页面（原图尺寸 w×h）上叠加不可见文字层。"""
    for res in _normalize_results(ocr_results):
        x0, y0, x1, y1 = res["box"]
        x0 = max(0.0, min(w, x0))
        x1 = max(0.0, min(w, x1))
        y0 = max(0.0, min(h, y0))
        y1 = max(0.0, min(h, y1))
        box_w = abs(x1 - x0)
        box_h = abs(y1 - y0)

        fontname = "china-s" if any(ord(c) > 0x2E80 for c in res["text"]) else "helv"
        fontsize = _fit_fontsize(res["text"], box_w, box_h, fontname)
        # 图像坐标 -> PDF 坐标（PDF y 自下向上），使用框底作为基线
        baseline = fitz.Point(min(x0, x1), h - max(y0, y1) + fontsize * 0.8)
        try:
            page.insert_text(
                baseline,
                res["text"],
                fontsize=fontsize,
                fontname=fontname,
                render_mode=3,  # 不可见
                rotate=0,
            )
        except Exception:
            page.insert_text(
                baseline,
                res["text"],
                fontsize=fontsize,
                fontname="helv",
                render_mode=3,
            )


def create_double_layer_pdf(
    image_path: str | Path,
    ocr_results: Sequence[dict],
    output_path: str | Path,
) -> Path:
    """生成双层 PDF：原图 + 不可见可复制文字层。"""
    _require_fitz()
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as im:
        w, h = im.size

    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    page.insert_image(page.rect, filename=str(image_path))
    _insert_text_layer(page, ocr_results, w, h)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path


def create_double_layer_pdf_pages(
    pages: Sequence[tuple],
    output_path: str | Path,
) -> Path:
    """生成多页双层 PDF。

    pages: [(image_path, ocr_results), ...]，每个元素一页（按顺序）。
    """
    _require_fitz()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for image_path, ocr_results in pages:
        with Image.open(image_path) as im:
            w, h = im.size
        page = doc.new_page(width=w, height=h)
        page.insert_image(page.rect, filename=str(image_path))
        _insert_text_layer(page, ocr_results, w, h)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path


def image_to_pdf_pages(images: Sequence[str | Path], pdf_path: str | Path) -> Path:
    """把多张图片按顺序封装为多页 PDF（无文字层）。"""
    _require_fitz()
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for image_path in images:
        with Image.open(image_path) as im:
            w, h = im.size
        page = doc.new_page(width=w, height=h)
        page.insert_image(page.rect, filename=str(image_path))
    doc.save(pdf_path, garbage=4, deflate=True)
    doc.close()
    return pdf_path


# --------------------------------------------------------------------------- #
# Word
# --------------------------------------------------------------------------- #
def _build_overlay_xml(lines: List[str], width_pt: float, height_pt: float) -> str:
    """构造覆盖整页的透明 VML 文本框 XML（文字可复制）。"""
    paragraphs = []
    for line in lines:
        safe = (
            (line or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        paragraphs.append(
            '<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
            '<w:r><w:rPr><w:color w:val="FFFFFF"/><w:sz w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve">{safe}</w:t></w:r></w:p>'
        )
    content = "".join(paragraphs) or '<w:p><w:r><w:t></w:t></w:r></w:p>'
    return (
        '<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:v="urn:schemas-microsoft-com:vml">'
        "<w:pict>"
        f'<v:shape id="libu_ocr_overlay" type="#_x0000_t202" '
        f'style="position:absolute;left:0;top:0;width:{width_pt:.1f}pt;'
        f'height:{height_pt:.1f}pt;z-index:2" filled="f" stroked="f">'
        '<v:textbox inset="0,0,0,0">'
        "<w:txbxContent>"
        f"{content}"
        "</w:txbxContent>"
        "</v:textbox>"
        "</v:shape>"
        "</w:pict>"
        "</w:r>"
    )


def create_word_with_image_and_hidden_text(
    image_path: str | Path,
    ocr_results: Sequence[dict],
    output_path: str | Path,
    page_width_inches: float = 8.27,
) -> Path:
    """Word 模式一：原图 + 覆盖其上的透明可复制文字层。"""
    _require_docx()
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    section = doc.sections[0]
    # A4 宽度（英寸）映射，保持图片比例
    with Image.open(image_path) as im:
        px_w, px_h = im.size
    draw_w = page_width_inches
    draw_h = draw_w * px_h / max(1, px_w)
    section.page_width = Inches(page_width_inches)
    section.page_height = Inches(draw_h)
    section.left_margin = section.right_margin = 0
    section.top_margin = section.bottom_margin = 0

    para = doc.add_paragraph()
    para.alignment = 1  # center
    run = para.add_run()
    run.add_picture(str(image_path), width=Inches(draw_w))

    # 覆盖文本框
    lines = [r["text"] for r in _normalize_results(ocr_results)]
    if lines:
        overlay = _build_overlay_xml(lines, draw_w * 72, draw_h * 72)
        para._p.append(parse_xml(overlay))

    doc.save(output_path)
    return output_path


def _group_lines(results: List[dict], y_tol: float = 12.0) -> List[str]:
    """按垂直位置把识别框聚合成行，并按从左到右拼接。"""
    rows: List[dict] = []
    for res in sorted(results, key=lambda r: (r["box"][1], r["box"][0])):
        y_mid = (res["box"][1] + res["box"][3]) / 2
        placed = False
        for row in rows:
            if abs(row["y"] - y_mid) <= y_tol:
                row["items"].append(res)
                row["y"] = (row["y"] + y_mid) / 2
                placed = True
                break
        if not placed:
            rows.append({"y": y_mid, "items": [res]})
    rows.sort(key=lambda r: r["y"])
    out: List[str] = []
    for row in rows:
        row["items"].sort(key=lambda r: r["box"][0])
        out.append("".join(it["text"] for it in row["items"]))
    return out


def create_word_text_only(
    ocr_results: Sequence[dict],
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Word 模式二：保留文字阅读顺序，去除图片等多余元素。"""
    _require_docx()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    if title:
        doc.add_heading(title, level=1)
    lines = _group_lines(_normalize_results(ocr_results))
    if not lines:
        doc.add_paragraph("")
    for line in lines:
        doc.add_paragraph(line)
    doc.save(output_path)
    return output_path


def create_word_with_image_and_hidden_text_pages(
    pages: Sequence[tuple],
    output_path: str | Path,
    page_width_inches: float = 8.27,
) -> Path:
    """Word 模式一（多页）：每页原图 + 不可见可复制文字层。

    pages: [(image_path, ocr_results), ...]。
    """
    _require_docx()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = 0
    section.top_margin = section.bottom_margin = 0

    draw_w = page_width_inches
    for idx, (image_path, ocr_results) in enumerate(pages):
        with Image.open(image_path) as im:
            px_w, px_h = im.size
        draw_h = draw_w * px_h / max(1, px_w)
        if idx == 0:
            section.page_width = Inches(page_width_inches)
            section.page_height = Inches(draw_h)

        para = doc.add_paragraph()
        para.alignment = 1
        para.add_run().add_picture(str(image_path), width=Inches(draw_w))

        lines = [r["text"] for r in _normalize_results(ocr_results)]
        if lines:
            overlay = _build_overlay_xml(lines, draw_w * 72, draw_h * 72)
            para._p.append(parse_xml(overlay))

        if idx < len(pages) - 1:
            doc.add_page_break()
    doc.save(output_path)
    return output_path


def create_word_text_only_pages(
    pages: Sequence[tuple],
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Word 模式二（多页）：按阅读顺序输出全部页文本。"""
    _require_docx()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    if title:
        doc.add_heading(title, level=1)
    for idx, (_image_path, ocr_results) in enumerate(pages):
        lines = _group_lines(_normalize_results(ocr_results))
        for line in lines:
            doc.add_paragraph(line)
        if idx < len(pages) - 1:
            doc.add_page_break()
    if not any(_normalize_results(r) for _i, r in pages):
        doc.add_paragraph("")
    doc.save(output_path)
    return output_path


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def process_image_to_outputs(
    image_path: str | Path,
    ocr_results: Sequence[dict] | None = None,
    base_name: str | None = None,
    output_dir: str | Path | None = None,
    outputs: Iterable[str] | None = None,
) -> Dict[str, Path]:
    """主入口：生成所请求的输出文件，返回 {类型: 路径}。"""
    image_path = Path(image_path)
    base_name = base_name or image_path.stem
    out_dir = Path(output_dir or OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(outputs or ("pdf", "word_hidden", "word_text"))

    paths: Dict[str, Path] = {}
    has_ocr = bool(_normalize_results(ocr_results))

    if "pdf" in wanted:
        pdf_path = out_dir / f"{base_name}.pdf"
        if has_ocr:
            create_double_layer_pdf(image_path, ocr_results, pdf_path)
        else:
            image_to_pdf(image_path, pdf_path)
        paths["pdf"] = pdf_path

    if has_ocr and "word_hidden" in wanted:
        wh = out_dir / f"{base_name}_原图可复制.docx"
        create_word_with_image_and_hidden_text(image_path, ocr_results, wh)
        paths["word_hidden"] = wh

    if has_ocr and "word_text" in wanted:
        wt = out_dir / f"{base_name}_纯文本.docx"
        create_word_text_only(ocr_results, wt, title=base_name)
        paths["word_text"] = wt

    return paths


def process_pages_to_outputs(
    pages: Sequence[tuple],
    base_name: str | None = None,
    output_dir: str | Path | None = None,
    outputs: Iterable[str] | None = None,
) -> Dict[str, Path]:
    """多页主入口：pages = [(image_path, ocr_results), ...]，按顺序输出。

    与单页版本共享输出命名规则；PDF 为多页双层，Word 为多页文档。
    """
    pages = [(Path(p), r) for p, r in pages if p]
    if not pages:
        raise ValueError("没有可处理的页面")
    if len(pages) == 1:
        img, res = pages[0]
        return process_image_to_outputs(
            img, res, base_name=base_name, output_dir=output_dir, outputs=outputs
        )

    base_name = base_name or pages[0][0].stem
    out_dir = Path(output_dir or OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(outputs or ("pdf", "word_hidden", "word_text"))
    has_ocr = any(_normalize_results(res) for _img, res in pages)

    paths: Dict[str, Path] = {}
    if "pdf" in wanted:
        pdf_path = out_dir / f"{base_name}.pdf"
        if has_ocr:
            create_double_layer_pdf_pages(pages, pdf_path)
        else:
            image_to_pdf_pages([img for img, _ in pages], pdf_path)
        paths["pdf"] = pdf_path

    if has_ocr and "word_hidden" in wanted:
        wh = out_dir / f"{base_name}_原图可复制.docx"
        create_word_with_image_and_hidden_text_pages(pages, wh)
        paths["word_hidden"] = wh

    if has_ocr and "word_text" in wanted:
        wt = out_dir / f"{base_name}_纯文本.docx"
        create_word_text_only_pages(pages, wt, title=base_name)
        paths["word_text"] = wt

    return paths


if __name__ == "__main__":  # pragma: no cover
    print("双层 PDF / Word 生成模块已加载")
    print(f"输出目录: {OUTPUT_DIR}")
