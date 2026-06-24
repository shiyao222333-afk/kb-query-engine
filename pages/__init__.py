"""
Citrinitas · 熔知 — 页面模块包

此包包含所有页面函数，从 main.py 拆分出来以降低主文件复杂度。

页面模块:
  - ingest.py: 文档注入页面 (/)
  - search.py: 智能检索页面 (/search)
  - hub.py: 知识中枢页面 (/hub)
  - config.py: 引擎配置页面 (/config)
"""

# 页面模块延迟导入（避免循环导入）
def get_page_ingest():
    from .ingest import page_ingest
    return page_ingest

def get_page_search():
    from .search import page_search
    return page_search

def get_page_hub():
    from .hub import page_hub
    return page_hub

def get_page_config():
    from .config import page_config
    return page_config
