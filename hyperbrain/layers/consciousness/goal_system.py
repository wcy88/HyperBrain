"""
目标体系模块

设定短期、中期、长期目标，管理目标层次结构、优先级、达成追踪和动态调整。
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("consciousness.goal_system")


class GoalTimeframe(str, Enum):
    """目标时间框架"""
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class GoalStatus(str, Enum):
    """目标状态"""
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"
    SUSPENDED = "suspended"


class GoalPriority(str, Enum):
    """目标优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Goal(BaseModel):
    """目标"""
    goal_id: str = Field(default_factory=lambda: f"goal_{int(time.time()*1000)}")
    description: str = Field(...)
    timeframe: GoalTimeframe
    priority: GoalPriority
    status: GoalStatus = Field(default=GoalStatus.PENDING)
    parent_id: Optional[str] = Field(default=None)
    sub_goals: List[str] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: float = Field(default_factory=time.time)
    deadline: Optional[float] = Field(default=None)
    completion_criteria: List[str] = Field(default_factory=list)
    resources_needed: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoalSystemConfig(BaseModel):
    """目标体系配置"""
    max_active_goals: int = Field(default=10, ge=1, le=50)
    max_goals_total: int = Field(default=100, ge=10, le=500)
    auto_prioritize: bool = Field(default=True)
    enable_progress_tracking: bool = Field(default=True)
    enable_dynamic_adjustment: bool = Field(default=True)
    progress_threshold_for_achievement: float = Field(default=0.95, ge=0.0, le=1.0)
    goal_decay_rate: float = Field(default=0.001, ge=0.0, le=1.0)


@dataclass
class GoalProgress:
    """目标进度"""
    goal_id: str
    previous_progress: float
    current_progress: float
    change_reason: str
    timestamp: float = field(default_factory=time.time)


class GoalSystem:
    """
    目标体系

    功能：
    1. 设定短期、中期、长期目标
    2. 目标层次结构
    3. 目标优先级管理
    4. 目标达成追踪
    5. 目标动态调整
    """

    PRIORITY_SCORES = {
        GoalPriority.CRITICAL: 4,
        GoalPriority.HIGH: 3,
        GoalPriority.MEDIUM: 2,
        GoalPriority.LOW: 1,
    }

    TIMEFRAME_WEIGHTS = {
        GoalTimeframe.SHORT_TERM: 1.2,
        GoalTimeframe.MEDIUM_TERM: 1.0,
        GoalTimeframe.LONG_TERM: 0.8,
    }

    def __init__(self, config: Optional[GoalSystemConfig] = None):
        self.config = config or GoalSystemConfig()
        self._goals: Dict[str, Goal] = {}
        self._progress_history: List[GoalProgress] = []
        self._goal_hierarchy: Dict[str, List[str]] = {}
        logger.info("GoalSystem initialized")

    def set_goal(
        self,
        description: str,
        timeframe: GoalTimeframe,
        priority: GoalPriority,
        parent_id: Optional[str] = None,
        deadline: Optional[float] = None,
        completion_criteria: Optional[List[str]] = None,
        resources_needed: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> Goal:
        """
        设定目标

        Args:
            description: 目标描述
            timeframe: 时间框架
            priority: 优先级
            parent_id: 父目标ID
            deadline: 截止时间
            completion_criteria: 完成标准
            resources_needed: 所需资源
            dependencies: 依赖目标

        Returns:
            Goal: 设定的目标
        """
        if len(self._goals) >= self.config.max_goals_total:
            logger.warning("Goal limit reached, cannot add new goal")
            raise RuntimeError("Maximum goal limit reached")

        goal = Goal(
            description=description,
            timeframe=timeframe,
            priority=priority,
            parent_id=parent_id,
            deadline=deadline,
            completion_criteria=completion_criteria or [],
            resources_needed=resources_needed or [],
            dependencies=dependencies or []
        )

        self._goals[goal.goal_id] = goal

        # 更新层次结构
        if parent_id:
            if parent_id not in self._goal_hierarchy:
                self._goal_hierarchy[parent_id] = []
            self._goal_hierarchy[parent_id].append(goal.goal_id)

            parent = self._goals.get(parent_id)
            if parent:
                parent.sub_goals.append(goal.goal_id)

        logger.debug(f"Set goal: {description} ({timeframe.value})")
        return goal

    def activate_goal(self, goal_id: str) -> bool:
        """
        激活目标

        Args:
            goal_id: 目标ID

        Returns:
            bool: 是否成功
        """
        goal = self._goals.get(goal_id)
        if not goal:
            return False

        # 检查依赖
        for dep_id in goal.dependencies:
            dep = self._goals.get(dep_id)
            if dep and dep.status != GoalStatus.ACHIEVED:
                logger.debug(f"Cannot activate goal {goal_id}, dependency {dep_id} not achieved")
                return False

        active_count = sum(1 for g in self._goals.values() if g.status == GoalStatus.ACTIVE)
        if active_count >= self.config.max_active_goals:
            logger.warning("Max active goals reached")
            return False

        goal.status = GoalStatus.ACTIVE
        logger.debug(f"Activated goal: {goal_id}")
        return True

    def update_progress(
        self,
        goal_id: str,
        progress: float,
        reason: str = ""
    ) -> Goal:
        """
        更新目标进度

        Args:
            goal_id: 目标ID
            progress: 进度 (0-1)
            reason: 更新原因

        Returns:
            Goal: 更新后的目标
        """
        goal = self._goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")

        previous = goal.progress
        goal.progress = max(0.0, min(1.0, progress))

        if self.config.enable_progress_tracking:
            self._progress_history.append(GoalProgress(
                goal_id=goal_id,
                previous_progress=previous,
                current_progress=goal.progress,
                change_reason=reason
            ))

        # 检查是否达成
        if goal.progress >= self.config.progress_threshold_for_achievement:
            goal.status = GoalStatus.ACHIEVED
            logger.info(f"Goal achieved: {goal.description}")

            # 更新父目标进度
            if goal.parent_id:
                self._update_parent_progress(goal.parent_id)

        logger.debug(f"Updated goal {goal_id} progress: {previous:.2f} -> {goal.progress:.2f}")
        return goal

    def adjust_goal(
        self,
        goal_id: str,
        new_description: Optional[str] = None,
        new_priority: Optional[GoalPriority] = None,
        new_deadline: Optional[float] = None
    ) -> Optional[Goal]:
        """
        动态调整目标

        Args:
            goal_id: 目标ID
            new_description: 新描述
            new_priority: 新优先级
            new_deadline: 新截止时间

        Returns:
            Optional[Goal]: 调整后的目标
        """
        if not self.config.enable_dynamic_adjustment:
            return None

        goal = self._goals.get(goal_id)
        if not goal:
            return None

        if new_description:
            goal.description = new_description
        if new_priority:
            goal.priority = new_priority
        if new_deadline:
            goal.deadline = new_deadline

        goal.metadata["last_adjusted"] = time.time()
        logger.debug(f"Adjusted goal: {goal_id}")
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """
        获取目标

        Args:
            goal_id: 目标ID

        Returns:
            Optional[Goal]: 目标
        """
        return self._goals.get(goal_id)

    def get_goals_by_status(self, status: GoalStatus) -> List[Goal]:
        """
        按状态获取目标

        Args:
            status: 目标状态

        Returns:
            List[Goal]: 目标列表
        """
        return [g for g in self._goals.values() if g.status == status]

    def get_goals_by_timeframe(self, timeframe: GoalTimeframe) -> List[Goal]:
        """
        按时间框架获取目标

        Args:
            timeframe: 时间框架

        Returns:
            List[Goal]: 目标列表
        """
        return [g for g in self._goals.values() if g.timeframe == timeframe]

    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return self.get_goals_by_status(GoalStatus.ACTIVE)

    def get_priority_sorted_goals(self) -> List[Goal]:
        """
        获取按优先级排序的目标

        Returns:
            List[Goal]: 排序后的目标列表
        """
        return sorted(
            self._goals.values(),
            key=lambda g: (
                self.PRIORITY_SCORES.get(g.priority, 0),
                self.TIMEFRAME_WEIGHTS.get(g.timeframe, 1.0),
                g.progress
            ),
            reverse=True
        )

    def get_goal_hierarchy(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取目标层次结构

        Args:
            root_id: 根目标ID

        Returns:
            Dict[str, Any]: 层次结构
        """
        def build_tree(goal_id: str) -> Dict[str, Any]:
            goal = self._goals.get(goal_id)
            if not goal:
                return {}

            children = self._goal_hierarchy.get(goal_id, [])
            return {
                "goal": goal.model_dump(),
                "children": [build_tree(child_id) for child_id in children]
            }

        if root_id:
            return build_tree(root_id)

        # 返回所有根目标
        root_goals = [g for g in self._goals.values() if g.parent_id is None]
        return {
            "roots": [
                build_tree(g.goal_id) for g in root_goals
            ]
        }

    def abandon_goal(self, goal_id: str, reason: str = "") -> bool:
        """
        放弃目标

        Args:
            goal_id: 目标ID
            reason: 原因

        Returns:
            bool: 是否成功
        """
        goal = self._goals.get(goal_id)
        if not goal:
            return False

        goal.status = GoalStatus.ABANDONED
        goal.metadata["abandon_reason"] = reason
        goal.metadata["abandoned_at"] = time.time()

        # 递归放弃子目标
        for sub_id in goal.sub_goals:
            self.abandon_goal(sub_id, f"Parent goal abandoned: {reason}")

        logger.debug(f"Abandoned goal: {goal_id}, reason: {reason}")
        return True

    def check_deadlines(self) -> List[Goal]:
        """
        检查即将到期的目标

        Returns:
            List[Goal]: 即将到期的目标列表
        """
        now = time.time()
        urgent = []

        for goal in self._goals.values():
            if goal.deadline and goal.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]:
                time_left = goal.deadline - now
                if time_left < 86400:  # 24小时内
                    urgent.append(goal)

        return sorted(urgent, key=lambda g: g.deadline or float('inf'))

    def get_goal_statistics(self) -> Dict[str, Any]:
        """
        获取目标统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        status_counts = {}
        timeframe_counts = {}
        priority_counts = {}
        total_progress = 0.0

        for goal in self._goals.values():
            status_counts[goal.status.value] = status_counts.get(goal.status.value, 0) + 1
            timeframe_counts[goal.timeframe.value] = timeframe_counts.get(goal.timeframe.value, 0) + 1
            priority_counts[goal.priority.value] = priority_counts.get(goal.priority.value, 0) + 1
            total_progress += goal.progress

        total = len(self._goals)

        return {
            "total_goals": total,
            "status_distribution": status_counts,
            "timeframe_distribution": timeframe_counts,
            "priority_distribution": priority_counts,
            "average_progress": total_progress / total if total > 0 else 0,
            "achieved_rate": status_counts.get("achieved", 0) / total if total > 0 else 0,
            "active_goals": status_counts.get("active", 0),
        }

    def _update_parent_progress(self, parent_id: str) -> None:
        """更新父目标进度"""
        parent = self._goals.get(parent_id)
        if not parent or not parent.sub_goals:
            return

        sub_progress = []
        for sub_id in parent.sub_goals:
            sub = self._goals.get(sub_id)
            if sub:
                sub_progress.append(sub.progress)

        if sub_progress:
            avg_progress = sum(sub_progress) / len(sub_progress)
            parent.progress = avg_progress

            if parent.progress >= self.config.progress_threshold_for_achievement:
                parent.status = GoalStatus.ACHIEVED

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "goals": self.get_goal_statistics(),
            "progress_history_length": len(self._progress_history),
            "hierarchy_nodes": len(self._goal_hierarchy),
            "config": self.config.model_dump(),
        }
