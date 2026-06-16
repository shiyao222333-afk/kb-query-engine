"""
Athanor · 熔知 / MindForge — Streamlit Web UI 主入口
Phase 3: pages/ 多文件架构 + st.navigation

页面:
  文档注入 — 上传/OCR/手动输入/预览/LLM优化/编辑/写入
  智能检索 — 搜索+问答合并，勾选是否用LLM，跨库搜索
  知识中枢 — 集合仪表盘/建库向导/操作/重建迁移/导出
  引擎配置 — LLM配置/嵌入模型管理/OCR设置/系统设置
"""

import os
import sys
import shutil

# ── 启动时清理过期字节码缓存 + 模块缓存 ──
_project_root = os.path.dirname(os.path.abspath(__file__))

# 1. 清除 __pycache__ 目录
_pycache_dirs = []
for root, dirs, _files in os.walk(_project_root):
    if "__pycache__" in dirs:
        _pycache_dirs.append(os.path.join(root, "__pycache__"))
        dirs.remove("__pycache__")
for d in _pycache_dirs:
    shutil.rmtree(d, ignore_errors=True)

# 2. 清除 sys.modules 中本项目的旧缓存（解决 Streamlit 热重载残留）
_project_modules = [k for k in list(sys.modules) if k.startswith(("config", "utils", "pages", "kb_query"))]
for k in _project_modules:
    del sys.modules[k]

del _project_root, _pycache_dirs, _project_modules

import streamlit as st
import threading
import time

# ── 自动退出监控：浏览器关闭 → 进程自动退出 ──
def _auto_shutdown_monitor():
    """后台线程：当所有浏览器标签页关闭时，自动退出 Streamlit 进程。"""
    CHECK_INTERVAL = 3       # 每 3 秒检查一次
    IDLE_COUNT_MAX = 3       # 连续 3 次无连接（约 9 秒）→ 退出
    STARTUP_TIMEOUT = 180    # 最多等 3 分钟让 Runtime 启动

    # 等待 Runtime 创建
    runtime = None
    waited = 0
    while runtime is None and waited < STARTUP_TIMEOUT:
        try:
            from streamlit.runtime.runtime import Runtime, RuntimeState
            runtime = Runtime.instance()
        except RuntimeError:
            time.sleep(3)
            waited += 3
    if runtime is None:
        return  # 无法获取 Runtime，放弃监控

    # 等待第一次浏览器连接（用户可能还没打开页面）
    for _ in range(40):
        try:
            if runtime.state != RuntimeState.NO_SESSIONS_CONNECTED:
                break
        except Exception:
            pass
        time.sleep(3)

    # 主监控循环
    idle_count = 0
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            if runtime.state == RuntimeState.NO_SESSIONS_CONNECTED:
                idle_count += 1
                if idle_count >= IDLE_COUNT_MAX:
                    print("\n[Athanor] 浏览器已关闭，自动退出。")
                    os._exit(0)
            else:
                idle_count = 0  # 有连接，重置计数器
        except Exception:
            pass

_shutdown_thread = threading.Thread(target=_auto_shutdown_monitor, daemon=True)
_shutdown_thread.start()

# ── 确保 kb_query 可导入 ──
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# ── .env 持久化 ──
ENV_FILE = os.path.join(PROJECT_DIR, ".env")

def _load_env():
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                os.environ[key] = value

_load_env()

import kb_query

if os.environ.get("KB_EMBED_MODEL"):
    kb_query.EMBED_MODEL = os.environ["KB_EMBED_MODEL"]

# ── 页面配置 ──
st.set_page_config(
    page_title="Athanor · 熔知",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State 初始化 ──
if "active_collection" not in st.session_state:
    st.session_state.active_collection = kb_query.DEFAULT_COLLECTION
if "kb_root_path" not in st.session_state:
    st.session_state.kb_root_path = os.environ.get("KB_ROOT_PATH") or os.path.join(
        PROJECT_DIR, "local_data"
    )
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "last_search" not in st.session_state:
    st.session_state.last_search = None
if "fetched_llm_models" not in st.session_state:
    st.session_state.fetched_llm_models = []

# ── CSS 加载 ──
@st.cache_resource(show_spinner=False)
def _load_css() -> str:
    css_path = os.path.join(PROJECT_DIR, "assets", "style.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f"<style>\n{f.read()}\n</style>"
    except FileNotFoundError:
        return ""

st.markdown(_load_css(), unsafe_allow_html=True)

# ── 页面注册 ──
pages = [
    st.Page("pages/1_文档注入.py", title="文档注入", icon="📥"),
    st.Page("pages/2_智能检索.py", title="智能检索", icon="💬"),
    st.Page("pages/3_知识中枢.py", title="知识中枢", icon="🗂️"),
    st.Page("pages/4_引擎配置.py", title="引擎配置", icon="⚙️"),
]

pg = st.navigation(pages)
pg.run()
