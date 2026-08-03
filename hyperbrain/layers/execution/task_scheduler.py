"""
任务调度器

管理和调度系统任务
"""

import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue

from hyperbrain.core.logger import get_logger

logger = get_logger("execution.scheduler")


@dataclass
class Task:
    """任务对象"""
    id: str
    name: str
    priority: int
    scheduled_time: float
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    recurring: bool = False
    interval: float = 0.0
    executed: bool = False


class TaskScheduler:
    """
    任务调度系统
    
    功能：
    1. 任务优先级调度
    2. 定时任务
    3. 循环任务
    4. 任务依赖管理
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[str] = []
        logger.info("TaskScheduler initialized")
    
    def schedule(self, task_id: str, name: str,
                func: Callable,
                priority: int = 5,
                delay: float = 0.0,
                args: tuple = (),
                kwargs: Optional[Dict[str, Any]] = None,
                recurring: bool = False,
                interval: float = 0.0) -> Task:
        """
        调度任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            func: 执行函数
            priority: 优先级（1-10，1最高）
            delay: 延迟执行时间（秒）
            args: 位置参数
            kwargs: 关键字参数
            recurring: 是否循环
            interval: 循环间隔（秒）
            
        Returns:
            Task: 任务对象
        """
        task = Task(
            id=task_id,
            name=name,
            priority=priority,
            scheduled_time=time.time() + delay,
            func=func,
            args=args,
            kwargs=kwargs or {},
            recurring=recurring,
            interval=interval
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: (t.scheduled_time, t.priority))
        
        logger.debug(f"Scheduled task: {name} (priority={priority})")
        return task
    
    def get_next_task(self) -> Optional[Task]:
        """获取下一个待执行任务"""
        current_time = time.time()
        
        for task in self.task_queue:
            if not task.executed and task.scheduled_time <= current_time:
                return task
        
        return None
    
    def execute_next(self) -> Optional[Any]:
        """执行下一个任务"""
        task = self.get_next_task()
        if not task:
            return None
        
        try:
            logger.info(f"Executing task: {task.name}")
            result = task.func(*task.args, **task.kwargs)
            
            task.executed = True
            self.completed_tasks.append(task.id)
            
            # 如果是循环任务，重新调度
            if task.recurring and task.interval > 0:
                task.executed = False
                task.scheduled_time = time.time() + task.interval
                self.task_queue.sort(key=lambda t: (t.scheduled_time, t.priority))
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
            task.executed = True
            self.completed_tasks.append(task.id)
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.tasks:
            self.tasks[task_id].executed = True
            logger.info(f"Cancelled task: {task_id}")
            return True
        return False
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待执行任务"""
        return [t for t in self.task_queue if not t.executed]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pending = len(self.get_pending_tasks())
        return {
            "total_tasks": len(self.tasks),
            "pending": pending,
            "completed": len(self.completed_tasks),
            "recurring": sum(1 for t in self.tasks.values() if t.recurring)
        }
