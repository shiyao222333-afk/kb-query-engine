"""
Citrinitas · 熔知 — 预热脚本

预先加载 PaddleOCR / Ollama 嵌入模型，避免首次调用慢。
用法：
  python warmup.py           # 预热所有模型
  python warmup.py --ocr     # 只预热 PaddleOCR
  python warmup.py --embed   # 只预热 Ollama 嵌入模型
"""
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

def warmup_paddleocr(verbose=True) -> dict:
    """预热 PaddleOCR 模型"""
    result = {"ok": False, "paddle": False, "structure": False, "time": 0.0}
    t0 = time.time()

    if verbose:
        logger.info("[WARMUP] 正在预热 PaddleOCR 模型...")

    # 1. 预热 PaddleOCR 主力引擎
    try:
        from text_pipeline import _get_paddle
        _get_paddle()
        result["paddle"] = True
        if verbose:
            logger.info("[WARMUP] ✅ PaddleOCR 模型加载成功")
    except Exception as e:
        result["paddle_error"] = str(e)
        if verbose:
            logger.warning(f"[WARMUP] ⚠️ PaddleOCR 模型加载失败: {e}")

    # 2. 预热 PPStructureV3 结构化引擎
    try:
        from text_pipeline import _get_structure_engine
        _get_structure_engine()
        result["structure"] = True
        if verbose:
            logger.info("[WARMUP] ✅ PPStructureV3 模型加载成功")
    except Exception as e:
        result["structure_error"] = str(e)
        if verbose:
            logger.warning(f"[WARMUP] ⚠️ PPStructureV3 模型加载失败: {e}")

    result["time"] = round(time.time() - t0, 2)
    result["ok"] = result["paddle"] or result["structure"]
    if verbose:
        logger.info(f"[WARMUP] PaddleOCR 预热完成，耗时 {result['time']} 秒")
    return result


def warmup_ollama_embed(verbose=True) -> dict:
    """预热 Ollama 嵌入模型（调用一次嵌入 API，让 Ollama 加载模型到内存）"""
    result = {"ok": False, "time": 0.0}
    t0 = time.time()

    if verbose:
        logger.info("[WARMUP] 正在预热 Ollama 嵌入模型...")

    try:
        from qconst import OLLAMA_URL, EMBED_MODEL
        import requests
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "warmup"},
            timeout=60
        )
        resp.raise_for_status()
        result["ok"] = True
        if verbose:
            logger.info(f"[WARMUP] ✅ Ollama 嵌入模型预热成功 ({EMBED_MODEL})")
    except Exception as e:
        result["error"] = str(e)
        if verbose:
            logger.warning(f"[WARMUP] ⚠️ Ollama 嵌入模型预热失败: {e}")

    result["time"] = round(time.time() - t0, 2)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Citrinitas 模型预热脚本")
    parser.add_argument("--ocr", action="store_true", help="只预热 PaddleOCR")
    parser.add_argument("--embed", action="store_true", help="只预热 Ollama 嵌入模型")
    args = parser.parse_args()

    t0 = time.time()
    logger.info("═══════════════════════════════════════")
    logger.info("  Citrinitas · 熔知 — 模型预热")
    logger.info("═══════════════════════════════════════")

    if not args.ocr and not args.embed:
        # 默认：预热所有模型
        r1 = warmup_paddleocr()
        r2 = warmup_ollama_embed()
        total_time = round(time.time() - t0, 2)
        logger.info(f"═══════════════════════════════════════")
        logger.info(f"  预热完成，总耗时 {total_time} 秒")
        logger.info(f"  PaddleOCR: {'✅' if r1['ok'] else '❌'} ({r1['time']}s)")
        logger.info(f"  Ollama:    {'✅' if r2['ok'] else '❌'} ({r2['time']}s)")
        logger.info(f"═══════════════════════════════════════")
    elif args.ocr:
        warmup_paddleocr()
    elif args.embed:
        warmup_ollama_embed()
