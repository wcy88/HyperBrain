"""
任务执行模块 (Task Execution)

负责任务的分解、调度、执行和结果收集。

功能：
- 执行具体的任务和操作
- 任务分解和调度
- 并行和串行执行
- 任务状态跟踪
- 任务结果收集
"""

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Union, Set, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.task")


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消
    TIMEOUT = "timeout"         # 超时
    RETRYING = "retrying"       # 重试中


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"   # 串行
    PARALLEL = "parallel"       # 并行
    PIPELINE = "pipeline"       # 流水线


class TaskPriority(int, Enum):
    """任务优先级"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskResult(BaseModel):
    """任务结果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count
        }


class ExecutableTask(BaseModel):
    """可执行任务"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 执行函数和参数
    func: Optional[Callable] = Field(default=None, exclude=True)
    args: tuple = Field(default_factory=tuple, exclude=True)
    kwargs: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    # 执行配置
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    
    # 依赖关系
    dependencies: List[str] = Field(default_factory=list)
    
    # 子任务
    subtasks: List["ExecutableTask"] = Field(default_factory=list)
    
    # 结果
    result: Optional[TaskResult] = None
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_ready(self) -> bool:
        """检查任务是否准备好执行（依赖已完成）"""
        return self.status == TaskStatus.PENDING
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, 
                               TaskStatus.CANCELLED, TaskStatus.TIMEOUT)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "execution_mode": self.execution_mode.value,
            "dependencies": self.dependencies,
            "subtask_count": len(self.subtasks),
            "result": self.result.to_dict() if self.result else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class TaskBatch(BaseModel):
    """任务批次"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: List[ExecutableTask] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    
    def add_task(self, task: ExecutableTask) -> None:
        """添加任务"""
        self.tasks.append(task)
    
    def get_ready_tasks(self) -> List[ExecutableTask]:
        """获取准备好的任务"""
        return [t for t in self.tasks if t.is_ready()]
    
    def get_completed_tasks(self) -> List[ExecutableTask]:
        """获取已完成的任务"""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[ExecutableTask]:
        """获取失败的任务"""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]
    
    def is_complete(self) -> bool:
        """检查批次是否全部完成"""
        return all(t.is_completed() for t in self.tasks)
    
    def get_progress(self) -> float:
        """获取进度"""
        if not self.tasks:
            return 1.0
        completed = sum(1 for t in self.tasks if t.is_completed())
        return completed / len(self.tasks)


class TaskExecutor:
    """
    任务执行器
    
    负责任务的执行、调度和结果收集。
    """
    
    def __init__(self):
        self.config = get_config().execution
        self._tasks: Dict[str, ExecutableTask] = {}
        self._batches: Dict[str, TaskBatch] = {}
        self._execution_history: List[Dict[str, Any]] = []
        logger.info("TaskExecutor initialized")
    
    def create_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 30.0,
        max_retries: int = 3,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutableTask:
        """
        创建任务
        
        Args:
            name: 任务名称
            func: 执行函数
            args: 位置参数
            kwargs: 关键字参数
            description: 描述
            priority: 优先级
            timeout: 超时时间
            max_retries: 最大重试次数
            dependencies: 依赖任务ID列表
            metadata: 元数据
            
        Returns:
            ExecutableTask: 创建的任务
        """
        task = ExecutableTask(
            name=name,
            description=description,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout_seconds=timeout,
            max_retries=max_retries,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self._tasks[task.id] = task
        logger.debug(f"Created task: {name} (id={task.id})")
        return task
    
    async def execute(self, task_id: str) -> TaskResult:
        """
        执行单个任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskResult: 执行结果
        """
        task = self._tasks.get(task_id)
        if not task:
            return TaskResult(
                success=False,
                error=f"Task not found: {task_id}"
            )
        
        if not task.func:
            return TaskResult(
                success=False,
                error=f"Task has no executable function: {task_id}"
            )
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= task.max_retries:
            try:
                logger.debug(f"Executing task: {task.name} (attempt {retry_count + 1})")
                
                # 执行函数
                if asyncio.iscoroutinefunction(task.func):
                    result_data = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout_seconds
                    )
                else:
                    # 同步函数在线程池中执行
                    loop = asyncio.get_event_loop()
                    result_data = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: task.func(*task.args, **task.kwargs)),
                        timeout=task.timeout_seconds
                    )
                
                execution_time = (time.time() - start_time) * 1000
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = TaskResult(
                    success=True,
                    data=result_data,
                    execution_time_ms=execution_time,
                    retry_count=retry_count
                )
                
                self._record_execution(task)
                logger.info(f"Task completed: {task.name} in {execution_time:.2f}ms")
                return task.result
                
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Task timeout: {task.name} (attempt {retry_count})")
                
                if retry_count > task.max_retries:
                    task.status = TaskStatus.TIMEOUT
                    task.completed_at = datetime.now()
                    task.result = TaskResult(
                        success=False,
                        error="Task timed out",
                        execution_time_ms=(time.time() - start_time) * 1000,
                        retry_count=retry_count
                    )
                    self._record_execution(task)
                    return task.result
                
                await asyncio.sleep(task.retry_delay_seconds)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Task error: {task.name} - {e} (attempt {retry_count})")
                
                if retry_count > task.max_retries:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.result = TaskResult(
                        success=False,
                        error=str(e),
                        execution_time_ms=(time.time() - start_time) * 1000,
                        retry_count=retry_count
                    )
                    self._record_execution(task)
                    return task.result
                
                task.status = TaskStatus.RETRYING
                await asyncio.sleep(task.retry_delay_seconds)
                task.status = TaskStatus.RUNNING
        
        return TaskResult(success=False, error="Max retries exceeded")
    
    async def execute_batch(
        self,
        batch_id: str,
        mode: Optional[ExecutionMode] = None
    ) -> Dict[str, TaskResult]:
        """
        执行批次任务
        
        Args:
            batch_id: 批次ID
            mode: 执行模式
            
        Returns:
            Dict[str, TaskResult]: 任务结果映射
        """
        batch = self._batches.get(batch_id)
        if not batch:
            return {}
        
        mode = mode or batch.execution_mode
        
        if mode == ExecutionMode.SEQUENTIAL:
            return await self._execute_sequential(batch)
        elif mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(batch)
        elif mode == ExecutionMode.PIPELINE:
            return await self._execute_pipeline(batch)
        else:
            return await self._execute_sequential(batch)
    
    async def _execute_sequential(self, batch: TaskBatch) -> Dict[str, TaskResult]:
        """串行执行"""
        results = {}
        
        # 按优先级排序
        sorted_tasks = sorted(batch.tasks, key=lambda t: t.priority.value)
        
        for task in sorted_tasks:
            result = await self.execute(task.id)
            results[task.id] = result
            
            # 如果任务失败且是关键任务，停止执行
            if not result.success and task.priority == TaskPriority.CRITICAL:
                logger.warning(f"Critical task failed, stopping batch: {batch.id}")
                break
        
        return results
    
    async def _execute_parallel(self, batch: TaskBatch) -> Dict[str, TaskResult]:
        """并行执行"""
        # 检查依赖关系
        ready_tasks = self._get_ready_tasks(batch)
        
        # 创建执行任务
        tasks_to_run = [
            self.execute(task.id) for task in ready_tasks
        ]
        
        # 并行执行
        results_list = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        
        results = {}
        for task, result in zip(ready_tasks, results_list):
            if isinstance(result, Exception):
                results[task.id] = TaskResult(success=False, error=str(result))
            else:
                results[task.id] = result
        
        return results
    
    async def _execute_pipeline(self, batch: TaskBatch) -> Dict[str, TaskResult]:
        """流水线执行"""
        results = {}
        completed_ids: Set[str] = set()
        
        while not batch.is_complete():
            # 获取可以执行的任务（依赖已满足）
            ready_tasks = [
                t for t in batch.tasks 
                if t.is_ready() and all(dep in completed_ids for dep in t.dependencies)
            ]
            
            if not ready_tasks:
                # 检查是否有死锁
                pending_tasks = [t for t in batch.tasks if not t.is_completed()]
                if pending_tasks and not ready_tasks:
                    logger.error("Task dependency deadlock detected")
                    break
                await asyncio.sleep(0.1)
                continue
            
            # 并行执行就绪任务
            tasks_to_run = [self.execute(t.id) for t in ready_tasks]
            batch_results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            for task, result in zip(ready_tasks, batch_results):
                if isinstance(result, Exception):
                    results[task.id] = TaskResult(success=False, error=str(result))
                else:
                    results[task.id] = result
                completed_ids.add(task.id)
        
        return results
    
    def _get_ready_tasks(self, batch: TaskBatch) -> List[ExecutableTask]:
        """获取准备好的任务"""
        return [t for t in batch.tasks if t.is_ready()]
    
    def create_batch(
        self,
        name: str,
        tasks: Optional[List[ExecutableTask]] = None,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    ) -> TaskBatch:
        """
        创建任务批次
        
        Args:
            name: 批次名称
            tasks: 任务列表
            execution_mode: 执行模式
            
        Returns:
            TaskBatch: 任务批次
        """
        batch = TaskBatch(
            name=name,
            tasks=tasks or [],
            execution_mode=execution_mode
        )
        
        self._batches[batch.id] = batch
        
        # 注册所有任务
        for task in batch.tasks:
            self._tasks[task.id] = task
        
        logger.debug(f"Created batch: {name} with {len(batch.tasks)} tasks")
        return batch
    
    def decompose_task(
        self,
        parent_task: ExecutableTask,
        subtask_functions: List[Tuple[str, Callable, tuple, Dict[str, Any]]]
    ) -> ExecutableTask:
        """
        将任务分解为子任务
        
        Args:
            parent_task: 父任务
            subtask_functions: [(name, func, args, kwargs), ...]
            
        Returns:
            ExecutableTask: 更新后的父任务
        """
        subtasks = []
        for name, func, args, kwargs in subtask_functions:
            subtask = ExecutableTask(
                name=name,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=parent_task.priority
            )
            subtasks.append(subtask)
            self._tasks[subtask.id] = subtask
        
        parent_task.subtasks = subtasks
        
        # 设置依赖关系（串行执行子任务）
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies.append(subtasks[i-1].id)
        
        logger.debug(f"Decomposed task {parent_task.name} into {len(subtasks)} subtasks")
        return parent_task
    
    async def execute_decomposed(self, task_id: str) -> TaskResult:
        """
        执行分解后的任务
        
        Args:
            task_id: 父任务ID
            
        Returns:
            TaskResult: 执行结果
        """
        parent_task = self._tasks.get(task_id)
        if not parent_task:
            return TaskResult(success=False, error=f"Task not found: {task_id}")
        
        if not parent_task.subtasks:
            return await self.execute(task_id)
        
        # 创建批次执行子任务
        batch = self.create_batch(
            name=f"subtasks_of_{parent_task.name}",
            tasks=parent_task.subtasks,
            execution_mode=ExecutionMode.PIPELINE
        )
        
        start_time = time.time()
        results = await self.execute_batch(batch.id)
        execution_time = (time.time() - start_time) * 1000
        
        # 汇总结果
        all_success = all(r.success for r in results.values())
        combined_data = {
            task_id: result.data 
            for task_id, result in results.items()
        }
        errors = [
            result.error 
            for result in results.values() 
            if result.error
        ]
        
        parent_task.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        parent_task.completed_at = datetime.now()
        parent_task.result = TaskResult(
            success=all_success,
            data=combined_data,
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time
        )
        
        return parent_task.result
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status in (TaskStatus.RUNNING, TaskStatus.PENDING, TaskStatus.RETRYING):
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"Cancelled task: {task.name}")
            return True
        
        return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        task = self._tasks.get(task_id)
        return task.result if task else None
    
    def get_batch_progress(self, batch_id: str) -> float:
        """获取批次进度"""
        batch = self._batches.get(batch_id)
        return batch.get_progress() if batch else 0.0
    
    def _record_execution(self, task: ExecutableTask) -> None:
        """记录执行历史"""
        self._execution_history.append({
            "task_id": task.id,
            "name": task.name,
            "status": task.status.value,
            "success": task.result.success if task.result else False,
            "execution_time_ms": task.result.execution_time_ms if task.result else 0,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        
        total_executions = len(self._execution_history)
        successful_executions = sum(
            1 for h in self._execution_history if h.get("success")
        )
        
        avg_execution_time = 0.0
        if self._execution_history:
            avg_execution_time = sum(
                h.get("execution_time_ms", 0) for h in self._execution_history
            ) / total_executions
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": successful_executions / max(total_executions, 1),
            "average_execution_time_ms": avg_execution_time,
            "total_batches": len(self._batches),
            "total_executions": total_executions
        }
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self._execution_history[-limit:]
    
    def clear_history(self) -> None:
        """清空历史"""
        self._execution_history.clear()
        self._tasks.clear()
        self._batches.clear()
        logger.info("TaskExecutor history cleared")
