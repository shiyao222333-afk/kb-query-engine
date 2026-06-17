# Athanor 测试报告 — v0.4.5

> 测试日期: 2026-06-16
> 测试范围: BUG修复验证 + 核心API功能 + NiceGUI启动

---

## 一、BUG修复清单（11个）

### 🔴 严重BUG — 已全部修复

| # | 位置 | 问题 | 症状 | 修复方式 |
|---|------|------|------|----------|
| 1 | `kb_query.py` | `ocr_image()` 函数不存在 | 上传图片OCR → AttributeError | 创建公共 `ocr_image()` 包装函数 |
| 2 | `main.py` L495 | `ingest()` 把文本当作 `file_path` | 摄入时报"文件不存在" | 改为 `text=` 关键字参数 |
| 3 | `kb_query.py` | `create_collection()` 不存在 | 创建集合 → AttributeError | 创建公共函数，带去重检查 |
| 4 | `main.py` L628 | `answer()` 返回 `synthesis`，代码用 `answer` | AI回答永远显示"无回答" | 改为 `synthesis` |
| 5 | `main.py` L631 | `answer()` 返回 `chunks`，代码用 `highlights` | 来源引用永远不显示 | 改为 `chunks` |
| 6 | `main.py` L650 | `search()` 返回 `chunks`，代码用 `results` | 搜索结果永远为空 | 改为 `chunks` |

### 🟡 中等BUG — 已全部修复

| # | 位置 | 问题 | 症状 | 修复方式 |
|---|------|------|------|----------|
| 7 | `main.py` L469 | `do_ingest` 同步阻塞 | 大文件摄入时UI卡死 | `async` + `asyncio.to_thread()` |
| 8 | `main.py` L619 | `do_search` 同步阻塞 | 搜索时UI卡死 | `async` + `asyncio.to_thread()` |
| 9 | `main.py` L259/337 | `on_upload`/`on_ocr` 临时文件不安全 | 可能冲突/泄露 | `tempfile.NamedTemporaryFile` + `finally`清理 |

### 🟢 低危BUG — 已全部修复

| # | 位置 | 问题 | 修复 |
|---|------|------|------|
| 10 | `main.py` 多处 | `.on("upload",...)` / `.on("click",...)` 语法错误 | 改为 `.on_upload()` / `.on_click()` |
| 11 | `main.py` | 清空按钮点击后只有提示 | 增加确认对话框 + `do_clear_collection()` |

---

## 二、自动测试结果

### 语法/导入检查 ✅

- `main.py` 语法编译: ✅
- `kb_query.py` 语法编译: ✅
- 18个 `kb_query.*` API函数: ✅ 全部存在且可调用
- `utils.file_handler` 导入: ✅
- `config.classifications` 导入: ✅

### 环境检查

- Qdrant 状态: ✅ 在线 (localhost:6333)
- Ollama 嵌入模型: ✅ `qwen3-embedding:4b` (2560维)
- NiceGUI 版本: ✅ 3.13.0 (API兼容)

### 核心API功能测试

| 测试项 | 结果 | 说明 |
|--------|------|------|
| `create_collection()` | ✅ | 创建新集合成功，重名拒绝正常 |
| `list_collections()` | ✅ | 返回所有集合及点数 |
| `ingest(text=..., metadata=...)` | ✅ | 文本嵌入→存储成功 |
| `search(query, top_k, collection)` | ✅ | 语义搜索正确返回相关文档（score=0.748） |
| `get_facet_stats(collection)` | ✅ | 分面统计正确：content_type/domain/temporal_nature/epistemic_status |
| `delete_collection()` | ✅ | 清理成功 |

### NiceGUI 服务

| 检查项 | 结果 |
|--------|------|
| 首页 `/` | ✅ HTTP 200 |
| 检索 `/search` | ✅ HTTP 200 |
| 知识中枢 `/hub` | ✅ HTTP 200 |
| 配置 `/config` | ✅ HTTP 200 |
| `ui.button.on_click()` | ✅ API可用 |
| `ui.upload.on_upload()` | ✅ API可用 |
| `ui.dialog().open()/close()` | ✅ API可用 |
| `asyncio.to_thread()` | ✅ 异步支持正确 |

---

## 三、无法自动测试的功能（需用户验证）

以下功能依赖外部环境（OCR引擎/LLM API Key），无法在无头环境中自动测试：

### A. OCR 图片识别
- **依赖**: PaddleOCR / PPStructureV3
- **测试方法**: 在摄入页面点击上传图片，观察OCR识别结果
- **预期**: 中文/英文/表格图片均可识别文字

### B. AI 自动分类
- **依赖**: Ollama LLM (如 `qwen3` 系列)
- **测试方法**: 在摄入页面点击「AI分析」按钮
- **预期**: 自动填充分面字段（content_type/domain/temporal_nature/epistemic_status）

### C. AI 问答搜索
- **依赖**: Ollama LLM
- **测试方法**: 在检索页面勾选「使用LLM」，输入问题
- **预期**: 返回基于知识库的合成回答 + 来源引用

### D. 文件上传摄入
- **依赖**: 无（已修复临时文件BUG）
- **测试方法**: 拖拽或选择 .txt/.md/.pdf 文件上传
- **预期**: 自动提取文本并填充到摄入区域

---

## 四、用户验收测试检查表

请按以下步骤进行端到端验收：

### 1. 启动验证
- [ ] 运行 `python main.py` 正常启动
- [ ] 浏览器访问 http://localhost:8080 看到摄入页面
- [ ] 四个Tab页签（摄入/检索/知识中枢/配置）可正常切换

### 2. 摄入流程
- [ ] 手动输入文本 + 填写分面表单 → 点击摄入按钮
- [ ] 上传文件 → 自动提取文本 → 填写分面 → 摄入
- [ ] 上传图片 → OCR识别 → 填入文本 → 分面 → 摄入
- [ ] 点击AI分析 → 自动填充分面 → 人工微调 → 摄入
- [ ] 摄入后显示成功通知

### 3. 检索流程
- [ ] 输入关键词 → 点击搜索 → 显示相关文档
- [ ] 勾选使用LLM → 输入问题 → 显示AI回答+来源引用
- [ ] 切换知识库集合 → 搜索

### 4. 知识中枢
- [ ] 查看当前集合的仪表盘统计
- [ ] 创建新集合
- [ ] 切换集合
- [ ] 清空集合（确认对话框正常）

### 5. 配置页面
- [ ] 查看当前LLM模型配置
- [ ] 查看/切换嵌入模型

### 6. 边界条件
- [ ] 空文本摄入 → 应提示内容为空
- [ ] 不选主题域摄入 → 应提示必填
- [ ] Qdrant离线时操作 → 应提示离线
- [ ] 大文件（>10MB）上传 → 应有提示

---

## 五、已知限制

1. **嵌入模型加载慢**: `qwen3-embedding:4b` (~2.5GB) 首次调用需等待加载
2. **OCR依赖PaddleOCR**: 需预先安装 `paddlepaddle` + `paddleocr`
3. **LLM依赖Ollama**: AI分析/问答需要本地运行Ollama + 至少一个LLM模型
4. **无认证机制**: 当前版本无登录/权限控制
