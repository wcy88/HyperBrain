"""
情感记忆模块

存储与情感相关的经历和体验，支持情感标记的记忆检索、强化和衰减。
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import MemoryItem, MemoryType, EmotionalTag

logger = get_logger("emotional.memory")


class EmotionalMemoryEntry(BaseModel):
    """情感记忆条目"""
    id: str = Field(default_factory=lambda: str(int(time.time() * 1000)))
    event_description: str = Field(default="")
    emotional_state: Dict[str, float] = Field(default_factory=dict)
    primary_emotion: str = Field(default="neutral")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: float = Field(default_factory=time.time)
    associated_memory_ids: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    reinforcement_count: int = Field(default=0)
    decay_factor: float = Field(default=1.0)
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    arousal: float = Field(default=0.0, ge=0.0, le=1.0)


class EmotionalMemoryConfig(BaseModel):
    """情感记忆配置"""
    max_entries: int = Field(default=1000, ge=100)
    decay_rate: float = Field(default=0.001, ge=0.0, le=1.0)
    reinforcement_boost: float = Field(default=0.1, ge=0.0, le=1.0)
    retrieval_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    enable_decay: bool = Field(default=True)
    enable_reinforcement: bool = Field(default=True)
    association_strength: float = Field(default=0.5, ge=0.0, le=1.0)


@dataclass
class RetrievalQuery:
    """情感记忆检索查询"""
    emotion_type: Optional[str] = None
    valence_range: Optional[Tuple[float, float]] = None
    arousal_range: Optional[Tuple[float, float]] = None
    time_range: Optional[Tuple[float, float]] = None
    intensity_threshold: float = 0.0
    context_filter: Optional[Dict[str, Any]] = None
    limit: int = 10


class EmotionalMemory:
    """
    情感记忆系统

    功能：
    1. 存储与情感相关的经历和体验
    2. 情感标记的记忆检索
    3. 情感记忆的强化和衰减
    4. 情感记忆与陈述性记忆的关联
    """

    def __init__(self, config: Optional[EmotionalMemoryConfig] = None):
        self.config = config or EmotionalMemoryConfig()
        self._entries: Dict[str, EmotionalMemoryEntry] = {}
        self._emotion_index: Dict[str, List[str]] = {}
        self._valence_index: List[Tuple[str, float]] = []
        self._access_history: List[Tuple[str, float]] = []
        logger.info("EmotionalMemory initialized")

    def store(
        self,
        event_description: str,
        emotional_state: Dict[str, float],
        associated_memory_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        valence: float = 0.0,
        arousal: float = 0.0
    ) -> EmotionalMemoryEntry:
        """
        存储情感记忆

        Args:
            event_description: 事件描述
            emotional_state: 情感状态字典
            associated_memory_ids: 关联的记忆ID
            context: 上下文信息
            valence: 效价
            arousal: 唤醒度

        Returns:
            EmotionalMemoryEntry: 存储的情感记忆
        """
        primary_emotion = self._determine_primary_emotion(emotional_state)
        intensity = max(emotional_state.values()) if emotional_state else 0.0

        entry = EmotionalMemoryEntry(
            event_description=event_description,
            emotional_state=emotional_state,
            primary_emotion=primary_emotion,
            intensity=intensity,
            associated_memory_ids=associated_memory_ids or [],
            context=context or {},
            valence=valence,
            arousal=arousal
        )

        self._entries[entry.id] = entry
        self._update_index(entry)

        # 检查容量限制
        if len(self._entries) > self.config.max_entries:
            self._evict_oldest()

        logger.debug(f"Stored emotional memory: {entry.id}, emotion={primary_emotion}")
        return entry

    def retrieve_by_emotion(
        self,
        emotion_type: str,
        limit: int = 10,
        min_intensity: float = 0.0
    ) -> List[EmotionalMemoryEntry]:
        """
        按情感类型检索记忆

        Args:
            emotion_type: 情感类型
            limit: 返回数量限制
            min_intensity: 最小强度阈值

        Returns:
            List[EmotionalMemoryEntry]: 匹配的情感记忆
        """
        ids = self._emotion_index.get(emotion_type, [])
        results = []

        for entry_id in ids:
            entry = self._entries.get(entry_id)
            if entry and entry.intensity >= min_intensity:
                entry.decay_factor = self._calculate_decay(entry)
                if entry.decay_factor >= self.config.retrieval_threshold:
                    results.append(entry)
                    self._access_history.append((entry_id, time.time()))

        results.sort(key=lambda x: x.intensity * x.decay_factor, reverse=True)
        return results[:limit]

    def retrieve_by_valence(
        self,
        valence_range: Tuple[float, float],
        limit: int = 10
    ) -> List[EmotionalMemoryEntry]:
        """
        按效价范围检索记忆

        Args:
            valence_range: 效价范围 (min, max)
            limit: 返回数量限制

        Returns:
            List[EmotionalMemoryEntry]: 匹配的情感记忆
        """
        results = []
        min_val, max_val = valence_range

        for entry in self._entries.values():
            if min_val <= entry.valence <= max_val:
                entry.decay_factor = self._calculate_decay(entry)
                if entry.decay_factor >= self.config.retrieval_threshold:
                    results.append(entry)

        results.sort(key=lambda x: abs(x.valence), reverse=True)
        return results[:limit]

    def retrieve_similar(
        self,
        emotional_state: Dict[str, float],
        limit: int = 10
    ) -> List[Tuple[EmotionalMemoryEntry, float]]:
        """
        检索相似情感状态的记忆

        Args:
            emotional_state: 目标情感状态
            limit: 返回数量限制

        Returns:
            List[Tuple[EmotionalMemoryEntry, float]]: (记忆, 相似度)
        """
        results = []

        for entry in self._entries.values():
            similarity = self._calculate_similarity(
                emotional_state, entry.emotional_state
            )
            entry.decay_factor = self._calculate_decay(entry)
            effective_similarity = similarity * entry.decay_factor

            if effective_similarity >= self.config.retrieval_threshold:
                results.append((entry, effective_similarity))
                self._access_history.append((entry.id, time.time()))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def retrieve_by_query(
        self,
        query: RetrievalQuery
    ) -> List[EmotionalMemoryEntry]:
        """
        使用复杂查询检索记忆

        Args:
            query: 检索查询

        Returns:
            List[EmotionalMemoryEntry]: 匹配的情感记忆
        """
        candidates = list(self._entries.values())

        if query.emotion_type:
            candidates = [e for e in candidates
                         if e.primary_emotion == query.emotion_type]

        if query.valence_range:
            min_v, max_v = query.valence_range
            candidates = [e for e in candidates if min_v <= e.valence <= max_v]

        if query.arousal_range:
            min_a, max_a = query.arousal_range
            candidates = [e for e in candidates if min_a <= e.arousal <= max_a]

        if query.time_range:
            min_t, max_t = query.time_range
            candidates = [e for e in candidates if min_t <= e.timestamp <= max_t]

        candidates = [e for e in candidates
                     if e.intensity >= query.intensity_threshold]

        if query.context_filter:
            for key, value in query.context_filter.items():
                candidates = [
                    e for e in candidates
                    if e.context.get(key) == value
                ]

        for entry in candidates:
            entry.decay_factor = self._calculate_decay(entry)

        candidates = [
            e for e in candidates
            if e.decay_factor >= self.config.retrieval_threshold
        ]

        candidates.sort(key=lambda x: x.intensity * x.decay_factor, reverse=True)
        return candidates[:query.limit]

    def reinforce(self, entry_id: str) -> Optional[EmotionalMemoryEntry]:
        """
        强化情感记忆

        Args:
            entry_id: 记忆条目ID

        Returns:
            Optional[EmotionalMemoryEntry]: 强化后的记忆
        """
        if not self.config.enable_reinforcement:
            return self._entries.get(entry_id)

        entry = self._entries.get(entry_id)
        if not entry:
            return None

        entry.reinforcement_count += 1
        entry.intensity = min(1.0, entry.intensity + self.config.reinforcement_boost)
        entry.decay_factor = min(1.0, entry.decay_factor + self.config.reinforcement_boost * 0.5)

        logger.debug(f"Reinforced emotional memory: {entry_id}, count={entry.reinforcement_count}")
        return entry

    def decay_all(self) -> int:
        """
        对所有记忆应用衰减

        Returns:
            int: 被移除的记忆数量
        """
        if not self.config.enable_decay:
            return 0

        to_remove = []
        for entry_id, entry in self._entries.items():
            entry.decay_factor = self._calculate_decay(entry)
            if entry.decay_factor < 0.01:
                to_remove.append(entry_id)

        for entry_id in to_remove:
            del self._entries[entry_id]
            self._remove_from_index(entry_id)

        logger.debug(f"Decayed {len(to_remove)} emotional memories")
        return len(to_remove)

    def associate_with_declarative_memory(
        self,
        emotional_entry_id: str,
        memory_item_id: str
    ) -> bool:
        """
        将情感记忆与陈述性记忆关联

        Args:
            emotional_entry_id: 情感记忆ID
            memory_item_id: 陈述性记忆ID

        Returns:
            bool: 是否成功
        """
        entry = self._entries.get(emotional_entry_id)
        if not entry:
            return False

        if memory_item_id not in entry.associated_memory_ids:
            entry.associated_memory_ids.append(memory_item_id)
            logger.debug(f"Associated emotional memory {emotional_entry_id} with memory {memory_item_id}")

        return True

    def get_associated_memories(
        self,
        emotional_entry_id: str
    ) -> List[str]:
        """
        获取关联的陈述性记忆ID

        Args:
            emotional_entry_id: 情感记忆ID

        Returns:
            List[str]: 关联的记忆ID列表
        """
        entry = self._entries.get(emotional_entry_id)
        return entry.associated_memory_ids.copy() if entry else []

    def get_emotional_summary(
        self,
        time_window: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        获取情感记忆摘要

        Args:
            time_window: 时间窗口（秒），None表示全部

        Returns:
            Dict[str, Any]: 情感摘要
        """
        now = time.time()
        entries = list(self._entries.values())

        if time_window:
            entries = [e for e in entries if now - e.timestamp <= time_window]

        if not entries:
            return {"count": 0}

        emotion_counts = {}
        total_valence = 0.0
        total_arousal = 0.0
        total_intensity = 0.0

        for entry in entries:
            emotion_counts[entry.primary_emotion] = emotion_counts.get(
                entry.primary_emotion, 0
            ) + 1
            total_valence += entry.valence
            total_arousal += entry.arousal
            total_intensity += entry.intensity

        return {
            "count": len(entries),
            "emotion_distribution": emotion_counts,
            "average_valence": total_valence / len(entries),
            "average_arousal": total_arousal / len(entries),
            "average_intensity": total_intensity / len(entries),
            "dominant_emotion": max(emotion_counts.items(), key=lambda x: x[1])[0]
        }

    def _determine_primary_emotion(self, emotional_state: Dict[str, float]) -> str:
        """确定主导情感"""
        if not emotional_state:
            return "neutral"
        return max(emotional_state.items(), key=lambda x: x[1])[0]

    def _calculate_decay(self, entry: EmotionalMemoryEntry) -> float:
        """计算衰减因子"""
        if not self.config.enable_decay:
            return entry.decay_factor

        age = time.time() - entry.timestamp
        time_decay = math.exp(-self.config.decay_rate * age)
        reinforcement_bonus = 1.0 + entry.reinforcement_count * 0.1

        return min(1.0, time_decay * reinforcement_bonus)

    def _calculate_similarity(
        self,
        state1: Dict[str, float],
        state2: Dict[str, float]
    ) -> float:
        """计算两个情感状态的相似度"""
        all_emotions = set(state1.keys()) | set(state2.keys())
        if not all_emotions:
            return 0.0

        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0

        for emotion in all_emotions:
            v1 = state1.get(emotion, 0.0)
            v2 = state2.get(emotion, 0.0)
            dot_product += v1 * v2
            norm1 += v1 ** 2
            norm2 += v2 ** 2

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))

    def _update_index(self, entry: EmotionalMemoryEntry) -> None:
        """更新索引"""
        if entry.primary_emotion not in self._emotion_index:
            self._emotion_index[entry.primary_emotion] = []
        self._emotion_index[entry.primary_emotion].append(entry.id)
        self._valence_index.append((entry.id, entry.valence))

    def _remove_from_index(self, entry_id: str) -> None:
        """从索引中移除"""
        for emotion, ids in self._emotion_index.items():
            if entry_id in ids:
                ids.remove(entry_id)

        self._valence_index = [
            (eid, val) for eid, val in self._valence_index
            if eid != entry_id
        ]

    def _evict_oldest(self) -> None:
        """淘汰最旧的记忆"""
        if not self._entries:
            return

        oldest_id = min(self._entries.keys(), key=lambda x: self._entries[x].timestamp)
        del self._entries[oldest_id]
        self._remove_from_index(oldest_id)
        logger.debug(f"Evicted oldest emotional memory: {oldest_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        emotion_distribution = {}
        for entry in self._entries.values():
            emotion_distribution[entry.primary_emotion] = emotion_distribution.get(
                entry.primary_emotion, 0
            ) + 1

        return {
            "total_entries": len(self._entries),
            "emotion_distribution": emotion_distribution,
            "index_size": sum(len(v) for v in self._emotion_index.values()),
            "access_history_length": len(self._access_history),
            "config": self.config.model_dump(),
        }
