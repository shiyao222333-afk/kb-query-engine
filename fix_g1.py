#!/usr/bin/env python3
"""Fix G1: enhance normalize_facet_values() to use FUZZY_FACET_MAPPING."""
import re

with open('D:/citrinitas/config/classifications.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 替换 normalize_facet_values() 函数 ──
old_func_start = 'def normalize_facet_values(metadata: dict) -> dict:'
old_func_end = '\n\ndef '  # next function

# Find the function
start_idx = content.find(old_func_start)
if start_idx == -1:
    print("❌ 找不到 normalize_facet_values() 函数")
    exit(1)

end_idx = content.find(old_func_end, start_idx + len(old_func_start))
if end_idx == -1:
    # Maybe it's the last function in the file
    end_idx = content.find('\n# ──', start_idx + len(old_func_start))
    if end_idx == -1:
        print("❌ 找不到函数结束位置")
        exit(1)

old_func = content[start_idx:end_idx]

# ── 新函数 ──
new_func = '''def normalize_facet_values(metadata: dict) -> dict:
    """
    枚举守卫：验证并规范化分面字段值。
    
    在 LLM 返回结果后、写入 Qdrant 前执行：
        LLM 返回 → normalize_facet_values() → 严格枚举值 → 写入 Qdrant
    
    核心逻辑：
        1. 查 FUZZY_FACET_MAPPING（LLM 常见跑偏 → 标准 key）
        2. 单选枚举（content_type / temporal_nature / epistemic_status）
           → 标准化空格/大小写/中英文 → 精确匹配 → fallback 默认值
        3. 多选列表（domain）
           → 逐项标准化 → 去重
        4. 数值字段（trust_score）
           → 确保在合法范围内
    
    返回：规范化后的 metadata（原地修改 + 返回）
    """
    # ── 辅助：模糊查表 ──
    def _fuzzy(value, mapping):
        """查 FUZZY_FACET_MAPPING，返回标准 key 或 None。"""
        if not value or not mapping:
            return None
        v = value.strip()
        # 1. 精确匹配（区分大小写）
        if v in mapping:
            return mapping[v]
        # 2. 大小写不敏感匹配
        v_lower = v.lower()
        for k, v2 in mapping.items():
            if k.lower() == v_lower:
                return v2
        # 3. 部分匹配（如 "视频脚本" in mapping keys）
        for k, v2 in mapping.items():
            if v in k or k in v:
                return v2
        return None

    # ── content_type：单选，15 种 ──
    ct = metadata.get("content_type")
    if ct and isinstance(ct, str):
        ct_norm = ct.strip().lower().replace(" ", "_")
        # 1. 查模糊映射表
        mapped = _fuzzy(ct, FUZZY_FACET_MAPPING.get("content_type", {}))
        if mapped and mapped in CONTENT_TYPES:
            metadata["content_type"] = mapped
        # 2. 精确匹配
        elif ct_norm in CONTENT_TYPES:
            metadata["content_type"] = ct_norm
        # 3. 子串匹配
        else:
            for valid_key in CONTENT_TYPES.keys():
                if valid_key in ct_norm or ct_norm in valid_key:
                    metadata["content_type"] = valid_key
                    break
            else:
                metadata["content_type"] = "other"  # fallback
    
    # ── domain：多选列表，9 种 UDC 主类 ──
    dom = metadata.get("domain")
    if dom:
        if isinstance(dom, str):
            dom = [d.strip() for d in dom.split(",")]
        elif not isinstance(dom, list):
            dom = [str(dom)]
        normalized = []
        for d in dom:
            d_norm = d.strip()
            # 1. 查模糊映射表
            mapped = _fuzzy(d, FUZZY_FACET_MAPPING.get("domain", {}))
            if mapped and mapped in DOMAINS:
                normalized.append(mapped)
            # 2. 精确匹配
            elif d_norm in DOMAINS:
                normalized.append(d_norm)
            # 3. 子串匹配（中文描述）
            else:
                for valid_key in DOMAINS.keys():
                    if valid_key in d_norm or d_norm in valid_key:
                        normalized.append(valid_key)
                        break
        metadata["domain"] = list(dict.fromkeys(normalized))  # 去重保持顺序
    
    # ── temporal_nature：单选，3 种 ──
    tn = metadata.get("temporal_nature")
    if tn and isinstance(tn, str):
        tn_norm = tn.strip().lower()
        # 1. 查模糊映射表
        mapped = _fuzzy(tn, FUZZY_FACET_MAPPING.get("temporal_nature", {}))
        if mapped and mapped in TEMPORAL_NATURE:
            metadata["temporal_nature"] = mapped
        # 2. 精确匹配
        elif tn_norm in TEMPORAL_NATURE:
            metadata["temporal_nature"] = tn_norm
        # 3. 子串匹配
        else:
            for valid_key in TEMPORAL_NATURE.keys():
                if valid_key in tn_norm or tn_norm in valid_key:
                    metadata["temporal_nature"] = valid_key
                    break
            else:
                metadata["temporal_nature"] = "timeboxed"  # fallback
    
    # ── epistemic_status：单选，3 种 ──
    es = metadata.get("epistemic_status")
    if es and isinstance(es, str):
        es_norm = es.strip().lower()
        # 1. 查模糊映射表
        mapped = _fuzzy(es, FUZZY_FACET_MAPPING.get("epistemic_status", {}))
        if mapped and mapped in EPISTEMIC_STATUS:
            metadata["epistemic_status"] = mapped
        # 2. 精确匹配
        elif es_norm in EPISTEMIC_STATUS:
            metadata["epistemic_status"] = es_norm
        # 3. 子串匹配
        else:
            for valid_key in EPISTEMIC_STATUS.keys():
                if valid_key in es_norm or es_norm in valid_key:
                    metadata["epistemic_status"] = valid_key
                    break
            else:
                metadata["epistemic_status"] = "unverified"  # fallback
    
    # ── trust_score：数值，0-5 ──
    ts = metadata.get("trust_score")
    if ts is not None:
        try:
            ts_int = int(ts)
            metadata["trust_score"] = max(0, min(5, ts_int))
        except (ValueError, TypeError):
            metadata["trust_score"] = 3  # fallback 中等可信
    
    # ── knowledge_type：单选，11 种（仅 content_type="knowledge" 时有效）──
    kt = metadata.get("knowledge_type")
    if kt and isinstance(kt, str):
        kt_norm = kt.strip().lower().replace(" ", "_")
        # 1. 查模糊映射表
        mapped = _fuzzy(kt, FUZZY_FACET_MAPPING.get("knowledge_type", {}))
        if mapped and mapped in KNOWLEDGE_TYPES:
            metadata["knowledge_type"] = mapped
        # 2. 精确匹配
        elif kt_norm in KNOWLEDGE_TYPES:
            metadata["knowledge_type"] = kt_norm
        # 3. 子串匹配
        else:
            for valid_key in KNOWLEDGE_TYPES.keys():
                if valid_key in kt_norm or kt_norm in valid_key:
                    metadata["knowledge_type"] = valid_key
                    break
            else:
                metadata["knowledge_type"] = "concept"  # fallback
    
    return metadata
'''

# 替换
new_content = content[:start_idx] + new_func + content[end_idx:]

with open('D:/citrinitas/config/classifications.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ G1: normalize_facet_values() 已增强，使用 FUZZY_FACET_MAPPING 映射表")
