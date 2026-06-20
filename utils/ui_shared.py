"""
Citrinitas · 熔知 — 共享 UI 函数

此模块存放页面间共享的 UI 函数，避免循环导入。
main.py 和 pages/*.py 都从此模块导入共享函数。
"""

from nicegui import ui

def render_chunk_card(c: dict, idx: int):
    """渲染搜索结果卡片（U4 修复 - 显示新字段）"""
    with ui.card().classes("w-full"):
        title = c.get("title") or c.get("source", "未知")
        ui.markdown(f"**{idx}.** {title}")
        
        # 显示新字段（U4 修复）
        with ui.row().classes("items-center gap-2 wrap"):
            if c.get("needs_review"):
                ui.badge("⚠️ 待审核", color="orange").classes("text-xs")
            ui.label(f"📄 {c.get('content_type', 'N/A')}").classes("text-xs text-gray-400")
            ui.label(f"🏷️ {', '.join(c.get('domain', []))}").classes("text-xs text-gray-400")
            ui.label(f"✅ {c.get('epistemic_status', 'N/A')}").classes("text-xs text-gray-400")
            ui.label(f"⏱️ {c.get('temporal_nature', 'N/A')}").classes("text-xs text-gray-500")
        
        ui.markdown(f"```\n{c.get('text', '')[:300]}\n```")
        ui.label(f"分数: {c.get('score', 0):.2f}").classes("text-xs text-gray-500")
