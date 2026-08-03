"""
情感生成模块

基于输入信息和内部状态生成情感，支持Plutchik情感轮模型和PAD情感模型。
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("emotional.generation")


class PlutchikEmotionType(str, Enum):
    """Plutchik情感轮中的8种基本情感"""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"


class EmotionIntensityLevel(str, Enum):
    """情感强度等级"""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class PADDimension(str, Enum):
    """PAD情感模型维度"""
    PLEASURE = "pleasure"
    AROUSAL = "arousal"
    DOMINANCE = "dominance"


class PlutchikEmotion(BaseModel):
    """Plutchik情感轮模型 - 8种基本情感及其强度"""
    joy: float = Field(default=0.0, ge=0.0, le=1.0)
    trust: float = Field(default=0.0, ge=0.0, le=1.0)
    fear: float = Field(default=0.0, ge=0.0, le=1.0)
    surprise: float = Field(default=0.0, ge=0.0, le=1.0)
    sadness: float = Field(default=0.0, ge=0.0, le=1.0)
    disgust: float = Field(default=0.0, ge=0.0, le=1.0)
    anger: float = Field(default=0.0, ge=0.0, le=1.0)
    anticipation: float = Field(default=0.0, ge=0.0, le=1.0)

    def get_dominant(self) -> Tuple[str, float]:
        """获取主导情感及其强度"""
        emotions = self.model_dump()
        return max(emotions.items(), key=lambda x: x[1])

    def get_secondary(self) -> Optional[Tuple[str, float]]:
        """获取次要情感"""
        emotions = self.model_dump()
        if len(emotions) < 2:
            return None
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        if sorted_emotions[1][1] > 0:
            return sorted_emotions[1]
        return None

    def to_vector(self) -> List[float]:
        """转换为向量表示"""
        return [
            self.joy, self.trust, self.fear, self.surprise,
            self.sadness, self.disgust, self.anger, self.anticipation
        ]

    @classmethod
    def from_vector(cls, vector: List[float]) -> "PlutchikEmotion":
        """从向量创建"""
        if len(vector) != 8:
            raise ValueError("Vector must have exactly 8 elements")
        return cls(
            joy=vector[0], trust=vector[1], fear=vector[2], surprise=vector[3],
            sadness=vector[4], disgust=vector[5], anger=vector[6], anticipation=vector[7]
        )


class PADEmotion(BaseModel):
    """PAD情感模型 - Pleasure-Arousal-Dominance三维模型"""
    pleasure: float = Field(default=0.0, ge=-1.0, le=1.0)
    arousal: float = Field(default=0.0, ge=-1.0, le=1.0)
    dominance: float = Field(default=0.0, ge=-1.0, le=1.0)

    def to_vector(self) -> List[float]:
        """转换为向量"""
        return [self.pleasure, self.arousal, self.dominance]

    @classmethod
    def from_vector(cls, vector: List[float]) -> "PADEmotion":
        """从向量创建"""
        if len(vector) != 3:
            raise ValueError("Vector must have exactly 3 elements")
        return cls(pleasure=vector[0], arousal=vector[1], dominance=vector[2])

    @classmethod
    def from_plutchik(cls, plutchik: PlutchikEmotion) -> "PADEmotion":
        """从Plutchik模型转换为PAD模型"""
        pleasure = (plutchik.joy + plutchik.trust - plutchik.sadness - plutchik.disgust) / 2
        arousal = (plutchik.joy + plutchik.anger + plutchik.fear + plutchik.surprise) / 2
        dominance = (plutchik.trust + plutchik.anticipation - plutchik.fear - plutchik.sadness) / 2
        return cls(pleasure=pleasure, arousal=arousal, dominance=dominance)

    def to_plutchik_approximation(self) -> PlutchikEmotion:
        """近似转换为Plutchik模型（粗略估计）"""
        joy = max(0.0, (self.pleasure + self.arousal) / 2)
        trust = max(0.0, (self.pleasure + self.dominance) / 2)
        fear = max(0.0, (-self.dominance + self.arousal) / 2)
        surprise = max(0.0, self.arousal * 0.5)
        sadness = max(0.0, (-self.pleasure - self.arousal * 0.5) / 2)
        disgust = max(0.0, (-self.pleasure - self.dominance * 0.5) / 2)
        anger = max(0.0, (-self.pleasure + self.arousal) / 2)
        anticipation = max(0.0, (self.dominance + self.arousal * 0.5) / 2)
        return PlutchikEmotion(
            joy=joy, trust=trust, fear=fear, surprise=surprise,
            sadness=sadness, disgust=disgust, anger=anger, anticipation=anticipation
        )


class EmotionBlend(BaseModel):
    """情感混合表示"""
    primary: str
    secondary: Optional[str] = None
    blend_name: Optional[str] = None
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


@dataclass
class EmotionState:
    """完整情感状态"""
    plutchik: PlutchikEmotion = field(default_factory=PlutchikEmotion)
    pad: PADEmotion = field(default_factory=PADEmotion)
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    trigger: str = ""

    def get_valence(self) -> float:
        """计算效价（正负面倾向）"""
        return self.pad.pleasure

    def get_arousal(self) -> float:
        """获取唤醒度"""
        return self.pad.arousal

    def get_dominance(self) -> float:
        """获取支配度"""
        return self.pad.dominance


class EmotionGenerationConfig(BaseModel):
    """情感生成配置"""
    base_intensity: float = Field(default=0.3, ge=0.0, le=1.0)
    max_intensity: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    enable_blending: bool = Field(default=True)
    enable_transitions: bool = Field(default=True)
    personality_bias: Dict[str, float] = Field(default_factory=dict)


class EmotionGenerator:
    """
    情感生成器

    功能：
    1. 基于输入信息生成情感
    2. 支持Plutchik情感轮模型
    3. 支持PAD情感模型
    4. 情感强度计算
    5. 情感混合和转换
    """

    # Plutchik情感轮中的对立情感对
    OPPOSITE_EMOTIONS = {
        PlutchikEmotionType.JOY: PlutchikEmotionType.SADNESS,
        PlutchikEmotionType.SADNESS: PlutchikEmotionType.JOY,
        PlutchikEmotionType.TRUST: PlutchikEmotionType.DISGUST,
        PlutchikEmotionType.DISGUST: PlutchikEmotionType.TRUST,
        PlutchikEmotionType.FEAR: PlutchikEmotionType.ANGER,
        PlutchikEmotionType.ANGER: PlutchikEmotionType.FEAR,
        PlutchikEmotionType.SURPRISE: PlutchikEmotionType.ANTICIPATION,
        PlutchikEmotionType.ANTICIPATION: PlutchikEmotionType.SURPRISE,
    }

    # 情感混合规则（Plutchik情感轮中的复合情感）
    EMOTION_BLENDS = {
        ("joy", "trust"): "love",
        ("trust", "fear"): "submission",
        ("fear", "surprise"): "awe",
        ("surprise", "sadness"): "disapproval",
        ("sadness", "disgust"): "remorse",
        ("disgust", "anger"): "contempt",
        ("anger", "anticipation"): "aggressiveness",
        ("anticipation", "joy"): "optimism",
    }

    def __init__(self, config: Optional[EmotionGenerationConfig] = None):
        self.config = config or EmotionGenerationConfig()
        self.current_state = EmotionState()
        self.emotion_history: List[EmotionState] = []
        self._personality = self.config.personality_bias
        logger.info("EmotionGenerator initialized")

    def generate_from_sentiment(
        self,
        sentiment_score: float,
        intensity: float = 1.0,
        arousal: Optional[float] = None,
        source: str = "",
        trigger: str = ""
    ) -> EmotionState:
        """
        基于情感分数生成情感状态

        Args:
            sentiment_score: 情感分数 (-1 到 1)
            intensity: 强度倍数
            arousal: 唤醒度 (可选)
            source: 情感来源
            trigger: 触发事件

        Returns:
            EmotionState: 生成的情感状态
        """
        plutchik = PlutchikEmotion()
        clamped_sentiment = max(-1.0, min(1.0, sentiment_score))
        effective_intensity = min(intensity, self.config.max_intensity)

        if clamped_sentiment > 0:
            plutchik.joy = clamped_sentiment * effective_intensity
            plutchik.trust = clamped_sentiment * effective_intensity * 0.5
        else:
            plutchik.sadness = abs(clamped_sentiment) * effective_intensity * 0.6
            plutchik.fear = abs(clamped_sentiment) * effective_intensity * 0.3

        if arousal is not None:
            plutchik.surprise = abs(arousal) * effective_intensity * 0.4

        pad = PADEmotion.from_plutchik(plutchik)
        if arousal is not None:
            pad.arousal = arousal

        state = EmotionState(
            plutchik=plutchik,
            pad=pad,
            source=source,
            trigger=trigger
        )

        self.current_state = state
        self.emotion_history.append(state)
        logger.debug(f"Generated emotion from sentiment: {clamped_sentiment:.2f}")
        return state

    def generate_from_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionState:
        """
        基于事件生成情感

        Args:
            event_type: 事件类型
            event_data: 事件数据
            context: 上下文信息

        Returns:
            EmotionState: 生成的情感状态
        """
        plutchik = PlutchikEmotion()
        intensity = event_data.get("intensity", self.config.base_intensity)
        intensity = min(intensity, self.config.max_intensity)

        event_emotion_map = {
            "success": {"joy": 0.8, "trust": 0.3},
            "failure": {"sadness": 0.7, "fear": 0.2},
            "threat": {"fear": 0.8, "surprise": 0.4},
            "loss": {"sadness": 0.8, "anger": 0.2},
            "achievement": {"joy": 0.9, "anticipation": 0.3},
            "betrayal": {"anger": 0.7, "disgust": 0.5, "sadness": 0.4},
            "surprise": {"surprise": 0.8, "anticipation": 0.2},
            "help": {"trust": 0.6, "joy": 0.3},
            "insult": {"anger": 0.7, "disgust": 0.4},
            "praise": {"joy": 0.7, "trust": 0.3},
        }

        emotions = event_emotion_map.get(event_type, {"surprise": 0.3})
        for emotion_name, base_value in emotions.items():
            current = getattr(plutchik, emotion_name, 0.0)
            setattr(plutchik, emotion_name, min(1.0, current + base_value * intensity))

        pad = PADEmotion.from_plutchik(plutchik)
        if context and "arousal" in context:
            pad.arousal = context["arousal"]

        state = EmotionState(
            plutchik=plutchik,
            pad=pad,
            source="event",
            trigger=event_type
        )

        self.current_state = state
        self.emotion_history.append(state)
        logger.debug(f"Generated emotion from event: {event_type}")
        return state

    def calculate_intensity(
        self,
        base_emotion: str,
        factors: Dict[str, float]
    ) -> float:
        """
        计算情感强度

        Args:
            base_emotion: 基础情感
            factors: 影响因素 {"unexpectedness": 0.5, "personal_relevance": 0.8, ...}

        Returns:
            float: 计算后的强度 (0-1)
        """
        base = self.config.base_intensity

        unexpectedness = factors.get("unexpectedness", 0.0)
        personal_relevance = factors.get("personal_relevance", 0.5)
        proximity = factors.get("proximity", 0.5)
        coping_potential = factors.get("coping_potential", 0.5)

        intensity = base + (
            unexpectedness * 0.25 +
            personal_relevance * 0.3 +
            proximity * 0.2 +
            (1 - coping_potential) * 0.25
        )

        personality_mod = self._personality.get(base_emotion, 0.0)
        intensity += personality_mod * 0.2

        return min(self.config.max_intensity, max(0.0, intensity))

    def blend_emotions(
        self,
        emotion1: str,
        emotion2: str,
        intensity1: float = 0.5,
        intensity2: float = 0.5
    ) -> EmotionBlend:
        """
        混合两种情感

        Args:
            emotion1: 第一种情感
            emotion2: 第二种情感
            intensity1: 第一种情感强度
            intensity2: 第二种情感强度

        Returns:
            EmotionBlend: 混合后的情感
        """
        if not self.config.enable_blending:
            primary = emotion1 if intensity1 >= intensity2 else emotion2
            return EmotionBlend(primary=primary, intensity=max(intensity1, intensity2))

        sorted_pair = tuple(sorted([emotion1.lower(), emotion2.lower()]))
        blend_name = self.EMOTION_BLENDS.get(sorted_pair)

        if blend_name:
            return EmotionBlend(
                primary=emotion1 if intensity1 >= intensity2 else emotion2,
                secondary=emotion2 if intensity1 >= intensity2 else emotion1,
                blend_name=blend_name,
                intensity=(intensity1 + intensity2) / 2
            )

        return EmotionBlend(
            primary=emotion1 if intensity1 >= intensity2 else emotion2,
            secondary=emotion2 if intensity1 >= intensity2 else emotion1,
            intensity=(intensity1 + intensity2) / 2
        )

    def transition_emotion(
        self,
        from_emotion: str,
        to_emotion: str,
        progress: float = 0.5
    ) -> PlutchikEmotion:
        """
        计算情感过渡状态

        Args:
            from_emotion: 起始情感
            to_emotion: 目标情感
            progress: 过渡进度 (0-1)

        Returns:
            PlutchikEmotion: 过渡中的情感状态
        """
        if not self.config.enable_transitions:
            plutchik = PlutchikEmotion()
            setattr(plutchik, to_emotion.lower(), 1.0)
            return plutchik

        from_state = PlutchikEmotion()
        setattr(from_state, from_emotion.lower(), 1.0)

        to_state = PlutchikEmotion()
        setattr(to_state, to_emotion.lower(), 1.0)

        from_vec = from_state.to_vector()
        to_vec = to_state.to_vector()

        interpolated = [
            from_vec[i] * (1 - progress) + to_vec[i] * progress
            for i in range(8)
        ]

        return PlutchikEmotion.from_vector(interpolated)

    def apply_opposite_inhibition(self, plutchik: PlutchikEmotion) -> PlutchikEmotion:
        """
        应用对立情感抑制

        当一种情感强烈时，抑制其对立情感

        Args:
            plutchik: 当前Plutchik情感

        Returns:
            PlutchikEmotion: 处理后的情感
        """
        result = PlutchikEmotion(**plutchik.model_dump())
        emotions = result.model_dump()

        for emotion_name, intensity in emotions.items():
            if intensity > 0.5:
                opposite_name = self.OPPOSITE_EMOTIONS.get(
                    PlutchikEmotionType(emotion_name)
                )
                if opposite_name:
                    opposite_intensity = getattr(result, opposite_name.value, 0.0)
                    inhibition = intensity * 0.3
                    setattr(result, opposite_name.value, max(0.0, opposite_intensity - inhibition))

        return result

    def get_current_state(self) -> EmotionState:
        """获取当前情感状态"""
        return self.current_state

    def get_emotion_history(self, limit: int = 100) -> List[EmotionState]:
        """获取情感历史"""
        return self.emotion_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.emotion_history:
            return {"history_count": 0}

        recent = self.emotion_history[-50:]
        avg_valence = sum(s.get_valence() for s in recent) / len(recent)
        avg_arousal = sum(s.get_arousal() for s in recent) / len(recent)

        dominant_emotions = {}
        for state in recent:
            dom, _ = state.plutchik.get_dominant()
            dominant_emotions[dom] = dominant_emotions.get(dom, 0) + 1

        return {
            "history_count": len(self.emotion_history),
            "average_valence": avg_valence,
            "average_arousal": avg_arousal,
            "dominant_emotions": dominant_emotions,
            "current_state": {
                "valence": self.current_state.get_valence(),
                "arousal": self.current_state.get_arousal(),
                "dominance": self.current_state.get_dominance(),
            }
        }
