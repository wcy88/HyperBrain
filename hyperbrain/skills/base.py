"""
Skill 基类 - 所有 Skill 的基础

参考 OpenClaw 的 Skill 设计理念
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class SkillStatus(Enum):
    """Skill 执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class SkillResult:
    """Skill 执行结果"""
    success: bool
    status: SkillStatus = SkillStatus.SUCCESS
    message: str = ""
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """Skill 基类"""
    
    name: str = "base_skill"
    description: str = "基础技能类"
    version: str = "1.0.0"
    author: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化 Skill"""
        self._initialized = True
        return True
    
    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """执行 Skill，子类必须实现"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        self._initialized = False
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Skill 信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags
        }
