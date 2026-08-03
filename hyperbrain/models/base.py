"""
统一大模型API调用层

定义所有大模型接口的抽象基类，提供统一的调用规范和数据模型。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from pydantic import BaseModel as PydanticBaseModel, Field, field_validator


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    UNKNOWN = "unknown"


class TaskType(str, Enum):
    """任务类型枚举"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    CODE = "code"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class FinishReason(str, Enum):
    """完成原因枚举"""
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"
    UNKNOWN = "unknown"


class ModelCapability(str, Enum):
    """模型能力枚举"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    STREAMING = "streaming"
    VISION = "vision"
    CODE = "code"
    REASONING = "reasoning"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    MULTILINGUAL = "multilingual"


@dataclass
class ChatMessage:
    """聊天消息数据类
    
    Attributes:
        role: 消息角色 (system, user, assistant, tool)
        content: 消息内容
        name: 发送者名称（可选，用于区分不同工具或用户）
        metadata: 额外元数据
    """
    role: str
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        return result
    
    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """创建系统消息"""
        return cls(role="system", content=content)
    
    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> ChatMessage:
        """创建用户消息"""
        return cls(role="user", content=content, name=name)
    
    @classmethod
    def assistant(cls, content: str) -> ChatMessage:
        """创建助手消息"""
        return cls(role="assistant", content=content)


@dataclass
class ModelUsage:
    """模型使用统计
    
    Attributes:
        prompt_tokens: 提示token数
        completion_tokens: 补全token数
        total_tokens: 总token数
        prompt_tokens_details: 提示token详情
        completion_tokens_details: 补全token详情
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = field(init=False)
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        self.total_tokens = self.prompt_tokens + self.completion_tokens
    
    @property
    def cost_estimate(self) -> float:
        """估算成本（简化计算，子类可覆盖）"""
        return 0.0


@dataclass
class ModelResponse:
    """标准化模型响应

    Attributes:
        content: 响应内容
        provider: 提供商名称
        model: 模型名称
        usage: Token使用统计
        finish_reason: 完成原因
        latency_ms: 响应延迟（毫秒）
        created_at: 创建时间
        metadata: 额外元数据
        thinking: 思维链内容（thinking 模型的 chain-of-thought；spec show-thinking-process）
    """
    content: str
    provider: str
    model: str
    usage: Optional[ModelUsage] = None
    finish_reason: Optional[FinishReason] = None
    latency_ms: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    thinking: str = ""  # spec show-thinking-process: thinking 模型的思维链，默认空串（向后兼容）
    
    @property
    def is_error(self) -> bool:
        """判断是否为错误响应"""
        return self.finish_reason == FinishReason.ERROR or self.content.startswith("Error:")


@dataclass
class EmbeddingResponse:
    """嵌入向量响应
    
    Attributes:
        embedding: 嵌入向量
        provider: 提供商名称
        model: 模型名称
        usage: Token使用统计
        latency_ms: 响应延迟（毫秒）
    """
    embedding: List[float]
    provider: str
    model: str
    usage: Optional[ModelUsage] = None
    latency_ms: Optional[float] = None


@dataclass
class StreamChunk:
    """流式响应块
    
    Attributes:
        content: 内容片段
        is_finished: 是否结束
        finish_reason: 完成原因
        usage: Token使用统计（通常在最后一块）
    """
    content: str
    is_finished: bool = False
    finish_reason: Optional[FinishReason] = None
    usage: Optional[ModelUsage] = None


class ModelConfig(PydanticBaseModel):
    """模型配置
    
    Attributes:
        model_name: 模型名称
        provider: 提供商
        api_key: API密钥
        base_url: 基础URL（用于自定义端点或代理）
        timeout: 请求超时（秒）
        max_retries: 最大重试次数
        temperature: 采样温度
        max_tokens: 最大生成token数
        top_p: 核采样参数
        frequency_penalty: 频率惩罚
        presence_penalty: 存在惩罚
        extra_params: 额外参数
    """
    model_name: str = Field(..., description="模型名称")
    provider: ModelProvider = Field(..., description="模型提供商")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="自定义基础URL")
    timeout: float = Field(default=60.0, ge=1.0, le=300.0, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(default=4096, ge=1, le=262144, description="最大生成token数 (1-256K)")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="额外参数")
    # === 新增：thinking 模型 + 降级链 + 流式 + worker 超时（spec fix-ollama-thinking-timeout）===
    think: bool = Field(default=True, description="是否允许 thinking 模型生成思维链（Ollama 0.9+ 支持 think=false 抑制）")  # spec show-thinking-process: 默认为 true
    fallback_models: List[str] = Field(default_factory=list, description="降级链：主模型超时后按顺序尝试的备选模型")
    stream: bool = Field(default=True, description="是否启用流式响应")
    worker_timeout: float = Field(default=180.0, ge=30, le=600, description="BrainWorker 等待模型响应的最大秒数；thinking 模型建议 180-300")
    
    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("模型名称不能为空")
        return v.strip()


class BaseModel(ABC):
    """大模型抽象基类
    
    所有大模型实现必须继承此类，并提供统一的调用接口。
    
    Attributes:
        config: 模型配置
        is_initialized: 是否已初始化
        capabilities: 模型能力列表
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.is_initialized = False
        self._capabilities: set[ModelCapability] = set()
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "avg_latency_ms": 0.0,
        }
    
    @property
    def provider(self) -> ModelProvider:
        """获取提供商"""
        return self.config.provider
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config.model_name
    
    @property
    def capabilities(self) -> set[ModelCapability]:
        """获取模型能力集合"""
        return self._capabilities.copy()
    
    def has_capability(self, capability: ModelCapability) -> bool:
        """检查是否支持某能力"""
        return capability in self._capabilities
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化模型连接
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """对话接口
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话接口
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Yields:
            StreamChunk: 流式响应块
        """
        pass
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """文本补全接口
        
        Args:
            prompt: 提示文本
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """获取文本嵌入向量
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 额外参数
            
        Returns:
            EmbeddingResponse 或 EmbeddingResponse列表
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 模型是否可用
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取模型状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "provider": self.provider.value,
            "model": self.model_name,
            "initialized": self.is_initialized,
            "capabilities": [c.value for c in self._capabilities],
            "stats": self._stats.copy(),
            "config": {
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
        }
    
    def _update_stats(self, latency_ms: float, tokens: int = 0, is_error: bool = False) -> None:
        """更新统计信息
        
        Args:
            latency_ms: 请求延迟
            tokens: 使用token数
            is_error: 是否错误
        """
        self._stats["total_requests"] += 1
        self._stats["total_tokens"] += tokens
        if is_error:
            self._stats["total_errors"] += 1
        
        # 更新平均延迟
        n = self._stats["total_requests"]
        self._stats["avg_latency_ms"] = (
            (self._stats["avg_latency_ms"] * (n - 1) + latency_ms) / n
        )
    
    def format_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """格式化消息为标准字典格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Dict[str, str]]: 格式化后的消息列表
        """
        return [msg.to_dict() for msg in messages]
    
    async def close(self) -> None:
        """关闭模型连接（子类可覆盖）"""
        self.is_initialized = False


class ModelError(Exception):
    """模型错误基类"""
    
    def __init__(self, message: str, provider: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.code = code
        self.timestamp = datetime.now()


class ModelNotInitializedError(ModelError):
    """模型未初始化错误"""
    pass


class ModelAPIError(ModelError):
    """模型API错误"""
    pass


class ModelRateLimitError(ModelAPIError):
    """速率限制错误"""
    pass


class ModelAuthenticationError(ModelAPIError):
    """认证错误"""
    pass


class ModelTimeoutError(ModelError):
    """超时错误"""
    pass
