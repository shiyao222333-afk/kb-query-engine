"""
Citrinitas · 熔知 — 文本管线包

OCR / 文本提取 / 分块 / 嵌入 / 页面分析。
所有函数返回统一的 {"ok": bool, ...} 格式。

本包是 facade：所有子模块的公共函数在此重新导出，
外部 import text_pipeline 的使用方式完全不变。
"""

# OCR
from .ocr import (
    ocr_image,
    _ocr_paddle,
    _ocr_tesseract,
    _ocr_structured,
    _check_ocr_quality,
    _ensure_images_dir,
)

# 文本提取 & 编码检测
from .extract import (
    extract_text,
    detect_encoding,
    detect_language,
    _detect_language,
)

# 嵌入
from .embed import _embed

# 切块
from .chunk import (
    _chunk_text,
    _text_hash,
    _extract_images,
)

# 页面分析
from .analyze import analyze_page_content
