"""
共享摄入表单组件 — v0.4.1

所有摄入 Tab（上传/OCR/手动）共用此组件，消除 ~200 行重复表单代码。

v0.4.1: 适配分面分类 v5.0 — temporal_nature + epistemic_status 替换 project_source
"""
import streamlit as st
from config.classifications import (
    CONTENT_TYPE_OPTIONS, DOMAIN_OPTIONS, LIFECYCLE_OPTIONS,
    TEMPORAL_NATURE_OPTIONS, EPISTEMIC_STATUS_OPTIONS,
    KNOWLEDGE_TYPE_OPTIONS,
    TARGET_PLATFORM_OPTIONS, LANGUAGE_OPTIONS, ACCESS_LEVEL_OPTIONS,
)


def _widget_key(prefix: str, field: str) -> str:
    """生成唯一 widget key: {prefix}_{field}"""
    return f"{prefix}_{field}"


def render_facet_form(prefix: str, defaults: dict = None) -> dict:
    """
    渲染分面字段表单（主分面 + 高级字段折叠面板）。
    三个 Tab 共用此函数，通过 prefix 区分 widget key。

    参数:
        prefix:   widget key 前缀（如 "upload" / "ocr" / "manual"）
        defaults: 预填值 dict（来自 auto_classify 结果），键名与返回值一致

    返回:
        dict 包含所有分面字段的值，可直接传给 build_facet_metadata()
    """
    d = defaults or {}

    # ── 主分面字段 ──
    st.markdown("---")
    st.markdown("#### 📋 分面字段（入库元数据）")

    col1, col2 = st.columns(2)
    with col1:
        # content_type — 默认值由调用方通过 defaults 控制
        ct_idx = _find_index(CONTENT_TYPE_OPTIONS, d.get("content_type", "knowledge"))
        content_type = st.selectbox(
            "内容类型 *",
            options=[o[0] for o in CONTENT_TYPE_OPTIONS],
            format_func=lambda x: dict(CONTENT_TYPE_OPTIONS).get(x, x),
            index=ct_idx,
            key=_widget_key(prefix, "content_type"),
            help="这条内容是什么类型",
        )
        lc_idx = _find_index(LIFECYCLE_OPTIONS, d.get("lifecycle", "published"))
        lifecycle = st.selectbox(
            "生命周期 *",
            options=[o[0] for o in LIFECYCLE_OPTIONS],
            format_func=lambda x: dict(LIFECYCLE_OPTIONS).get(x, x),
            index=lc_idx,
            key=_widget_key(prefix, "lifecycle"),
            help="内容当前在哪个阶段（必填）",
        )
    with col2:
        tn_idx = _find_index(TEMPORAL_NATURE_OPTIONS, d.get("temporal_nature", "timeboxed"))
        temporal_nature = st.selectbox(
            "时效属性 *",
            options=[o[0] for o in TEMPORAL_NATURE_OPTIONS],
            format_func=lambda x: dict(TEMPORAL_NATURE_OPTIONS).get(x, x),
            index=tn_idx,
            key=_widget_key(prefix, "temporal_nature"),
            help="这条知识会随时间贬值吗",
        )
        ep_idx = _find_index(EPISTEMIC_STATUS_OPTIONS, d.get("epistemic_status", "unverified"))
        epistemic_status = st.selectbox(
            "认知验证 *",
            options=[o[0] for o in EPISTEMIC_STATUS_OPTIONS],
            format_func=lambda x: dict(EPISTEMIC_STATUS_OPTIONS).get(x, x),
            index=ep_idx,
            key=_widget_key(prefix, "epistemic_status"),
            help="L0猜想 / L1逻辑验证 / L2实证验证",
        )

    # domain — 支持多选 + 默认值（必填）
    default_domains = d.get("domain", [])
    if isinstance(default_domains, str):
        default_domains = [default_domains]
    domain = st.multiselect(
        "主题域 *（可多选，至少一个）",
        options=[o[0] for o in DOMAIN_OPTIONS],
        format_func=lambda x: dict(DOMAIN_OPTIONS).get(x, x),
        default=[d for d in default_domains if d in dict(DOMAIN_OPTIONS)],
        key=_widget_key(prefix, "domain"),
        help="这条内容关于什么领域，必填，至少选一个",
    )
    if not domain:
        st.warning("⚠️ 主题域为必填项，请至少选择一个领域。")

    # ── 辅助字段 ──
    col_lc, col_ip, col_ps = st.columns(3)
    with col_lc:
        lc_idx = _find_index(LIFECYCLE_OPTIONS, d.get("lifecycle", "published"))
        lifecycle = st.selectbox(
            "工作流阶段",
            options=[o[0] for o in LIFECYCLE_OPTIONS],
            format_func=lambda x: dict(LIFECYCLE_OPTIONS).get(x, x),
            index=lc_idx,
            key=_widget_key(prefix, "lifecycle"),
            help="内容写到哪一步了（非分面）",
        )
    with col_ip:
        is_personal = st.checkbox(
            "个人化内容",
            value=bool(d.get("is_personal", False)),
            key=_widget_key(prefix, "is_personal"),
            help="勾选表示这是个人笔记/想法，非公开知识",
        )
    with col_ps:
        project_source = st.text_input(
            "关联项目",
            value=d.get("project_source", ""),
            key=_widget_key(prefix, "project_source"),
            help="关联的产品/项目名（可选，如'智能台灯Pro'）",
            placeholder="例如：智能台灯Pro",
        )

    # trust_score — 支持默认值
    trust_score = st.slider(
        "可信度",
        min_value=1, max_value=5,
        value=int(d.get("trust_score", 3)),
        format="⭐ %d",
        key=_widget_key(prefix, "trust_score"),
        help="1=存疑，5=权威来源",
    )

    # tags
    tags_input = st.text_input(
        "标签（逗号分隔）",
        value=", ".join(d.get("tags", [])) if isinstance(d.get("tags"), list) else d.get("tags", ""),
        placeholder="例如：齿轮,强度计算,Q235",
        key=_widget_key(prefix, "tags"),
        help="自定义标签，用于精细过滤",
    )

    # ── 高级字段（折叠面板）──
    with st.expander("📋 高级字段（标题、作者、版本等）", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            title = st.text_input("标题", value=d.get("title", ""),
                placeholder="留空则用文件名", key=_widget_key(prefix, "title"),
                help="知识条目的标题，搜索结果展示用")
            author = st.text_input("作者/来源", value=d.get("author", ""),
                placeholder="例如：国家标准化管理委员会", key=_widget_key(prefix, "author"),
                help="原作者或来源组织")
            version = st.text_input("版本号", value=d.get("version", ""),
                placeholder="例如：GB/T 1357-2008", key=_widget_key(prefix, "version"),
                help="标准版本号或文档版本")
            lang_idx = _find_index(LANGUAGE_OPTIONS, d.get("language", "zh"))
            language = st.selectbox("语言", options=[o[0] for o in LANGUAGE_OPTIONS],
                format_func=lambda x: dict(LANGUAGE_OPTIONS).get(x, x),
                index=lang_idx, key=_widget_key(prefix, "language"),
                help="文档语言")
        with c2:
            kt = d.get("knowledge_type", "")
            kt_idx = _find_index([("", "（自动）")] + KNOWLEDGE_TYPE_OPTIONS, kt) if kt else 0
            knowledge_type = st.selectbox("知识子类型",
                options=[""] + [o[0] for o in KNOWLEDGE_TYPE_OPTIONS],
                format_func=lambda x: "（自动）" if x == "" else dict(KNOWLEDGE_TYPE_OPTIONS).get(x, x),
                index=kt_idx, key=_widget_key(prefix, "knowledge_type"),
                help="仅 content_type=knowledge 时有效")
            tp = d.get("target_platform", "")
            tp_idx = _find_index([("", "（无）")] + TARGET_PLATFORM_OPTIONS, tp) if tp else 0
            target_platform = st.selectbox("目标平台",
                options=[""] + [o[0] for o in TARGET_PLATFORM_OPTIONS],
                format_func=lambda x: "（无）" if x == "" else dict(TARGET_PLATFORM_OPTIONS).get(x, x),
                index=tp_idx, key=_widget_key(prefix, "target_platform"),
                help="内容创作目标发布平台")
            al_idx = _find_index(ACCESS_LEVEL_OPTIONS, d.get("access_level", "private"))
            access_level = st.selectbox("访问权限",
                options=[o[0] for o in ACCESS_LEVEL_OPTIONS],
                format_func=lambda x: dict(ACCESS_LEVEL_OPTIONS).get(x, x),
                index=al_idx, key=_widget_key(prefix, "access_level"),
                help="知识的访问权限级别")
            related_product = st.text_input("关联产品", value=d.get("related_product", ""),
                placeholder="例如：智能台灯Pro", key=_widget_key(prefix, "related_product"),
                help="关联的产品名称")
        with c3:
            kw = d.get("keywords", [])
            kw_str = ", ".join(kw) if isinstance(kw, list) else str(kw)
            keywords = st.text_input("关键词（逗号分隔）", value=kw_str,
                placeholder="例如：齿轮,模数,强度", key=_widget_key(prefix, "keywords"),
                help="用于精确匹配搜索")
            source_url = st.text_input("来源链接", value=d.get("source_url", ""),
                placeholder="https://...", key=_widget_key(prefix, "source_url"),
                help="原始来源URL")
            publish_date = st.text_input("发布时间", value=d.get("publish_date", ""),
                placeholder="YYYY-MM-DD", key=_widget_key(prefix, "publish_date"),
                help="原始文档的发布时间")
            file_type = st.selectbox("原始文件类型",
                options=["txt", "pdf", "md", "json", "docx", "html", "image"],
                index=0, key=_widget_key(prefix, "file_type"),
                help="原始文件格式")

    # ── 返回所有值 ──
    return {
        "content_type":     content_type,
        "domain":           domain,
        "temporal_nature":  temporal_nature,
        "epistemic_status": epistemic_status,
        "lifecycle":        lifecycle,
        "is_personal":      is_personal,
        "project_source":   project_source,
        "trust_score":      trust_score,
        "tags":             tags_input,
        "title":            title,
        "author":           author,
        "version":          version,
        "language":         language,
        "knowledge_type":   knowledge_type,
        "target_platform":  target_platform,
        "access_level":     access_level,
        "related_product":  related_product,
        "keywords":         keywords,
        "source_url":       source_url,
        "publish_date":     publish_date,
        "file_type":        file_type,
    }


def validate_facet_form(form: dict) -> tuple:
    """
    校验四个核心分面是否全部非空。

    返回:
        (is_valid: bool, errors: list[str])
    """
    errors = []
    required_facets = {
        "content_type": "内容类型",
        "domain": "主题域",
        "temporal_nature": "时效属性",
        "epistemic_status": "认知验证状态",
    }
    for key, label in required_facets.items():
        val = form.get(key)
        if val is None or (isinstance(val, (list, str)) and len(val) == 0) or val == "":
            errors.append(f"「{label}」为必填分面，不能为空")
    return len(errors) == 0, errors


def build_facet_metadata(form: dict, ingest_method: str, source: str = "") -> dict:
    """
    将 render_facet_form() 的 dict 输出转换为 ingest() 的 metadata 参数。

    处理类型转换（字符串 → 列表等）、空值处理、默认值。

    参数:
        form:          render_facet_form() 的返回值
        ingest_method: "upload" / "ocr" / "manual"
        source:        来源标识（文件名等）

    返回:
        dict，可直接解包到 ingest(metadata={...})
    """
    def _parse_list(val):
        """将字符串（逗号分隔）或列表转换为干净的 list"""
        if isinstance(val, list):
            return [v.strip() for v in val if v and str(v).strip()]
        if isinstance(val, str) and val.strip():
            return [v.strip() for v in val.split(",") if v.strip()]
        return []

    metadata = {
        "source": source or "未命名来源",

        # 分面字段
        "content_type":     form.get("content_type", "knowledge"),
        "domain":           form.get("domain", []),
        "temporal_nature":  form.get("temporal_nature", "timeboxed"),
        "epistemic_status": form.get("epistemic_status", "unverified"),

        # 普通字段
        "lifecycle":       form.get("lifecycle", "published"),
        "project_source":  form.get("project_source", ""),
        "is_personal":     bool(form.get("is_personal", False)),
        "trust_score":     int(form.get("trust_score", 3)),

        # 标签
        "tags":     _parse_list(form.get("tags", "")),
        "keywords": _parse_list(form.get("keywords", "")),

        # 高级字段 — 文本类
        "title":    form.get("title", "").strip() or None,
        "author":   form.get("author", "").strip() or None,
        "version":  form.get("version", "").strip() or None,

        # 高级字段 — 选择类
        "language":        form.get("language", "zh"),
        "knowledge_type":  form.get("knowledge_type", "") or None,
        "target_platform": form.get("target_platform", "") or None,
        "access_level":    form.get("access_level", "private"),
        "file_type":       form.get("file_type", "txt"),

        # 高级字段 — 其他
        "related_product": form.get("related_product", "").strip() or None,
        "source_url":      form.get("source_url", "").strip() or None,
        "publish_date":    form.get("publish_date", "").strip() or None,

        # 摄入方式
        "ingest_method": ingest_method,
    }

    return metadata


def _find_index(options: list, val: str) -> int:
    """在 [(key, label), ...] 列表中查找 key 匹配的 index"""
    for i, (k, _) in enumerate(options):
        if k == val:
            return i
    return 0
