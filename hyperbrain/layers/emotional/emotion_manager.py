"""
情感管理器

统一管理所有情感模块，协调情感生成、表达、调节，提供统一的情感API。
"""

import time
from typing import Dict, List, Optional, Any, Union

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.emotional.emotion_generation import (
    EmotionGenerator, EmotionState, PlutchikEmotion, PADEmotion,
    EmotionGenerationConfig
)
from hyperbrain.layers.emotional.emotion_expression import (
    EmotionExpresser, ExpressionStyle, ExpressionIntensity,
    ExpressionResult, ExpressionConfig
)
from hyperbrain.layers.emotional.emotion_memory import (
    EmotionalMemory, EmotionalMemoryEntry, EmotionalMemoryConfig,
    RetrievalQuery
)
from hyperbrain.layers.emotional.emotion_regulation import (
    EmotionRegulator, RegulationStrategy, EmotionRegulationConfig
)
from hyperbrain.layers.emotional.empathy import (
    EmpathyEngine, EmpathyLevel, EmpathyResponse, EmpathyConfig
)

logger = get_logger("emotional.manager")


class EmotionManager:
    """
    情感管理器 - 情感系统的中央控制器

    统一管理所有情感模块，协调情感生成、表达、调节，
    提供统一的情感API，与记忆系统和认知系统交互。

    Attributes:
        generator: 情感生成器
        expresser: 情感表达器
        memory: 情感记忆
        regulator: 情感调节器
        empathy: 共情引擎
    """

    def __init__(
        self,
        generation_config: Optional[EmotionGenerationConfig] = None,
        expression_config: Optional[ExpressionConfig] = None,
        memory_config: Optional[EmotionalMemoryConfig] = None,
        regulation_config: Optional[EmotionRegulationConfig] = None,
        empathy_config: Optional[EmpathyConfig] = None,
        memory_manager=None,
        cognitive_manager=None
    ):
        self.config = get_config().emotional

        self.generator = EmotionGenerator(config=generation_config)
        self.expresser = EmotionExpresser(config=expression_config)
        self.memory = EmotionalMemory(config=memory_config)
        self.regulator = EmotionRegulator(config=regulation_config)
        self.empathy = EmpathyEngine(config=empathy_config)

        self.memory_manager = memory_manager
        self.cognitive_manager = cognitive_manager

        self._current_state: Optional[EmotionState] = None
        self._state_history: List[Dict[str, Any]] = []

        logger.info("EmotionManager initialized")

    # ========== 统一情感API ==========

    def process_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理输入并生成情感响应

        完整流程：
        1. 生成情感
        2. 存储情感记忆
        3. 自动调节
        4. 返回结果

        Args:
            input_data: 输入数据
                - sentiment_score: 情感分数
                - event_type: 事件类型
                - intensity: 强度
                - context: 上下文

        Returns:
            Dict[str, Any]: 处理结果
        """
        sentiment_score = input_data.get("sentiment_score", 0.0)
        event_type = input_data.get("event_type")
        intensity = input_data.get("intensity", 1.0)
        context = input_data.get("context", {})

        if event_type:
            state = self.generator.generate_from_event(
                event_type=event_type,
                event_data={"intensity": intensity, **context},
                context=context
            )
        else:
            state = self.generator.generate_from_sentiment(
                sentiment_score=sentiment_score,
                intensity=intensity,
                source="input",
                trigger=context.get("trigger", "")
            )

        self._current_state = state

        # 存储情感记忆
        self._store_emotional_memory(state, input_data)

        # 自动调节
        regulated = self._auto_regulate(state)
        if regulated:
            state.pad = PADEmotion(**regulated)
            state.plutchik = state.pad.to_plutchik_approximation()

        result = {
            "emotion_state": {
                "plutchik": state.plutchik.model_dump(),
                "pad": state.pad.model_dump(),
                "valence": state.get_valence(),
                "arousal": state.get_arousal(),
                "dominance": state.get_dominance(),
            },
            "dominant_emotion": state.plutchik.get_dominant(),
            "was_regulated": regulated is not None,
        }

        self._state_history.append(result)
        return result

    def express(
        self,
        text: str,
        style: Optional[ExpressionStyle] = None,
        intensity: Optional[ExpressionIntensity] = None
    ) -> ExpressionResult:
        """
        表达情感

        Args:
            text: 原始文本
            style: 表达风格
            intensity: 表达强度

        Returns:
            ExpressionResult: 表达结果
        """
        if self._current_state:
            dominant, _ = self._current_state.plutchik.get_dominant()
        else:
            dominant = "neutral"

        return self.expresser.express(
            text=text,
            emotion=dominant,
            style=style,
            intensity=intensity
        )

    def empathize(
        self,
        other_emotion: str,
        intensity: float,
        context: Optional[str] = None
    ) -> EmpathyResponse:
        """
        对他人情感产生共情

        Args:
            other_emotion: 他人情感类型
            intensity: 情感强度
            context: 上下文

        Returns:
            EmpathyResponse: 共情响应
        """
        response = self.empathy.generate_empathy_response(
            other_emotion=other_emotion,
            intensity=intensity,
            context=context
        )

        # 镜像情感到自身
        if self.config.enable_emotional_memory:
            mirrored = self.empathy.mirror_emotion(other_emotion, intensity)
            if self._current_state:
                self._current_state.pad.pleasure = mirrored.get("valence", 0.0)
                self._current_state.pad.arousal = mirrored.get("arousal", 0.0)

        return response

    def regulate(
        self,
        strategy: Optional[RegulationStrategy] = None,
        target_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        主动调节情感

        Args:
            strategy: 调节策略
            target_state: 目标状态

        Returns:
            Dict[str, float]: 调节后的状态
        """
        if not self._current_state:
            return target_state or {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}

        current = {
            "valence": self._current_state.get_valence(),
            "arousal": self._current_state.get_arousal(),
            "dominance": self._current_state.get_dominance(),
        }

        regulated = self.regulator.regulate(
            current_state=current,
            target_state=target_state,
            strategy=strategy
        )

        self._current_state.pad = PADEmotion(**regulated)
        self._current_state.plutchik = self._current_state.pad.to_plutchik_approximation()

        return regulated

    def get_current_emotion(self) -> Optional[Dict[str, Any]]:
        """
        获取当前情感状态

        Returns:
            Optional[Dict[str, Any]]: 当前情感状态
        """
        if not self._current_state:
            return None

        return {
            "plutchik": self._current_state.plutchik.model_dump(),
            "pad": self._current_state.pad.model_dump(),
            "valence": self._current_state.get_valence(),
            "arousal": self._current_state.get_arousal(),
            "dominance": self._current_state.get_dominance(),
            "dominant": self._current_state.plutchik.get_dominant(),
        }

    def get_emotional_influence(self) -> Dict[str, float]:
        """
        获取情感对决策的影响因子

        Returns:
            Dict[str, float]: 影响因子
        """
        if not self._current_state:
            return {
                "risk_taking": 0.5,
                "creativity": 0.5,
                "caution": 0.5,
                "openness": 0.5,
                "urgency": 0.5,
            }

        valence = self._current_state.get_valence()
        arousal = self._current_state.get_arousal()
        plutchik = self._current_state.plutchik

        return {
            "risk_taking": 0.5 + valence * 0.3 + arousal * 0.2,
            "creativity": 0.5 + plutchik.joy * 0.3 + plutchik.surprise * 0.2,
            "caution": 0.5 + plutchik.fear * 0.4 + plutchik.sadness * 0.2,
            "openness": 0.5 + plutchik.trust * 0.3 + plutchik.anticipation * 0.2,
            "urgency": arousal,
            "valence": valence,
        }

    # ========== 记忆交互 ==========

    def store_emotional_memory(
        self,
        event_description: str,
        emotional_state: Optional[Dict[str, float]] = None,
        associated_memory_ids: Optional[List[str]] = None
    ) -> EmotionalMemoryEntry:
        """
        存储情感记忆

        Args:
            event_description: 事件描述
            emotional_state: 情感状态
            associated_memory_ids: 关联记忆ID

        Returns:
            EmotionalMemoryEntry: 存储的条目
        """
        if emotional_state is None and self._current_state:
            emotional_state = self._current_state.plutchik.model_dump()

        valence = 0.0
        arousal = 0.0
        if self._current_state:
            valence = self._current_state.get_valence()
            arousal = self._current_state.get_arousal()

        entry = self.memory.store(
            event_description=event_description,
            emotional_state=emotional_state or {},
            associated_memory_ids=associated_memory_ids,
            valence=valence,
            arousal=arousal
        )

        # 同步到记忆系统
        if self.memory_manager:
            try:
                self.memory_manager.store(
                    content={
                        "event": event_description,
                        "emotional_state": emotional_state,
                    },
                    memory_type=MemoryType.EMOTIONAL,
                    importance=abs(valence) * 0.5 + 0.3,
                    emotional_tag={
                        "valence": "positive" if valence > 0 else "negative" if valence < 0 else "neutral",
                        "intensity": max(emotional_state.values()) if emotional_state else 0.0,
                        "primary_emotion": entry.primary_emotion,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to sync emotional memory to memory manager: {e}")

        return entry

    def retrieve_emotional_memories(
        self,
        emotion_type: Optional[str] = None,
        valence_range: Optional[tuple] = None,
        limit: int = 10
    ) -> List[EmotionalMemoryEntry]:
        """
        检索情感记忆

        Args:
            emotion_type: 情感类型
            valence_range: 效价范围
            limit: 数量限制

        Returns:
            List[EmotionalMemoryEntry]: 情感记忆列表
        """
        if emotion_type:
            return self.memory.retrieve_by_emotion(emotion_type, limit)
        elif valence_range:
            return self.memory.retrieve_by_valence(valence_range, limit)
        else:
            query = RetrievalQuery(limit=limit)
            return self.memory.retrieve_by_query(query)

    # ========== 内部方法 ==========

    def _store_emotional_memory(
        self,
        state: EmotionState,
        input_data: Dict[str, Any]
    ) -> None:
        """内部方法：存储情感记忆"""
        if not self.config.enable_emotional_memory:
            return

        event = input_data.get("event_description", "情感输入")
        self.memory.store(
            event_description=event,
            emotional_state=state.plutchik.model_dump(),
            valence=state.get_valence(),
            arousal=state.get_arousal(),
            context=input_data.get("context", {})
        )

    def _auto_regulate(self, state: EmotionState) -> Optional[Dict[str, float]]:
        """内部方法：自动调节"""
        current = {
            "valence": state.get_valence(),
            "arousal": state.get_arousal(),
            "dominance": state.get_dominance(),
        }
        return self.regulator.auto_regulate(current)

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """
        获取整体统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "generation": self.generator.get_stats(),
            "expression": self.expresser.get_stats(),
            "memory": self.memory.get_stats(),
            "regulation": self.regulator.get_stats(),
            "empathy": self.empathy.get_stats(),
            "current_emotion": self.get_current_emotion(),
            "state_history_length": len(self._state_history),
        }

    def get_emotional_report(self) -> Dict[str, Any]:
        """
        获取情感报告

        Returns:
            Dict[str, Any]: 情感报告
        """
        current = self.get_current_emotion()
        influence = self.get_emotional_influence()
        summary = self.memory.get_emotional_summary(time_window=86400)

        return {
            "current_state": current,
            "influence_on_cognition": influence,
            "recent_memory_summary": summary,
            "stability": self.regulator.maintain_stability(
                [s.get("emotion_state", {}).get("pad", {}) for s in self._state_history[-20:]]
            ) if self._state_history else {"stable": True},
            "timestamp": time.time(),
        }

    def __repr__(self) -> str:
        if self._current_state:
            dom, intensity = self._current_state.plutchik.get_dominant()
            return f"EmotionManager(dominant={dom}, intensity={intensity:.2f})"
        return "EmotionManager(no_active_emotion)"
