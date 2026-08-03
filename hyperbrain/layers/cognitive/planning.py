"""
规划模块 (Planning Module)

实现多时间尺度的规划功能：
- 短期规划：当前任务分解
- 中期规划：阶段目标设定
- 长期规划：战略目标制定
- 动态规划调整
- 依赖关系管理
"""

import uuid
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.planning")


class PlanType(str, Enum):
    """规划类型枚举"""
    SHORT_TERM = "short_term"        # 短期规划
    MEDIUM_TERM = "medium_term"      # 中期规划
    LONG_TERM = "long_term"          # 长期规划


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"              # 待执行
    READY = "ready"                  # 就绪
    IN_PROGRESS = "in_progress"      # 执行中
    BLOCKED = "blocked"              # 被阻塞
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消


class DependencyType(str, Enum):
    """依赖类型枚举"""
    FINISH_TO_START = "finish_to_start"  # 完成到开始
    START_TO_START = "start_to_start"    # 开始到开始
    FINISH_TO_FINISH = "finish_to_finish"  # 完成到完成
    START_TO_FINISH = "start_to_finish"    # 开始到完成


class PlanTask(BaseModel):
    """计划任务模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    description: str = Field(default="")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    estimated_duration: float = Field(default=1.0)
    actual_duration: Optional[float] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    deadline: Optional[datetime] = Field(default=None)
    dependencies: List[str] = Field(default_factory=list)
    sub_tasks: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = Field(default=None)
    resources: List[str] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("priority", "progress")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class PlanDependency(BaseModel):
    """计划依赖模型"""
    dependency_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_task_id: str = Field(...)
    to_task_id: str = Field(...)
    dependency_type: DependencyType = Field(default=DependencyType.FINISH_TO_START)
    is_hard: bool = Field(default=True)
    lag: float = Field(default=0.0)


class Plan(BaseModel):
    """计划模型"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    description: str = Field(default="")
    plan_type: PlanType = Field(default=PlanType.SHORT_TERM)
    goals: List[str] = Field(default_factory=list)
    tasks: Dict[str, PlanTask] = Field(default_factory=dict)
    dependencies: List[PlanDependency] = Field(default_factory=list)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    status: str = Field(default="draft")
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class PlanAdjustment(BaseModel):
    """计划调整记录"""
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = Field(...)
    adjustment_type: str = Field(...)
    description: str = Field(default="")
    affected_tasks: List[str] = Field(default_factory=list)
    before_state: Dict[str, Any] = Field(default_factory=dict)
    after_state: Dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class PlanExecutionResult(BaseModel):
    """计划执行结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = Field(...)
    completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    skipped_tasks: List[str] = Field(default_factory=list)
    execution_time: float = Field(default=0.0)
    is_successful: bool = Field(default=False)
    lessons_learned: List[str] = Field(default_factory=list)


class Planner:
    """
    规划器

    实现多时间尺度的规划功能，支持任务分解和依赖管理。

    Attributes:
        plans: 计划库
        plan_history: 计划历史
        adjustment_history: 调整历史
    """

    def __init__(
        self,
        enable_logging: bool = True
    ):
        self.plans: Dict[str, Plan] = {}
        self.plan_history: List[Plan] = []
        self.adjustment_history: List[PlanAdjustment] = []
        self.enable_logging = enable_logging

        if enable_logging:
            logger.info("Planner initialized")

    def create_plan(
        self,
        name: str,
        description: str,
        plan_type: PlanType,
        goals: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Plan:
        """
        创建计划

        Args:
            name: 计划名称
            description: 计划描述
            plan_type: 计划类型
            goals: 目标列表
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Plan: 创建的计划
        """
        plan = Plan(
            name=name,
            description=description,
            plan_type=plan_type,
            goals=goals or [],
            start_time=start_time,
            end_time=end_time
        )

        self.plans[plan.plan_id] = plan
        logger.info(f"Created plan: {plan.plan_id}, type={plan_type.value}")
        return plan

    def add_task(
        self,
        plan_id: str,
        name: str,
        description: str = "",
        priority: float = 0.5,
        estimated_duration: float = 1.0,
        deadline: Optional[datetime] = None,
        parent_task_id: Optional[str] = None,
        resources: Optional[List[str]] = None
    ) -> Optional[PlanTask]:
        """
        向计划添加任务

        Args:
            plan_id: 计划ID
            name: 任务名称
            description: 任务描述
            priority: 优先级
            estimated_duration: 预估持续时间
            deadline: 截止时间
            parent_task_id: 父任务ID
            resources: 所需资源

        Returns:
            Optional[PlanTask]: 添加的任务
        """
        plan = self.plans.get(plan_id)
        if not plan:
            logger.error(f"Plan not found: {plan_id}")
            return None

        task = PlanTask(
            name=name,
            description=description,
            priority=priority,
            estimated_duration=estimated_duration,
            deadline=deadline,
            parent_task_id=parent_task_id,
            resources=resources or []
        )

        plan.tasks[task.task_id] = task

        if parent_task_id and parent_task_id in plan.tasks:
            plan.tasks[parent_task_id].sub_tasks.append(task.task_id)

        plan.updated_at = datetime.now()
        logger.debug(f"Added task {task.task_id} to plan {plan_id}")
        return task

    def add_dependency(
        self,
        plan_id: str,
        from_task_id: str,
        to_task_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        is_hard: bool = True,
        lag: float = 0.0
    ) -> Optional[PlanDependency]:
        """
        添加任务依赖

        Args:
            plan_id: 计划ID
            from_task_id: 前置任务ID
            to_task_id: 后置任务ID
            dependency_type: 依赖类型
            is_hard: 是否为硬依赖
            lag: 延迟时间

        Returns:
            Optional[PlanDependency]: 添加的依赖
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        if from_task_id not in plan.tasks or to_task_id not in plan.tasks:
            logger.error("Task not found in plan")
            return None

        if self._would_create_cycle(plan, from_task_id, to_task_id):
            logger.error("Dependency would create cycle")
            return None

        dep = PlanDependency(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=dependency_type,
            is_hard=is_hard,
            lag=lag
        )

        plan.dependencies.append(dep)
        plan.tasks[to_task_id].dependencies.append(from_task_id)

        self._update_task_status(plan, to_task_id)

        logger.debug(f"Added dependency: {from_task_id} -> {to_task_id}")
        return dep

    def decompose_task(
        self,
        plan_id: str,
        task_id: str,
        sub_task_names: List[str]
    ) -> List[PlanTask]:
        """
        任务分解

        Args:
            plan_id: 计划ID
            task_id: 任务ID
            sub_task_names: 子任务名称列表

        Returns:
            List[PlanTask]: 子任务列表
        """
        plan = self.plans.get(plan_id)
        if not plan or task_id not in plan.tasks:
            return []

        parent = plan.tasks[task_id]
        sub_tasks = []

        for name in sub_task_names:
            sub = PlanTask(
                name=name,
                description=f"子任务: {name}",
                priority=parent.priority,
                estimated_duration=parent.estimated_duration / max(len(sub_task_names), 1),
                parent_task_id=task_id
            )
            plan.tasks[sub.task_id] = sub
            parent.sub_tasks.append(sub.task_id)
            sub_tasks.append(sub)

        logger.info(f"Decomposed task {task_id} into {len(sub_tasks)} sub-tasks")
        return sub_tasks

    def get_execution_order(self, plan_id: str) -> List[str]:
        """
        获取任务执行顺序（拓扑排序）

        Args:
            plan_id: 计划ID

        Returns:
            List[str]: 任务ID执行顺序
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return []

        in_degree: Dict[str, int] = {tid: 0 for tid in plan.tasks}
        adjacency: Dict[str, List[str]] = {tid: [] for tid in plan.tasks}

        for dep in plan.dependencies:
            adjacency[dep.from_task_id].append(dep.to_task_id)
            in_degree[dep.to_task_id] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            queue.sort(key=lambda tid: plan.tasks[tid].priority, reverse=True)
            current = queue.pop(0)
            order.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(plan.tasks):
            logger.warning("Cycle detected in plan dependencies")
            remaining = [tid for tid in plan.tasks if tid not in order]
            order.extend(remaining)

        return order

    def calculate_critical_path(self, plan_id: str) -> List[str]:
        """
        计算关键路径

        Args:
            plan_id: 计划ID

        Returns:
            List[str]: 关键路径任务ID列表
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return []

        order = self.get_execution_order(plan_id)
        if not order:
            return []

        earliest_start: Dict[str, float] = {tid: 0.0 for tid in plan.tasks}
        earliest_finish: Dict[str, float] = {tid: 0.0 for tid in plan.tasks}

        for tid in order:
            task = plan.tasks[tid]
            es = 0.0
            for dep in plan.dependencies:
                if dep.to_task_id == tid:
                    pred_ef = earliest_finish.get(dep.from_task_id, 0.0)
                    es = max(es, pred_ef + dep.lag)
            earliest_start[tid] = es
            earliest_finish[tid] = es + task.estimated_duration

        max_duration = max(earliest_finish.values()) if earliest_finish else 0.0

        latest_start: Dict[str, float] = {tid: max_duration for tid in plan.tasks}
        latest_finish: Dict[str, float] = {tid: max_duration for tid in plan.tasks}

        for tid in reversed(order):
            task = plan.tasks[tid]
            lf = max_duration
            for dep in plan.dependencies:
                if dep.from_task_id == tid:
                    succ_ls = latest_start.get(dep.to_task_id, max_duration)
                    lf = min(lf, succ_ls - dep.lag)
            latest_finish[tid] = lf
            latest_start[tid] = lf - task.estimated_duration

        critical_path = [
            tid for tid in plan.tasks
            if abs(earliest_start[tid] - latest_start[tid]) < 0.001
        ]

        critical_path.sort(key=lambda tid: earliest_start[tid])
        return critical_path

    def adjust_plan(
        self,
        plan_id: str,
        adjustment_type: str,
        description: str,
        affected_tasks: List[str],
        changes: Dict[str, Any],
        reason: str = ""
    ) -> Optional[PlanAdjustment]:
        """
        调整计划

        Args:
            plan_id: 计划ID
            adjustment_type: 调整类型
            description: 调整描述
            affected_tasks: 受影响任务
            changes: 变更内容
            reason: 调整原因

        Returns:
            Optional[PlanAdjustment]: 调整记录
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        before_state = {}
        for tid in affected_tasks:
            if tid in plan.tasks:
                before_state[tid] = plan.tasks[tid].model_dump()

        self._apply_changes(plan, affected_tasks, changes)

        after_state = {}
        for tid in affected_tasks:
            if tid in plan.tasks:
                after_state[tid] = plan.tasks[tid].model_dump()

        adjustment = PlanAdjustment(
            plan_id=plan_id,
            adjustment_type=adjustment_type,
            description=description,
            affected_tasks=affected_tasks,
            before_state=before_state,
            after_state=after_state,
            reason=reason
        )

        self.adjustment_history.append(adjustment)
        plan.updated_at = datetime.now()

        logger.info(f"Adjusted plan {plan_id}: {adjustment_type}")
        return adjustment

    def execute_plan(
        self,
        plan_id: str,
        task_executor: Optional[Callable[[PlanTask], Dict[str, Any]]] = None
    ) -> PlanExecutionResult:
        """
        执行计划

        Args:
            plan_id: 计划ID
            task_executor: 任务执行函数

        Returns:
            PlanExecutionResult: 执行结果
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return PlanExecutionResult(
                plan_id=plan_id,
                is_successful=False,
                lessons_learned=["计划不存在"]
            )

        plan.status = "executing"
        order = self.get_execution_order(plan_id)

        completed = []
        failed = []
        skipped = []
        start_time = datetime.now()

        for tid in order:
            task = plan.tasks[tid]

            if task.status == TaskStatus.CANCELLED:
                skipped.append(tid)
                continue

            if task.status == TaskStatus.BLOCKED:
                deps_satisfied = all(
                    plan.tasks[d].status == TaskStatus.COMPLETED
                    for d in task.dependencies if d in plan.tasks
                )
                if not deps_satisfied:
                    skipped.append(tid)
                    continue

            task.status = TaskStatus.IN_PROGRESS
            task.start_time = datetime.now()

            if task_executor:
                result = task_executor(task)
                success = result.get("success", True)
            else:
                success = self._simulate_task_execution(task)

            task.end_time = datetime.now()

            if success:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                completed.append(tid)
            else:
                task.status = TaskStatus.FAILED
                failed.append(tid)

            self._update_dependent_tasks(plan, tid)

        execution_time = (datetime.now() - start_time).total_seconds()
        is_successful = len(failed) == 0 and len(skipped) == 0

        plan.status = "completed" if is_successful else "partial"
        plan.progress = len(completed) / max(len(plan.tasks), 1)

        lessons = []
        if is_successful:
            lessons.append("计划执行成功")
        else:
            if failed:
                lessons.append(f"{len(failed)} 个任务失败")
            if skipped:
                lessons.append(f"{len(skipped)} 个任务被跳过")

        result = PlanExecutionResult(
            plan_id=plan_id,
            completed_tasks=completed,
            failed_tasks=failed,
            skipped_tasks=skipped,
            execution_time=execution_time,
            is_successful=is_successful,
            lessons_learned=lessons
        )

        self.plan_history.append(plan)
        logger.info(f"Executed plan {plan_id}: success={is_successful}")
        return result

    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        获取计划进度

        Args:
            plan_id: 计划ID

        Returns:
            Dict[str, Any]: 进度信息
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}

        total = len(plan.tasks)
        if total == 0:
            return {"plan_id": plan_id, "progress": 0.0, "total_tasks": 0}

        status_counts: Dict[str, int] = {}
        for task in plan.tasks.values():
            s = task.status.value
            status_counts[s] = status_counts.get(s, 0) + 1

        completed = status_counts.get("completed", 0)
        progress = completed / total

        return {
            "plan_id": plan_id,
            "plan_name": plan.name,
            "progress": progress,
            "total_tasks": total,
            "completed_tasks": completed,
            "status_breakdown": status_counts,
            "critical_path": self.calculate_critical_path(plan_id)
        }

    def get_ready_tasks(self, plan_id: str) -> List[PlanTask]:
        """
        获取就绪的任务

        Args:
            plan_id: 计划ID

        Returns:
            List[PlanTask]: 就绪任务列表
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return []

        ready = []
        for task in plan.tasks.values():
            if task.status == TaskStatus.PENDING:
                deps_satisfied = all(
                    plan.tasks[d].status == TaskStatus.COMPLETED
                    for d in task.dependencies if d in plan.tasks
                )
                if deps_satisfied:
                    task.status = TaskStatus.READY
                    ready.append(task)

        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready

    def cancel_task(self, plan_id: str, task_id: str) -> bool:
        """
        取消任务

        Args:
            plan_id: 计划ID
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        plan = self.plans.get(plan_id)
        if not plan or task_id not in plan.tasks:
            return False

        plan.tasks[task_id].status = TaskStatus.CANCELLED
        self._update_dependent_tasks(plan, task_id)
        plan.updated_at = datetime.now()

        logger.info(f"Cancelled task {task_id} in plan {plan_id}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_plans = len(self.plans)
        total_adjustments = len(self.adjustment_history)

        type_counts: Dict[str, int] = {}
        for plan in self.plans.values():
            pt = plan.plan_type.value
            type_counts[pt] = type_counts.get(pt, 0) + 1

        total_tasks = sum(len(p.tasks) for p in self.plans.values())
        completed_tasks = sum(
            1
            for p in self.plans.values()
            for t in p.tasks.values()
            if t.status == TaskStatus.COMPLETED
        )

        return {
            "total_plans": total_plans,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "total_adjustments": total_adjustments,
            "plan_type_distribution": type_counts,
            "completion_rate": completed_tasks / max(total_tasks, 1)
        }

    def _would_create_cycle(
        self,
        plan: Plan,
        from_id: str,
        to_id: str
    ) -> bool:
        """检查是否会创建循环依赖"""
        visited: Set[str] = set()
        stack = [to_id]

        while stack:
            current = stack.pop()
            if current == from_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            for dep in plan.dependencies:
                if dep.from_task_id == current:
                    stack.append(dep.to_task_id)

        return False

    def _update_task_status(self, plan: Plan, task_id: str) -> None:
        """更新任务状态"""
        task = plan.tasks.get(task_id)
        if not task:
            return

        if task.status != TaskStatus.PENDING:
            return

        for dep_id in task.dependencies:
            dep_task = plan.tasks.get(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.BLOCKED
                return

    def _update_dependent_tasks(self, plan: Plan, completed_task_id: str) -> None:
        """更新依赖任务的状态"""
        for dep in plan.dependencies:
            if dep.from_task_id == completed_task_id:
                self._update_task_status(plan, dep.to_task_id)

    def _apply_changes(
        self,
        plan: Plan,
        affected_tasks: List[str],
        changes: Dict[str, Any]
    ) -> None:
        """应用变更"""
        for tid in affected_tasks:
            if tid not in plan.tasks:
                continue

            task = plan.tasks[tid]
            if "priority" in changes:
                task.priority = max(0.0, min(1.0, changes["priority"]))
            if "deadline" in changes:
                task.deadline = changes["deadline"]
            if "estimated_duration" in changes:
                task.estimated_duration = changes["estimated_duration"]
            if "status" in changes:
                task.status = TaskStatus(changes["status"])

    def _simulate_task_execution(self, task: PlanTask) -> bool:
        """模拟任务执行"""
        return task.priority >= 0.1
