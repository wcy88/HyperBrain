"""
记忆增强机制 (Memory Enhancement)

模拟人脑的记忆增强过程：
- 重复强化：多次访问的记忆增强
- 深度编码：重要信息的深度处理
- 关联增强：建立更多关联连接

增强机制帮助重要记忆更加稳固。
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryChunk, EnhancementConfig
)
from hyperbrain.layers.memory.memory_utils import cosine_similarity

logger = get_logger("memory.enhancement")


class MemoryEnhancer:
    """
    记忆增强器
    
    功能：
    - 重复强化
    - 深度编码
    - 关联增强
    - 重要性提升
    - 置信度调整
    
    Attributes:
        config: 增强配置
    """
    
    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self._enhancement_callbacks: List[Callable[[MemoryItem], None]] = []
        
        logger.info("MemoryEnhancer initialized")
    
    def reinforce_by_repetition(
        self,
        memory: MemoryItem,
        repetition_count: Optional[int] = None
    ) -> MemoryItem:
        """
        通过重复强化记忆
        
        每次访问都会增强记忆的稳定性
        
        Args:
            memory: 记忆条目
            repetition_count: 重复次数（默认使用memory.repetition_count）
            
        Returns:
            MemoryItem: 强化后的记忆
        """
        count = repetition_count or memory.repetition_count
        
        # 计算强化量（随重复次数递减）
        boost = self.config.repetition_boost / (1 + count * 0.1)
        
        # 提升重要性
        old_importance = memory.importance
        memory.importance = min(
            self.config.max_importance_cap,
            memory.importance + boost
        )
        
        # 提升置信度
        memory.confidence = min(1.0, memory.confidence + boost * 0.5)
        
        # 更新重复计数
        memory.repetition_count = count + 1
        memory.updated_at = datetime.now()
        
        logger.debug(
            f"Reinforced memory {memory.id} by repetition: "
            f"importance {old_importance:.2f} -> {memory.importance:.2f}"
        )
        
        self._trigger_callbacks(memory)
        return memory
    
    def deep_encode(
        self,
        memory: MemoryItem,
        processing_depth: int = 3
    ) -> MemoryItem:
        """
        深度编码记忆
        
        对重要信息进行更深层的处理，增强记忆效果
        
        Args:
            memory: 记忆条目
            processing_depth: 处理深度（1-5）
            
        Returns:
            MemoryItem: 深度编码后的记忆
        """
        depth = max(1, min(5, processing_depth))
        
        # 深度编码乘数
        multiplier = 1 + (depth - 1) * (self.config.depth_processing_multiplier - 1) / 4
        
        # 提升重要性
        old_importance = memory.importance
        memory.importance = min(
            self.config.max_importance_cap,
            memory.importance * multiplier
        )
        
        # 提升置信度
        memory.confidence = min(1.0, memory.confidence * (1 + depth * 0.05))
        
        # 标记为深度编码
        memory.metadata["deep_encoded"] = True
        memory.metadata["processing_depth"] = depth
        memory.metadata["encoded_at"] = datetime.now().isoformat()
        memory.updated_at = datetime.now()
        
        logger.debug(
            f"Deep encoded memory {memory.id}: "
            f"importance {old_importance:.2f} -> {memory.importance:.2f}, "
            f"depth={depth}"
        )
        
        self._trigger_callbacks(memory)
        return memory
    
    def enhance_associations(
        self,
        memory: MemoryItem,
        related_memories: List[MemoryItem],
        min_similarity: float = 0.3
    ) -> Tuple[MemoryItem, List[Tuple[str, float]]]:
        """
        增强记忆的关联
        
        发现与当前记忆相关的其他记忆，建立关联
        
        Args:
            memory: 当前记忆
            related_memories: 候选相关记忆
            min_similarity: 最小相似度
            
        Returns:
            Tuple[MemoryItem, List[Tuple[str, float]]]: (增强后的记忆, 新关联列表)
        """
        new_associations: List[Tuple[str, float]] = []
        
        # 基于内容相似度建立关联
        memory_content = str(memory.content).lower().split()
        memory_words = set(memory_content)
        
        for other in related_memories:
            if other.id == memory.id:
                continue
            
            # 检查是否已有关联
            if other.id in memory.associations:
                continue
            
            # 计算内容相似度
            other_content = str(other.content).lower().split()
            other_words = set(other_content)
            
            if not memory_words or not other_words:
                continue
            
            intersection = memory_words & other_words
            union = memory_words | other_words
            similarity = len(intersection) / len(union) if union else 0
            
            # 也考虑向量相似度
            if memory.embedding and other.embedding:
                vec_sim = cosine_similarity(
                    np.array(memory.embedding),
                    np.array(other.embedding)
                )
                similarity = max(similarity, vec_sim * 0.5)
            
            if similarity >= min_similarity:
                # 建立双向关联
                memory.associations.append(other.id)
                other.associations.append(memory.id)
                
                new_associations.append((other.id, similarity))
                
                logger.debug(
                    f"Enhanced association: {memory.id} <-> {other.id}, "
                    f"similarity={similarity:.2f}"
                )
        
        # 提升当前记忆的重要性（因为有更多关联）
        if new_associations:
            boost = len(new_associations) * self.config.association_boost
            memory.importance = min(
                self.config.max_importance_cap,
                memory.importance + boost
            )
            memory.updated_at = datetime.now()
        
        self._trigger_callbacks(memory)
        return memory, new_associations
    
    def strengthen_by_emotion(
        self,
        memory: MemoryItem,
        emotional_intensity: float
    ) -> MemoryItem:
        """
        通过情感强化记忆
        
        情感强烈的记忆更容易被记住
        
        Args:
            memory: 记忆条目
            emotional_intensity: 情感强度 [0, 1]
            
        Returns:
            MemoryItem: 强化后的记忆
        """
        if emotional_intensity <= 0:
            return memory
        
        # 情感强化
        emotion_boost = emotional_intensity * 0.15
        
        old_importance = memory.importance
        memory.importance = min(
            self.config.max_importance_cap,
            memory.importance + emotion_boost
        )
        
        # 更新情感标签
        if memory.emotional_tag:
            current_intensity = memory.emotional_tag.get("intensity", 0)
            memory.emotional_tag["intensity"] = max(current_intensity, emotional_intensity)
        else:
            memory.emotional_tag = {
                "valence": "neutral",
                "intensity": emotional_intensity,
                "primary_emotion": "unknown"
            }
        
        memory.updated_at = datetime.now()
        
        logger.debug(
            f"Strengthened memory {memory.id} by emotion: "
            f"importance {old_importance:.2f} -> {memory.importance:.2f}"
        )
        
        self._trigger_callbacks(memory)
        return memory
    
    def consolidate_embeddings(
        self,
        memories: List[MemoryItem]
    ) -> List[MemoryItem]:
        """
        巩固嵌入向量
        
        通过平均相关记忆的向量来增强表示
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[MemoryItem]: 更新后的记忆
        """
        memory_map = {m.id: m for m in memories}
        
        for memory in memories:
            if not memory.associations or not memory.embedding:
                continue
            
            # 收集关联记忆的向量
            related_vectors = []
            for assoc_id in memory.associations:
                if assoc_id in memory_map:
                    assoc_memory = memory_map[assoc_id]
                    if assoc_memory.embedding:
                        related_vectors.append(np.array(assoc_memory.embedding))
            
            if not related_vectors:
                continue
            
            # 计算平均向量
            current_vector = np.array(memory.embedding)
            avg_related = np.mean(related_vectors, axis=0)
            
            # 融合当前向量和关联向量
            enhanced_vector = current_vector * 0.7 + avg_related * 0.3
            
            # 归一化
            norm = np.linalg.norm(enhanced_vector)
            if norm > 0:
                enhanced_vector = enhanced_vector / norm
            
            memory.embedding = enhanced_vector.tolist()
            memory.embedding_dim = len(memory.embedding)
        
        logger.debug(f"Consolidated embeddings for {len(memories)} memories")
        return memories
    
    def boost_working_memory_chunk(
        self,
        chunk: MemoryChunk,
        boost_type: str = "attention"
    ) -> MemoryChunk:
        """
        增强工作记忆组块
        
        Args:
            chunk: 组块
            boost_type: 增强类型 (attention, repetition, emotion)
            
        Returns:
            MemoryChunk: 增强后的组块
        """
        if boost_type == "attention":
            chunk.priority = min(1.0, chunk.priority + 0.15)
        elif boost_type == "repetition":
            chunk.priority = min(1.0, chunk.priority + 0.1)
        elif boost_type == "emotion":
            chunk.priority = min(1.0, chunk.priority + 0.2)
        
        logger.debug(f"Boosted chunk {chunk.id} by {boost_type}: priority={chunk.priority:.2f}")
        return chunk
    
    def create_memory_hierarchy(
        self,
        memories: List[MemoryItem]
    ) -> Dict[str, List[str]]:
        """
        创建记忆层次结构
        
        根据关联关系组织记忆的层次
        
        Args:
            memories: 记忆列表
            
        Returns:
            Dict[str, List[str]]: 层次结构
        """
        memory_map = {m.id: m for m in memories}
        hierarchy: Dict[str, List[str]] = {}
        
        # 找到核心记忆（关联最多的）
        core_memories = sorted(
            memories,
            key=lambda m: len(m.associations),
            reverse=True
        )[:len(memories) // 5 + 1]  # 前20%
        
        for core in core_memories:
            children = []
            for assoc_id in core.associations:
                if assoc_id in memory_map:
                    children.append(assoc_id)
            hierarchy[core.id] = children
        
        return hierarchy
    
    def evaluate_memory_quality(self, memory: MemoryItem) -> Dict[str, float]:
        """
        评估记忆质量
        
        Args:
            memory: 记忆条目
            
        Returns:
            Dict[str, float]: 质量评分
        """
        scores = {
            "importance": memory.importance,
            "confidence": memory.confidence,
            "familiarity": memory.familiarity,
            "association_richness": min(1.0, len(memory.associations) / 10),
            "access_frequency": min(1.0, memory.access_count / 20),
            "recency": 1.0 / (1.0 + (datetime.now() - memory.created_at).total_seconds() / 86400)
        }
        
        # 综合质量分
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "repetition_boost": self.config.repetition_boost,
            "association_boost": self.config.association_boost,
            "depth_processing_multiplier": self.config.depth_processing_multiplier,
            "max_importance_cap": self.config.max_importance_cap,
            "callback_count": len(self._enhancement_callbacks)
        }
    
    def register_callback(self, callback: Callable[[MemoryItem], None]) -> None:
        """
        注册增强回调
        
        Args:
            callback: 回调函数
        """
        self._enhancement_callbacks.append(callback)
    
    def _trigger_callbacks(self, memory: MemoryItem) -> None:
        """触发增强回调"""
        for callback in self._enhancement_callbacks:
            try:
                callback(memory)
            except Exception as e:
                logger.error(f"Enhancement callback error: {e}")
