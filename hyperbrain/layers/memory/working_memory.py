"""
工作记忆模块 (Working Memory)

模拟人脑的工作记忆系统：
- 容量限制：7±2个组块（5-9个）
- 使用优先级队列管理
- 支持组块的合并和拆分
- 实现注意力聚焦机制
- 定期将重要信息转移到长期记忆

工作记忆是认知加工的核心，负责临时存储和操作信息。
"""

import time
import heapq
import threading
from typing import Any, List, Optional, Dict, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import MemoryChunk, MemoryItem, MemoryType
from hyperbrain.layers.memory.memory_utils import (
    compute_attention_weights,
    time_since,
    time_since_hours
)

logger = get_logger("memory.working")


@dataclass(order=True)
class PrioritizedChunk:
    """带优先级的组块包装器（用于堆队列）"""
    priority: float
    timestamp: float = field(compare=False)
    chunk: MemoryChunk = field(compare=False)
    
    def __post_init__(self):
        # 确保priority可用于比较
        if not isinstance(self.priority, (int, float)):
            self.priority = float(self.priority)


class WorkingMemory:
    """
    工作记忆系统
    
    特点：
    - 容量有限（默认7±2个组块）
    - 优先级队列管理
    - 注意力聚焦机制
    - 组块合并/拆分
    - 自动向长期记忆转移
    - 线程安全
    
    Attributes:
        capacity: 最大容量（组块数）
        chunks: 组块列表
        focus_target: 注意力焦点
        _lock: 线程锁
        _transfer_callbacks: 转移回调
    """
    
    def __init__(
        self,
        capacity: int = 7,
        importance_threshold: float = 0.7,
        auto_transfer_interval: float = 60.0
    ):
        self.capacity = capacity
        self.importance_threshold = importance_threshold
        self.auto_transfer_interval = auto_transfer_interval
        
        self.chunks: List[PrioritizedChunk] = []
        self.focus_target: Optional[str] = None
        self.focused_chunk_ids: set = set()
        
        self._lock = threading.RLock()
        self._transfer_callbacks: List[Callable[[MemoryChunk], None]] = []
        self._chunk_map: Dict[str, MemoryChunk] = {}  # ID到chunk的快速映射
        
        logger.info(
            f"WorkingMemory initialized: capacity={capacity}, "
            f"threshold={importance_threshold}"
        )
    
    def add(
        self,
        content: Any,
        chunk_type: str = "generic",
        priority: float = 0.5,
        size: int = 1,
        source: str = "",
        related_chunks: Optional[List[str]] = None
    ) -> MemoryChunk:
        """
        添加组块到工作记忆
        
        Args:
            content: 内容
            chunk_type: 组块类型
            priority: 优先级 [0, 1]
            size: 占用大小
            source: 来源
            related_chunks: 相关组块ID
            
        Returns:
            MemoryChunk: 创建的组块
        """
        chunk = MemoryChunk(
            content=content,
            chunk_type=chunk_type,
            priority=priority,
            size=size,
            source=source,
            related_chunks=related_chunks or []
        )
        
        with self._lock:
            # 检查容量
            current_size = sum(c.chunk.size for c in self.chunks)
            
            # 如果超出容量，移除低优先级的组块
            while current_size + size > self.capacity and self.chunks:
                # 找到优先级最低的组块
                lowest = min(self.chunks, key=lambda x: x.priority)
                self.chunks.remove(lowest)
                del self._chunk_map[lowest.chunk.id]
                current_size -= lowest.chunk.size
                logger.debug(f"Evicted chunk: {lowest.chunk.id}")
            
            # 添加新组块
            prioritized = PrioritizedChunk(
                priority=priority,
                timestamp=time.time(),
                chunk=chunk
            )
            self.chunks.append(prioritized)
            self._chunk_map[chunk.id] = chunk
            
            # 按优先级排序
            self.chunks.sort(key=lambda x: x.priority, reverse=True)
        
        logger.debug(
            f"Added chunk: {chunk.id}, type={chunk_type}, "
            f"priority={priority:.2f}, size={size}"
        )
        return chunk
    
    def add_chunk(self, chunk: MemoryChunk) -> MemoryChunk:
        """
        直接添加MemoryChunk对象
        
        Args:
            chunk: 组块对象
            
        Returns:
            MemoryChunk: 添加的组块
        """
        with self._lock:
            current_size = sum(c.chunk.size for c in self.chunks)
            
            while current_size + chunk.size > self.capacity and self.chunks:
                lowest = min(self.chunks, key=lambda x: x.priority)
                self.chunks.remove(lowest)
                del self._chunk_map[lowest.chunk.id]
                current_size -= lowest.chunk.size
            
            prioritized = PrioritizedChunk(
                priority=chunk.priority,
                timestamp=time.time(),
                chunk=chunk
            )
            self.chunks.append(prioritized)
            self._chunk_map[chunk.id] = chunk
            self.chunks.sort(key=lambda x: x.priority, reverse=True)
        
        return chunk
    
    def get_all(self) -> List[MemoryChunk]:
        """
        获取所有组块（按优先级排序）
        
        Returns:
            List[MemoryChunk]: 组块列表
        """
        with self._lock:
            return [pc.chunk for pc in sorted(self.chunks, key=lambda x: x.priority, reverse=True)]
    
    def get_recent(self, n: int = 3) -> List[MemoryChunk]:
        """
        获取最近的n个组块
        
        Args:
            n: 数量
            
        Returns:
            List[MemoryChunk]: 组块列表
        """
        with self._lock:
            sorted_by_time = sorted(self.chunks, key=lambda x: x.timestamp, reverse=True)
            return [pc.chunk for pc in sorted_by_time[:n]]
    
    def get_focused(self) -> List[MemoryChunk]:
        """
        获取注意力焦点中的组块
        
        Returns:
            List[MemoryChunk]: 焦点组块
        """
        with self._lock:
            if self.focus_target:
                return [
                    pc.chunk for pc in self.chunks
                    if pc.chunk.id in self.focused_chunk_ids
                ]
            return []
    
    def get_by_type(self, chunk_type: str) -> List[MemoryChunk]:
        """
        按类型获取组块
        
        Args:
            chunk_type: 组块类型
            
        Returns:
            List[MemoryChunk]: 匹配的组块
        """
        with self._lock:
            return [pc.chunk for pc in self.chunks if pc.chunk.chunk_type == chunk_type]
    
    def get_chunk(self, chunk_id: str) -> Optional[MemoryChunk]:
        """
        通过ID获取组块
        
        Args:
            chunk_id: 组块ID
            
        Returns:
            Optional[MemoryChunk]: 组块或None
        """
        with self._lock:
            return self._chunk_map.get(chunk_id)
    
    def update_priority(self, chunk_id: str, new_priority: float) -> bool:
        """
        更新组块优先级
        
        Args:
            chunk_id: 组块ID
            new_priority: 新优先级
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            for pc in self.chunks:
                if pc.chunk.id == chunk_id:
                    pc.priority = new_priority
                    pc.chunk.priority = new_priority
                    self.chunks.sort(key=lambda x: x.priority, reverse=True)
                    return True
            return False
    
    def boost_priority(self, chunk_id: str, boost: float = 0.1) -> bool:
        """
        提升组块优先级
        
        Args:
            chunk_id: 组块ID
            boost: 提升量
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            for pc in self.chunks:
                if pc.chunk.id == chunk_id:
                    new_priority = min(1.0, pc.priority + boost)
                    pc.priority = new_priority
                    pc.chunk.priority = new_priority
                    self.chunks.sort(key=lambda x: x.priority, reverse=True)
                    return True
            return False
    
    def merge_chunks(self, chunk_id1: str, chunk_id2: str) -> Optional[MemoryChunk]:
        """
        合并两个组块
        
        Args:
            chunk_id1: 第一个组块ID
            chunk_id2: 第二个组块ID
            
        Returns:
            Optional[MemoryChunk]: 合并后的组块
        """
        with self._lock:
            chunk1 = self._chunk_map.get(chunk_id1)
            chunk2 = self._chunk_map.get(chunk_id2)
            
            if not chunk1 or not chunk2:
                return None
            
            # 合并组块
            merged = chunk1.merge_with(chunk2)
            
            # 移除旧组块
            self.chunks = [
                pc for pc in self.chunks
                if pc.chunk.id not in (chunk_id1, chunk_id2)
            ]
            del self._chunk_map[chunk_id1]
            del self._chunk_map[chunk_id2]
            
            # 添加合并后的组块
            prioritized = PrioritizedChunk(
                priority=merged.priority,
                timestamp=time.time(),
                chunk=merged
            )
            self.chunks.append(prioritized)
            self._chunk_map[merged.id] = merged
            
            logger.debug(f"Merged chunks {chunk_id1} and {chunk_id2} into {merged.id}")
            return merged
    
    def split_chunk(self, chunk_id: str) -> List[MemoryChunk]:
        """
        拆分组块
        
        Args:
            chunk_id: 组块ID
            
        Returns:
            List[MemoryChunk]: 拆分后的组块列表
        """
        with self._lock:
            chunk = self._chunk_map.get(chunk_id)
            if not chunk:
                return []
            
            split_chunks = chunk.split()
            if len(split_chunks) <= 1:
                return [chunk]
            
            # 移除原组块
            self.chunks = [pc for pc in self.chunks if pc.chunk.id != chunk_id]
            del self._chunk_map[chunk_id]
            
            # 添加拆分后的组块
            for new_chunk in split_chunks:
                prioritized = PrioritizedChunk(
                    priority=new_chunk.priority,
                    timestamp=time.time(),
                    chunk=new_chunk
                )
                self.chunks.append(prioritized)
                self._chunk_map[new_chunk.id] = new_chunk
            
            logger.debug(f"Split chunk {chunk_id} into {len(split_chunks)} chunks")
            return split_chunks
    
    def set_focus(self, target: str, chunk_ids: Optional[List[str]] = None) -> None:
        """
        设置注意力焦点
        
        Args:
            target: 焦点目标描述
            chunk_ids: 需要聚焦的组块ID列表
        """
        with self._lock:
            self.focus_target = target
            self.focused_chunk_ids = set(chunk_ids or [])
            
            # 提升焦点组块的优先级
            for chunk_id in self.focused_chunk_ids:
                self.boost_priority(chunk_id, boost=0.2)
        
        logger.debug(f"Focus set to: {target}, chunks: {chunk_ids}")
    
    def clear_focus(self) -> None:
        """清除注意力焦点"""
        with self._lock:
            self.focus_target = None
            self.focused_chunk_ids.clear()
        
        logger.debug("Focus cleared")
    
    def compute_attention_distribution(self) -> Dict[str, float]:
        """
        计算注意力分布
        
        Returns:
            Dict[str, float]: 组块ID到注意力权重的映射
        """
        with self._lock:
            if not self.chunks:
                return {}
            
            # 计算各项分数
            relevance_scores = [pc.priority for pc in self.chunks]
            recency_scores = [
                1.0 / (1.0 + time_since_hours(datetime.fromtimestamp(pc.timestamp)))
                for pc in self.chunks
            ]
            importance_scores = [pc.chunk.priority for pc in self.chunks]
            
            # 如果有焦点，提升焦点组块的分数
            if self.focused_chunk_ids:
                for i, pc in enumerate(self.chunks):
                    if pc.chunk.id in self.focused_chunk_ids:
                        relevance_scores[i] *= 1.5
            
            weights = compute_attention_weights(
                self.chunks,
                relevance_scores,
                recency_scores,
                importance_scores
            )
            
            return {
                pc.chunk.id: weight
                for pc, weight in zip(self.chunks, weights)
            }
    
    def get_attention_focused_chunks(self, top_k: int = 3) -> List[Tuple[MemoryChunk, float]]:
        """
        获取注意力最集中的组块
        
        Args:
            top_k: 返回数量
            
        Returns:
            List[Tuple[MemoryChunk, float]]: (组块, 注意力权重)列表
        """
        distribution = self.compute_attention_distribution()
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for chunk_id, weight in sorted_items[:top_k]:
            chunk = self.get_chunk(chunk_id)
            if chunk:
                result.append((chunk, weight))
        
        return result
    
    def remove(self, chunk_id: str) -> bool:
        """
        移除组块
        
        Args:
            chunk_id: 组块ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            for i, pc in enumerate(self.chunks):
                if pc.chunk.id == chunk_id:
                    del self.chunks[i]
                    del self._chunk_map[chunk_id]
                    self.focused_chunk_ids.discard(chunk_id)
                    return True
            return False
    
    def clear(self) -> None:
        """清空工作记忆"""
        with self._lock:
            count = len(self.chunks)
            self.chunks.clear()
            self._chunk_map.clear()
            self.focused_chunk_ids.clear()
            self.focus_target = None
            logger.info(f"Cleared {count} chunks from working memory")
    
    def get_high_importance_chunks(self, threshold: Optional[float] = None) -> List[MemoryChunk]:
        """
        获取高重要性的组块
        
        Args:
            threshold: 重要性阈值
            
        Returns:
            List[MemoryChunk]: 高重要性组块
        """
        threshold = threshold or self.importance_threshold
        with self._lock:
            return [
                pc.chunk for pc in self.chunks
                if pc.priority >= threshold
            ]
    
    def to_memory_items(self) -> List[MemoryItem]:
        """
        将工作记忆中的组块转换为记忆条目
        
        Returns:
            List[MemoryItem]: 记忆条目列表
        """
        with self._lock:
            items = []
            for pc in self.chunks:
                item = MemoryItem(
                    content=str(pc.chunk.content),
                    memory_type=MemoryType.WORKING,
                    importance=pc.priority,
                    metadata={
                        "chunk_type": pc.chunk.chunk_type,
                        "source": pc.chunk.source,
                        "working_memory_timestamp": pc.timestamp
                    }
                )
                items.append(item)
            return items
    
    def register_transfer_callback(self, callback: Callable[[MemoryChunk], None]) -> None:
        """
        注册向长期记忆转移的回调
        
        Args:
            callback: 回调函数
        """
        self._transfer_callbacks.append(callback)
    
    def transfer_to_long_term(self, chunk_id: str) -> bool:
        """
        将指定组块转移到长期记忆
        
        Args:
            chunk_id: 组块ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            chunk = self._chunk_map.get(chunk_id)
            if not chunk:
                return False
            
            # 触发回调
            for callback in self._transfer_callbacks:
                try:
                    callback(chunk)
                except Exception as e:
                    logger.error(f"Transfer callback error: {e}")
            
            # 从工作记忆移除
            self.remove(chunk_id)
            
            logger.debug(f"Transferred chunk {chunk_id} to long-term memory")
            return True
    
    def auto_transfer(self) -> int:
        """
        自动将高重要性组块转移到长期记忆
        
        Returns:
            int: 转移的数量
        """
        transferred = 0
        with self._lock:
            high_priority = self.get_high_importance_chunks()
            for chunk in high_priority:
                if self.transfer_to_long_term(chunk.id):
                    transferred += 1
        
        if transferred > 0:
            logger.info(f"Auto-transferred {transferred} chunks to long-term memory")
        
        return transferred
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            current_size = sum(pc.chunk.size for pc in self.chunks)
            chunk_types = {}
            for pc in self.chunks:
                t = pc.chunk.chunk_type
                chunk_types[t] = chunk_types.get(t, 0) + 1
            
            return {
                "capacity": self.capacity,
                "current_chunks": len(self.chunks),
                "current_size": current_size,
                "utilization": current_size / self.capacity if self.capacity > 0 else 0,
                "chunk_types": chunk_types,
                "focus_target": self.focus_target,
                "focused_chunks": len(self.focused_chunk_ids),
                "avg_priority": (
                    sum(pc.priority for pc in self.chunks) / len(self.chunks)
                    if self.chunks else 0
                )
            }
    
    def is_full(self) -> bool:
        """
        检查是否已满
        
        Returns:
            bool: 是否已满
        """
        with self._lock:
            current_size = sum(pc.chunk.size for pc in self.chunks)
            return current_size >= self.capacity
    
    def is_empty(self) -> bool:
        """
        检查是否为空
        
        Returns:
            bool: 是否为空
        """
        with self._lock:
            return len(self.chunks) == 0
    
    def __len__(self) -> int:
        """返回组块数量"""
        with self._lock:
            return len(self.chunks)
    
    def __contains__(self, chunk_id: str) -> bool:
        """检查是否包含指定ID的组块"""
        with self._lock:
            return chunk_id in self._chunk_map
    
    def __repr__(self) -> str:
        return f"WorkingMemory(capacity={self.capacity}, chunks={len(self)})"
