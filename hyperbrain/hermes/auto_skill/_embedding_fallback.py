"""
轻量 embedding 兜底实现。

为什么不放 common：
- 单独成模块避免循环引用
- 这里实现纯 Python 的 n-gram 集合相似度 + md5 哈希向量，
  与 hyperbrain 项目里 memory_utils.generate_text_embedding 思路一致。
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import List


_WORD_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in _WORD_RE.findall(text)]


def _shingles(tokens: List[str], n: int = 2) -> List[str]:
    if len(tokens) < n:
        return tokens[:]
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def jaccard(a: str, b: str) -> float:
    """两个文本的 Jaccard 相似度（基于 2-gram 集合）。"""
    sa = set(_shingles(_tokenize(a)))
    sb = set(_shingles(_tokenize(b)))
    if not sa and not sb:
        return 0.0
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    return len(inter) / max(len(union), 1)


def hash_vector(text: str, dim: int = 64) -> List[float]:
    """
    稳定 64 维伪 embedding：把 2-gram 哈希到 dim 个 bin。
    与 hyperbrain 现有 memory_utils 的"md5 + n-gram 确定性向量"思路一致。
    """
    vec = [0.0] * dim
    if not text:
        return vec
    for sh in _shingles(_tokenize(text)):
        h = int(hashlib.md5(sh.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0
    # 归一化
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]
