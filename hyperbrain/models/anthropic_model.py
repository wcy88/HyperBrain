"""
Anthropic 模型集成

支持 Claude 系列模型，提供 Messages API 和流式响应功能。
"""

from __future__ import annotations

import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from hyperbrain.core.logger import get_logger
from .base import (
    BaseModel,
    ChatMessage,
    EmbeddingResponse,
    FinishReason,
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ModelUsage,
    StreamChunk,
)
from .error_handler import with_retry

logger = get_logger("models.anthropic")


# Anthropic 模型定价（每 1K tokens，美元）
_ANTHROPIC_PRICING = {
    "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
    "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-haiku-20241022": {"prompt": 0.0008, "completion": 0.004},
}


class AnthropicModelUsage(ModelUsage):
    """Anthropic 模型使用统计，包含成本估算"""
    
    def __init__(self, model: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        super().__init__(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        self.model = model
    
    @property
    def cost_estimate(self) -> float:
        """估算成本（美元）"""
        pricing = _ANTHROPIC_PRICING.get(self.model, {"prompt": 0.0, "completion": 0.0})
        prompt_cost = (self.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (self.completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost


class AnthropicModel(BaseModel):
    """Anthropic 模型实现
    
    支持 Claude 系列模型，通过 Anthropic Messages API 提供以下功能：
    - 对话 (messages)
    - 流式响应 (streaming)
    - 工具调用 (tool use)
    
    注意：Anthropic 目前不提供嵌入 API，embed 方法将抛出 NotImplementedError。
    
    Attributes:
        client: Anthropic 异步客户端
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client: Any = None
        
        # 设置能力
        self._capabilities = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.CODE,
            ModelCapability.REASONING,
            ModelCapability.MULTILINGUAL,
        }
        
        logger.info(f"AnthropicModel initialized: {config.model_name}")
    
    async def initialize(self) -> bool:
        """初始化 Anthropic 客户端
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            from anthropic import AsyncAnthropic
            
            client_kwargs: Dict[str, Any] = {}
            
            if self.config.api_key:
                client_kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            
            self.client = AsyncAnthropic(
                timeout=self.config.timeout,
                **client_kwargs
            )
            self.is_initialized = True
            
            logger.info("Anthropic client initialized successfully")
            return True
            
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            return False
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="anthropic_chat")
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """对话接口
        
        使用 Anthropic Messages API 进行对话。
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置，Anthropic 要求必须提供）
            **kwargs: 额外参数（如 tools, system 等）
            
        Returns:
            ModelResponse: 模型响应
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # 分离 system 消息
            system_message = None
            chat_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            params: Dict[str, Any] = {
                "model": self.config.model_name,
                "messages": chat_messages,
                "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            }
            
            # Anthropic 的 temperature 参数
            if temperature is not None:
                params["temperature"] = temperature
            elif self.config.temperature is not None:
                params["temperature"] = self.config.temperature
            
            # 添加 system 消息
            if system_message:
                params["system"] = system_message
            
            # 合并额外参数
            params.update(self.config.extra_params)
            params.update(kwargs)
            
            response = await self.client.messages.create(**params)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 提取内容
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text
            
            # 提取使用统计
            usage = None
            if response.usage:
                usage = AnthropicModelUsage(
                    model=self.config.model_name,
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens
                )
            
            # 映射完成原因
            finish_reason = self._map_finish_reason(response.stop_reason)
            
            # 更新统计
            total_tokens = usage.total_tokens if usage else 0
            self._update_stats(latency_ms, total_tokens, is_error=False)
            
            return ModelResponse(
                content=content,
                provider=self.provider.value,
                model=self.config.model_name,
                usage=usage,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
                metadata={
                    "response_id": response.id,
                    "model_version": response.model,
                    "stop_sequence": response.stop_sequence,
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Anthropic chat error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话接口
        
        使用 Anthropic Streaming API 进行流式对话。
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Yields:
            StreamChunk: 流式响应块
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # 分离 system 消息
            system_message = None
            chat_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            params: Dict[str, Any] = {
                "model": self.config.model_name,
                "messages": chat_messages,
                "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                "stream": True,
            }
            
            if temperature is not None:
                params["temperature"] = temperature
            elif self.config.temperature is not None:
                params["temperature"] = self.config.temperature
            
            if system_message:
                params["system"] = system_message
            
            params.update(kwargs)
            
            stream = await self.client.messages.create(**params)
            
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield StreamChunk(content=event.delta.text)
                
                elif event.type == "message_stop":
                    # 获取最终统计
                    usage = None
                    if hasattr(event, "message") and event.message.usage:
                        usage = AnthropicModelUsage(
                            model=self.config.model_name,
                            prompt_tokens=event.message.usage.input_tokens,
                            completion_tokens=event.message.usage.output_tokens
                        )
                    
                    yield StreamChunk(
                        content="",
                        is_finished=True,
                        finish_reason=FinishReason.STOP,
                        usage=usage
                    )
                    
                    latency_ms = (time.time() - start_time) * 1000
                    total_tokens = usage.total_tokens if usage else 0
                    self._update_stats(latency_ms, total_tokens, is_error=False)
                    break
                    
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Anthropic stream error: {e}")
            yield StreamChunk(
                content=f"Error: {str(e)}",
                is_finished=True,
                finish_reason=FinishReason.ERROR
            )
            raise
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="anthropic_complete")
    async def complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """文本补全接口
        
        将 prompt 包装为 user 消息调用 chat 接口。
        
        Args:
            prompt: 提示文本
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        messages = [ChatMessage.user(prompt)]
        return await self.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)
    
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """获取文本嵌入向量
        
        Anthropic 目前不提供嵌入 API，此方法将抛出 NotImplementedError。
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 额外参数
            
        Raises:
            NotImplementedError: Anthropic 不支持嵌入 API
        """
        raise NotImplementedError("Anthropic does not provide an embedding API. Use OpenAI or other providers for embeddings.")
    
    async def health_check(self) -> bool:
        """健康检查
        
        通过简单的 API 调用验证模型可用性。
        
        Returns:
            bool: 模型是否可用
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        try:
            response = await self.client.messages.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            return len(response.content) > 0
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False
    
    def _map_finish_reason(self, reason: Optional[str]) -> FinishReason:
        """映射 Anthropic 完成原因到标准枚举
        
        Args:
            reason: Anthropic 完成原因字符串
            
        Returns:
            FinishReason: 标准完成原因
        """
        mapping = {
            "end_turn": FinishReason.STOP,
            "max_tokens": FinishReason.LENGTH,
            "stop_sequence": FinishReason.STOP,
            "tool_use": FinishReason.TOOL_CALLS,
        }
        return mapping.get(reason or "", FinishReason.UNKNOWN)
    
    async def close(self) -> None:
        """关闭客户端连接"""
        if self.client:
            await self.client.close()
        self.is_initialized = False
        logger.info("Anthropic client closed")
