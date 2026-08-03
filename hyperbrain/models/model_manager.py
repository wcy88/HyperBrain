"""
模型管理器

统一管理所有模型，提供模型注册、发现、统一调用接口和配置管理。
"""

from __future__ import annotations

import asyncio
import os
import aiohttp
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, Union

from hyperbrain.core.config import ModelConfig as ConfigModelConfig, get_config
from hyperbrain.core.logger import get_logger
from .base import (
    BaseModel,
    ChatMessage,
    EmbeddingResponse,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    StreamChunk,
    TaskType,
)
from .capability_evaluator import CapabilityEvaluator, get_capability_evaluator
from .error_handler import ErrorHandler, get_error_handler
from .openai_model import OpenAIModel
from .scheduler import ModelScheduler
from .token_manager import BudgetConfig, TokenManager, get_token_manager

logger = get_logger("models.model_manager")


# 可选模型导入
try:
    from .anthropic_model import AnthropicModel
except ImportError:
    AnthropicModel = None

try:
    from .google_model import GoogleModel
except ImportError:
    GoogleModel = None

try:
    from .ollama_model import OllamaModel
except ImportError:
    OllamaModel = None


# 模型类映射
_MODEL_CLASS_MAP: Dict[ModelProvider, Type[BaseModel]] = {
    ModelProvider.OPENAI: OpenAIModel,
}

if AnthropicModel:
    _MODEL_CLASS_MAP[ModelProvider.ANTHROPIC] = AnthropicModel
if GoogleModel:
    _MODEL_CLASS_MAP[ModelProvider.GOOGLE] = GoogleModel
if OllamaModel:
    _MODEL_CLASS_MAP[ModelProvider.OLLAMA] = OllamaModel


class ModelManager:
    """模型管理器
    
    统一管理所有模型，作为系统与模型层交互的统一入口。
    
    功能：
    - 统一管理所有模型
    - 模型注册和发现
    - 统一调用接口
    - 配置管理
    - 与系统其他层交互
    
    Attributes:
        scheduler: 模型调度器
        token_manager: Token 管理器
        evaluator: 能力评估器
        error_handler: 错误处理器
        models: 已注册的模型
    """
    
    def __init__(
        self,
        budget_config: Optional[BudgetConfig] = None,
        auto_discover: bool = True
    ):
        self.token_manager = get_token_manager(budget_config)
        self.evaluator = get_capability_evaluator()
        self.error_handler = get_error_handler()
        self.scheduler = ModelScheduler(
            evaluator=self.evaluator,
            error_handler=self.error_handler,
            token_manager=self.token_manager
        )
        self.models: Dict[str, BaseModel] = {}
        self._initialized = False
        self._fallback_active_model: Optional[str] = None  # 跟踪降级后的激活模型名（不修改全局 config）

        if auto_discover:
            self._load_from_config()

        # spec fix-ollama-connection-debug: 任务5 + 任务6
        # 启动校验：注册摘要 + model_name 漂移告警 + fallback 存在性校验
        # 全部 best-effort，任何异常都不能影响 __init__ 主流程
        try:
            self._log_registration_summary()
        except Exception as e:
            logger.debug(f"_log_registration_summary failed: {e}")
        try:
            self._validate_fallback_models()
        except Exception as e:
            logger.debug(f"_validate_fallback_models failed: {e}")
    
    def _load_from_config(self) -> None:
        """从系统配置加载模型"""
        config = get_config().model
        
        # OpenAI
        if config.openai_api_key:
            self.register_model(
                name="openai_default",
                config=ModelConfig(
                    model_name=config.openai_model,
                    provider=ModelProvider.OPENAI,
                    api_key=config.openai_api_key,
                    base_url=config.openai_base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                ),
                priority=8
            )
        
        # Anthropic
        if config.anthropic_api_key:
            self.register_model(
                name="anthropic_default",
                config=ModelConfig(
                    model_name=config.anthropic_model,
                    provider=ModelProvider.ANTHROPIC,
                    api_key=config.anthropic_api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                ),
                priority=7
            )
        
        # Google
        if config.google_api_key:
            self.register_model(
                name="google_default",
                config=ModelConfig(
                    model_name=config.google_model,
                    provider=ModelProvider.GOOGLE,
                    api_key=config.google_api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                ),
                priority=6
            )
        
        # Ollama
        if OllamaModel and config.ollama_base_url:
            self.register_model(
                name="ollama_default",
                config=ModelConfig(
                    model_name=config.ollama_model,
                    provider=ModelProvider.OLLAMA,
                    base_url=config.ollama_base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                ),
                priority=9  # 本地模型优先级更高
            )

    def _log_registration_summary(self) -> None:
        """打印注册摘要，检测 model_name 漂移（spec fix-ollama-connection-debug 任务5）"""
        try:
            from hyperbrain.core.config import get_config
            cfg = get_config().model
        except Exception:
            return

        # 1) 打印所有注册模型
        for name, m in self.models.items():
            try:
                prov = getattr(m.provider, 'value', str(m.provider))
            except Exception:
                prov = "?"
            actual = getattr(m, 'model_name', '?')
            logger.info(f"[registration] {name}: provider={prov} model_name={actual}")

        # 2) 漂移检测：比较 cfg.ollama_model 与 ollama_default.model_name
        if "ollama_default" in self.models:
            actual_name = getattr(self.models["ollama_default"], 'model_name', None)
            cfg_name = getattr(cfg, 'ollama_model', None)
            if cfg_name and actual_name and cfg_name != actual_name:
                logger.error(
                    f"[drift] model_name mismatch: config.ollama_model={cfg_name!r} "
                    f"but ollama_default.model_name={actual_name!r}. "
                    f"Check if any code overrides config after _load_from_config."
                )
                # 通知状态栏（best effort）
                try:
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app is not None:
                        for w in app.topLevelWidgets():
                            if hasattr(w, 'status_label'):
                                try:
                                    w.status_label.setText(
                                        f"⚠ 模型名漂移: 配置={cfg_name}, 实际={actual_name}"
                                    )
                                except Exception:
                                    pass
                                break
                except Exception:
                    pass
        else:
            if getattr(cfg, 'ollama_base_url', None):
                logger.warning(
                    f"[registration] config.ollama_base_url={cfg.ollama_base_url} but "
                    f"ollama_default is not registered (Ollama unavailable?)"
                )

    def _validate_fallback_models(self) -> None:
        """校验 cfg.fallback_models 中的每个模型是否在 Ollama /api/tags 中存在

        spec fix-ollama-connection-debug 任务6:
        - 启动时对每个 fallback 调 /api/tags 比对
        - 不存在 → 状态栏 WARN + 日志 WARN
        - chat_with_fallback() 在 chain 中跳过不存在的（已通过 try/except 实现，
          但要确保这里给出明确日志）
        """
        try:
            from hyperbrain.core.config import get_config
            cfg = get_config().model
        except Exception:
            return
        fb = getattr(cfg, 'fallback_models', None)
        if not fb or not isinstance(fb, (list, tuple)):
            return
        if "ollama_default" not in self.models:
            logger.warning("[fallback-validation] skip: ollama_default not registered")
            return
        try:
            import aiohttp as _aiohttp
            aiohttp = _aiohttp
        except Exception:
            logger.debug("[fallback-validation] aiohttp not available, skip")
            return
        base_url = (
            getattr(cfg, 'ollama_base_url', None)
            or 'http://127.0.0.1:11434'
        )

        async def _check() -> list:
            timeout = aiohttp.ClientTimeout(total=5)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as s:
                    try:
                        async with s.get(f"{base_url}/api/tags") as r:
                            if r.status != 200:
                                logger.warning(
                                    f"[fallback-validation] /api/tags returned {r.status}, skip"
                                )
                                return []
                            data = await r.json()
                            available = {m.get("name") for m in data.get("models", [])}
                    except Exception as e:
                        logger.warning(
                            f"[fallback-validation] /api/tags failed: {e}, skip"
                        )
                        return []
            except Exception as e:
                logger.debug(f"[fallback-validation] session failed: {e}")
                return []

            missing = []
            for name in fb:
                if not name or name in available:
                    continue
                missing.append(name)
                logger.warning(
                    f"[fallback-validation] fallback model {name!r} not in /api/tags, "
                    f"will be skipped in chat_with_fallback"
                )
            if missing:
                # 状态栏 WARN
                try:
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app is not None:
                        msg = f"⚠ fallback 模型不存在: {', '.join(missing)}（将被忽略）"
                        for w in app.topLevelWidgets():
                            if hasattr(w, 'status_label'):
                                try:
                                    w.status_label.setText(msg)
                                except Exception:
                                    pass
                                break
                except Exception:
                    pass
            return missing

        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 已在 async 上下文 → 跳过（外部会在 initialize_all 后调）
                    logger.debug(
                        "[fallback-validation] loop running, defer validation"
                    )
                    return
            except RuntimeError:
                pass
            asyncio.run(_check())
        except Exception as e:
            logger.debug(f"[fallback-validation] async run failed: {e}")
    
    def register_model(
        self,
        name: str,
        config: ModelConfig,
        priority: int = 5,
        weight: float = 1.0
    ) -> Optional[BaseModel]:
        """注册模型
        
        Args:
            name: 模型标识名
            config: 模型配置
            priority: 调度优先级
            weight: 负载均衡权重
            
        Returns:
            Optional[BaseModel]: 创建的模型实例
        """
        model_class = _MODEL_CLASS_MAP.get(config.provider)
        if not model_class:
            logger.error(f"Unknown provider: {config.provider}")
            return None
        
        try:
            model = model_class(config)
            self.models[name] = model
            self.scheduler.register_model(name, model, priority=priority, weight=weight)
            
            logger.info(f"Registered model: {name} ({config.provider.value}/{config.model_name})")
            return model
            
        except Exception as e:
            logger.error(f"Failed to register model {name}: {e}")
            return None
    
    def unregister_model(self, name: str) -> None:
        """注销模型
        
        Args:
            name: 模型标识名
        """
        if name in self.models:
            del self.models[name]
            self.scheduler.unregister_model(name)
            logger.info(f"Unregistered model: {name}")
    
    async def initialize_all(self) -> Dict[str, bool]:
        """初始化所有模型
        
        Returns:
            Dict[str, bool]: 初始化结果
        """
        results = {}
        
        for name, model in self.models.items():
            try:
                success = await model.initialize()
                results[name] = success
                
                if success:
                    logger.info(f"Initialized model: {name}")
                else:
                    logger.warning(f"Failed to initialize model: {name}")
                    
            except Exception as e:
                logger.error(f"Error initializing model {name}: {e}")
                results[name] = False
        
        self._initialized = True
        return results
    
    async def discover_local_models(self) -> List[str]:
        """发现本地模型
        
        自动发现本地 Ollama 服务并注册所有可用模型。
        
        Returns:
            List[str]: 发现的模型名称列表
        """
        discovered: List[str] = []
        
        if OllamaModel is None:
            logger.warning("OllamaModel not available for discovery")
            return discovered
        
        try:
            # 获取配置中的 Ollama 基础 URL
            config = get_config()
            base_url = config.model.ollama_base_url
            logger.info(f"Attempting to discover models from Ollama at {base_url}")
            
            # 先获取模型列表
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{base_url}/api/tags") as resp:
                    if resp.status != 200:
                        logger.warning(f"Ollama /api/tags returned status {resp.status}")
                        return discovered
                    
                    data = await resp.json()
                    models = data.get("models", [])
            
            logger.info(f"Found {len(models)} local Ollama models")
            
            # 为每个模型创建独立实例并初始化
            for model_info in models:
                model_name = model_info["name"]
                name = f"ollama_{model_name.replace(':', '_')}"
                
                # 如果已注册则跳过
                if name in self.models:
                    logger.debug(f"Model {name} already registered, skipping")
                    continue
                
                logger.info(f"Creating model instance for {model_name}")
                ollama_config = ModelConfig(
                    model_name=model_name,
                    provider=ModelProvider.OLLAMA,
                    base_url=base_url,
                    temperature=config.model.temperature,
                    max_tokens=config.model.max_tokens,
                    timeout=config.model.timeout,
                )
                
                model = OllamaModel(ollama_config)
                # 让每个模型管理自己的 session
                success = await model.initialize()
                if not success:
                    logger.warning(f"Failed to initialize model {name}")
                    continue
                
                self.models[name] = model
                # 发现的模型优先级低于默认模型（默认模型 priority=9）
                self.scheduler.register_model(name, model, priority=5)
                discovered.append(name)
                logger.info(f"Discovered local model: {name}")
        except Exception as e:
            logger.warning(f"Local model discovery failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        logger.info(f"Discovery complete. Found {len(discovered)} new models")
        return discovered
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        task_type: TaskType = TaskType.CHAT,
        **kwargs: Any
    ) -> ModelResponse:
        """统一对话接口

        Args:
            messages: 消息列表
            model_name: 指定模型名
            task_type: 任务类型
            **kwargs: 额外参数

        Returns:
            ModelResponse: 模型响应
        """
        if not self._initialized:
            await self.initialize_all()

        return await self.scheduler.chat(
            messages=messages,
            model_name=model_name,
            task_type=task_type,
            **kwargs
        )

    async def chat_with_fallback(
        self,
        messages: List[ChatMessage],
        primary_model: str = "ollama_default",
        fallback_models: Optional[List[str]] = None,
        fallback_per_call_timeout: float = 30.0,
        **kwargs: Any,
    ) -> ModelResponse:
        """带降级链的对话（spec fix-ollama-thinking-timeout）。

        - 先尝试 primary_model（受 BrainWorker.worker_timeout 控制）
        - 抛 asyncio.TimeoutError 时，按 fallback_models 顺序切换 ollama_default 重新调用
        - 全部失败时抛出最后异常
        - 切换时 emit "model_fallback" 回调（best effort）

        Args:
            messages: 消息列表
            primary_model: 主模型注册名（默认 ollama_default）
            fallback_models: 降级链模型名（注册名或 ollama 模型名）
            fallback_per_call_timeout: 每次重试的硬超时（秒），仅作兜底
            **kwargs: 传给 chat 的额外参数

        Returns:
            ModelResponse: 成功的模型响应
        """
        chain: List[str] = [primary_model]
        if fallback_models:
            chain.extend([m for m in fallback_models if m and m != primary_model])

        last_exc: Optional[Exception] = None
        for idx, model_name in enumerate(chain):
            try:
                if idx == 0:
                    # 主模型：原样调用
                    return await self.chat(
                        messages=messages,
                        model_name=model_name,
                        **kwargs,
                    )
                else:
                    # 降级：unregister 旧的 ollama_default，register fallback，再 chat
                    self._swap_to_fallback_model(model_name)
                    logger.info(
                        f"chat_with_fallback: switching to fallback model={model_name}"
                    )
                    # 通知监听器（UI 状态栏）
                    self._notify_fallback(primary_model, model_name)
                    return await self.chat(
                        messages=messages,
                        model_name="ollama_default",
                        **kwargs,
                    )
            except asyncio.TimeoutError as e:
                last_exc = e
                logger.warning(
                    f"chat_with_fallback: model {model_name} timed out, trying next"
                )
                # 不做 sleep，立即尝试下一个
                continue
            except Exception as e:
                last_exc = e
                # 非超时错误：决定是否继续
                logger.warning(
                    f"chat_with_fallback: model {model_name} failed: {type(e).__name__}: {e}"
                )
                # 若是 connection-level error 也尝试 fallback
                err_name = type(e).__name__.lower()
                if "timeout" in err_name or "connect" in err_name or "connection" in err_name:
                    continue
                # 其他错误（如 4xx 业务错误）也继续，避免卡死
                continue

        # 全部失败
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("chat_with_fallback: empty chain")

    def _swap_to_fallback_model(self, model_name: str) -> None:
        """把 ollama_default 替换为 fallback 模型名（同步 best-effort）。"""
        try:
            from hyperbrain.core.config import get_config
            from hyperbrain.models.base import ModelConfig, ModelProvider
            cfg = get_config().model
            # 如果传入的 model_name 已经是 ollama_xxx 注册名，直接用
            if model_name in self.models:
                target_name = model_name
                target_model = self.models[model_name]
            else:
                # 视为 ollama 模型名（裸名）
                target_name = "ollama_default"
                target_model = OllamaModel(ModelConfig(
                    model_name=model_name,
                    provider=ModelProvider.OLLAMA,
                    base_url=cfg.ollama_base_url,
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                    timeout=cfg.timeout,
                )) if OllamaModel else None
                if target_model is not None:
                    # 同步初始化（不阻塞太久）
                    try:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # 已在 async 上下文，跳过同步 init
                                pass
                        except RuntimeError:
                            pass
                    except Exception:
                        pass
            # 替换 ollama_default
            if target_model is not None:
                try:
                    self.unregister_model("ollama_default")
                except Exception:
                    pass
                self.register_model(
                    name="ollama_default",
                    config=target_model.config,
                    priority=9,
                )
                # 记录降级后的激活模型名（不修改全局 config，避免污染配置）
                self._fallback_active_model = target_model.model_name
        except Exception as e:
            logger.warning(f"_swap_to_fallback_model failed: {e}")

    def _notify_fallback(self, from_model: str, to_model: str) -> None:
        """通知监听器发生模型降级（best effort）。"""
        try:
            from PyQt6.QtCore import QObject
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                return
            for w in app.topLevelWidgets():
                if hasattr(w, 'status_label'):
                    msg = f"主模型 {from_model} 超时，已自动切换到 {to_model}"
                    w.status_label.setText(msg)
                    break
        except Exception:
            pass

    async def set_active_model(self, name: str, config: Optional[ModelConfig] = None) -> None:
        """切换/激活指定模型（spec fix-ollama-thinking-timeout 配套）。"""
        if config is not None:
            self.register_model(name=name, config=config, priority=9)
        if hasattr(self, '_initialized'):
            self._initialized = True
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        task_type: TaskType = TaskType.CHAT,
        **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        """统一流式对话接口
        
        Args:
            messages: 消息列表
            model_name: 指定模型名
            task_type: 任务类型
            **kwargs: 额外参数
            
        Yields:
            StreamChunk: 流式响应块
        """
        if not self._initialized:
            await self.initialize_all()
        
        async for chunk in self.scheduler.stream_chat(
            messages=messages,
            model_name=model_name,
            task_type=task_type,
            **kwargs
        ):
            yield chunk
    
    async def complete(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        task_type: TaskType = TaskType.COMPLETION,
        **kwargs: Any
    ) -> ModelResponse:
        """统一补全接口
        
        Args:
            prompt: 提示文本
            model_name: 指定模型名
            task_type: 任务类型
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        messages = [ChatMessage.user(prompt)]
        return await self.chat(
            messages=messages,
            model_name=model_name,
            task_type=task_type,
            **kwargs
        )
    
    async def embed(
        self,
        text: Union[str, List[str]],
        model_name: Optional[str] = None,
        **kwargs: Any
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """统一嵌入接口
        
        Args:
            text: 输入文本或文本列表
            model_name: 指定模型名
            **kwargs: 额外参数
            
        Returns:
            EmbeddingResponse 或 EmbeddingResponse列表
        """
        if not self._initialized:
            await self.initialize_all()
        
        # 查找支持嵌入的模型
        if model_name and model_name in self.models:
            model = self.models[model_name]
        else:
            # 选择支持嵌入的模型
            model = None
            for name, m in self.models.items():
                if m.has_capability(ModelCapability.EMBEDDING) and m.is_initialized:
                    model = m
                    break
            
            if not model:
                # 尝试初始化第一个支持嵌入的模型
                for name, m in self.models.items():
                    if m.has_capability(ModelCapability.EMBEDDING):
                        await m.initialize()
                        model = m
                        break
        
        if not model:
            raise RuntimeError("No model available for embedding")
        
        return await model.embed(text, **kwargs)
    
    def get_model(self, name: str) -> Optional[BaseModel]:
        """获取指定模型
        
        Args:
            name: 模型标识名
            
        Returns:
            Optional[BaseModel]: 模型实例
        """
        return self.models.get(name)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有模型
        
        Returns:
            List[Dict[str, Any]]: 模型信息列表
        """
        return [
            {
                "name": name,
                "provider": model.provider.value,
                "model_name": model.model_name,
                "initialized": model.is_initialized,
                "capabilities": [c.value for c in model.capabilities],
            }
            for name, model in self.models.items()
        ]
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表
        
        Returns:
            List[Dict[str, Any]]: 可用模型信息列表
        """
        return self.scheduler.get_available_models()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有模型健康状态
        
        Returns:
            Dict[str, bool]: 健康状态字典
        """
        return await self.scheduler.health_check_all()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_models": len(self.models),
            "scheduler_stats": self.scheduler.get_stats(),
            "budget_status": self.token_manager.get_budget_status(),
        }
    
    def get_budget_status(self) -> Dict[str, Any]:
        """获取预算状态
        
        Returns:
            Dict[str, Any]: 预算状态
        """
        return self.token_manager.get_budget_status()
    
    async def evaluate_all_models(self) -> Dict[str, Any]:
        """评估所有模型
        
        Returns:
            Dict[str, Any]: 评估结果
        """
        return await self.scheduler.evaluate_all_models()
    
    def set_scheduling_strategy(self, strategy: str) -> None:
        """设置调度策略
        
        Args:
            strategy: 策略名称
        """
        self.scheduler.set_strategy(strategy)
    
    async def close_all(self) -> None:
        """关闭所有模型连接"""
        # spec comprehensive-debug-v2: 显式关闭每个模型的 aiohttp session，
        # 避免 Unclosed client session 警告
        for name, model in list(self.models.items()):
            try:
                close_fn = getattr(model, "close", None)
                if close_fn is not None:
                    await close_fn()
            except Exception as e:
                logger.warning(f"Error closing model {name}: {e}")
        await self.scheduler.close_all()
        self._initialized = False
        logger.info("All models closed")
    
    async def __aenter__(self) -> ModelManager:
        """异步上下文管理器入口"""
        await self.initialize_all()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close_all()


# 全局模型管理器实例
_global_model_manager: Optional[ModelManager] = None


def get_model_manager(
    budget_config: Optional[BudgetConfig] = None,
    auto_discover: bool = True
) -> ModelManager:
    """获取全局模型管理器
    
    Args:
        budget_config: 预算配置
        auto_discover: 是否自动发现模型
        
    Returns:
        ModelManager: 模型管理器实例
    """
    global _global_model_manager
    if _global_model_manager is None:
        _global_model_manager = ModelManager(budget_config, auto_discover)
    return _global_model_manager
