"""
Ollama 本地模型集成

支持本地部署的开源大模型，自动发现本地 Ollama 服务。
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiohttp

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

logger = get_logger("models.ollama")


# Ollama 默认配置
_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=120)


class OllamaConnectionError(Exception):
    """结构化的 Ollama 连接错误（spec fix-ollama-connection-debug）

    把 aiohttp / asyncio 的底层异常统一映射为带有 stage 的结构化错误，
    方便 UI 层（BrainWorker）根据 stage 渲染针对性建议。

    Attributes:
        stage: 失败阶段, ∈ {TCP_CONNECT, HTTP_VERSION, HTTP_TAGS, HTTP_SHOW,
                            HTTP_CHAT, HTTP_CHAT_TIMEOUT, HTTP_EMBED}
        model: 涉及的模型名（如果适用）
        url: 请求的 URL
        detail: 原始错误描述
        suggestion: 给用户的修复建议
    """

    DEFAULT_SUGGESTIONS: Dict[str, str] = {
        "TCP_CONNECT": "请检查 Ollama 服务是否启动（运行 `ollama serve`）或端口是否被防火墙拦截",
        "HTTP_VERSION": "Ollama 服务异常，请重启 Ollama",
        "HTTP_TAGS": "请检查 base_url 是否正确",
        "HTTP_SHOW": "模型可能不存在或已损坏，请用 `ollama pull <model>` 重新拉取",
        "HTTP_CHAT": "模型推理失败，请检查模型状态或切换到 gemma2:2b",
        "HTTP_CHAT_TIMEOUT": "模型响应超时，请调高 worker_timeout 或切换到非 thinking 模型",
        "HTTP_EMBED": "Embedding 调用失败，请检查模型是否支持 embed",
    }

    def __init__(
        self,
        stage: str,
        url: str,
        detail: str,
        model: str = "",
        suggestion: str = "",
    ) -> None:
        self.stage = stage
        self.model = model
        self.url = url
        self.detail = detail
        self.suggestion = suggestion or self.DEFAULT_SUGGESTIONS.get(
            stage, "请检查 Ollama 服务状态"
        )
        super().__init__(f"Ollama {stage} failed @ {url}: {detail}")

    def to_dict(self) -> Dict[str, str]:
        """序列化为 BrainWorker 透传用的 dict。"""
        return {
            "code": "OLLAMA_CONNECT_FAIL",
            "stage": self.stage,
            "model": self.model,
            "url": self.url,
            "detail": self.detail,
            "suggestion": self.suggestion,
        }


class OllamaModelUsage(ModelUsage):
    """Ollama 模型使用统计"""
    
    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        super().__init__(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
    
    @property
    def cost_estimate(self) -> float:
        """本地模型成本为0"""
        return 0.0


class OllamaModel(BaseModel):
    """Ollama 模型实现
    
    通过 HTTP API 与本地 Ollama 服务通信，支持：
    - 自动发现本地 Ollama 服务
    - 列出可用模型
    - 对话和流式对话
    - 文本嵌入
    
    Attributes:
        session: aiohttp 客户端会话
        base_url: Ollama 服务基础 URL
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.base_url or _DEFAULT_BASE_URL
        # spec fix-ollama-thinking-timeout: 标记 thinking 模型
        self.is_thinking: bool = False
        self._think_supported: bool = True  # 探测后置 false
        # spec fix-ollama-connection-debug: 最近一次结构化连接错误
        self.last_connection_error: Optional[OllamaConnectionError] = None

        # 设置能力
        self._capabilities = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.EMBEDDING,
            ModelCapability.STREAMING,
            ModelCapability.CODE,
            ModelCapability.REASONING,
        }

        logger.info(f"OllamaModel initialized: {config.model_name} @ {self.base_url}")

    async def initialize(self, raise_structured: bool = False) -> bool:
        """初始化 HTTP 会话并测试连接

        spec fix-ollama-thinking-timeout: 同时探测 /api/show 设置 is_thinking
        spec fix-ollama-connection-debug: 把 ClientConnectorError /
            ClientResponseError / asyncio.TimeoutError 包装为
            OllamaConnectionError，默认 catch-all 仍 return False（向后兼容）。

        Args:
            raise_structured: 为 True 时，已知类型错误以 OllamaConnectionError
                              抛出；为 False（默认）时仍返回 bool，并把错误
                              存到 self.last_connection_error 供调用方检查。

        Returns:
            bool: 初始化是否成功（仅当 raise_structured=False 时保证返回 bool）
        """
        try:
            # 使用配置的 timeout，兜底 120 秒
            timeout_secs = getattr(self.config, 'timeout', 120) or 120
            client_timeout = aiohttp.ClientTimeout(total=float(timeout_secs))
            self.session = aiohttp.ClientSession(timeout=client_timeout)

            # 测试连接
            try:
                async with self.session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        self.is_initialized = True
                        logger.info(f"Ollama connection established at {self.base_url}")
                    else:
                        # HTTP 非 200：可能是 base_url 指向了非 Ollama 服务
                        err = OllamaConnectionError(
                            stage="HTTP_TAGS",
                            url=f"{self.base_url}/api/tags",
                            detail=f"HTTP {resp.status}",
                            model=self.config.model_name,
                        )
                        self.last_connection_error = err
                        logger.warning(f"Ollama returned status {resp.status}")
                        if raise_structured:
                            raise err
                        return False
            except aiohttp.ClientResponseError as e:
                err = OllamaConnectionError(
                    stage="HTTP_TAGS",
                    url=f"{self.base_url}/api/tags",
                    detail=f"HTTP {e.status}: {e.message}",
                    model=self.config.model_name,
                )
                self.last_connection_error = err
                logger.error(
                    f"Ollama /api/tags returned HTTP {e.status}: {e.message}"
                )
                if raise_structured:
                    raise err from e
                return False
            except asyncio.TimeoutError as e:
                err = OllamaConnectionError(
                    stage="HTTP_TAGS",
                    url=f"{self.base_url}/api/tags",
                    detail=f"Ollama 响应超时: {e}",
                    model=self.config.model_name,
                    suggestion="Ollama 响应超时",
                )
                self.last_connection_error = err
                logger.error(f"Ollama /api/tags timeout: {e}")
                if raise_structured:
                    raise err from e
                return False

            # 探测模型是否属于 thinking 家族（spec fix-ollama-thinking-timeout）
            # spec fix-ollama-connection-debug: 失败仅 WARN，不抛
            try:
                await self._probe_thinking_capability()
            except Exception as probe_err:
                logger.debug(f"thinking probe failed (non-fatal): {probe_err}")

            return True

        except aiohttp.ClientConnectorError as e:
            err = OllamaConnectionError(
                stage="TCP_CONNECT",
                url=self.base_url,
                detail=str(e),
                model=self.config.model_name,
            )
            self.last_connection_error = err
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            if raise_structured:
                raise err from e
            return False
        except OllamaConnectionError:
            # 内部 raise_structured 路径已经处理
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            return False

    async def _probe_thinking_capability(self) -> None:
        """通过 /api/show 探测当前模型是否为 thinking 模型。

        匹配家族名: qwen3* / deepseek-r1* / qwq* / qwen3.5*
        设置 self.is_thinking=True 并发出 UI 提示。
        """
        if not self.session:
            return
        try:
            payload = {"name": self.config.model_name}
            async with self.session.post(
                f"{self.base_url}/api/show",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.debug(f"/api/show returned {resp.status} for {self.config.model_name}")
                    return
                data = await resp.json()
        except Exception as e:
            logger.debug(f"/api/show probe failed: {e}")
            return

        try:
            family = (data.get("details") or {}).get("family", "") or ""
            capabilities = data.get("capabilities") or []
            model_info = data.get("model_info") or {}
            name_lower = (self.config.model_name or "").lower()
            family_lower = (family or "").lower()

            # 启发式判断
            thinking_markers = ["qwen3", "deepseek-r1", "qwq"]
            is_thinking = any(
                marker in name_lower or marker in family_lower
                for marker in thinking_markers
            )
            # capabilities 中可能含 "thinking"
            if isinstance(capabilities, list) and "thinking" in [str(c).lower() for c in capabilities]:
                is_thinking = True

            self.is_thinking = bool(is_thinking)
            logger.info(
                f"Ollama model probe: name={self.config.model_name} family={family} "
                f"capabilities={capabilities} is_thinking={self.is_thinking}"
            )

            if self.is_thinking:
                # 在主窗口可用时打状态栏提示
                try:
                    from PyQt6.QtCore import QMetaObject, Qt as _Qt
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app is not None:
                        for w in app.topLevelWidgets():
                            if hasattr(w, 'status_label') and hasattr(w, 'statusbar'):
                                msg = (
                                    f"已加载 thinking 模型 {self.config.model_name}，"
                                    f"建议关闭 think 或切换到非 thinking 模型"
                                )
                                w.status_label.setText(msg)
                                break
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"thinking parse failed: {e}")
    
    @classmethod
    async def discover(cls, base_url: Optional[str] = None) -> Optional[OllamaModel]:
        """自动发现本地 Ollama 服务
        
        尝试连接本地 Ollama 服务，如果成功则返回模型实例。
        
        Args:
            base_url: 指定基础 URL，默认尝试 localhost
            
        Returns:
            Optional[OllamaModel]: 如果找到则返回模型实例
        """
        urls_to_try = [base_url] if base_url else [
            _DEFAULT_BASE_URL,
            "http://127.0.0.1:11434",
        ]
        
        for url in urls_to_try:
            if not url:
                continue
            
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{url}/api/tags") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            models = data.get("models", [])
                            
                            if models:
                                # 使用第一个可用模型
                                model_name = models[0]["name"]
                                config = ModelConfig(
                                    model_name=model_name,
                                    provider=ModelProvider.OLLAMA,
                                    base_url=url
                                )
                                instance = cls(config)
                                instance.session = session
                                instance.is_initialized = True
                                logger.info(f"Discovered Ollama model: {model_name} at {url}")
                                return instance
                            else:
                                logger.warning(f"Ollama at {url} has no models")
                                
            except Exception as e:
                logger.debug(f"Ollama discovery failed for {url}: {e}")
                continue
        
        logger.info("No Ollama service found")
        return None
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """列出可用模型
        
        Returns:
            List[Dict[str, Any]]: 可用模型列表
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("models", [])
                else:
                    logger.warning(f"Failed to list models: HTTP {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    @with_retry(max_retries=2, base_delay=0.5, circuit_breaker_name="ollama_chat")
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """对话接口
        
        使用 Ollama Chat API 进行对话。
        
        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置，Ollama 中为 num_predict）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            ollama_messages = self.format_messages(messages)

            payload: Dict[str, Any] = {
                "model": self.config.model_name,
                "messages": ollama_messages,
                "stream": False,
            }

            # spec fix-ollama-thinking-timeout: 当 is_thinking 且配置 think=False 时抑制思维链
            try:
                if self.is_thinking and not bool(getattr(self.config, 'think', True)):
                    payload["think"] = False
            except Exception:
                pass

            # 构建 options
            options: Dict[str, Any] = {}
            if temperature is not None:
                options["temperature"] = temperature
            elif self.config.temperature is not None:
                options["temperature"] = self.config.temperature

            if max_tokens is not None:
                options["num_predict"] = max_tokens
            elif self.config.max_tokens is not None:
                options["num_predict"] = self.config.max_tokens

            if options:
                payload["options"] = options

            # 合并额外参数
            payload.update(self.config.extra_params)
            payload.update(kwargs)

            try:
                async with self.session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    if resp.status == 400 and "think" in payload:
                        # 旧版 Ollama 不支持 think 字段 → 回退重试
                        logger.warning(
                            f"Ollama /api/chat returned 400 (think not supported?); "
                            f"retrying without think field"
                        )
                        payload.pop("think", None)
                        async with self.session.post(
                            f"{self.base_url}/api/chat",
                            json=payload
                        ) as resp2:
                            return await self._parse_chat_response(resp2, start_time)
                    if resp.status != 200:
                        error_text = await resp.text()
                        # spec fix-ollama-connection-debug: 抛结构化错误
                        raise OllamaConnectionError(
                            stage="HTTP_CHAT",
                            url=f"{self.base_url}/api/chat",
                            detail=f"HTTP {resp.status}: {error_text}",
                            model=self.config.model_name,
                        )
                    return await self._parse_chat_response(resp, start_time)
            except asyncio.TimeoutError as e:
                # spec fix-ollama-connection-debug: chat 超时单独 stage
                raise OllamaConnectionError(
                    stage="HTTP_CHAT_TIMEOUT",
                    url=f"{self.base_url}/api/chat",
                    detail=f"模型响应超时: {e}",
                    model=self.config.model_name,
                ) from e
            except AttributeError:
                # 测试中 session 可能为 None
                raise
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            import traceback
            logger.error(f"Ollama chat error ({self.config.model_name}): {type(e).__name__}: {e}")
            logger.debug(traceback.format_exc())
            raise

    async def _chat_stream_internal(
        self,
        payload: Dict[str, Any],
        start_time: float,
    ) -> ModelResponse:
        """spec show-thinking-process: chat() 在 stream=True 时调用 stream_chat() 并 join

        流式调用 /api/chat，迭代 stream_chat() 产出的 (type, text) 元组，
        累加 thinking 和 content，返回 ModelResponse(thinking=..., content=...)。

        Args:
            payload: 已构造好的 /api/chat 请求体（必须含 "stream": True）
            start_time: 起始时间戳（用于 latency_ms）

        Returns:
            ModelResponse: 含完整 thinking + content 的响应
        """
        url = f"{self.base_url}/api/chat"
        try:
            # 用 stream_chat() 的内部迭代逻辑
            # 避免重复打开 session：直接用 session.post 迭代
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 400 and "think" in payload:
                    logger.warning(
                        f"Ollama /api/chat returned 400 (think not supported?); "
                        f"retrying without think field"
                    )
                    payload.pop("think", None)
                    async with self.session.post(url, json=payload) as resp2:
                        return await self._iter_stream_to_response(resp2, start_time)
                if resp.status != 200:
                    error_text = await resp.text()
                    raise OllamaConnectionError(
                        stage="HTTP_CHAT",
                        url=url,
                        detail=f"HTTP {resp.status}: {error_text}",
                        model=self.config.model_name,
                    )
                return await self._iter_stream_to_response(resp, start_time)
        except asyncio.TimeoutError as e:
            raise OllamaConnectionError(
                stage="HTTP_CHAT_TIMEOUT",
                url=url,
                detail=f"模型响应超时: {e}",
                model=self.config.model_name,
            ) from e
        except AttributeError:
            # 测试中 session 可能为 None
            raise

    async def _iter_stream_to_response(
        self, resp, start_time: float
    ) -> ModelResponse:
        """spec show-thinking-process: 迭代流式响应，累加 thinking + content，返回 ModelResponse"""
        full_thinking = ""
        full_content = ""
        last_data: Dict[str, Any] = {}

        async for line in resp.content:
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            last_data = data
            message = data.get("message", {})
            thinking_chunk = message.get("thinking", "") or ""
            content_chunk = message.get("content", "") or ""
            if thinking_chunk:
                full_thinking += thinking_chunk
            if content_chunk:
                full_content += content_chunk
            if data.get("done", False):
                break

        # 提取 usage
        usage = None
        if "prompt_eval_count" in last_data or "eval_count" in last_data:
            usage = OllamaModelUsage(
                prompt_tokens=last_data.get("prompt_eval_count", 0),
                completion_tokens=last_data.get("eval_count", 0)
            )
        latency_ms = (time.time() - start_time) * 1000
        total_tokens = usage.total_tokens if usage else 0
        self._update_stats(latency_ms, total_tokens, is_error=False)

        return ModelResponse(
            content=full_content,
            provider=self.provider.value,
            model=self.config.model_name,
            usage=usage,
            finish_reason=FinishReason.STOP,
            latency_ms=latency_ms,
            thinking=full_thinking,  # spec show-thinking-process
            metadata={
                "total_duration": last_data.get("total_duration"),
                "load_duration": last_data.get("load_duration"),
                "prompt_eval_duration": last_data.get("prompt_eval_duration"),
                "eval_duration": last_data.get("eval_duration"),
            },
        )

    async def _parse_chat_response(self, resp, start_time: float) -> ModelResponse:
        """解析 /api/chat 响应。"""
        data = await resp.json()
        latency_ms = (time.time() - start_time) * 1000

        # 提取内容
        msg = data.get("message", {})
        content = msg.get("content", "")

        # 某些模型（如 qwen3.5）可能将输出放在 thinking 字段
        if not content and msg.get("thinking"):
            content = msg.get("thinking", "")
            logger.debug(f"Using thinking field as content for {self.config.model_name}")

        # spec show-thinking-process: 提取 thinking 字段（思维链）
        # Ollama 0.30.7 thinking 字段位置可能在:
        #   - data.message.thinking (标准)
        #   - data.thinking (某些版本)
        thinking = ""
        try:
            if isinstance(msg, dict):
                thinking = msg.get("thinking", "") or ""
            if not thinking and isinstance(data, dict):
                thinking = data.get("thinking", "") or ""
        except Exception:
            thinking = ""

        # 提取使用统计
        usage = None
        if "prompt_eval_count" in data or "eval_count" in data:
            usage = OllamaModelUsage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0)
            )

        # 更新统计
        total_tokens = usage.total_tokens if usage else 0
        self._update_stats(latency_ms, total_tokens, is_error=False)

        return ModelResponse(
            content=content,
            provider=self.provider.value,
            model=self.config.model_name,
            usage=usage,
            finish_reason=FinishReason.STOP if not data.get("done_reason") else FinishReason.UNKNOWN,
            latency_ms=latency_ms,
            metadata={
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_duration": data.get("prompt_eval_duration"),
                "eval_duration": data.get("eval_duration"),
            },
            thinking=thinking,  # spec show-thinking-process
        )
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[Union[Tuple[str, str], StreamChunk], None]:
        """流式对话接口

        使用 Ollama Streaming API 进行流式对话。

        spec show-thinking-process: 分别 yield thinking 和 content 片段
        - thinking 模型: yield ("thinking", text) 和 ("content", text)
        - 非 thinking 模型: yield ("content", text)
        - 兼容老调用方: is_finished=True 的 StreamChunk 也被 yield

        Args:
            messages: 消息列表
            temperature: 采样温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            **kwargs: 额外参数

        Yields:
            Union[Tuple[str, str], StreamChunk]: 流式响应块
            - (type, text) 元组：type ∈ {"thinking", "content"}
            - StreamChunk(is_finished=True)：流结束信号（向后兼容）
        """
        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()

        try:
            ollama_messages = self.format_messages(messages)

            payload: Dict[str, Any] = {
                "model": self.config.model_name,
                "messages": ollama_messages,
                "stream": True,
            }

            # spec fix-ollama-thinking-timeout: 抑制思维链
            try:
                if self.is_thinking and not bool(getattr(self.config, 'think', True)):
                    payload["think"] = False
            except Exception:
                pass

            options: Dict[str, Any] = {}
            if temperature is not None:
                options["temperature"] = temperature
            elif self.config.temperature is not None:
                options["temperature"] = self.config.temperature

            if max_tokens is not None:
                options["num_predict"] = max_tokens
            elif self.config.max_tokens is not None:
                options["num_predict"] = self.config.max_tokens

            if options:
                payload["options"] = options

            payload.update(kwargs)

            try:
                async with self.session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        # spec fix-ollama-connection-debug: 抛结构化错误
                        raise OllamaConnectionError(
                            stage="HTTP_CHAT",
                            url=f"{self.base_url}/api/chat",
                            detail=f"HTTP {resp.status}: {error_text}",
                            model=self.config.model_name,
                        )

                    async for line in resp.content:
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # 提取内容
                        message = data.get("message", {})
                        # spec show-thinking-process: 分别 yield thinking 和 content
                        thinking_chunk = message.get("thinking", "") or ""
                        content_chunk = message.get("content", "") or ""

                        if thinking_chunk:
                            yield ("thinking", thinking_chunk)
                        if content_chunk:
                            yield ("content", content_chunk)

                        # 检查是否完成
                        if data.get("done", False):
                            usage = None
                            if "prompt_eval_count" in data or "eval_count" in data:
                                usage = OllamaModelUsage(
                                    prompt_tokens=data.get("prompt_eval_count", 0),
                                    completion_tokens=data.get("eval_count", 0)
                                )

                            # spec show-thinking-process: 用 StreamChunk(is_finished=True) 通知结束（向后兼容）
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
            except asyncio.TimeoutError as e:
                # spec fix-ollama-connection-debug: stream chat 超时单独 stage
                raise OllamaConnectionError(
                    stage="HTTP_CHAT_TIMEOUT",
                    url=f"{self.base_url}/api/chat",
                    detail=f"模型响应超时: {e}",
                    model=self.config.model_name,
                ) from e

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Ollama stream error: {e}")
            yield StreamChunk(
                content=f"Error: {str(e)}",
                is_finished=True,
                finish_reason=FinishReason.ERROR
            )
            raise
    
    @with_retry(max_retries=2, base_delay=0.5, circuit_breaker_name="ollama_complete")
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
    
    @with_retry(max_retries=2, base_delay=0.5, circuit_breaker_name="ollama_embed")
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """获取文本嵌入向量
        
        使用 Ollama Embeddings API。
        
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
            results: List[EmbeddingResponse] = []
            
            for input_text in inputs:
                payload = {
                    "model": self.config.model_name,
                    "input": input_text,
                }
                payload.update(kwargs)

                async with self.session.post(
                    f"{self.base_url}/api/embed",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama HTTP {resp.status}: {error_text}")

                    data = await resp.json()
                    # /api/embed 返回 {"embeddings": [[...]]}，兼容旧版 /api/embeddings 的 {"embedding": [...]}
                    embedding = data.get("embedding", [])
                    if not embedding:
                        embeddings_list = data.get("embeddings", [])
                        if embeddings_list:
                            embedding = embeddings_list[0]
                    
                    results.append(EmbeddingResponse(
                        embedding=embedding,
                        provider=self.provider.value,
                        model=self.config.model_name,
                        latency_ms=(time.time() - start_time) * 1000
                    ))
            
            self._update_stats((time.time() - start_time) * 1000, 0)
            
            return results if is_batch else results[0]
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_error=True)
            logger.error(f"Ollama embed error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康检查
        
        通过检查 Ollama 服务是否可访问来验证。
        
        Returns:
            bool: 模型是否可用
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def pull_model(self, model_name: Optional[str] = None) -> bool:
        """拉取模型
        
        从 Ollama 仓库拉取指定模型。
        
        Args:
            model_name: 要拉取的模型名称，默认使用当前配置
            
        Returns:
            bool: 是否成功
        """
        if not self.is_initialized:
            await self.initialize()
        
        target = model_name or self.config.model_name
        
        try:
            payload = {"name": target, "stream": False}
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Successfully pulled model: {target}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to pull model {target}: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to pull model {target}: {e}")
            return False
    
    async def close(self) -> None:
        """关闭 aiohttp session（spec comprehensive-debug-v2）"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.debug(f"Closed aiohttp session for {self.model_name}")
        self.is_initialized = False
