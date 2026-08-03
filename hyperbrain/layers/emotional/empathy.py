"""
共情模块

理解他人情感状态，实现情感镜像、共情响应生成和情感共鸣检测。
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("emotional.empathy")


class EmpathyLevel(str, Enum):
    """共情程度等级"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    DEEP = "deep"


class EmpathyType(str, Enum):
    """共情类型"""
    COGNITIVE = "cognitive"
    AFFECTIVE = "affective"
    COMPASSIONATE = "compassionate"
    MIRRORING = "mirroring"


class EmpathyConfig(BaseModel):
    """共情配置"""
    default_level: EmpathyLevel = Field(default=EmpathyLevel.MODERATE)
    enable_mirroring: bool = Field(default=True)
    enable_cognitive_empathy: bool = Field(default=True)
    enable_affective_empathy: bool = Field(default=True)
    resonance_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_empathy_intensity: float = Field(default=0.8, ge=0.0, le=1.0)
    personal_boundary: float = Field(default=0.3, ge=0.0, le=1.0)


@dataclass
class EmpathyRecord:
    """共情记录"""
    target_emotion: str
    target_intensity: float
    empathy_type: EmpathyType
    empathy_level: EmpathyLevel
    mirrored_state: Dict[str, float]
    response: str
    resonance_score: float
    timestamp: float = field(default_factory=time.time)


class EmpathyResponse(BaseModel):
    """共情响应"""
    response_text: str = Field(default="")
    empathy_level: EmpathyLevel = Field(default=EmpathyLevel.MODERATE)
    empathy_type: EmpathyType = Field(default=EmpathyType.COGNITIVE)
    resonance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    suggested_actions: List[str] = Field(default_factory=list)
    emotional_support_score: float = Field(default=0.0, ge=0.0, le=1.0)


class EmpathyEngine:
    """
    共情引擎

    功能：
    1. 理解他人情感状态
    2. 情感镜像
    3. 共情响应生成
    4. 共情程度调节
    5. 情感共鸣检测
    """

    # 共情响应模板
    EMPATHY_TEMPLATES = {
        ("joy", EmpathyLevel.LOW): ["那很好。", "不错。"],
        ("joy", EmpathyLevel.MODERATE): ["听起来很棒！", "真为你高兴！"],
        ("joy", EmpathyLevel.HIGH): ["太棒了！我能感受到你的喜悦！", "这真是个好消息，我和你一样开心！"],
        ("sadness", EmpathyLevel.LOW): ["知道了。", "我理解。"],
        ("sadness", EmpathyLevel.MODERATE): ["听起来很难过。", "我能理解你的感受。"],
        ("sadness", EmpathyLevel.HIGH): ["这一定很难受，我在这里陪着你。", "你的感受完全可以理解，想哭就哭吧。"],
        ("anger", EmpathyLevel.LOW): ["明白了。", "我注意到了。"],
        ("anger", EmpathyLevel.MODERATE): ["这确实让人生气。", "你有理由感到愤怒。"],
        ("anger", EmpathyLevel.HIGH): ["这太不公平了！我能理解你为什么这么生气。", "换作是我也会很愤怒的。"],
        ("fear", EmpathyLevel.LOW): ["知道了。", "我理解。"],
        ("fear", EmpathyLevel.MODERATE): ["这听起来确实令人担心。", "我能理解你的担忧。"],
        ("fear", EmpathyLevel.HIGH): ["这一定很可怕，但你会挺过去的。", "我理解你的恐惧，让我们一起面对。"],
        ("surprise", EmpathyLevel.LOW): ["哦。", "知道了。"],
        ("surprise", EmpathyLevel.MODERATE): ["真的吗？", "这确实令人惊讶。"],
        ("surprise", EmpathyLevel.HIGH): ["天哪！这也太出乎意料了！", "我完全能理解你的震惊！"],
        ("neutral", EmpathyLevel.LOW): ["知道了。", "明白。"],
        ("neutral", EmpathyLevel.MODERATE): ["我了解了。", "明白了。"],
        ("neutral", EmpathyLevel.HIGH): ["我理解你的感受。", "我听到了。"],
    }

    # 情感共鸣权重
    RESONANCE_WEIGHTS = {
        "valence_match": 0.4,
        "arousal_match": 0.3,
        "intensity_proximity": 0.3,
    }

    def __init__(self, config: Optional[EmpathyConfig] = None):
        self.config = config or EmpathyConfig()
        self._empathy_history: List[EmpathyRecord] = []
        self._current_resonance: float = 0.0
        logger.info("EmpathyEngine initialized")

    def understand_emotion(
        self,
        other_emotion: str,
        intensity: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        理解他人情感状态

        Args:
            other_emotion: 他人情感类型
            intensity: 情感强度
            context: 上下文信息

        Returns:
            Dict[str, Any]: 理解结果
        """
        understanding = {
            "detected_emotion": other_emotion,
            "intensity": intensity,
            "likely_causes": self._infer_causes(other_emotion, context),
            "appropriate_response_level": self._determine_response_level(intensity),
            "potential_needs": self._identify_needs(other_emotion),
        }

        logger.debug(f"Understood emotion: {other_emotion} at intensity {intensity:.2f}")
        return understanding

    def mirror_emotion(
        self,
        other_emotion: str,
        other_intensity: float,
        own_current_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        情感镜像

        模拟体验他人情感，但保持适当距离

        Args:
            other_emotion: 他人情感类型
            other_intensity: 他人情感强度
            own_current_state: 自身当前情感状态

        Returns:
            Dict[str, float]: 镜像后的情感状态
        """
        if not self.config.enable_mirroring:
            return own_current_state or {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}

        mirrored_intensity = min(
            other_intensity * 0.6,
            self.config.max_empathy_intensity
        )

        emotion_valence_map = {
            "joy": 1.0, "trust": 0.8, "anticipation": 0.5,
            "surprise": 0.0,
            "sadness": -1.0, "fear": -0.8, "anger": -0.7, "disgust": -0.6
        }

        valence = emotion_valence_map.get(other_emotion, 0.0) * mirrored_intensity
        arousal = mirrored_intensity * 0.7

        mirrored_state = {
            "valence": valence,
            "arousal": arousal,
            "dominance": 0.0,
            "mirrored_emotion": other_emotion,
            "mirrored_intensity": mirrored_intensity,
        }

        logger.debug(f"Mirrored emotion: {other_emotion} at {mirrored_intensity:.2f}")
        return mirrored_state

    def generate_empathy_response(
        self,
        other_emotion: str,
        intensity: float,
        context: Optional[str] = None,
        level: Optional[EmpathyLevel] = None
    ) -> EmpathyResponse:
        """
        生成共情响应

        Args:
            other_emotion: 他人情感类型
            intensity: 情感强度
            context: 上下文描述
            level: 共情等级

        Returns:
            EmpathyResponse: 共情响应
        """
        empathy_level = level or self.config.default_level

        if intensity < 0.2:
            empathy_level = EmpathyLevel.LOW
        elif intensity > 0.7 and empathy_level == EmpathyLevel.MODERATE:
            empathy_level = EmpathyLevel.HIGH

        templates = self.EMPATHY_TEMPLATES.get(
            (other_emotion, empathy_level),
            self.EMPATHY_TEMPLATES.get(("neutral", empathy_level), ["我理解。"])
        )

        response_text = templates[0] if templates else "我理解。"

        if context:
            response_text = f"{response_text} {context}"

        empathy_type = self._select_empathy_type(other_emotion, intensity)
        resonance = self._calculate_resonance(other_emotion, intensity)
        suggested_actions = self._suggest_actions(other_emotion, empathy_level)

        record = EmpathyRecord(
            target_emotion=other_emotion,
            target_intensity=intensity,
            empathy_type=empathy_type,
            empathy_level=empathy_level,
            mirrored_state=self.mirror_emotion(other_emotion, intensity),
            response=response_text,
            resonance_score=resonance
        )
        self._empathy_history.append(record)

        return EmpathyResponse(
            response_text=response_text,
            empathy_level=empathy_level,
            empathy_type=empathy_type,
            resonance_score=resonance,
            suggested_actions=suggested_actions,
            emotional_support_score=min(1.0, resonance * 1.2)
        )

    def detect_resonance(
        self,
        other_emotion: str,
        other_intensity: float,
        own_state: Dict[str, float]
    ) -> float:
        """
        检测情感共鸣

        Args:
            other_emotion: 他人情感类型
            other_intensity: 他人情感强度
            own_state: 自身情感状态

        Returns:
            float: 共鸣分数 (0-1)
        """
        emotion_valence_map = {
            "joy": 1.0, "trust": 0.8, "anticipation": 0.5,
            "surprise": 0.0,
            "sadness": -1.0, "fear": -0.8, "anger": -0.7, "disgust": -0.6
        }

        other_valence = emotion_valence_map.get(other_emotion, 0.0) * other_intensity
        own_valence = own_state.get("valence", 0.0)

        valence_match = 1.0 - abs(other_valence - own_valence) / 2
        valence_match = max(0.0, valence_match)

        other_arousal = other_intensity * 0.7
        own_arousal = own_state.get("arousal", 0.0)
        arousal_match = 1.0 - abs(other_arousal - own_arousal)
        arousal_match = max(0.0, arousal_match)

        intensity_proximity = 1.0 - abs(other_intensity - abs(own_valence))
        intensity_proximity = max(0.0, intensity_proximity)

        resonance = (
            valence_match * self.RESONANCE_WEIGHTS["valence_match"] +
            arousal_match * self.RESONANCE_WEIGHTS["arousal_match"] +
            intensity_proximity * self.RESONANCE_WEIGHTS["intensity_proximity"]
        )

        self._current_resonance = resonance
        logger.debug(f"Detected resonance: {resonance:.2f}")
        return resonance

    def adjust_empathy_level(
        self,
        current_level: EmpathyLevel,
        situation: Dict[str, Any]
    ) -> EmpathyLevel:
        """
        调节共情程度

        Args:
            current_level: 当前共情等级
            situation: 情境信息

        Returns:
            EmpathyLevel: 调整后的共情等级
        """
        urgency = situation.get("urgency", 0.5)
        familiarity = situation.get("familiarity", 0.5)
        emotional_distance = situation.get("emotional_distance", 0.5)

        level_scores = {
            EmpathyLevel.NONE: 0.0,
            EmpathyLevel.LOW: 0.25,
            EmpathyLevel.MODERATE: 0.5,
            EmpathyLevel.HIGH: 0.75,
            EmpathyLevel.DEEP: 1.0,
        }

        current_score = level_scores[current_level]

        if urgency > 0.7:
            current_score += 0.2
        if familiarity > 0.6:
            current_score += 0.15
        if emotional_distance > 0.6:
            current_score -= 0.2

        current_score = max(0.0, min(1.0, current_score))

        if current_score < 0.15:
            return EmpathyLevel.NONE
        elif current_score < 0.35:
            return EmpathyLevel.LOW
        elif current_score < 0.6:
            return EmpathyLevel.MODERATE
        elif current_score < 0.85:
            return EmpathyLevel.HIGH
        else:
            return EmpathyLevel.DEEP

    def get_empathy_history(
        self,
        limit: int = 50
    ) -> List[EmpathyRecord]:
        """获取共情历史"""
        return self._empathy_history[-limit:]

    def get_average_resonance(self) -> float:
        """获取平均共鸣分数"""
        if not self._empathy_history:
            return 0.0
        return sum(r.resonance_score for r in self._empathy_history) / len(self._empathy_history)

    def _infer_causes(
        self,
        emotion: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """推断情感可能的原因"""
        common_causes = {
            "joy": ["成功", "好消息", "被认可", "达成目标"],
            "sadness": ["失去", "失败", "失望", "分离"],
            "anger": ["不公平", "被冒犯", "阻碍", "背叛"],
            "fear": ["威胁", "未知", "危险", "不确定性"],
            "surprise": ["意外事件", "新信息", "突发事件"],
            "disgust": ["厌恶的事物", "道德冒犯", "不适"],
            "trust": ["被信任", "合作成功", "安全感"],
            "anticipation": ["期待的事件", "即将发生", "希望"],
        }
        return common_causes.get(emotion, ["未知原因"])

    def _determine_response_level(self, intensity: float) -> EmpathyLevel:
        """根据强度确定响应等级"""
        if intensity < 0.2:
            return EmpathyLevel.LOW
        elif intensity < 0.5:
            return EmpathyLevel.MODERATE
        elif intensity < 0.8:
            return EmpathyLevel.HIGH
        else:
            return EmpathyLevel.DEEP

    def _identify_needs(self, emotion: str) -> List[str]:
        """识别潜在需求"""
        needs_map = {
            "joy": ["分享", "庆祝", "认可"],
            "sadness": ["安慰", "倾听", "陪伴"],
            "anger": ["理解", "公正", "发泄"],
            "fear": ["安全感", "信息", "支持"],
            "surprise": ["解释", "适应", "信息"],
            "disgust": ["距离", "清洁", "改变"],
            "trust": ["回报", "深化", "维护"],
            "anticipation": ["耐心", "准备", "鼓励"],
        }
        return needs_map.get(emotion, ["倾听"])

    def _select_empathy_type(
        self,
        emotion: str,
        intensity: float
    ) -> EmpathyType:
        """选择共情类型"""
        if not self.config.enable_cognitive_empathy:
            return EmpathyType.AFFECTIVE
        if not self.config.enable_affective_empathy:
            return EmpathyType.COGNITIVE

        if intensity > 0.6:
            return EmpathyType.AFFECTIVE
        elif emotion in ["sadness", "fear"]:
            return EmpathyType.COMPASSIONATE
        else:
            return EmpathyType.COGNITIVE

    def _calculate_resonance(
        self,
        emotion: str,
        intensity: float
    ) -> float:
        """计算共鸣分数"""
        base_resonance = intensity * 0.7
        emotion_multiplier = {
            "joy": 1.0, "sadness": 1.1, "anger": 0.9,
            "fear": 1.0, "surprise": 0.8, "trust": 0.9
        }
        return min(1.0, base_resonance * emotion_multiplier.get(emotion, 1.0))

    def _suggest_actions(
        self,
        emotion: str,
        level: EmpathyLevel
    ) -> List[str]:
        """建议行动"""
        if level in [EmpathyLevel.NONE, EmpathyLevel.LOW]:
            return ["继续观察"]

        actions = {
            "joy": ["分享喜悦", "给予肯定", "一起庆祝"],
            "sadness": ["倾听", "给予安慰", "提供陪伴"],
            "anger": ["倾听", "表示理解", "帮助冷静"],
            "fear": ["提供信息", "给予安全感", "陪伴"],
            "surprise": ["解释情况", "帮助适应", "提供支持"],
            "trust": ["回报信任", "深化关系", "保持诚实"],
        }
        return actions.get(emotion, ["倾听", "表示理解"])

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._empathy_history:
            return {"total_interactions": 0}

        emotion_counts = {}
        level_counts = {}
        for record in self._empathy_history:
            emotion_counts[record.target_emotion] = emotion_counts.get(
                record.target_emotion, 0
            ) + 1
            level_counts[record.empathy_level.value] = level_counts.get(
                record.empathy_level.value, 0
            ) + 1

        return {
            "total_interactions": len(self._empathy_history),
            "average_resonance": self.get_average_resonance(),
            "current_resonance": self._current_resonance,
            "emotion_distribution": emotion_counts,
            "level_distribution": level_counts,
            "config": self.config.model_dump(),
        }
