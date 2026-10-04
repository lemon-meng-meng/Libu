# 双层 PDF / Word 生成

## 功能
- `create_double_layer_pdf`: 原图 + 隐形 OCR 文本层
- `create_word_with_image_and_hidden_text`: Word 原图 + 隐形文字可复制
- `create_word_text_only`: 纯文本 Word，去除多余元素

## 依赖
- PyMuPDF `pip install pymupdf`
- python-docx `pip install python-docx`

## 使用示例
```python
from libu.pdf_word_generator import process_image_to_outputs
ocr_results = [{"text":"你好","box":[10,10,100,30]}]
paths = process_image_to_outputs(Path("in.jpg"), ocr_results)
```
