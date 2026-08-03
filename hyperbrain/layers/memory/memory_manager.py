"""
记忆管理器 (Memory Manager)

统一管理所有记忆类型，协调各模块工作，提供统一的API接口。

这是记忆系统的中央控制器，负责：
- 管理瞬时记忆、工作记忆、长期记忆
- 协调巩固、检索、遗忘、增强机制
- 提供统一的数据流
- 维护记忆生命周期
"""

import time
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

import numpy as np

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryChunk, MemoryType, MemoryStatus,
    SensoryInput, RetrievalResult,
    ConsolidationConfig, ForgettingConfig, EnhancementConfig
)
from hyperbrain.layers.memory.memory_utils import generate_text_embedding, generate_random_embedding

from hyperbrain.layers.memory.sensory_memory import SensoryMemory
from hyperbrain.layers.memory.working_memory import WorkingMemory
from hyperbrain.layers.memory.long_term_memory import LongTermMemory
from hyperbrain.layers.memory.consolidation import MemoryConsolidator
from hyperbrain.layers.memory.retrieval import MemoryRetriever
from hyperbrain.layers.memory.forgetting import MemoryForgetting
from hyperbrain.layers.memory.enhancement import MemoryEnhancer

logger = get_logger("memory.manager")


class MemoryManager:
    """
    记忆管理器 - 记忆系统的中央控制器
    
    功能：
    1. 统一管理所有记忆类型
    2. 协调各模块工作
    3. 提供统一的API接口
    4. 维护记忆生命周期
    5. 自动巩固和清理
    
    数据流：
    感官输入 -> 瞬时记忆 -> 工作记忆 -> 长期记忆
                              -> 遗忘
    
    Attributes:
        sensory_memory: 瞬时记忆
        working_memory: 工作记忆
        long_term_memory: 长期记忆
        consolidator: 巩固器
        retriever: 检索器
        forgetter: 遗忘器
        enhancer: 增强器
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        vector_dim: int = 1536,
        enable_faiss: bool = False,
        sensory_capacity: int = 10,
        sensory_ttl: float = 30.0,
        working_capacity: int = 7,
        auto_consolidate: bool = True,
        auto_cleanup: bool = True
    ):
        self.config = get_config().memory
        self.vector_dim = vector_dim
        
        # 初始化各模块
        logger.info("Initializing MemoryManager...")
        
        # 瞬时记忆
        self.sensory_memory = SensoryMemory(
            capacity=sensory_capacity,
            ttl_seconds=sensory_ttl
        )
        
        # 工作记忆
        self.working_memory = WorkingMemory(
            capacity=working_capacity,
            importance_threshold=0.6
        )
        
        # 长期记忆
        self.long_term_memory = LongTermMemory(
            db_path=db_path,
            vector_dim=vector_dim,
            enable_faiss=enable_faiss
        )
        
        # 功能模块
        self.consolidator = MemoryConsolidator(ConsolidationConfig())
        self.retriever = MemoryRetriever(self.long_term_memory)
        self.forgetter = MemoryForgetting(ForgettingConfig())
        self.enhancer = MemoryEnhancer(EnhancementConfig())
        
        # 自动任务
        self.auto_consolidate = auto_consolidate
        self.auto_cleanup = auto_cleanup
        self._consolidation_interval = 300.0  # 5分钟
        self._cleanup_interval = 3600.0  # 1小时
        self._last_consolidation = time.time()
        self._last_cleanup = time.time()
        
        # 注册回调
        self._setup_callbacks()
        
        # 线程锁
        self._lock = threading.RLock()
        
        logger.info("MemoryManager initialized successfully")
    
    def _setup_callbacks(self) -> None:
        """设置模块间的回调"""
        # 工作记忆 -> 长期记忆的转移回调
        self.working_memory.register_transfer_callback(
            self._on_working_memory_transfer
        )
        
        # 巩固完成回调
        self.consolidator.register_callback(
            self._on_consolidation_complete
        )
        
        # 遗忘回调
        self.forgetter.register_callback(
            self._on_memory_forgotten
        )
        
        # 增强回调
        self.enhancer.register_callback(
            self._on_memory_enhanced
        )
    
    # ========== 输入处理 ==========
    
    def process_input(
        self,
        content: Any,
        modality: str = "text",
        source: str = "",
        intensity: float = 1.0,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理新的感知输入
        
        完整的数据流：
        1. 存入瞬时记忆
        2. 评估是否进入工作记忆
        3. 高重要性直接存入长期记忆
        
        Args:
            content: 输入内容
            modality: 模态类型
            source: 来源
            intensity: 强度
            embedding: 向量嵌入
            metadata: 元数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        with self._lock:
            # 1. 存入瞬时记忆
            sensory_input = self.sensory_memory.add(
                content=content,
                modality=modality,
                source=source,
                intensity=intensity,
                metadata=metadata
            )
            
            # 2. 评估重要性
            importance = self._evaluate_importance(content, intensity, metadata)
            
            # 3. 添加到工作记忆
            chunk = self.working_memory.add(
                content=content,
                chunk_type=modality,
                priority=importance,
                source=source
            )
            
            # 4. 高重要性直接存入长期记忆
            memory_item = None
            if importance >= 0.7:
                memory_item = self._store_to_long_term(
                    content=content,
                    importance=importance,
                    embedding=embedding,
                    metadata=metadata
                )
            
            # 5. 检查自动任务
            self._check_auto_tasks()
            
            return {
                "sensory_input_id": sensory_input.id,
                "chunk_id": chunk.id,
                "memory_id": memory_item.id if memory_item else None,
                "importance": importance,
                "direct_storage": importance >= 0.7
            }
    
    def _evaluate_importance(
        self,
        content: Any,
        intensity: float,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """评估输入的重要性"""
        base_importance = 0.3
        
        # 强度加成
        intensity_bonus = intensity * 0.3
        
        # 内容长度加成（简短=可能重要）
        content_bonus = 0.0
        if isinstance(content, str):
            if len(content) < 50:
                content_bonus = 0.15
            elif len(content) > 500:
                content_bonus = 0.05
        
        # 元数据加成
        metadata_bonus = 0.0
        if metadata:
            if metadata.get("urgent"):
                metadata_bonus += 0.25
            if metadata.get("emotional"):
                metadata_bonus += 0.15
        
        importance = base_importance + intensity_bonus + content_bonus + metadata_bonus
        return min(1.0, importance)
    
    # ========== 存储接口 ==========
    
    def store(
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.DECLARATIVE,
        importance: float = 0.5,
        embedding: Optional[np.ndarray] = None,
        emotional_tag: Optional[Dict[str, Any]] = None,
        context_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryItem:
        """
        直接存储到长期记忆
        
        Args:
            content: 内容
            memory_type: 记忆类型
            importance: 重要性
            embedding: 向量嵌入
            emotional_tag: 情感标签
            context_tags: 上下文标签
            metadata: 元数据
            
        Returns:
            MemoryItem: 存储的记忆
        """
        with self._lock:
            # 生成嵌入（如果没有提供）
            if embedding is None:
                embedding = self._make_embedding_from_content(content)

            item = self.long_term_memory.store(
                content=content,
                memory_type=memory_type,
                importance=importance,
                embedding=embedding,
                emotional_tag=emotional_tag,
                context_tags=context_tags,
                metadata=metadata
            )

            logger.info(f"Stored memory: {item.id}, type={memory_type.value}")
            return item

    def _make_embedding_from_content(self, content: Any) -> np.ndarray:
        """
        从内容生成确定性嵌入向量

        优先从 content 字典中提取 ``input/output`` 字段拼接成文本，
        否则将 content 转为字符串。对于空内容使用零向量。
        """
        text = self._extract_text_for_embedding(content)
        if not text:
            return generate_text_embedding("__empty__", self.vector_dim)
        return generate_text_embedding(text, self.vector_dim)

    @staticmethod
    def _extract_text_for_embedding(content: Any) -> str:
        """从内容中提取用于嵌入的文本"""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            parts: List[str] = []
            for key in ("input", "output", "content", "text", "query", "message"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value)
            if not parts:
                # 回退：序列化整个字典
                import json
                try:
                    return json.dumps(content, ensure_ascii=False, sort_keys=True)
                except Exception:
                    return str(content)
            return " ".join(parts)
        if isinstance(content, (list, tuple)):
            return " ".join(str(x) for x in content if x)
        return str(content)

    def _store_to_long_term(
        self,
        content: Any,
        importance: float,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryItem:
        """内部方法：存储到长期记忆"""
        if embedding is None:
            embedding = self._make_embedding_from_content(content)

        return self.long_term_memory.store(
            content=content,
            importance=importance,
            embedding=embedding,
            metadata=metadata
        )
    
    # ========== 检索接口 ==========
    
    def retrieve(
        self,
        query: Optional[str] = None,
        query_embedding: Optional[np.ndarray] = None,
        context_tags: Optional[List[str]] = None,
        target_emotion: Optional[str] = None,
        top_k: int = 10,
        search_working: bool = True,
        search_long_term: bool = True
    ) -> List[RetrievalResult]:
        """
        统一检索接口
        
        同时检索工作记忆和长期记忆
        
        Args:
            query: 文本查询
            query_embedding: 向量查询
            context_tags: 上下文标签
            target_emotion: 目标情感
            top_k: 返回数量
            search_working: 是否搜索工作记忆
            search_long_term: 是否搜索长期记忆
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        all_results: Dict[str, RetrievalResult] = {}

        # 如果提供了 query 但没有 query_embedding，则生成文本嵌入
        if query is not None and query_embedding is None:
            query_embedding = generate_text_embedding(query, self.vector_dim)

        with self._lock:
            # 1. 检索工作记忆
            if search_working:
                working_results = self._search_working_memory(query)
                for result in working_results:
                    all_results[result.memory.id] = result

            # 2. 检索长期记忆
            if search_long_term:
                long_term_results = self._search_long_term_memory(
                    query=query,
                    query_embedding=query_embedding,
                    context_tags=context_tags,
                    target_emotion=target_emotion,
                    top_k=top_k
                )
                for result in long_term_results:
                    if result.memory.id in all_results:
                        # 合并分数
                        existing = all_results[result.memory.id]
                        existing.similarity_score = max(
                            existing.similarity_score,
                            result.similarity_score
                        )
                    else:
                        all_results[result.memory.id] = result
        
        # 排序并返回
        results = list(all_results.values())
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return results[:top_k]
    
    def _search_working_memory(
        self,
        query: Optional[str]
    ) -> List[RetrievalResult]:
        """搜索工作记忆"""
        chunks = self.working_memory.get_all()
        results = []
        
        for chunk in chunks:
            score = 0.5  # 基础分数
            
            if query and isinstance(chunk.content, str):
                if query.lower() in chunk.content.lower():
                    score = 0.9
            
            # 将工作记忆组块转换为MemoryItem用于结果
            item = MemoryItem(
                content=str(chunk.content),
                memory_type=MemoryType.WORKING,
                importance=chunk.priority,
                metadata={
                    "chunk_type": chunk.chunk_type,
                    "source": chunk.source,
                    "in_working_memory": True
                }
            )
            
            result = RetrievalResult(
                memory=item,
                similarity_score=score,
                retrieval_method="working_memory"
            )
            results.append(result)
        
        return results
    
    def _search_long_term_memory(
        self,
        query: Optional[str],
        query_embedding: Optional[np.ndarray],
        context_tags: Optional[List[str]],
        target_emotion: Optional[str],
        top_k: int
    ) -> List[RetrievalResult]:
        """搜索长期记忆"""
        memories = self.long_term_memory.get_all_memories(limit=1000)
        
        if not memories:
            return []
        
        # 使用混合检索
        return self.retriever.hybrid_search(
            query_embedding=query_embedding,
            context_tags=context_tags,
            target_emotion=target_emotion,
            memories=memories,
            top_k=top_k
        )
    
    def retrieve_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """
        通过ID检索记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[MemoryItem]: 记忆条目
        """
        # 先检查长期记忆
        item = self.long_term_memory.retrieve(memory_id)
        if item:
            return item
        
        return None
    
    # ========== 巩固接口 ==========
    
    def consolidate(self, force: bool = False) -> int:
        """
        手动触发记忆巩固
        
        Args:
            force: 是否强制巩固所有工作记忆
            
        Returns:
            int: 巩固的记忆数量
        """
        with self._lock:
            chunks = self.working_memory.get_all()
            
            if force:
                # 强制巩固所有
                worthy_chunks = chunks
            else:
                # 筛选值得巩固的
                worthy_chunks = [
                    chunk for chunk in chunks
                    if self.consolidator.should_consolidate(chunk)
                ]
            
            if not worthy_chunks:
                return 0
            
            # 生成嵌入（使用确定性 embedding，不使用随机向量）
            embeddings = {
                chunk.id: generate_text_embedding(
                    self._extract_text_for_embedding(chunk.content),
                    self.vector_dim
                )
                for chunk in worthy_chunks
            }
            
            # 巩固
            consolidated = self.consolidator.consolidate_chunks(
                chunks=worthy_chunks,
                embeddings=embeddings
            )
            
            # 存储到长期记忆
            for item in consolidated:
                self.long_term_memory.store_item(item)
            
            # 从工作记忆移除已巩固的
            for chunk in worthy_chunks:
                self.working_memory.remove(chunk.id)
            
            logger.info(f"Consolidated {len(consolidated)} memories")
            return len(consolidated)
    
    def sleep_consolidation(self) -> int:
        """
        睡眠模式巩固
        
        Returns:
            int: 巩固的记忆数量
        """
        with self._lock:
            chunks = self.working_memory.get_all()
            existing = self.long_term_memory.get_all_memories(limit=1000)
            
            consolidated = self.consolidator.sleep_consolidation(
                chunks=chunks,
                existing_memories=existing
            )
            
            # 存储到长期记忆
            for item in consolidated:
                self.long_term_memory.store_item(item)
            
            logger.info(f"Sleep consolidation: {len(consolidated)} memories")
            return len(consolidated)
    
    # ========== 遗忘接口 ==========
    
    def forget(self, memory_id: str) -> bool:
        """
        遗忘指定记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            # 先检查记忆是否存在
            memory = self.long_term_memory.retrieve(memory_id)
            if not memory:
                return False
            
            # 从长期记忆删除
            deleted = self.long_term_memory.delete(memory_id)
            
            if deleted:
                logger.info(f"Forgot memory: {memory_id}")
            
            return deleted
    
    def cleanup(self) -> int:
        """
        清理过期记忆
        
        Returns:
            int: 清理的数量
        """
        with self._lock:
            memories = self.long_term_memory.get_all_memories()
            retained = self.forgetter.cleanup_memories(memories)
            
            # 更新数据库中的状态
            forgotten_count = len(memories) - len(retained)
            
            # 更新保留的记忆
            for memory in retained:
                if memory.status == MemoryStatus.DECAYING:
                    self.long_term_memory.update_memory(
                        memory.id,
                        {"decay_factor": memory.decay_factor, "status": memory.status.value}
                    )
            
            logger.info(f"Cleanup: {forgotten_count} forgotten, {len(retained)} retained")
            return forgotten_count
    
    # ========== 增强接口 ==========
    
    def reinforce(self, memory_id: str) -> Optional[MemoryItem]:
        """
        强化指定记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[MemoryItem]: 强化后的记忆
        """
        with self._lock:
            memory = self.long_term_memory.retrieve(memory_id)
            if not memory:
                return None
            
            # 应用强化
            reinforced = self.enhancer.reinforce_by_repetition(memory)
            
            # 更新数据库
            self.long_term_memory.update_memory(
                memory_id,
                {
                    "importance": reinforced.importance,
                    "confidence": reinforced.confidence,
                    "repetition_count": reinforced.repetition_count
                }
            )
            
            # 同时对抗遗忘
            self.forgetter.reinforce_memory(reinforced)
            
            return reinforced
    
    def enhance_associations(self, memory_id: str) -> bool:
        """
        增强记忆的关联
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            memory = self.long_term_memory.retrieve(memory_id)
            if not memory:
                return False
            
            # 获取候选关联记忆
            candidates = self.long_term_memory.get_all_memories(limit=100)
            
            # 增强关联
            enhanced, new_assocs = self.enhancer.enhance_associations(
                memory, candidates
            )
            
            # 更新数据库
            if new_assocs:
                self.long_term_memory.update_memory(
                    memory_id,
                    {
                        "associations": enhanced.associations,
                        "importance": enhanced.importance
                    }
                )
                
                # 添加关联记录
                for assoc_id, strength in new_assocs:
                    self.long_term_memory.add_association(
                        memory_id, assoc_id, strength=strength
                    )
            
            return len(new_assocs) > 0
    
    # ========== 内部回调 ==========
    
    def _on_working_memory_transfer(self, chunk: MemoryChunk) -> None:
        """工作记忆转移回调"""
        logger.debug(f"Working memory chunk transferred: {chunk.id}")
    
    def _on_consolidation_complete(self, item: MemoryItem) -> None:
        """巩固完成回调"""
        logger.debug(f"Consolidation complete: {item.id}")
    
    def _on_memory_forgotten(self, item: MemoryItem) -> None:
        """记忆遗忘回调"""
        logger.debug(f"Memory forgotten: {item.id}")
    
    def _on_memory_enhanced(self, item: MemoryItem) -> None:
        """记忆增强回调"""
        logger.debug(f"Memory enhanced: {item.id}")
    
    def _check_auto_tasks(self) -> None:
        """检查并执行自动任务"""
        current_time = time.time()
        
        # 自动巩固
        if self.auto_consolidate:
            if current_time - self._last_consolidation >= self._consolidation_interval:
                self.consolidate()
                self._last_consolidation = current_time
        
        # 自动清理
        if self.auto_cleanup:
            if current_time - self._last_cleanup >= self._cleanup_interval:
                self.cleanup()
                self._last_cleanup = current_time
    
    # ========== 统计接口 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取整体统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "sensory_memory": self.sensory_memory.get_stats(),
            "working_memory": self.working_memory.get_stats(),
            "long_term_memory": self.long_term_memory.get_stats(),
            "consolidator": self.consolidator.get_stats(),
            "forgetter": self.forgetter.get_stats(),
            "enhancer": self.enhancer.get_stats(),
            "retriever": self.retriever.get_retrieval_stats()
        }
    
    def get_memory_flow(self) -> Dict[str, int]:
        """
        获取记忆流信息
        
        Returns:
            Dict[str, int]: 各层记忆数量
        """
        return {
            "sensory": len(self.sensory_memory),
            "working": len(self.working_memory),
            "long_term": len(self.long_term_memory)
        }
    
    # ========== 生命周期管理 ==========
    
    def shutdown(self) -> None:
        """关闭记忆管理器"""
        logger.info("Shutting down MemoryManager...")
        
        # 巩固剩余工作记忆
        if len(self.working_memory) > 0:
            self.consolidate(force=True)
        
        # 关闭瞬时记忆
        self.sensory_memory.shutdown()
        
        logger.info("MemoryManager shutdown complete")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()
    
    def __repr__(self) -> str:
        flow = self.get_memory_flow()
        return (
            f"MemoryManager("
            f"sensory={flow['sensory']}, "
            f"working={flow['working']}, "
            f"long_term={flow['long_term']})"
        )
