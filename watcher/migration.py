"""
Citrinitas Watch Folder — 旧版迁移（v1 6 目录 → 统一收件箱 + JSONL）。

仅依赖 state.py 的 _append_state + utils.py 的 _ensure_dir。
"""

import os
import json
import shutil
from datetime import datetime, timezone

from config.settings import PROJECT_DIR
from watcher.utils import INBOX_DIR, _ensure_dir
from watcher.state import _append_state
from utils.activity_log import log_activity


def _migrate_from_v1():
    """从旧版守望（v1，6 目录模型）迁移到统一收件箱（统一收件箱 + JSONL）。

    幂等：已迁移则跳过（通过标记文件检测）。
    """
    marker = os.path.join(PROJECT_DIR, "data", ".watch_migrated")
    if os.path.isfile(marker):
        return

    old_dirs = {
        "watch":              os.path.join(PROJECT_DIR, "data", "watch"),
        "watch_staging":      os.path.join(PROJECT_DIR, "data", "watch_staging"),
        "watch_dead_letter":  os.path.join(PROJECT_DIR, "data", "watch_dead_letter"),
        "watch_processed":    os.path.join(PROJECT_DIR, "data", "watch_processed"),
    }

    if not any(os.path.isdir(d) for d in old_dirs.values()):
        _ensure_dir(os.path.dirname(marker))
        with open(marker, "w", encoding="utf-8") as f:
            f.write(datetime.now(timezone.utc).isoformat())
        return

    migrated_files = 0
    migrated_dlq = 0

    # 1. data/watch/ → inbox/
    if os.path.isdir(old_dirs["watch"]):
        for filename in os.listdir(old_dirs["watch"]):
            if filename == ".gitkeep":
                continue
            src = os.path.join(old_dirs["watch"], filename)
            if os.path.isfile(src):
                dst = os.path.join(INBOX_DIR, filename)
                shutil.move(src, dst)
                migrated_files += 1

    # 2. data/watch_staging/ → inbox/
    if os.path.isdir(old_dirs["watch_staging"]):
        for filename in os.listdir(old_dirs["watch_staging"]):
            if filename == ".gitkeep":
                continue
            src = os.path.join(old_dirs["watch_staging"], filename)
            if os.path.isfile(src):
                dst = os.path.join(INBOX_DIR, filename)
                shutil.move(src, dst)
                migrated_files += 1

    # 3. data/watch_dead_letter/ → inbox/ + state 条目
    if os.path.isdir(old_dirs["watch_dead_letter"]):
        for filename in sorted(os.listdir(old_dirs["watch_dead_letter"])):
            if filename == ".gitkeep" or filename.endswith(".meta.json"):
                continue
            src = os.path.join(old_dirs["watch_dead_letter"], filename)
            if not os.path.isfile(src):
                continue

            meta_path = src + ".meta.json"
            error = "从旧版 DLQ 迁移"
            step = "unknown"
            ts = datetime.now(timezone.utc).isoformat()

            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    error = meta.get("error", error)
                    step = meta.get("failed_step", step)
                    ts = meta.get("failed_at", ts)
                except (OSError, json.JSONDecodeError):
                    pass

            dst = os.path.join(INBOX_DIR, filename)
            try:
                shutil.move(src, dst)
            except OSError:
                continue

            _append_state({
                "file": filename,
                "state": "failed",
                "step": step,
                "error": error,
                "failure_type": "migrated_from_v1",
            })
            migrated_dlq += 1

            if os.path.isfile(meta_path):
                try:
                    os.remove(meta_path)
                except OSError:
                    pass

    # 4. 清理旧目录
    for dir_key in ["watch", "watch_staging", "watch_dead_letter", "watch_processed"]:
        old_dir = old_dirs[dir_key]
        if not os.path.isdir(old_dir):
            continue
        try:
            for item in os.listdir(old_dir):
                item_path = os.path.join(old_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
            os.rmdir(old_dir)
        except OSError:
            pass

    # 5. 写入迁移标记
    _ensure_dir(os.path.dirname(marker))
    with open(marker, "w", encoding="utf-8") as f:
        f.write(datetime.now(timezone.utc).isoformat())

    if migrated_files > 0 or migrated_dlq > 0:
        log_activity(
            action="watch_migration",
            detail=f"从 v1 迁移: {migrated_files} 文件, {migrated_dlq} DLQ 条目",
        )
        print(f"[watcher] 旧版迁移完成: {migrated_files} 文件, {migrated_dlq} DLQ")
