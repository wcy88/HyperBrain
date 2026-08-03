"""
错误处理与重试机制

提供自动重试、指数退避、错误分类、熔断机制和日志记录功能。
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from hyperbrain.core.logger import get_logger
from .base import (
    ModelAPIError,
    ModelAuthenticationError,
    ModelError,
    ModelRateLimitError,
    ModelTimeoutError,
)

logger = get_logger("models.error_handler")


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SERVER = "server"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ErrorRecord:
    """错误记录
    
    Attributes:
        error: 错误对象
        category: 错误分类
        timestamp: 发生时间
        retry_count: 重试次数
        context: 上下文信息
    """
    error: Exception
    category: ErrorCategory
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """重试配置
    
    Attributes:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        retryable_errors: 可重试的错误类型
        on_retry: 重试回调函数
        on_failure: 失败回调函数
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_errors: tuple[Type[Exception], ...] = field(
        default_factory=lambda: (Exception,)
    )
    on_retry: Optional[Callable[[Exception, int], None]] = None
    on_failure: Optional[Callable[[Exception, int], None]] = None
    
    def calculate_delay(self, attempt: int) -> float:
        """计算退避延迟
        
        使用指数退避策略：delay = min(base_delay * base^attempt, max_delay)
        
        Args:
            attempt: 当前尝试次数（从0开始）
            
        Returns:
            float: 延迟秒数
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """熔断器配置
    
    Attributes:
        failure_threshold: 触发熔断的失败次数阈值
        recovery_timeout: 熔断后恢复超时（秒）
        half_open_max_calls: 半开状态最大测试调用数
        success_threshold: 半开状态恢复所需成功次数
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """熔断器
    
    实现熔断机制，防止级联故障。
    
    状态转换：
    - CLOSED: 正常状态，请求直接通过
    - OPEN: 熔断状态，请求快速失败
    - HALF_OPEN: 半开状态，允许有限请求测试恢复
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    @property
    def is_open(self) -> bool:
        """检查熔断器是否打开"""
        return self.state == CircuitBreakerState.OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行带熔断保护的调用
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            ModelError: 熔断器打开时抛出
        """
        async with self._lock:
            await self._update_state()
            
            if self.state == CircuitBreakerState.OPEN:
                raise ModelError(
                    f"Circuit breaker '{self.name}' is OPEN",
                    code="CIRCUIT_OPEN"
                )
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise ModelError(
                        f"Circuit breaker '{self.name}' half-open limit reached",
                        code="CIRCUIT_HALF_OPEN_LIMIT"
                    )
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _update_state(self) -> None:
        """更新熔断器状态"""
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
    
    async def _on_success(self) -> None:
        """成功回调"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._reset()
                    logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self) -> None:
        """失败回调"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPEN (half-open failed)")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPEN (threshold reached)")
    
    def _reset(self) -> None:
        """重置熔断器"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def get_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class ErrorClassifier:
    """错误分类器
    
    根据错误类型和消息内容对错误进行分类。
    """
    
    _error_patterns: Dict[ErrorCategory, List[str]] = {
        ErrorCategory.RATE_LIMIT: [
            "rate limit", "too many requests", "429", "quota exceeded",
            "throttled", "limit exceeded"
        ],
        ErrorCategory.AUTHENTICATION: [
            "unauthorized", "authentication", "api key", "invalid key",
            "401", "403", "forbidden", "access denied"
        ],
        ErrorCategory.TIMEOUT: [
            "timeout", "timed out", "deadline exceeded", "request timeout"
        ],
        ErrorCategory.NETWORK: [
            "connection", "network", "dns", "unreachable", "refused",
            "reset", "broken pipe", "network error"
        ],
        ErrorCategory.SERVER: [
            "internal server error", "500", "502", "503", "504",
            "bad gateway", "service unavailable", "server error"
        ],
        ErrorCategory.VALIDATION: [
            "bad request", "invalid", "validation", "schema",
            "parameter", "400", "malformed"
        ],
    }
    
    @classmethod
    def classify(cls, error: Exception) -> ErrorCategory:
        """对错误进行分类
        
        Args:
            error: 错误对象
            
        Returns:
            ErrorCategory: 错误分类
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 根据错误类型直接判断
        if isinstance(error, ModelRateLimitError):
            return ErrorCategory.RATE_LIMIT
        elif isinstance(error, ModelAuthenticationError):
            return ErrorCategory.AUTHENTICATION
        elif isinstance(error, ModelTimeoutError):
            return ErrorCategory.TIMEOUT
        
        # 根据错误消息模式匹配
        for category, patterns in cls._error_patterns.items():
            for pattern in patterns:
                if pattern in error_str or pattern in error_type:
                    return category
        
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def is_retryable(cls, error: Exception, retryable_categories: Optional[List[ErrorCategory]] = None) -> bool:
        """判断错误是否可重试
        
        Args:
            error: 错误对象
            retryable_categories: 可重试的分类列表
            
        Returns:
            bool: 是否可重试
        """
        if retryable_categories is None:
            retryable_categories = [
                ErrorCategory.NETWORK,
                ErrorCategory.RATE_LIMIT,
                ErrorCategory.SERVER,
                ErrorCategory.TIMEOUT,
            ]
        
        category = cls.classify(error)
        return category in retryable_categories


class ErrorHandler:
    """错误处理器
    
    提供统一的错误处理、重试和熔断功能。
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorRecord] = []
        self.max_history_size = 1000
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """获取或创建熔断器
        
        Args:
            name: 熔断器名称
            config: 熔断器配置
            
        Returns:
            CircuitBreaker: 熔断器实例
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """执行带重试的函数调用
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            retry_config: 重试配置
            circuit_breaker: 熔断器（可选）
            context: 上下文信息
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            Exception: 重试耗尽后抛出最后一次异常
        """
        config = retry_config or RetryConfig()
        context = context or {}
        
        last_error: Optional[Exception] = None
        
        for attempt in range(config.max_retries + 1):
            try:
                if circuit_breaker:
                    return await circuit_breaker.call(func, *args, **kwargs)
                else:
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_error = e
                category = ErrorClassifier.classify(e)
                
                # 记录错误
                self._record_error(e, category, attempt, context)
                
                # 检查是否可重试
                if attempt >= config.max_retries:
                    logger.error(f"Max retries ({config.max_retries}) exceeded: {e}")
                    if config.on_failure:
                        config.on_failure(e, attempt)
                    raise
                
                if not ErrorClassifier.is_retryable(e):
                    logger.warning(f"Non-retryable error: {e}")
                    raise
                
                # 计算延迟
                delay = config.calculate_delay(attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                if config.on_retry:
                    config.on_retry(e, attempt)
                
                await asyncio.sleep(delay)
        
        # 不应该到达这里
        raise last_error or Exception("Unknown error in retry loop")
    
    def _record_error(self, error: Exception, category: ErrorCategory, retry_count: int, context: Dict[str, Any]) -> None:
        """记录错误
        
        Args:
            error: 错误对象
            category: 错误分类
            retry_count: 重试次数
            context: 上下文信息
        """
        record = ErrorRecord(
            error=error,
            category=category,
            retry_count=retry_count,
            context=context
        )
        
        self.error_history.append(record)
        
        # 限制历史记录大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_error_stats(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """获取错误统计
        
        Args:
            since: 统计起始时间
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        records = self.error_history
        if since:
            records = [r for r in records if r.timestamp >= since]
        
        if not records:
            return {"total": 0, "by_category": {}, "by_hour": {}}
        
        by_category: Dict[str, int] = {}
        by_hour: Dict[str, int] = {}
        
        for record in records:
            cat = record.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            hour = record.timestamp.strftime("%Y-%m-%d %H:00")
            by_hour[hour] = by_hour.get(hour, 0) + 1
        
        return {
            "total": len(records),
            "by_category": by_category,
            "by_hour": by_hour,
            "time_range": {
                "start": records[0].timestamp.isoformat(),
                "end": records[-1].timestamp.isoformat(),
            }
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """获取所有熔断器状态"""
        return {
            name: cb.get_status()
            for name, cb in self.circuit_breakers.items()
        }


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_errors: Optional[tuple[Type[Exception], ...]] = None,
    circuit_breaker_name: Optional[str] = None,
):
    """重试装饰器
    
    为异步函数添加重试功能。
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        retryable_errors: 可重试的错误类型
        circuit_breaker_name: 熔断器名称（可选）
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        handler = get_error_handler()  # 使用全局单例，确保熔断器状态跨调用共享
        config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            retryable_errors=retryable_errors or (Exception,)
        )
        
        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = handler.get_circuit_breaker(circuit_breaker_name)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await handler.execute_with_retry(
                func, *args,
                retry_config=config,
                circuit_breaker=circuit_breaker,
                context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数不支持异步重试，直接调用
            return func(*args, **kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    return decorator


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler
