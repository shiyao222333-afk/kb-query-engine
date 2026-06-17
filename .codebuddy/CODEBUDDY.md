# Athanor · 熔知 — 项目规范

## 环境速查
| 项目 | 值 |
|------|-----|
| Python | `C:\Python314\python.exe` |
| 端口 | `8080` |
| Qdrant | `http://127.0.0.1:6333`（IPv4） |
| 环境变量 | `.env` 文件 |
| 服务目录 | `local_data/reports/` |

## 启动
```bash
cd /d/knowledge-forge
/c/Python314/python.exe main.py
```
或双击 `run.bat`

## 管理文件
| 文件 | 用途 |
|------|------|
| `CHANGELOG.md` | 版本变更记录 |
| `PROJECT_PLAN.md` | 功能路线图 |
| `ISSUES.md` | Bug 跟踪 |
| `kb_query.py` | 核心引擎（`__version__` 在此） |

## 架构原则
1. kb_query.py 与 UI 完全解耦
2. 所有函数返回 dict
3. 配置用环境变量 KB_* 前缀
4. 本地优先（Qdrant + 嵌入本地，仅 LLM 联网）

## 常见陷阱
- `kb_query.py` 模块级变量在 `import` 时求值，`.env` 之后才加载
- QDRANT_URL 必须用 `127.0.0.1` 不能用 `localhost`（IPv6 问题）
- NiceGUI `ui.run()` 的 `reconnect_timeout` 必须 ≥ 60s
