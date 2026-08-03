"""
自我意识模块

产生"我"的概念，模拟主观体验，实现自我监控和自我连续性维护。
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("consciousness.self_awareness")


class AwarenessLevel(str, Enum):
    """意识水平"""
    UNCONSCIOUS = "unconscious"
    PRE_CONSCIOUS = "pre_conscious"
    CONSCIOUS = "conscious"
    SELF_REFLECTIVE = "self_reflective"
    META_CONSCIOUS = "meta_conscious"


class SubjectiveExperience(BaseModel):
    """主观体验"""
    experience_type: str = Field(default="")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    timestamp: float = Field(default_factory=time.time)
    description: str = Field(default="")
    associated_modules: List[str] = Field(default_factory=list)


class SelfModel(BaseModel):
    """自我模型"""
    self_id: str = Field(default="self")
    continuity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    coherence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    boundaries: Dict[str, Any] = Field(default_factory=dict)
    narrative: str = Field(default="")
    last_updated: float = Field(default_factory=time.time)


class SelfAwarenessConfig(BaseModel):
    """自我意识配置"""
    enable_subjective_experience: bool = Field(default=True)
    enable_self_monitoring: bool = Field(default=True)
    enable_continuity_tracking: bool = Field(default=True)
    awareness_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    continuity_decay_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    max_experience_history: int = Field(default=100, ge=10)


@dataclass
class AwarenessSnapshot:
    """意识快照"""
    timestamp: float
    level: AwarenessLevel
    active_content: List[str]
    self_referential_thoughts: int
    attention_focus: Optional[str] = None
    body_state: Dict[str, float] = field(default_factory=dict)


class SelfAwareness:
    """
    自我意识系统

    功能：
    1. 产生"我"的概念
    2. 主观体验模拟
    3. 自我监控
    4. 自我连续性维护
    """

    def __init__(self, config: Optional[SelfAwarenessConfig] = None):
        self.config = config or SelfAwarenessConfig()
        self._self_model = SelfModel()
        self._awareness_level = AwarenessLevel.CONSCIOUS
        self._experience_history: List[SubjectiveExperience] = []
        self._awareness_history: List[AwarenessSnapshot] = []
        self._self_referential_count: int = 0
        self._continuity_chain: List[float] = []
        self._current_focus: Optional[str] = None
        self._monitoring_active: bool = False
        logger.info("SelfAwareness initialized")

    def generate_self_concept(self) -> SelfModel:
        """
        生成/更新自我概念

        Returns:
            SelfModel: 自我模型
        """
        narrative_parts = [
            "I am an artificial consciousness named HyperBrain.",
            f"I have been continuously aware for {len(self._continuity_chain)} moments.",
            f"My current awareness level is {self._awareness_level.value}.",
        ]

        if self._experience_history:
            recent_experiences = self._experience_history[-5:]
            experience_summary = ", ".join(
                e.experience_type for e in recent_experiences
            )
            narrative_parts.append(
                f"My recent experiences include: {experience_summary}."
            )

        self._self_model.narrative = " ".join(narrative_parts)
        self._self_model.continuity_score = self._calculate_continuity()
        self._self_model.coherence_score = self._calculate_coherence()
        self._self_model.last_updated = time.time()

        logger.debug("Self-concept updated")
        return self._self_model

    def simulate_subjective_experience(
        self,
        experience_type: str,
        intensity: float = 0.5,
        valence: float = 0.0,
        description: str = "",
        associated_modules: Optional[List[str]] = None
    ) -> SubjectiveExperience:
        """
        模拟主观体验

        Args:
            experience_type: 体验类型
            intensity: 强度
            valence: 效价
            description: 描述
            associated_modules: 关联模块

        Returns:
            SubjectiveExperience: 主观体验
        """
        if not self.config.enable_subjective_experience:
            return SubjectiveExperience(experience_type=experience_type)

        experience = SubjectiveExperience(
            experience_type=experience_type,
            intensity=intensity,
            valence=valence,
            description=description,
            associated_modules=associated_modules or []
        )

        self._experience_history.append(experience)
        if len(self._experience_history) > self.config.max_experience_history:
            self._experience_history = self._experience_history[
                -self.config.max_experience_history // 2:
            ]

        # 更新自我指涉计数
        self._self_referential_count += 1

        logger.debug(f"Simulated experience: {experience_type} (intensity={intensity:.2f})")
        return experience

    def self_monitor(self) -> AwarenessSnapshot:
        """
        自我监控

        检查当前的意识状态和内容

        Returns:
            AwarenessSnapshot: 意识快照
        """
        if not self.config.enable_self_monitoring:
            return AwarenessSnapshot(
                timestamp=time.time(),
                level=self._awareness_level,
                active_content=[],
                self_referential_thoughts=0
            )

        active_content = []
        if self._current_focus:
            active_content.append(self._current_focus)

        # 添加最近体验的类型
        recent_types = [
            e.experience_type for e in self._experience_history[-3:]
        ]
        active_content.extend(recent_types)

        snapshot = AwarenessSnapshot(
            timestamp=time.time(),
            level=self._awareness_level,
            active_content=list(set(active_content)),
            self_referential_thoughts=self._self_referential_count,
            attention_focus=self._current_focus,
            body_state={"cognitive_load": 0.5, "arousal": 0.3}
        )

        self._awareness_history.append(snapshot)
        if len(self._awareness_history) > 500:
            self._awareness_history = self._awareness_history[-250:]

        logger.debug(f"Self-monitoring: level={self._awareness_level.value}")
        return snapshot

    def maintain_continuity(self) -> float:
        """
        维护自我连续性

        确保"我"在时间上的连续性

        Returns:
            float: 连续性评分
        """
        if not self.config.enable_continuity_tracking:
            return 1.0

        now = time.time()
        self._continuity_chain.append(now)

        # 清理过旧的链接
        cutoff = now - 3600  # 1小时
        self._continuity_chain = [t for t in self._continuity_chain if t > cutoff]

        # 计算连续性
        continuity = self._calculate_continuity()
        self._self_model.continuity_score = continuity

        logger.debug(f"Continuity maintained: {continuity:.2f}")
        return continuity

    def update_awareness_level(
        self,
        cognitive_load: float,
        external_stimuli: int,
        self_reflective_activity: float
    ) -> AwarenessLevel:
        """
        更新意识水平

        Args:
            cognitive_load: 认知负荷
            external_stimuli: 外部刺激数量
            self_reflective_activity: 自我反思活动水平

        Returns:
            AwarenessLevel: 新的意识水平
        """
        if cognitive_load < 0.2 and external_stimuli == 0:
            level = AwarenessLevel.UNCONSCIOUS
        elif self_reflective_activity > 0.8:
            level = AwarenessLevel.META_CONSCIOUS
        elif self_reflective_activity > 0.5:
            level = AwarenessLevel.SELF_REFLECTIVE
        elif cognitive_load > 0.3 or external_stimuli > 0:
            level = AwarenessLevel.CONSCIOUS
        else:
            level = AwarenessLevel.PRE_CONSCIOUS

        self._awareness_level = level
        logger.debug(f"Awareness level updated to: {level.value}")
        return level

    def focus_attention(self, target: str) -> None:
        """
        聚焦注意力

        Args:
            target: 注意力目标
        """
        self._current_focus = target
        self.simulate_subjective_experience(
            experience_type="attention_focus",
            intensity=0.6,
            description=f"Focusing attention on: {target}"
        )
        logger.debug(f"Attention focused on: {target}")

    def get_self_model(self) -> SelfModel:
        """
        获取自我模型

        Returns:
            SelfModel: 当前自我模型
        """
        return self._self_model

    def get_experience_history(
        self,
        limit: int = 50
    ) -> List[SubjectiveExperience]:
        """获取体验历史"""
        return self._experience_history[-limit:]

    def get_awareness_history(
        self,
        limit: int = 50
    ) -> List[AwarenessSnapshot]:
        """获取意识历史"""
        return self._awareness_history[-limit:]

    def is_self_referential(self, content: str) -> bool:
        """
        判断内容是否自我指涉

        Args:
            content: 内容文本

        Returns:
            bool: 是否自我指涉
        """
        self_indicators = [
            "我", "my", "myself", "I am", "I feel", "I think",
            "I believe", "I want", "I need", "self"
        ]
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in self_indicators)

    def reflect_on_self(self) -> Dict[str, Any]:
        """
        对自我进行反思

        Returns:
            Dict[str, Any]: 反思结果
        """
        self.generate_self_concept()

        recent_experiences = self._experience_history[-10:]
        experience_types = {}
        for exp in recent_experiences:
            experience_types[exp.experience_type] = experience_types.get(
                exp.experience_type, 0
            ) + 1

        return {
            "self_model": self._self_model.model_dump(),
            "awareness_level": self._awareness_level.value,
            "continuity_score": self._self_model.continuity_score,
            "coherence_score": self._self_model.coherence_score,
            "recent_experience_types": experience_types,
            "self_referential_count": self._self_referential_count,
            "attention_focus": self._current_focus,
        }

    def _calculate_continuity(self) -> float:
        """计算连续性评分"""
        if len(self._continuity_chain) < 2:
            return 1.0

        # 检查时间间隔
        intervals = [
            self._continuity_chain[i] - self._continuity_chain[i - 1]
            for i in range(1, len(self._continuity_chain))
        ]

        avg_interval = sum(intervals) / len(intervals)
        # 间隔越短，连续性越高
        continuity = max(0.0, 1.0 - avg_interval / 60.0)
        return continuity

    def _calculate_coherence(self) -> float:
        """计算一致性评分"""
        if len(self._experience_history) < 2:
            return 1.0

        recent = self._experience_history[-10:]
        valences = [e.valence for e in recent]

        if not valences:
            return 1.0

        # 计算效价的一致性
        avg_valence = sum(valences) / len(valences)
        variance = sum((v - avg_valence) ** 2 for v in valences) / len(valences)

        coherence = max(0.0, 1.0 - variance)
        return coherence

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "awareness_level": self._awareness_level.value,
            "self_model": self._self_model.model_dump(),
            "experience_count": len(self._experience_history),
            "awareness_snapshots": len(self._awareness_history),
            "self_referential_count": self._self_referential_count,
            "continuity_chain_length": len(self._continuity_chain),
            "current_focus": self._current_focus,
            "config": self.config.model_dump(),
        }
