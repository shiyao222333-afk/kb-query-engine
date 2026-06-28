"""
Text Pipeline — 文本切块

去重哈希 / 图片提取 / 安全切片 / 长段落切分 / 主切块函数。
"""

import re
import hashlib

from qconst import CHUNK_MAX_CHARS, CHUNK_OVERLAP


def _text_hash(text: str) -> str:
    """内容的去重哈希（规范化后 SHA256，取前 32 位）"""
    normalized = re.sub(r'\s+', ' ', text).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _extract_images(text: str) -> list[str]:
    """提取文本中的图片引用（支持 3 种格式：[:image:] / Markdown / HTML）。"""
    images = []
    images.extend(re.findall(r'\[image:\s*([^\]]+)\]', text))
    images.extend(re.findall(r'!\[.*?\]\(([^\)]+)\)', text))
    images.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE))
    seen = set()
    unique = []
    for img in images:
        if img not in seen:
            seen.add(img)
            unique.append(img)
    return unique


def _safe_slice_point(text: str, target: int) -> int:
    """
    寻找安全的切片点：优先在 target 附近找标点/空格，避免切断中文。
    向前搜索 50 字符，向后搜索 50 字符。
    找不到则返回 target（允许切断）。
    """
    if target <= 0 or target >= len(text):
        return target
    start = max(0, target - 50)
    end = min(len(text), target + 50)
    punctuation = set('。！？；;,.!? \n\t')
    for i in range(target, start, -1):
        if text[i] in punctuation:
            return i + 1
    for i in range(target, end):
        if text[i] in punctuation:
            return i + 1
    for i in range(target, start, -1):
        if text[i] == ' ':
            return i + 1
    for i in range(target, end):
        if text[i] == ' ':
            return i + 1
    return target


def _split_long_paragraph(text: str, max_chars: int, overlap: int) -> list[str]:
    """将长段落按句子切分，不切断内联公式 $...$。
    超长句（>max_chars）安全切片，避免切断中文。"""
    sentences = re.split(r'(?<=[。；;])\s*', text)
    chunks = []
    current = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(current) + len(sent) < max_chars:
            current = (current + sent).strip()
        else:
            if current:
                chunks.append(current)
            if len(sent) > max_chars:
                while len(sent) > max_chars:
                    cut = _safe_slice_point(sent, max_chars)
                    chunks.append(sent[:cut])
                    sent = sent[cut:].strip()
                current = sent if sent else ""
            else:
                current = sent
    if current:
        chunks.append(current)
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i-1][-overlap:] if len(chunks[i-1]) >= overlap else chunks[i-1]
            overlapped.append(prev_tail + "\n\n" + chunks[i])
        return overlapped
    return chunks


def _chunk_text(text: str, max_chars: int = None, overlap: int = None) -> list[str]:
    """
    将文本切分为重叠的块。
    保护原子结构（公式/表格/图片引用）不被截断。
    """
    if max_chars is None:
        max_chars = CHUNK_MAX_CHARS
    if overlap is None:
        overlap = CHUNK_OVERLAP
    # ── 第1步：保护原子块（替换为占位符）──
    placeholders = {}
    counter = [0]

    def _protect(match):
        key = f"__ATOMIC_{counter[0]}__"
        placeholders[key] = match.group(0)
        counter[0] += 1
        return key

    text = re.sub(r'\$\$[\s\S]*?\$\$', _protect, text)
    text = re.sub(r'(?:^\|.+\|$\n?)+', _protect, text, flags=re.MULTILINE)
    text = re.sub(r'\[image:[^\]]+\]', _protect, text)
    text = re.sub(r'\[图表\][^\n]*', _protect, text)

    # ── 第2步：正常切分 ──
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                sub_chunks = _split_long_paragraph(para, max_chars, overlap)
                chunks.extend(sub_chunks)
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)

    # ── 第3步：还原占位符 ──
    restored = []
    for chunk in chunks:
        for key, val in placeholders.items():
            chunk = chunk.replace(key, val)
        restored.append(chunk)

    return restored
