"""
瞬时记忆模块 (Sensory Memory)

模拟人脑的瞬时记忆（感觉记忆）：
- 容量：最近10条输入
- 持续时间：30秒自动过期
- 使用双端队列实现
- 支持快速存取

瞬时记忆是信息进入记忆系统的第一道门户，负责短暂保存感官输入。
"""

import time
import threading
from typing import Any, List, Optional, Dict, Callable
from collections import deque
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import SensoryInput

logger = get_logger("memory.sensory")


class SensoryMemory:
    """
    瞬时记忆系统
    
    特点：
    - 容量有限（默认10条）
    - 自动过期（默认30秒）
    - 快速存取
    - 线程安全
    - 支持多种感知模态
    
    Attributes:
        capacity: 最大容量
        ttl_seconds: 生存时间（秒）
        inputs: 输入队列
        _lock: 线程锁
        _cleanup_thread: 清理线程
        _callbacks: 过期回调函数列表
    """
    
    def __init__(
        self,
        capacity: int = 10,
        ttl_seconds: float = 30.0,
        enable_auto_cleanup: bool = True
    ):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.inputs: deque = deque(maxlen=capacity)
        self._lock = threading.RLock()
        self._callbacks: List[Callable[[SensoryInput], None]] = []
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._enable_auto_cleanup = enable_auto_cleanup
        
        if enable_auto_cleanup:
            self._start_cleanup_thread()
        
        logger.info(
            f"SensoryMemory initialized: capacity={capacity}, "
            f"ttl={ttl_seconds}s"
        )
    
    def _start_cleanup_thread(self) -> None:
        """启动自动清理线程"""
        def cleanup_loop():
            while not self._stop_cleanup.wait(timeout=5.0):
                self._cleanup_expired()
        
        self._cleanup_thread = threading.Thread(
            target=cleanup_loop,
            daemon=True,
            name="SensoryMemoryCleanup"
        )
        self._cleanup_thread.start()
    
    def add(
        self,
        content: Any,
        modality: str = "text",
        source: str = "",
        intensity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SensoryInput:
        """
        添加感知输入到瞬时记忆
        
        Args:
            content: 输入内容
            modality: 模态类型 (text, image, audio, video)
            source: 来源
            intensity: 强度 [0, 1]
            metadata: 元数据
            
        Returns:
            SensoryInput: 创建的感知输入对象
        """
        sensory_input = SensoryInput(
            content=content,
            modality=modality,
            source=source,
            intensity=intensity,
            metadata=metadata or {}
        )
        
        with self._lock:
            # 如果队列已满，最旧的输入会被自动移除
            if len(self.inputs) >= self.capacity:
                expired_item = self.inputs.popleft()
                logger.debug(f"Sensory input evicted (capacity): {expired_item['input'].id}")
            
            self.inputs.append({
                "input": sensory_input,
                "timestamp": time.time()
            })
        
        logger.debug(
            f"Added sensory input: {sensory_input.id}, "
            f"modality={modality}, intensity={intensity:.2f}"
        )
        return sensory_input
    
    def get_recent(self, n: int = 5) -> List[SensoryInput]:
        """
        获取最近的n条感知输入
        
        Args:
            n: 获取数量
            
        Returns:
            List[SensoryInput]: 感知输入列表（按时间倒序）
        """
        with self._lock:
            # 先清理过期数据
            self._cleanup_expired()
            
            recent = list(self.inputs)[-n:]
            return [item["input"] for item in reversed(recent)]
    
    def get_all(self) -> List[SensoryInput]:
        """
        获取所有有效的感知输入
        
        Returns:
            List[SensoryInput]: 所有有效输入
        """
        with self._lock:
            self._cleanup_expired()
            return [item["input"] for item in self.inputs]
    
    def get_by_modality(self, modality: str) -> List[SensoryInput]:
        """
        按模态获取感知输入
        
        Args:
            modality: 模态类型
            
        Returns:
            List[SensoryInput]: 匹配的输入列表
        """
        with self._lock:
            self._cleanup_expired()
            return [
                item["input"] for item in self.inputs
                if item["input"].modality == modality
            ]
    
    def get_by_source(self, source: str) -> List[SensoryInput]:
        """
        按来源获取感知输入
        
        Args:
            source: 来源标识
            
        Returns:
            List[SensoryInput]: 匹配的输入列表
        """
        with self._lock:
            self._cleanup_expired()
            return [
                item["input"] for item in self.inputs
                if item["input"].source == source
            ]
    
    def get_latest(self) -> Optional[SensoryInput]:
        """
        获取最新的感知输入
        
        Returns:
            Optional[SensoryInput]: 最新输入，如果没有则返回None
        """
        with self._lock:
            self._cleanup_expired()
            if self.inputs:
                return self.inputs[-1]["input"]
            return None
    
    def peek(self, index: int = -1) -> Optional[SensoryInput]:
        """
        查看指定位置的感知输入（不移除）
        
        Args:
            index: 索引（默认-1表示最新）
            
        Returns:
            Optional[SensoryInput]: 感知输入
        """
        with self._lock:
            self._cleanup_expired()
            try:
                return self.inputs[index]["input"]
            except IndexError:
                return None
    
    def remove(self, input_id: str) -> bool:
        """
        移除指定ID的感知输入
        
        Args:
            input_id: 输入ID
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            for i, item in enumerate(self.inputs):
                if item["input"].id == input_id:
                    del self.inputs[i]
                    logger.debug(f"Removed sensory input: {input_id}")
                    return True
            return False
    
    def clear(self) -> None:
        """清空所有感知输入"""
        with self._lock:
            count = len(self.inputs)
            self.inputs.clear()
            logger.info(f"Cleared {count} sensory inputs")
    
    def _cleanup_expired(self) -> int:
        """
        清理过期的感知输入
        
        Returns:
            int: 清理的数量
        """
        current_time = time.time()
        expired_count = 0
        
        # 创建新队列，过滤掉过期数据
        valid_items = deque(maxlen=self.capacity)
        for item in self.inputs:
            age = current_time - item["timestamp"]
            if age <= self.ttl_seconds:
                valid_items.append(item)
            else:
                expired_count += 1
                # 触发回调
                for callback in self._callbacks:
                    try:
                        callback(item["input"])
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
        
        self.inputs = valid_items
        
        if expired_count > 0:
            logger.debug(f"Cleaned up {expired_count} expired sensory inputs")
        
        return expired_count
    
    def force_cleanup(self) -> int:
        """
        强制清理所有过期数据
        
        Returns:
            int: 清理的数量
        """
        with self._lock:
            return self._cleanup_expired()
    
    def register_expiry_callback(
        self,
        callback: Callable[[SensoryInput], None]
    ) -> None:
        """
        注册过期回调函数
        
        Args:
            callback: 回调函数，接收过期的SensoryInput
        """
        self._callbacks.append(callback)
        logger.debug(f"Registered expiry callback: {callback.__name__}")
    
    def unregister_expiry_callback(
        self,
        callback: Callable[[SensoryInput], None]
    ) -> bool:
        """
        注销过期回调函数
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功注销
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            self._cleanup_expired()
            
            modalities = {}
            for item in self.inputs:
                mod = item["input"].modality
                modalities[mod] = modalities.get(mod, 0) + 1
            
            return {
                "capacity": self.capacity,
                "current_size": len(self.inputs),
                "utilization": len(self.inputs) / self.capacity if self.capacity > 0 else 0,
                "ttl_seconds": self.ttl_seconds,
                "modalities": modalities,
                "oldest_age_seconds": (
                    time.time() - self.inputs[0]["timestamp"]
                    if self.inputs else 0
                ),
                "newest_age_seconds": (
                    time.time() - self.inputs[-1]["timestamp"]
                    if self.inputs else 0
                )
            }
    
    def is_full(self) -> bool:
        """
        检查是否已满
        
        Returns:
            bool: 是否已满
        """
        with self._lock:
            return len(self.inputs) >= self.capacity
    
    def is_empty(self) -> bool:
        """
        检查是否为空
        
        Returns:
            bool: 是否为空
        """
        with self._lock:
            self._cleanup_expired()
            return len(self.inputs) == 0
    
    def __len__(self) -> int:
        """返回当前有效输入数量"""
        with self._lock:
            self._cleanup_expired()
            return len(self.inputs)
    
    def __contains__(self, input_id: str) -> bool:
        """检查是否包含指定ID的输入"""
        with self._lock:
            self._cleanup_expired()
            return any(
                item["input"].id == input_id
                for item in self.inputs
            )
    
    def shutdown(self) -> None:
        """关闭瞬时记忆，停止清理线程"""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)
        logger.info("SensoryMemory shutdown")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except Exception:
            pass
    
    def __repr__(self) -> str:
        return (
            f"SensoryMemory("
            f"capacity={self.capacity}, "
            f"ttl={self.ttl_seconds}s, "
            f"items={len(self)})"
        )
