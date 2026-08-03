"""
模型调度器

提供模型择优调度、负载均衡、故障切换、模型能力评估和调用统计监控。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from hyperbrain.core.logger import get_logger
from .base import (
    BaseModel,
    ChatMessage,
    ModelCapability,
    ModelProvider,
    ModelResponse,
    StreamChunk,
    TaskType,
)
from .capability_evaluator import CapabilityEvaluator, get_capability_evaluator
from .error_handler import ErrorHandler, get_error_handler
from .token_manager import TokenManager, get_token_manager

logger = get_logger("models.scheduler")


@dataclass
class ModelInstance:
    """模型实例包装
    
    Attributes:
        model: 模型实例
        name: 实例名称
        priority: 优先级（越高越优先）
        weight: 负载均衡权重
        is_available: 是否可用
        avg_latency_ms: 平均延迟
        error_rate: 错误率
        last_used: 最后使用时间
        call_count: 调用次数
        total_tokens: 总token数
    """
    model: BaseModel
    name: str
    priority: int = 5
    weight: float = 1.0
    is_available: bool = True
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    last_used: Optional[datetime] = None
    call_count: int = 0
    total_tokens: int = 0


@dataclass
class SchedulingDecision:
    """调度决策结果
    
    Attributes:
        model_name: 选中的模型名称
        provider: 提供商
        reason: 选择原因
        score: 调度得分
    """
    model_name: str
    provider: str
    reason: str
    score: float


class ModelScheduler:
    """模型调度器
    
    管理多个模型的选择、负载均衡和故障切换。
    
    功能：
    - 模型择优调度：根据任务类型选择最优模型
    - 负载均衡：均匀分配请求
    - 故障切换：自动切换到可用模型
    - 模型能力评估：基于评估结果选择
    - 调用统计和监控
    
    Attributes:
        models: 注册的模型实例
        default_model: 默认模型名称
        evaluator: 能力评估器
        error_handler: 错误处理器
        token_manager: Token 管理器
    """
    
    def __init__(
        self,
        evaluator: Optional[CapabilityEvaluator] = None,
        error_handler: Optional[ErrorHandler] = None,
        token_manager: Optional[TokenManager] = None
    ):
        self.models: Dict[str, ModelInstance] = {}
        self.default_model: Optional[str] = None
        self.evaluator = evaluator or get_capability_evaluator()
        self.error_handler = error_handler or get_error_handler()
        self.token_manager = token_manager or get_token_manager()
        
        # 任务类型到能力的映射
        self._task_capability_map = {
            TaskType.CHAT: ModelCapability.CHAT,
            TaskType.COMPLETION: ModelCapability.COMPLETION,
            TaskType.EMBEDDING: ModelCapability.EMBEDDING,
            TaskType.REASONING: ModelCapability.REASONING,
            TaskType.CODE: ModelCapability.CODE,
            TaskType.CREATIVE: ModelCapability.CHAT,
            TaskType.ANALYSIS: ModelCapability.REASONING,
            TaskType.SUMMARIZATION: ModelCapability.CHAT,
            TaskType.TRANSLATION: ModelCapability.MULTILINGUAL,
        }
        
        # 调度策略
        self._strategy = "adaptive"  # adaptive, round_robin, priority, capability
        self._round_robin_index = 0
        
        logger.info("ModelScheduler initialized")
    
    def register_model(
        self,
        name: str,
        model: BaseModel,
        priority: int = 5,
        weight: float = 1.0
    ) -> None:
        """注册模型
        
        Args:
            name: 模型标识名
            model: 模型实例
            priority: 优先级（1-10，越高越优先）
            weight: 负载均衡权重
        """
        self.models[name] = ModelInstance(
            model=model,
            name=name,
            priority=priority,
            weight=weight
        )
        
        if self.default_model is None:
            self.default_model = name
        
        logger.info(f"Registered model: {name} ({model.provider.value}/{model.model_name}) with priority={priority}")
    
    def unregister_model(self, name: str) -> None:
        """注销模型
        
        Args:
            name: 模型标识名
        """
        if name in self.models:
            del self.models[name]
            if self.default_model == name:
                self.default_model = next(iter(self.models.keys()), None)
            logger.info(f"Unregistered model: {name}")
    
    async def select_model(
        self,
        task_type: TaskType = TaskType.CHAT,
        preferred_provider: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> Optional[BaseModel]:
        """选择最佳模型
        
        根据任务类型、提供商偏好和调度策略选择最优模型。
        
        Args:
            task_type: 任务类型
            preferred_provider: 优先提供商
            strategy: 调度策略（覆盖默认策略）
            
        Returns:
            Optional[BaseModel]: 选中的模型
        """
        strategy = strategy or self._strategy
        
        available_models = [
            instance for instance in self.models.values()
            if instance.is_available
        ]
        
        if not available_models:
            logger.warning("No available models")
            return None
        
        # 过滤支持所需能力的模型
        required_capability = self._task_capability_map.get(task_type)
        if required_capability:
            capable_models = [
                inst for inst in available_models
                if inst.model.has_capability(required_capability)
            ]
            if capable_models:
                available_models = capable_models
        
        # 根据策略选择
        if strategy == "round_robin":
            return self._round_robin_select(available_models)
        elif strategy == "priority":
            return self._priority_select(available_models)
        elif strategy == "capability":
            return await self._capability_select(available_models, task_type)
        else:  # adaptive
            return await self._adaptive_select(available_models, task_type, preferred_provider)
    
    def _round_robin_select(self, instances: List[ModelInstance]) -> Optional[BaseModel]:
        """轮询选择
        
        Args:
            instances: 可用实例列表
            
        Returns:
            Optional[BaseModel]: 选中的模型
        """
        if not instances:
            return None
        
        idx = self._round_robin_index % len(instances)
        self._round_robin_index = (self._round_robin_index + 1) % len(instances)
        
        instance = instances[idx]
        instance.last_used = datetime.now()
        instance.call_count += 1
        
        return instance.model
    
    def _priority_select(self, instances: List[ModelInstance]) -> Optional[BaseModel]:
        """优先级选择
        
        Args:
            instances: 可用实例列表
            
        Returns:
            Optional[BaseModel]: 选中的模型
        """
        if not instances:
            return None
        
        # 按优先级排序（不修改入参列表）
        sorted_instances = sorted(instances, key=lambda x: x.priority, reverse=True)

        instance = sorted_instances[0]
        instance.last_used = datetime.now()
        instance.call_count += 1
        
        return instance.model
    
    async def _capability_select(
        self,
        instances: List[ModelInstance],
        task_type: TaskType
    ) -> Optional[BaseModel]:
        """基于能力评估选择
        
        Args:
            instances: 可用实例列表
            task_type: 任务类型
            
        Returns:
            Optional[BaseModel]: 选中的模型
        """
        if not instances:
            return None
        
        best_instance = None
        best_score = -1.0
        
        for instance in instances:
            cache_key = f"{instance.model.provider.value}:{instance.model.model_name}"
            evaluation = self.evaluator.get_evaluation(
                instance.model.provider.value,
                instance.model.model_name
            )
            
            if evaluation:
                score = evaluation.capabilities.get(task_type.value, 0.0)
                if score > best_score:
                    best_score = score
                    best_instance = instance
        
        # 如果没有评估数据，回退到优先级
        if best_instance is None:
            return self._priority_select(instances)
        
        best_instance.last_used = datetime.now()
        best_instance.call_count += 1
        
        return best_instance.model
    
    async def _adaptive_select(
        self,
        instances: List[ModelInstance],
        task_type: TaskType,
        preferred_provider: Optional[str] = None
    ) -> Optional[BaseModel]:
        """自适应选择
        
        综合考虑优先级、延迟、错误率、能力和提供商偏好。
        
        Args:
            instances: 可用实例列表
            task_type: 任务类型
            preferred_provider: 优先提供商
            
        Returns:
            Optional[BaseModel]: 选中的模型
        """
        if not instances:
            return None
        
        scores: List[Tuple[ModelInstance, float]] = []
        
        for instance in instances:
            score = 0.0
            
            # 基础优先级分数 (0-50)
            score += instance.priority * 5
            
            # 提供商偏好 (+30)
            if preferred_provider and instance.model.provider.value == preferred_provider:
                score += 30
            
            # 延迟惩罚 (0-20)
            if instance.avg_latency_ms > 0:
                latency_penalty = min(20, instance.avg_latency_ms / 100)
                score -= latency_penalty
            
            # 错误率惩罚 (0-20)
            error_penalty = instance.error_rate * 20
            score -= error_penalty
            
            # 能力加分 (0-20)
            evaluation = self.evaluator.get_evaluation(
                instance.model.provider.value,
                instance.model.model_name
            )
            if evaluation:
                capability_score = evaluation.capabilities.get(task_type.value, 0.0)
                score += capability_score * 0.2
            
            # 本地模型优先 (+10)
            if instance.model.provider == ModelProvider.OLLAMA:
                score += 10
            
            scores.append((instance, score))
        
        # 选择得分最高的
        scores.sort(key=lambda x: x[1], reverse=True)
        best_instance = scores[0][0]
        
        best_instance.last_used = datetime.now()
        best_instance.call_count += 1
        
        logger.debug(f"Selected model: {best_instance.name} (score={scores[0][1]:.2f})")
        
        return best_instance.model
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        task_type: TaskType = TaskType.CHAT,
        **kwargs: Any
    ) -> ModelResponse:
        """使用指定或默认模型对话
        
        Args:
            messages: 消息列表
            model_name: 指定模型名
            task_type: 任务类型
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        # 选择模型
        if model_name and model_name in self.models:
            instance = self.models[model_name]
            model = instance.model
        else:
            model = await self.select_model(task_type)
            instance = None
            for inst in self.models.values():
                if inst.model == model:
                    instance = inst
                    break
        
        if not model:
            return ModelResponse(
                content="No available model",
                provider="none",
                model="none",
                finish_reason=None
            )
        
        start_time = time.time()
        
        try:
            response = await model.chat(messages, **kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 更新实例统计
            if instance:
                self._update_instance_stats(instance, latency_ms, response, success=True)
            
            # 记录 Token 使用
            if response.usage:
                await self.token_manager.record_usage(
                    provider=model.provider.value,
                    model=model.model_name,
                    usage=response.usage,
                    cost=getattr(response.usage, "cost_estimate", 0.0),
                    latency_ms=latency_ms,
                    task_type=task_type.value
                )
            
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            if instance:
                self._update_instance_stats(instance, latency_ms, None, success=False)
            
            logger.error(f"Model chat error: {e}")
            
            # 尝试故障切换
            return await self._failover_chat(messages, task_type, exclude=instance.name if instance else None, **kwargs)
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        task_type: TaskType = TaskType.CHAT,
        **kwargs: Any
    ) -> AsyncGenerator[Union[StreamChunk, Tuple[str, str]], None]:
        """流式对话

        spec show-thinking-process: 透传 (type, text) 元组或 StreamChunk

        Args:
            messages: 消息列表
            model_name: 指定模型名
            task_type: 任务类型
            **kwargs: 额外参数

        Yields:
            Union[StreamChunk, Tuple[str, str]]: 流式响应块
        """
        if model_name and model_name in self.models:
            model = self.models[model_name].model
        else:
            model = await self.select_model(task_type)

        if not model:
            yield StreamChunk(content="No available model", is_finished=True)
            return

        start_time = time.time()
        total_content = ""

        try:
            async for item in model.stream_chat(messages, **kwargs):
                # spec show-thinking-process: 兼容新元组格式 + 旧 StreamChunk
                if isinstance(item, tuple) and len(item) == 2:
                    chunk_type, chunk_text = item
                    if chunk_type == "content":
                        total_content += chunk_text
                    # thinking 也透传（task 5 BrainWorker 需要）
                    yield item
                else:
                    # 旧 StreamChunk 格式
                    chunk = item
                    if hasattr(chunk, "content"):
                        total_content += chunk.content
                    yield chunk
                    if getattr(chunk, "is_finished", False):
                        latency_ms = (time.time() - start_time) * 1000

                        # 记录使用
                        usage = getattr(chunk, "usage", None)
                        if usage:
                            await self.token_manager.record_usage(
                                provider=model.provider.value,
                                model=model.model_name,
                                usage=usage,
                                cost=getattr(usage, "cost_estimate", 0.0),
                                latency_ms=latency_ms,
                                task_type=task_type.value
                            )

                        break

        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield StreamChunk(content=f"Error: {str(e)}", is_finished=True)
    
    async def _failover_chat(
        self,
        messages: List[ChatMessage],
        task_type: TaskType,
        exclude: Optional[str] = None,
        **kwargs: Any
    ) -> ModelResponse:
        """故障切换
        
        当主模型失败时，尝试其他可用模型。
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            exclude: 排除的模型名称
            **kwargs: 额外参数
            
        Returns:
            ModelResponse: 模型响应
        """
        for name, instance in self.models.items():
            if name == exclude:
                continue
            if not instance.is_available:
                continue
            
            try:
                logger.info(f"Failover to model: {name}")
                response = await instance.model.chat(messages, **kwargs)
                
                if not response.is_error:
                    instance.error_rate = max(0, instance.error_rate - 0.05)
                    return response
                    
            except Exception as e:
                logger.warning(f"Failover model {name} also failed: {e}")
                instance.error_rate = min(1.0, instance.error_rate + 0.1)
                continue
        
        return ModelResponse(
            content="All models failed",
            provider="none",
            model="none",
            finish_reason=None
        )
    
    def _update_instance_stats(
        self,
        instance: ModelInstance,
        latency_ms: float,
        response: Optional[ModelResponse],
        success: bool
    ) -> None:
        """更新实例统计
        
        Args:
            instance: 模型实例
            latency_ms: 延迟
            response: 响应
            success: 是否成功
        """
        # 更新平均延迟（指数移动平均）
        alpha = 0.3
        instance.avg_latency_ms = (
            alpha * latency_ms + (1 - alpha) * instance.avg_latency_ms
            if instance.avg_latency_ms > 0 else latency_ms
        )
        
        # 更新错误率
        if success:
            instance.error_rate = max(0, instance.error_rate - 0.02)
        else:
            instance.error_rate = min(1.0, instance.error_rate + 0.1)
        
        # 更新 Token 统计
        if response and response.usage:
            instance.total_tokens += response.usage.total_tokens
        
        # 如果错误率过高，标记为不可用
        if instance.error_rate > 0.5:
            instance.is_available = False
            logger.warning(f"Model {instance.name} marked as unavailable (error_rate={instance.error_rate:.2f})")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有模型健康状态
        
        Returns:
            Dict[str, bool]: 健康状态字典
        """
        results = {}
        
        for name, instance in self.models.items():
            try:
                is_healthy = await instance.model.health_check()
                instance.is_available = is_healthy
                results[name] = is_healthy
                
                if not is_healthy:
                    logger.warning(f"Model {name} health check failed")
                    
            except Exception as e:
                logger.error(f"Health check error for {name}: {e}")
                instance.is_available = False
                results[name] = False
        
        return results
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表
        
        Returns:
            List[Dict[str, Any]]: 可用模型信息列表
        """
        return [
            {
                "name": inst.name,
                "provider": inst.model.provider.value,
                "model": inst.model.model_name,
                "priority": inst.priority,
                "available": inst.is_available,
                "avg_latency_ms": inst.avg_latency_ms,
                "error_rate": inst.error_rate,
                "call_count": inst.call_count,
                "capabilities": [c.value for c in inst.model.capabilities],
            }
            for inst in self.models.values()
            if inst.is_available
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_calls = sum(inst.call_count for inst in self.models.values())
        total_tokens = sum(inst.total_tokens for inst in self.models.values())
        
        return {
            "total_models": len(self.models),
            "available_models": sum(1 for inst in self.models.values() if inst.is_available),
            "default_model": self.default_model,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "strategy": self._strategy,
            "models": {
                name: {
                    "provider": inst.model.provider.value,
                    "model": inst.model.model_name,
                    "priority": inst.priority,
                    "available": inst.is_available,
                    "avg_latency_ms": inst.avg_latency_ms,
                    "error_rate": inst.error_rate,
                    "call_count": inst.call_count,
                    "total_tokens": inst.total_tokens,
                }
                for name, inst in self.models.items()
            }
        }
    
    def set_strategy(self, strategy: str) -> None:
        """设置调度策略
        
        Args:
            strategy: 策略名称 (adaptive, round_robin, priority, capability)
        """
        valid_strategies = ["adaptive", "round_robin", "priority", "capability"]
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {strategy}. Must be one of {valid_strategies}")
        
        self._strategy = strategy
        logger.info(f"Scheduling strategy set to: {strategy}")
    
    async def evaluate_all_models(self) -> Dict[str, Any]:
        """评估所有模型
        
        Returns:
            Dict[str, Any]: 评估结果
        """
        models = [inst.model for inst in self.models.values() if inst.is_available]
        
        if not models:
            return {"error": "No available models to evaluate"}
        
        results = await self.evaluator.evaluate_multiple(models)
        
        return {
            "evaluated_models": len(results),
            "rankings": self.evaluator.get_model_ranking(),
            "capability_matrix": self.evaluator.get_capability_matrix(),
        }
    
    async def close_all(self) -> None:
        """关闭所有模型连接"""
        for name, instance in self.models.items():
            try:
                await instance.model.close()
                logger.info(f"Closed model: {name}")
            except Exception as e:
                logger.error(f"Error closing model {name}: {e}")
