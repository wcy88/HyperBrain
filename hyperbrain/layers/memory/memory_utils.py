"""
记忆系统工具函数

提供向量操作、时间计算、相似度计算等通用工具
"""

import math
import time
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime, timedelta


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        a: 向量a
        b: 向量b
        
    Returns:
        float: 余弦相似度 [-1, 1]
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    计算欧几里得距离
    
    Args:
        a: 向量a
        b: 向量b
        
    Returns:
        float: 欧几里得距离
    """
    return float(np.linalg.norm(a - b))


def normalize_vector(v: np.ndarray) -> np.ndarray:
    """
    归一化向量
    
    Args:
        v: 输入向量
        
    Returns:
        np.ndarray: 归一化后的向量
    """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def compute_ebbinghaus_retention(
    time_elapsed_hours: float,
    initial_strength: float = 1.0,
    base_decay: float = 1.25
) -> float:
    """
    计算基于艾宾浩斯遗忘曲线的记忆保持率
    
    R = e^(-t/S)
    其中 t 是时间，S 是记忆强度
    
    Args:
        time_elapsed_hours: 经过的时间（小时）
        initial_strength: 初始记忆强度
        base_decay: 基础衰减系数
        
    Returns:
        float: 记忆保持率 [0, 1]
    """
    if time_elapsed_hours <= 0:
        return initial_strength
    
    # 艾宾浩斯遗忘曲线公式
    retention = math.exp(-time_elapsed_hours / (initial_strength * base_decay))
    return max(0.0, min(1.0, retention))


def compute_adaptive_decay_rate(
    importance: float,
    access_frequency: float,
    emotional_intensity: float,
    base_rate: float = 0.05,
    importance_weight: float = 0.3,
    frequency_weight: float = 0.4,
    emotional_weight: float = 0.3
) -> float:
    """
    计算自适应遗忘速率
    
    遗忘速率 = 基础速率 * (1 - 重要性影响 - 频率影响 - 情感影响)
    
    Args:
        importance: 重要性 [0, 1]
        access_frequency: 访问频率 [0, 1]
        emotional_intensity: 情感强度 [0, 1]
        base_rate: 基础遗忘速率
        importance_weight: 重要性权重
        frequency_weight: 频率权重
        emotional_weight: 情感权重
        
    Returns:
        float: 自适应遗忘速率
    """
    # 计算保护因子（越高越不容易遗忘）
    protection = (
        importance * importance_weight +
        access_frequency * frequency_weight +
        emotional_intensity * emotional_weight
    )
    
    # 保护因子降低遗忘速率
    decay_rate = base_rate * (1 - protection)
    return max(0.001, decay_rate)  # 最小遗忘速率


def compute_next_review_time(
    repetition_count: int,
    base_interval: timedelta = timedelta(hours=1),
    ease_factor: float = 2.5
) -> datetime:
    """
    计算下次复习时间（基于SM-2间隔重复算法）
    
    Args:
        repetition_count: 重复次数
        base_interval: 基础间隔
        ease_factor: 容易度因子
        
    Returns:
        datetime: 下次复习时间
    """
    if repetition_count == 0:
        return datetime.now() + base_interval
    
    # 间隔重复算法
    interval_multiplier = ease_factor ** repetition_count
    next_interval = base_interval * interval_multiplier
    
    # 最大间隔限制为1年
    max_interval = timedelta(days=365)
    next_interval = min(next_interval, max_interval)
    
    return datetime.now() + next_interval


def compute_memory_strength(
    repetition_count: int,
    importance: float,
    emotional_intensity: float,
    time_since_last_access: float  # 小时
) -> float:
    """
    计算记忆强度
    
    Args:
        repetition_count: 重复次数
        importance: 重要性
        emotional_intensity: 情感强度
        time_since_last_access: 距上次访问时间（小时）
        
    Returns:
        float: 记忆强度 [0, 1]
    """
    # 基础强度
    base_strength = 0.3 + (repetition_count * 0.1) + (importance * 0.3) + (emotional_intensity * 0.2)
    
    # 时间衰减
    time_decay = math.exp(-time_since_last_access / 24)  # 以天为单位衰减
    
    strength = base_strength * time_decay
    return min(1.0, max(0.0, strength))


def softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
    """
    Softmax函数，用于注意力分配
    
    Args:
        scores: 分数列表
        temperature: 温度参数（越高越平滑）
        
    Returns:
        List[float]: 概率分布
    """
    if not scores:
        return []
    
    exp_scores = [math.exp(s / temperature) for s in scores]
    sum_exp = sum(exp_scores)
    
    if sum_exp == 0:
        return [1.0 / len(scores)] * len(scores)
    
    return [es / sum_exp for es in exp_scores]


def compute_attention_weights(
    items: List,
    relevance_scores: List[float],
    recency_scores: List[float],
    importance_scores: List[float],
    relevance_weight: float = 0.4,
    recency_weight: float = 0.3,
    importance_weight: float = 0.3
) -> List[float]:
    """
    计算注意力权重
    
    Args:
        items: 项目列表
        relevance_scores: 相关性分数
        recency_scores: 新近性分数
        importance_scores: 重要性分数
        relevance_weight: 相关性权重
        recency_weight: 新近性权重
        importance_weight: 重要性权重
        
    Returns:
        List[float]: 注意力权重
    """
    if not items or len(items) != len(relevance_scores):
        return []
    
    combined_scores = []
    for rel, rec, imp in zip(relevance_scores, recency_scores, importance_scores):
        score = (rel * relevance_weight + rec * recency_weight + imp * importance_weight)
        combined_scores.append(score)
    
    return softmax(combined_scores)


def time_since(dt: Optional[datetime]) -> float:
    """
    计算距离某个时间点的秒数
    
    Args:
        dt: 时间点
        
    Returns:
        float: 秒数
    """
    if dt is None:
        return float('inf')
    return (datetime.now() - dt).total_seconds()


def time_since_hours(dt: Optional[datetime]) -> float:
    """
    计算距离某个时间点的小时数
    
    Args:
        dt: 时间点
        
    Returns:
        float: 小时数
    """
    return time_since(dt) / 3600.0


def format_duration(seconds: float) -> str:
    """
    格式化持续时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}小时"
    else:
        return f"{seconds/86400:.1f}天"


def generate_random_embedding(dim: int = 1536) -> np.ndarray:
    """
    生成随机归一化向量（用于测试）

    .. deprecated::
        此函数生成完全随机的向量，相似度搜索无法返回语义相关的结果。
        请使用 ``generate_text_embedding`` 替代。

    Args:
        dim: 维度

    Returns:
        np.ndarray: 随机归一化向量
    """
    import warnings
    warnings.warn(
        "generate_random_embedding 已弃用，请使用 generate_text_embedding "
        "以获得语义一致的向量表示。",
        DeprecationWarning,
        stacklevel=2
    )
    vec = np.random.randn(dim).astype(np.float32)
    return normalize_vector(vec)


def _hash_token(token: str, dim: int) -> int:
    """
    使用稳定哈希将 token 映射到向量维度索引

    使用 Python 内置 hash() 在进程内一致（PYTHONHASHSEED 固定时跨进程也一致）。
    同时叠加一个 murmur 风格的混合来缓解 Python hash 字符串的随机化。

    Args:
        token: 输入 token
        dim: 向量维度

    Returns:
        int: 维度索引 [0, dim)
    """
    # 使用 md5 获得稳定的字节序列，然后转为整数
    import hashlib
    digest = hashlib.md5(token.encode("utf-8")).digest()
    # 取前 8 字节作为无符号整数
    value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return value % dim


def _tokenize_for_embedding(text: str) -> List[str]:
    """
    将文本拆分为用于嵌入的特征 token 列表

    特征包括：
    - 完整词（Unicode 友好）
    - 字符 bigram / trigram
    - 归一化（lower-cased）

    Args:
        text: 输入文本

    Returns:
        List[str]: token 列表
    """
    if not text:
        return []

    text_lower = text.lower().strip()
    if not text_lower:
        return []

    tokens: List[str] = []

    # 1. 完整词（支持中文按字切分 + 英文按空格切分）
    # 中文按字符切分，英文按非字母数字切分
    import re
    # 中文字符范围
    chinese_pattern = re.compile(r"[\u4e00-\u9fff]+")
    english_pattern = re.compile(r"[a-z0-9]+")

    # 中文：每两个连续字作为一个 token（bigram），这样 "今天" 和 "今日" 会有部分重叠
    chinese_segments = chinese_pattern.findall(text_lower)
    for seg in chinese_segments:
        # 单字 token
        for ch in seg:
            tokens.append(f"c1:{ch}")
        # 双字 token
        for i in range(len(seg) - 1):
            tokens.append(f"c2:{seg[i:i+2]}")
        # 三字 token
        for i in range(len(seg) - 2):
            tokens.append(f"c3:{seg[i:i+3]}")

    # 英文：按词 + 字符 n-gram
    english_words = english_pattern.findall(text_lower)
    for word in english_words:
        tokens.append(f"w:{word}")
        # 字符 n-gram
        if len(word) >= 2:
            for i in range(len(word) - 1):
                tokens.append(f"e2:{word[i:i+2]}")
        if len(word) >= 3:
            for i in range(len(word) - 2):
                tokens.append(f"e3:{word[i:i+3]}")

    return tokens


def generate_text_embedding(text: str, dim: int = 1536) -> np.ndarray:
    """
    基于文本特征生成确定性嵌入向量

    特性：
    - **确定性**：相同文本总是返回完全相同的向量
    - **语义性**：相似文本返回高相似度的向量（余弦相似度）
    - **多语言支持**：中英文混合文本都能处理
    - **L2 归一化**：可直接使用余弦相似度

    实现原理：
    - 提取文本中的词、字符 n-gram 等特征作为 token
    - 使用稳定哈希（md5）将每个 token 映射到向量维度
    - 使用 ``TF`` (term frequency) 风格累加（带 ``log`` 缩放以缓解高频词主导）
    - L2 归一化

    Args:
        text: 输入文本
        dim: 向量维度，默认 1536

    Returns:
        np.ndarray: 归一化的嵌入向量

    Examples:
        >>> v1 = generate_text_embedding("今天天气真好")
        >>> v2 = generate_text_embedding("今天天气不错")
        >>> cosine_similarity(v1, v2) > 0.5
        True
        >>> v3 = generate_text_embedding("Python 编程")
        >>> cosine_similarity(v1, v3) < 0.3
        True
    """
    vec = np.zeros(dim, dtype=np.float32)
    tokens = _tokenize_for_embedding(text)

    if not tokens:
        # 空文本返回零向量（归一化后为零）
        return vec

    # 统计 token 频率
    from collections import Counter
    token_counts = Counter(tokens)

    # 累加到向量（使用 log 缩放的 TF）
    for token, count in token_counts.items():
        idx = _hash_token(token, dim)
        # 使用对数缩放：1 + log(count)
        weight = 1.0 + np.log1p(count)
        vec[idx] += weight

    # 归一化
    return normalize_vector(vec)
