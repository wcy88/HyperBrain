"""
Google 模型集成

支持 Gemini 系列模型，提供生成内容 API 和嵌入功能。
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

logger = get_logger("models.google")


# Google 模型定价（每 1K tokens，美元）
_GOOGLE_PRICING = {
    "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
    "gemini-1.5-flash": {"prompt": 0.00035, "completion": 0.00105},
    "gemini-1.0-pro": {"prompt": 0.0005, "completion": 0.0015},
    "gemini-pro": {"prompt": 0.0005, "completion": 0.0015},
    "text-embedding-004": {"prompt": 0.0001, "completion": 0.0},
    "embedding-001": {"prompt": 0.0001, "completion": 0.0},
}

# 默认嵌入模型
_DEFAULT_EMBEDDING_MODEL = "text-embedding-004"


class GoogleModelUsage(ModelUsage):
    """Google 模型使用统计，包含成本估算"""
    
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
        pricing = _GOOGLE_PRICING.get(self.model, {"prompt": 0.0, "completion": 0.0})
        prompt_cost = (self.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (self.completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost


class GoogleModel(BaseModel):
    """Google (Gemini) 模型实现
    
    支持 Gemini 系列模型，通过 Google Generative AI API 提供以下功能：
    - 生成内容 (generateContent)
    - 流式生成 (streamGenerateContent)
    - 文本嵌入 (embedContent)
    
    Attributes:
        client: Google Generative AI 客户端
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
            ModelCapability.VISION,
            ModelCapability.CODE,
            ModelCapability.REASONING,
            ModelCapability.MULTILINGUAL,
            ModelCapability.FUNCTION_CALLING,
        }
        
        logger.info(f"GoogleModel initialized: {config.model_name}")
    
    async def initialize(self) -> bool:
        """初始化 Google Generative AI 客户端
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            import google.generativeai as genai
            
            api_key = self.config.api_key
            if not api_key:
                logger.warning("Google API key not provided")
                return False
            
            genai.configure(api_key=api_key)
            
            # 创建模型实例
            self.client = genai.GenerativeModel(self.config.model_name)
            self.is_initialized = True
            
            logger.info("Google Generative AI client initialized successfully")
            return True
            
        except ImportError:
            logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Google client: {e}")
            return False
    
    def _build_contents(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """构建 Google API 格式的内容列表
        
        Google Gemini API 使用 role: "user" / "model" 格式。
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Dict[str, Any]]: Google 格式的内容列表
        """
        contents = []
        
        for msg in messages:
            if msg.role == "system":
                # Google API 不直接支持 system 角色，转换为 user 角色并标注
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"[System Instruction]\n{msg.content}"}]
                })
            elif msg.role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })
            else:  # user
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
        
        return contents
    
    def _build_generation_config(self, temperature: Optional[float], max_tokens: Optional[int]) -> Dict[str, Any]:
        """构建生成配置
        
        Args:
            temperature: 采样温度
            max_tokens: 最大token数
            
        Returns:
            Dict[str, Any]: 生成配置
        """
        config: Dict[str, Any] = {}
        
        if temperature is not None:
            config["temperature"] = temperature
        elif self.config.temperature is not None:
            config["temperature"] = self.config.temperature
        
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
        elif self.config.max_tokens is not None:
            config["max_output_tokens"] = self.config.max_tokens
        
        if self.config.top_p is not None:
            config["top_p"] = self.config.top_p
        
        return config
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="google_chat")
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """对话接口
        
        使用 Google Generative AI API 进行对话。
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            contents = self._build_contents(messages)
            generation_config = self._build_generation_config(temperature, max_tokens)
            
            # 合并额外参数
            generation_config.update(self.config.extra_params)
            generation_config.update(kwargs)
            
            response = await self.client.generate_content_async(
                contents,
                generation_config=generation_config if generation_config else None
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 提取内容
            content = ""
            if response.parts:
                for part in response.parts:
                    if hasattr(part, "text"):
                        content += part.text
            elif hasattr(response, "text"):
                content = response.text
            
            # 提取使用统计
            usage = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                metadata = response.usage_metadata
                usage = GoogleModelUsage(
                    model=self.config.model_name,
                    prompt_tokens=getattr(metadata, "prompt_token_count", 0),
                    completion_tokens=getattr(metadata, "candidates_token_count", 0)
                )
            
            # 检查完成原因
            finish_reason = FinishReason.STOP
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    finish_reason = self._map_finish_reason(str(candidate.finish_reason))
            
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
                    "prompt_feedback": getattr(response, "prompt_feedback", None),
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Google chat error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话接口
        
        使用 Google Streaming API 进行流式对话。
        
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
            contents = self._build_contents(messages)
            generation_config = self._build_generation_config(temperature, max_tokens)
            generation_config.update(kwargs)
            
            stream = await self.client.generate_content_async(
                contents,
                generation_config=generation_config if generation_config else None,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.parts:
                    for part in chunk.parts:
                        if hasattr(part, "text") and part.text:
                            yield StreamChunk(content=part.text)
                
                # 检查是否结束
                if hasattr(chunk, "candidates") and chunk.candidates:
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, "finish_reason") and candidate.finish_reason:
                        finish_reason = self._map_finish_reason(str(candidate.finish_reason))
                        
                        # 获取使用统计
                        usage = None
                        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                            metadata = chunk.usage_metadata
                            usage = GoogleModelUsage(
                                model=self.config.model_name,
                                prompt_tokens=getattr(metadata, "prompt_token_count", 0),
                                completion_tokens=getattr(metadata, "candidates_token_count", 0)
                            )
                        
                        yield StreamChunk(
                            content="",
                            is_finished=True,
                            finish_reason=finish_reason,
                            usage=usage
                        )
                        
                        latency_ms = (time.time() - start_time) * 1000
                        total_tokens = usage.total_tokens if usage else 0
                        self._update_stats(latency_ms, total_tokens, is_error=False)
                        return
                        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Google stream error: {e}")
            yield StreamChunk(
                content=f"Error: {str(e)}",
                is_finished=True,
                finish_reason=FinishReason.ERROR
            )
            raise
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="google_complete")
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
    
    @with_retry(max_retries=3, base_delay=1.0, circuit_breaker_name="google_embed")
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """获取文本嵌入向量
        
        使用 Google Embedding API。
        
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
            import google.generativeai as genai
            
            results: List[EmbeddingResponse] = []
            
            for input_text in inputs:
                response = await genai.embed_content_async(
                    model=f"models/{self.embedding_model}",
                    content=input_text,
                    **kwargs
                )
                
                embedding = response.get("embedding", [])
                
                results.append(EmbeddingResponse(
                    embedding=embedding,
                    provider=self.provider.value,
                    model=self.embedding_model,
                    latency_ms=(time.time() - start_time) * 1000
                ))
            
            self._update_stats((time.time() - start_time) * 1000, 0)
            
            return results if is_batch else results[0]
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Google embed error: {e}")
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
            response = await self.client.generate_content_async(
                [{"role": "user", "parts": [{"text": "hi"}]}],
                generation_config={"max_output_tokens": 1}
            )
            return hasattr(response, "text") or (hasattr(response, "parts") and response.parts)
        except Exception as e:
            logger.warning(f"Google health check failed: {e}")
            return False
    
    def _map_finish_reason(self, reason: str) -> FinishReason:
        """映射 Google 完成原因到标准枚举
        
        Args:
            reason: Google 完成原因字符串
            
        Returns:
            FinishReason: 标准完成原因
        """
        mapping = {
            "STOP": FinishReason.STOP,
            "MAX_TOKENS": FinishReason.LENGTH,
            "SAFETY": FinishReason.CONTENT_FILTER,
            "RECITATION": FinishReason.CONTENT_FILTER,
            "OTHER": FinishReason.UNKNOWN,
        }
        return mapping.get(reason.upper(), FinishReason.UNKNOWN)
    
    async def close(self) -> None:
        """关闭客户端连接"""
        self.client = None
        self.is_initialized = False
        logger.info("Google client closed")
