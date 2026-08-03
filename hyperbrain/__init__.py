"""
HyperBrain - 拟人脑认知架构系统

一个模拟人脑认知过程的AI系统，包含8个核心认知层：
- 感知层 (Sensory)
- 记忆层 (Memory)
- 认知层 (Cognitive)
- 学习层 (Learning)
- 进化层 (Evolution)
- 情感层 (Emotional)
- 执行层 (Execution)
- 意识层 (Consciousness)

核心组件：
- Brain: 系统核心大脑，整合所有认知层
- Config: 配置系统
- Logger: 日志系统
- Cache: 缓存系统
- ErrorHandler: 错误处理系统
"""

__version__ = "0.2.0"
__author__ = "HyperBrain Team"

from hyperbrain.core.brain import Brain, get_brain, SystemState, ProcessingResult
from hyperbrain.core.config import Config, get_config
from hyperbrain.core.logger import get_logger, setup_logging
from hyperbrain.core.cache import get_cache_manager, LRUCache, cached
from hyperbrain.core.error_handler import (
    get_error_handler,
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    safe_execute,
    retry_on_error
)

__all__ = [
    "Brain",
    "get_brain",
    "SystemState",
    "ProcessingResult",
    "Config",
    "get_config",
    "get_logger",
    "setup_logging",
    "get_cache_manager",
    "LRUCache",
    "cached",
    "get_error_handler",
    "ErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "safe_execute",
    "retry_on_error",
]
