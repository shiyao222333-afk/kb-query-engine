"""
💬 智能检索 — 语义搜索 + AI 问答合并，勾选是否用 LLM，跨库搜索
"""

import streamlit as st
import os
import sys
import html as html_mod

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
import kb_query
from config import classifications  # 新增：导入分面分类定义
from utils.ui_utils import (
    render_sidebar, cached_stats, cached_collections,
)
from utils.flame_bg import render_flame_banner

# ── 侧边栏 ──
with st.sidebar:
    render_sidebar()

# ── 标题 ──
st.title("💬 智能检索")
render_flame_banner()

collection = st.session_state.get("active_collection", kb_query.DEFAULT_COLLECTION)
qdrant_info = cached_stats(collection)
if qdrant_info.get("status") != "ok":
    st.error("⚠️ Qdrant 未运行，无法搜索。请先启动 `run.bat`。")

# ── 知识库选择 ──
col_data = cached_collections()
all_cols = [c["name"] for c in col_data.get("collections", [])] if col_data.get("ok") else [collection]
if all_cols:
    selected_col = st.selectbox(
        "📚 搜索范围",
        options=all_cols,
        index=all_cols.index(collection) if collection in all_cols else 0,
        help="选择要搜索的知识库。",
    )
else:
    selected_col = collection

# ── 输入框 ──
query = st.text_input(
    "输入问题或关键词",
    placeholder="例如：齿轮的失效形式有哪些？",
    label_visibility="collapsed",
    key="search_query",
)

# ── 控制栏 ──
col1, col2, col3 = st.columns([2, 1, 3])

with col1:
    use_llm = st.checkbox("🤖 使用 AI 综合回答", value=False,
                          help="勾选后将先搜索知识库，再调用 LLM 综合成答案。不勾选只显示原始搜索结果。")

with col2:
    top_k = st.selectbox("返回条数", [3, 5, 10, 20], index=1, key="search_top_k")

with col3:
    search_btn = st.button("🔍 开始检索", type="primary", use_container_width=True)

# ── 分面过滤选项（展开可选）──
with st.expander("📊 分面过滤（可选，缩小搜索范围）", expanded=False):
    st.caption("留空表示不过滤（全库搜索）")

    fcol1, fcol2, fcol3 = st.columns(3)

    with fcol1:
        filter_content_type = st.multiselect(
            "内容类型",
            options=[o[0] for o in classifications.CONTENT_TYPE_OPTIONS],
            format_func=lambda x: dict(classifications.CONTENT_TYPE_OPTIONS).get(x, x),
            default=[],
            key="ff_ctype",
        )
        filter_lifecycle = st.selectbox(
            "生命周期",
            options=[""] + [o[0] for o in classifications.LIFECYCLE_OPTIONS],
            format_func=lambda x: "（不过滤）" if x == "" else dict(classifications.LIFECYCLE_OPTIONS).get(x, x),
            index=0,
            key="ff_lcycle",
        )

    with fcol2:
        filter_domain = st.multiselect(
            "主题域",
            options=[o[0] for o in classifications.DOMAIN_OPTIONS],
            format_func=lambda x: dict(classifications.DOMAIN_OPTIONS).get(x, x),
            default=[],
            key="ff_domain",
        )
        filter_project = st.selectbox(
            "来源项目",
            options=[""] + [o[0] for o in classifications.PROJECT_SOURCE_OPTIONS],
            format_func=lambda x: "（不过滤）" if x == "" else dict(classifications.PROJECT_SOURCE_OPTIONS).get(x, x),
            index=0,
            key="ff_psource",
        )

    with fcol3:
        filter_is_personal = st.selectbox(
            "是否个人化",
            options=["", "false", "true"],
            format_func=lambda x: "（不过滤）" if x == "" else "✅ 个人化" if x == "true" else "📖 非个人化",
            index=0,
            key="ff_personal",
        )
        filter_trust_min = st.slider(
            "最低可信度",
            min_value=1,
            max_value=5,
            value=1,
            format="⭐ %d+",
            key="ff_trust",
        )

    # 构建 facet_filter dict（只传非空的过滤条件）
    facet_filter = {}
    if filter_content_type:
        facet_filter["content_type"] = filter_content_type
    if filter_domain:
        facet_filter["domain"] = filter_domain
    if filter_lifecycle and filter_lifecycle != "":
        facet_filter["lifecycle"] = filter_lifecycle
    if filter_project and filter_project != "":
        facet_filter["project_source"] = filter_project
    if filter_is_personal and filter_is_personal != "":
        facet_filter["is_personal"] = (filter_is_personal == "true")
    if filter_trust_min > 1:
        facet_filter["trust_score_min"] = filter_trust_min

    # 显示当前过滤条件
    if facet_filter:
        st.success(f"✅ 已启用 {len(facet_filter)} 项过滤条件")
    else:
        st.caption("💡 未设置过滤条件，将进行全库搜索")

# ── 搜索逻辑 ──
if search_btn and query.strip():
    if qdrant_info.get("status") != "ok":
        st.error("⚠️ Qdrant 未运行。")
    elif not selected_col:
        st.warning("⚠️ 没有可选的知识库。")
    else:
        if use_llm:
            if not os.environ.get("KB_LLM_API_KEY"):
                st.error("⚠️ 未配置 LLM API Key，请先到「引擎配置」页面配置。")
            else:
                with st.spinner("🔍 搜索 + AI 合成中..."):
                    answer_kwargs = dict(
                        query=query.strip(),
                        top_k=top_k,
                        collection=selected_col,
                        llm_api_key=os.environ.get("KB_LLM_API_KEY", ""),
                        llm_base_url=os.environ.get("KB_LLM_BASE_URL", ""),
                        llm_model=os.environ.get("KB_LLM_MODEL", ""),
                    )
                    # 传入分面过滤条件
                    if facet_filter:
                        answer_kwargs["facet_filter"] = facet_filter

                    result = kb_query.answer(**answer_kwargs)
                st.session_state.last_answer = result
        else:
            with st.spinner("🔍 搜索中..."):
                search_kwargs = dict(
                    query=query.strip(),
                    top_k=top_k,
                    collection=selected_col,
                )
                # 传入分面过滤条件
                if facet_filter:
                    search_kwargs["facet_filter"] = facet_filter

                result = kb_query.search(**search_kwargs)
            st.session_state.last_search = result
            st.session_state.last_answer = None

# ── 渲染结果 ──
# AI 问答结果
if st.session_state.get("last_answer"):
    result = st.session_state.last_answer
    st.markdown("---")
    if not result.get("ok"):
        st.error(f"❌ {result.get('error', '请求失败')}")
    else:
        synthesis = result.get("synthesis", "")
        chunks = result.get("chunks", [])

        st.markdown("### 🤖 AI 综合回答")
        st.markdown(f"""
        <div class="kf-answer-card" style="white-space:pre-wrap">
            {html_mod.escape(synthesis)}
        </div>
        """, unsafe_allow_html=True)

        if chunks:
            st.markdown("---")
            st.markdown(f"### 📚 引用来源（共 {len(chunks)} 条）")
            from config.classifications import CONTENT_TYPE_OPTIONS as CTO_REF
            for i, chunk in enumerate(chunks):
                score = chunk.get("score", 0)
                source = chunk.get("source", "未知")
                title = chunk.get("title", source)
                text = chunk.get("text", "")[:300]
                ctype = chunk.get("content_type", "")
                ct_label = dict(CTO_REF).get(ctype, ctype)
                domain = chunk.get("domain", [])
                trust = chunk.get("trust_score", 0)
                trust_stars = "⭐" * trust + "☆" * (5 - trust) if trust else ""
                keywords = chunk.get("keywords", [])

                badge = f'<span style="background:rgba(255,107,53,0.15);color:#FF6B35;font-size:10px;padding:1px 4px;border-radius:3px;margin-right:3px;">{ct_label}</span>{trust_stars}'
                if keywords:
                    badge += f' <span style="color:#888;font-size:9px;">🔑 {", ".join(keywords[:2])}</span>'

                with st.expander(f"[{i+1}] {title} — 相关度 {score:.2f}"):
                    st.markdown(badge, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="kf-score-bar" style="width:{int(score*100)}%"></div>
                    """, unsafe_allow_html=True)
                    if source and source != "未知":
                        st.caption(f"📄 来源: {source}")
                    st.markdown(f"**内容**：{text}")

        # 下载报告
        html_path = result.get("html")
        pdf_path = result.get("pdf")
        has_report = (html_path and os.path.exists(html_path))
        if has_report:
            st.markdown("---")
            dl_col1, dl_col2 = st.columns(2)
            if html_path and os.path.exists(html_path):
                with dl_col1:
                    with open(html_path, "r", encoding="utf-8") as f:
                        st.download_button(
                            "📥 下载 HTML 报告",
                            f.read(),
                            file_name=os.path.basename(html_path),
                            mime="text/html",
                            use_container_width=True,
                        )
            if pdf_path and os.path.exists(pdf_path):
                with dl_col2:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📥 下载 PDF 报告",
                            f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            use_container_width=True,
                        )

# 纯搜索结果
elif st.session_state.get("last_search"):
    sr = st.session_state.last_search
    st.markdown("---")
    if not sr.get("ok"):
        st.error(f"❌ 搜索失败: {sr.get('error', '未知错误')}")
    else:
        chunks = sr.get("chunks", [])
        if not chunks:
            st.info("📭 未找到相关内容，请尝试更换关键词。")
        else:
            st.markdown(f"### 📋 搜索结果（共 {len(chunks)} 条）")
            for i, chunk in enumerate(chunks):
                score = chunk.get("score", 0)
                source = chunk.get("source", "未知")
                title = chunk.get("title", source)
                text = chunk.get("text", "")
                ctype = chunk.get("content_type", "")
                domain = chunk.get("domain", [])
                trust = chunk.get("trust_score", 0)
                keywords = chunk.get("keywords", [])
                relations = chunk.get("relations", [])
                timeline = chunk.get("timeline", {})
                origin = chunk.get("origin", {})
                version = chunk.get("version", "")

                # 内容类型中文映射
                from config.classifications import CONTENT_TYPE_OPTIONS
                ct_label = dict(CONTENT_TYPE_OPTIONS).get(ctype, ctype)
                from config.classifications import DOMAIN_OPTIONS
                domain_labels = {d: dict(DOMAIN_OPTIONS).get(d, d) for d in domain}

                # 构建标签行
                badge_html = f'<span style="background:rgba(255,107,53,0.15);color:#FF6B35;font-size:10px;padding:1px 6px;border-radius:3px;margin-right:4px;">{ct_label}</span>'
                for d, dl in domain_labels.items():
                    badge_html += f'<span style="background:rgba(247,201,72,0.15);color:#F7C948;font-size:10px;padding:1px 6px;border-radius:3px;margin-right:4px;">{dl}</span>'
                trust_html = "⭐" * trust + "☆" * (5 - trust)
                badge_html += f'<span style="color:#F7C948;font-size:10px;margin-left:4px;">{trust_html}</span>'
                if keywords:
                    kw_str = ", ".join(keywords[:3])
                    badge_html += f'<span style="color:#888;font-size:9px;margin-left:6px;">🔑 {kw_str}</span>'

                with st.expander(f"[{i+1}] {title} — 相关度 {score:.2f}"):
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="kf-score-bar" style="width:{int(score*100)}%"></div>
                    """, unsafe_allow_html=True)
                    if source and source != "未知":
                        st.caption(f"📄 来源: {source}")
                    if version:
                        st.caption(f"📌 版本: {version}")
                    if origin.get("author"):
                        st.caption(f"✍️ 作者: {origin['author']}")
                    if timeline.get("published"):
                        st.caption(f"📅 发布: {timeline['published']}")
                    st.markdown(text)

                    # 关系展示
                    if relations:
                        from config.classifications import CONTENT_TYPE_OPTIONS as CTO
                        rel_parts = []
                        for r in relations:
                            rtype = r.get("type", "")
                            rdoc = r.get("doc_id", "")
                            emoji = {"similar": "📖", "references": "📎", "contradicts": "⚠️", "derived_from": "📄", "merged_into": "🔗", "supersedes": "🔄"}.get(rtype, "🔹")
                            rel_parts.append(f"{emoji} {rtype}: {rdoc[:12]}")
                        if rel_parts:
                            st.caption(" | ".join(rel_parts))
