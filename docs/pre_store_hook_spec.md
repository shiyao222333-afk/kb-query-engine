# 预存储钩子接口规格

> 版本: 1.0 | 日期: 2026-06-21
> 面向: 外部程序开发者（Nigredo、Alembic 等）

---

## 概述

Citrinitas（熔知）的摄入管线在「嵌入完成」和「写入 Qdrant」之间留了一个**空工位**（叫预存储钩子）。外部程序可以在这个位置插入自己的逻辑，在知识入库前做最后的加工。

流水线结构：

```
读取 → 去重 → 图片 → 切块 → 嵌入 → [预存储钩子] → 构建Payload → 写入Qdrant → 日志
                                       ↑
                                  Nigredo 等外部程序介入
```

---

## 钩子函数规格

### 签名

```python
def my_hook(state: dict) -> dict:
    """返回值必须和输入格式一样"""
    # 修改 state...
    return state
```

### 输入（state 字典）

| 字段 | 类型 | 含义 | 谁填的 |
|------|------|------|--------|
| `file_path` | str | 源文件路径（可为空） | 管线输入 |
| `text` | str | 全文内容 | `_step_read_content` |
| `collection` | str | 目标知识库名称 | 管线输入 |
| `metadata` | dict | 用户提供的元数据 | 管线输入 |
| `model` | str | 嵌入模型名 | 管线输入 |
| `source` | str | 来源标识（文件名或"直接输入"） | `_step_read_content` |
| `content_hash` | str | 全文哈希（去重用） | `_step_dedup` |
| `chunks` | list[str] | 切好的文本块 | `_step_chunk` |
| `vectors` | list[list[float]] | 嵌入向量（和 chunks 一一对应） | `_step_embed` |
| `valid_images` | list[str] | 有效图片路径 | `_step_extract_images` |

### 输出

返回修改后的 state 字典，格式和输入完全一样。

钩子可以做：
- **不改不动** — 原样返回，什么都不做
- **补充 metadata** — 加上外部程序的专属信息
- **修改 text** — 替换文本内容（比如把原始字幕换成结构化笔记）
- **修改 source** — 改变来源标记

⚠️ 注意：如果修改了 `text`，也需要同步更新 `chunks` 和 `vectors`（设为空列表），让后续步骤重新处理。或者不修改 text，只补充 metadata，这样最安全。

### 错误处理

钩子内部的异常会被捕获，打印警告后继续管线。不会因为钩子失败而中断入库。

---

## 外部程序如何接入

### 第一步：写钩子函数

```python
# 在 Nigredo 中创建 core/citrinitas_hook.py

def nigredo_pre_store(state: dict) -> dict:
    """Nigredo 预存储钩子"""

    # 补充视频专属元数据
    state["metadata"]["source_project"] = "nigredo"
    state["metadata"]["video_title"] = state.get("metadata", {}).get("video_title", "")
    state["metadata"]["video_url"] = state.get("metadata", {}).get("video_url", "")

    # 可选：把原始字幕替换成 LLM 生成的结构化笔记
    if state["metadata"].get("use_structured_notes") and state["metadata"].get("structured_notes"):
        state["text"] = state["metadata"]["structured_notes"]
        state["chunks"] = []
        state["vectors"] = []

    return state
```

### 第二步：注册钩子

```python
# 在 Nigredo 启动时调用
from citrinitas.config.hooks import register_hook
from nigredo.core.citrinitas_hook import nigredo_pre_store

register_hook(nigredo_pre_store)
```

### 第三步：通过 ingest() 入库

```python
from citrinitas.kb_query import ingest

result = ingest(
    text=structured_notes,
    metadata={
        "source_project": "nigredo",
        "video_title": "齿轮设计入门",
        "video_author": "某UP主",
        "video_url": "https://www.bilibili.com/video/...",
    },
    source="nigredo",
)
```

注册钩子后，每次调用 `ingest()` 时钩子都会自动执行。

---

## 和旧方式（kb_bridge.py）的区别

| | 旧方式（直写 Qdrant） | 新方式（走 ingest 管线） |
|---|---|---|
| 去重 | ❌ 没有 | ✅ 自动检查 |
| 四维分面分类 | ❌ 缺失 | ✅ 自动分类 |
| 字段规范化 | ❌ 绕过 | ✅ 枚举守卫 |
| 置信度打分 | ❌ 没有 | ✅ 自动计算 |
| 语言检测 | ❌ 没有 | ✅ 自动 |
| 摄入日志 | ❌ 没有 | ✅ 自动记录 |
| 可搜索 | ⚠️ 基础 | ✅ 完整字段索引 |

---

## 参考文件

| 文件 | 内容 |
|------|------|
| `config/hooks.py` | 钩子注册表（`register_hook()` / `get_hooks()`） |
| `kb_query.py` 中的 `_step_pre_store_hooks()` | 钩子被调用的位置（管线第 7 步） |
| `kb_query.py` 中的 `ingest()` | 主入口函数 |
| `kb_query.py` 中的 `ingest_batch()` | 批量摄入（支持一次多个文件） |
