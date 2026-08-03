"""
感知管理器 (Sensory Manager)

统一管理所有感知模块，协调多模态输入处理，提供统一的感知API。

功能：
- 统一管理所有感知模块
- 协调多模态输入处理
- 提供统一的感知API
- 与记忆系统交互
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.sensory.multimodal_input import (
    MultimodalInputProcessor,
    ProcessedInput,
    InputModality,
    InputQuality,
    InputQualityReport
)
from hyperbrain.layers.sensory.attention import (
    AttentionMechanism,
    AttentionMap,
    AttentionLevel,
    AttentionStrategy,
    AttentionConfig
)
from hyperbrain.layers.sensory.context_awareness import (
    ContextAwareness,
    SituationContext,
    UserEmotionalState
)

from hyperbrain.layers.memory.memory_manager import MemoryManager
from hyperbrain.layers.memory.memory_models import MemoryType, SensoryInput

logger = get_logger("sensory.manager")


class PerceptionResult(BaseModel):
    """感知结果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processed_input: ProcessedInput
    attention_map: Optional[AttentionMap] = None
    context: Optional[SituationContext] = None
    
    # 整合后的信息
    key_information: List[str] = Field(default_factory=list)
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    urgency_level: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "processed_input": self.processed_input.model_dump() if self.processed_input else None,
            "key_information": self.key_information,
            "priority_score": self.priority_score,
            "urgency_level": self.urgency_level,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }


class SensoryPipelineConfig(BaseModel):
    """感知流水线配置"""
    enable_attention: bool = True
    enable_context_awareness: bool = True
    enable_quality_check: bool = True
    default_attention_level: AttentionLevel = AttentionLevel.SENTENCE
    default_attention_strategy: AttentionStrategy = AttentionStrategy.HYBRID
    min_quality_score: float = Field(default=0.2, ge=0.0, le=1.0)
    max_processing_time_ms: float = 5000.0
    store_to_memory: bool = True


class SensoryManager:
    """
    感知管理器 - 感知系统的中央控制器
    
    统一管理多模态输入处理、注意力机制和情境感知，
    提供统一的感知API，并与记忆系统交互。
    
    Attributes:
        input_processor: 多模态输入处理器
        attention: 注意力机制
        context_awareness: 情境感知
        memory_manager: 记忆管理器（可选）
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        pipeline_config: Optional[SensoryPipelineConfig] = None,
        attention_config: Optional[AttentionConfig] = None
    ):
        self.config = get_config().sensory
        self.pipeline_config = pipeline_config or SensoryPipelineConfig()
        
        # 初始化子模块
        self.input_processor = MultimodalInputProcessor()
        self.attention = AttentionMechanism(attention_config)
        self.context_awareness = ContextAwareness()
        
        # 记忆管理器
        self.memory_manager = memory_manager
        
        # 状态
        self._perception_history: List[PerceptionResult] = []
        self._is_initialized = False
        
        logger.info("SensoryManager initialized")
    
    async def initialize(self, user_id: str = "default",
                         location_hints: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化感知系统
        
        Args:
            user_id: 用户ID
            location_hints: 位置线索
        """
        if self._is_initialized:
            return
        
        # 初始化情境感知
        self.context_awareness.initialize_context(user_id, location_hints)
        
        self._is_initialized = True
        logger.info(f"SensoryManager initialized for user {user_id}")
    
    async def perceive(self,
                       content: Any,
                       modality: Union[str, InputModality] = InputModality.TEXT,
                       source: str = "user",
                       metadata: Optional[Dict[str, Any]] = None) -> PerceptionResult:
        """
        统一感知接口 - 处理输入并返回感知结果
        
        完整流程：
        1. 多模态输入处理
        2. 质量检查
        3. 注意力聚焦
        4. 情境整合
        5. 记忆存储
        
        Args:
            content: 输入内容
            modality: 输入模态
            source: 输入来源
            metadata: 附加元数据
            
        Returns:
            PerceptionResult: 感知结果
        """
        if not self._is_initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        # 1. 多模态输入处理
        processed = await self.input_processor.process(
            content=content,
            modality=modality,
            source=source,
            metadata=metadata
        )
        
        # 2. 质量检查
        if self.pipeline_config.enable_quality_check:
            quality_report = self.input_processor.assess_quality(processed)
            if quality_report.overall_score < self.pipeline_config.min_quality_score:
                logger.warning(
                    f"Input quality too low: {quality_report.overall_score:.2f}"
                )
                processed.is_valid = False
                processed.error_message = f"Quality check failed: {quality_report.issues}"
        
        # 3. 注意力聚焦
        attention_map = None
        if self.pipeline_config.enable_attention and processed.is_valid:
            if processed.normalized_text:
                context = self._build_attention_context()
                attention_map = self.attention.focus(
                    text=processed.normalized_text,
                    context=context,
                    strategy=self.pipeline_config.default_attention_strategy,
                    level=self.pipeline_config.default_attention_level
                )
        
        # 4. 情境整合
        if self.pipeline_config.enable_context_awareness:
            self.context_awareness.update_context(
                user_input=processed.normalized_text if processed.modality == InputModality.TEXT else None,
                intent=processed.text_features.intent if processed.text_features else None,
                sentiment=processed.text_features.sentiment_score if processed.text_features else 0.0
            )
        
        # 5. 构建感知结果
        result = self._build_perception_result(
            processed, attention_map, start_time
        )
        
        # 6. 存储到记忆
        if self.pipeline_config.store_to_memory and self.memory_manager:
            await self._store_to_memory(result)
        
        self._perception_history.append(result)
        
        # 限制历史大小
        if len(self._perception_history) > 1000:
            self._perception_history = self._perception_history[-500:]
        
        return result
    
    async def perceive_batch(self,
                             inputs: List[Tuple[Any, Union[str, InputModality], str]]) -> List[PerceptionResult]:
        """
        批量感知处理
        
        Args:
            inputs: [(content, modality, source), ...]
            
        Returns:
            List[PerceptionResult]: 感知结果列表
        """
        tasks = [
            self.perceive(content, modality, source)
            for content, modality, source in inputs
        ]
        return await asyncio.gather(*tasks)
    
    def _build_attention_context(self) -> Dict[str, Any]:
        """构建注意力上下文"""
        context = self.context_awareness.get_current_context()
        
        return {
            "keywords": context.user_state.recent_topics[-5:] if context.user_state.recent_topics else [],
            "topics": context.dialogue_context.topic_history[-3:] if context.dialogue_context.topic_history else [],
            "user_emotion": context.user_state.emotional_state.value,
            "current_topic": context.dialogue_context.current_topic
        }
    
    def _build_perception_result(self,
                                  processed: ProcessedInput,
                                  attention_map: Optional[AttentionMap],
                                  start_time: datetime) -> PerceptionResult:
        """构建感知结果"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 提取关键信息
        key_info = []
        
        if processed.entities:
            key_info.extend([
                f"Entity: {e.text} ({e.entity_type})"
                for e in processed.entities[:5]
            ])
        
        if processed.text_features:
            if processed.text_features.intent:
                key_info.append(f"Intent: {processed.text_features.intent}")
            if processed.text_features.keywords:
                key_info.append(f"Keywords: {', '.join(processed.text_features.keywords[:5])}")
        
        if attention_map:
            focused = attention_map.get_focused_text(threshold=0.5)
            if focused:
                key_info.append(f"Focus: {focused[:100]}")
        
        # 计算优先级
        priority = processed.quality_score
        if processed.text_features:
            priority = max(priority, abs(processed.text_features.sentiment_score))
        
        # 计算紧急程度
        urgency = 0.0
        context = self.context_awareness.get_current_context()
        urgency = context.user_state.urgency_level
        
        return PerceptionResult(
            processed_input=processed,
            attention_map=attention_map,
            context=context if self.pipeline_config.enable_context_awareness else None,
            key_information=key_info,
            priority_score=priority,
            urgency_level=urgency,
            processing_time_ms=processing_time
        )
    
    async def _store_to_memory(self, result: PerceptionResult) -> None:
        """存储到记忆系统"""
        if not self.memory_manager:
            return
        
        try:
            # 存储感知输入
            content = {
                "text": result.processed_input.normalized_text,
                "modality": result.processed_input.modality.value,
                "key_info": result.key_information,
                "priority": result.priority_score
            }
            
            self.memory_manager.store(
                content=content,
                memory_type=MemoryType.SENSORY,
                importance=result.priority_score,
                context_tags=["sensory", result.processed_input.modality.value],
                metadata={
                    "source": result.processed_input.source,
                    "quality_score": result.processed_input.quality_score,
                    "urgency": result.urgency_level
                }
            )
            
            logger.debug(f"Stored perception result to memory")
            
        except Exception as e:
            logger.error(f"Failed to store to memory: {e}")
    
    def get_attention_summary(self, text: str,
                              max_sentences: int = 3) -> str:
        """
        获取注意力摘要
        
        Args:
            text: 输入文本
            max_sentences: 最大句子数
            
        Returns:
            str: 摘要文本
        """
        return self.attention.get_summary(text, max_sentences)
    
    def filter_input(self, text: str,
                     threshold: Optional[float] = None) -> str:
        """
        过滤输入中的无关信息
        
        Args:
            text: 输入文本
            threshold: 过滤阈值
            
        Returns:
            str: 过滤后的文本
        """
        return self.attention.filter_irrelevant(text, threshold=threshold)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取情境摘要"""
        return self.context_awareness.get_context_summary()
    
    def get_current_situation(self) -> SituationContext:
        """获取当前情境"""
        return self.context_awareness.get_current_context()
    
    def update_user_state(self,
                          emotional_state: Optional[UserEmotionalState] = None,
                          preferences: Optional[Dict[str, Any]] = None) -> None:
        """
        更新用户状态
        
        Args:
            emotional_state: 情绪状态
            preferences: 偏好设置
        """
        user_id = self.context_awareness.get_current_context().user_state.user_id
        
        if emotional_state:
            self.context_awareness.user_tracker.get_or_create_user(user_id).emotional_state = emotional_state
        
        if preferences:
            self.context_awareness.user_tracker.update_preferences(user_id, preferences)
    
    def add_dialogue_turn(self,
                          speaker: str,
                          content: str,
                          intent: Optional[str] = None) -> None:
        """
        添加对话轮次
        
        Args:
            speaker: 说话者
            content: 内容
            intent: 意图
        """
        self.context_awareness.get_current_context().dialogue_context.add_turn(
            speaker=speaker,
            content=content,
            intent=intent
        )
    
    def set_memory_manager(self, memory_manager: MemoryManager) -> None:
        """设置记忆管理器"""
        self.memory_manager = memory_manager
        logger.info("Memory manager connected to SensoryManager")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "perception_history_size": len(self._perception_history),
            "input_processor": self.input_processor.get_stats(),
            "attention": self.attention.get_stats(),
            "context_awareness": self.context_awareness.get_stats(),
            "memory_connected": self.memory_manager is not None,
            "is_initialized": self._is_initialized
        }
    
    def get_recent_perceptions(self, limit: int = 10) -> List[PerceptionResult]:
        """获取最近的感知结果"""
        return self._perception_history[-limit:]
    
    def clear_history(self) -> None:
        """清空历史"""
        self._perception_history.clear()
        self.input_processor.clear_history()
        self.attention.clear_history()
        logger.info("SensoryManager history cleared")
    
    def reset(self) -> None:
        """重置感知系统"""
        self.clear_history()
        self.context_awareness.reset_dialogue()
        self._is_initialized = False
        logger.info("SensoryManager reset")
