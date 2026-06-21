"""
Citrinitas · 熔知 — Qdrant 客户端

Qdrant 连接检查 / 集合创建与管理 / 嵌入模型列表。
所有函数返回统一的 {"ok": bool, ...} 格式。
"""

import requests
import logging
from qconst import QDRANT_URL, DEFAULT_COLLECTION, OLLAMA_URL, EMBED_DIM, _check_qdrant

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# 集合管理
# ═══════════════════════════════════════════

def _ensure_collection(collection: str) -> bool:
    """确保指定集合存在，不存在则自动创建。"""
    if not _check_qdrant():
        return False
    try:
        resp = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        names = [c["name"] for c in resp.json()["result"]["collections"]]
        if collection not in names:
            requests.put(
                f"{QDRANT_URL}/collections/{collection}",
                json={"vectors": {"size": EMBED_DIM, "distance": "Cosine"}},
                timeout=10
            )
            # ── 创建 Payload Index（分面字段 + 常用过滤字段）──
            payload_index_fields = {
                "content_type":     "keyword",
                "domain":          "keyword",  # list of keywords
                "temporal_nature": "keyword",
                "epistemic_status": "keyword",
                "lifecycle":       "keyword",
                "is_personal":     "bool",
                "trust_score":      "integer",
                "knowledge_type":   "keyword",
                "language":        "keyword",
                "access_level":     "keyword",
                "needs_review":    "bool",
            }
            for field, schema in payload_index_fields.items():
                try:
                    requests.put(
                        f"{QDRANT_URL}/collections/{collection}/index",
                        json={"field_name": field, "field_schema": schema},
                        timeout=5
                    )
                except Exception as e:
                    logger.warning(f"[Qdrant] Payload 索引创建失败（可忽略）: {e}")
        return True
    except Exception:
        return False


def create_collection(collection: str) -> dict:
    """
    创建新的知识库集合。如果集合已存在则报错。

    返回:
        {"ok": true, "collection": "...", "dim": N}
    """
    if not _check_qdrant():
        return {"ok": False, "error": "Qdrant 未运行"}
    try:
        resp = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        existing = [c["name"] for c in resp.json()["result"]["collections"]]
        if collection in existing:
            return {"ok": False, "error": f"集合「{collection}」已存在"}
        requests.put(
            f"{QDRANT_URL}/collections/{collection}",
            json={"vectors": {"size": EMBED_DIM, "distance": "Cosine"}},
            timeout=10
        )
        # ── 创建 Payload Index ──
        payload_index_fields = {
            "content_type":     "keyword",
            "domain":          "keyword",
            "temporal_nature": "keyword",
            "epistemic_status": "keyword",
            "lifecycle":       "keyword",
            "is_personal":     "bool",
            "trust_score":      "integer",
            "knowledge_type":   "keyword",
            "language":        "keyword",
            "access_level":     "keyword",
            "needs_review":    "bool",
        }
        for field, schema in payload_index_fields.items():
            try:
                requests.put(
                    f"{QDRANT_URL}/collections/{collection}/index",
                    json={"field_name": field, "field_schema": schema},
                    timeout=5
                )
            except Exception as e:
                logger.warning(f"[Qdrant] 集合创建异常（可忽略）: {e}")
        return {"ok": True, "collection": collection, "dim": EMBED_DIM}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_collections() -> dict:
    """
    列出所有 Qdrant 知识库集合。

    返回:
        {"ok": true, "collections": [{"name": "...", "points": N, "dim": N}, ...]}
    """
    if not _check_qdrant():
        return {"ok": False, "error": "Qdrant 未运行"}
    try:
        resp = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        resp.raise_for_status()
        all_cols = resp.json()["result"]["collections"]
        result = []
        for c in all_cols:
            name = c["name"]
            try:
                info = requests.get(f"{QDRANT_URL}/collections/{name}", timeout=5).json()
                cfg = info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {})
                pts = info.get("result", {}).get("points_count", 0)
                result.append({
                    "name": name,
                    "points": pts,
                    "dim": cfg.get("size", "?") if cfg else "?",
                })
            except Exception:
                result.append({"name": name, "points": "?", "dim": "?"})
        return {"ok": True, "collections": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def clear_collection(collection: str = DEFAULT_COLLECTION) -> dict:
    """
    清空指定知识库集合（删除所有向量点，但保留集合结构）。

    参数:
        collection: 集合名称

    返回:
        {"ok": true, "deleted": N, "collection": "..."}
    """
    if not _check_qdrant():
        return {"ok": False, "error": "Qdrant 未运行"}
    try:
        # 获取当前点数
        info = requests.get(f"{QDRANT_URL}/collections/{collection}", timeout=5).json()
        points_count = info.get("result", {}).get("points_count", 0)

        if points_count == 0:
            return {"ok": True, "deleted": 0, "collection": collection, "message": "集合已为空"}

        # 分批删除所有点（scroll + delete）
        deleted_total = 0
        while True:
            scroll_resp = requests.post(
                f"{QDRANT_URL}/collections/{collection}/points/scroll",
                json={"limit": 1000, "with_payload": False, "with_vector": False},
                timeout=30
            )
            scroll_resp.raise_for_status()
            points = scroll_resp.json()["result"].get("points", [])
            if not points:
                break
            ids = [p["id"] for p in points]
            del_resp = requests.post(
                f"{QDRANT_URL}/collections/{collection}/points/delete",
                json={"points": ids},
                timeout=30
            )
            del_resp.raise_for_status()
            deleted_total += len(ids)

        return {"ok": True, "deleted": deleted_total, "collection": collection}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_collection(collection: str) -> dict:
    """
    完全删除一个知识库集合（包括集合结构）。

    参数:
        collection: 集合名称

    返回:
        {"ok": true, "collection": "..."}
    """
    if not _check_qdrant():
        return {"ok": False, "error": "Qdrant 未运行"}
    try:
        resp = requests.delete(f"{QDRANT_URL}/collections/{collection}", timeout=10)
        resp.raise_for_status()
        return {"ok": True, "collection": collection, "message": "集合已删除"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════
# 嵌入模型
# ═══════════════════════════════════════════

def get_embed_models() -> list[str]:
    """
    从 Ollama 获取本地可用的嵌入模型列表。

    返回:
        ["qwen3-embedding:4b", ...] 或空列表
    """
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("models", []):
            models.append(m["name"])
        return models
    except Exception:
        return []


# ═══════════════════════════════════════════
# 数据检查
# ═══════════════════════════════════════════

def has_any_data() -> bool:
    """
    检查任意 Qdrant 集合中是否有数据（用于判断是否锁定分类法/嵌入模型选择）。
    """
    try:
        col_list = list_collections()
        if not col_list.get("ok"):
            return False
        for c in col_list.get("collections", []):
            if c.get("points", 0) > 0:
                return True
        return False
    except Exception:
        return False
