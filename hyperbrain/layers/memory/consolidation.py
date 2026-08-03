"""
记忆巩固机制 (Memory Consolidation)

模拟人脑的记忆巩固过程：
- 定期将工作记忆转化为长期记忆
- 基于重要性和重复次数的巩固策略
- 睡眠模式下的批量巩固

巩固是将短期/工作记忆转化为长期记忆的关键过程。
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryType, MemoryStatus, MemoryChunk, ConsolidationConfig
)
from hyperbrain.layers.memory.memory_utils import compute_memory_strength

logger = get_logger("memory.consolidation")


class MemoryConsolidator:
    """
    记忆巩固器
    
    功能：
    - 评估工作记忆中的组块是否值得巩固
    - 将工作记忆转化为长期记忆
    - 批量巩固（睡眠模式）
    - 关联建立
    
    Attributes:
        config: 巩固配置
        _consolidation_callbacks: 巩固完成回调
    """
    
    def __init__(self, config: Optional[ConsolidationConfig] = None):
        self.config = config or ConsolidationConfig()
        self._consolidation_callbacks: List[Callable[[MemoryItem], None]] = []
        self._lock = threading.RLock()
        
        logger.info(
            f"MemoryConsolidator initialized: "
            f"threshold={self.config.importance_threshold}"
        )
    
    def evaluate_consolidation_worthiness(
        self,
        chunk: MemoryChunk,
        access_count: int = 0,
        emotional_intensity: float = 0.0
    ) -> float:
        """
        评估组块是否值得巩固
        
        评分因素：
        - 优先级/重要性
        - 访问次数
        - 情感强度
        - 组块大小（小=容易巩固）
        
        Args:
            chunk: 组块
            access_count: 访问次数
            emotional_intensity: 情感强度
            
        Returns:
            float: 巩固评分 [0, 1]
        """
        # 基础评分来自优先级
        base_score = chunk.priority
        
        # 访问频率加成
        access_bonus = min(access_count / self.config.repetition_threshold, 1.0) * 0.3
        
        # 情感加成
        emotion_bonus = emotional_intensity * 0.2
        
        # 大小惩罚（大组块较难巩固）
        size_penalty = (chunk.size - 1) * 0.1
        
        score = base_score + access_bonus + emotion_bonus - size_penalty
        return max(0.0, min(1.0, score))
    
    def should_consolidate(
        self,
        chunk: MemoryChunk,
        access_count: int = 0,
        emotional_intensity: float = 0.0
    ) -> bool:
        """
        判断是否应该巩固
        
        Args:
            chunk: 组块
            access_count: 访问次数
            emotional_intensity: 情感强度
            
        Returns:
            bool: 是否应该巩固
        """
        score = self.evaluate_consolidation_worthiness(
            chunk, access_count, emotional_intensity
        )
        return score >= self.config.importance_threshold
    
    def consolidate_chunk(
        self,
        chunk: MemoryChunk,
        embedding: Optional[Any] = None,
        emotional_tag: Optional[Dict[str, Any]] = None,
        context_tags: Optional[List[str]] = None
    ) -> MemoryItem:
        """
        将工作记忆组块巩固为长期记忆
        
        Args:
            chunk: 工作记忆组块
            embedding: 向量嵌入
            emotional_tag: 情感标签
            context_tags: 上下文标签
            
        Returns:
            MemoryItem: 巩固后的长期记忆
        """
        # 确定记忆类型
        memory_type = self._infer_memory_type(chunk)
        
        # 计算巩固后的重要性
        consolidated_importance = min(1.0, chunk.priority * 1.1)
        
        # 创建长期记忆条目
        item = MemoryItem(
            content=str(chunk.content),
            memory_type=memory_type,
            status=MemoryStatus.CONSOLIDATED,
            importance=consolidated_importance,
            confidence=0.85,
            emotional_tag=emotional_tag,
            context_tags=context_tags or [],
            metadata={
                "source": chunk.source,
                "chunk_type": chunk.chunk_type,
                "consolidated_at": datetime.now().isoformat(),
                "original_chunk_id": chunk.id
            }
        )
        
        if embedding is not None:
            item.set_embedding(embedding)
        
        # 触发回调
        for callback in self._consolidation_callbacks:
            try:
                callback(item)
            except Exception as e:
                logger.error(f"Consolidation callback error: {e}")
        
        logger.info(
            f"Consolidated chunk {chunk.id} to long-term memory {item.id}, "
            f"type={memory_type.value}, importance={consolidated_importance:.2f}"
        )
        return item
    
    def consolidate_chunks(
        self,
        chunks: List[MemoryChunk],
        embeddings: Optional[Dict[str, Any]] = None,
        emotional_tags: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[MemoryItem]:
        """
        批量巩固多个组块
        
        Args:
            chunks: 组块列表
            embeddings: 组块ID到嵌入向量的映射
            emotional_tags: 组块ID到情感标签的映射
            
        Returns:
            List[MemoryItem]: 巩固后的记忆列表
        """
        consolidated = []
        embeddings = embeddings or {}
        emotional_tags = emotional_tags or {}
        
        for chunk in chunks:
            if self.should_consolidate(chunk):
                item = self.consolidate_chunk(
                    chunk=chunk,
                    embedding=embeddings.get(chunk.id),
                    emotional_tag=emotional_tags.get(chunk.id)
                )
                consolidated.append(item)
        
        # 建立关联
        self._establish_associations(consolidated)
        
        logger.info(f"Batch consolidated {len(consolidated)}/{len(chunks)} chunks")
        return consolidated
    
    def sleep_consolidation(
        self,
        chunks: List[MemoryChunk],
        existing_memories: Optional[List[MemoryItem]] = None
    ) -> List[MemoryItem]:
        """
        睡眠模式下的批量巩固
        
        特点：
        - 处理更大批量
        - 重新组织记忆结构
        - 加强重要关联
        - 弱化不重要信息
        
        Args:
            chunks: 待巩固的组块
            existing_memories: 现有长期记忆（用于关联）
            
        Returns:
            List[MemoryItem]: 巩固后的记忆
        """
        logger.info(f"Starting sleep consolidation with {len(chunks)} chunks")
        
        # 1. 筛选值得巩固的组块（降低阈值）
        sleep_threshold = self.config.importance_threshold * 0.7
        worthy_chunks = []
        
        for chunk in chunks:
            score = self.evaluate_consolidation_worthiness(chunk)
            if score >= sleep_threshold:
                worthy_chunks.append((chunk, score))
        
        # 2. 按重要性排序
        worthy_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # 3. 限制批量大小
        batch_size = self.config.sleep_mode_batch_size
        worthy_chunks = worthy_chunks[:batch_size]
        
        # 4. 巩固
        consolidated = []
        for chunk, score in worthy_chunks:
            item = self.consolidate_chunk(chunk)
            consolidated.append(item)
        
        # 5. 与现有记忆建立关联
        if existing_memories:
            self._cross_associate(consolidated, existing_memories)
        
        logger.info(f"Sleep consolidation complete: {len(consolidated)} memories")
        return consolidated
    
    def _infer_memory_type(self, chunk: MemoryChunk) -> MemoryType:
        """
        推断记忆类型
        
        Args:
            chunk: 组块
            
        Returns:
            MemoryType: 推断的记忆类型
        """
        chunk_type = chunk.chunk_type.lower()
        
        if "skill" in chunk_type or "procedure" in chunk_type or "habit" in chunk_type:
            return MemoryType.PROCEDURAL
        elif "event" in chunk_type or "episode" in chunk_type or "experience" in chunk_type:
            return MemoryType.EPISODIC
        elif "emotion" in chunk_type or "feeling" in chunk_type:
            return MemoryType.EMOTIONAL
        elif "fact" in chunk_type or "concept" in chunk_type or "knowledge" in chunk_type:
            return MemoryType.DECLARATIVE
        elif "semantic" in chunk_type or "meaning" in chunk_type:
            return MemoryType.SEMANTIC
        
        return MemoryType.DECLARATIVE
    
    def _establish_associations(self, items: List[MemoryItem]) -> None:
        """
        在新巩固的记忆之间建立关联
        
        Args:
            items: 新巩固的记忆列表
        """
        if len(items) < 2:
            return
        
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                # 简单的关联策略：同时巩固的记忆相互关联
                similarity = self._compute_content_similarity(
                    str(item1.content), str(item2.content)
                )
                if similarity > 0.3:
                    item1.associations.append(item2.id)
                    item2.associations.append(item1.id)
    
    def _cross_associate(
        self,
        new_items: List[MemoryItem],
        existing_items: List[MemoryItem]
    ) -> None:
        """
        在新记忆和现有记忆之间建立关联
        
        Args:
            new_items: 新记忆
            existing_items: 现有记忆
        """
        for new_item in new_items:
            for existing in existing_items:
                similarity = self._compute_content_similarity(
                    str(new_item.content), str(existing.content)
                )
                if similarity > 0.5:
                    new_item.associations.append(existing.id)
                    existing.associations.append(new_item.id)
    
    def _compute_content_similarity(self, content1: str, content2: str) -> float:
        """
        计算内容相似度（简单实现）
        
        Args:
            content1: 内容1
            content2: 内容2
            
        Returns:
            float: 相似度 [0, 1]
        """
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def register_callback(self, callback: Callable[[MemoryItem], None]) -> None:
        """
        注册巩固完成回调
        
        Args:
            callback: 回调函数
        """
        self._consolidation_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "importance_threshold": self.config.importance_threshold,
            "repetition_threshold": self.config.repetition_threshold,
            "sleep_mode_enabled": self.config.enable_sleep_consolidation,
            "batch_size": self.config.sleep_mode_batch_size,
            "callback_count": len(self._consolidation_callbacks)
        }
