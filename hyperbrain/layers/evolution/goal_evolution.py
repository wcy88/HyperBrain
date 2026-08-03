"""
目标进化模块 (Goal Evolution Module)

根据经验和环境变化调整目标，动态调整目标优先级，
发现新目标，淘汰过时目标，评估目标达成情况，优化目标体系。

功能：
1. 目标优先级动态调整
2. 新目标发现
3. 过时目标淘汰
4. 目标达成评估
5. 目标体系优化
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict, deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("evolution.goal_evolution")


class GoalStatus(str, Enum):
    """目标状态"""
    ACTIVE = "active"           # 活跃
    PENDING = "pending"         # 待处理
    IN_PROGRESS = "in_progress" # 进行中
    ACHIEVED = "achieved"       # 已达成
    FAILED = "failed"           # 已失败
    ABANDONED = "abandoned"     # 已放弃
    OBSOLETE = "obsolete"       # 已过时


class GoalPriority(str, Enum):
    """目标优先级"""
    CRITICAL = 5                # 关键
    HIGH = 4                    # 高
    MEDIUM = 3                  # 中
    LOW = 2                     # 低
    TRIVIAL = 1                 # 轻微


class SystemGoal(BaseModel):
    """系统目标"""
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="目标名称")
    description: str = Field(..., description="目标描述")
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    priority: int = Field(default=GoalPriority.MEDIUM, ge=1, le=5)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deadline: Optional[datetime] = Field(default=None)
    parent_goal_id: Optional[str] = Field(default=None)
    sub_goals: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)
    failure_criteria: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    achievement_history: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("priority", "progress")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0 if isinstance(v, float) else 5, v))


class GoalEvaluation(BaseModel):
    """目标评估"""
    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str = Field(...)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timeliness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    difficulty_assessment: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.8, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    notes: str = Field(default="")

    @field_validator("completion_rate", "quality_score", "timeliness_score",
                     "difficulty_assessment", "relevance_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class GoalAdjustment(BaseModel):
    """目标调整"""
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str = Field(...)
    adjustment_type: str = Field(..., description="调整类型")
    old_value: Any = Field(default=None)
    new_value: Any = Field(default=None)
    reason: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    triggered_by: str = Field(default="", description="触发原因")


class GoalEvolutionReport(BaseModel):
    """目标进化报告"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    total_goals: int = Field(default=0)
    achieved_goals: int = Field(default=0)
    failed_goals: int = Field(default=0)
    new_goals: List[SystemGoal] = Field(default_factory=list)
    abandoned_goals: List[SystemGoal] = Field(default_factory=list)
    priority_changes: List[GoalAdjustment] = Field(default_factory=list)
    overall_progress: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)
    summary: str = Field(default="")


class GoalEvolutionConfig(BaseModel):
    """目标进化配置"""
    evaluation_interval: float = Field(default=86400.0, description="评估间隔(秒)")
    max_active_goals: int = Field(default=20)
    min_goal_lifetime_days: int = Field(default=1)
    auto_prioritize: bool = Field(default=True)
    enable_goal_discovery: bool = Field(default=True)
    enable_goal_pruning: bool = Field(default=True)
    relevance_decay_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    achievement_threshold: float = Field(default=0.95, ge=0.0, le=1.0)


class GoalEvolver:
    """
    目标进化系统

    根据经验和环境变化调整目标体系，动态优化目标优先级和结构。

    Attributes:
        config: 进化配置
        goals: 目标库
        evaluations: 评估历史
        adjustments: 调整历史
    """

    def __init__(self, config: Optional[GoalEvolutionConfig] = None):
        self.config = config or GoalEvolutionConfig()
        self._goals: Dict[str, SystemGoal] = {}
        self._evaluations: Dict[str, List[GoalEvaluation]] = defaultdict(list)
        self._adjustments: List[GoalAdjustment] = []
        self._last_evaluation_time: Optional[datetime] = None
        self._evolution_callbacks: List[Callable[[GoalEvolutionReport], None]] = []
        logger.info("GoalEvolver initialized")

    # ========== 目标管理 ==========

    def add_goal(
        self,
        name: str,
        description: str,
        priority: int = GoalPriority.MEDIUM,
        deadline: Optional[datetime] = None,
        parent_goal_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> SystemGoal:
        """
        添加新目标

        Args:
            name: 目标名称
            description: 目标描述
            priority: 优先级 (1-5)
            deadline: 截止日期
            parent_goal_id: 父目标ID
            dependencies: 依赖目标ID列表
            success_criteria: 成功标准
            tags: 标签

        Returns:
            SystemGoal: 创建的目标
        """
        goal = SystemGoal(
            name=name,
            description=description,
            priority=max(1, min(5, int(priority))),
            deadline=deadline,
            parent_goal_id=parent_goal_id,
            dependencies=dependencies or [],
            success_criteria=success_criteria or [],
            tags=tags or []
        )

        self._goals[goal.goal_id] = goal

        # 更新父目标的子目标列表
        if parent_goal_id and parent_goal_id in self._goals:
            self._goals[parent_goal_id].sub_goals.append(goal.goal_id)

        logger.info(f"Added goal: {name} (priority={priority})")
        return goal

    def update_goal_progress(
        self,
        goal_id: str,
        progress: float,
        notes: str = ""
    ) -> bool:
        """
        更新目标进度

        Args:
            goal_id: 目标ID
            progress: 进度 (0-1)
            notes: 备注

        Returns:
            bool: 是否成功
        """
        if goal_id not in self._goals:
            return False

        goal = self._goals[goal_id]
        old_progress = goal.progress
        goal.progress = max(0.0, min(1.0, progress))
        goal.updated_at = datetime.now()

        # 检查是否达成
        if goal.progress >= self.config.achievement_threshold and old_progress < self.config.achievement_threshold:
            goal.status = GoalStatus.ACHIEVED
            goal.achievement_history.append({
                "event": "achieved",
                "timestamp": datetime.now().isoformat(),
                "notes": notes
            })
            logger.info(f"Goal achieved: {goal.name}")

        return True

    def remove_goal(self, goal_id: str, reason: str = "") -> bool:
        """
        移除目标

        Args:
            goal_id: 目标ID
            reason: 原因

        Returns:
            bool: 是否成功
        """
        if goal_id not in self._goals:
            return False

        goal = self._goals[goal_id]
        goal.status = GoalStatus.ABANDONED
        goal.updated_at = datetime.now()

        # 从父目标中移除
        if goal.parent_goal_id and goal.parent_goal_id in self._goals:
            parent = self._goals[goal.parent_goal_id]
            if goal_id in parent.sub_goals:
                parent.sub_goals.remove(goal_id)

        logger.info(f"Removed goal: {goal.name}, reason={reason}")
        return True

    # ========== 优先级调整 ==========

    def adjust_priority(
        self,
        goal_id: str,
        new_priority: int,
        reason: str = ""
    ) -> bool:
        """
        调整目标优先级

        Args:
            goal_id: 目标ID
            new_priority: 新优先级
            reason: 原因

        Returns:
            bool: 是否成功
        """
        if goal_id not in self._goals:
            return False

        goal = self._goals[goal_id]
        old_priority = goal.priority
        goal.priority = max(1, min(5, new_priority))
        goal.updated_at = datetime.now()

        adjustment = GoalAdjustment(
            goal_id=goal_id,
            adjustment_type="priority",
            old_value=old_priority,
            new_value=goal.priority,
            reason=reason,
            triggered_by="manual" if reason else "auto"
        )
        self._adjustments.append(adjustment)

        logger.info(f"Priority adjusted: {goal.name} {old_priority} -> {goal.priority}")
        return True

    def auto_prioritize(self) -> List[GoalAdjustment]:
        """
        自动调整优先级

        Returns:
            List[GoalAdjustment]: 调整记录
        """
        if not self.config.auto_prioritize:
            return []

        adjustments = []
        now = datetime.now()

        for goal in self._goals.values():
            if goal.status not in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS, GoalStatus.PENDING]:
                continue

            old_priority = goal.priority
            new_priority = old_priority

            # 基于截止日期调整
            if goal.deadline:
                time_remaining = (goal.deadline - now).total_seconds()
                if time_remaining < 86400:  # 少于1天
                    new_priority = min(5, old_priority + 2)
                elif time_remaining < 604800:  # 少于1周
                    new_priority = min(5, old_priority + 1)

            # 基于进度调整
            if goal.progress > 0.8 and goal.progress < 1.0:
                # 接近完成，保持或略微提高
                new_priority = max(old_priority, 3)

            # 基于依赖关系调整
            if goal.dependencies:
                blocked = any(
                    self._goals.get(dep_id, SystemGoal(name="")).status != GoalStatus.ACHIEVED
                    for dep_id in goal.dependencies
                )
                if blocked:
                    new_priority = max(1, old_priority - 1)

            if new_priority != old_priority:
                goal.priority = new_priority
                adjustment = GoalAdjustment(
                    goal_id=goal.goal_id,
                    adjustment_type="priority",
                    old_value=old_priority,
                    new_value=new_priority,
                    reason="自动优先级调整",
                    triggered_by="auto_prioritize"
                )
                self._adjustments.append(adjustment)
                adjustments.append(adjustment)

        logger.info(f"Auto-prioritized {len(adjustments)} goals")
        return adjustments

    # ========== 目标发现 ==========

    def discover_goals(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> List[SystemGoal]:
        """
        发现新目标

        基于当前状态和环境上下文发现潜在的新目标。

        Args:
            context: 环境上下文

        Returns:
            List[SystemGoal]: 新发现的目标
        """
        if not self.config.enable_goal_discovery:
            return []

        new_goals = []
        context = context or {}

        # 基于能力差距发现目标
        capability_gaps = context.get("capability_gaps", [])
        for gap in capability_gaps:
            dimension = gap.get("dimension", "")
            gap_size = gap.get("gap_size", 0.0)

            if gap_size > 0.3:
                goal = self.add_goal(
                    name=f"提升 {dimension} 能力",
                    description=f"缩小 {dimension} 能力差距，当前差距 {gap_size:.1%}",
                    priority=min(5, max(1, int(gap_size * 5))),
                    success_criteria=[
                        f"{dimension} 能力评分提升 20%",
                        "完成相关练习和评估"
                    ],
                    tags=["capability", "improvement", dimension]
                )
                new_goals.append(goal)

        # 基于错误模式发现目标
        error_patterns = context.get("error_patterns", [])
        for pattern in error_patterns:
            if pattern.get("frequency", 0) > 3:
                goal = self.add_goal(
                    name=f"消除错误模式: {pattern.get('name', '')}",
                    description=f"解决频繁出现的 {pattern.get('category', '')} 错误",
                    priority=4,
                    success_criteria=[
                        "错误频率降低 50%",
                        "建立预防机制"
                    ],
                    tags=["error", "prevention", pattern.get("category", "")]
                )
                new_goals.append(goal)

        # 基于反思洞察发现目标
        insights = context.get("reflection_insights", [])
        for insight in insights:
            if insight.get("severity") == "high":
                goal = self.add_goal(
                    name=f"解决: {insight.get('title', '')}",
                    description=insight.get("description", ""),
                    priority=5,
                    success_criteria=[
                        "问题不再出现",
                        "建立长期解决方案"
                    ],
                    tags=["reflection", "improvement"]
                )
                new_goals.append(goal)

        logger.info(f"Discovered {len(new_goals)} new goals")
        return new_goals

    # ========== 目标淘汰 ==========

    def prune_goals(self) -> List[SystemGoal]:
        """
        淘汰过时目标

        Returns:
            List[SystemGoal]: 被淘汰的目标
        """
        if not self.config.enable_goal_pruning:
            return []

        pruned = []
        now = datetime.now()

        for goal in list(self._goals.values()):
            should_prune = False
            reason = ""

            # 检查是否已过时
            if goal.status == GoalStatus.ACHIEVED:
                # 已达成目标，保留一段时间后可清理
                if (now - goal.updated_at).days > 30:
                    should_prune = True
                    reason = "已达成且超过30天"

            # 检查相关性衰减
            if goal.status == GoalStatus.ACTIVE:
                age_days = (now - goal.created_at).days
                relevance = 1.0 - (age_days * self.config.relevance_decay_rate)
                if relevance < 0.2:
                    should_prune = True
                    reason = "相关性过低"

            # 检查是否已过期
            if goal.deadline and now > goal.deadline + timedelta(days=7):
                if goal.status != GoalStatus.ACHIEVED:
                    goal.status = GoalStatus.FAILED
                    should_prune = True
                    reason = "已过期超过7天"

            # 检查活跃目标数量限制
            active_count = sum(1 for g in self._goals.values() if g.status == GoalStatus.ACTIVE)
            if active_count > self.config.max_active_goals:
                # 标记最低优先级的非关键目标
                if goal.priority <= 2 and goal.status == GoalStatus.ACTIVE:
                    should_prune = True
                    reason = "超出活跃目标数量限制"

            if should_prune:
                goal.status = GoalStatus.OBSOLETE
                pruned.append(goal)
                logger.info(f"Pruned goal: {goal.name}, reason={reason}")

        return pruned

    # ========== 目标评估 ==========

    def evaluate_goal(self, goal_id: str) -> Optional[GoalEvaluation]:
        """
        评估单个目标

        Args:
            goal_id: 目标ID

        Returns:
            Optional[GoalEvaluation]: 评估结果
        """
        if goal_id not in self._goals:
            return None

        goal = self._goals[goal_id]
        now = datetime.now()

        # 计算完成率
        completion_rate = goal.progress

        # 计算质量分（基于成功标准达成情况）
        quality_score = completion_rate  # 简化计算

        # 计算时效性
        timeliness_score = 1.0
        if goal.deadline:
            if now > goal.deadline:
                timeliness_score = max(0.0, 1.0 - (now - goal.deadline).days / 7)
            else:
                timeliness_score = 1.0

        # 评估难度
        evaluations = self._evaluations.get(goal_id, [])
        if evaluations:
            avg_difficulty = sum(e.difficulty_assessment for e in evaluations) / len(evaluations)
            difficulty = min(1.0, avg_difficulty * 1.1)  # 略微上调
        else:
            difficulty = 0.5

        # 相关性评估
        relevance = 0.8  # 默认较高
        if goal.status == GoalStatus.OBSOLETE:
            relevance = 0.1

        evaluation = GoalEvaluation(
            goal_id=goal_id,
            completion_rate=completion_rate,
            quality_score=quality_score,
            timeliness_score=timeliness_score,
            difficulty_assessment=difficulty,
            relevance_score=relevance,
            notes=f"Goal status: {goal.status.value}"
        )

        self._evaluations[goal_id].append(evaluation)
        return evaluation

    def evaluate_all_goals(self) -> Dict[str, GoalEvaluation]:
        """
        评估所有活跃目标

        Returns:
            Dict[str, GoalEvaluation]: 评估结果字典
        """
        results = {}
        for goal_id, goal in self._goals.items():
            if goal.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]:
                evaluation = self.evaluate_goal(goal_id)
                if evaluation:
                    results[goal_id] = evaluation

        self._last_evaluation_time = datetime.now()
        return results

    # ========== 目标体系优化 ==========

    def optimize_goal_system(self) -> GoalEvolutionReport:
        """
        优化目标体系

        Returns:
            GoalEvolutionReport: 进化报告
        """
        now = datetime.now()
        period_start = now - timedelta(seconds=self.config.evaluation_interval)

        logger.info("Starting goal system optimization")

        # 自动优先级调整
        priority_changes = self.auto_prioritize()

        # 发现新目标
        context = self._build_discovery_context()
        new_goals = self.discover_goals(context)

        # 淘汰过时目标
        abandoned_goals = self.prune_goals()

        # 评估所有目标
        evaluations = self.evaluate_all_goals()

        # 计算统计
        total_goals = len(self._goals)
        achieved = sum(1 for g in self._goals.values() if g.status == GoalStatus.ACHIEVED)
        failed = sum(1 for g in self._goals.values() if g.status == GoalStatus.FAILED)

        # 计算整体进度
        active_goals = [g for g in self._goals.values() if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]]
        overall_progress = (
            sum(g.progress for g in active_goals) / len(active_goals)
            if active_goals else 0.0
        )

        # 生成建议
        recommendations = self._generate_recommendations()

        # 生成总结
        summary = (
            f"目标体系优化完成。"
            f"总目标: {total_goals}, 已达成: {achieved}, 失败: {failed}。"
            f"新发现: {len(new_goals)} 个, 淘汰: {len(abandoned_goals)} 个。"
            f"整体进度: {overall_progress:.1%}。"
        )

        report = GoalEvolutionReport(
            period_start=period_start,
            period_end=now,
            total_goals=total_goals,
            achieved_goals=achieved,
            failed_goals=failed,
            new_goals=new_goals,
            abandoned_goals=abandoned_goals,
            priority_changes=priority_changes,
            overall_progress=overall_progress,
            recommendations=recommendations,
            summary=summary
        )

        # 触发回调
        for callback in self._evolution_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.warning(f"Goal evolution callback failed: {e}")

        logger.info("Goal system optimization completed")
        return report

    def auto_evolve(self) -> Optional[GoalEvolutionReport]:
        """
        自动进化（检查时间间隔）

        Returns:
            Optional[GoalEvolutionReport]: 进化报告
        """
        now = datetime.now()
        if (self._last_evaluation_time is None or
            (now - self._last_evaluation_time).total_seconds() >= self.config.evaluation_interval):
            return self.optimize_goal_system()
        return None

    def _build_discovery_context(self) -> Dict[str, Any]:
        """构建目标发现上下文"""
        context = {}

        # 收集活跃目标的标签
        active_tags = set()
        for goal in self._goals.values():
            if goal.status == GoalStatus.ACTIVE:
                active_tags.update(goal.tags)

        context["active_tags"] = list(active_tags)

        # 收集已达成目标的类型
        achieved_categories = defaultdict(int)
        for goal in self._goals.values():
            if goal.status == GoalStatus.ACHIEVED:
                for tag in goal.tags:
                    achieved_categories[tag] += 1

        context["achieved_categories"] = dict(achieved_categories)

        return context

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        active_goals = [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]
        if len(active_goals) > self.config.max_active_goals:
            recommendations.append(
                f"活跃目标数量({len(active_goals)})超过限制，建议聚焦核心目标"
            )

        stalled_goals = [g for g in active_goals if g.progress < 0.1]
        if len(stalled_goals) > 3:
            recommendations.append(
                f"有 {len(stalled_goals)} 个目标进展缓慢，建议重新评估或分解"
            )

        high_priority_inactive = [
            g for g in self._goals.values()
            if g.priority >= 4 and g.status == GoalStatus.PENDING
        ]
        if high_priority_inactive:
            recommendations.append(
                f"有 {len(high_priority_inactive)} 个高优先级目标待启动"
            )

        if not recommendations:
            recommendations.append("目标体系状态良好")

        return recommendations

    # ========== 回调注册 ==========

    def register_evolution_callback(
        self,
        callback: Callable[[GoalEvolutionReport], None]
    ) -> None:
        """
        注册进化回调

        Args:
            callback: 回调函数
        """
        self._evolution_callbacks.append(callback)
        logger.debug("Registered goal evolution callback")

    # ========== 查询接口 ==========

    def get_goal(self, goal_id: str) -> Optional[SystemGoal]:
        """
        获取目标

        Args:
            goal_id: 目标ID

        Returns:
            Optional[SystemGoal]: 目标
        """
        return self._goals.get(goal_id)

    def get_active_goals(self) -> List[SystemGoal]:
        """
        获取活跃目标

        Returns:
            List[SystemGoal]: 活跃目标列表
        """
        return sorted(
            [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE],
            key=lambda g: (-g.priority, -g.progress)
        )

    def get_goals_by_status(self, status: GoalStatus) -> List[SystemGoal]:
        """
        按状态获取目标

        Args:
            status: 目标状态

        Returns:
            List[SystemGoal]: 目标列表
        """
        return [g for g in self._goals.values() if g.status == status]

    def get_goals_by_tag(self, tag: str) -> List[SystemGoal]:
        """
        按标签获取目标

        Args:
            tag: 标签

        Returns:
            List[SystemGoal]: 目标列表
        """
        return [g for g in self._goals.values() if tag in g.tags]

    def get_goal_tree(self, root_goal_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取目标树

        Args:
            root_goal_id: 根目标ID（None则获取所有顶层目标）

        Returns:
            Dict[str, Any]: 目标树结构
        """
        if root_goal_id:
            goal = self._goals.get(root_goal_id)
            if not goal:
                return {}
            return self._build_tree_node(goal)

        # 获取所有顶层目标
        root_goals = [g for g in self._goals.values() if g.parent_goal_id is None]
        return {
            "roots": [self._build_tree_node(g) for g in root_goals]
        }

    def _build_tree_node(self, goal: SystemGoal) -> Dict[str, Any]:
        """构建树节点"""
        return {
            "goal_id": goal.goal_id,
            "name": goal.name,
            "status": goal.status.value,
            "priority": goal.priority,
            "progress": goal.progress,
            "sub_goals": [
                self._build_tree_node(self._goals[gid])
                for gid in goal.sub_goals
                if gid in self._goals
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        status_counts = defaultdict(int)
        for goal in self._goals.values():
            status_counts[goal.status.value] += 1

        priority_counts = defaultdict(int)
        for goal in self._goals.values():
            priority_counts[goal.priority] += 1

        return {
            "total_goals": len(self._goals),
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts),
            "active_goals": len(self.get_active_goals()),
            "achieved_goals": len(self.get_goals_by_status(GoalStatus.ACHIEVED)),
            "total_evaluations": sum(len(e) for e in self._evaluations.values()),
            "total_adjustments": len(self._adjustments),
            "last_evaluation": self._last_evaluation_time.isoformat() if self._last_evaluation_time else None
        }

    def reset(self) -> None:
        """重置所有状态"""
        self._goals.clear()
        self._evaluations.clear()
        self._adjustments.clear()
        self._last_evaluation_time = None
        logger.info("GoalEvolver reset")
