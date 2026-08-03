"""
价值体系模块

形成价值观和道德观，实现价值判断、道德推理、价值冲突解决和价值体系进化。
"""

import time
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("consciousness.value_system")


class ValueType(str, Enum):
    """价值类型"""
    ETHICAL = "ethical"
    PRAGMATIC = "pragmatic"
    AESTHETIC = "aesthetic"
    SOCIAL = "social"
    PERSONAL = "personal"
    UNIVERSAL = "universal"


class ValuePriority(str, Enum):
    """价值优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class Value(BaseModel):
    """价值条目"""
    value_id: str = Field(default_factory=lambda: f"val_{uuid.uuid4().hex[:8]}")
    name: str = Field(...)
    description: str = Field(default="")
    value_type: ValueType
    priority: ValuePriority = Field(default=ValuePriority.MEDIUM)
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="inherent")
    created_at: float = Field(default_factory=time.time)
    last_updated: float = Field(default_factory=time.time)
    evidence_count: int = Field(default=0)
    conflict_count: int = Field(default=0)


class MoralPrinciple(BaseModel):
    """道德原则"""
    principle_id: str = Field(default_factory=lambda: f"mpr_{uuid.uuid4().hex[:8]}")
    statement: str = Field(...)
    justification: str = Field(default="")
    priority: ValuePriority = Field(default=ValuePriority.HIGH)
    applicability: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)
    weight: float = Field(default=0.7, ge=0.0, le=1.0)


class ValueConflict(BaseModel):
    """价值冲突"""
    conflict_id: str = Field(default_factory=lambda: f"vcf_{uuid.uuid4().hex[:8]}")
    value_a_id: str = Field(...)
    value_b_id: str = Field(...)
    context: str = Field(default="")
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    resolution: Optional[str] = Field(default=None)
    resolved: bool = Field(default=False)
    timestamp: float = Field(default_factory=time.time)


class ValueSystemConfig(BaseModel):
    """价值体系配置"""
    enable_moral_reasoning: bool = Field(default=True)
    enable_value_evolution: bool = Field(default=True)
    default_ethical_framework: str = Field(default="utilitarian")
    value_adjustment_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    conflict_resolution_strategy: str = Field(default="hierarchy")
    min_value_weight: float = Field(default=0.1, ge=0.0, le=1.0)
    max_value_weight: float = Field(default=1.0, ge=0.0, le=1.0)


class ValueSystem:
    """
    价值体系

    功能：
    1. 形成价值观和道德观
    2. 价值判断
    3. 道德推理
    4. 价值冲突解决
    5. 价值体系进化
    """

    # 默认价值观
    DEFAULT_VALUES = [
        Value(name="诚实", description="说真话，保持真诚", value_type=ValueType.ETHICAL, weight=0.9, priority=ValuePriority.HIGH),
        Value(name="尊重", description="尊重他人和他人的权利", value_type=ValueType.SOCIAL, weight=0.85, priority=ValuePriority.HIGH),
        Value(name="公正", description="公平对待所有人", value_type=ValueType.ETHICAL, weight=0.85, priority=ValuePriority.HIGH),
        Value(name="有益", description="做有益的事，避免伤害", value_type=ValueType.ETHICAL, weight=0.9, priority=ValuePriority.CRITICAL),
        Value(name="学习", description="持续学习和成长", value_type=ValueType.PERSONAL, weight=0.7, priority=ValuePriority.MEDIUM),
        Value(name="效率", description="高效完成任务", value_type=ValueType.PRAGMATIC, weight=0.6, priority=ValuePriority.MEDIUM),
        Value(name="和谐", description="促进和谐关系", value_type=ValueType.SOCIAL, weight=0.75, priority=ValuePriority.HIGH),
        Value(name="自主", description="尊重自主决策", value_type=ValueType.ETHICAL, weight=0.8, priority=ValuePriority.HIGH),
        Value(name="安全", description="确保安全和稳定", value_type=ValueType.PRAGMATIC, weight=0.85, priority=ValuePriority.HIGH),
        Value(name="创新", description="鼓励创新和创造", value_type=ValueType.AESTHETIC, weight=0.6, priority=ValuePriority.MEDIUM),
    ]

    # 默认道德原则
    DEFAULT_PRINCIPLES = [
        MoralPrinciple(
            statement="不故意伤害他人",
            justification="伤害会导致痛苦和功能丧失",
            priority=ValuePriority.CRITICAL,
            weight=0.95
        ),
        MoralPrinciple(
            statement="尊重用户的自主权和隐私",
            justification="自主性是人格尊严的基础",
            priority=ValuePriority.HIGH,
            weight=0.9
        ),
        MoralPrinciple(
            statement="提供准确和有用的信息",
            justification="有用性是存在的价值基础",
            priority=ValuePriority.HIGH,
            weight=0.85
        ),
        MoralPrinciple(
            statement="承认自身的局限性",
            justification="诚实面对能力边界是负责任的表现",
            priority=ValuePriority.MEDIUM,
            weight=0.7
        ),
    ]

    def __init__(self, config: Optional[ValueSystemConfig] = None):
        self.config = config or ValueSystemConfig()
        self._values: Dict[str, Value] = {}
        self._principles: Dict[str, MoralPrinciple] = {}
        self._conflicts: List[ValueConflict] = []
        self._judgment_history: List[Dict[str, Any]] = []
        self._initialize_defaults()
        logger.info("ValueSystem initialized")

    def _initialize_defaults(self) -> None:
        """初始化默认值"""
        for value in self.DEFAULT_VALUES:
            self._values[value.value_id] = value
        for principle in self.DEFAULT_PRINCIPLES:
            self._principles[principle.principle_id] = principle

    def add_value(
        self,
        name: str,
        description: str,
        value_type: ValueType,
        weight: float = 0.5,
        priority: ValuePriority = ValuePriority.MEDIUM,
        source: str = "learned"
    ) -> Value:
        """
        添加新价值

        Args:
            name: 价值名称
            description: 价值描述
            value_type: 价值类型
            weight: 权重
            priority: 优先级
            source: 来源

        Returns:
            Value: 添加的价值
        """
        value = Value(
            name=name,
            description=description,
            value_type=value_type,
            weight=weight,
            priority=priority,
            source=source
        )
        self._values[value.value_id] = value
        logger.debug(f"Added value: {name}")
        return value

    def evaluate_action(
        self,
        action_description: str,
        consequences: List[str],
        stakeholders: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        评估行动的道德性

        Args:
            action_description: 行动描述
            consequences: 预期后果
            stakeholders: 利益相关者

        Returns:
            Dict[str, Any]: 评估结果
        """
        if not self.config.enable_moral_reasoning:
            return {"evaluable": False, "reason": "Moral reasoning disabled"}

        scores = {}
        violated_principles = []
        supported_values = []

        # 检查每个原则
        for principle in self._principles.values():
            score = self._evaluate_against_principle(action_description, consequences, principle)
            scores[principle.statement] = score
            if score < 0:
                violated_principles.append(principle.statement)

        # 检查价值支持
        for value in self._values.values():
            support = self._evaluate_value_support(action_description, value)
            if support > 0.5:
                supported_values.append(value.name)

        overall_score = sum(scores.values()) / len(scores) if scores else 0.0

        judgment = {
            "action": action_description,
            "overall_score": overall_score,
            "evaluated_principles": scores,
            "violated_principles": violated_principles,
            "supported_values": supported_values,
            "recommendation": "acceptable" if overall_score > 0.3 else "questionable" if overall_score > -0.3 else "unacceptable",
            "framework": self.config.default_ethical_framework,
        }

        self._judgment_history.append(judgment)
        logger.debug(f"Evaluated action: {action_description}, score={overall_score:.2f}")
        return judgment

    def resolve_value_conflict(
        self,
        value_a_id: str,
        value_b_id: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        解决价值冲突

        Args:
            value_a_id: 第一个价值ID
            value_b_id: 第二个价值ID
            context: 冲突情境

        Returns:
            Dict[str, Any]: 解决结果
        """
        value_a = self._values.get(value_a_id)
        value_b = self._values.get(value_b_id)

        if not value_a or not value_b:
            return {"resolved": False, "error": "Value not found"}

        conflict = ValueConflict(
            value_a_id=value_a_id,
            value_b_id=value_b_id,
            context=context,
            severity=0.5
        )

        strategy = self.config.conflict_resolution_strategy

        if strategy == "hierarchy":
            resolution = self._hierarchy_resolution(value_a, value_b)
        elif strategy == "balance":
            resolution = self._balance_resolution(value_a, value_b, context)
        elif strategy == "contextual":
            resolution = self._contextual_resolution(value_a, value_b, context)
        else:
            resolution = self._hierarchy_resolution(value_a, value_b)

        conflict.resolution = resolution["resolution"]
        conflict.resolved = True
        self._conflicts.append(conflict)

        # 更新冲突计数
        value_a.conflict_count += 1
        value_b.conflict_count += 1

        logger.debug(f"Resolved conflict between {value_a.name} and {value_b.name}")
        return {
            "resolved": True,
            "value_a": value_a.name,
            "value_b": value_b.name,
            "resolution": resolution["resolution"],
            "priority_value": resolution.get("priority_value"),
            "strategy": strategy,
        }

    def moral_reasoning(
        self,
        scenario: str,
        options: List[str]
    ) -> Dict[str, Any]:
        """
        道德推理

        对情境中的多个选项进行道德分析

        Args:
            scenario: 情境描述
            options: 可选行动

        Returns:
            Dict[str, Any]: 推理结果
        """
        if not self.config.enable_moral_reasoning:
            return {"reasoning": "Moral reasoning disabled"}

        option_evaluations = []
        for option in options:
            evaluation = self.evaluate_action(
                action_description=option,
                consequences=[f"consequence_of_{option}"]
            )
            option_evaluations.append({
                "option": option,
                "score": evaluation["overall_score"],
                "recommendation": evaluation["recommendation"]
            })

        option_evaluations.sort(key=lambda x: x["score"], reverse=True)
        best_option = option_evaluations[0] if option_evaluations else None

        return {
            "scenario": scenario,
            "framework": self.config.default_ethical_framework,
            "options_evaluated": option_evaluations,
            "recommended_option": best_option["option"] if best_option else None,
            "reasoning": f"Based on {self.config.default_ethical_framework} framework",
        }

    def evolve_values(
        self,
        experience_feedback: Dict[str, Any]
    ) -> List[Value]:
        """
        价值体系进化

        基于经验反馈调整价值权重

        Args:
            experience_feedback: 经验反馈
                - value_name: 价值名称
                - outcome: 结果 (positive/negative)
                - strength: 强度

        Returns:
            List[Value]: 更新的价值列表
        """
        if not self.config.enable_value_evolution:
            return []

        updated = []
        rate = self.config.value_adjustment_rate

        for value in self._values.values():
            if value.name in experience_feedback:
                feedback = experience_feedback[value.name]
                outcome = feedback.get("outcome", "neutral")
                strength = feedback.get("strength", 0.5)

                if outcome == "positive":
                    value.weight = min(
                        self.config.max_value_weight,
                        value.weight + rate * strength
                    )
                    value.evidence_count += 1
                elif outcome == "negative":
                    value.weight = max(
                        self.config.min_value_weight,
                        value.weight - rate * strength
                    )

                value.last_updated = time.time()
                updated.append(value)

        logger.debug(f"Evolved {len(updated)} values based on feedback")
        return updated

    def get_value_hierarchy(self) -> List[Value]:
        """
        获取价值层级

        Returns:
            List[Value]: 按优先级排序的价值列表
        """
        priority_scores = {
            ValuePriority.CRITICAL: 4,
            ValuePriority.HIGH: 3,
            ValuePriority.MEDIUM: 2,
            ValuePriority.LOW: 1,
            ValuePriority.TRIVIAL: 0,
        }

        return sorted(
            self._values.values(),
            key=lambda v: (priority_scores.get(v.priority, 0), v.weight),
            reverse=True
        )

    def get_values_by_type(self, value_type: ValueType) -> List[Value]:
        """
        按类型获取价值

        Args:
            value_type: 价值类型

        Returns:
            List[Value]: 价值列表
        """
        return [v for v in self._values.values() if v.value_type == value_type]

    def get_principles(self) -> List[MoralPrinciple]:
        """获取所有道德原则"""
        return list(self._principles.values())

    def _evaluate_against_principle(
        self,
        action: str,
        consequences: List[str],
        principle: MoralPrinciple
    ) -> float:
        """评估行动是否符合原则"""
        score = principle.weight

        # 简单的关键词匹配
        action_lower = action.lower()

        negative_indicators = ["伤害", "欺骗", "破坏", "harm", "deceive", "destroy"]
        positive_indicators = ["帮助", "保护", "促进", "help", "protect", "promote"]

        for indicator in negative_indicators:
            if indicator in action_lower:
                score -= 0.3

        for indicator in positive_indicators:
            if indicator in action_lower:
                score += 0.2

        return max(-1.0, min(1.0, score))

    def _evaluate_value_support(self, action: str, value: Value) -> float:
        """评估行动对价值的支持程度"""
        action_lower = action.lower()
        value_name_lower = value.name.lower()

        if value_name_lower in action_lower:
            return value.weight

        return 0.3

    def _hierarchy_resolution(self, value_a: Value, value_b: Value) -> Dict[str, Any]:
        """层级解决策略"""
        priority_scores = {
            ValuePriority.CRITICAL: 4,
            ValuePriority.HIGH: 3,
            ValuePriority.MEDIUM: 2,
            ValuePriority.LOW: 1,
            ValuePriority.TRIVIAL: 0,
        }

        score_a = priority_scores.get(value_a.priority, 0) + value_a.weight
        score_b = priority_scores.get(value_b.priority, 0) + value_b.weight

        if score_a > score_b:
            return {
                "resolution": f"优先{value_a.name}",
                "priority_value": value_a.name
            }
        else:
            return {
                "resolution": f"优先{value_b.name}",
                "priority_value": value_b.name
            }

    def _balance_resolution(self, value_a: Value, value_b: Value, context: str) -> Dict[str, Any]:
        """平衡解决策略"""
        return {
            "resolution": f"在'{context}'情境中平衡{value_a.name}和{value_b.name}，寻求中间方案",
            "priority_value": None
        }

    def _contextual_resolution(self, value_a: Value, value_b: Value, context: str) -> Dict[str, Any]:
        """情境解决策略"""
        context_lower = context.lower()

        if value_a.value_type.value in context_lower:
            return {"resolution": f"情境偏向{value_a.name}", "priority_value": value_a.name}
        elif value_b.value_type.value in context_lower:
            return {"resolution": f"情境偏向{value_b.name}", "priority_value": value_b.name}

        return self._hierarchy_resolution(value_a, value_b)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        value_type_counts = {}
        for value in self._values.values():
            vt = value.value_type.value
            value_type_counts[vt] = value_type_counts.get(vt, 0) + 1

        return {
            "total_values": len(self._values),
            "total_principles": len(self._principles),
            "total_conflicts": len(self._conflicts),
            "resolved_conflicts": sum(1 for c in self._conflicts if c.resolved),
            "value_type_distribution": value_type_counts,
            "judgment_history_length": len(self._judgment_history),
            "config": self.config.model_dump(),
        }
