# Changelog

本文档记录 KB Query Engine 的所有 notable changes。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Added
- 待添加功能（见 PROJECT_PLAN.md）

---

## [v0.4.1] - 2026-06-15

### Added
- ✨ 分面分类 v5.0：UDC 9 主类（国际十进分类法）替代自定义 9 域
- ✨ temporal_nature 分面：evergreen / timeboxed / transient（基于 RMS-Ltd doc-lifecycle-metadata-spec）
- ✨ epistemic_status 分面：unverified / substantiated / corroborated（基于 FPF arxiv 2601.21116）
- ✨ udc_code 普通字段：LLM 自由输出 UDC 细分码 / 复合类号
- ✨ NiceGUI SPA 迁移：FastAPI + Vue + Quasar + WebSocket 替代 Streamlit
- ✨ auto_classify() 增强：四层管道（模板默认值 → 文件元数据 → 关键词匹配 → LLM 推断）
- ✨ normalize_facet_values() 枚举守卫：保证 Payload Index 值合法
- ✨ DOMAIN_MIGRATION_MAP：旧 9 域 → UDC 9 主类迁移映射

### Changed
- 🔄 domain 分面：9 大中文主题域 → UDC 9 主类（0-9）
- 🔄 lifecycle + project_source 降级为普通字段（仍支持 filter）
- 🔄 Payload Index：lifecycle/project_source → temporal_nature/epistemic_status
- 🔄 auto_classify() 推理字段增加：domain/temporal_nature/epistemic_status/udc_code
- 🔄 Web UI：Streamlit 多页面 → NiceGUI 单文件 SPA（main.py）
- 🔄 旧 Streamlit 文件归档至 _archive/

### Removed
- ❌ objectivity 字段（被 content_type + epistemic_status 联合覆盖）
- ❌ project_source 硬编码 5 项选项（改为自由文本）

---

## [v0.4.0] - 2026-06-15

### Added
- ✨ LLM 自动分类：auto_classify(text) 推断 content_type/domain/keywords/trust_score 等
- ✨ 两阶段摄入管线：内容确认 → AI 分析 + 微调 → 入库
- ✨ 共享表单组件：utils/ingest_ui.py，三 Tab 统一调用（消减 ~200 行重复代码）
- ✨ AI 分析结果可视化：5 列度量卡片（内容类型/主题域/关键词/可信度/生命周期）
- ✨ 智能默认值：手动输入默认 content_type=idea，文件/OCR 默认 knowledge

### Changed
- 🔄 文档注入页面重构：660 行 → ~240 行
- 🔄 三 Tab 表单去重：共享 render_facet_form() + build_facet_metadata()
- 🔄 auto_classify() 字段合法性校验 + 默认值回退

### Fixed
- 🐛 手动输入/OCR/Alembic 推送内容无本地源文件时 source_path 处理

---

## [v0.3.0] - 2026-06-15

### Added
- ✨ 分面分类 v4.0：15 种内容类型 × 9 大主题域 × 6 级生命周期
- ✨ 通用关系字段：8 种关系类型（similar/references/contradicts/derived_from...）
- ✨ 分组字段：timeline/origin/stats（15 个独立字段压缩为 3 个嵌套对象）
- ✨ 知识管理面板：可信度编辑 / 归档开关 / 主版本标记 / 关系管理
- ✨ 分面统计仪表盘：内容类型/主题域/生命周期分布可视化
- ✨ 5 个新增 API：get_facet_stats / update_metadata / set_doc_relations / search_by_doc_id / get_doc_ids
- ✨ 搜索结果富展示：Badge / 关键词 / 关系链 / 可信度星标
- ✨ 12 个预留扩展字段（ext_text1-5 / ext_num1-3 / ext_bool1-3 / ext_date1-3）
- ✨ TARGET_PLATFORM_OPTIONS（9 种目标平台）/ LANGUAGE_OPTIONS / ACCESS_LEVEL_OPTIONS

### Changed
- 🔄 字段精简：49 → 36 字段，通用分组合并 15 个独立字段
- 🔄 摄入 Payload 从 22 字段升级为 36 字段 v4.0 分组结构
- 🔄 分面过滤从 should/min_should 改为 must + match 语法
- 🔄 Qdrant Payload Index 从 0 个扩展到 11 个
- 🔄 set_payload API 替代旧 PUT /points 端点
- 🔄 _source_to_meta() 标记弃用

### Fixed
- 🐛 Qdrant facet filter should/min_should 语法失效 → 改为 must + match
- 🐛 update_metadata PUT /points 404 → 改为 POST /points/payload
- 🐛 ingest title=None 时 fallback 不生效
- 🐛 search_multi source 字段读取 "file_name" → 改为 "source"
- 🐛 pages/2_智能检索.py selected_cols 拼写错误 → selected_col
- 🐛 pages/0_关于.py 两个 col2 列冲突

### Removed
- ❌ content_stage / task_id / updated_at / quality_score / category（旧层级分类字段）
- ❌ book / chapter / page 扁平字段（由 origin 分组替代）

---

## [v0.2.0] - 2026-06-14

### Added
- ✨ Streamlit 多页面架构（app.py + 4 页面导航）
- ✨ 文档注入页面：上传 / OCR / 手动输入 + LLM 优化 + 手动编辑
- ✨ 智能检索页面：搜索 + AI 问答合并，跨库多选
- ✨ 知识中枢页面：卡片仪表盘 + 首次建库向导 + 集合管理
- ✨ 引擎配置页面：LLM 预设（5 个）+ 在线获取模型 + 嵌入模型管理
- ✨ st.dialog 原生弹窗确认（清空 / 删除操作）
- ✨ 缓存优化：精确清理替代全量清除
- ✨ 像素火焰背景动画（欢迎页）
- ✨ utils/ui_utils.py：共享侧边栏 / 缓存 / save_env
- ✨ utils/flame_bg.py：火焰背景渲染

### Changed
- 🔄 核心逻辑（kb_query.py）与 UI 层完全分离
- 🔄 配置用环境变量 + .env，路径用相对路径
- 🔄 LLM 后端切换至 DeepSeek API（OpenAI 兼容）

### Fixed
- 🐛 8 个严重 Bug + 7 个重要 Bug（详见 DEVELOPPMENT_HISTORY.md）

---

## [v0.1.0] - 2026-06-14

### Added
- ✨ OCR 摄入功能（PaddleOCR / PPStructureV3）
- ✨ 向量搜索（Qdrant + qwen3-embedding:4b）
- ✨ LLM 合成（DeepSeek API）+ 引用标注
- ✨ 表格行拆分（引用粒度控制）
- ✨ 引用重编号（连续不跳跃）
- ✨ KaTeX 服务端公式渲染
- ✨ HTML 报告生成（双层结构）
- ✨ `[补充]` 标记（非知识库内容标注）
- ✨ 去重过滤（SHA256 + 同源去重 + OCR质量过滤）

### Fixed
- 无（初始版本）

### Changed
- 无（初始版本）

---

## 版本说明

| 标签 | 含义 |
|------|------|
| `Added` | 新功能 |
| `Fixed` | Bug 修复 |
| `Changed` | 功能变更 |
| `Deprecated` | 即将移除的功能 |
| `Removed` | 已移除的功能 |
| `Security` | 安全问题 |
