"""
Citrinitas · 熔知 — 全局共享状态

此模块存放全局状态字典，避免循环导入。
main.py 和 pages/*.py 都从此模块导入 STATE。
"""

from collections import defaultdict

# 全局状态（替代 st.session_state）
STATE = {
    "active_collection": "athanor_v1",
    "collections": [],
    "qdrant_online": False,
    "stats": {},
    "embed_models": [],
    "llm_models": [],
    "ingest_content": "",
    "ingest_source": "",
    "ingest_method": "",
    "ingest_stage": "input",
    "classify_result": None,
    "auto_metadata": None,
    "file_info": None,
    "last_answer": None,
    "last_search": None,
    "current_project": "通用",
    "source_path": "",
}

# 面板值缓存（供摄入页面和 panel_funcs 使用）
PANEL_VALUES = {}
