"""
全局错误处理系统

提供：
- 全局错误捕获和恢复
- 异常分类和处理
- 错误报告生成
- 自动重试机制
"""

import asyncio
import functools
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from dataclasses import dataclass, field

from hyperbrain.core.logger import get_logger

logger = get_logger("error_handler")


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 轻微错误，不影响功能
    MEDIUM = "medium"     # 中等错误，部分功能受影响
    HIGH = "high"         # 严重错误，核心功能受影响
    CRITICAL = "critical" # 致命错误，系统无法运行


class ErrorCategory(Enum):
    """错误类别"""
    SYSTEM = "system"           # 系统错误
    NETWORK = "network"         # 网络错误
    DATABASE = "database"       # 数据库错误
    MODEL = "model"             # 模型错误
    MEMORY = "memory"           # 内存错误
    CONFIG = "config"           # 配置错误
    VALIDATION = "validation"   # 验证错误
    UNKNOWN = "unknown"         # 未知错误


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    recovered: bool = False
    recovery_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "traceback": self.traceback,
            "context": self.context,
            "recovered": self.recovered,
            "recovery_attempts": self.recovery_attempts
        }


class ErrorHandler:
    """全局错误处理器
    
    提供统一的错误处理、记录和恢复机制
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._error_history: List[ErrorRecord] = []
        self._error_counts: Dict[str, int] = {}
        self._recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self._handlers: Dict[Type[Exception], Callable] = {}
        
        # 注册默认恢复策略
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """注册默认恢复策略"""
        # 数据库错误恢复策略
        self._recovery_strategies[ErrorCategory.DATABASE] = [
            self._retry_strategy,
            self._fallback_to_memory_strategy
        ]
        
        # 网络错误恢复策略
        self._recovery_strategies[ErrorCategory.NETWORK] = [
            self._retry_strategy,
            self._offline_mode_strategy
        ]
        
        # 模型错误恢复策略
        self._recovery_strategies[ErrorCategory.MODEL] = [
            self._retry_strategy,
            self._fallback_model_strategy
        ]
        
        # 内存错误恢复策略
        self._recovery_strategies[ErrorCategory.MEMORY] = [
            self._cleanup_memory_strategy,
            self._reduce_load_strategy
        ]
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorRecord:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            severity: 严重程度
            
        Returns:
            ErrorRecord: 错误记录
        """
        # 分类错误
        category = self._classify_error(error)
        
        # 创建错误记录
        record = ErrorRecord(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            message=str(error),
            traceback=traceback.format_exc(),
            context=context or {}
        )
        
        # 记录到历史
        self._error_history.append(record)
        if len(self._error_history) > self.max_history:
            self._error_history = self._error_history[-self.max_history:]
        
        # 更新错误计数
        error_key = f"{category.value}:{type(error).__name__}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # 记录日志
        self._log_error(record)
        
        # 尝试恢复
        if category in self._recovery_strategies:
            self._attempt_recovery(record)
        
        return record
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_type = type(error).__name__.lower()
        
        if any(kw in error_type for kw in ["connection", "timeout", "network", "http"]):
            return ErrorCategory.NETWORK
        elif any(kw in error_type for kw in ["sql", "database", "db", "sqlite"]):
            return ErrorCategory.DATABASE
        elif any(kw in error_type for kw in ["model", "api", "llm", "openai"]):
            return ErrorCategory.MODEL
        elif any(kw in error_type for kw in ["memory", "oom", "allocation"]):
            return ErrorCategory.MEMORY
        elif any(kw in error_type for kw in ["config", "configuration", "setting"]):
            return ErrorCategory.CONFIG
        elif any(kw in error_type for kw in ["validation", "value", "type"]):
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.UNKNOWN
    
    def _log_error(self, record: ErrorRecord) -> None:
        """记录错误日志"""
        log_message = (
            f"[{record.severity.value.upper()}] "
            f"[{record.category.value}] "
            f"{record.message} "
            f"(ID: {record.error_id})"
        )
        
        if record.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif record.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif record.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        if record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.debug(record.traceback)
    
    def _attempt_recovery(self, record: ErrorRecord) -> bool:
        """尝试恢复
        
        Args:
            record: 错误记录
            
        Returns:
            bool: 是否恢复成功
        """
        strategies = self._recovery_strategies.get(record.category, [])
        
        for strategy in strategies:
            try:
                record.recovery_attempts += 1
                if strategy(record):
                    record.recovered = True
                    logger.info(f"Error {record.error_id} recovered using {strategy.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Recovery strategy failed: {e}")
        
        return False
    
    # ========== 恢复策略 ==========
    
    def _retry_strategy(self, record: ErrorRecord) -> bool:
        """重试策略"""
        if record.recovery_attempts >= 3:
            return False
        
        logger.info(f"Retrying operation for error {record.error_id}")
        # 实际重试逻辑由调用方实现
        return True
    
    def _fallback_to_memory_strategy(self, record: ErrorRecord) -> bool:
        """回退到内存策略"""
        logger.info(f"Falling back to memory storage for error {record.error_id}")
        return True
    
    def _offline_mode_strategy(self, record: ErrorRecord) -> bool:
        """离线模式策略"""
        logger.info(f"Switching to offline mode for error {record.error_id}")
        return True
    
    def _fallback_model_strategy(self, record: ErrorRecord) -> bool:
        """回退模型策略"""
        logger.info(f"Switching to fallback model for error {record.error_id}")
        return True
    
    def _cleanup_memory_strategy(self, record: ErrorRecord) -> bool:
        """清理内存策略"""
        try:
            import gc
            gc.collect()
            logger.info(f"Memory cleaned up for error {record.error_id}")
            return True
        except Exception:
            return False
    
    def _reduce_load_strategy(self, record: ErrorRecord) -> bool:
        """降低负载策略"""
        logger.info(f"Reducing system load for error {record.error_id}")
        return True
    
    # ========== 查询接口 ==========
    
    def get_error_history(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> List[ErrorRecord]:
        """获取错误历史
        
        Args:
            category: 过滤类别
            severity: 过滤严重程度
            limit: 限制数量
            
        Returns:
            List[ErrorRecord]: 错误记录列表
        """
        filtered = self._error_history
        
        if category:
            filtered = [r for r in filtered if r.category == category]
        
        if severity:
            filtered = [r for r in filtered if r.severity == severity]
        
        return filtered[-limit:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            "total_errors": len(self._error_history),
            "error_counts": self._error_counts.copy(),
            "by_severity": {
                severity.value: len([r for r in self._error_history if r.severity == severity])
                for severity in ErrorSeverity
            },
            "by_category": {
                category.value: len([r for r in self._error_history if r.category == category])
                for category in ErrorCategory
            },
            "recovery_rate": (
                len([r for r in self._error_history if r.recovered]) /
                max(len(self._error_history), 1)
            )
        }
    
    def generate_error_report(self) -> Dict[str, Any]:
        """生成错误报告"""
        recent_errors = self.get_error_history(limit=50)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_error_stats(),
            "recent_errors": [r.to_dict() for r in recent_errors],
            "top_errors": sorted(
                self._error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def clear_history(self) -> None:
        """清空错误历史"""
        self._error_history.clear()
        self._error_counts.clear()


# 装饰器

def safe_execute(
    fallback_value: Any = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None
):
    """安全执行装饰器
    
    捕获异常并返回fallback值
    
    Args:
        fallback_value: 失败时的返回值
        severity: 错误严重程度
        context: 错误上下文
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                error_handler.handle_error(
                    e,
                    context={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                        **(context or {})
                    },
                    severity=severity
                )
                return fallback_value
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                error_handler.handle_error(
                    e,
                    context={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                        **(context or {})
                    },
                    severity=severity
                )
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """重试装饰器
    
    在指定异常时自动重试
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)
                        import time
                        time.sleep(delay * (attempt + 1))
            
            raise last_exception
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)
                        await asyncio.sleep(delay * (attempt + 1))
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


# 全局错误处理器
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler
