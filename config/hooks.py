"""
预存储钩子注册表 — Pre-Store Hook Registry

外部程序（如 Nigredo / Alembic）可通过 register_hook() 注册钩子函数，
在 Citrinitas 摄入管线的「嵌入完成→写入 Qdrant」阶段介入。

钩子函数签名:
    hook(state: dict) -> state: dict

state 包含:
    file_path, text, collection, metadata, model,
    source, content_hash, chunks, vectors, valid_images,
    doc_id, ingested_at, points

钩子可以修改 state 中的任意字段后返回。管线会使用修改后的 state 继续执行。

用法:
    from config.hooks import register_hook

    def my_hook(state):
        state["metadata"]["source_project"] = "nigredo"
        return state

    register_hook(my_hook)
"""

_hooks: list = []


def register_hook(hook):
    """注册一个预存储钩子函数"""
    if hook not in _hooks:
        _hooks.append(hook)


def get_hooks() -> list:
    """返回当前注册的所有钩子（副本，防止外部修改内部列表）"""
    return list(_hooks)
