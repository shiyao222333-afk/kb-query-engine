"""
Citrinitas · 熔知 — NiceGUI 主入口
v0.4.4 → NiceGUI migration (分面 v5.0)

纯 Python SPA 架构：页面切换不重跑脚本，WebSocket 实时通信
底层：FastAPI + Vue + Quasar + WebSocket

页面:
  /            → 文档注入（默认首页）
  /search      → 智能检索
  /hub         → 知识中枢
  /config      → 引擎配置
"""

import os
import sys
import threading
import time
import asyncio
import json
from datetime import datetime, timezone
import html as html_mod
from collections import defaultdict
from fastapi.responses import FileResponse

# ── 路径设置 ──
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

import kb_query
from config import classifications
from field_cfg import FIELD_DISPLAY_CFG, SOURCE_ICON, PANEL_VALUES
from panel_funcs import build_result_panel, build_advanced_panel, edit_field_dialog
from utils.file_handler import (
    detect_file_type, extract_text, extract_auto_metadata, detect_encoding,
    SIZE_LIMIT_MB, FORMAT_DISPLAY_NAMES,
)

from nicegui import ui, app

# ── 启用 .env ──
ENV_FILE = os.path.join(PROJECT_DIR, ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

from utils.ui_shared import render_chunk_card
from utils.state import STATE

# ═══════════════════════════════════════════
# 页面路由注册（从 pages/*.py 导入，触发 @ui.page() 装饰器）
# ═══════════════════════════════════════════
from pages.ingest import page_ingest
from pages.search import page_search
from pages.hub import page_hub
from pages.config import page_config
from pages.manage import page_manage

if os.environ.get("KB_EMBED_MODEL"):
    kb_query.EMBED_MODEL = os.environ["KB_EMBED_MODEL"]

# ═══════════════════════════════════════════
# 全局状态（替代 st.session_state）
# ═══════════════════════════════════════════

def refresh_system_state():
    """刷新全局状态：Qdrant 连接、集合列表、统计信息（所有请求带 timeout）。"""
    import requests
    try:
        col_data = kb_query.list_collections()
        STATE["collections"] = [c["name"] for c in col_data.get("collections", [])] if col_data.get("ok") else []
        STATE["qdrant_online"] = col_data.get("ok", False)

        if STATE["active_collection"] not in STATE["collections"] and STATE["collections"]:
            STATE["active_collection"] = STATE["collections"][0]

        if STATE["qdrant_online"]:
            try:
                resp = requests.get(
                    f"{kb_query.QDRANT_URL}/collections/{STATE['active_collection']}",
                    timeout=3,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    cfg = data.get("result", {}).get("config", {}).get("params", {}).get("vectors", {})
                    pts = data.get("result", {}).get("points_count", 0)
                    STATE["stats"] = {"points": pts, "dim": cfg.get("size", "?"), "collection": STATE["active_collection"]}
            except Exception:
                STATE["stats"] = {}
        else:
            STATE["stats"] = {}
    except Exception:
        STATE["collections"] = []
        STATE["qdrant_online"] = False
        STATE["stats"] = {}

    try:
        STATE["embed_models"] = kb_query.get_embed_models()
    except Exception:
        STATE["embed_models"] = []

# ── 启动时刷新状态（异步，不阻塞启动）──
import requests as _requests
_qdrant_alive = False
_r = None
try:
    print(f"[启动] 检查 Qdrant: {kb_query.QDRANT_URL}/collections", flush=True)
    _r = _requests.get(f"{kb_query.QDRANT_URL}/collections", timeout=3)
    _qdrant_alive = _r.status_code == 200
    print(f"[启动] Qdrant 状态: {_r.status_code} -> {_qdrant_alive}", flush=True)
except Exception as _e:
    print(f"[启动] Qdrant 离线: {_e}", flush=True)

if _qdrant_alive:
    refresh_system_state()
else:
    STATE["qdrant_online"] = False

del _r, _qdrant_alive
# _requests 保留（后续路由可能用到）

# 嵌入模型预设
EMBED_PRESETS = {
    "qwen3-embedding": "qwen3-embedding:4b",
    "bge-m3": "bge-m3:latest",
    "nomic-embed-text": "nomic-embed-text:latest",
    "mxbai-embed-large": "mxbai-embed-large:latest",
}

# ═══════════════════════════════════════════
# 共享 UI 函数
# ═══════════════════════════════════════════

_STATUS_WIDGETS = {}   # 状态栏控件引用（供 app.timer 回调更新）
_GLOBAL_TIMER = None   # app.timer 只创建一次

def _status_tick():
    """全局状态刷新回调（由 app.timer 每10秒触发，独立于任何UI元素）。"""
    w = _STATUS_WIDGETS
    if not w:
        return
    try:
        refresh_system_state()
        badge = w.get("badge")
        if badge is None:
            return
        if STATE["qdrant_online"]:
            badge.set_text("在线")
            badge.props("color=green")
            stats = STATE.get("stats", {})
            pts = w.get("points")
            if pts:
                pts.set_text(f"文档块: {stats.get('points', '--')}")
            dm = w.get("dim")
            if dm:
                dm.set_text(f"维度: {stats.get('dim', '--')}")
        else:
            badge.set_text("离线")
            badge.props("color=red")
    except Exception:
        pass  # 控件临时不可用（抽屉重建中），静默跳过

def build_left_drawer():
    """构建左侧导航抽屉（所有页面共用）。"""
    global _GLOBAL_TIMER
    with ui.left_drawer(value=True, fixed=False, bordered=True).classes("bg-gray-900 text-white") as drawer:
        with ui.column().classes("w-full items-center p-4"):
            ui.markdown("## 🏭 Citrinitas")
            ui.markdown("##### 熔知 · Citrinitas")
            ui.label("个人本地知识引擎").classes("text-sm text-gray-400")
            ui.separator()

        # 知识库选择器
        with ui.column().classes("w-full px-4"):
            ui.markdown("### 📚 当前知识库")
            collection_select = ui.select(
                options=STATE["collections"] if STATE["collections"] else [kb_query.DEFAULT_COLLECTION],
                value=STATE["active_collection"],
                on_change=lambda e: set_active_collection(e.value),
            ).classes("w-full").props('dense outlined dark')

        ui.separator()

        # 系统状态
        with ui.column().classes("w-full px-4"):
            ui.markdown("### 📊 系统状态")
            _initial = "在线" if STATE["qdrant_online"] else "离线"
            _color   = "green" if STATE["qdrant_online"] else "red"
            status_badge = ui.badge(_initial, color=_color)
            points_label = ui.label("文档块: --").classes("text-sm")
            dim_label = ui.label("维度: --").classes("text-sm")

            def _update_status():
                refresh_system_state()
                if STATE["qdrant_online"]:
                    status_badge.set_text("在线")
                    status_badge.props("color=green")
                    stats = STATE.get("stats", {})
                    points_label.set_text(f"文档块: {stats.get('points', '--')}")
                    dim_label.set_text(f"维度: {stats.get('dim', '--')}")
                else:
                    status_badge.set_text("离线")
                    status_badge.props("color=red")

            ui.button("🔄 刷新", on_click=_update_status).props("flat dense").classes("text-xs")

            # 全局定时器（app.timer 独立于UI，只创建一次）
            global _STATUS_WIDGETS, _GLOBAL_TIMER
            _STATUS_WIDGETS.update(badge=status_badge, points=points_label, dim=dim_label)
            if _GLOBAL_TIMER is None:
                _GLOBAL_TIMER = app.timer(10.0, _status_tick)

        ui.separator()

        # 导航链接
        with ui.column().classes("w-full px-2 gap-1"):
            ui.link("📥 文档注入", "/").classes(
                "w-full text-left p-2 rounded hover:bg-blue-700 transition no-underline text-white"
            )
            ui.link("💬 智能检索", "/search").classes(
                "w-full text-left p-2 rounded hover:bg-blue-700 transition no-underline text-white"
            )
            ui.link("📄 文档管理", "/manage").classes(
                "w-full text-left p-2 rounded hover:bg-blue-700 transition no-underline text-white"
            )
            ui.link("🗂️ 知识中枢", "/hub").classes(
                "w-full text-left p-2 rounded hover:bg-blue-700 transition no-underline text-white"
            )
            ui.link("⚙️ 引擎配置", "/config").classes(
                "w-full text-left p-2 rounded hover:bg-blue-700 transition no-underline text-white"
            )

        ui.separator()
        with ui.column().classes("w-full px-4"):
            ui.link("🔗 GitHub", "https://github.com/shiyao222333-afk/citrinitas").classes("text-xs text-blue-300")
            ui.button("⏻ 关机", on_click=lambda: os._exit(0)).props("flat dense color=red").classes("text-xs mt-2")

        return drawer

def set_active_collection(name: str):
    STATE["active_collection"] = name

def _sys_status_section() -> tuple:
    """返回系统状态 UI 元素供页面复用。"""
    return STATE["qdrant_online"], STATE.get("stats", {})

# ═══════════════════════════════════════════
# 页面 1：文档注入（首页）
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 页面 2：智能检索
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 页面 3：知识中枢
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 页面 4：引擎配置
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _save_env(kv: dict):
    """增量写入 .env 文件。"""
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    for key, val in kv.items():
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and stripped.split("=", 1)[0].strip() == key:
                lines[i] = f"{key}={val}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={val}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

# ═══════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════

def _auto_shutdown():
    """后台线程：当所有浏览器标签页关闭时自动退出。"""
    CHECK = 3
    IDLE_MAX = 3
    time.sleep(10)  # 等 NiceGUI 启动
    idle = 0
    while True:
        time.sleep(CHECK)
        try:
            # NiceGUI app.storage 和 WebSocket 连接检测
            import requests
            requests.get("http://localhost:8080", timeout=2)
            idle = 0
        except Exception:
            idle += 1
            if idle >= IDLE_MAX:
                print("\n[Citrinitas] 浏览器已关闭，自动退出。")
                os._exit(0)

@app.on_startup
def startup():
    refresh_system_state()
    threading.Thread(target=_auto_shutdown, daemon=True).start()

@app.get("/reports/{filename}")
def _serve_report(filename: str):
    """Serve report HTML/PDF files from local_data/reports/."""
    file_path = os.path.join(PROJECT_DIR, "local_data", "reports", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    from fastapi.responses import JSONResponse
    return JSONResponse({"error": "File not found"}, status_code=404)

# ═══════════════════════════════════════
# 页面 4：文档管理
# ═══════════════════════════════════════

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Citrinitas · 熔知",
        host="127.0.0.1",
        port=8080,
        reload=False,
        show=False,
        storage_secret="citrinitas-mindforge-secret",
        reconnect_timeout=120,  # 给 LLM/嵌入模型 充足加载时间
    )
