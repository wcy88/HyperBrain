"""
情感调节模块

调节自身情感状态，维护情感稳定性，处理负面情感，实现情感恢复和平衡。
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("emotional.regulation")


class RegulationStrategy(str, Enum):
    """情感调节策略"""
    COGNITIVE_REAPPRAISAL = "cognitive_reappraisal"
    EXPRESSIVE_SUPPRESSION = "expressive_suppression"
    ATTENTION_DEPLOYMENT = "attention_deployment"
    SITUATION_SELECTION = "situation_selection"
    SITUATION_MODIFICATION = "situation_modification"
    RESPONSE_MODULATION = "response_modulation"
    SOCIAL_SHARING = "social_sharing"
    RUMINATION = "rumination"
    DISTRACTION = "distraction"
    ACCEPTANCE = "acceptance"


class RegulationTarget(str, Enum):
    """调节目标"""
    VALENCE = "valence"
    AROUSAL = "arousal"
    DOMINANCE = "dominance"
    SPECIFIC_EMOTION = "specific_emotion"
    OVERALL_BALANCE = "overall_balance"


class EmotionRegulationConfig(BaseModel):
    """情感调节配置"""
    stability_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    recovery_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    negative_emotion_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    enable_auto_regulation: bool = Field(default=True)
    max_regulation_attempts: int = Field(default=5, ge=1, le=20)
    balance_target_valence: float = Field(default=0.1, ge=-1.0, le=1.0)
    balance_target_arousal: float = Field(default=0.3, ge=0.0, le=1.0)


@dataclass
class RegulationRecord:
    """调节记录"""
    strategy: RegulationStrategy
    target: RegulationTarget
    before_state: Dict[str, float]
    after_state: Dict[str, float]
    effectiveness: float
    timestamp: float = field(default_factory=time.time)
    notes: str = ""


class EmotionRegulator:
    """
    情感调节器

    功能：
    1. 调节自身情感状态
    2. 情感稳定性维护
    3. 负面情感处理
    4. 情感恢复机制
    5. 情感平衡策略
    """

    # 策略效果系数
    STRATEGY_EFFECTIVENESS = {
        RegulationStrategy.COGNITIVE_REAPPRAISAL: {
            "valence": 0.7, "arousal": 0.4, "dominance": 0.3
        },
        RegulationStrategy.EXPRESSIVE_SUPPRESSION: {
            "valence": 0.2, "arousal": 0.6, "dominance": 0.1
        },
        RegulationStrategy.ATTENTION_DEPLOYMENT: {
            "valence": 0.4, "arousal": 0.7, "dominance": 0.2
        },
        RegulationStrategy.SITUATION_SELECTION: {
            "valence": 0.6, "arousal": 0.3, "dominance": 0.4
        },
        RegulationStrategy.SITUATION_MODIFICATION: {
            "valence": 0.5, "arousal": 0.4, "dominance": 0.5
        },
        RegulationStrategy.RESPONSE_MODULATION: {
            "valence": 0.3, "arousal": 0.5, "dominance": 0.3
        },
        RegulationStrategy.SOCIAL_SHARING: {
            "valence": 0.5, "arousal": 0.3, "dominance": 0.2
        },
        RegulationStrategy.RUMINATION: {
            "valence": -0.3, "arousal": 0.2, "dominance": -0.1
        },
        RegulationStrategy.DISTRACTION: {
            "valence": 0.3, "arousal": 0.6, "dominance": 0.1
        },
        RegulationStrategy.ACCEPTANCE: {
            "valence": 0.4, "arousal": 0.5, "dominance": 0.4
        },
    }

    def __init__(self, config: Optional[EmotionRegulationConfig] = None):
        self.config = config or EmotionRegulationConfig()
        self._regulation_history: List[RegulationRecord] = []
        self._stability_score: float = 1.0
        self._consecutive_negative_count: int = 0
        logger.info("EmotionRegulator initialized")

    def regulate(
        self,
        current_state: Dict[str, float],
        target_state: Optional[Dict[str, float]] = None,
        strategy: Optional[RegulationStrategy] = None
    ) -> Dict[str, float]:
        """
        调节情感状态

        Args:
            current_state: 当前情感状态 {"valence": 0.5, "arousal": 0.3, ...}
            target_state: 目标情感状态
            strategy: 调节策略

        Returns:
            Dict[str, float]: 调节后的情感状态
        """
        if target_state is None:
            target_state = {
                "valence": self.config.balance_target_valence,
                "arousal": self.config.balance_target_arousal,
                "dominance": 0.0
            }

        selected_strategy = strategy or self._select_strategy(current_state, target_state)
        before_state = current_state.copy()

        regulated_state = self._apply_strategy(
            current_state, target_state, selected_strategy
        )

        effectiveness = self._calculate_effectiveness(
            before_state, regulated_state, target_state
        )

        record = RegulationRecord(
            strategy=selected_strategy,
            target=RegulationTarget.OVERALL_BALANCE,
            before_state=before_state,
            after_state=regulated_state,
            effectiveness=effectiveness
        )
        self._regulation_history.append(record)

        self._update_stability(regulated_state)
        logger.debug(f"Applied regulation strategy: {selected_strategy.value}, effectiveness={effectiveness:.2f}")

        return regulated_state

    def maintain_stability(
        self,
        emotional_history: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        维护情感稳定性

        Args:
            emotional_history: 情感历史记录

        Returns:
            Dict[str, Any]: 稳定性分析结果
        """
        if len(emotional_history) < 2:
            return {"stable": True, "variance": 0.0}

        valences = [e.get("valence", 0.0) for e in emotional_history]
        arousals = [e.get("arousal", 0.0) for e in emotional_history]

        valence_variance = self._calculate_variance(valences)
        arousal_variance = self._calculate_variance(arousals)

        avg_variance = (valence_variance + arousal_variance) / 2
        is_stable = avg_variance < self.config.stability_threshold

        self._stability_score = max(0.0, 1.0 - avg_variance)

        recommendations = []
        if not is_stable:
            if valence_variance > self.config.stability_threshold:
                recommendations.append("Consider cognitive reappraisal for valence stability")
            if arousal_variance > self.config.stability_threshold:
                recommendations.append("Consider attention deployment for arousal stability")

        return {
            "stable": is_stable,
            "variance": avg_variance,
            "valence_variance": valence_variance,
            "arousal_variance": arousal_variance,
            "stability_score": self._stability_score,
            "recommendations": recommendations
        }

    def process_negative_emotion(
        self,
        emotion_state: Dict[str, float],
        emotion_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        处理负面情感

        Args:
            emotion_state: 当前情感状态
            emotion_type: 负面情感类型

        Returns:
            Dict[str, float]: 处理后的情感状态
        """
        valence = emotion_state.get("valence", 0.0)

        if valence >= -self.config.negative_emotion_threshold:
            return emotion_state

        self._consecutive_negative_count += 1

        if self._consecutive_negative_count >= 3:
            strategy = RegulationStrategy.COGNITIVE_REAPPRAISAL
        elif emotion_type in ["anger", "disgust"]:
            strategy = RegulationStrategy.DISTRACTION
        elif emotion_type in ["sadness", "fear"]:
            strategy = RegulationStrategy.SOCIAL_SHARING
        else:
            strategy = RegulationStrategy.ACCEPTANCE

        target_state = {
            "valence": self.config.balance_target_valence,
            "arousal": emotion_state.get("arousal", 0.5) * 0.7,
            "dominance": emotion_state.get("dominance", 0.0)
        }

        result = self._apply_strategy(emotion_state, target_state, strategy)

        if result.get("valence", 0.0) > -0.2:
            self._consecutive_negative_count = 0

        logger.debug(f"Processed negative emotion with strategy: {strategy.value}")
        return result

    def recover(
        self,
        current_state: Dict[str, float],
        recovery_target: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        情感恢复

        从强烈情感状态恢复到基线水平

        Args:
            current_state: 当前情感状态
            recovery_target: 恢复目标

        Returns:
            Dict[str, float]: 恢复后的情感状态
        """
        if recovery_target is None:
            recovery_target = {
                "valence": self.config.balance_target_valence,
                "arousal": self.config.balance_target_arousal,
                "dominance": 0.0
            }

        rate = self.config.recovery_rate
        recovered = {}

        for key in ["valence", "arousal", "dominance"]:
            current = current_state.get(key, 0.0)
            target = recovery_target.get(key, 0.0)
            diff = target - current
            recovered[key] = current + diff * rate

        other_keys = set(current_state.keys()) - {"valence", "arousal", "dominance"}
        for key in other_keys:
            current = current_state[key]
            recovered[key] = current * (1 - rate * 0.5)

        logger.debug(f"Recovered emotion state, rate={rate:.2f}")
        return recovered

    def balance_emotions(
        self,
        emotion_state: Dict[str, float]
    ) -> Dict[str, float]:
        """
        平衡情感

        调整情感状态使其更加平衡

        Args:
            emotion_state: 当前情感状态

        Returns:
            Dict[str, float]: 平衡后的情感状态
        """
        balanced = emotion_state.copy()

        valence = balanced.get("valence", 0.0)
        arousal = balanced.get("arousal", 0.0)

        if abs(valence) > 0.7:
            balanced["valence"] = valence * 0.8

        if arousal > 0.8:
            balanced["arousal"] = arousal * 0.85
        elif arousal < 0.1:
            balanced["arousal"] = min(0.2, arousal + 0.1)

        positive = max(0, valence)
        negative = max(0, -valence)
        imbalance = abs(positive - negative)

        if imbalance > 0.5:
            adjustment = (positive - negative) * 0.1
            balanced["valence"] = valence - adjustment

        logger.debug("Balanced emotion state")
        return balanced

    def auto_regulate(
        self,
        current_state: Dict[str, float]
    ) -> Optional[Dict[str, float]]:
        """
        自动调节

        根据当前状态自动判断是否需要调节

        Args:
            current_state: 当前情感状态

        Returns:
            Optional[Dict[str, float]]: 调节后的状态，如不需要调节则返回None
        """
        if not self.config.enable_auto_regulation:
            return None

        valence = current_state.get("valence", 0.0)
        arousal = current_state.get("arousal", 0.0)

        needs_regulation = (
            abs(valence) > 0.7 or
            arousal > 0.8 or
            arousal < 0.05 or
            self._consecutive_negative_count >= 2
        )

        if not needs_regulation:
            return None

        if valence < -self.config.negative_emotion_threshold:
            return self.process_negative_emotion(current_state)

        return self.balance_emotions(current_state)

    def get_regulation_history(
        self,
        limit: int = 50
    ) -> List[RegulationRecord]:
        """获取调节历史"""
        return self._regulation_history[-limit:]

    def get_regulation_effectiveness(
        self,
        strategy: Optional[RegulationStrategy] = None
    ) -> float:
        """
        获取调节效果评分

        Args:
            strategy: 特定策略，None表示整体效果

        Returns:
            float: 平均效果评分
        """
        records = self._regulation_history
        if strategy:
            records = [r for r in records if r.strategy == strategy]

        if not records:
            return 0.0

        return sum(r.effectiveness for r in records) / len(records)

    def _select_strategy(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> RegulationStrategy:
        """选择最佳调节策略"""
        valence_diff = abs(target.get("valence", 0.0) - current.get("valence", 0.0))
        arousal_diff = abs(target.get("arousal", 0.0) - current.get("arousal", 0.0))

        if valence_diff > arousal_diff:
            if current.get("valence", 0.0) < -0.3:
                return RegulationStrategy.COGNITIVE_REAPPRAISAL
            return RegulationStrategy.SITUATION_SELECTION
        else:
            if current.get("arousal", 0.0) > 0.6:
                return RegulationStrategy.ATTENTION_DEPLOYMENT
            return RegulationStrategy.DISTRACTION

    def _apply_strategy(
        self,
        current: Dict[str, float],
        target: Dict[str, float],
        strategy: RegulationStrategy
    ) -> Dict[str, float]:
        """应用调节策略"""
        effectiveness = self.STRATEGY_EFFECTIVENESS.get(strategy, {})
        result = current.copy()

        for dimension in ["valence", "arousal", "dominance"]:
            current_val = current.get(dimension, 0.0)
            target_val = target.get(dimension, 0.0)
            diff = target_val - current_val
            factor = effectiveness.get(dimension, 0.3)
            result[dimension] = current_val + diff * factor

        return result

    def _calculate_effectiveness(
        self,
        before: Dict[str, float],
        after: Dict[str, float],
        target: Dict[str, float]
    ) -> float:
        """计算调节效果"""
        before_distance = self._state_distance(before, target)
        after_distance = self._state_distance(after, target)

        if before_distance == 0:
            return 1.0

        improvement = (before_distance - after_distance) / before_distance
        return max(0.0, min(1.0, improvement))

    def _state_distance(
        self,
        state1: Dict[str, float],
        state2: Dict[str, float]
    ) -> float:
        """计算两个状态之间的距离"""
        dimensions = ["valence", "arousal", "dominance"]
        squared_diff = 0.0

        for dim in dimensions:
            diff = state1.get(dim, 0.0) - state2.get(dim, 0.0)
            squared_diff += diff ** 2

        return math.sqrt(squared_diff)

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        squared_diffs = [(v - mean) ** 2 for v in values]
        return sum(squared_diffs) / len(squared_diffs)

    def _update_stability(self, state: Dict[str, float]) -> None:
        """更新稳定性评分"""
        valence = state.get("valence", 0.0)
        if valence < -0.3:
            self._stability_score *= 0.95
        else:
            self._stability_score = min(1.0, self._stability_score + 0.02)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        strategy_effectiveness = {}
        for strategy in RegulationStrategy:
            strategy_effectiveness[strategy.value] = self.get_regulation_effectiveness(strategy)

        return {
            "total_regulations": len(self._regulation_history),
            "stability_score": self._stability_score,
            "consecutive_negative_count": self._consecutive_negative_count,
            "average_effectiveness": self.get_regulation_effectiveness(),
            "strategy_effectiveness": strategy_effectiveness,
            "config": self.config.model_dump(),
        }
