"""
行动执行器

执行具体行动并处理结果
"""

import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.action")


class ActionStatus(Enum):
    """行动状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionResult:
    """行动结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Action:
    """行动对象"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    priority: int = 1
    max_retries: int = 3
    timeout: float = 10.0


class ActionExecutor:
    """
    行动执行系统
    
    功能：
    1. 行动调度和执行
    2. 错误处理和重试
    3. 超时控制
    4. 并行执行
    """
    
    def __init__(self):
        self.config = get_config().execution
        self.pending_actions: List[Action] = []
        self.running_actions: Dict[str, Action] = {}
        self.completed_actions: List[Action] = []
        self.action_history: List[Dict[str, Any]] = []
        logger.info("ActionExecutor initialized")
    
    def register_action(self, action_id: str, name: str,
                       func: Callable,
                       args: tuple = (),
                       kwargs: Optional[Dict[str, Any]] = None,
                       priority: int = 1) -> Action:
        """
        注册行动
        
        Args:
            action_id: 行动ID
            name: 行动名称
            func: 执行函数
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            
        Returns:
            Action: 行动对象
        """
        action = Action(
            id=action_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=self.config.retry_attempts,
            timeout=self.config.action_timeout
        )
        
        self.pending_actions.append(action)
        self.pending_actions.sort(key=lambda a: a.priority, reverse=True)
        
        logger.debug(f"Registered action: {name} (id={action_id})")
        return action
    
    async def execute(self, action_id: str) -> ActionResult:
        """
        执行指定行动
        
        Args:
            action_id: 行动ID
            
        Returns:
            ActionResult: 执行结果
        """
        action = self._get_action(action_id)
        if not action:
            return ActionResult(success=False, error=f"Action not found: {action_id}")
        
        action.status = ActionStatus.RUNNING
        self.running_actions[action_id] = action
        
        start_time = time.time()
        retries = 0
        
        while retries <= action.max_retries:
            try:
                # 执行行动
                if asyncio_compatible := True:
                    import asyncio
                    result = await asyncio.wait_for(
                        self._run_action(action),
                        timeout=action.timeout
                    )
                else:
                    result = action.func(*action.args, **action.kwargs)
                
                execution_time = time.time() - start_time
                
                action.status = ActionStatus.SUCCESS
                self.completed_actions.append(action)
                del self.running_actions[action_id]
                
                action_result = ActionResult(
                    success=True,
                    data=result,
                    execution_time=execution_time
                )
                
                self._record_history(action, action_result)
                logger.info(f"Action {action.name} completed in {execution_time:.2f}s")
                return action_result
                
            except Exception as e:
                retries += 1
                logger.warning(f"Action {action.name} failed (attempt {retries}): {e}")
                
                if retries > action.max_retries:
                    action.status = ActionStatus.FAILED
                    self.completed_actions.append(action)
                    if action_id in self.running_actions:
                        del self.running_actions[action_id]
                    
                    action_result = ActionResult(
                        success=False,
                        error=str(e),
                        execution_time=time.time() - start_time
                    )
                    self._record_history(action, action_result)
                    return action_result
        
        return ActionResult(success=False, error="Max retries exceeded")
    
    async def _run_action(self, action: Action) -> Any:
        """运行行动"""
        import asyncio
        
        if asyncio.iscoroutinefunction(action.func):
            return await action.func(*action.args, **action.kwargs)
        else:
            # 同步函数在线程中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                lambda: action.func(*action.args, **action.kwargs)
            )
    
    def cancel_action(self, action_id: str) -> bool:
        """取消行动"""
        if action_id in self.running_actions:
            self.running_actions[action_id].status = ActionStatus.CANCELLED
            del self.running_actions[action_id]
            logger.info(f"Cancelled action: {action_id}")
            return True
        
        # 从待执行队列中移除
        for i, action in enumerate(self.pending_actions):
            if action.id == action_id:
                action.status = ActionStatus.CANCELLED
                self.pending_actions.pop(i)
                return True
        
        return False
    
    def _get_action(self, action_id: str) -> Optional[Action]:
        """获取行动"""
        for action in self.pending_actions:
            if action.id == action_id:
                return action
        return self.running_actions.get(action_id)
    
    def _record_history(self, action: Action, result: ActionResult) -> None:
        """记录历史"""
        self.action_history.append({
            "action_id": action.id,
            "name": action.name,
            "status": action.status.value,
            "success": result.success,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.action_history)
        successful = sum(1 for h in self.action_history if h["success"])
        
        return {
            "pending": len(self.pending_actions),
            "running": len(self.running_actions),
            "completed": len(self.completed_actions),
            "total_executed": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_execution_time": sum(h["execution_time"] for h in self.action_history) / max(total, 1)
        }
