"""
工具调用模块 (Tool Invocation)

管理和调用各种外部工具和API。

功能：
- 调用各种外部工具和API
- 工具注册和管理
- 参数解析和验证
- 工具结果处理
- 错误处理和重试
"""

import asyncio
import time
import json
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict, create_model

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.tool")


class ToolCategory(str, Enum):
    """工具类别"""
    WEB_SEARCH = "web_search"
    CALCULATION = "calculation"
    FILE_OPERATION = "file_operation"
    DATA_PROCESSING = "data_processing"
    API_CALL = "api_call"
    SYSTEM = "system"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    """工具状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    ERROR = "error"


class ToolResult(BaseModel):
    """工具调用结果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_name: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "tool_name": self.tool_name
        }


class ToolParameter(BaseModel):
    """工具参数定义"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    param_type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None
    enum_values: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.param_type,
            "description": self.description,
            "required": self.required
        }
        if self.default is not None:
            result["default"] = self.default
        if self.enum_values:
            result["enum"] = self.enum_values
        return result


class ToolDefinition(BaseModel):
    """工具定义"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    description: str = ""
    category: ToolCategory = ToolCategory.CUSTOM
    parameters: List[ToolParameter] = Field(default_factory=list)
    func: Optional[Callable] = Field(default=None, exclude=True)
    status: ToolStatus = ToolStatus.AVAILABLE
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "status": self.status.value,
            "timeout_seconds": self.timeout_seconds,
            "requires_confirmation": self.requires_confirmation
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        logger.info("ToolRegistry initialized")
    
    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: ToolCategory = ToolCategory.CUSTOM,
        parameters: Optional[List[ToolParameter]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        requires_confirmation: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolDefinition:
        """
        注册工具
        
        Args:
            name: 工具名称
            func: 执行函数
            description: 描述
            category: 类别
            parameters: 参数定义
            timeout: 超时时间
            max_retries: 最大重试次数
            requires_confirmation: 是否需要确认
            metadata: 元数据
            
        Returns:
            ToolDefinition: 工具定义
        """
        # 自动提取参数
        if parameters is None:
            parameters = self._extract_parameters(func)
        
        tool = ToolDefinition(
            name=name,
            description=description or func.__doc__ or "",
            category=category,
            parameters=parameters,
            func=func,
            timeout_seconds=timeout,
            max_retries=max_retries,
            requires_confirmation=requires_confirmation,
            metadata=metadata or {}
        )
        
        self._tools[name] = tool
        
        # 更新分类索引
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.info(f"Registered tool: {name} ({category.value})")
        return tool
    
    def _extract_parameters(self, func: Callable) -> List[ToolParameter]:
        """从函数签名提取参数"""
        parameters = []
        sig = inspect.signature(func)
        
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list or getattr(param.annotation, "__origin__", None) == list:
                    param_type = "array"
                elif param.annotation == dict or getattr(param.annotation, "__origin__", None) == dict:
                    param_type = "object"
            
            tool_param = ToolParameter(
                name=param_name,
                param_type=param_type,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
            parameters.append(tool_param)
        
        return parameters
    
    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否成功
        """
        if name not in self._tools:
            return False
        
        tool = self._tools.pop(name)
        
        # 从分类索引中移除
        if tool.category in self._categories:
            if name in self._categories[tool.category]:
                self._categories[tool.category].remove(name)
        
        logger.info(f"Unregistered tool: {name}")
        return True
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """
        列出工具
        
        Args:
            category: 过滤类别
            
        Returns:
            List[ToolDefinition]: 工具列表
        """
        if category:
            return [
                self._tools[name] 
                for name in self._categories.get(category, [])
                if name in self._tools
            ]
        return list(self._tools.values())
    
    def get_tools_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """按类别获取工具"""
        result = {}
        for category, names in self._categories.items():
            result[category.value] = [
                self._tools[name].to_dict() 
                for name in names 
                if name in self._tools
            ]
        return result
    
    def is_registered(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._tools
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_tools": len(self._tools),
            "categories": {
                cat.value: len(tools) 
                for cat, tools in self._categories.items()
            },
            "available": sum(1 for t in self._tools.values() if t.status == ToolStatus.AVAILABLE)
        }


class ToolInvoker:
    """
    工具调用器
    
    负责执行工具调用，处理参数验证和错误重试。
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()
        self._invocation_history: List[Dict[str, Any]] = []
        logger.info("ToolInvoker initialized")
    
    async def invoke(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> ToolResult:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            parameters: 调用参数
            timeout: 超时时间
            
        Returns:
            ToolResult: 调用结果
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name
            )
        
        if tool.status != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error=f"Tool unavailable: {tool_name} (status: {tool.status.value})",
                tool_name=tool_name
            )
        
        if not tool.func:
            return ToolResult(
                success=False,
                error=f"Tool has no function: {tool_name}",
                tool_name=tool_name
            )
        
        # 参数验证
        parameters = parameters or {}
        validation_error = self._validate_parameters(tool, parameters)
        if validation_error:
            return ToolResult(
                success=False,
                error=validation_error,
                tool_name=tool_name
            )
        
        # 执行工具
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= tool.max_retries:
            try:
                logger.debug(f"Invoking tool: {tool_name} (attempt {retry_count + 1})")
                
                if asyncio.iscoroutinefunction(tool.func):
                    result_data = await asyncio.wait_for(
                        tool.func(**parameters),
                        timeout=timeout or tool.timeout_seconds
                    )
                else:
                    loop = asyncio.get_event_loop()
                    result_data = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: tool.func(**parameters)),
                        timeout=timeout or tool.timeout_seconds
                    )
                
                execution_time = (time.time() - start_time) * 1000
                
                result = ToolResult(
                    success=True,
                    data=result_data,
                    execution_time_ms=execution_time,
                    tool_name=tool_name
                )
                
                self._record_invocation(tool_name, result, parameters)
                return result
                
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Tool timeout: {tool_name} (attempt {retry_count})")
                
                if retry_count > tool.max_retries:
                    result = ToolResult(
                        success=False,
                        error="Tool invocation timed out",
                        execution_time_ms=(time.time() - start_time) * 1000,
                        tool_name=tool_name
                    )
                    self._record_invocation(tool_name, result, parameters)
                    return result
                
                await asyncio.sleep(tool.retry_delay_seconds)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Tool error: {tool_name} - {e} (attempt {retry_count})")
                
                if retry_count > tool.max_retries:
                    result = ToolResult(
                        success=False,
                        error=str(e),
                        execution_time_ms=(time.time() - start_time) * 1000,
                        tool_name=tool_name
                    )
                    self._record_invocation(tool_name, result, parameters)
                    return result
                
                await asyncio.sleep(tool.retry_delay_seconds)
        
        return ToolResult(
            success=False,
            error="Max retries exceeded",
            tool_name=tool_name
        )
    
    async def invoke_batch(
        self,
        invocations: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """
        批量调用工具
        
        Args:
            invocations: [{"tool": name, "parameters": {...}}, ...]
            
        Returns:
            List[ToolResult]: 结果列表
        """
        tasks = [
            self.invoke(inv["tool"], inv.get("parameters", {}))
            for inv in invocations
        ]
        return await asyncio.gather(*tasks)
    
    def _validate_parameters(
        self,
        tool: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """验证参数"""
        # 检查必需参数
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                return f"Missing required parameter: {param.name}"
        
        # 检查未知参数
        known_params = {p.name for p in tool.parameters}
        unknown = set(parameters.keys()) - known_params
        if unknown:
            return f"Unknown parameters: {', '.join(unknown)}"
        
        # 类型检查（简化版）
        for param in tool.parameters:
            if param.name in parameters:
                value = parameters[param.name]
                if param.param_type == "integer" and not isinstance(value, int):
                    return f"Parameter {param.name} should be integer"
                elif param.param_type == "number" and not isinstance(value, (int, float)):
                    return f"Parameter {param.name} should be number"
                elif param.param_type == "boolean" and not isinstance(value, bool):
                    return f"Parameter {param.name} should be boolean"
                elif param.param_type == "array" and not isinstance(value, list):
                    return f"Parameter {param.name} should be array"
        
        return None
    
    def _record_invocation(
        self,
        tool_name: str,
        result: ToolResult,
        parameters: Dict[str, Any]
    ) -> None:
        """记录调用历史"""
        self._invocation_history.append({
            "tool_name": tool_name,
            "parameters": parameters,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": datetime.now().isoformat()
        })
    
    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本解析工具调用
        
        支持格式：
        - tool_name(param1=value1, param2=value2)
        - { "tool": "name", "parameters": {...} }
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[Dict]: 解析结果
        """
        # 尝试JSON格式
        try:
            data = json.loads(text)
            if "tool" in data:
                return {
                    "tool": data["tool"],
                    "parameters": data.get("parameters", {})
                }
        except json.JSONDecodeError:
            pass
        
        # 尝试函数调用格式
        pattern = r'(\w+)\s*\((.*?)\)'
        match = __import__('re').match(pattern, text.strip())
        if match:
            tool_name = match.group(1)
            param_str = match.group(2)
            
            parameters = {}
            if param_str.strip():
                # 简单解析 key=value 格式
                for pair in param_str.split(','):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # 尝试转换类型
                        try:
                            if value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            elif value.isdigit():
                                value = int(value)
                            elif __import__('re').match(r'^\d+\.\d+$', value):
                                value = float(value)
                        except Exception:
                            pass
                        
                        parameters[key] = value
            
            return {
                "tool": tool_name,
                "parameters": parameters
            }
        
        return None
    
    def get_invocation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取调用历史"""
        return self._invocation_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._invocation_history)
        successful = sum(1 for h in self._invocation_history if h.get("success"))
        
        tool_counts = {}
        for h in self._invocation_history:
            name = h["tool_name"]
            tool_counts[name] = tool_counts.get(name, 0) + 1
        
        avg_time = 0.0
        if self._invocation_history:
            avg_time = sum(h.get("execution_time_ms", 0) for h in self._invocation_history) / total
        
        return {
            "total_invocations": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / max(total, 1),
            "average_execution_time_ms": avg_time,
            "tool_usage": tool_counts,
            "registered_tools": self.registry.get_stats()
        }
    
    def clear_history(self) -> None:
        """清空历史"""
        self._invocation_history.clear()
        logger.info("Tool invocation history cleared")


# 内置工具函数

def calculator(expression: str) -> Union[int, float]:
    """计算器工具"""
    try:
        # 安全评估简单数学表达式
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        result = eval(expression)
        return result
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")


def text_formatter(text: str, format_type: str = "upper") -> str:
    """文本格式化工具"""
    if format_type == "upper":
        return text.upper()
    elif format_type == "lower":
        return text.lower()
    elif format_type == "title":
        return text.title()
    elif format_type == "reverse":
        return text[::-1]
    else:
        return text


def data_converter(data: Any, target_format: str = "json") -> str:
    """数据转换工具"""
    if target_format == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)
    elif target_format == "yaml":
        # 简化YAML格式
        if isinstance(data, dict):
            lines = []
            for k, v in data.items():
                lines.append(f"{k}: {v}")
            return "\n".join(lines)
        return str(data)
    else:
        return str(data)


def create_default_tools() -> ToolRegistry:
    """创建默认工具注册表"""
    registry = ToolRegistry()
    
    # 注册计算器
    registry.register(
        name="calculator",
        func=calculator,
        description="执行数学计算",
        category=ToolCategory.CALCULATION,
        parameters=[
            ToolParameter(name="expression", param_type="string", description="数学表达式", required=True)
        ]
    )
    
    # 注册文本格式化
    registry.register(
        name="text_formatter",
        func=text_formatter,
        description="格式化文本",
        category=ToolCategory.DATA_PROCESSING,
        parameters=[
            ToolParameter(name="text", param_type="string", description="输入文本", required=True),
            ToolParameter(name="format_type", param_type="string", description="格式类型", required=False, default="upper")
        ]
    )
    
    # 注册数据转换
    registry.register(
        name="data_converter",
        func=data_converter,
        description="转换数据格式",
        category=ToolCategory.DATA_PROCESSING,
        parameters=[
            ToolParameter(name="data", param_type="object", description="输入数据", required=True),
            ToolParameter(name="target_format", param_type="string", description="目标格式", required=False, default="json")
        ]
    )
    
    return registry
