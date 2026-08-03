"""
记忆系统数据模型

定义记忆系统中使用的所有数据结构和Pydantic模型
"""

import uuid
import time
import json
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field

import numpy as np
from pydantic import BaseModel, Field, ConfigDict


class MemoryType(str, Enum):
    """记忆类型枚举"""
    SENSORY = "sensory"           # 瞬时记忆
    WORKING = "working"           # 工作记忆
    DECLARATIVE = "declarative"   # 陈述性记忆（事实、概念）
    EPISODIC = "episodic"         # 情景记忆（事件）
    PROCEDURAL = "procedural"     # 程序性记忆（技能、习惯）
    EMOTIONAL = "emotional"       # 情感记忆
    SEMANTIC = "semantic"         # 语义记忆


class MemoryStatus(str, Enum):
    """记忆状态枚举"""
    ACTIVE = "active"             # 活跃
    CONSOLIDATING = "consolidating"  # 巩固中
    CONSOLIDATED = "consolidated"    # 已巩固
    DECAYING = "decaying"         # 衰减中
    FORGOTTEN = "forgotten"       # 已遗忘
    ARCHIVED = "archived"         # 已归档


class EmotionalValence(str, Enum):
    """情感效价"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class EmotionalTag:
    """情感标签"""
    valence: EmotionalValence = EmotionalValence.NEUTRAL
    intensity: float = 0.0          # 强度 0-1
    arousal: float = 0.0            # 唤醒度 0-1
    dominance: float = 0.5          # 支配度 0-1
    primary_emotion: str = ""       # 主要情感
    secondary_emotions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valence": self.valence.value if hasattr(self.valence, 'value') else self.valence,
            "intensity": self.intensity,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "primary_emotion": self.primary_emotion,
            "secondary_emotions": self.secondary_emotions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalTag":
        return cls(
            valence=EmotionalValence(data.get("valence", "neutral")),
            intensity=data.get("intensity", 0.0),
            arousal=data.get("arousal", 0.0),
            dominance=data.get("dominance", 0.5),
            primary_emotion=data.get("primary_emotion", ""),
            secondary_emotions=data.get("secondary_emotions", [])
        )


@dataclass
class MemoryChunk:
    """记忆组块 - 工作记忆的基本单元"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Any = None
    chunk_type: str = "generic"
    priority: float = 0.5           # 优先级 0-1
    size: int = 1                   # 组块大小（占用的工作记忆槽位数）
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    related_chunks: List[str] = field(default_factory=list)
    
    def merge_with(self, other: "MemoryChunk") -> "MemoryChunk":
        """与另一个组块合并"""
        merged_content = f"{self.content} | {other.content}"
        merged_priority = max(self.priority, other.priority)
        merged_size = self.size + other.size
        
        return MemoryChunk(
            content=merged_content,
            chunk_type=f"merged_{self.chunk_type}_{other.chunk_type}",
            priority=merged_priority,
            size=merged_size,
            related_chunks=list(set(self.related_chunks + other.related_chunks + [other.id]))
        )
    
    def split(self) -> List["MemoryChunk"]:
        """拆分组块"""
        if isinstance(self.content, str) and " | " in self.content:
            parts = self.content.split(" | ")
            return [
                MemoryChunk(
                    content=part,
                    chunk_type=self.chunk_type,
                    priority=self.priority,
                    size=1,
                    related_chunks=[self.id]
                )
                for part in parts
            ]
        return [self]


class MemoryItem(BaseModel):
    """记忆条目 - 长期记忆的基本单元"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: Union[str, Dict[str, Any], List[Any]] = Field(default="")
    memory_type: MemoryType = Field(default=MemoryType.DECLARATIVE)
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = Field(default=None)
    
    # 评分
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 访问统计
    access_count: int = Field(default=0)
    repetition_count: int = Field(default=0)
    
    # 向量表示
    embedding: Optional[List[float]] = Field(default=None)
    embedding_dim: int = Field(default=0)
    
    # 情感标签
    emotional_tag: Optional[Dict[str, Any]] = Field(default=None)
    
    # 关联记忆
    associations: List[str] = Field(default_factory=list)
    context_tags: List[str] = Field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 遗忘相关
    decay_factor: float = Field(default=1.0)
    next_review: Optional[datetime] = Field(default=None)
    forgetting_curve_stage: int = Field(default=0)
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.updated_at = datetime.now()
        self.familiarity = min(1.0, self.familiarity + 0.1)
    
    def get_embedding_array(self) -> Optional[np.ndarray]:
        """获取嵌入向量的numpy数组"""
        if self.embedding:
            return np.array(self.embedding, dtype=np.float32)
        return None
    
    def set_embedding(self, embedding: np.ndarray) -> None:
        """设置嵌入向量"""
        self.embedding = embedding.tolist()
        self.embedding_dim = len(self.embedding)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = self.model_dump()
        data["memory_type"] = self.memory_type.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["last_accessed"] = self.last_accessed.isoformat() if self.last_accessed else None
        data["next_review"] = self.next_review.isoformat() if self.next_review else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """从字典创建"""
        if "memory_type" in data:
            data["memory_type"] = MemoryType(data["memory_type"])
        if "status" in data:
            data["status"] = MemoryStatus(data["status"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "last_accessed" in data and isinstance(data["last_accessed"], str):
            data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        if "next_review" in data and isinstance(data["next_review"], str):
            data["next_review"] = datetime.fromisoformat(data["next_review"])
        return cls(**data)


class SensoryInput(BaseModel):
    """感知输入模型"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: Union[str, bytes, Dict[str, Any]] = Field(...)
    modality: str = Field(default="text")  # text, image, audio, video
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="")
    intensity: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """检索结果模型"""
    memory: MemoryItem
    similarity_score: float = Field(default=0.0)
    retrieval_method: str = Field(default="semantic")
    context_score: float = Field(default=0.0)
    emotional_match: float = Field(default=0.0)
    
    @property
    def combined_score(self) -> float:
        """综合评分"""
        return (
            self.similarity_score * 0.5 +
            self.context_score * 0.3 +
            self.emotional_match * 0.2
        ) * self.memory.importance


class ConsolidationConfig(BaseModel):
    """记忆巩固配置"""
    importance_threshold: float = Field(default=0.6)
    repetition_threshold: int = Field(default=3)
    consolidation_interval: float = Field(default=300.0)  # 5分钟
    sleep_mode_batch_size: int = Field(default=100)
    enable_sleep_consolidation: bool = Field(default=True)


class ForgettingConfig(BaseModel):
    """遗忘机制配置"""
    base_decay_rate: float = Field(default=0.05)
    importance_weight: float = Field(default=0.3)
    frequency_weight: float = Field(default=0.4)
    emotional_weight: float = Field(default=0.3)
    cleanup_interval: float = Field(default=3600.0)  # 1小时
    min_importance_to_keep: float = Field(default=0.1)


class EnhancementConfig(BaseModel):
    """记忆增强配置"""
    repetition_boost: float = Field(default=0.1)
    association_boost: float = Field(default=0.05)
    depth_processing_multiplier: float = Field(default=1.5)
    max_importance_cap: float = Field(default=0.99)
