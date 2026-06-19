#!/usr/bin/env python3
"""Fix G2: implement L2 pipeline (file metadata → UDC inference) in auto_classify()."""
import re

with open('D:/citrinitas/kb_query.py', 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# ── Fix 1: Move keyword_domain_map BEFORE L2 ──
# Currently keyword_domain_map is defined inside L3 (after L2 comment).
# We need to move it BEFORE L2 so L2 can use it.
# Actually, easier approach: just implement L2 using the SAME keyword_domain_map.
# But keyword_domain_map is defined in L3. Let me check...

# Actually, looking at the code, keyword_domain_map is defined at line 2018-2025 (inside auto_classify()).
# L2 is at line 2014: "# L2（文件元数据）：无文件扩展名信息，跳过"
# L3 is at line 2016: "# L3（关键词匹配）：根据文本内容推断 domain"
# So keyword_domain_map is defined in L3, which is AFTER L2.
# I need to MOVE keyword_domain_map BEFORE L2.

# Let me find the exact string...
old_l2_l3 = """    # ── L1-L3 四层管道（简化版）──
    # L1（模板默认）：如果 metadata 已提供值，优先使用
    result = metadata.copy() if metadata else {}
    
    # L2（文件元数据）：无文件扩展名信息，跳过
    
    # L3（关键词匹配）：根据文本内容推断 domain
    text_lower = text.lower()
    keyword_domain_map = {"""

if old_l2_l3 in content:
    # Move keyword_domain_map before L2
    new_l2_l3 = """    # ── L1-L3 四层管道（简化版）──
    # L1（模板默认）：如果 metadata 已提供值，优先使用
    result = metadata.copy() if metadata else {}
    
    # 关键词→domain 映射表（L2/L3 共用）
    keyword_domain_map = {
        "齿轮|模数|强度|公差|机械设计": ["6"],
        "ai|llm|模型|深度学习|神经网络": ["0"],
        "标准|国标|iso|gb/t": ["0", "6"],
        "公式|定理|数学": ["5"],
        "程序|代码|python|javascript": ["0"],
        "设计|ux|ui|排版": ["7"],
    }
    
    # L2（文件元数据）：从 metadata 提取关键词，推断 domain
    if "domain" not in result or not result["domain"]:
        # 从 metadata 提取可用来推断 domain 的字段
        meta_text = " ".join([
            str(metadata.get("title", "")),
            str(metadata.get("author", "")),
            " ".join(metadata.get("keywords", [])),
            metadata.get("source", ""),
        ]).lower()
        # 复用 keyword_domain_map
        for kw_pattern, domains in keyword_domain_map.items():
            if any(kw in meta_text for kw in kw_pattern.split("|")):
                result["domain"] = domains
                break
    
    # L3（关键词匹配）：根据文本内容推断 domain
    if "domain" not in result or not result["domain"]:
        text_lower = text.lower()
        for kw_pattern, domains in keyword_domain_map.items():
            if any(kw in text_lower for kw in kw_pattern.split("|")):
                result["domain"] = domains
                break
    
    # L4（LLM 推断）：..."""
    if new_l2_l3 in content:
        print("❌ 新字符串也已存在（可能已修复），跳过")
    else:
        content = content.replace(old_l2_l3, new_l2_l3, 1)
        count += 1
        print("✅ Fix G2: L2 管道已实现，keyword_domain_map 移到 L2 前")
else:
    print("❌ 未找到 L1-L3 代码块，尝试模糊匹配...")
    # Try to find the L2 comment
    if "# L2（文件元数据）：无文件扩展名信息，跳过" in content:
        print("  找到 L2 占位符，直接替换...")
        old_l2 = "# L2（文件元数据）：无文件扩展名信息，跳过"
        new_l2 = """    # L2（文件元数据）：从 metadata 提取关键词，推断 domain
    if "domain" not in result or not result["domain"]:
        # 从 metadata 提取可用来推断 domain 的字段
        meta_text = " ".join([
            str(metadata.get("title", "")),
            str(metadata.get("author", "")),
            " ".join(metadata.get("keywords", [])),
            metadata.get("source", ""),
        ]).lower()
        # 复用 L3 的 keyword_domain_map
        for kw_pattern, domains in keyword_domain_map.items():
            if any(kw in meta_text for kw in kw_pattern.split("|")):
                result["domain"] = domains
                break"""
        # But keyword_domain_map is defined LATER (in L3). Need to move it before L2.
        print("  ⚠️  need to move keyword_domain_map before L2")
        # Let me just do a more comprehensive fix...
        pass

print(f"\n共修复 {count} 处")
if count > 0:
    with open('D:/citrinitas/kb_query.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 已写入 kb_query.py")
else:
    print("⚠️  未做任何修改")
