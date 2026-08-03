"""
记忆检索机制 (Memory Retrieval)

模拟人脑的记忆检索过程：
- 基于语义的相似性检索（FAISS）
- 基于情境的检索
- 基于情感的检索
- 联想检索：通过一个记忆联想到相关记忆

检索是记忆系统的核心功能，支持多种检索策略。
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryType, RetrievalResult, EmotionalTag
)
from hyperbrain.layers.memory.memory_utils import (
    cosine_similarity,
    normalize_vector,
    time_since_hours
)

logger = get_logger("memory.retrieval")


class MemoryRetriever:
    """
    记忆检索器
    
    功能：
    - 语义检索（向量相似度）
    - 情境检索（标签匹配）
    - 情感检索
    - 联想检索
    - 混合检索（综合多种策略）
    
    Attributes:
        long_term_memory: 长期记忆存储引用
        retrieval_history: 检索历史
    """
    
    def __init__(self, long_term_memory=None):
        self.long_term_memory = long_term_memory
        self.retrieval_history: List[Dict[str, Any]] = []
        self._retrieval_callbacks: List[Callable[[RetrievalResult], None]] = []
    
    def semantic_search(
        self,
        query_embedding: np.ndarray,
        memories: List[MemoryItem],
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> List[RetrievalResult]:
        """
        基于语义的相似性检索
        
        Args:
            query_embedding: 查询向量
            memories: 记忆列表
            top_k: 返回数量
            min_similarity: 最小相似度
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        query_norm = normalize_vector(query_embedding)
        results = []
        
        for memory in memories:
            memory_embedding = memory.get_embedding_array()
            if memory_embedding is None:
                continue
            
            similarity = cosine_similarity(query_norm, memory_embedding)
            
            if similarity >= min_similarity:
                result = RetrievalResult(
                    memory=memory,
                    similarity_score=float(similarity),
                    retrieval_method="semantic"
                )
                results.append(result)
        
        # 按相似度排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.debug(f"Semantic search: {len(results)} results")
        return results[:top_k]
    
    def context_search(
        self,
        context_tags: List[str],
        memories: List[MemoryItem],
        top_k: int = 10,
        min_match_ratio: float = 0.3
    ) -> List[RetrievalResult]:
        """
        基于情境的检索
        
        根据上下文标签匹配度检索相关记忆
        
        Args:
            context_tags: 上下文标签
            memories: 记忆列表
            top_k: 返回数量
            min_match_ratio: 最小匹配比例
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        if not context_tags:
            return []
        
        results = []
        
        for memory in memories:
            if not memory.context_tags:
                continue
            
            # 计算标签匹配度
            matching_tags = set(memory.context_tags) & set(context_tags)
            match_ratio = len(matching_tags) / len(context_tags) if context_tags else 0
            
            if match_ratio >= min_match_ratio:
                result = RetrievalResult(
                    memory=memory,
                    similarity_score=match_ratio,
                    retrieval_method="context",
                    context_score=match_ratio
                )
                results.append(result)
        
        # 按匹配度排序
        results.sort(key=lambda x: x.context_score, reverse=True)
        
        logger.debug(f"Context search: {len(results)} results")
        return results[:top_k]
    
    def emotional_search(
        self,
        target_emotion: str,
        memories: List[MemoryItem],
        top_k: int = 10,
        min_intensity: float = 0.2
    ) -> List[RetrievalResult]:
        """
        基于情感的检索
        
        检索与特定情感相关的记忆
        
        Args:
            target_emotion: 目标情感
            memories: 记忆列表
            top_k: 返回数量
            min_intensity: 最小情感强度
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        results = []
        
        for memory in memories:
            if not memory.emotional_tag:
                continue
            
            # 检查主要情感
            primary_emotion = memory.emotional_tag.get("primary_emotion", "")
            intensity = memory.emotional_tag.get("intensity", 0)
            
            if primary_emotion == target_emotion and intensity >= min_intensity:
                result = RetrievalResult(
                    memory=memory,
                    similarity_score=intensity,
                    retrieval_method="emotional",
                    emotional_match=intensity
                )
                results.append(result)
            else:
                # 检查次要情感
                secondary = memory.emotional_tag.get("secondary_emotions", [])
                if target_emotion in secondary:
                    result = RetrievalResult(
                        memory=memory,
                        similarity_score=intensity * 0.5,
                        retrieval_method="emotional",
                        emotional_match=intensity * 0.5
                    )
                    results.append(result)
        
        # 按情感匹配度排序
        results.sort(key=lambda x: x.emotional_match, reverse=True)
        
        logger.debug(f"Emotional search: {len(results)} results")
        return results[:top_k]
    
    def associative_search(
        self,
        seed_memory: MemoryItem,
        memories: List[MemoryItem],
        max_hops: int = 2,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        联想检索
        
        通过一个记忆联想到相关记忆，支持多跳联想
        
        Args:
            seed_memory: 种子记忆
            memories: 记忆池
            max_hops: 最大联想跳数
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        if not seed_memory.associations:
            return []
        
        # 构建记忆ID到对象的映射
        memory_map = {m.id: m for m in memories}
        
        # BFS进行联想检索
        visited = {seed_memory.id}
        current_level = list(seed_memory.associations)  # 从种子记忆的关联开始
        all_results: Dict[str, Tuple[MemoryItem, float, int]] = {}
        
        for hop in range(1, max_hops + 1):
            next_level = []
            
            for memory_id in current_level:
                if memory_id in visited:
                    continue
                    
                if memory_id not in memory_map:
                    visited.add(memory_id)
                    continue
                
                memory = memory_map[memory_id]
                visited.add(memory_id)
                
                # 计算关联强度（随跳数衰减）
                strength = 1.0 / hop
                
                # 如果已经找到，保留更强的路径
                if memory_id in all_results:
                    if strength > all_results[memory_id][1]:
                        all_results[memory_id] = (memory, strength, hop)
                else:
                    all_results[memory_id] = (memory, strength, hop)
                
                # 继续探索下一层
                for assoc_id in memory.associations:
                    if assoc_id not in visited:
                        next_level.append(assoc_id)
            
            current_level = next_level
            if not current_level:
                break
        
        # 构建结果
        results = []
        for memory, strength, hop in all_results.values():
            result = RetrievalResult(
                memory=memory,
                similarity_score=strength,
                retrieval_method=f"associative_{hop}hop"
            )
            results.append(result)
        
        # 按关联强度排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.debug(f"Associative search: {len(results)} results")
        return results[:top_k]
    
    def hybrid_search(
        self,
        query_embedding: Optional[np.ndarray] = None,
        context_tags: Optional[List[str]] = None,
        target_emotion: Optional[str] = None,
        seed_memory: Optional[MemoryItem] = None,
        memories: Optional[List[MemoryItem]] = None,
        top_k: int = 10,
        semantic_weight: float = 0.4,
        context_weight: float = 0.3,
        emotional_weight: float = 0.2,
        associative_weight: float = 0.1
    ) -> List[RetrievalResult]:
        """
        混合检索（综合多种策略）
        
        结合语义、情境、情感和联想检索的结果
        
        Args:
            query_embedding: 查询向量（语义检索）
            context_tags: 上下文标签（情境检索）
            target_emotion: 目标情感（情感检索）
            seed_memory: 种子记忆（联想检索）
            memories: 记忆池
            top_k: 返回数量
            semantic_weight: 语义权重
            context_weight: 情境权重
            emotional_weight: 情感权重
            associative_weight: 联想权重
            
        Returns:
            List[RetrievalResult]: 综合排序后的结果
        """
        if memories is None and self.long_term_memory is not None:
            memories = self.long_term_memory.get_all_memories()
        
        if not memories:
            return []
        
        # 收集各策略的结果
        all_results: Dict[str, RetrievalResult] = {}
        
        # 语义检索
        if query_embedding is not None:
            semantic_results = self.semantic_search(
                query_embedding, memories, top_k=len(memories)
            )
            for result in semantic_results:
                result.similarity_score *= semantic_weight
                if result.memory.id in all_results:
                    all_results[result.memory.id].similarity_score += result.similarity_score
                else:
                    all_results[result.memory.id] = result
        
        # 情境检索
        if context_tags:
            context_results = self.context_search(
                context_tags, memories, top_k=len(memories)
            )
            for result in context_results:
                result.context_score *= context_weight
                if result.memory.id in all_results:
                    all_results[result.memory.id].context_score += result.context_score
                    all_results[result.memory.id].similarity_score += result.context_score
                else:
                    all_results[result.memory.id] = result
        
        # 情感检索
        if target_emotion:
            emotional_results = self.emotional_search(
                target_emotion, memories, top_k=len(memories)
            )
            for result in emotional_results:
                result.emotional_match *= emotional_weight
                if result.memory.id in all_results:
                    all_results[result.memory.id].emotional_match += result.emotional_match
                    all_results[result.memory.id].similarity_score += result.emotional_match
                else:
                    all_results[result.memory.id] = result
        
        # 联想检索
        if seed_memory:
            associative_results = self.associative_search(
                seed_memory, memories, top_k=len(memories)
            )
            for result in associative_results:
                result.similarity_score *= associative_weight
                if result.memory.id in all_results:
                    all_results[result.memory.id].similarity_score += result.similarity_score
                else:
                    all_results[result.memory.id] = result
        
        # 如果没有指定任何检索条件，返回所有记忆按重要性排序
        if not all_results:
            for memory in memories:
                result = RetrievalResult(
                    memory=memory,
                    similarity_score=memory.importance * 0.5,
                    retrieval_method="default"
                )
                all_results[memory.id] = result
        
        # 转换为列表并排序
        results = list(all_results.values())
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # 记录检索历史
        self._record_retrieval("hybrid", len(results))
        
        logger.debug(f"Hybrid search: {len(results)} results")
        return results[:top_k]
    
    def temporal_search(
        self,
        memories: List[MemoryItem],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_k: int = 20
    ) -> List[RetrievalResult]:
        """
        基于时间的检索
        
        检索特定时间段内的记忆
        
        Args:
            memories: 记忆列表
            start_time: 开始时间
            end_time: 结束时间
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        results = []
        
        for memory in memories:
            memory_time = memory.created_at
            
            if start_time and memory_time < start_time:
                continue
            if end_time and memory_time > end_time:
                continue
            
            # 计算时间相关性（越近越相关）
            hours_ago = time_since_hours(memory_time)
            recency_score = 1.0 / (1.0 + hours_ago / 24)
            
            result = RetrievalResult(
                memory=memory,
                similarity_score=recency_score,
                retrieval_method="temporal",
                context_score=recency_score
            )
            results.append(result)
        
        # 按时间排序（最近的在前）
        results.sort(key=lambda x: x.memory.created_at, reverse=True)
        
        return results[:top_k]
    
    def importance_search(
        self,
        memories: List[MemoryItem],
        min_importance: float = 0.5,
        top_k: int = 20
    ) -> List[RetrievalResult]:
        """
        基于重要性的检索
        
        检索高重要性的记忆
        
        Args:
            memories: 记忆列表
            min_importance: 最小重要性
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        results = []
        
        for memory in memories:
            if memory.importance >= min_importance:
                result = RetrievalResult(
                    memory=memory,
                    similarity_score=memory.importance,
                    retrieval_method="importance"
                )
                results.append(result)
        
        # 按重要性排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def search_with_feedback(
        self,
        query_embedding: np.ndarray,
        memories: List[MemoryItem],
        positive_examples: Optional[List[str]] = None,
        negative_examples: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        带反馈的检索
        
        根据正负例调整检索结果
        
        Args:
            query_embedding: 查询向量
            memories: 记忆列表
            positive_examples: 正例ID列表
            negative_examples: 负例ID列表
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 调整后的结果
        """
        # 基础语义检索
        results = self.semantic_search(query_embedding, memories, top_k=len(memories))
        
        positive_examples = positive_examples or []
        negative_examples = negative_examples or []
        
        # 调整分数
        for result in results:
            if result.memory.id in positive_examples:
                result.similarity_score *= 1.2
            elif result.memory.id in negative_examples:
                result.similarity_score *= 0.8
        
        # 重新排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def _record_retrieval(self, method: str, result_count: int) -> None:
        """记录检索历史"""
        self.retrieval_history.append({
            "method": method,
            "timestamp": datetime.now(),
            "result_count": result_count
        })
        
        # 限制历史长度
        if len(self.retrieval_history) > 1000:
            self.retrieval_history = self.retrieval_history[-500:]
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        获取检索统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.retrieval_history:
            return {"total_retrievals": 0}
        
        method_counts = {}
        for record in self.retrieval_history:
            method = record["method"]
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_retrievals": len(self.retrieval_history),
            "method_distribution": method_counts,
            "avg_results": sum(r["result_count"] for r in self.retrieval_history) / len(self.retrieval_history)
        }
    
    def register_callback(self, callback: Callable[[RetrievalResult], None]) -> None:
        """
        注册检索回调
        
        Args:
            callback: 回调函数
        """
        self._retrieval_callbacks.append(callback)
