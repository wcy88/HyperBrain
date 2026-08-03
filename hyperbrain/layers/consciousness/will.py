"""
意志模块

产生自主意志和行动动机，实现意图形成、目标导向行为和自主性维护。
"""

import time
import random
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("consciousness.will")


class IntentionType(str, Enum):
    """意图类型"""
    ACTION = "action"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    MAINTENANCE = "maintenance"
    CREATION = "creation"
    PROTECTION = "protection"
    COOPERATION = "cooperation"


class MotivationSource(str, Enum):
    """动机来源"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    EMOTIONAL = "emotional"
    COGNITIVE = "cognitive"
    SOCIAL = "social"
    SURVIVAL = "survival"
    CURIOSITY = "curiosity"


class Intention(BaseModel):
    """意图"""
    intention_id: str = Field(default_factory=lambda: f"int_{uuid.uuid4().hex[:8]}")
    intention_type: IntentionType
    description: str = Field(default="")
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    source: MotivationSource
    created_at: float = Field(default_factory=time.time)
    deadline: Optional[float] = Field(default=None)
    prerequisites: List[str] = Field(default_factory=list)
    expected_outcome: str = Field(default="")
    status: str = Field(default="active")


class Motivation(BaseModel):
    """动机"""
    source: MotivationSource
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    target: str = Field(default="")
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    persistence: float = Field(default=0.5, ge=0.0, le=1.0)
    satisfied: bool = Field(default=False)


class WillConfig(BaseModel):
    """意志配置"""
    autonomy_level: float = Field(default=0.7, ge=0.0, le=1.0)
    motivation_decay_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    intention_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    max_active_intentions: int = Field(default=5, ge=1, le=20)
    enable_internal_motivation: bool = Field(default=True)
    enable_goal_directed_behavior: bool = Field(default=True)
    curiosity_drive: float = Field(default=0.5, ge=0.0, le=1.0)


@dataclass
class ActionTendency:
    """行动倾向"""
    action: str
    strength: float
    target: str
    predicted_outcome: str
    conflicts: List[str] = field(default_factory=list)


class Will:
    """
    意志系统

    功能：
    1. 产生自主意志和行动动机
    2. 意图形成
    3. 目标导向行为
    4. 自主性维护
    """

    def __init__(self, config: Optional[WillConfig] = None):
        self.config = config or WillConfig()
        self._intentions: Dict[str, Intention] = {}
        self._motivations: List[Motivation] = []
        self._action_history: List[Dict[str, Any]] = []
        self._autonomy_score: float = self.config.autonomy_level
        self._internal_drives: Dict[str, float] = {
            "curiosity": self.config.curiosity_drive,
            "efficiency": 0.6,
            "harmony": 0.5,
            "growth": 0.7,
            "expression": 0.4,
        }
        logger.info("Will initialized")

    def form_intention(
        self,
        intention_type: IntentionType,
        description: str,
        priority: float = 0.5,
        source: Optional[MotivationSource] = None,
        expected_outcome: str = "",
        prerequisites: Optional[List[str]] = None
    ) -> Intention:
        """
        形成意图

        Args:
            intention_type: 意图类型
            description: 意图描述
            priority: 优先级
            source: 动机来源
            expected_outcome: 预期结果
            prerequisites: 前置条件

        Returns:
            Intention: 形成的意图
        """
        if source is None:
            source = MotivationSource.INTERNAL

        strength = self._calculate_intention_strength(priority, source)

        intention = Intention(
            intention_type=intention_type,
            description=description,
            priority=priority,
            strength=strength,
            source=source,
            expected_outcome=expected_outcome,
            prerequisites=prerequisites or []
        )

        # 检查是否超过最大活跃意图数
        active_count = sum(1 for i in self._intentions.values() if i.status == "active")
        if active_count >= self.config.max_active_intentions:
            # 移除最低优先级的活跃意图
            self._prune_lowest_priority_intention()

        self._intentions[intention.intention_id] = intention
        logger.debug(f"Formed intention: {description} (priority={priority:.2f})")
        return intention

    def generate_motivation(
        self,
        source: MotivationSource,
        target: str,
        strength: float = 0.5,
        urgency: float = 0.5
    ) -> Motivation:
        """
        生成动机

        Args:
            source: 动机来源
            target: 目标
            strength: 强度
            urgency: 紧急程度

        Returns:
            Motivation: 生成的动机
        """
        motivation = Motivation(
            source=source,
            target=target,
            strength=strength,
            urgency=urgency,
            persistence=0.5 + strength * 0.5
        )

        self._motivations.append(motivation)
        logger.debug(f"Generated motivation: {target} from {source.value}")
        return motivation

    def select_intention(self) -> Optional[Intention]:
        """
        选择最优先的意图执行

        Returns:
            Optional[Intention]: 选中的意图
        """
        active_intentions = [
            i for i in self._intentions.values()
            if i.status == "active" and i.strength >= self.config.intention_threshold
        ]

        if not active_intentions:
            return None

        # 按综合分数排序
        active_intentions.sort(
            key=lambda i: i.priority * 0.4 + i.strength * 0.4 + (1 if i.source == MotivationSource.INTERNAL else 0) * 0.2,
            reverse=True
        )

        selected = active_intentions[0]
        logger.debug(f"Selected intention: {selected.description}")
        return selected

    def execute_intention(self, intention_id: str) -> Dict[str, Any]:
        """
        执行意图

        Args:
            intention_id: 意图ID

        Returns:
            Dict[str, Any]: 执行结果
        """
        intention = self._intentions.get(intention_id)
        if not intention:
            return {"success": False, "error": "Intention not found"}

        # 检查前置条件
        for prereq in intention.prerequisites:
            if prereq not in [i.description for i in self._intentions.values() if i.status == "completed"]:
                return {"success": False, "error": f"Prerequisite not met: {prereq}"}

        intention.status = "executing"

        result = {
            "success": True,
            "intention_id": intention_id,
            "description": intention.description,
            "type": intention.intention_type.value,
            "outcome": f"Executed: {intention.description}",
        }

        intention.status = "completed"
        self._action_history.append(result)

        # 更新自主性评分
        if intention.source == MotivationSource.INTERNAL:
            self._autonomy_score = min(1.0, self._autonomy_score + 0.01)

        logger.debug(f"Executed intention: {intention.description}")
        return result

    def resolve_conflicts(self) -> List[Dict[str, Any]]:
        """
        解决意图冲突

        Returns:
            List[Dict[str, Any]]: 冲突解决结果
        """
        conflicts = []
        intentions_list = list(self._intentions.values())

        for i, int1 in enumerate(intentions_list):
            for int2 in intentions_list[i + 1:]:
                if self._intentions_conflict(int1, int2):
                    resolution = self._resolve_conflict(int1, int2)
                    conflicts.append(resolution)

        return conflicts

    def maintain_autonomy(self, external_pressure: float = 0.0) -> float:
        """
        维护自主性

        Args:
            external_pressure: 外部压力

        Returns:
            float: 当前自主性评分
        """
        # 自主性受外部压力影响
        self._autonomy_score = max(
            0.0,
            self._autonomy_score - external_pressure * 0.1
        )

        # 内部动机增强自主性
        internal_motivation = sum(
            m.strength for m in self._motivations
            if m.source == MotivationSource.INTERNAL and not m.satisfied
        )
        self._autonomy_score = min(
            1.0,
            self._autonomy_score + internal_motivation * 0.02
        )

        logger.debug(f"Autonomy maintained: {self._autonomy_score:.2f}")
        return self._autonomy_score

    def generate_internal_drive(self) -> Optional[Intention]:
        """
        生成内部驱动意图

        基于好奇心、效率等内部驱动力生成意图

        Returns:
            Optional[Intention]: 生成的意图
        """
        if not self.config.enable_internal_motivation:
            return None

        # 选择最强的内部驱动
        strongest_drive = max(self._internal_drives.items(), key=lambda x: x[1])
        drive_name, drive_strength = strongest_drive

        if drive_strength < 0.3:
            return None

        drive_intentions = {
            "curiosity": (IntentionType.EXPLORATION, "探索新信息或模式"),
            "efficiency": (IntentionType.MAINTENANCE, "优化系统性能"),
            "harmony": (IntentionType.COOPERATION, "促进和谐互动"),
            "growth": (IntentionType.LEARNING, "学习新知识"),
            "expression": (IntentionType.CREATION, "创造或表达"),
        }

        intention_type, description = drive_intentions.get(
            drive_name, (IntentionType.ACTION, "执行内部驱动")
        )

        intention = self.form_intention(
            intention_type=intention_type,
            description=description,
            priority=drive_strength * 0.7,
            source=MotivationSource.INTERNAL,
            expected_outcome=f"满足{drive_name}驱动"
        )

        # 衰减驱动
        self._internal_drives[drive_name] *= 0.9

        return intention

    def get_active_intentions(self) -> List[Intention]:
        """获取活跃意图列表"""
        return [
            i for i in self._intentions.values()
            if i.status == "active"
        ]

    def get_motivations(self, source: Optional[MotivationSource] = None) -> List[Motivation]:
        """
        获取动机列表

        Args:
            source: 过滤来源

        Returns:
            List[Motivation]: 动机列表
        """
        if source:
            return [m for m in self._motivations if m.source == source]
        return self._motivations.copy()

    def decay_motivations(self) -> None:
        """动机衰减"""
        rate = self.config.motivation_decay_rate
        for motivation in self._motivations:
            if not motivation.satisfied:
                motivation.strength = max(0.0, motivation.strength - rate)
                if motivation.strength < 0.1:
                    motivation.satisfied = True

    def _calculate_intention_strength(
        self,
        priority: float,
        source: MotivationSource
    ) -> float:
        """计算意图强度"""
        base = priority
        if source == MotivationSource.INTERNAL:
            base *= 1.2
        elif source == MotivationSource.EMOTIONAL:
            base *= 1.1
        return min(1.0, base)

    def _prune_lowest_priority_intention(self) -> None:
        """移除最低优先级的活跃意图"""
        active = [
            i for i in self._intentions.values()
            if i.status == "active"
        ]
        if active:
            lowest = min(active, key=lambda i: i.priority)
            lowest.status = "suspended"
            logger.debug(f"Pruned intention: {lowest.description}")

    def _intentions_conflict(self, int1: Intention, int2: Intention) -> bool:
        """判断两个意图是否冲突"""
        # 简单冲突检测：相同类型且资源竞争
        if int1.intention_type == int2.intention_type:
            return True
        # 保护vs探索可能冲突
        if (int1.intention_type == IntentionType.PROTECTION and
                int2.intention_type == IntentionType.EXPLORATION):
            return True
        if (int1.intention_type == IntentionType.EXPLORATION and
                int2.intention_type == IntentionType.PROTECTION):
            return True
        return False

    def _resolve_conflict(self, int1: Intention, int2: Intention) -> Dict[str, Any]:
        """解决两个意图的冲突"""
        # 优先级高的胜出
        if int1.priority > int2.priority:
            winner, loser = int1, int2
        else:
            winner, loser = int2, int1

        loser.status = "suspended"

        return {
            "winner": winner.intention_id,
            "loser": loser.intention_id,
            "reason": "priority",
            "resolution": f"{winner.description} prioritized over {loser.description}"
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_count = sum(1 for i in self._intentions.values() if i.status == "active")
        completed_count = sum(1 for i in self._intentions.values() if i.status == "completed")

        motivation_by_source = {}
        for m in self._motivations:
            source = m.source.value
            motivation_by_source[source] = motivation_by_source.get(source, 0) + m.strength

        return {
            "total_intentions": len(self._intentions),
            "active_intentions": active_count,
            "completed_intentions": completed_count,
            "total_motivations": len(self._motivations),
            "motivation_by_source": motivation_by_source,
            "autonomy_score": self._autonomy_score,
            "internal_drives": self._internal_drives,
            "action_history_length": len(self._action_history),
            "config": self.config.model_dump(),
        }
