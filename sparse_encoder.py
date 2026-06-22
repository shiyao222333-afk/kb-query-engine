"""
Sparse Encoder Module — 稀疏向量生成器

为 Qdrant 混合查询生成 BM25 稀疏向量。
配置：sparse_vectors = {"bm25": {"modifier": "idf"}}
摄入时只需提供词频（TF），Qdrant 自动计算 IDF。
"""

import json
import os
import jieba
import re

# 全局词汇表：token → index
_SPARSE_VOCAB = {}
_VOCAB_PATH = os.path.join(os.path.dirname(__file__), "sparse_vocab.json")
_MAX_VOCAB_SIZE = 50000  # 最大词汇表大小


def _load_vocab():
    """加载词汇表"""
    global _SPARSE_VOCAB
    if os.path.exists(_VOCAB_PATH):
        try:
            with open(_VOCAB_PATH, "r", encoding="utf-8") as f:
                _SPARSE_VOCAB = json.load(f)
        except Exception:
            _SPARSE_VOCAB = {}


def _save_vocab():
    """保存词汇表"""
    with open(_VOCAB_PATH, "w", encoding="utf-8") as f:
        json.dump(_SPARSE_VOCAB, f, ensure_ascii=False, indent=2)


def tokenize(text: str) -> list:
    """中英文分词"""
    # 英文：按空格和标点分割
    en_tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    # 中文：使用 jieba 分词
    try:
        zh_tokens = list(jieba.cut_for_search(text))
        zh_tokens = [t.strip() for t in zh_tokens if t.strip()]
    except Exception:
        zh_tokens = []
    return en_tokens + zh_tokens


def encode_sparse(text: str, update_vocab: bool = True) -> tuple:
    """
    将文本编码为稀疏向量（用于摄入）。
    
    参数:
        text: 输入文本
        update_vocab: 是否更新全局词汇表
        
    返回:
        (indices, values) 元组
        - indices: 词 ID 列表（int）
        - values: 词频（TF）列表（float）
    """
    if not _SPARSE_VOCAB:
        _load_vocab()
    
    tokens = tokenize(text)
    if not tokens:
        return [], []
    
    # 统计词频
    tf = {}
    for token in tokens:
        if token not in tf:
            tf[token] = 0
        tf[token] += 1
    
    indices = []
    values = []
    
    for token, count in tf.items():
        # 获取或分配 token index
        if token not in _SPARSE_VOCAB:
            if len(_SPARSE_VOCAB) >= _MAX_VOCAB_SIZE:
                continue  # 跳过，词汇表已满
            _SPARSE_VOCAB[token] = len(_SPARSE_VOCAB)
        
        indices.append(_SPARSE_VOCAB[token])
        values.append(float(count))  # TF 作为值
    
    if update_vocab:
        _save_vocab()
    
    return indices, values


def encode_sparse_query(text: str) -> tuple:
    """
    将查询文本编码为稀疏向量（用于查询）。
    
    注意：查询时不能更新词汇表，只能使用已有的 token。
    """
    if not _SPARSE_VOCAB:
        _load_vocab()
    
    tokens = tokenize(text)
    if not tokens:
        return [], []
    
    # 统计词频
    tf = {}
    for token in tokens:
        if token not in _SPARSE_VOCAB:
            continue  # 跳过词汇表中没有的词
        if token not in tf:
            tf[token] = 0
        tf[token] += 1
    
    indices = []
    values = []
    
    for token, count in tf.items():
        indices.append(_SPARSE_VOCAB[token])
        values.append(float(count))
    
    return indices, values


def get_vocab_size() -> int:
    """获取词汇表大小"""
    if not _SPARSE_VOCAB:
        _load_vocab()
    return len(_SPARSE_VOCAB)


# 初始化时加载词汇表
_load_vocab()
