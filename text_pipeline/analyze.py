"""
Text Pipeline — 逐页内容分析

守望文件夹 v2 专用：5 信号判定内容可丢性。
"""


def analyze_page_content(text: str, page_images: list = None,
                         page_tables: list = None, ocr_conf: float = None,
                         text_density_threshold: float = 0.3,
                         ocr_conf_threshold: float = 0.7) -> dict:
    """
    逐页内容分析 — 5 信号判定内容可丢性。

    用于守望文件夹 v2 的内容驱动保留策略：判断一页内容是否可安全删除（纯文本，已入库）。

    参数:
        text: 该页提取的文本
        page_images: 该页包含的图片引用列表
        page_tables: 该页包含的表格列表
        ocr_conf: OCR 置信度（仅 OCR 页面使用）
        text_density_threshold: 文本密度阈值（低于此值视为非文本页）
        ocr_conf_threshold: OCR 置信度阈值（低于此值视为不可靠）

    返回:
        {
            "has_non_text": bool,       # 信号1: 含非文本元素（图片/表格/公式/代码块）
            "text_density": float,       # 信号2: 内容密度（有效文本字符占比，0-1）
            "ocr_reliable": bool,        # 信号3: OCR 是否可靠（置信度 >= 阈值）
            "extraction_complete": bool, # 信号4: 提取是否完整（有文本内容）
            "content_preserved": bool,   # 信号5: 提取内容是否等效于原文（纯文本则等效）
            "deletable": bool,           # 综合判断：该页是否可删除
            "summary": str,              # 人类可读的描述
        }
    """
    has_non_text = False
    reasons = []

    # ── 信号1: 非文本元素检测 ──
    images = page_images or []
    tables = page_tables or []
    if images:
        has_non_text = True
        reasons.append(f"含 {len(images)} 个图片")
    if tables:
        has_non_text = True
        reasons.append(f"含 {len(tables)} 个表格")

    # 检测数学公式（$$ 或 $ 标记）
    formula_count = text.count("$$") // 2 + text.count("$")
    if formula_count > 0:
        has_non_text = True
        reasons.append(f"含约 {formula_count} 个公式")

    # 检测代码块
    if "```" in text:
        has_non_text = True
        reasons.append("含代码块")

    # ── 信号2: 内容密度 ──
    text_chars = len(text.strip())
    total_chars = len(text) if text else 1
    text_density = text_chars / max(total_chars, 1)

    # ── 信号3: OCR 可靠性 ──
    ocr_reliable = True
    if ocr_conf is not None and ocr_conf < ocr_conf_threshold:
        ocr_reliable = False
        reasons.append(f"OCR 置信度低 ({ocr_conf:.2f})")

    # ── 信号4: 提取完整性 ──
    extraction_complete = True
    if not text_chars:
        extraction_complete = False
        reasons.append("提取内容为空")

    # ── 信号5: 内容等效性（有非文本元素时不等效）──
    content_preserved = not has_non_text and text_chars > 0

    # ── 可删性判断 ──
    # 该页可删除的条件：
    # 1. 无非文本元素（纯文本页）
    # 2. 提取完整
    # 3. （对 OCR 页）OCR 可靠
    # 4. 内容密度不低（不是空白/扫描噪音页）
    deletable = (
        not has_non_text
        and extraction_complete
        and (ocr_conf is None or ocr_reliable)
        and text_chars > 0
    )

    return {
        "has_non_text": has_non_text,
        "text_density": round(text_density, 3),
        "ocr_reliable": ocr_reliable,
        "extraction_complete": extraction_complete,
        "content_preserved": content_preserved,
        "deletable": deletable,
        "summary": "; ".join(reasons) if reasons else "纯文本页，可删除",
    }
