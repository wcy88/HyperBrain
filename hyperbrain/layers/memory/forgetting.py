"""
遗忘机制 (Forgetting)

模拟人脑的遗忘过程：
- 基于Ebbinghaus遗忘曲线
- 自适应遗忘：根据重要性和使用频率调整遗忘速度
- 主动遗忘：释放认知资源
- 定期清理过期记忆

遗忘不是缺陷，而是优化记忆系统的必要机制。
"""

import math
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta

from hyperbrain.core.logger import get_logger
from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryStatus, ForgettingConfig
)
from hyperbrain.layers.memory.memory_utils import (
    compute_ebbinghaus_retention,
    compute_adaptive_decay_rate,
    time_since_hours
)

logger = get_logger("memory.forgetting")


class MemoryForgetting:
    """
    记忆遗忘系统
    
    功能：
    - 艾宾浩斯遗忘曲线计算
    - 自适应遗忘速率
    - 主动遗忘
    - 定期清理
    - 记忆衰减模拟
    
    Attributes:
        config: 遗忘配置
        _forgotten_callbacks: 遗忘回调
    """
    
    def __init__(self, config: Optional[ForgettingConfig] = None):
        self.config = config or ForgettingConfig()
        self._forgotten_callbacks: List[Callable[[MemoryItem], None]] = []
        self._lock = threading.RLock()
        
        logger.info(
            f"MemoryForgetting initialized: "
            f"base_rate={self.config.base_decay_rate}"
        )
    
    def compute_retention(
        self,
        memory: MemoryItem,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        计算记忆的保持率
        
        基于艾宾浩斯遗忘曲线和自适应参数
        
        Args:
            memory: 记忆条目
            current_time: 当前时间
            
        Returns:
            float: 保持率 [0, 1]
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 计算经过的时间
        last_access = memory.last_accessed or memory.created_at
        hours_elapsed = (current_time - last_access).total_seconds() / 3600
        
        if hours_elapsed <= 0:
            return 1.0
        
        # 计算记忆强度
        strength = self._compute_memory_strength(memory)
        
        # 应用艾宾浩斯遗忘曲线
        retention = compute_ebbinghaus_retention(
            hours_elapsed,
            initial_strength=strength,
            base_decay=1.25
        )
        
        # 应用衰减因子
        retention *= memory.decay_factor
        
        return max(0.0, min(1.0, retention))
    
    def should_forget(
        self,
        memory: MemoryItem,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        判断是否应该遗忘
        
        Args:
            memory: 记忆条目
            current_time: 当前时间
            
        Returns:
            bool: 是否应该遗忘
        """
        retention = self.compute_retention(memory, current_time)
        
        # 如果保持率低于阈值，考虑遗忘
        if retention < 0.1:
            # 但重要记忆有保护
            if memory.importance > 0.8:
                return False
            return True
        
        # 检查重要性
        if memory.importance < self.config.min_importance_to_keep:
            return True
        
        return False
    
    def compute_decay_rate(self, memory: MemoryItem) -> float:
        """
        计算记忆的自适应遗忘速率
        
        Args:
            memory: 记忆条目
            
        Returns:
            float: 遗忘速率
        """
        # 计算访问频率（每小时）
        hours_since_creation = time_since_hours(memory.created_at)
        access_frequency = (
            memory.access_count / hours_since_creation
            if hours_since_creation > 0 else 1.0
        )
        access_frequency = min(1.0, access_frequency)
        
        # 情感强度
        emotional_intensity = 0.0
        if memory.emotional_tag:
            emotional_intensity = memory.emotional_tag.get("intensity", 0)
        
        return compute_adaptive_decay_rate(
            importance=memory.importance,
            access_frequency=access_frequency,
            emotional_intensity=emotional_intensity,
            base_rate=self.config.base_decay_rate,
            importance_weight=self.config.importance_weight,
            frequency_weight=self.config.frequency_weight,
            emotional_weight=self.config.emotional_weight
        )
    
    def apply_decay(self, memory: MemoryItem) -> MemoryItem:
        """
        对记忆应用衰减
        
        Args:
            memory: 记忆条目
            
        Returns:
            MemoryItem: 衰减后的记忆
        """
        decay_rate = self.compute_decay_rate(memory)
        
        # 更新衰减因子
        memory.decay_factor *= (1 - decay_rate)
        memory.decay_factor = max(0.0, memory.decay_factor)
        
        # 如果衰减严重，更新状态
        if memory.decay_factor < 0.1:
            memory.status = MemoryStatus.DECAYING
        
        if memory.decay_factor < 0.01:
            memory.status = MemoryStatus.FORGOTTEN
        
        return memory
    
    def forget_memory(self, memory: MemoryItem, reason: str = "decay") -> MemoryItem:
        """
        主动遗忘记忆
        
        Args:
            memory: 记忆条目
            reason: 遗忘原因
            
        Returns:
            MemoryItem: 遗忘后的记忆
        """
        memory.status = MemoryStatus.FORGOTTEN
        memory.decay_factor = 0.0
        memory.metadata["forgotten_at"] = datetime.now().isoformat()
        memory.metadata["forget_reason"] = reason
        
        # 触发回调
        for callback in self._forgotten_callbacks:
            try:
                callback(memory)
            except Exception as e:
                logger.error(f"Forgotten callback error: {e}")
        
        logger.debug(f"Forgot memory {memory.id}: {reason}")
        return memory
    
    def cleanup_memories(
        self,
        memories: List[MemoryItem],
        force: bool = False
    ) -> List[MemoryItem]:
        """
        清理过期记忆
        
        Args:
            memories: 记忆列表
            force: 是否强制清理（忽略重要性保护）
            
        Returns:
            List[MemoryItem]: 应该被保留的记忆
        """
        current_time = datetime.now()
        retained = []
        forgotten = []
        
        for memory in memories:
            if self.should_forget(memory, current_time):
                if not force and memory.importance > 0.8:
                    retained.append(memory)
                else:
                    forgotten.append(self.forget_memory(memory, "cleanup"))
            else:
                # 应用衰减
                decayed = self.apply_decay(memory)
                if decayed.status == MemoryStatus.FORGOTTEN:
                    forgotten.append(decayed)
                else:
                    retained.append(decayed)
        
        if forgotten:
            logger.info(f"Cleaned up {len(forgotten)} forgotten memories, retained {len(retained)}")
        
        return retained
    
    def batch_decay(
        self,
        memories: List[MemoryItem]
    ) -> Tuple[List[MemoryItem], List[MemoryItem]]:
        """
        批量应用衰减
        
        Args:
            memories: 记忆列表
            
        Returns:
            Tuple[List[MemoryItem], List[MemoryItem]]: (保留的, 遗忘的)
        """
        retained = []
        forgotten = []
        
        for memory in memories:
            decayed = self.apply_decay(memory)
            if decayed.status == MemoryStatus.FORGOTTEN:
                forgotten.append(decayed)
            else:
                retained.append(decayed)
        
        return retained, forgotten
    
    def reinforce_memory(
        self,
        memory: MemoryItem,
        reinforcement_amount: float = 0.2
    ) -> MemoryItem:
        """
        强化记忆（对抗遗忘）
        
        Args:
            memory: 记忆条目
            reinforcement_amount: 强化量
            
        Returns:
            MemoryItem: 强化后的记忆
        """
        # 提升衰减因子
        memory.decay_factor = min(1.0, memory.decay_factor + reinforcement_amount)
        
        # 更新访问信息
        memory.update_access()
        memory.repetition_count += 1
        
        # 如果之前正在衰减，恢复为活跃
        if memory.status == MemoryStatus.DECAYING:
            memory.status = MemoryStatus.ACTIVE
        
        logger.debug(f"Reinforced memory {memory.id}: decay_factor={memory.decay_factor:.2f}")
        return memory
    
    def get_forgetting_curve(
        self,
        memory: MemoryItem,
        hours: int = 168  # 一周
    ) -> List[Tuple[float, float]]:
        """
        获取记忆的遗忘曲线数据
        
        Args:
            memory: 记忆条目
            hours: 时间范围（小时）
            
        Returns:
            List[Tuple[float, float]]: [(时间, 保持率), ...]
        """
        curve = []
        strength = self._compute_memory_strength(memory)
        
        for h in range(0, hours + 1, max(1, hours // 50)):
            retention = compute_ebbinghaus_retention(h, strength)
            curve.append((h, retention * memory.decay_factor))
        
        return curve
    
    def _compute_memory_strength(self, memory: MemoryItem) -> float:
        """
        计算记忆强度
        
        Args:
            memory: 记忆条目
            
        Returns:
            float: 记忆强度
        """
        # 基础强度
        base = 0.3
        
        # 重复次数加成
        repetition_bonus = min(memory.repetition_count * 0.1, 0.5)
        
        # 重要性加成
        importance_bonus = memory.importance * 0.3
        
        # 情感加成
        emotion_bonus = 0.0
        if memory.emotional_tag:
            emotion_bonus = memory.emotional_tag.get("intensity", 0) * 0.2
        
        strength = base + repetition_bonus + importance_bonus + emotion_bonus
        return min(1.0, strength)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "base_decay_rate": self.config.base_decay_rate,
            "importance_weight": self.config.importance_weight,
            "frequency_weight": self.config.frequency_weight,
            "emotional_weight": self.config.emotional_weight,
            "min_importance_to_keep": self.config.min_importance_to_keep,
            "callback_count": len(self._forgotten_callbacks)
        }
    
    def register_callback(self, callback: Callable[[MemoryItem], None]) -> None:
        """
        注册遗忘回调
        
        Args:
            callback: 回调函数
        """
        self._forgotten_callbacks.append(callback)
