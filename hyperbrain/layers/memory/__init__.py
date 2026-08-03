"""
记忆层 - 负责信息存储与检索

这是整个拟人脑系统的核心灵魂功能，模拟人脑的多层次记忆系统：

架构：
    感官输入 -> 瞬时记忆 -> 工作记忆 -> 长期记忆
                              -> 遗忘

模块：
    - memory_models: 数据模型和Pydantic模型
    - memory_utils: 工具函数（向量操作、遗忘曲线等）
    - sensory_memory: 瞬时记忆（容量10，TTL 30秒）
    - working_memory: 工作记忆（容量7±2组块）
    - long_term_memory: 长期记忆（SQLite + FAISS）
    - consolidation: 记忆巩固机制
    - retrieval: 记忆检索机制（语义/情境/情感/联想）
    - forgetting: 遗忘机制（艾宾浩斯曲线）
    - enhancement: 记忆增强机制
    - memory_manager: 统一管理器

使用示例：
    >>> from hyperbrain.layers.memory import MemoryManager
    >>> manager = MemoryManager()
    >>> 
    >>> # 处理输入
    >>> result = manager.process_input("今天学习了Python")
    >>> 
    >>> # 检索记忆
    >>> memories = manager.retrieve(query="Python")
    >>> 
    >>> # 存储重要信息
    >>> memory = manager.store("重要概念", importance=0.9)
    >>> 
    >>> # 手动巩固
    >>> manager.consolidate()
    >>> 
    >>> # 获取统计
    >>> stats = manager.get_stats()
"""

from hyperbrain.layers.memory.memory_models import (
    MemoryType,
    MemoryStatus,
    EmotionalValence,
    EmotionalTag,
    MemoryChunk,
    MemoryItem,
    SensoryInput,
    RetrievalResult,
    ConsolidationConfig,
    ForgettingConfig,
    EnhancementConfig,
)

from hyperbrain.layers.memory.memory_utils import (
    cosine_similarity,
    normalize_vector,
    compute_ebbinghaus_retention,
    compute_adaptive_decay_rate,
    compute_next_review_time,
    compute_memory_strength,
    generate_random_embedding,
)

from hyperbrain.layers.memory.sensory_memory import SensoryMemory
from hyperbrain.layers.memory.working_memory import WorkingMemory
from hyperbrain.layers.memory.long_term_memory import LongTermMemory
from hyperbrain.layers.memory.consolidation import MemoryConsolidator
from hyperbrain.layers.memory.retrieval import MemoryRetriever
from hyperbrain.layers.memory.forgetting import MemoryForgetting
from hyperbrain.layers.memory.enhancement import MemoryEnhancer
from hyperbrain.layers.memory.memory_manager import MemoryManager

__all__ = [
    # 数据模型
    "MemoryType",
    "MemoryStatus",
    "EmotionalValence",
    "EmotionalTag",
    "MemoryChunk",
    "MemoryItem",
    "SensoryInput",
    "RetrievalResult",
    "ConsolidationConfig",
    "ForgettingConfig",
    "EnhancementConfig",
    # 工具函数
    "cosine_similarity",
    "normalize_vector",
    "compute_ebbinghaus_retention",
    "compute_adaptive_decay_rate",
    "compute_next_review_time",
    "compute_memory_strength",
    "generate_random_embedding",
    # 记忆模块
    "SensoryMemory",
    "WorkingMemory",
    "LongTermMemory",
    "MemoryConsolidator",
    "MemoryRetriever",
    "MemoryForgetting",
    "MemoryEnhancer",
    "MemoryManager",
]
