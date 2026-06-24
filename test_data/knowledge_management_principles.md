# 知识管理核心原则

## 1. 分面分类法（Faceted Classification）

分面分类法是一种灵活的知识组织方式，允许单个知识条目同时属于多个类别。

### 1.1 四个分面

| 分面 | 字段名 | 枚举值 |
|------|--------|--------|
| 内容类型 | content_type | standard, case_study, design_reference, trouble_shooting, data_record, method, concept, tool, news, discussion, original_document, personal_note, meeting_note, decision, plan, other |
| 领域 | domain | UDC 9 主类（0-9） |
| 时效属性 | temporal_nature | evergreen, timeboxed, transient |
| 认知验证状态 | epistemic_status | unverified, substantiated, corroborated |

### 1.2 搜索场景

- **场景 A**：找永久有效的原理性知识 → temporal_nature=evergreen
- **场景 B**：找可能有价值但需要验证时效的信息 → temporal_nature=timeboxed
- **场景 C**：只看已验证的知识（L2） → epistemic_status=corroborated
- **场景 D**：找需要验证的假设（L0） → epistemic_status=unverified

## 2. WLNK（Weakest Link）信任聚合

知识条目的总体置信度由最弱证据决定：
R_eff = min(evidence_scores)

## 3. 混合检索（Hybrid Search）

结合稠密向量（语义相似度）和稀疏向量（关键词匹配）：
- 稠密向量：qwen3-embedding:4b, 2560 维, Cosine 距离
- 稀疏向量：BM25, bge-reranker-v2-m3 重排序