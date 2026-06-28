"""
Citrinitas Watch Folder — 工具函数

路径定义 + 基础设施检查 + OCR 就绪检测。
此模块不导入 watcher.*，无循环依赖。
"""

import os
import time
import shutil
import fnmatch
import threading

import requests

from config.settings import (
    PROJECT_DIR,
    WATCH_V2_INBOX_DIR,
    WATCH_V2_STATE_FILE,
    WATCH_V2_WRITE_COMPLETE_CHECKS,
    WATCH_V2_WRITE_CHECK_INTERVAL,
    WATCH_V2_TEMP_PATTERNS,
)
from qconst import QDRANT_URL, OLLAMA_URL
from utils.activity_log import log_activity

# ═══════════════════════════════════════════
# 路径定义
# ═══════════════════════════════════════════

INBOX_DIR = os.path.join(PROJECT_DIR, WATCH_V2_INBOX_DIR)
STATE_FILE = os.path.join(PROJECT_DIR, WATCH_V2_STATE_FILE)
LOCK_FILE = os.path.join(os.path.dirname(STATE_FILE), ".watch.lock")

# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════


def _is_temp_file(filename: str) -> bool:
    """检查是否为临时文件（Office ~$/下载中/系统文件）。"""
    for pattern in WATCH_V2_TEMP_PATTERNS:
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return True
    return False


def _is_write_complete(filepath: str) -> bool:
    """轮询文件大小，连续 N 次不变 -> 认为写入完成。"""
    checks = WATCH_V2_WRITE_COMPLETE_CHECKS
    interval = WATCH_V2_WRITE_CHECK_INTERVAL
    last_size = -1
    stable_count = 0
    lock_retry_max = 3

    for _ in range(checks * 2):
        lock_retries = 0
        while lock_retries < lock_retry_max:
            try:
                current_size = os.path.getsize(filepath)
                break
            except PermissionError:
                lock_retries += 1
                if lock_retries >= lock_retry_max:
                    return False
                time.sleep(interval * 2)
            except OSError:
                return False

        if current_size == last_size:
            stable_count += 1
            if stable_count >= checks:
                return True
        else:
            stable_count = 0
            last_size = current_size
        time.sleep(interval)

    return False


def _check_infra() -> dict:
    """检查基础设施健康状态。"""
    result = {"qdrant": False, "ollama": False}
    try:
        resp = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        result["qdrant"] = resp.status_code == 200
    except requests.RequestException:
        pass
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        result["ollama"] = resp.status_code == 200
    except requests.RequestException:
        pass
    return result


def _check_disk_space(min_free_mb: int = 100) -> dict:
    """检查 INBOX_DIR 所在磁盘的可用空间。

    Returns:
        {"ok": bool, "free_mb": float, "total_mb": float}
    """
    try:
        usage = shutil.disk_usage(INBOX_DIR)
        free_mb = usage.free / (1024 * 1024)
        total_mb = usage.total / (1024 * 1024)
        return {"ok": free_mb >= min_free_mb, "free_mb": free_mb, "total_mb": total_mb}
    except OSError:
        return {"ok": True, "free_mb": -1, "total_mb": -1}


def _ensure_dir(path: str):
    """确保目录存在。"""
    os.makedirs(path, exist_ok=True)


# ── OCR 就绪状态 ──
_ocr_ready: bool | None = None
_ocr_lock = threading.Lock()


def _check_ocr_ready(force: bool = False) -> bool:
    """检查 OCR 引擎是否可用。加上线程锁和强制重检开关。"""
    global _ocr_ready
    with _ocr_lock:
        if _ocr_ready is not None and not force:
            return _ocr_ready
        try:
            from paddleocr import PaddleOCR
            _ocr_ready = True
        except ImportError:
            _ocr_ready = False
            log_activity(
                action="watch_ocr_unavailable",
                detail="PaddleOCR 未安装，图片文件将标记为需要审核",
            )
    return _ocr_ready
