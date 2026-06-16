"""
🗂️ 知识中枢 — 集合仪表盘 / 建库向导 / 操作 / 重建迁移 / 导出
"""

import streamlit as st
import os
import sys
import re
import json
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
import kb_query
from utils.ui_utils import (
    render_sidebar, cached_stats, cached_collections, cached_ingest_log,
    cached_embed_models, save_env, clear_kb_caches,
)
from utils.flame_bg import render_flame_banner

# ── 侧边栏 ──
with st.sidebar:
    render_sidebar()

# ── 标题 ──
st.title("🗂️ 知识中枢")
render_flame_banner()
st.markdown("知识库集合的指挥中心 — 创建、管理、切换、重建。")

# ── 获取数据 ──
col_data = cached_collections()
qdrant_ok = col_data.get("ok", False)
collections = col_data.get("collections", []) if qdrant_ok else []
current_col = st.session_state.get("active_collection", kb_query.DEFAULT_COLLECTION)

# ── Dialogs（定义在顶层）──

@st.dialog("清空知识库")
def dialog_clear():
    col = st.session_state.get("dialog_target", "")
    st.error(f"⚠️ 确定要清空知识库「**{col}**」吗？")
    st.caption("所有文档块的向量数据将被删除，集合结构保留。此操作不可撤销。")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 确认清空", type="primary", use_container_width=True, key="confirm_clear"):
            result = kb_query.clear_collection(col)
            if result.get("ok"):
                st.success(f"✅ 已清空 {result.get('deleted', 0)} 条记录")
                clear_kb_caches()
            else:
                st.error(f"清空失败: {result.get('error')}")
            st.session_state.show_clear_dialog = False
            st.rerun()
    with c2:
        if st.button("❌ 取消", use_container_width=True, key="cancel_clear"):
            st.session_state.show_clear_dialog = False
            st.rerun()

@st.dialog("删除知识库")
def dialog_delete():
    col = st.session_state.get("dialog_target", "")
    st.error(f"⚠️ 确定要删除知识库「**{col}**」吗？")
    st.caption("集合结构和所有数据将被完全移除。此操作不可撤销。")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 确认删除", type="primary", use_container_width=True, key="confirm_delete"):
            result = kb_query.delete_collection(col)
            if result.get("ok"):
                st.success(f"✅ 已删除集合: {col}")
                if col == st.session_state.get("active_collection", ""):
                    new_cols = [c["name"] for c in cached_collections().get("collections", []) if c["name"] != col]
                    st.session_state.active_collection = new_cols[0] if new_cols else kb_query.DEFAULT_COLLECTION
                clear_kb_caches()
            else:
                st.error(f"删除失败: {result.get('error')}")
            st.session_state.show_delete_dialog = False
            st.rerun()
    with c2:
        if st.button("❌ 取消", use_container_width=True, key="cancel_delete"):
            st.session_state.show_delete_dialog = False
            st.rerun()

# ── 渲染 Dialog（在页面顶层调用）──
if st.session_state.get("show_clear_dialog"):
    dialog_clear()
if st.session_state.get("show_delete_dialog"):
    dialog_delete()

# ═══════════════════════════════════════════
# 首次建库向导
# ═══════════════════════════════════════════
if qdrant_ok and not collections:
    st.info("🔧 **首次使用？** 检测到没有任何知识库集合，请先创建一个。", icon="🚀")

    with st.form("wizard_form"):
        st.markdown("---")
        st.markdown("### 🏗️ 创建你的第一个知识库")
        st.markdown("#### 选择嵌入模型")

        st.info("📊 分类方式：**分面分类法**（单集合 `athanor_v1` + 多维度 Payload 过滤）")

        embed_models = cached_embed_models()
        if embed_models:
            embed_model = st.selectbox(
                "选择向量化模型",
                options=embed_models,
                index=0,
                help="后续可在「引擎配置」里更换。",
            )
        else:
            embed_model = st.text_input(
                "嵌入模型名称",
                value=kb_query.EMBED_MODEL,
                help="手动输入（Ollama 离线时）",
            )

        st.markdown("---")
        st.caption("将创建集合：athanor_v1（2560维，Cosine 距离）")

        submitted = st.form_submit_button("🚀 创建知识库", type="primary", use_container_width=True)

    if submitted:
        if not kb_query._check_qdrant():
            st.error("⚠️ Qdrant 未运行，无法创建。")
        else:
            if kb_query._ensure_collection("athanor_v1"):
                save_env({"KB_CLASSIFICATION": "faceted"})
                os.environ["KB_CLASSIFICATION"] = "faceted"
                if embed_model:
                    save_env({"KB_EMBED_MODEL": embed_model})
                    os.environ["KB_EMBED_MODEL"] = embed_model
                    kb_query.EMBED_MODEL = embed_model
                st.session_state.active_collection = "athanor_v1"
                clear_kb_caches()
                st.success("✅ 已创建知识库！请开始摄入文档。")
                st.rerun()
            else:
                st.error("Qdrant 未运行")

    st.stop()

# ── 检查 Qdrant ──
if not qdrant_ok:
    st.error(f"⚠️ Qdrant 未运行: {col_data.get('error', '未知错误')}")
    st.stop()

# ═══════════════════════════════════════════
# 层 1: 集合仪表盘
# ═══════════════════════════════════════════
st.markdown("---")
st.markdown("### 📊 集合仪表盘")

total_pts = sum(c["points"] for c in collections)
current_embed = os.environ.get("KB_EMBED_MODEL", kb_query.EMBED_MODEL)

# 统计卡片
c1, c2, c3, c4 = st.columns(4)
c1.metric("集合总数", len(collections))
c2.metric("文档块总数", total_pts)
c3.metric("嵌入模型", current_embed[:20])
c4.metric("分类法", "分面分类")

# 搜索过滤
st.markdown("---")
fc1, fc2 = st.columns([3, 1])
with fc1:
    search_filter = st.text_input("🔍 搜索集合", placeholder="输入名称过滤...", label_visibility="collapsed")
with fc2:
    status_filter = st.selectbox("状态筛选", ["全部", "有数据", "空库"], label_visibility="collapsed")

filtered = collections
if search_filter:
    filtered = [c for c in filtered if search_filter.lower() in c["name"].lower()]
if status_filter == "有数据":
    filtered = [c for c in filtered if c["points"] > 0]
elif status_filter == "空库":
    filtered = [c for c in filtered if c["points"] == 0]

if not filtered:
    st.info("📭 没有匹配的集合。")
else:
    cards_per_row = 3
    for i in range(0, len(filtered), cards_per_row):
        row_cards = filtered[i:i+cards_per_row]
        cols = st.columns(cards_per_row)
        for idx, c in enumerate(row_cards):
            with cols[idx]:
                name = c["name"]
                pts = c["points"]
                dim = c["dim"]
                is_active = name == current_col

                status_icon = "🟢" if pts > 0 else "🔴"
                border = "2px solid #FF6B35" if is_active else "1px solid #333"

                st.markdown(f"""
                <div style="
                    background: rgba(26, 26, 46, 0.8);
                    border: {border};
                    border-radius: 10px;
                    padding: 16px;
                    margin-bottom: 8px;
                ">
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                        <span style="font-size:16px;">{status_icon}</span>
                        <span style="font-weight:500;color:#F7C948;font-size:14px;">{name}</span>
                        {'<span style="background:rgba(255,107,53,0.2);color:#FF6B35;font-size:10px;padding:2px 6px;border-radius:4px;">当前</span>' if is_active else ''}
                    </div>
                    <div style="color:#888;font-size:12px;line-height:1.6;">
                        {pts} 条记录 · 维度 {dim}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 操作按钮（每张卡片下方）
                bc = st.columns(3)
                with bc[0]:
                    if not is_active:
                        st.button("🔄 切换", key=f"sw_{name}", use_container_width=True,
                                  on_click=lambda n=name: setattr(st.session_state, "active_collection", n))
                with bc[1]:
                    if st.button("🧹 清空", key=f"clr_{name}", use_container_width=True):
                        st.session_state.dialog_target = name
                        st.session_state.show_clear_dialog = True
                        st.rerun()
                with bc[2]:
                    if st.button("🗑️ 删除", key=f"del_{name}", use_container_width=True):
                        st.session_state.dialog_target = name
                        st.session_state.show_delete_dialog = True
                        st.rerun()

# ═══════════════════════════════════════════
# 层 1.5: 分面统计 + 知识管理（仅当前集合有数据时显示）
# ═══════════════════════════════════════════
active_col_info = next((c for c in collections if c["name"] == current_col), None)
if active_col_info and active_col_info["points"] > 0:
    st.markdown("---")
    mgmt_tab1, mgmt_tab2 = st.tabs(["📊 分面统计", "🔧 知识管理"])

    with mgmt_tab1:
        st.markdown("#### 分面维度分布")
        if st.button("🔄 刷新统计", key="refresh_facet_stats", type="secondary"):
            st.session_state.facet_stats = kb_query.get_facet_stats(current_col)
            st.rerun()

        facet_stats = st.session_state.get("facet_stats")
        if facet_stats is None:
            # 首次加载
            with st.spinner("统计中..."):
                facet_stats = kb_query.get_facet_stats(current_col)
                st.session_state.facet_stats = facet_stats

        if facet_stats and facet_stats.get("ok"):
            fs = facet_stats
            total = fs.get("total_points", 0)
            meta = fs.get("meta", {})

            # Meta 卡片
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("总条目", total)
            mc2.metric("平均可信度", f"{meta.get('avg_trust', 0)} ⭐")
            mc3.metric("个人化", meta.get('personal_count', 0))
            mc4.metric("已归档", meta.get('archived_count', 0))

            facets = fs.get("facets", {})

            # 内容类型分布
            ct_data = facets.get("content_type", {})
            if ct_data:
                st.markdown("##### 内容类型分布")
                from config.classifications import CONTENT_TYPE_OPTIONS
                ct_labels = dict(CONTENT_TYPE_OPTIONS)
                ct_bars = ""
                for ct, cnt in sorted(ct_data.items(), key=lambda x: -x[1]):
                    pct = f"{cnt/total*100:.0f}%"
                    label = ct_labels.get(ct, ct)
                    ct_bars += f'<div style="display:flex;align-items:center;margin:4px 0;"><span style="width:120px;color:#ccc;font-size:12px;">{label}</span><div style="flex:1;background:rgba(255,107,53,0.1);border-radius:4px;height:18px;"><div style="width:{pct};background:linear-gradient(90deg,#FF6B35,#F7C948);height:100%;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:6px;"><span style="font-size:10px;color:#1a1a2e;font-weight:600;">{cnt}</span></div></div></div>'
                st.markdown(ct_bars, unsafe_allow_html=True)

            # 主题域分布
            domain_data = facets.get("domain", {})
            if domain_data:
                st.markdown("##### 主题域分布")
                from config.classifications import DOMAIN_OPTIONS
                dom_labels = dict(DOMAIN_OPTIONS)
                dom_cols = st.columns(min(len(domain_data), 4))
                for idx, (d, cnt) in enumerate(sorted(domain_data.items(), key=lambda x: -x[1])):
                    with dom_cols[idx % len(dom_cols)]:
                        st.metric(dom_labels.get(d, d), cnt)

            # 生命周期分布
            lc_data = facets.get("lifecycle", {})
            if lc_data:
                st.markdown("##### 生命周期分布")
                from config.classifications import LIFECYCLE_OPTIONS
                lc_labels = dict(LIFECYCLE_OPTIONS)
                lc_items = []
                for lc, cnt in sorted(lc_data.items(), key=lambda x: -x[1]):
                    icon = {"idea": "💡", "draft": "📝", "in_progress": "⚙️", "review": "👁️", "published": "✅", "archived": "📦"}.get(lc, "📌")
                    lc_items.append(f"{icon} {lc_labels.get(lc, lc)}: **{cnt}**")
                st.markdown(" · ".join(lc_items))
        else:
            st.info("暂无统计数据。请先摄入文档。")

    with mgmt_tab2:
        st.markdown("#### 知识条目管理")
        st.caption("按文档管理：修改字段、建立关系、归档/删除。")

        # 加载文档列表
        if st.button("📋 加载文档列表", key="load_doc_list", type="secondary"):
            with st.spinner("加载中..."):
                st.session_state.doc_list = kb_query.get_doc_ids(current_col)
            st.rerun()

        doc_list = st.session_state.get("doc_list", {})
        if doc_list and doc_list.get("ok"):
            doc_ids = doc_list.get("doc_ids", [])
            st.caption(f"共 **{len(doc_ids)}** 个文档")

            # 选一个文档进行管理
            selected_doc = st.selectbox(
                "选择要管理的文档",
                options=[""] + doc_ids,
                format_func=lambda x: "（选择文档）" if x == "" else x[:16],
                key="mgmt_selected_doc",
            )

            if selected_doc:
                st.session_state.mgmt_doc = selected_doc
                # 加载文档详情
                doc_info = kb_query.search_by_doc_id(selected_doc)
                if doc_info.get("ok") and doc_info.get("chunks"):
                    first = doc_info["chunks"][0]

                    st.markdown("---")
                    st.markdown(f"**📄 {first.get('title', '无标题')}**")
                    st.caption(f"类型: {first.get('content_type', '?')} · 可信度: {'⭐'*first.get('trust_score',3)} · 块数: {doc_info.get('total',0)}")
                    if first.get("auto_summary"):
                        st.caption(f"摘要: {first['auto_summary'][:100]}")

                    # 快捷操作
                    mgmt_col1, mgmt_col2, mgmt_col3 = st.columns(3)
                    with mgmt_col1:
                        new_trust = st.slider("可信度", 1, 5, first.get("trust_score", 3), key="mgmt_trust")
                        if st.button("💾 更新可信度", key="save_trust", use_container_width=True):
                            r = kb_query.update_metadata(selected_doc, {"trust_score": new_trust})
                            if r.get("ok"):
                                st.success(f"✅ 已更新 {r['updated']} 条")
                                clear_kb_caches()
                                st.rerun()
                            else:
                                st.error(r.get("error", "失败"))

                    with mgmt_col2:
                        is_arch = first.get("is_archived", False)
                        archive_btn = "📤 取消归档" if is_arch else "📦 归档"
                        if st.button(archive_btn, key="toggle_archive", use_container_width=True):
                            r = kb_query.update_metadata(selected_doc, {"is_archived": not is_arch})
                            if r.get("ok"):
                                st.success(f"✅ 已{'取消归档' if is_arch else '归档'} {r['updated']} 条")
                                clear_kb_caches()
                                st.rerun()
                            else:
                                st.error(r.get("error", "失败"))

                    with mgmt_col3:
                        is_can = first.get("is_canonical", True)
                        can_btn = "⭐ 标记非主版本" if is_can else "✅ 标记为主版本"
                        if st.button(can_btn, key="toggle_canonical", use_container_width=True):
                            r = kb_query.update_metadata(selected_doc, {"is_canonical": not is_can})
                            if r.get("ok"):
                                st.success(f"✅ {r['updated']} 条已更新")
                                clear_kb_caches()
                                st.rerun()
                            else:
                                st.error(r.get("error", "失败"))

                    # 关系管理
                    st.markdown("---")
                    st.markdown("##### 🔗 关系管理")
                    current_rels = first.get("relations", [])
                    if current_rels:
                        rel_text = ""
                        for r in current_rels:
                            rel_type = r.get("type", "?")
                            rel_doc = r.get("doc_id", "?")
                            emoji = {"similar": "📖", "references": "📎", "contradicts": "⚠️", "derived_from": "📄", "merged_into": "🔗", "supersedes": "🔄"}.get(rel_type, "🔹")
                            rel_text += f"{emoji} {rel_type}: `{rel_doc[:12]}`  \n"
                        st.markdown(rel_text or "*无关系*")
                    else:
                        st.caption("*暂无关系*")

                    rel_col1, rel_col2, rel_col3 = st.columns([1, 2, 2])
                    with rel_col1:
                        rel_type = st.selectbox("关系类型", ["similar", "references", "contradicts", "derived_from", "merged_into", "supersedes"], key="mgmt_rel_type")
                    with rel_col2:
                        rel_target = st.text_input("目标文档ID", placeholder="doc_id", key="mgmt_rel_target")
                    with rel_col3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("➕ 添加关系", key="add_rel", use_container_width=True):
                            if rel_target.strip():
                                r = kb_query.set_doc_relations(selected_doc, add_relations=[{"type": rel_type, "doc_id": rel_target.strip()}])
                                if r.get("ok"):
                                    st.success(f"✅ 已添加关系（{r['updated']} 条）")
                                    clear_kb_caches()
                                    st.rerun()
                                else:
                                    st.error(r.get("error", "失败"))
        else:
            st.info("点击「加载文档列表」查看可管理的文档。")

# ═══════════════════════════════════════════
# 层 2: 集合操作区
# ═══════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔧 集合操作区")

op1, op2, op3 = st.columns(3)

with op1:
    st.markdown("#### ➕ 新建集合")
    new_name = st.text_input("集合名称", placeholder="engine, materials, notes...",
                             key="new_col", label_visibility="collapsed")
    if st.button("➕ 创建", type="primary", use_container_width=True, key="create_btn"):
        if not new_name.strip():
            st.warning("⚠️ 请输入名称")
        elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_name.strip()):
            st.warning("⚠️ 名称只能包含英文字母、数字和下划线")
        else:
            existing = [c["name"] for c in collections]
            if new_name.strip() in existing:
                st.warning(f"⚠️ 集合「{new_name.strip()}」已存在")
            elif kb_query._ensure_collection(new_name.strip()):
                st.success(f"✅ 集合「{new_name.strip()}」已创建！")
                st.session_state.active_collection = new_name.strip()
                clear_kb_caches()
                st.rerun()
            else:
                st.error("Qdrant 未运行")

with op2:
    st.markdown("#### 📊 当前分类法")
    st.info("**分面分类法** — 单集合 `athanor_v1` + 多维度 Payload 过滤\n\n内容类型 / 主题域 / 生命周期 / 来源项目")
    st.caption("分面分类是统一方案，不再需要切换。")

with op3:
    st.markdown("#### 💾 导出备份")
    if st.button("📤 导出集合统计", use_container_width=True, key="export_stats"):
        st.session_state.show_stats_dl = True
    if st.session_state.get("show_stats_dl"):
        stats = [
            {"name": c["name"], "points": c["points"], "dim": c["dim"],
             "embed_model": current_embed, "classification": "faceted"}
            for c in collections
        ]
        st.download_button("📥 下载 JSON", json.dumps(stats, ensure_ascii=False, indent=2),
                           file_name="collections_stats.json", mime="application/json",
                           use_container_width=True)
    if st.button("📤 备份摄入日志", use_container_width=True, key="export_log"):
        st.session_state.show_log_dl = True
    if st.session_state.get("show_log_dl"):
        log_entries = cached_ingest_log()
        if log_entries:
            st.download_button("📥 下载日志", json.dumps(log_entries, ensure_ascii=False, indent=2),
                               file_name="ingest_log_backup.json", mime="application/json",
                               use_container_width=True)
        else:
            st.caption("摄入日志为空")

# ═══════════════════════════════════════════
# 层 3: 重建与迁移
# ═══════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔄 重建与迁移")
st.caption("换嵌入模型或分类法后，用此功能重新处理已摄入的文档。")

log_entries = cached_ingest_log()
if not log_entries:
    st.info("📭 摄入日志为空。摄入过文档后这里会有记录。")
else:
    by_file = defaultdict(list)
    for e in log_entries:
        key = e.get("source_file", "") or e.get("source_text", "手动输入")[:30]
        by_file[key].append(e)
    st.markdown(f"追踪到 **{len(by_file)}** 个源文件/记录")
    st.caption("注：当前版本重建全部文件，后续将支持按文件筛选。")

    target_opts = [c["name"] for c in collections]
    target_cols = st.multiselect("重建到集合（留空=原集合）", options=target_opts)

    st.caption(
        f"将重建 {len(log_entries)} 条记录，"
        f"目标: {'、'.join(target_cols) if target_cols else '原始集合'}"
    )

    if st.button("🔄 开始重建", type="primary", use_container_width=True):
        if not kb_query._check_qdrant():
            st.error("⚠️ Qdrant 未运行。")
        else:
            with st.spinner("重建中...（可能需要几分钟）"):
                progress_bar = st.progress(0, "准备中...")
                def update_progress(current, total, msg):
                    if total > 0:
                        progress_bar.progress(int(current / total * 100), msg)
                result = kb_query.rebuild_from_log(
                    target_collections=target_cols if target_cols else None,
                    progress_callback=update_progress,
                )
            progress_bar.empty()
            if result.get("ok"):
                st.success(f"✅ 重建完成！成功 {result['rebuilt']} 篇，跳过 {result['skipped']} 篇")
                if result.get("errors"):
                    with st.expander(f"⚠️ {len(result['errors'])} 个错误"):
                        for err in result["errors"]:
                            st.markdown(f"- {err}")
                clear_kb_caches()
            else:
                st.error(f"❌ 重建失败: {result.get('error', '未知错误')}")
