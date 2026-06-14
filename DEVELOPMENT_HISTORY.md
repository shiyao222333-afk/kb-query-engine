# 《知炬 Athanor》开发全记录

> 本文档记录了一个"个人知识库管理系统"从想法到 MVP 的完整开发过程。
> 适合作为技术分享视频的脚本素材，包含决策思路、踩坑记录、代码片段。
> 作者：SSS（B站UP主）
> 项目：https://github.com/shiyao222333-afk/kb-query-engine

---

## 一、项目起源：为什么要做这个？

### 痛点

我（SSS）日常积累了几 GB 的技术文档、产品手册、个人笔记、截图照片。
但这些资料是"死"的：

- 想找某个参数，要翻半天的文件夹
- 截图里的文字无法搜索
- 手册是 PDF，复制出来格式全乱
- 同一个知识点散落在 5 个文件里，没人帮你整理

市面上的知识库工具要么要上传云端（隐私问题），要么搜索就是关键词匹配（不够智能）。

### 目标

做一个**本地运行的**、**能理解中文技术文档的**、**可以对话的知识库系统**。

核心流程：
```
图片/文档 → OCR识别 → 向量化 → 存入知识库 → 提问 → AI回答（附带来源）
```

---

## 二、技术选型过程

### 2.1 向量数据库：为什么选 Qdrant？

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| FAISS | 老牌，性能好 | 没有服务端，管理麻烦 | ❌ |
| Chroma | 简单，Python友好 | 生产级功能少 | ❌ |
| **Qdrant** | 有REST API，支持过滤，Rust性能高 | 需要单独运行服务 | ✅ 选中 |

Qdrant 可以独立运行（二进制或 Docker），提供 HTTP API，非常适合本地工具场景。

### 2.2 嵌入模型：为什么用 Ollama + qwen3-embedding？

- OpenAI Embedding API：要联网，要花钱，数据要上传 → ❌
- 本地 Embedding 模型：离线，免费，数据不出门 → ✅

Ollama 可以本地运行 embedding 模型，`qwen3-embedding:4b` 是通义千问的嵌入模型，中文效果很好，4B 大小，普通显卡能跑。

### 2.3 OCR引擎：PaddleOCR vs Tesseract

| 方案 | 中文效果 | 表格识别 | 公式识别 |
|------|----------|----------|----------|
| Tesseract | 差 | 不支持 | 不支持 |
| **PaddleOCR** | 好 | 支持（PPStructure） | 支持（LaTeX输出） |
| EasyOCR | 一般 | 不支持 | 不支持 |

结论：PaddleOCR 是中文场景的最优解，PPStructureV3 还能识别表格结构。

### 2.4 LLM：为什么用 DeepSeek API？

本地跑 LLM 对显卡要求高（70B 模型需要多卡）。
作为个人工具，调用 API 更实际：便宜（每百万 token 几块钱），效果好。

同时架构上支持切换任意 OpenAI 兼容的 API（Qwen、GLM 等都可以）。

---

## 三、开发历程（按时间顺序）

---

### 阶段一：最小可用 —— OCR → 向量搜索 → 结果展示

**目标**：验证核心流程能不能跑通。

**实现内容**：

1. **OCR 摄入**（`--ocr` 模式）：
   - 用 PaddleOCR 识别图片中的文字
   - 用 PPStructureV3 识别表格和公式
   - 公式识别结果保存为 LaTeX 格式
   - 识别结果 + 元信息（来源、页码）存入 `local_data/`

2. **向量搜索**（`--ingest` 模式）：
   - 读取文本文件，按语义分块（chunk）
   - 调用 Ollama API 生成向量
   - 存入 Qdrant 集合 `kb_chunks`

3. **搜索展示**（直接运行 `python kb_query.py "查询词"`）：
   - 查询词向量化
   - Qdrant 相似度搜索
   - 返回 top-K 个 chunk，展示原文

**关键代码片段**（向量搜索核心）：

```python
# 查询词向量化
emb = ollama_embed(query)  # 调用 Ollama API

# Qdrant 搜索
results = client.search(
    collection_name="kb_chunks",
    query_vector=emb,
    limit=top_k,
    score_threshold=0.3
)
```

**踩坑记录**：

- **坑1**：PaddleOCR 第一次运行会自动下载模型（几百 MB），如果网络不好会卡住。→ 解决：提前手动下载模型文件。
- **坑2**：Ollama 默认只监听 localhost，跨进程调用没问题，但如果 Ollama 没启动会报错。→ 解决：`start.bat` 里先启动 Ollama 服务。

---

### 阶段二：LLM 合成回答 + 引用标注

**目标**：不只返回原始 chunk，而是让 LLM 综合多个 chunk 的内容，生成一段通顺的回答，并标注每句话的来源。

**实现方案**：

1. 把 top-K 个 chunk 的原文拼接到 Prompt 里
2. 要求 LLM 在回答中标注 `[引用N]`（N 对应第N个 chunk）
3. 解析 LLM 输出，提取回答和引用编号

**Prompt 设计**（核心）：

```
你是一个知识库助手。以下是检索到的相关资料：

[引用1] 原文内容...
[引用2] 原文内容...
...

请根据以上资料回答问题。要求：
1. 回答中用 [引用N] 标注信息来源
2. 如果资料不足以回答，明确说"资料中未提及"
3. 不要编造信息
```

**关键代码片段**（调用 LLM API）：

```python
resp = requests.post(
    f"{LLM_API_BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {LLM_API_KEY}"},
    json={
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    },
)
answer = resp.json()["choices"][0]["message"]["content"]
```

**踩坑记录**：

- **坑3**：LLM 有时候不按格式输出 `[引用N]`，而是写"根据资料1"... → 解决：在 Prompt 里加强调，并做后处理正则匹配。
- **坑4**：引用编号跳跃。比如有6个 chunk，但 LLM 只用了第5个，回答里就只有 `[引用5]`，读者会困惑。→ 这是后面的阶段四要解决的核心问题。

---

### 阶段三：HTML 报告生成

**目标**：把搜索结果和 LLM 回答做成一个漂亮的 HTML 报告，可以保存、打印、分享。

**设计思路**：双层结构

```
┌─────────────────────────────────┐
│  AI 回答（干净，无干扰）        │  ← 第一层：主要信息
├─────────────────────────────────┤
│  ▼ 展开查看原始素材            │  ← 第二层：来源追溯
│  [引用1] 原始 chunk 内容...   │
│  [引用2] 原始 chunk 内容...   │
└─────────────────────────────────┘
```

**技术要点**：

- 服务端不依赖任何模板引擎，纯字符串拼接生成 HTML
- 公式用 KaTeX 渲染（把 LaTeX 转换成 HTML）
- 表格用 HTML `<table>` 渲染
- 引用标签可点击跳转

**踩坑记录**：

- **坑5**：KaTeX 渲染中文公式时，某些符号显示不正常。→ 解决：在 HTML 里引入完整的中文字体栈。
- **坑6**：LLM 输出里的 LaTeX 公式有时候不带 `$` 分隔符。→ 解决：后处理正则，自动识别 LaTeX 语法并加 `$` 包裹。

---

### 阶段四：引用粒度优化（表格行拆分）⭐ 核心技术亮点

> 这部分是本项目最有技术含量的设计，也是视频里最值得讲的部分。

**问题背景**：

用户上传了一张齿轮参数表的截图，OCR 识别后整个表格作为一个 chunk 存入向量库。
用户问："模数2.5的齿轮外径是多少？"
LLM 回答："根据资料，模数2.5的齿轮外径是..." 并标注 `[引用1]`。

**问题**：`[引用1]` 指向的是整个表格（20行 × 6列），观众不知道具体是哪一行！
引用粒度太粗，失去了对答案的精准追溯能力。

**解决方案（三套方案对比）**：

| 方案 | 思路 | 优点 | 缺点 | 结论 |
|------|------|------|------|------|
| A. 表格整体引用 | 不拆分，Prompt 里要求 LLM 指出具体行 | 实现简单 | 依赖 LLM 遵守格式，不稳定 | ❌ |
| B. 按行拆分 chunk | 表格 > N 行时，按行拆成多个虚拟 chunk | 引用精确到行，100% 准确 | chunk 数量增多，token 消耗增加 | ✅ 选中 |
| C. 字符级定位 | 在原文里标注起止字符偏移量 | 最精确 | 实现极复杂，OCR 排版还原难 | ❌ |

**最终方案：B（按行拆分）+ Prompt 强化**

实现细节：

```python
def _expand_chunks(chunks, table_split_threshold=4):
    """将大表格按行拆分，提升引用粒度"""
    expanded = []
    for chunk in chunks:
        if chunk["type"] == "table" and chunk["row_count"] > table_split_threshold:
            # 按行拆分成多个虚拟 chunk
            for i, row in enumerate(chunk["rows"]):
                expanded.append({
                    "id": f"{chunk['id']}_row{i}",
                    "content": row,
                    "source": chunk["source"],
                    "is_row": True,
                    "row_index": i,
                })
        else:
            expanded.append(chunk)
    return expanded
```

**Prompt 强化规则**（三条铁律）：

```
1. 【全引用标注】回答中每一个事实陈述都必须标注对应的 [引用N]，不得省略。
2. 【补充标记】如果某句话综合了多个资料，但加了你的推理，必须在句尾加 [补充]。
3. 【禁止编造】如果资料中没有相关信息，明确输出"资料中未提及"，禁止编造。
```

**效果**：

拆分前：`[引用1]` → 整个表格（20行）
拆分后：`[引用1]` → 第3行，`[引用2]` → 第7行，精确到行。

**用户反馈**：这个问题在 B站视频里可以用"before/after"对比来展示，视觉冲击力强。

**踩坑记录**：

- **坑7**：表格拆分后 chunk 数量暴增，超过 LLM 的 context window。→ 解决：增加 `--max-chunks` 参数，限制送入 LLM 的 chunk 数量，按相关度排序取 top-K。
- **坑8**：拆分后引用编号和原始 chunk ID 不一致，HTML 报告里无法正确跳转。→ 解决：建立 `expanded_id → original_chunk_id` 的映射表，`_render_report_html()` 里用映射表做跳转链接。

---

### 阶段五：引用编号连续化（后处理重编号）⭐ 用户体验优化

**问题背景**：

阶段四实现了表格行拆分，但引入了一个新问题：

假设搜索返回 6 个 chunk（其中2个是拆分后的表格行），LLM 实际只用了其中的 第2、4、5 号 chunk。
LLM 输出的回答里标注的是 `[引用2]`、`[引用4]`、`[引用5]` —— 编号不连续，用户会困惑："引用1、3呢？去哪了？"

**解决方案（两套方案对比）**：

| 方案 | 思路 | 优点 | 缺点 | 结论 |
|------|------|------|------|------|
| A. 后处理正则重编号 | 用正则提取 LLM 输出中的 `[引用N]`，映射为连续的 1~M | 不侵入 LLM 生成，稳定可控 | 需要解析 LLM 自由文本，正则可能漏匹配 | ✅ 选中 |
| B. 要求 LLM 自己重编号 | 在 Prompt 里要求"只用到的资料重新编号为 [引用1]~[引用M]" | LLM 理解上下文，更准确 | 依赖 LLM 遵守指令，实测不稳定 | ❌ |

**最终方案：A（后处理正则 + 智能重编号）**

实现细节：

```python
def _renumber_citations(answer, used_chunk_ids):
    """将回答中的引用编号重编号为连续的 1~M"""
    # 建立旧编号 → 新编号的映射
    id_map = {old_id: new_id for new_id, old_id in enumerate(used_chunk_ids, 1)}

    # 正则替换所有 [引用N] 为新的连续编号
    def replace_fn(match):
        old_num = int(match.group(1))
        new_num = id_map.get(old_num, old_num)
        return f"[引用{new_num}]"

    new_answer = re.sub(r'\[引用(\d+)\]', replace_fn, answer)
    return new_answer
```

**效果**：

重编号前：回答里有 `[引用2]`、`[引用4]`、`[引用5]`
重编号后：回答里有 `[引用1]`、`[引用2]`、`[引用3]` —— 连续，干净，专业。

**踩坑记录**：

- **坑9**：LLM 有时候输出 `[引用1][引用2]`（多个引用叠加），正则要支持多引用。→ 解决：正则改为全局替换，每个 `[引用N]` 独立处理。
- **坑10**：有时候 LLM 输出的是 `【引用1】`（中文括号），正则匹配不到。→ 解决：正则同时匹配 `\[引用(\d+)\]` 和 `【引用(\d+)】`。

---

### 阶段六：KaTeX 公式渲染优化

**问题背景**：

技术文档里大量存在数学公式（比如齿轮强度计算公式）。
OCR 可以识别公式为 LaTeX 格式，但 HTML 报告里不能直接显示 LaTeX 源码，需要渲染成公式图片/HTML。

**方案选型**：

| 方案 | 思路 | 优点 | 缺点 |
|------|------|------|------|
| 服务端渲染（KaTeX） | 用 Node.js 的 KaTeX 包，在服务端把 LaTeX 转成 HTML | 客户端无需 JS，离线可用 | 需要安装 Node.js 和 KaTeX |
| 客户端渲染（KaTeX CDN） | HTML 里引入 KaTeX CDN，客户端浏览器渲染 | 无需服务端安装 | 需要联网，离线不可用 |
| 图片渲染（matplotlib） | 把 LaTeX 转成 PNG 图片 | 兼容性最好 | 图片不能复制文本，可访问性差 |

**最终方案**：服务端渲染（KaTeX）+ 客户端渲染（KaTeX CDN）双重保障。

实现细节：

```python
def render_katex(latex_src):
    """用 KaTeX 将 LaTeX 渲染为 HTML"""
    # 调用 Node.js 执行 KaTeX
    result = subprocess.run(
        ["node", "render_math.js", latex_src],
        capture_output=True,
        text=True,
    )
    return result.stdout  # 返回渲染后的 HTML
```

HTML 报告里同时内联 KaTeX CSS，确保离线也能显示。

**踩坑记录**：

- **坑11**：LaTeX 里的 `\frac` 命令，KaTeX 渲染出来和 LaTeX 有细微差别。→ 解决：这是正常的，KaTeX 是 LaTeX 的子集，大部分公式都能正确渲染。
- **坑12**：OCR 识别的 LaTeX 有时候不完整（缺 `}`），导致 KaTeX 渲染失败。→ 解决：加 try-catch，渲染失败时显示原始 LaTeX 源码（至少用户能看到公式）。

---

### 阶段七：数据清洗（去重 + 质量过滤）

**问题背景**：

用户多次摄入同一个文件（或同一张截图的不同版本），知识库里会出现重复 chunk。
搜索时同一个资料出现多次，浪费 token，也影响用户体验。

**去重方案**：

1. **入库时去重**：计算原始文本的 SHA256 哈希，如果已存在则跳过（不让重复 chunk 入库）
2. **搜索结果去重**：同一来源（文件名 + 页码）的 chunk，只保留相关度最高的一个

```python
def deduplicate_by_source(chunks, top_k):
    """同源去重：同一来源只保留相关度最高的 chunk"""
    seen_sources = set()
    result = []
    for chunk in chunks:
        source_key = f"{chunk['source']}_{chunk['page']}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            result.append(chunk)
        if len(result) >= top_k:
            break
    return result
```

**质量过滤**：

OCR 质量不高的图片，识别结果会有大量乱码（`%%`、`@@` 等）。
这类 chunk 入库后，搜索时会出现在结果里，但内容毫无价值。

过滤规则：
- 如果 chunk 里 50% 以上的字符是乱码（非中英日韩字符），直接丢弃
- 如果 chunk 长度 < 20 字符，可能是 OCR 识别失败的碎片，丢弃

**踩坑记录**：

- **坑13**：去重时，不同版本的同一份文档（v1.0.docx 和 v2.0.docx）被认为是不同来源，没有去重。→ 解决：用文档内容的哈希去重，而不是文件名。
- **坑14**：质量过滤把某些含大量特殊符号的公式 chunk 误判为乱码。→ 解决：过滤规则里加入 LaTeX 命令白名单（`\frac`、`\sum` 等），如果 chunk 包含这些命令，不做质量过滤。

---

### 阶段八：上传 GitHub + 文档完善（开源准备）

**目标**：把项目开源到 GitHub，让更多人可以用、可以贡献代码。

**做了什么**：

1. **清除硬编码的 API KEY**：代码里不能包含真实 KEY，改为从环境变量读取
2. **创建 `.gitignore`**：排除 `local_data/`、`qdrant_data/`、`*.log` 等本地数据
3. **编写完整文档**：
   - `README.md`：项目介绍、安装步骤、使用示例
   - `CONTRIBUTING.md`：如何贡献代码
   - `CODE_OF_CONDUCT.md`：社区行为准则
   - `CHANGELOG.md`：版本更新记录
   - `LICENSE`：MIT 开源协议
4. **创建 GitHub Issue/PR 模板**：引导用户提交高质量的 Issue 和 PR
5. **修复 CI 检查失败**：删除了从模板项目继承来的无关 GitHub Actions workflow 文件

**踩坑记录**：

- **坑15**：第一次推送时，把整个 `zylon-ai/private-gpt` 的原始代码也推上去了（因为本地目录是从那个仓库 clone 的）。→ 解决：从临时目录重新推送，只推我们自己写的文件。
- **坑16**：GitHub 的 CI 检查失败（3 failing, 2 cancelled, 1 skipped, 1 successful），原因是仓库里包含了来自模板的 GitHub Actions workflow 文件，这些文件引用了不存在的 `Makefile`、`pyproject.toml` 等。→ 解决：删除所有无关的 workflow 文件，只保留 Issue/PR 模板。

---

## 四、BUG 清单与修复过程（完整记录）

> 这部分适合做"踩坑"类视频，每个 BUG 都讲清楚：现象 → 原因 → 修复方案。

| BUG # | 现象 | 根本原因 | 修复方案 | 视频时间点 |
|--------|------|----------|----------|------------|
| 1 | PaddleOCR 首次运行卡住 | 自动下载模型，网络超时 | 提前手动下载模型文件 | 03:20 |
| 2 | Ollama 没启动时报错不友好 | 没有做服务可用性检查 | `start.bat` 里先启动 Ollama，再加服务健康检查 | 05:40 |
| 3 | LLM 不按格式输出引用标注 | Prompt 不够强 | 三条强化规则 + 后处理正则 | 08:15 |
| 4 | 引用编号跳跃（[引用5] 但只有1个引用） | LLM 只用了部分 chunk，编号未重排 | 后处理正则重编号 | 12:30 |
| 5 | KaTeX 中文公式显示异常 | 字体栈不完整 | HTML 里引入完整中文字体栈 | 16:45 |
| 6 | LLM 输出 LaTeX 不带 `$` 分隔符 | LLM 自由文本输出不稳定 | 后处理正则自动识别 LaTeX 并加 `$` 包裹 | 18:20 |
| 7 | 表格拆分后 chunk 数量暴增，超 context | 没有限制送入 LLM 的 chunk 数 | 增加 `--max-chunks` 参数 | 21:00 |
| 8 | 拆分后引用跳转链接失效 | expanded_id 和 original_id 映射丢失 | 建立映射表，`_render_report_html()` 里用映射表 | 23:30 |
| 9 | 多个引用叠加（`[引用1][引用2]`）正则匹配不完整 | 正则只匹配单个引用 | 改为全局替换，每个引用独立处理 | 26:10 |
| 10 | LLM 输出中文括号（`【引用1】`），正则匹配不到 | 正则只匹配英文括号 | 同时匹配英文和中文括号 | 27:40 |
| 11 | OCR 识别的 LaTeX 不完整，KaTeX 渲染失败 | LaTeX 语法错误 | try-catch，渲染失败时显示原始 LaTeX | 30:00 |
| 12 | 同一文档不同版本未去重 | 去重用文件名，未用内容哈希 | 改为内容 SHA256 去重 | 32:15 |
| 13 | 含特殊符号的公式 chunk 被误判为乱码 | 质量过滤规则太简单 | 加入 LaTeX 命令白名单 | 34:50 |
| 14 | `answer()` 函数返回原始 chunks 而非 expanded_chunks | 函数返回值用错了变量 | 修复返回值为 `expanded_chunks` | 37:20 |
| 15 | API KEY 硬编码在代码里 | 开发时为了方便，忘记清除 | 清除硬编码，改为环境变量 + 强制检查 | 39:00 |
| 16 | 推送了 `zylon-ai/private-gpt` 的原始代码 | 本地目录是从那个仓库 clone 的 | 从临时目录重新推送，只推自己的文件 | 41:30 |

---

## 五、MVP 功能清单（当前版本 v0.1.0）

- [x] 图片 OCR 摄入（PaddleOCR / PPStructureV3）
- [x] 文本文件向量化摄入
- [x] Qdrant 向量搜索
- [x] LLM 合成回答 + 引用标注
- [x] HTML 报告生成（双层结构）
- [x] 表格行拆分（引用粒度优化）
- [x] 引用编号连续化（后处理重编号）
- [x] KaTeX 公式渲染
- [x] 入库 SHA256 去重
- [x] 搜索结果同源去重
- [x] OCR 质量过滤
- [x] 环境变量配置（API KEY 等敏感信息不入库）
- [x] 完整文档（README、CONTRIBUTING、CODE_OF_CONDUCT、CHANGELOG）
- [x] GitHub 开源（MIT 协议）

---

## 六、未来规划（路线图）

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

## 七、技术总结与思考

### 架构原则（为什么这样设计？）

1. **非必要不用大模型**：OCR、向量搜索、引用重编号，都由固定程序完成。只有"搜索结果 → 回答合成"这一步调用 LLM API。→ 省钱，可控，可调试。
2. **HTML 报告 100% 程序生成**：不依赖 LLM 生成 HTML（LLM 生成 HTML 容易出 bug，而且不可控）。→ 稳定，格式统一。
3. **本地优先，数据不出门**：向量库在本地，嵌入模型在本地运行。只有 LLM 合成这一步需要联网（可以切换为本地 LLM）。→ 隐私安全。

### 给独立开发者的建议

1. **先做 MVP，再优化**：第一版不要追求完美，先把核心流程跑通。
2. **Prompt 是有代码的**：把 Prompt 当作代码来管理（版本化、测试、迭代）。
3. **后处理比 Prompt 更可靠**：不要让 LLM 做格式化输出（比如 JSON、编号），用后处理正则来做，稳定得多。
4. **开源是最好的文档**：把项目开源到 GitHub，逼自己把文档写清楚。

---

## 八、附录：完整命令行参数说明

```bash
# 摄入文本文件
python kb_query.py --ingest "文件路径"

# OCR 图片
python kb_query.py --ocr "图片路径" --source "来源名称"

# OCR 后先审核再入库
python kb_query.py --ocr "图片路径" --check-only

# 搜索（不调用 LLM）
python kb_query.py "查询词" --top 10

# 端到端问答（搜索 → LLM 合成 → HTML报告）
python kb_query.py "查询词" --answer --llm-api-key sk-xxx

# 表格行数 > 3 时按行拆分（默认4）
python kb_query.py "查询词" --answer --table-split-threshold 3

# 搜索相关度阈值（默认 0.3）
python kb_query.py "查询词" --threshold 0.5
```

---

## 九、附录：环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `KB_LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `KB_LLM_API_KEY` | LLM API Key | （必须自行设置） |
| `KB_LLM_MODEL` | LLM 模型名 | `deepseek-chat` |

---

**文档结束**

> 如果你觉得这个项目有意思，欢迎到 GitHub 给一个 ⭐
> https://github.com/shiyao222333-afk/kb-query-engine
