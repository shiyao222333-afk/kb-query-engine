# Citrinitas — 项目主计划

> 本文档管理 **功能路线图** 和 **设计决策**。版本变更记录见 `CHANGELOG.md`，Bug 跟踪见 `ISSUES.md`。

最后更新: 2026-06-20

---

## 待验收清单

> 代码已修改、测试已通过，等待用户 L4 验收。

| 版本 | 日期 | 内容 | 验收项 |
|------|------|------|--------|
| v0.5.0 | 2026-06-20 | auto_classify 增强 + P2/P3 修复 | L2 管道（文件元数据→UDC 推断）生效；`normalize_facet_values()` 模糊映射生效；6 处 `except:pass` 有日志；`search()` 返回 `content_hash`/`doc_uid` |
| v0.4.9 | 2026-06-20 | P1 剩余问题修复 | `trust_score` 0-5 刻度统一；Payload Index 含 `needs_review`；`search_by_doc_id()` 返回 `needs_review` |
| v0.4.8 | 2026-06-19 | 搜索结果展示新字段 | 搜索结果卡片显示 content_type/domain/epistemic_status/temporal_nature/needs_review |
| v0.4.7 | 2026-06-19 | needs_review 过滤 | 文档管理页面可按 needs_review 状态过滤 |
| v0.4.6 | 2026-06-19 | AI 分析确认卡片 | 阶段2 AI 分析后显示确认卡片，用户可审核元数据再摄入 |
| v0.4.5 | 2026-06-18 | P1 问题修复（17项） | 见 CHANGELOG v0.4.5 Fixed 章节 |
| v0.4.4 | 2026-06-18 | 文档管理页面 + XSS 修复 | `/manage` 页面可列出/查看/删除文档；XSS 漏洞修复 |
| v0.4.3 | 2026-06-18 | 摄入管线 5 项 PATCH | language 真检测 / overlap 机制 / embed 容错 / source 防护 / images 多格式 |

---

## 一、版本路线图

> 按「地基 → 框架 → 墙体 → 装修 → 交付」逐层递进。

| 版本 | 状态 | 层级 | 代号 | 核心交付 |
|------|:----:|:--:|------|---------|
| v0.1.0 | ✅ | 地基 | 核心引擎 | CLI 向量搜索 + LLM 问答 + OCR + KaTeX |
| v0.2.0 | ✅ | 地基 | Web UI MVP | Streamlit 4 页面 |
| v0.3.0 | ✅ | 框架 | 分面分类 v4.0 | 36 字段分组 + 关系管理 |
| v0.4.0 | ✅ | 框架 | 智能摄入 | LLM 自动分类 + 两阶段管线 |
| v0.4.1 | ✅ | 框架 | 分面分类 v5.0 | UDC + temporal/epistemic + NiceGUI 迁移 |
| v0.4.2 | ✅ | 框架 | Bug 修复汇总 | 8 项 PATCH 修复 |
| v0.4.3 | ✅ | 框架 | 摄入管线修复 | 5 项 PATCH（language + overlap + embed 容错 + source + images） |
| v0.4.4 | ✅ | 框架 | 文档管理 + XSS 修复 | 文档管理页面 `/manage` + XSS 漏洞修复 |
| v0.4.5 | ✅ | 框架 | P1 问题修复 | 17 项 P1 修复（F1-F4, G1-G2, D1-D3, C1-C2, E1-E4） |
| v0.4.6 | ✅ | 框架 | AI 分析确认卡片 | 阶段2 AI 分析后显示确认卡片 |
| v0.4.7 | ✅ | 框架 | needs_review 过滤 | 文档管理页面添加审核状态过滤器 |
| v0.4.8 | ✅ | 框架 | 搜索结果展示增强 | 搜索结果卡片显示新字段 |
| v0.4.9 | ✅ | 框架 | P1 剩余问题修复 | D1+U7/S1/F4 修复 |
| v0.5.0 | 🚧 | 框架 | auto_classify 增强 + P2/P3 修复 | L2 管道（文件元数据→UDC 推断）+ `normalize_facet_values()` 模糊映射 + `except:pass` 加日志 |
| v0.6.0 | 🔮 | 框架 | 知识关系网 | NetworkX 图谱 + Plotly 可视化 |
| v0.7.0 | 🔮 | 墙体 | 检索增强 | QA 自动生成 + 图谱联动检索 |
| v0.8.0 | 🔮 | 装修 | 管线自动化 | YAML 配置化 + 守望文件夹 |
| v1.0.0 | 🔮 | 交付 | 生产就绪 | 插件协议 + 桌面端打包 |

---

## 二、当前版本：v0.5.0 🚧

### 目标

增强 `auto_classify()` 四层管道（L1-L4），补充 L2 文件元数据推断；修复 P2/P3 代码质量和健壮性问题。

### 技术栈

| 层 | 技术 |
|----|------|
| 向量库 | Qdrant（单集合 `athanor_v1`, 2560d, Cosine, 11 Payload Index） |
| 嵌入 | Ollama + qwen3-embedding:4b |
| LLM | DeepSeek API（OpenAI 兼容） |
| OCR | PaddleOCR / PPStructureV3 |
| 公式 | KaTeX（服务端渲染） |
| Web | NiceGUI 3.13（SPA, FastAPI + Vue + Quasar + WebSocket） |

### 已完成的修复（v0.5.0）

- [x] G2: L2 管道实现（文件元数据→UDC 推断）
- [x] G1: `normalize_facet_values()` 增强（模糊映射表）
- [x] C10: 为 6 处 `except:pass` 添加日志记录
- [x] D4: `_text_hash()` 16-bit → 32-bit（降低碰撞风险）
- [x] F6+S3: `search()` 返回 `content_hash` 字段
- [x] S4: `search()` 返回 `doc_uid` 字段

### 待修复（P2/P3 剩余）

- [ ] F8: `source_path` 未入库
- [ ] D5: 图片存绝对路径
- [ ] E3: XSS 防护复核
- [ ] C1-C3: `schema.md` 修正
- [ ] C6-C11: 僵尸文件清理
- [ ] N1-N5: `.env` 清理
- [ ] U1: `ingest_ui.py` 僵尸文件
- [ ] D6-D7: `ext_` 字段 + `facet_filter` 静默忽略
- [ ] S5: `get_facet_stats()` 全量 scroll

---

## 三、设计决策

> 可追溯的设计决策记录，避免未来重蹈覆辙。

### v0.5.0 决策（2026-06-20 确认）

| 决策点 | 结论 |
|--------|------|
| L2 管道 | 从 `metadata` 字段（title/author/keywords/source）提取文本，使用 `keyword_domain_map` 推断 UDC 主类 |
| 模糊映射 | `normalize_facet_values()` 使用 `FUZZY_FACET_MAPPING` 表（精确/大小写不敏感/部分匹配） |
| 异常处理 | 所有 `except:pass` 改为 `except Exception as e:` 并记录 `logger.warning` |
| content_hash | 使用 SHA256 前 32 位十六进制字符（原 16 位，碰撞风险高） |

### v0.4.5 决策（2026-06-15 确认）

| 决策点 | 结论 |
|--------|------|
| 元数据优先级 | 文件自带 > LLM 推断 > 用户手动 |
| 置信度路由 | < 0.5 审核队列；0.5–0.8 入库 + needs_review；≥ 0.8 直接入库 |
| 置信度计算 | 启发式 (JSON完整性 0.25 + 字段合法性 0.35 + 信息丰度 0.25 + 一致性 0.15) |
| 审核队列入口 | 知识中枢页面 |
| 文件大小上限 | 50MB，超限提示但允许继续 |
| 编码检测 | chardet → UTF-8 → GBK → latin-1 兜底链 |
| PDF 双路径 | pypdf 提取文字层 → 不足时 PaddleOCR 逐页 |

### v0.4.5 不做

- 批量文件摄入（v0.8.0 守望文件夹）
- EPUB/PDF 加密文件解密
- .doc（旧版 Word）/ .xlsx Excel 处理
- 守望文件夹触发策略
- 推送通知层（Server酱/邮件）

### v0.6.0 决策（2026-06-16 确认）

| 决策点 | 结论 |
|--------|------|
| 图谱后端 | NetworkX（零依赖），GEXF 序列化持久化 |
| 数据源 | 零 LLM 建图：Qdrant relations → NetworkX |
| 数据兜底 | relations 为空时，向量 Top-K 相似度生成 `similar` 边 |
| 可视化 | Plotly 力导向图，NiceGUI `ui.plotly` 渲染 |
| 嵌入位置 | 知识中枢页面 |
| 同步策略 | 惰性同步：dirty 标记 → 打开图谱页按需重建 |
| 节点着色 | domain 颜色 + epistemic_status 边框线型 |
| 边着色 | relation_type 颜色区分 |

---

## 四、竞品学习路线（2026-06-16 研究产出）

> 详细分析见 `docs/competitor-research-2026-06-16.md` 和 `docs/knowledge-graph-research-2026-06-16.md`

### 三条启发

| # | 启发方向 | 学自 | 核心想法 | Citrinitas 切入点 | 落地版本 |
|---|------|------|---------|-----------------|:--:|
| 1 | 知识关系网 | RAGFlow | NetworkX 内存图，实体+关系提取+图遍历 | 从已有关系字段建图（零 LLM），分面分类天然着色 | v0.6.0 |
| 2 | QA 自动生成 | FastGPT | 文档→LLM 拆成问答对→向量化 | 嵌入摄入管线，作为可选开关 | v0.7.0 |
| 3 | 管线配置化 | Dify | 摄入步骤 YAML 声明 | 步骤可配置/可跳过/可调参 | v0.8.0 |

### 学习优先级

| 优先级 | 内容 | 难度 | 落地 |
|:--:|------|:--:|:--:|
| 1 | 知识关系网：Schema 定稿 + NetworkX + 可视化 | 🟡 中 | v0.6.0 |
| 2 | API 熔断机制 | 🟢 低 | v0.6.0 |
| 3 | QA 自动生成摄入模式 | 🟢 低 | v0.7.0 |
| 4 | LLM 关系发现（按需触发） | 🟡 中 | v0.7.0 |
| 5 | 管线 YAML 配置化 | 🟢 低 | v0.8.0 |
| 6 | 双队列异步摄入 | 🟡 中 | v0.8.0 |
| 7 | 插件协议（MCP/OpenAPI） | 🔴 高 | v1.0.0 |
| 8 | 工作流可视化编排 | 🔴 高 | v1.0.0 |
| 9 | 桌面端一键打包 | 🟡 中 | v1.0.0 |

### 不做什么

- ❌ 照搬 GraphRAG 社区发现+摘要（个人 KB 不需要，LLM 成本高）
- ❌ 引入 Neo4j（NetworkX 零依赖足够）
- ❌ 从零实体提取（分面分类已定义知识维度）
- ❌ 完整的可视化工作流编辑器（YAML 配置足够）

---

## 五、架构原则（不可变）

1. **非必要不用大模型** — 尽可能由固定程序完成
2. **核心逻辑与 UI 完全解耦** — 面向未来多端交互
3. **输出统一 JSON 结构化数据** — search/ingest/answer 返回值均为 dict
4. **配置用环境变量** — KB_LLM_BASE_URL/KEY/MODEL, KB_EMBED_MODEL 等
5. **本地优先** — 向量库本地、嵌入模型本地，仅 LLM 合成需联网

---

## 六、远期待办

> 不在当前版本计划中，作为未来参考。

### 搜索词 → 分面自动推断

LLM 解析搜索词自动生成分面过滤条件（如 "齿轮国标" → domain:["6"] + content_type:"standard"）。

### 个人内容分类深化

当前 content_type 有 `personal_note` 兜底，但个人生活文件分类颗粒度不足：
- `content_type` 可扩展子类：`medical_record` / `financial_doc` / `diary`
- 配套隐私/访问权限机制（`access_level` 落地实现）
- domain 推断规则优化：`personal_note` 类型的 domain 默认 → 哲学/心理学(1)

### FPF 信任聚合（WLNK）→ 并入 Albedo

arxiv 2601.21116 WLNK 原则不放在 Citrinitas，作为 Albedo（炼真）的核心功能。

### project_source 升级路径

当前为普通自由文本字段。未来可升级为分面（Payload Index），需配合 LLM 项目推断。

### 关键词→UDC 映射增强

当前 L3 关键词→UDC 映射表仅 52 条，待积累后增强为规则引擎。

### normalize_facet_values() 独立化

当前 auto_classify() 内联校验。未来独立为函数，统一入口供所有摄入路径调用。

### 旧域数据迁移

执行 `DOMAIN_MIGRATION_MAP`，为历史数据补充 temporal_nature/epistemic_status 默认值。

### 🔬 待深入研究（2026-06-18 标记）

> 以下问题已在 v0.4.3 做了最小可行实现，未来需做竞品调研/论文检索/技术验证后升级。

| # | 问题 | 状态 | 复杂度 | 未来研究方向 |
|---|------|:--:|:--:|------|
| R1 | **切块 overlap 机制** | ✅ v0.4.3 尾部→头部拼接 | 🟡 中 | 句边界语义感知 vs 固定字符窗口；各竞品（RAGFlow/Dify/LlamaIndex）的 overlap 策略对比 |
| R2 | **图片引用多格式提取** | ✅ v0.4.3 Markdown + HTML + 自有格式 | 🟡 中 | OCR 内嵌图的统一提取管道；图片与文本 chunk 的关联保持；Base64 内联图片支持 |

---

## 七、管理文件体系

| 文件 | 用途 |
|------|------|
| `PROJECT_PLAN.md` | 功能路线图 + 设计决策（本文件） |
| `CHANGELOG.md` | 版本变更日志 |
| `ISSUES.md` | Bug 跟踪 |
| `README.md` | 项目门面 |
| `docs/schema.md` | 字段设计文档 |
| `WEB_UI_PLAN.md` | v0.2 Web UI 任务清单（已归档） |
| `DEVELOPMENT_HISTORY.md` | 开发过程记录 |
| `COMPARISON.md` | 同类工具对比 |
