"""
执行管理器 (Execution Manager)

统一管理所有执行模块，协调任务执行流程，提供统一的执行API。

功能：
- 统一管理所有执行模块
- 协调任务执行流程
- 提供统一的执行API
- 与其他系统层交互
"""

import asyncio
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.execution.task_execution import (
    TaskExecutor,
    ExecutableTask,
    TaskResult,
    TaskStatus,
    TaskPriority,
    ExecutionMode
)
from hyperbrain.layers.execution.tool_invocation import (
    ToolInvoker,
    ToolRegistry,
    ToolResult,
    ToolDefinition,
    ToolCategory,
    create_default_tools
)
from hyperbrain.layers.execution.output_generation import (
    OutputManager,
    GeneratedOutput,
    OutputType,
    OutputFormat,
    CodeLanguage,
    QualityCheckResult
)
from hyperbrain.layers.execution.behavior_control import (
    BehaviorController,
    BehaviorDecision,
    BehaviorType,
    BehaviorPolicy,
    BehaviorProfile,
    BehaviorRule,
    ConstraintType
)
from hyperbrain.layers.execution.progress_monitor import (
    ProgressMonitor,
    ProgressReport,
    MonitoredTask,
    AlertLevel,
    ResourceType
)

logger = get_logger("execution.manager")


class ExecutionRequest(BaseModel):
    """执行请求"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_type: str = ""  # task, tool, output, behavior_check
    content: Any = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ExecutionResponse(BaseModel):
    """执行响应"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    request_id: str = ""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    behavior_decision: Optional[BehaviorDecision] = None
    output: Optional[GeneratedOutput] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class ExecutionPipeline(BaseModel):
    """执行流水线配置"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    enable_behavior_check: bool = True
    enable_progress_monitor: bool = True
    enable_output_quality_check: bool = True
    default_execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    default_timeout: float = 30.0
    max_concurrent_tasks: int = 10


class ExecutionManager:
    """
    执行管理器 - 执行系统的中央控制器
    
    统一管理任务执行、工具调用、输出生成、行为控制和进度监控，
    提供统一的执行API，并与其他系统层交互。
    
    Attributes:
        task_executor: 任务执行器
        tool_invoker: 工具调用器
        output_manager: 输出管理器
        behavior_controller: 行为控制器
        progress_monitor: 进度监控器
    """
    
    def __init__(
        self,
        pipeline_config: Optional[ExecutionPipeline] = None,
        behavior_profile: Optional[BehaviorProfile] = None
    ):
        self.config = get_config()
        self.pipeline_config = pipeline_config or ExecutionPipeline()
        
        # 初始化子模块
        self.task_executor = TaskExecutor()
        self.tool_invoker = ToolInvoker(create_default_tools())
        self.output_manager = OutputManager()
        self.behavior_controller = BehaviorController(behavior_profile)
        self.progress_monitor = ProgressMonitor()
        
        # 状态
        self._execution_history: List[ExecutionResponse] = []
        self._is_initialized = False
        
        logger.info("ExecutionManager initialized")
    
    async def initialize(self) -> None:
        """初始化执行系统"""
        if self._is_initialized:
            return
        
        # 启动进度监控
        if self.pipeline_config.enable_progress_monitor:
            await self.progress_monitor.start_monitoring()
        
        self._is_initialized = True
        logger.info("ExecutionManager initialized")
    
    async def shutdown(self) -> None:
        """关闭执行系统"""
        if self.pipeline_config.enable_progress_monitor:
            await self.progress_monitor.stop_monitoring()
        
        self._is_initialized = False
        logger.info("ExecutionManager shutdown")
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        统一执行接口
        
        完整流程：
        1. 行为检查
        2. 执行请求
        3. 进度监控
        4. 输出生成
        5. 质量检查
        
        Args:
            request: 执行请求
            
        Returns:
            ExecutionResponse: 执行响应
        """
        if not self._is_initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        # 1. 行为检查
        behavior_decision = None
        if self.pipeline_config.enable_behavior_check and isinstance(request.content, str):
            behavior_decision = self.behavior_controller.decide(
                request.content,
                context=request.metadata.get("context")
            )
            
            # 如果被拒绝，直接返回
            if behavior_decision.behavior_type == BehaviorType.REFUSE:
                return ExecutionResponse(
                    request_id=request.id,
                    success=False,
                    error=behavior_decision.suggested_response or "Request refused by behavior controller",
                    behavior_decision=behavior_decision,
                    execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
        
        # 2. 执行请求
        result_data = None
        error = None
        
        try:
            if request.request_type == "task":
                result_data = await self._execute_task(request)
            elif request.request_type == "tool":
                result_data = await self._execute_tool(request)
            elif request.request_type == "output":
                result_data = await self._generate_output(request)
            elif request.request_type == "batch":
                result_data = await self._execute_batch(request)
            else:
                error = f"Unknown request type: {request.request_type}"
        except Exception as e:
            error = str(e)
            logger.error(f"Execution error: {e}")
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 3. 构建响应
        response = ExecutionResponse(
            request_id=request.id,
            success=error is None,
            data=result_data,
            error=error,
            execution_time_ms=execution_time,
            behavior_decision=behavior_decision
        )
        
        self._execution_history.append(response)
        
        # 限制历史大小
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-500:]
        
        return response
    
    async def _execute_task(self, request: ExecutionRequest) -> Any:
        """执行任务"""
        func = request.parameters.get("func")
        args = request.parameters.get("args", ())
        kwargs = request.parameters.get("kwargs", {})
        
        if not func:
            raise ValueError("Task execution requires 'func' parameter")
        
        # 创建任务
        task = self.task_executor.create_task(
            name=request.parameters.get("name", "unnamed_task"),
            func=func,
            args=args,
            kwargs=kwargs,
            priority=request.priority,
            timeout=request.timeout_seconds
        )
        
        # 注册到进度监控
        if self.pipeline_config.enable_progress_monitor:
            monitored = self.progress_monitor.register_task(
                task_id=task.id,
                name=task.name,
                total_steps=request.parameters.get("total_steps", 100)
            )
            monitored.start()
        
        # 执行任务
        result = await self.task_executor.execute(task.id)
        
        # 更新监控
        if self.pipeline_config.enable_progress_monitor:
            monitored = self.progress_monitor.get_task(task.id)
            if monitored:
                monitored.complete(result.success)
        
        return result.to_dict() if result else None
    
    async def _execute_tool(self, request: ExecutionRequest) -> Any:
        """执行工具"""
        tool_name = request.parameters.get("tool_name")
        tool_params = request.parameters.get("parameters", {})
        
        if not tool_name:
            raise ValueError("Tool execution requires 'tool_name' parameter")
        
        result = await self.tool_invoker.invoke(
            tool_name=tool_name,
            parameters=tool_params,
            timeout=request.timeout_seconds
        )
        
        return result.to_dict()
    
    async def _generate_output(self, request: ExecutionRequest) -> Any:
        """生成输出"""
        output_type = request.parameters.get("output_type", "text")
        content = request.parameters.get("content", "")
        
        if output_type == "text":
            output = self.output_manager.generate_text(
                content=content,
                format_type=OutputFormat(request.parameters.get("format", "plain"))
            )
        elif output_type == "code":
            output = self.output_manager.generate_code(
                code=content,
                language=CodeLanguage(request.parameters.get("language", "python")),
                title=request.parameters.get("title")
            )
        elif output_type == "markdown":
            output = self.output_manager.generate_markdown(
                content=content,
                title=request.parameters.get("title")
            )
        else:
            raise ValueError(f"Unknown output type: {output_type}")
        
        # 质量检查
        if self.pipeline_config.enable_output_quality_check:
            self.output_manager.check_quality(output.id)
        
        return output.to_dict()
    
    async def _execute_batch(self, request: ExecutionRequest) -> Any:
        """批量执行"""
        items = request.parameters.get("items", [])
        results = []
        
        for item in items:
            sub_request = ExecutionRequest(
                request_type=item.get("type", "task"),
                content=item.get("content"),
                parameters=item.get("parameters", {}),
                priority=TaskPriority(item.get("priority", 3))
            )
            result = await self.execute(sub_request)
            results.append(result.to_dict())
        
        return results
    
    async def execute_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 30.0,
        monitor_progress: bool = True
    ) -> TaskResult:
        """
        便捷方法：执行任务
        
        Args:
            name: 任务名称
            func: 执行函数
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            timeout: 超时时间
            monitor_progress: 是否监控进度
            
        Returns:
            TaskResult: 执行结果
        """
        task = self.task_executor.create_task(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout
        )
        
        if monitor_progress and self.pipeline_config.enable_progress_monitor:
            monitored = self.progress_monitor.register_task(
                task_id=task.id,
                name=name,
                total_steps=100
            )
            monitored.start()
        
        result = await self.task_executor.execute(task.id)
        
        if monitor_progress and self.pipeline_config.enable_progress_monitor:
            monitored = self.progress_monitor.get_task(task.id)
            if monitored:
                monitored.complete(result.success if result else False)
        
        return result
    
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> ToolResult:
        """
        便捷方法：调用工具
        
        Args:
            tool_name: 工具名称
            parameters: 参数
            timeout: 超时时间
            
        Returns:
            ToolResult: 调用结果
        """
        return await self.tool_invoker.invoke(tool_name, parameters, timeout)
    
    def generate_text_output(
        self,
        content: str,
        format_type: OutputFormat = OutputFormat.PLAIN
    ) -> GeneratedOutput:
        """便捷方法：生成文本输出"""
        return self.output_manager.generate_text(content, format_type)
    
    def generate_code_output(
        self,
        code: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        title: Optional[str] = None
    ) -> GeneratedOutput:
        """便捷方法：生成代码输出"""
        return self.output_manager.generate_code(code, language, title)
    
    def generate_markdown_output(
        self,
        content: str,
        title: Optional[str] = None
    ) -> GeneratedOutput:
        """便捷方法：生成Markdown输出"""
        return self.output_manager.generate_markdown(content, title)
    
    def check_behavior(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> BehaviorDecision:
        """便捷方法：检查行为"""
        return self.behavior_controller.decide(input_text, context)
    
    def get_progress_report(self, title: str = "Execution Progress") -> ProgressReport:
        """获取进度报告"""
        return self.progress_monitor.generate_report(title)
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: ToolCategory = ToolCategory.CUSTOM,
        **kwargs
    ) -> ToolDefinition:
        """注册工具"""
        return self.tool_invoker.registry.register(
            name=name,
            func=func,
            description=description,
            category=category,
            **kwargs
        )
    
    def add_behavior_rule(self, rule: BehaviorRule) -> None:
        """添加行为规则"""
        self.behavior_controller.add_constraint_rule(rule)
    
    def set_behavior_profile(self, profile: BehaviorProfile) -> None:
        """设置行为画像"""
        self.behavior_controller.set_profile(profile)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_initialized": self._is_initialized,
            "execution_history_size": len(self._execution_history),
            "task_executor": self.task_executor.get_stats(),
            "tool_invoker": self.tool_invoker.get_stats(),
            "output_manager": self.output_manager.get_stats(),
            "behavior_controller": self.behavior_controller.get_stats(),
            "progress_monitor": self.progress_monitor.get_stats()
        }
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResponse]:
        """获取执行历史"""
        return self._execution_history[-limit:]
    
    def clear_history(self) -> None:
        """清空历史"""
        self._execution_history.clear()
        self.task_executor.clear_history()
        self.tool_invoker.clear_history()
        self.output_manager.clear()
        self.behavior_controller.reset()
        self.progress_monitor.clear_history()
        logger.info("ExecutionManager history cleared")
    
    def reset(self) -> None:
        """重置执行系统"""
        self.clear_history()
        self.progress_monitor.reset()
        self._is_initialized = False
        logger.info("ExecutionManager reset")
