"""
OpenAI 模型集成

支持 GPT-4、GPT-3.5 等模型，提供聊天补全、文本嵌入和流式响应功能。
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

logger = get_logger("models.openai")


# OpenAI 模型定价（每 1K tokens，美元）
_OPENAI_PRICING = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "text-embedding-3-small": {"prompt": 0.00002, "completion": 0.0},
    "text-embedding-3-large": {"prompt": 0.00013, "completion": 0.0},
    "text-embedding-ada-002": {"prompt": 0.0001, "completion": 0.0},
}

# 默认嵌入模型
_DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class OpenAIModelUsage(ModelUsage):
    """OpenAI 模型使用统计，包含成本估算"""
    
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
        pricing = _OPENAI_PRICING.get(self.model, {"prompt": 0.0, "completion": 0.0})
        prompt_cost = (self.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (self.completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost


class OpenAIModel(BaseModel):
    """OpenAI 模型实现
    
    支持 GPT-4、GPT-3.5 等模型，通过 OpenAI API 提供以下功能：
    - 聊天补全 (chat.completions)
    - 文本嵌入 (embeddings)
    - 流式响应 (streaming)
    
    Attributes:
        client: OpenAI 异步客户端
        embedding_model: 用于嵌入的模型名称
    """
    
    def __init__(self, config: ModelConfig, embedding_model: Optional[str] = None):
        super().__init__(config)
        self.client: Any = None
        self.embedding_model = embedding_model or _DEFAULT_EMBEDDING_MODEL
        
        # 设置能力
        self._capabilities = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.EMBEDDING,
            ModelCapability.STREAMING,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.JSON_MODE,
            ModelCapability.MULTILINGUAL,
        }
        
        # 视觉能力（仅特定模型）
        vision_models = {"gpt-4o", "gpt-4-turbo", "gpt-4-vision-preview"}
        if any(vm in config.model_name for vm in vision_models):
            self._capabilities.add(ModelCapability.VISION)
        
        # 代码能力（所有 GPT-4 模型）
        if "gpt-4" in config.model_name:
            self._capabilities.add(ModelCapability.CODE)
            self._capabilities.add(ModelCapability.REASONING)
        
        logger.info(f"OpenAIModel initialized: {config.model_name}")
    
    async def initialize(self) -> bool:
        """初始化 OpenAI 客户端
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            from openai import AsyncOpenAI
            
            client_kwargs: Dict[str, Any] = {}
            
            if self.config.api_key:
                client_kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            
            self.client = AsyncOpenAI(
                timeout=self.config.timeout,
                **client_kwargs
            )
            self.is_initialized = True
            
            logger.info("OpenAI client initialized successfully")
            return True
            
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return False
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="openai_chat")
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """对话接口
        
        使用 OpenAI Chat Completions API 进行对话。
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数（如 tools, response_format 等）
            
        Returns:
            ModelResponse: 模型响应
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            formatted_messages = self.format_messages(messages)
            
            params = {
                "model": self.config.model_name,
                "messages": formatted_messages,
                "temperature": temperature if temperature is not None else self.config.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
            }
            
            # 合并额外参数
            params.update(self.config.extra_params)
            params.update(kwargs)
            
            response = await self.client.chat.completions.create(**params)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 提取内容
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # 提取使用统计
            usage = None
            if response.usage:
                usage = OpenAIModelUsage(
                    model=self.config.model_name,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens or 0
                )
            
            # 映射完成原因
            finish_reason = self._map_finish_reason(choice.finish_reason)
            
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
                    "created": response.created,
                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"OpenAI chat error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话接口
        
        使用 OpenAI Streaming API 进行流式对话。
        
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
            formatted_messages = self.format_messages(messages)
            
            params = {
                "model": self.config.model_name,
                "messages": formatted_messages,
                "temperature": temperature if temperature is not None else self.config.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                "stream": True,
                "stream_options": {"include_usage": True},
            }
            params.update(kwargs)
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                
                if delta and delta.content:
                    yield StreamChunk(content=delta.content)
                
                # 检查是否结束
                finish_reason = chunk.choices[0].finish_reason if chunk.choices else None
                if finish_reason:
                    # 获取最终 usage（如果有）
                    usage = None
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage = OpenAIModelUsage(
                            model=self.config.model_name,
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens or 0
                        )
                    
                    yield StreamChunk(
                        content="",
                        is_finished=True,
                        finish_reason=self._map_finish_reason(finish_reason),
                        usage=usage
                    )
                    
                    latency_ms = (time.time() - start_time) * 1000
                    total_tokens = usage.total_tokens if usage else 0
                    self._update_stats(latency_ms, total_tokens, is_error=False)
                    break
                    
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"OpenAI stream error: {e}")
            yield StreamChunk(
                content=f"Error: {str(e)}",
                is_finished=True,
                finish_reason=FinishReason.ERROR
            )
            raise
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="openai_complete")
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
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="openai_embed")
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """获取文本嵌入向量
        
        使用 OpenAI Embeddings API。
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 额外参数
            
        Returns:
            EmbeddingResponse 或 EmbeddingResponse列表
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        is_batch = isinstance(text, list)
        inputs = text if is_batch else [text]
        
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=inputs,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            results: List[EmbeddingResponse] = []
            for item in response.data:
                usage = None
                if response.usage:
                    usage = OpenAIModelUsage(
                        model=self.embedding_model,
                        prompt_tokens=response.usage.total_tokens // len(inputs),
                        completion_tokens=0
                    )
                
                results.append(EmbeddingResponse(
                    embedding=item.embedding,
                    provider=self.provider.value,
                    model=self.embedding_model,
                    usage=usage,
                    latency_ms=latency_ms
                ))
            
            self._update_stats(latency_ms, response.usage.total_tokens if response.usage else 0)
            
            return results if is_batch else results[0]
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"OpenAI embed error: {e}")
            raise
    
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
            # 发送一个极简单的请求验证连接
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def _map_finish_reason(self, reason: Optional[str]) -> FinishReason:
        """映射 OpenAI 完成原因到标准枚举
        
        Args:
            reason: OpenAI 完成原因字符串
            
        Returns:
            FinishReason: 标准完成原因
        """
        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
            "tool_calls": FinishReason.TOOL_CALLS,
        }
        return mapping.get(reason or "", FinishReason.UNKNOWN)
    
    async def close(self) -> None:
        """关闭客户端连接"""
        if self.client:
            await self.client.close()
        self.is_initialized = False
        logger.info("OpenAI client closed")
