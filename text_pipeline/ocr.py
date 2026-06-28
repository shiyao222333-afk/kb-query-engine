"""
Text Pipeline — OCR 引擎

OCR 初始化 / 识别 / 结构化提取 / 质量检查。
所有函数返回统一的 {"ok": bool, ...} 格式。
"""

import os
import re
import subprocess
import logging

from qconst import PROJECT_DIR, IMAGES_DIR

logger = logging.getLogger(__name__)

# ── PIL 可选 ──
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    PILImage = None
    HAS_PIL = False

# Tesseract 备选（可通过环境变量覆盖）
_TESSERACT_FALLBACK = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT = os.environ.get("KB_TESSERACT_PATH") or _TESSERACT_FALLBACK
os.environ.setdefault("TESSDATA_PREFIX", os.environ.get("KB_TESSDATA_PREFIX") or r"D:\Tesseract-OCR\tessdata")

# PaddleOCR 主力引擎（延迟初始化）
_paddle_ocr = None

# PPStructureV3 引擎（延迟初始化）
_structure_engine = None


# ═══════════════════════════════════════════
# 内部工具
# ═══════════════════════════════════════════

def _ensure_images_dir():
    """确保图片存储目录存在"""
    os.makedirs(IMAGES_DIR, exist_ok=True)


# ═══════════════════════════════════════════
# OCR 引擎初始化
# ═══════════════════════════════════════════

def _get_paddle():
    """延迟初始化 PaddleOCR（首次调用才加载模型）"""
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(lang='ch', ocr_version='PP-OCRv4', use_textline_orientation=True)
        except ImportError:
            import sys
            python_exe = sys.executable
            raise ImportError(
                "PaddleOCR 未安装。运行: "
                f"{python_exe} -m pip install paddlepaddle paddleocr"
            )
    return _paddle_ocr


def _get_structure_engine():
    """延迟初始化 PPStructureV3（首次调用才加载模型）"""
    global _structure_engine
    if _structure_engine is None:
        try:
            from paddleocr import PPStructureV3
            _structure_engine = PPStructureV3(
                lang='ch',
                use_formula_recognition=True,
                use_table_recognition=True,
                use_chart_recognition=False,
                format_block_content=True,
            )
        except ImportError as e:
            import sys
            python_exe = sys.executable
            raise ImportError(
                f"PPStructureV3 初始化失败: {e}\n"
                f"请确保 paddlex[ocr] 已安装：\n"
                f"  {python_exe} -m pip install 'paddlex[ocr]==3.7.0'"
            )
    return _structure_engine


# ═══════════════════════════════════════════
# OCR 实现
# ═══════════════════════════════════════════

def _ocr_paddle(image_path: str) -> dict:
    """
    PaddleOCR 识别（主力引擎，中文+公式优化）
    返回: {"ok": true, "text": "...", "chars": N, "conf": 0.95, "raw": [...]}
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")

    engine = _get_paddle()
    result = engine.predict(image_path)

    if not result or not isinstance(result, list) or not result[0]:
        return {"ok": True, "text": "", "chars": 0, "conf": 0.0, "raw": []}

    page = result[0]
    texts = page.get('rec_texts', [])
    scores = page.get('rec_scores', [])

    lines = []
    confs = []
    for i, text in enumerate(texts):
        text = text.strip()
        if text:
            lines.append(text)
            conf = scores[i] if i < len(scores) else 0.0
            confs.append(float(conf))

    full_text = "\n".join(lines)
    avg_conf = sum(confs) / len(confs) if confs else 0.0

    return {
        "ok": True,
        "text": full_text,
        "chars": len(full_text),
        "conf": round(float(avg_conf), 4),
        "lines": len(lines),
        "raw": [{"text": t, "conf": c} for t, c in zip(lines, confs)]
    }


def _ocr_tesseract(image_path: str, lang: str = "chi_sim+eng") -> dict:
    """
    Tesseract OCR（备选引擎）
    返回: {"ok": true, "text": "...", "chars": N, "conf": null}
    """
    if not os.path.exists(TESSERACT):
        raise FileNotFoundError(f"Tesseract 未找到: {TESSERACT}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")

    outbase = image_path + "_ocr_tmp"
    result = subprocess.run(
        [TESSERACT, image_path, outbase, "-l", lang, "--psm", "6"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tesseract 失败: {result.stderr.strip()}")

    txt_path = outbase + ".txt"
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    os.remove(txt_path)

    return {
        "ok": True,
        "text": text,
        "chars": len(text),
        "conf": None,
        "lines": text.count("\n") + 1,
        "raw": []
    }


def _html_table_to_markdown(html_text: str) -> str:
    """将 HTML <table> 转换为 Markdown 表格（简化版，处理 PPStructureV3 输出）"""

    def _convert_table(match):
        table_html = match.group(0)
        rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
        md_rows = []
        for row_idx, row in enumerate(rows):
            cells = re.findall(r'<(?:td|th).*?>(.*?)</(?:td|th)>', row, re.DOTALL | re.IGNORECASE)
            clean_cells = []
            for c in cells:
                c = re.sub(r'<img\s+src="([^"]+)"[^>]*>', r'[image: \1]', c)
                c = re.sub(r'<div[^>]*>', ' ', c)
                c = re.sub(r'</div>', '', c)
                c = re.sub(r'<[^>]+>', '', c)
                c = c.strip()
                c = c.replace('|', '\\|')
                clean_cells.append(c)
            md_rows.append('| ' + ' | '.join(clean_cells) + ' |')
            if row_idx == 0:
                md_rows.append('|' + '|'.join([' --- ' for _ in clean_cells]) + '|')
        return '\n'.join(md_rows)

    html_text = re.sub(r'(?:<div[^>]*>\s*)?<html><body>\s*<table[^>]*>.*?</table>\s*</body></html>\s*(?:</div>)?',
                        _convert_table, html_text, flags=re.DOTALL)
    return html_text


def _assemble_blocks_v2(blocks: list, page_idx: int, image_list: list, source_image: str, page) -> str:
    """
    手动拼装 PPStructureV3 LayoutBlocks（_to_markdown 失败时的回退路径）。
    blocks 是 LayoutBlock 对象列表（label/content/bbox）。
    """
    if not blocks:
        return ""

    parts = []
    for b in blocks:
        label = getattr(b, 'label', 'text')
        content = getattr(b, 'content', '') or ''
        content = str(content)

        if label == 'table':
            parts.append(f"\n[表格] {content}\n")
        elif label in ('figure', 'figure_title', 'image'):
            imgs = page.get('imgs_in_doc', [])
            if imgs and hasattr(b, 'bbox'):
                bbox = b.bbox
                for img_item in imgs:
                    if isinstance(img_item, dict) and 'coordinate' in img_item:
                        coord = img_item['coordinate']
                        if (abs(bbox[0] - coord[0]) < 30 and abs(bbox[1] - coord[1]) < 30):
                            pil = img_item.get('img')
                            if pil:
                                _ensure_images_dir()
                                dest_name = f"fig_p{page_idx}_{len(image_list)}.png"
                                dest_path = os.path.join(IMAGES_DIR, dest_name)
                                pil.save(dest_path)
                                image_list.append(dest_path)
                                parts.append(f"[image: {dest_path}]")
                            break
            if not parts or parts[-1].startswith('[image') is False:
                parts.append(f"[图表] {content}")
        elif label == 'formula':
            content = content.strip()
            if content and not content.startswith('$$'):
                content = f"$${content}$$"
            parts.append(content)
        else:
            if content.strip():
                parts.append(content.strip())

    return "\n".join(parts)


def _check_ocr_quality(ocr_result: dict, image_path: str = None) -> dict:
    """
    检查 OCR 识别质量。

    检测信号:
    - 中文占比 < 10% → 可能图片模糊/纯英文/非文档
    - 字符数过少 → 可能图片模糊
    - 重复乱码 → 图片质量差
    - 平均置信度低 → 不确定

    返回: {"grade": "good|warn|bad", "score": 0-100, "issues": [...], "suggestion": "..."}
    """
    text = ocr_result.get("text", "")
    conf = ocr_result.get("conf")
    issues = []

    # 1. 中文占比
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text))
    total_chars = len(text.strip())
    cjk_ratio = cjk_chars / max(total_chars, 1)

    if total_chars < 3:
        issues.append("识别文字过少（<3字符）")
    elif total_chars < 20:
        issues.append(f"识别文字较少（{total_chars}字符），可能图片模糊")

    if cjk_ratio < 0.05 and total_chars > 10:
        issues.append(f"中文占比极低（{cjk_ratio:.1%}），确认是否中文文档")

    # 2. 乱码检测（连续非打印字符）
    garbled = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]{3,}', text)
    if garbled:
        issues.append("检测到乱码字符")

    # 3. 置信度
    if conf is not None:
        if conf < 0.5:
            issues.append(f"平均置信度低（{conf:.2f}），OCR 不确定")
        elif conf < 0.7:
            issues.append(f"平均置信度偏低（{conf:.2f}）")

    # 评分
    if not issues:
        score = 90
        grade = "good"
    elif len(issues) == 1 and ("偏低" in issues[0] or "较少" in issues[0]):
        score = 65
        grade = "warn"
    else:
        score = 30
        grade = "bad"

    return {
        "grade": grade,
        "score": score,
        "chars": total_chars,
        "cjk_ratio": round(cjk_ratio, 3),
        "issues": issues,
        "suggestion": "可直接入库" if grade == "good"
                       else "建议人工审核后入库" if grade == "warn"
                       else "图片可能模糊或非中文文档，建议重新拍摄"
    }


def _ocr_structured(image_path: str) -> dict:
    """
    PPStructureV3 结构化识别（主力引擎）
    自动检测版面区域：文字/公式/表格/图表，分别用最优方式处理。

    PPStructureV3.predict() 返回 list[LayoutParsingResultV2]。
    使用内置 _to_markdown() 获取统一 Markdown，包含：
      - HTML 表格 → 转为 Markdown 表格
      - 内嵌 LaTeX 公式 ($...$)
      - <img> 图片引用 → 保存为 [image: path]

    返回: {
        "ok": true,
        "text": "...",
        "chars": N,
        "blocks": [...],
        "images": [...],
        "conf": 0.95,
    }
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")

    engine = _get_structure_engine()

    try:
        pages = engine.predict(image_path)
    except Exception as e:
        return {"ok": False, "error": f"PPStructureV3 识别失败: {e}"}

    if not pages:
        return {"ok": True, "text": "", "chars": 0, "blocks": [], "images": [], "conf": 0.0}

    all_text_parts = []
    all_images = []
    block_summary = []

    for page_idx, page in enumerate(pages):
        try:
            md_result = page._to_markdown(pretty=True, show_formula_number=False)
        except Exception:
            layout_blocks = page.get('parsing_res_list', [])
            page_text = _assemble_blocks_v2(layout_blocks, page_idx, all_images, image_path, page)
            all_text_parts.append(page_text)
            block_summary.append({"page": page_idx, "type": "fallback", "length": len(page_text)})
            continue

        md_text = md_result.get('markdown_texts', '')
        if not md_text:
            continue

        # ── 1. 收集并保存图片 ──
        path_to_pil = {}
        imgs_in_doc = page.get('imgs_in_doc', [])
        for img_item in imgs_in_doc:
            if isinstance(img_item, dict):
                p = img_item.get('path', '')
                pil = img_item.get('img')
                if p and pil:
                    path_to_pil[p] = pil

        def _replace_img(match):
            src = match.group(1)
            _ensure_images_dir()
            dest_name = f"fig_p{page_idx}_{len(all_images)}.png"
            dest_path = os.path.join(IMAGES_DIR, dest_name)
            if src in path_to_pil:
                path_to_pil[src].save(dest_path)
            all_images.append(dest_path)
            return f"\n[image: {dest_path}]\n"

        md_text = re.sub(
            r'(?:<div[^>]*>\s*)?<img\s+src="([^"]+)"[^>]*>(?:\s*</div>)?',
            _replace_img, md_text
        )

        # ── 2. 转换 HTML 表格为 Markdown 表格 ──
        md_text = _html_table_to_markdown(md_text)

        # ── 3. 清理残余 HTML 标签 ──
        md_text = re.sub(r'<div[^>]*>', '\n', md_text)
        md_text = re.sub(r'</div>', '', md_text)
        md_text = re.sub(r'<html><body>', '', md_text)
        md_text = re.sub(r'</body></html>', '', md_text)
        md_text = re.sub(r'\n{3,}', '\n\n', md_text)

        all_text_parts.append(md_text.strip())
        block_summary.append({"page": page_idx, "type": "structured", "length": len(md_text)})

    full_text = "\n\n".join(all_text_parts)

    return {
        "ok": True,
        "text": full_text,
        "chars": len(full_text),
        "blocks": block_summary,
        "images": all_images,
        "conf": 0.95,
    }


# ═══════════════════════════════════════════
# 公共 OCR 入口
# ═══════════════════════════════════════════

def ocr_image(image_path: str) -> dict:
    """
    公共 OCR 入口：自动选择最优引擎识别图片文字。

    优先使用 PPStructureV3（结构化识别：文字+表格+公式），
    回退到 PaddleOCR（基础文字识别）。

    返回:
        {
            "ok": true,
            "ocr_text": "识别出的文字...",
            "text": "识别出的文字...",
            "chars": N,
            "conf": 0.95,
            "needs_correction": false,
            "quality": {...}
        }
    """
    if not os.path.exists(image_path):
        return {"ok": False, "error": f"图片不存在: {image_path}"}

    # 优先尝试 PPStructureV3
    try:
        result = _ocr_structured(image_path)
        if result.get("ok") and result.get("text"):
            quality = _check_ocr_quality(result, image_path)
            return {
                "ok": True,
                "ocr_text": result.get("text", ""),
                "text": result.get("text", ""),
                "chars": result.get("chars", len(result.get("text", ""))),
                "conf": result.get("conf", 0.0),
                "needs_correction": quality.get("grade") != "good",
                "quality": quality,
                "model": "PPStructureV3",
            }
    except Exception as e:
        logger.warning(f"[OCR] PPStructure 失败，回退到 PaddleOCR: {e}")

    # 回退到 PaddleOCR
    try:
        result = _ocr_paddle(image_path)
        if result.get("ok"):
            quality = _check_ocr_quality(result, image_path)
            return {
                "ok": True,
                "ocr_text": result.get("text", ""),
                "text": result.get("text", ""),
                "chars": result.get("chars", len(result.get("text", ""))),
                "conf": result.get("conf", 0.0),
                "needs_correction": quality.get("grade") != "good",
                "quality": quality,
                "model": "PaddleOCR",
            }
    except Exception as e:
        return {"ok": False, "error": f"OCR 引擎初始化失败: {e}"}

    return {"ok": False, "error": "无法加载任何 OCR 引擎"}
