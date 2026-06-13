<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/Status-Active-green?style=flat-square" alt="Active">
  <img src="https://img.shields.io/badge/Stage-MVP-red?style=flat-square" alt="MVP">
  <img src="https://img.shields.io/github/license/shiyao222333-afk/kb-query-engine?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/github/stars/shiyao222333-afk/kb-query-engine?style=social" alt="Stars">
</p>

<h1 align="center">🗂️ KB Query Engine</h1>

<p align="center">
  <b>个人知识库管理系统</b><br>
  从碎片化文档到结构化知识，让 AI 真正理解你的资料
</p>

<p align="center">
  <a href="#-项目愿景"><b>项目愿景</b></a> ·
  <a href="#-当前进度"><b>当前进度</b></a> ·
  <a href="#-路线图"><b>路线图</b></a> ·
  <a href="#-快速开始"><b>快速开始</b></a> ·
  <a href="#-常见问题"><b>常见问题</b></a> ·
  <a href="https://github.com/shiyao222333-afk/kb-query-engine/issues"><b>提Issue</b></a>
</p>

---

## 🧭 项目愿景

> 你积累了几 GB 的技术文档、手册、笔记、截图 —— 但它们是「死资料」，找不到、用不上。
> **KB Query Engine 的目标：把这些碎片化资料，变成你可以对话的活知识库。**

### 我们不走传统知识库的老路

| 传统知识库 ❌ | KB Query Engine 的方向 ✅ |
|--------------|--------------------------|
| 全文搜索，靠人自己找 | AI 理解语义，直接给答案 |
| 文档格式受限（只支持PDF） | 图片/截图/OCR/文本全支持 |
| 搜索结果是一堆文件名 | 答案是综合的，附带来源引用 |
| 公式/表格/图表无法理解 | 结构化识别，理解表格每一行 |
| 数据必须上传云端 | 本地优先，数据不出门 |
| 用完就忘，无法积累 | 每次问答都在丰富知识图谱 |

**最终目标**：一个完全属于你自己的、会成长的、本地运行的知识大脑。

---

## 🚀 当前进度（MVP 阶段）

> 以下是 **已实现的基础能力**，作为后续开发的基石。当前版本定位为 **可验证核心假设的原型**。

### ✅ 已实现（v0.1.0）

- **文档摄入**：图片 OCR（PaddleOCR / PPStructureV3）+ 文本文件直接入库
- **向量搜索**：Qdrant + Ollama 本地嵌入模型，语义检索
- **引用合成**：LLM API 生成答案 + 标注来源引用 `[引用N]`
- **引用粒度控制**：大表格按行拆分，避免引用范围过大
- **公式渲染**：KaTeX 服务端渲染，HTML 报告中原生显示公式
- **HTML 报告**：双层结构（AI回答 + 原始素材），支持打印/分享
- **数据清洗**：入库 SHA256 去重；搜索结果同源去重 + OCR 质量过滤

### 🔜 近期规划（v0.2 ~ v0.5）

见 [路线图](#-路线图) 章节。

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

### 🌟 更远未来
- [ ] 多用户知识库（团队协作）
- [ ] 与 CAD / 设计软件插件联动（直接在设计软件里问技术参数）
- [ ] 本地 LLM 完整方案（完全离线运行）

---

## 🏗️ 架构概览

```
知识库管理系统（分层架构）

┌─────────────────────────────────────────────┐
│  用户层：CLI / Web UI（规划中）           │
├─────────────────────────────────────────────┤
│  服务层：问答合成 · 引用管理 · 报告生成 │
├─────────────────────────────────────────────┤
│  核心层：向量检索 · OCR · 嵌入           │
├─────────────────────────────────────────────┤
│  存储层：Qdrant（向量）· 文件系统（原图）│
└─────────────────────────────────────────────┘
```

**技术栈**：
- 向量数据库：[Qdrant](https://github.com/qdrant/qdrant)
- 嵌入模型：[Ollama](https://github.com/ollama/ollama) + `qwen3-embedding:4b`
- OCR引擎：[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) / PPStructureV3
- LLM合成：OpenAI 兼容 API（默认 DeepSeek）
- 公式渲染：[KaTeX](https://github.com/KaTeX/KaTeX)

---

## 📦 安装依赖

```bash
# Python 环境
pip install requests fpdf2 pillow

# PaddleOCR（中文 OCR）
pip install paddlepaddle paddleocr

# PPStructureV3（结构化识别，可选）
pip install "paddlex[ocr]==3.7.0"

# Ollama（嵌入模型运行环境）
# 从 https://ollama.com 安装，然后：
ollama pull qwen3-embedding:4b

# KaTeX（公式渲染，需要 Node.js）
npm install -g katex
```

---

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动 Qdrant + Ollama（Windows）
.\start.bat
```

### 2. 构建你的知识库

```bash
# 摄入文本文件
python kb_query.py --ingest "D:/Documents/KnowledgeBase/齿轮设计基础.txt"

# OCR 图片（自动识别公式/表格）
python kb_query.py --ocr "photo.jpg" --source "手册-P3"

# OCR 后先审核再入库
python kb_query.py --ocr "photo.jpg" --check-only
```

### 3. 向知识库提问

```bash
# 端到端问答（搜索 → LLM 合成 → HTML报告）
python kb_query.py "齿轮的失效形式有哪些" --answer --llm-api-key sk-xxx

# 纯搜索（不调用 LLM，查看原始素材）
python kb_query.py "齿轮参数表" --top 10
```

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

# 搜索相关度阈值（默认 0.3）
python kb_query.py "查询词" --threshold 0.5
```

---

## 📊 输出示例

**（规划中：此处将添加知识库管理界面的截图和HTML报告截图）**

当前可通过以下命令生成 HTML 报告预览：

```bash
python kb_query.py "你的问题" --answer --llm-api-key sk-xxx
# 报告保存于 query_result.html，用浏览器打开即可查看
```

---

## 🤝 贡献指南

欢迎参与！这个项目处于早期阶段，每一份贡献都能显著影响方向。

### 你可以怎么参与

- 🐛 **报告 Bug**：[提交 Issue](https://github.com/shiyao222333-afk/kb-query-engine/issues/new?template=bug_report.yml)
- 💡 **提议新功能**：[功能请求](https://github.com/shiyao222333-afk/kb-query-engine/issues/new?template=feature_request.yml)
- 💻 **提交代码**：Fork → 分支 → PR
- 📖 **完善文档**：路线图、使用案例、最佳实践

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [Ollama](https://github.com/ollama/ollama) - 本地LLM运行环境
- [KaTeX](https://github.com/KaTeX/KaTeX) - 公式渲染
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 中文OCR

---

<p align="center">
  ⭐ 如果这个方向对你有启发，请给一个 Star！<br>
  🗂️ 让每个人的知识积累，都变成真正的资产。
</p>
