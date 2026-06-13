<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/Status-Active-green?style=flat-square" alt="Active">
  <img src="https://img.shields.io/badge/Stage-MVP-red?style=flat-square" alt="MVP">
  <img src="https://img.shields.io/github/license/shiyao222333-afk/knowledge-forge?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/github/stars/shiyao222333-afk/knowledge-forge?style=social" alt="Stars">
</p>

<h1 align="center">🔥 KnowledgeForge / 知炬</h1>

<p align="center">
  <b>个人知识库管理系统</b><br>
  从碎片化文档到可对话的活知识库，让 AI 真正理解你的资料
</p>

<p align="center">
  <a href="#-项目愿景"><b>项目愿景</b></a> ·
  <a href="#-快速开始"><b>快速开始</b></a> ·
  <a href="#-流程图"><b>流程图</b></a> ·
  <a href="#-路线图"><b>路线图</b></a> ·
  <a href="https://github.com/shiyao222333-afk/knowledge-forge/issues"><b>提 Issue</b></a> ·
  <a href="https://github.com/shiyao222333-afk/knowledge-forge/blob/main/DEVELOPMENT_HISTORY.md"><b>开发历程</b></a>
</p>

---

## ✨ 一句话介绍

> 把你的截图、手册、笔记丢进去，问一个问题，直接得到**带来源引用的答案**。
> 数据全在本地，不联网也能用。

```bash
# 1. 启动（首次）
.\start.bat

# 2. 摄入资料（支持图片/文本/Word/PDF）
python kb_query.py --ocr "齿轮手册截图.jpg" --source "齿轮设计手册-P23"
python kb_query.py --ingest "设计笔记.txt"

# 3. 提问
python kb_query.py "模数2.5的齿轮外径是多少" --answer --llm-api-key sk-xxx
# → 生成 query_result.html，浏览器打开即可看到答案 + 原始素材来源
```

---

## 📐 它解决什么问题？

| 你的痛点 | KnowledgeForge 的方案 |
|----------|--------------------------|
| 几 GB 资料，想找一句话要翻半小时 | AI 语义搜索，直接给答案 |
| 截图里的文字搜不到 | PaddleOCR 识别图片文字，一并入库 |
| 表格/公式无法理解 | PPStructureV3 结构化识别，公式渲染为 LaTeX |
| 不知道答案从哪来的 | 每个回答都标注 `[引用N]`，可点击溯源 |
| 数据不敢上传云端 | 全本地运行，数据不出门 |
| 传统知识库只能搜文件名 | 语义理解，跨文档综合回答 |

---

## 🎯 核心特性

- 🔍 **语义搜索** — 不是关键词匹配，是真的理解你在问什么
- 🖼️ **图片 OCR** — 截图、照片、扫描件，自动识别文字并入库
- 📊 **表格精确引用** — 大表格按行拆分，引用精确到行（不只是整张表）
- 🔗 **引用连续化** — 回答里的引用编号永远是 1、2、3... 不跳跃
- 🧮 **公式渲染** — KaTeX 服务端渲染，LaTeX 公式正确显示
- 📄 **HTML 报告** — 双层结构：干净回答 + 可展开的原始素材
- 🔐 **本地优先** — 向量库和嵌入模型全在本地，隐私零泄露
- 🔗 **IMA 联动** — 支持从 IMA 知识库同步内容（`sync_ima.py`）

---

## 📊 操作流程图

> 完整 Mermaid 流程图（10 张图：架构、摄入、查询、引用优化、序列图）👉  
> **[点此查看 flow_diagram.md](flow_diagram.md)**

GitHub 原生渲染 Mermaid，点击上方链接即可看到全部流程图。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python 包
pip install requests fpdf2 pillow paddlepaddle paddleocr "paddlex[ocr]==3.7.0"

# Ollama（本地嵌入模型）
# 从 https://ollama.com 安装，然后拉取模型：
ollama pull qwen3-embedding:4b

# KaTeX（公式渲染，可选）
npm install -g katex
```

### 2. 启动服务

```bash
.\start.bat   # 启动 Qdrant + Ollama（Windows）
```

### 3. 摄入你的资料

```bash
# 文本文件直接入库
python kb_query.py --ingest "D:/Documents/齿轮设计基础.txt"

# 图片 OCR 后入库（自动识别公式/表格）
python kb_query.py --ocr "photo.jpg" --source "手册-P23"

# OCR 后先预览再决定是否入库
python kb_query.py --ocr "photo.jpg" --check-only
```

### 4. 提问！

```bash
# 端到端问答（搜索 → LLM 合成 → HTML 报告）
python kb_query.py "齿轮的失效形式有哪些" --answer --llm-api-key sk-xxx
# 报告保存于 query_result.html，用浏览器打开

# 纯搜索（不调用 LLM，只查看相关素材）
python kb_query.py "齿轮参数表" --top 10
```

---

## 🧭 项目愿景

我们把知识库管理系统的发展分为三个阶段：

```
阶段一（当前）：个人知识库工具
  → 摄入、搜索、问答、引用标注

阶段二（规划中）：知识图谱 + 多模态
  → 自动建立知识点关联、图表理解、手写笔记

阶段三（更远未来）：完全本地智能
  → 本地 LLM、CAD 插件联动、团队协作知识库
```

**最终目标**：一个完全属于你自己的、会成长的、本地运行的知识大脑。

---

## 🗺️ 路线图

### v0.2 — 知识库管理面板
- [ ] Web UI：上传/删除/预览知识库中的文档
- [ ] 知识库统计：文档数量、覆盖主题、存储占用
- [ ] 批量摄入：拖拽上传整个文件夹

### v0.3 — 知识图谱雏形
- [ ] 自动提取文档中的实体（公式、参数、概念）
- [ ] 建立知识点之间的关联关系
- [ ] 问答时展示相关知识网络

### v0.4 — 多模态理解
- [ ] 图表理解：识别图中的曲线、趋势、标注
- [ ] 手写笔记 OCR 优化
- [ ] 视频帧提取 + 关键帧入库

### v0.5 — 知识库自进化
- [ ] 用户纠错反馈 → 自动优化入库质量
- [ ] 定期重新嵌入（模型升级时）
- [ ] 知识库版本管理（快照/回滚）

---

## 🏗️ 架构概览

```
KnowledgeForge（分层架构）

┌─────────────────────────────────────────────┐
│  用户层：CLI / Web UI（规划中）           │
├─────────────────────────────────────────────┤
│  服务层：问答合成 · 引用管理 · 报告生成 │
├─────────────────────────────────────────────┤
│  核心层：向量检索 · OCR · 嵌入           │
├─────────────────────────────────────────────┤
│  存储层：Qdrant（向量）· 文件系统      │
└─────────────────────────────────────────────┘
```

**技术栈**：
- 向量数据库：[Qdrant](https://github.com/qdrant/qdrant)
- 嵌入模型：[Ollama](https://github.com/ollama/ollama) + `qwen3-embedding:4b`
- OCR 引擎：[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) / PPStructureV3
- LLM 合成：OpenAI 兼容 API（默认 DeepSeek）
- 公式渲染：[KaTeX](https://github.com/KaTeX/KaTeX)

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `KB_LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `KB_LLM_API_KEY` | LLM API Key | （必须自行设置） |
| `KB_LLM_MODEL` | LLM 模型名 | `deepseek-chat` |

### 常用参数

```bash
# 表格行数 > 4 时按行拆分引用（可调整）
python kb_query.py "转动惯量公式" --answer --table-split-threshold 3

# 搜索相关度阈值（默认 0.3，越高越严格）
python kb_query.py "查询词" --threshold 0.5

# 限制送入 LLM 的 chunk 数量（避免超 context）
python kb_query.py "查询词" --answer --max-chunks 8
```

---

## 📸 输出示例

**（规划中：此处将添加知识库管理界面截图和 HTML 报告截图）**

当前可通过以下命令生成 HTML 报告预览：

```bash
python kb_query.py "你的问题" --answer --llm-api-key sk-xxx
# 报告保存于 query_result.html，用浏览器打开即可查看
```

---

## 🤝 贡献指南

欢迎参与！这个项目处于早期阶段，每一份贡献都能显著影响方向。

### 你可以怎么参与

- 🐛 **报告 Bug**：[提交 Issue](https://github.com/shiyao222333-afk/knowledge-forge/issues/new?template=bug_report.yml)
- 💡 **提议新功能**：[功能请求](https://github.com/shiyao222333-afk/knowledge-forge/issues/new?template=feature_request.yml)
- 💻 **提交代码**：Fork → 分支 → PR
- 📖 **完善文档**：路线图、使用案例、最佳实践

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [Ollama](https://github.com/ollama/ollama) - 本地 LLM 运行环境
- [KaTeX](https://github.com/KaTeX/KaTeX) - 公式渲染
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 中文 OCR

---

<p align="center">
  ⭐ 如果这个方向对你有启发，请给一个 Star！<br>
  🗂️ 让每个人的知识积累，都变成真正的资产。
</p>
