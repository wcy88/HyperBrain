"""
决策模块 (Decision Making Module)

实现多种决策模式：
- 基于目标的决策
- 基于价值的决策
- 基于风险的决策
- 多准则决策分析
- 决策树实现
"""

import uuid
import math
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.decision_making")


class DecisionType(str, Enum):
    """决策类型枚举"""
    GOAL_BASED = "goal_based"            # 基于目标
    VALUE_BASED = "value_based"          # 基于价值
    RISK_BASED = "risk_based"            # 基于风险
    MULTI_CRITERIA = "multi_criteria"    # 多准则
    PROBABILISTIC = "probabilistic"      # 概率决策


class DecisionStatus(str, Enum):
    """决策状态枚举"""
    PENDING = "pending"                  # 待决策
    ANALYZING = "analyzing"              # 分析中
    DECIDED = "decided"                  # 已决策
    EXECUTED = "executed"                # 已执行
    EVALUATED = "evaluated"              # 已评估
    REVISED = "revised"                  # 已修订


class RiskLevel(str, Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Alternative(BaseModel):
    """决策选项模型"""
    alternative_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    description: str = Field(default="")
    expected_outcomes: List[str] = Field(default_factory=list)
    probabilities: Dict[str, float] = Field(default_factory=dict)
    values: Dict[str, float] = Field(default_factory=dict)
    costs: Dict[str, float] = Field(default_factory=dict)
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_feasible: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Criterion(BaseModel):
    """决策准则模型"""
    criterion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    direction: str = Field(default="maximize")
    scale_min: float = Field(default=0.0)
    scale_max: float = Field(default=1.0)
    description: str = Field(default="")

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Goal(BaseModel):
    """目标模型"""
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(...)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    deadline: Optional[datetime] = Field(default=None)
    sub_goals: List[str] = Field(default_factory=list)
    is_achieved: bool = Field(default=False)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class RiskAssessment(BaseModel):
    """风险评估模型"""
    risk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(...)
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    impact: float = Field(default=0.0, ge=0.0, le=1.0)
    mitigation: str = Field(default="")
    risk_level: RiskLevel = Field(default=RiskLevel.VERY_LOW)

    @field_validator("probability", "impact")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def model_post_init(self, __context: Any) -> None:
        score = self.probability * self.impact
        if score > 0.8:
            self.risk_level = RiskLevel.VERY_HIGH
        elif score > 0.6:
            self.risk_level = RiskLevel.HIGH
        elif score > 0.4:
            self.risk_level = RiskLevel.MEDIUM
        elif score > 0.2:
            self.risk_level = RiskLevel.LOW
        else:
            self.risk_level = RiskLevel.VERY_LOW


class DecisionTreeNode(BaseModel):
    """决策树节点"""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    node_type: str = Field(default="decision")
    probability: Optional[float] = Field(default=None)
    value: float = Field(default=0.0)
    children: List["DecisionTreeNode"] = Field(default_factory=list)
    parent_id: Optional[str] = Field(default=None)
    is_terminal: bool = Field(default=False)


class DecisionResult(BaseModel):
    """决策结果模型"""
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: DecisionType = Field(...)
    selected_alternative: Optional[Alternative] = Field(default=None)
    alternatives: List[Alternative] = Field(default_factory=list)
    reasoning: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_value: float = Field(default=0.0)
    risks: List[RiskAssessment] = Field(default_factory=list)
    status: DecisionStatus = Field(default=DecisionStatus.DECIDED)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class DecisionMaker:
    """
    决策器

    实现多种决策模式，支持多准则分析和决策树。

    Attributes:
        criteria: 决策准则库
        goals: 目标库
        decision_history: 决策历史
    """

    def __init__(
        self,
        risk_tolerance: float = 0.5,
        enable_logging: bool = True
    ):
        self.criteria: Dict[str, Criterion] = {}
        self.goals: Dict[str, Goal] = {}
        self.decision_history: List[DecisionResult] = []
        self.risk_tolerance = risk_tolerance
        self.enable_logging = enable_logging

        if enable_logging:
            logger.info("DecisionMaker initialized")

    def add_criterion(self, criterion: Criterion) -> None:
        """添加决策准则"""
        self.criteria[criterion.criterion_id] = criterion
        logger.debug(f"Added criterion: {criterion.name}")

    def add_goal(self, goal: Goal) -> None:
        """添加目标"""
        self.goals[goal.goal_id] = goal
        logger.debug(f"Added goal: {goal.description}")

    def goal_based_decision(
        self,
        alternatives: List[Alternative],
        goals: Optional[List[Goal]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DecisionResult:
        """
        基于目标的决策

        选择最能实现目标的方案。

        Args:
            alternatives: 可选方案
            goals: 目标列表
            context: 上下文

        Returns:
            DecisionResult: 决策结果
        """
        start_time = datetime.now()
        target_goals = goals or list(self.goals.values())

        if not target_goals:
            return DecisionResult(
                decision_type=DecisionType.GOAL_BASED,
                reasoning="没有定义目标",
                confidence=0.0
            )

        scored_alternatives = []
        for alt in alternatives:
            score = self._evaluate_goal_alignment(alt, target_goals)
            alt.score = score
            scored_alternatives.append(alt)

        scored_alternatives.sort(key=lambda a: a.score, reverse=True)
        selected = scored_alternatives[0] if scored_alternatives else None

        reasoning = self._generate_goal_reasoning(selected, target_goals)

        result = DecisionResult(
            decision_type=DecisionType.GOAL_BASED,
            selected_alternative=selected,
            alternatives=scored_alternatives,
            reasoning=reasoning,
            confidence=selected.score if selected else 0.0,
            metadata={"goal_count": len(target_goals), "context": context or {}}
        )

        self.decision_history.append(result)
        logger.info(f"Goal-based decision made: selected={selected.name if selected else 'None'}")
        return result

    def value_based_decision(
        self,
        alternatives: List[Alternative],
        values: Optional[Dict[str, float]] = None,
        criteria_weights: Optional[Dict[str, float]] = None
    ) -> DecisionResult:
        """
        基于价值的决策

        根据价值体系选择最优方案。

        Args:
            alternatives: 可选方案
            values: 价值权重
            criteria_weights: 准则权重

        Returns:
            DecisionResult: 决策结果
        """
        start_time = datetime.now()
        value_weights = values or {}

        scored_alternatives = []
        for alt in alternatives:
            score = self._evaluate_value_alignment(alt, value_weights, criteria_weights)
            alt.score = score
            scored_alternatives.append(alt)

        scored_alternatives.sort(key=lambda a: a.score, reverse=True)
        selected = scored_alternatives[0] if scored_alternatives else None

        reasoning = self._generate_value_reasoning(selected, value_weights)

        result = DecisionResult(
            decision_type=DecisionType.VALUE_BASED,
            selected_alternative=selected,
            alternatives=scored_alternatives,
            reasoning=reasoning,
            confidence=selected.score if selected else 0.0,
            metadata={"value_dimensions": list(value_weights.keys())}
        )

        self.decision_history.append(result)
        logger.info(f"Value-based decision made: selected={selected.name if selected else 'None'}")
        return result

    def risk_based_decision(
        self,
        alternatives: List[Alternative],
        risk_assessments: Optional[Dict[str, List[RiskAssessment]]] = None,
        risk_tolerance: Optional[float] = None
    ) -> DecisionResult:
        """
        基于风险的决策

        考虑风险因素进行决策。

        Args:
            alternatives: 可选方案
            risk_assessments: 各方案的风险评估
            risk_tolerance: 风险容忍度

        Returns:
            DecisionResult: 决策结果
        """
        start_time = datetime.now()
        tolerance = risk_tolerance or self.risk_tolerance

        all_risks: List[RiskAssessment] = []
        scored_alternatives = []

        for alt in alternatives:
            risks = (risk_assessments or {}).get(alt.alternative_id, [])
            risk_score = self._calculate_risk_score(risks)

            if risk_score > tolerance and tolerance < 0.8:
                alt.is_feasible = False
                alt.score = 0.0
            else:
                benefit_score = sum(alt.values.values()) / max(len(alt.values), 1)
                alt.score = benefit_score * (1.0 - risk_score * 0.5)

            alt.risks = [r.model_dump() for r in risks]
            all_risks.extend(risks)
            scored_alternatives.append(alt)

        feasible = [a for a in scored_alternatives if a.is_feasible]
        if feasible:
            feasible.sort(key=lambda a: a.score, reverse=True)
            selected = feasible[0]
        else:
            scored_alternatives.sort(key=lambda a: a.score, reverse=True)
            selected = scored_alternatives[0] if scored_alternatives else None

        reasoning = self._generate_risk_reasoning(selected, tolerance)

        result = DecisionResult(
            decision_type=DecisionType.RISK_BASED,
            selected_alternative=selected,
            alternatives=scored_alternatives,
            reasoning=reasoning,
            confidence=selected.score if selected else 0.0,
            risks=all_risks,
            metadata={"risk_tolerance": tolerance}
        )

        self.decision_history.append(result)
        logger.info(f"Risk-based decision made: selected={selected.name if selected else 'None'}")
        return result

    def multi_criteria_decision(
        self,
        alternatives: List[Alternative],
        criteria: Optional[List[Criterion]] = None,
        method: str = "weighted_sum"
    ) -> DecisionResult:
        """
        多准则决策分析

        Args:
            alternatives: 可选方案
            criteria: 决策准则
            method: 决策方法 (weighted_sum, topsis, ahp)

        Returns:
            DecisionResult: 决策结果
        """
        start_time = datetime.now()
        mcdm_criteria = criteria or list(self.criteria.values())

        if not mcdm_criteria:
            return DecisionResult(
                decision_type=DecisionType.MULTI_CRITERIA,
                reasoning="没有定义决策准则",
                confidence=0.0
            )

        if method == "weighted_sum":
            scored = self._weighted_sum_method(alternatives, mcdm_criteria)
        elif method == "topsis":
            scored = self._topsis_method(alternatives, mcdm_criteria)
        else:
            scored = self._weighted_sum_method(alternatives, mcdm_criteria)

        scored.sort(key=lambda a: a.score, reverse=True)
        selected = scored[0] if scored else None

        reasoning = f"使用 {method} 方法进行多准则决策，"
        if selected:
            reasoning += f"选中 '{selected.name}' (得分: {selected.score:.3f})"
        else:
            reasoning += "未找到可行方案"

        result = DecisionResult(
            decision_type=DecisionType.MULTI_CRITERIA,
            selected_alternative=selected,
            alternatives=scored,
            reasoning=reasoning,
            confidence=selected.score if selected else 0.0,
            metadata={"method": method, "criteria_count": len(mcdm_criteria)}
        )

        self.decision_history.append(result)
        logger.info(f"Multi-criteria decision made: method={method}, selected={selected.name if selected else 'None'}")
        return result

    def probabilistic_decision(
        self,
        alternatives: List[Alternative],
        outcomes: Optional[Dict[str, Dict[str, float]]] = None
    ) -> DecisionResult:
        """
        概率决策

        基于期望效用理论进行决策。

        Args:
            alternatives: 可选方案
            outcomes: 各方案的结果概率分布

        Returns:
            DecisionResult: 决策结果
        """
        start_time = datetime.now()
        outcome_probs = outcomes or {}

        scored_alternatives = []
        for alt in alternatives:
            probs = outcome_probs.get(alt.alternative_id, alt.probabilities)
            ev = self._calculate_expected_value(alt, probs)
            alt.score = ev
            scored_alternatives.append(alt)

        scored_alternatives.sort(key=lambda a: a.score, reverse=True)
        selected = scored_alternatives[0] if scored_alternatives else None

        expected_value = selected.score if selected else 0.0

        reasoning = f"基于期望效用分析，"
        if selected:
            reasoning += f"'{selected.name}' 的期望效用最高: {expected_value:.3f}"
        else:
            reasoning += "未找到可行方案"

        result = DecisionResult(
            decision_type=DecisionType.PROBABILISTIC,
            selected_alternative=selected,
            alternatives=scored_alternatives,
            reasoning=reasoning,
            confidence=min(1.0, expected_value),
            expected_value=expected_value,
            metadata={"outcome_distributions": outcome_probs}
        )

        self.decision_history.append(result)
        logger.info(f"Probabilistic decision made: selected={selected.name if selected else 'None'}, EV={expected_value:.3f}")
        return result

    def build_decision_tree(
        self,
        root_name: str,
        decisions: List[Dict[str, Any]]
    ) -> DecisionTreeNode:
        """
        构建决策树

        Args:
            root_name: 根节点名称
            decisions: 决策结构

        Returns:
            DecisionTreeNode: 决策树根节点
        """
        root = DecisionTreeNode(name=root_name, node_type="decision")

        for decision in decisions:
            child = self._build_tree_node(decision)
            child.parent_id = root.node_id
            root.children.append(child)

        logger.debug(f"Built decision tree with {len(decisions)} top-level decisions")
        return root

    def evaluate_decision_tree(self, node: DecisionTreeNode) -> float:
        """
        评估决策树（回溯法计算期望价值）

        Args:
            node: 决策树节点

        Returns:
            float: 节点的期望价值
        """
        if node.is_terminal or not node.children:
            return node.value

        if node.node_type == "decision":
            return max(self.evaluate_decision_tree(child) for child in node.children)
        elif node.node_type == "chance":
            ev = 0.0
            for child in node.children:
                prob = child.probability or 0.5
                ev += prob * self.evaluate_decision_tree(child)
            return ev

        return node.value

    def get_optimal_path(self, tree: DecisionTreeNode) -> List[str]:
        """
        获取决策树的最优路径

        Args:
            tree: 决策树

        Returns:
            List[str]: 最优路径节点名称列表
        """
        path = [tree.name]

        if tree.is_terminal or not tree.children:
            return path

        if tree.node_type == "decision":
            best_child = max(
                tree.children,
                key=lambda c: self.evaluate_decision_tree(c)
            )
            path.extend(self.get_optimal_path(best_child))
        elif tree.node_type == "chance":
            best_child = max(
                tree.children,
                key=lambda c: (c.probability or 0) * self.evaluate_decision_tree(c)
            )
            path.extend(self.get_optimal_path(best_child))

        return path

    def evaluate_decision(
        self,
        decision_id: str,
        actual_outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估已做出的决策

        Args:
            decision_id: 决策ID
            actual_outcome: 实际结果

        Returns:
            Dict[str, Any]: 评估结果
        """
        decision = next(
            (d for d in self.decision_history if d.decision_id == decision_id),
            None
        )

        if not decision:
            return {"error": "Decision not found"}

        expected = decision.expected_value
        actual = actual_outcome.get("value", 0.0)
        deviation = actual - expected

        decision.status = DecisionStatus.EVALUATED

        return {
            "decision_id": decision_id,
            "expected_value": expected,
            "actual_value": actual,
            "deviation": deviation,
            "accuracy": 1.0 - abs(deviation) / max(abs(expected), 0.001),
            "selected_alternative": decision.selected_alternative.name if decision.selected_alternative else None,
            "timestamp": datetime.now().isoformat()
        }

    def get_decision_history(
        self,
        decision_type: Optional[DecisionType] = None,
        limit: int = 100
    ) -> List[DecisionResult]:
        """获取决策历史"""
        results = self.decision_history
        if decision_type:
            results = [d for d in results if d.decision_type == decision_type]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.decision_history)
        type_dist: Dict[str, int] = {}
        for d in self.decision_history:
            dt = d.decision_type.value
            type_dist[dt] = type_dist.get(dt, 0) + 1

        avg_confidence = sum(d.confidence for d in self.decision_history) / total if total > 0 else 0.0

        return {
            "total_decisions": total,
            "average_confidence": avg_confidence,
            "decision_type_distribution": type_dist,
            "criteria_count": len(self.criteria),
            "goals_count": len(self.goals),
            "risk_tolerance": self.risk_tolerance
        }

    def _evaluate_goal_alignment(
        self,
        alternative: Alternative,
        goals: List[Goal]
    ) -> float:
        """评估方案与目标的对齐度"""
        if not goals:
            return 0.5

        scores = []
        for goal in goals:
            goal_score = 0.0
            for outcome in alternative.expected_outcomes:
                if any(word in outcome.lower() for word in goal.description.lower().split()):
                    goal_score += 0.5

            goal_score += goal.priority * 0.5
            scores.append(min(1.0, goal_score))

        return sum(scores) / len(scores)

    def _evaluate_value_alignment(
        self,
        alternative: Alternative,
        value_weights: Dict[str, float],
        criteria_weights: Optional[Dict[str, float]]
    ) -> float:
        """评估方案与价值的对齐度"""
        if not value_weights and not alternative.values:
            return 0.5

        scores = []
        weights = criteria_weights or {}

        for key, val in alternative.values.items():
            weight = value_weights.get(key, weights.get(key, 1.0))
            scores.append(val * weight)

        for key, weight in value_weights.items():
            if key not in alternative.values:
                scores.append(0.0)

        return sum(scores) / max(len(scores), 1) if scores else 0.5

    def _calculate_risk_score(self, risks: List[RiskAssessment]) -> float:
        """计算风险评分"""
        if not risks:
            return 0.0

        total_risk = sum(r.probability * r.impact for r in risks)
        return min(1.0, total_risk / len(risks))

    def _calculate_expected_value(
        self,
        alternative: Alternative,
        probabilities: Dict[str, float]
    ) -> float:
        """计算期望价值"""
        if not probabilities:
            return sum(alternative.values.values()) / max(len(alternative.values), 1)

        ev = 0.0
        for outcome, prob in probabilities.items():
            value = alternative.values.get(outcome, 0.0)
            ev += prob * value

        return ev

    def _weighted_sum_method(
        self,
        alternatives: List[Alternative],
        criteria: List[Criterion]
    ) -> List[Alternative]:
        """加权和方法"""
        total_weight = sum(c.weight for c in criteria)
        if total_weight == 0:
            total_weight = 1.0

        for alt in alternatives:
            score = 0.0
            for crit in criteria:
                val = alt.values.get(crit.name, 0.0)
                normalized = (val - crit.scale_min) / (crit.scale_max - crit.scale_min + 0.001)
                if crit.direction == "minimize":
                    normalized = 1.0 - normalized
                score += normalized * (crit.weight / total_weight)
            alt.score = score

        return alternatives

    def _topsis_method(
        self,
        alternatives: List[Alternative],
        criteria: List[Criterion]
    ) -> List[Alternative]:
        """TOPSIS方法"""
        if not alternatives or not criteria:
            return alternatives

        crit_names = [c.name for c in criteria]
        weights = [c.weight for c in criteria]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        matrix = []
        for alt in alternatives:
            row = [alt.values.get(cn, 0.0) for cn in crit_names]
            matrix.append(row)

        if not matrix:
            return alternatives

        col_sums = [math.sqrt(sum(row[i] ** 2 for row in matrix)) for i in range(len(crit_names))]

        normalized = []
        for row in matrix:
            norm_row = [row[i] / (col_sums[i] + 0.001) for i in range(len(crit_names))]
            weighted = [norm_row[i] * weights[i] for i in range(len(crit_names))]
            normalized.append(weighted)

        ideal = [max(normalized[j][i] for j in range(len(normalized))) for i in range(len(crit_names))]
        nadir = [min(normalized[j][i] for j in range(len(normalized))) for i in range(len(crit_names))]

        for idx, alt in enumerate(alternatives):
            d_ideal = math.sqrt(sum((normalized[idx][i] - ideal[i]) ** 2 for i in range(len(crit_names))))
            d_nadir = math.sqrt(sum((normalized[idx][i] - nadir[i]) ** 2 for i in range(len(crit_names))))
            alt.score = d_nadir / (d_ideal + d_nadir + 0.001)

        return alternatives

    def _generate_goal_reasoning(self, selected: Optional[Alternative], goals: List[Goal]) -> str:
        """生成目标决策的理由"""
        if not selected:
            return "没有可行的方案"
        return f"'{selected.name}' 最能实现定义的 {len(goals)} 个目标"

    def _generate_value_reasoning(self, selected: Optional[Alternative], values: Dict[str, float]) -> str:
        """生成价值决策的理由"""
        if not selected:
            return "没有可行的方案"
        return f"'{selected.name}' 最符合价值体系"

    def _generate_risk_reasoning(self, selected: Optional[Alternative], tolerance: float) -> str:
        """生成风险决策的理由"""
        if not selected:
            return "没有可行的方案"
        return f"在风险容忍度 {tolerance:.2f} 下，'{selected.name}' 是最佳选择"

    def _build_tree_node(self, decision: Dict[str, Any]) -> DecisionTreeNode:
        """递归构建决策树节点"""
        node = DecisionTreeNode(
            name=decision.get("name", "Unknown"),
            node_type=decision.get("type", "decision"),
            probability=decision.get("probability"),
            value=decision.get("value", 0.0),
            is_terminal=decision.get("is_terminal", False)
        )

        for child_data in decision.get("children", []):
            child = self._build_tree_node(child_data)
            child.parent_id = node.node_id
            node.children.append(child)

        return node
