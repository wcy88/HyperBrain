"""
HyperBrain 大模型集成与调度系统

提供统一的大模型 API 调用、多模型调度、Token 管理和能力评估功能。
"""

from .base import (
    BaseModel,
    ChatMessage,
    EmbeddingResponse,
    FinishReason,
    ModelCapability,
    ModelConfig,
    ModelError,
    ModelNotInitializedError,
    ModelAPIError,
    ModelRateLimitError,
    ModelAuthenticationError,
    ModelTimeoutError,
    ModelProvider,
    ModelResponse,
    ModelUsage,
    StreamChunk,
    TaskType,
)
from .openai_model import OpenAIModel, OpenAIModelUsage

# 可选模型：仅在依赖可用时导入
try:
    from .anthropic_model import AnthropicModel, AnthropicModelUsage
except ImportError:
    AnthropicModel = None
    AnthropicModelUsage = None

try:
    from .google_model import GoogleModel, GoogleModelUsage
except ImportError:
    GoogleModel = None
    GoogleModelUsage = None

try:
    from .ollama_model import OllamaModel, OllamaModelUsage
except ImportError:
    OllamaModel = None
    OllamaModelUsage = None

from .scheduler import ModelScheduler, ModelInstance
from .token_manager import (
    BudgetAlert,
    BudgetConfig,
    TokenManager,
    AlertLevel,
    AlertType,
    get_token_manager,
)
from .error_handler import (
    CircuitBreaker,
    CircuitBreakerConfig,
    ErrorCategory,
    ErrorClassifier,
    ErrorHandler,
    ErrorRecord,
    RetryConfig,
    get_error_handler,
    with_retry,
)
from .capability_evaluator import (
    BenchmarkResult,
    CapabilityEvaluator,
    ModelEvaluation,
    get_capability_evaluator,
)
from .model_manager import ModelManager, get_model_manager

__all__ = [
    # Base
    "BaseModel",
    "ChatMessage",
    "EmbeddingResponse",
    "FinishReason",
    "ModelCapability",
    "ModelConfig",
    "ModelError",
    "ModelNotInitializedError",
    "ModelAPIError",
    "ModelRateLimitError",
    "ModelAuthenticationError",
    "ModelTimeoutError",
    "ModelProvider",
    "ModelResponse",
    "ModelUsage",
    "StreamChunk",
    "TaskType",
    # Models
    "OpenAIModel",
    "OpenAIModelUsage",
    "AnthropicModel",
    "AnthropicModelUsage",
    "GoogleModel",
    "GoogleModelUsage",
    "OllamaModel",
    "OllamaModelUsage",
    # Scheduler
    "ModelScheduler",
    "ModelInstance",
    # Token Manager
    "BudgetAlert",
    "BudgetConfig",
    "TokenManager",
    "AlertLevel",
    "AlertType",
    "get_token_manager",
    # Error Handler
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorHandler",
    "ErrorRecord",
    "RetryConfig",
    "get_error_handler",
    "with_retry",
    # Capability Evaluator
    "BenchmarkResult",
    "CapabilityEvaluator",
    "ModelEvaluation",
    "get_capability_evaluator",
    # Model Manager
    "ModelManager",
    "get_model_manager",
]
