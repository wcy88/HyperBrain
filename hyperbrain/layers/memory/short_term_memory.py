"""
短期记忆（工作记忆）

模拟人脑的工作记忆，容量有限，用于临时存储当前上下文
"""

from typing import Any, Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger

logger = get_logger("memory.short_term")


@dataclass
class WorkingMemorySlot:
    """工作记忆槽位"""
    content: Any
    focus_level: float = 1.0  # 注意力水平
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""


class ShortTermMemory:
    """
    短期记忆系统
    
    特点：
    - 容量有限（默认7±2个组块）
    - 信息保持时间短
    - 支持注意力机制
    """
    
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.slots: deque = deque(maxlen=capacity)
        self.focus_target: Optional[str] = None
        logger.info(f"ShortTermMemory initialized with capacity {capacity}")
    
    def add(self, content: Any, source: str = "") -> None:
        """添加内容到工作记忆"""
        slot = WorkingMemorySlot(
            content=content,
            source=source
        )
        self.slots.append(slot)
        logger.debug(f"Added to working memory from {source}")
    
    def get_context(self, n_recent: int = 3) -> List[Any]:
        """获取最近的工作记忆内容"""
        recent = list(self.slots)[-n_recent:]
        return [slot.content for slot in recent]
    
    def clear(self) -> None:
        """清空工作记忆"""
        self.slots.clear()
        logger.info("Short-term memory cleared")
    
    def set_focus(self, target: str) -> None:
        """设置注意力焦点"""
        self.focus_target = target
        logger.debug(f"Focus set to: {target}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "capacity": self.capacity,
            "current_size": len(self.slots),
            "utilization": len(self.slots) / self.capacity,
            "focus_target": self.focus_target
        }
