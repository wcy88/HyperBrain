"""
逻辑推理模块 (Reasoning Module)

实现多种推理模式，支持思维链和置信度评估。

推理类型：
- 演绎推理：从一般到特殊的推理
- 归纳推理：从特殊到一般的推理
- 类比推理：基于相似性的推理
- 溯因推理：从结果推断最佳解释
- 思维链推理：逐步思考过程
"""

import uuid
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.reasoning")


class ReasoningType(str, Enum):
    """推理类型枚举"""
    DEDUCTIVE = "deductive"      # 演绎推理
    INDUCTIVE = "inductive"      # 归纳推理
    ANALOGICAL = "analogical"    # 类比推理
    ABDUCTIVE = "abductive"      # 溯因推理
    CAUSAL = "causal"            # 因果推理
    CHAIN_OF_THOUGHT = "chain_of_thought"  # 思维链


class ConfidenceLevel(str, Enum):
    """置信度等级"""
    CERTAIN = "certain"          # 确定 (>0.95)
    HIGH = "high"                # 高 (0.8-0.95)
    MODERATE = "moderate"        # 中等 (0.6-0.8)
    LOW = "low"                  # 低 (0.4-0.6)
    UNCERTAIN = "uncertain"      # 不确定 (<0.4)


class ReasoningStep(BaseModel):
    """推理步骤模型"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int = Field(default=1, ge=1)
    description: str = Field(default="")
    premise: str = Field(default="")
    operation: str = Field(default="")
    conclusion: str = Field(default="")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning_type: ReasoningType = Field(default=ReasoningType.DEDUCTIVE)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ReasoningResult(BaseModel):
    """推理结果模型"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conclusion: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.UNCERTAIN)
    steps: List[ReasoningStep] = Field(default_factory=list)
    reasoning_type: ReasoningType = Field(default=ReasoningType.DEDUCTIVE)
    premises: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: float = Field(default=0.0)

    def get_confidence_level(self) -> ConfidenceLevel:
        """根据置信度获取等级"""
        c = self.confidence
        if c > 0.95:
            return ConfidenceLevel.CERTAIN
        elif c > 0.8:
            return ConfidenceLevel.HIGH
        elif c > 0.6:
            return ConfidenceLevel.MODERATE
        elif c > 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def model_post_init(self, __context: Any) -> None:
        self.confidence_level = self.get_confidence_level()


class Premise(BaseModel):
    """前提条件模型"""
    premise_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = Field(...)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(default="")
    is_fact: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    """推理规则模型"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="")
    condition: str = Field(...)
    conclusion: str = Field(...)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    domain: str = Field(default="general")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalogyMapping(BaseModel):
    """类比映射模型"""
    source_domain: str = Field(...)
    target_domain: str = Field(...)
    mappings: Dict[str, str] = Field(default_factory=dict)
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ReasoningEngine:
    """
    逻辑推理引擎

    支持多种推理模式，提供思维链和置信度评估功能。

    Attributes:
        rules: 推理规则库
        history: 推理历史记录
        max_chain_length: 最大思维链长度
        confidence_threshold: 置信度阈值
    """

    def __init__(
        self,
        max_chain_length: int = 10,
        confidence_threshold: float = 0.6,
        enable_logging: bool = True
    ):
        self.rules: Dict[str, Rule] = {}
        self.history: List[ReasoningResult] = []
        self.max_chain_length = max_chain_length
        self.confidence_threshold = confidence_threshold
        self.enable_logging = enable_logging
        self._analogies: List[AnalogyMapping] = []

        if enable_logging:
            logger.info("ReasoningEngine initialized")

    def add_rule(self, rule: Rule) -> None:
        """添加推理规则"""
        self.rules[rule.rule_id] = rule
        logger.debug(f"Added rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """移除推理规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def deductive_reasoning(
        self,
        premises: List[Premise],
        rules: Optional[List[Rule]] = None,
        question: Optional[str] = None
    ) -> ReasoningResult:
        """
        演绎推理：从一般到特殊

        基于前提和规则，通过逻辑推导得出结论。

        Args:
            premises: 前提条件列表
            rules: 推理规则列表（可选，默认使用引擎规则库）
            question: 待解答的问题

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []
        used_rules = rules or list(self.rules.values())
        current_confidence = 1.0

        for i, premise in enumerate(premises):
            step = ReasoningStep(
                step_number=i + 1,
                description=f"应用前提: {premise.statement}",
                premise=premise.statement,
                operation="assert_premise",
                conclusion=f"接受前提: {premise.statement}",
                confidence=premise.confidence,
                reasoning_type=ReasoningType.DEDUCTIVE
            )
            steps.append(step)
            current_confidence *= premise.confidence

        applied_rules = []
        step_num = len(steps) + 1

        for rule in used_rules:
            if self._check_rule_applicability(rule, premises):
                rule_confidence = rule.confidence * current_confidence
                step = ReasoningStep(
                    step_number=step_num,
                    description=f"应用规则: {rule.name}",
                    premise=rule.condition,
                    operation="apply_rule",
                    conclusion=rule.conclusion,
                    confidence=rule_confidence,
                    reasoning_type=ReasoningType.DEDUCTIVE,
                    metadata={"rule_id": rule.rule_id, "rule_name": rule.name}
                )
                steps.append(step)
                applied_rules.append(rule)
                current_confidence = rule_confidence
                step_num += 1

        if applied_rules:
            final_conclusion = applied_rules[-1].conclusion
        else:
            final_conclusion = "无法从给定前提演绎出结论"
            current_confidence = 0.3

        if question:
            final_conclusion = f"针对'{question}': {final_conclusion}"

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_conclusion,
            confidence=current_confidence,
            steps=steps,
            reasoning_type=ReasoningType.DEDUCTIVE,
            premises=[p.statement for p in premises],
            duration_ms=duration
        )

        self.history.append(result)
        return result

    def inductive_reasoning(
        self,
        observations: List[str],
        pattern_hints: Optional[List[str]] = None
    ) -> ReasoningResult:
        """
        归纳推理：从特殊到一般

        从观察实例中归纳出一般性规律。

        Args:
            observations: 观察实例列表
            pattern_hints: 模式提示（可选）

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []

        if not observations:
            return ReasoningResult(
                conclusion="没有观察数据可供归纳",
                confidence=0.0,
                reasoning_type=ReasoningType.INDUCTIVE
            )

        for i, obs in enumerate(observations):
            step = ReasoningStep(
                step_number=i + 1,
                description=f"观察实例 {i+1}",
                premise=obs,
                operation="observe",
                conclusion=f"记录观察: {obs}",
                confidence=0.9,
                reasoning_type=ReasoningType.INDUCTIVE
            )
            steps.append(step)

        common_patterns = self._extract_common_patterns(observations, pattern_hints)

        step_num = len(steps) + 1
        pattern_confidence = min(0.95, 0.5 + len(observations) * 0.1)

        for pattern in common_patterns:
            step = ReasoningStep(
                step_number=step_num,
                description="识别共同模式",
                premise=f"从{len(observations)}个观察中",
                operation="generalize",
                conclusion=f"归纳模式: {pattern}",
                confidence=pattern_confidence,
                reasoning_type=ReasoningType.INDUCTIVE
            )
            steps.append(step)
            step_num += 1

        if common_patterns:
            final_conclusion = f"归纳结论: {common_patterns[0]}"
            if len(common_patterns) > 1:
                final_conclusion += f" (及其他{len(common_patterns)-1}个模式)"
        else:
            final_conclusion = "未能从观察中归纳出明确模式"
            pattern_confidence = 0.2

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_conclusion,
            confidence=pattern_confidence,
            steps=steps,
            reasoning_type=ReasoningType.INDUCTIVE,
            premises=observations,
            duration_ms=duration
        )

        self.history.append(result)
        return result

    def analogical_reasoning(
        self,
        source_domain: str,
        target_domain: str,
        source_features: Dict[str, Any],
        target_features: Dict[str, Any]
    ) -> ReasoningResult:
        """
        类比推理：基于相似性的推理

        通过识别源域和目标域之间的相似性进行推理。

        Args:
            source_domain: 源域名称
            target_domain: 目标域名称
            source_features: 源域特征
            target_features: 目标域特征

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []

        mapping, similarity = self._create_analogy_mapping(
            source_domain, target_domain,
            source_features, target_features
        )

        step1 = ReasoningStep(
            step_number=1,
            description="识别源域特征",
            premise=str(source_features),
            operation="identify_source",
            conclusion=f"源域 '{source_domain}' 有 {len(source_features)} 个特征",
            confidence=0.95,
            reasoning_type=ReasoningType.ANALOGICAL
        )
        steps.append(step1)

        step2 = ReasoningStep(
            step_number=2,
            description="识别目标域特征",
            premise=str(target_features),
            operation="identify_target",
            conclusion=f"目标域 '{target_domain}' 有 {len(target_features)} 个特征",
            confidence=0.95,
            reasoning_type=ReasoningType.ANALOGICAL
        )
        steps.append(step2)

        step3 = ReasoningStep(
            step_number=3,
            description="建立类比映射",
            premise=f"源域: {source_domain}, 目标域: {target_domain}",
            operation="map_analogy",
            conclusion=f"建立 {len(mapping.mappings)} 个映射，相似度: {similarity:.2f}",
            confidence=similarity,
            reasoning_type=ReasoningType.ANALOGICAL,
            metadata={"mappings": mapping.mappings}
        )
        steps.append(step3)

        inferred_conclusions = self._infer_from_analogy(mapping, source_features)

        step_num = 4
        for conclusion in inferred_conclusions:
            step = ReasoningStep(
                step_number=step_num,
                description="类比推断",
                premise=f"基于{source_domain}到{target_domain}的映射",
                operation="analogical_inference",
                conclusion=conclusion,
                confidence=similarity * 0.85,
                reasoning_type=ReasoningType.ANALOGICAL
            )
            steps.append(step)
            step_num += 1

        if inferred_conclusions:
            final_conclusion = inferred_conclusions[0]
        else:
            final_conclusion = f"通过类比 '{source_domain}' -> '{target_domain}' 未能得出明确结论"

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_conclusion,
            confidence=similarity * 0.85,
            steps=steps,
            reasoning_type=ReasoningType.ANALOGICAL,
            premises=[f"{source_domain}: {source_features}", f"{target_domain}: {target_features}"],
            duration_ms=duration,
            metadata={"similarity": similarity, "mappings": mapping.mappings}
        )

        self._analogies.append(mapping)
        self.history.append(result)
        return result

    def abductive_reasoning(
        self,
        observation: str,
        possible_explanations: List[str],
        explanation_priorities: Optional[List[float]] = None
    ) -> ReasoningResult:
        """
        溯因推理：从结果推断最佳解释

        给定观察结果，推断最可能的解释。

        Args:
            observation: 观察到的结果
            possible_explanations: 可能的解释列表
            explanation_priorities: 解释的先验优先级

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []

        step1 = ReasoningStep(
            step_number=1,
            description="观察结果",
            premise=observation,
            operation="observe",
            conclusion=f"观察到: {observation}",
            confidence=0.95,
            reasoning_type=ReasoningType.ABDUCTIVE
        )
        steps.append(step1)

        if not possible_explanations:
            return ReasoningResult(
                conclusion="没有可能的解释",
                confidence=0.0,
                steps=steps,
                reasoning_type=ReasoningType.ABDUCTIVE,
                premises=[observation]
            )

        priorities = explanation_priorities or [1.0 / len(possible_explanations)] * len(possible_explanations)

        scored_explanations = []
        for i, (exp, priority) in enumerate(zip(possible_explanations, priorities)):
            score = self._evaluate_explanation(observation, exp, priority)
            scored_explanations.append((exp, score))

            step = ReasoningStep(
                step_number=i + 2,
                description=f"评估解释 {i+1}",
                premise=exp,
                operation="evaluate_explanation",
                conclusion=f"解释 '{exp}' 的评分为 {score:.2f}",
                confidence=score,
                reasoning_type=ReasoningType.ABDUCTIVE
            )
            steps.append(step)

        scored_explanations.sort(key=lambda x: x[1], reverse=True)
        best_explanation, best_score = scored_explanations[0]

        final_conclusion = f"最佳解释: {best_explanation} (评分: {best_score:.2f})"

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_conclusion,
            confidence=best_score,
            steps=steps,
            reasoning_type=ReasoningType.ABDUCTIVE,
            premises=[observation],
            duration_ms=duration,
            metadata={
                "all_explanations": scored_explanations,
                "best_explanation": best_explanation
            }
        )

        self.history.append(result)
        return result

    def chain_of_thought(
        self,
        problem: str,
        sub_problems: Optional[List[str]] = None,
        max_steps: Optional[int] = None,
        reasoning_callback: Optional[Callable[[ReasoningStep], None]] = None
    ) -> ReasoningResult:
        """
        思维链推理：逐步思考过程

        将复杂问题分解为多个步骤，逐步推理得出结论。

        Args:
            problem: 主问题
            sub_problems: 子问题列表（可选）
            max_steps: 最大推理步数
            reasoning_callback: 每步推理的回调函数

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []
        max_steps = max_steps or self.max_chain_length

        if sub_problems is None:
            sub_problems = self._decompose_problem(problem)

        step1 = ReasoningStep(
            step_number=1,
            description="理解问题",
            premise=problem,
            operation="comprehend",
            conclusion=f"问题分解为 {len(sub_problems)} 个子问题",
            confidence=0.9,
            reasoning_type=ReasoningType.CHAIN_OF_THOUGHT,
            metadata={"sub_problems": sub_problems}
        )
        steps.append(step1)
        if reasoning_callback:
            reasoning_callback(step1)

        current_conclusion = ""
        overall_confidence = 1.0

        for i, sub in enumerate(sub_problems[:max_steps - 1]):
            step_num = i + 2
            sub_confidence = max(0.5, 0.95 - i * 0.05)

            step = ReasoningStep(
                step_number=step_num,
                description=f"解决子问题 {i+1}",
                premise=sub,
                operation="reason",
                conclusion=f"子问题 '{sub}' 的分析结果",
                confidence=sub_confidence,
                reasoning_type=ReasoningType.CHAIN_OF_THOUGHT
            )
            steps.append(step)
            if reasoning_callback:
                reasoning_callback(step)

            current_conclusion = step.conclusion
            overall_confidence *= sub_confidence

        final_step = ReasoningStep(
            step_number=len(steps) + 1,
            description="综合结论",
            premise="所有子问题的分析结果",
            operation="synthesize",
            conclusion=f"综合结论: 基于{len(sub_problems)}步推理",
            confidence=overall_confidence,
            reasoning_type=ReasoningType.CHAIN_OF_THOUGHT
        )
        steps.append(final_step)
        if reasoning_callback:
            reasoning_callback(final_step)

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_step.conclusion,
            confidence=overall_confidence,
            steps=steps,
            reasoning_type=ReasoningType.CHAIN_OF_THOUGHT,
            premises=[problem],
            duration_ms=duration,
            metadata={"sub_problem_count": len(sub_problems)}
        )

        self.history.append(result)
        return result

    def causal_reasoning(
        self,
        events: List[str],
        causal_links: Optional[List[tuple]] = None
    ) -> ReasoningResult:
        """
        因果推理：分析事件之间的因果关系

        Args:
            events: 事件列表
            causal_links: 已知因果链接 [(原因, 结果, 强度)]

        Returns:
            ReasoningResult: 推理结果
        """
        start_time = datetime.now()
        steps: List[ReasoningStep] = []

        if len(events) < 2:
            return ReasoningResult(
                conclusion="事件数量不足，无法分析因果关系",
                confidence=0.0,
                reasoning_type=ReasoningType.CAUSAL,
                premises=events
            )

        for i, event in enumerate(events):
            step = ReasoningStep(
                step_number=i + 1,
                description=f"事件 {i+1}",
                premise=event,
                operation="identify_event",
                conclusion=f"事件 {i+1}: {event}",
                confidence=0.95,
                reasoning_type=ReasoningType.CAUSAL
            )
            steps.append(step)

        inferred_causes = []
        if causal_links:
            for cause, effect, strength in causal_links:
                if cause in events and effect in events:
                    step = ReasoningStep(
                        step_number=len(steps) + 1,
                        description="识别因果链接",
                        premise=f"{cause} -> {effect}",
                        operation="identify_causation",
                        conclusion=f"'{cause}' 导致 '{effect}' (强度: {strength})",
                        confidence=strength,
                        reasoning_type=ReasoningType.CAUSAL
                    )
                    steps.append(step)
                    inferred_causes.append((cause, effect, strength))
        else:
            for i in range(len(events) - 1):
                step = ReasoningStep(
                    step_number=len(steps) + 1,
                    description="推断因果关系",
                    premise=f"{events[i]} 先于 {events[i+1]}",
                    operation="infer_causation",
                    conclusion=f"'{events[i]}' 可能导致 '{events[i+1]}'",
                    confidence=0.6,
                    reasoning_type=ReasoningType.CAUSAL
                )
                steps.append(step)
                inferred_causes.append((events[i], events[i+1], 0.6))

        if inferred_causes:
            avg_strength = sum(s for _, _, s in inferred_causes) / len(inferred_causes)
            final_conclusion = f"识别了 {len(inferred_causes)} 个因果链接，平均强度: {avg_strength:.2f}"
        else:
            avg_strength = 0.3
            final_conclusion = "未能识别明确的因果关系"

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ReasoningResult(
            conclusion=final_conclusion,
            confidence=avg_strength,
            steps=steps,
            reasoning_type=ReasoningType.CAUSAL,
            premises=events,
            duration_ms=duration,
            metadata={"causal_links": inferred_causes}
        )

        self.history.append(result)
        return result

    def evaluate_confidence(
        self,
        result: ReasoningResult,
        additional_factors: Optional[Dict[str, float]] = None
    ) -> float:
        """
        评估推理结果的置信度

        Args:
            result: 推理结果
            additional_factors: 额外置信度影响因素

        Returns:
            float: 调整后的置信度
        """
        base_confidence = result.confidence

        step_consistency = self._evaluate_step_consistency(result.steps)

        premise_strength = 1.0
        if result.premises:
            premise_strength = min(1.0, 0.5 + len(result.premises) * 0.1)

        adjusted = base_confidence * step_consistency * premise_strength

        if additional_factors:
            for factor_name, factor_value in additional_factors.items():
                adjusted *= max(0.0, min(1.0, factor_value))

        adjusted = max(0.0, min(1.0, adjusted))
        return adjusted

    def get_reasoning_history(
        self,
        reasoning_type: Optional[ReasoningType] = None,
        limit: int = 100
    ) -> List[ReasoningResult]:
        """获取推理历史"""
        results = self.history
        if reasoning_type:
            results = [r for r in results if r.reasoning_type == reasoning_type]
        return results[-limit:]

    def clear_history(self) -> None:
        """清空推理历史"""
        self.history.clear()
        logger.debug("Reasoning history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.history:
            return {
                "total_reasoning_count": 0,
                "average_confidence": 0.0,
                "reasoning_type_distribution": {},
                "rule_count": len(self.rules)
            }

        type_dist: Dict[str, int] = {}
        for r in self.history:
            rt = r.reasoning_type.value
            type_dist[rt] = type_dist.get(rt, 0) + 1

        return {
            "total_reasoning_count": len(self.history),
            "average_confidence": sum(r.confidence for r in self.history) / len(self.history),
            "reasoning_type_distribution": type_dist,
            "rule_count": len(self.rules),
            "analogy_count": len(self._analogies)
        }

    def _check_rule_applicability(self, rule: Rule, premises: List[Premise]) -> bool:
        """检查规则是否适用于给定前提"""
        premise_text = " ".join(p.statement.lower() for p in premises)
        condition_keywords = set(rule.condition.lower().split())
        return bool(condition_keywords & set(premise_text.split()))

    def _extract_common_patterns(
        self,
        observations: List[str],
        hints: Optional[List[str]]
    ) -> List[str]:
        """从观察中提取共同模式"""
        patterns = []

        if hints:
            patterns.extend(hints)

        common_words = set()
        for obs in observations:
            words = set(obs.lower().split())
            if not common_words:
                common_words = words
            else:
                common_words &= words

        if common_words:
            patterns.append(f"共同关键词: {', '.join(common_words)}")

        if len(observations) >= 3:
            patterns.append(f"基于{len(observations)}个实例的统计规律")

        return patterns if patterns else ["未发现明显模式"]

    def _create_analogy_mapping(
        self,
        source_domain: str,
        target_domain: str,
        source_features: Dict[str, Any],
        target_features: Dict[str, Any]
    ) -> tuple[AnalogyMapping, float]:
        """创建类比映射"""
        mappings: Dict[str, str] = {}

        for s_key, s_val in source_features.items():
            for t_key, t_val in target_features.items():
                if str(s_val).lower() == str(t_val).lower():
                    mappings[s_key] = t_key

        total_features = max(len(source_features), len(target_features))
        similarity = len(mappings) / total_features if total_features > 0 else 0.0

        mapping = AnalogyMapping(
            source_domain=source_domain,
            target_domain=target_domain,
            mappings=mappings,
            similarity_score=similarity,
            confidence=similarity
        )

        return mapping, similarity

    def _infer_from_analogy(
        self,
        mapping: AnalogyMapping,
        source_features: Dict[str, Any]
    ) -> List[str]:
        """从类比中推断结论"""
        conclusions = []

        for s_key, t_key in mapping.mappings.items():
            if s_key in source_features:
                conclusions.append(
                    f"因为 '{s_key}' 对应 '{t_key}'，"
                    f"所以源域中的 '{source_features[s_key]}' 可能对应目标域中的相似特征"
                )

        if not conclusions:
            conclusions.append(
                f"基于 {mapping.source_domain} 和 {mapping.target_domain} 的类比，"
                f"推断两域存在结构相似性"
            )

        return conclusions

    def _evaluate_explanation(
        self,
        observation: str,
        explanation: str,
        priority: float
    ) -> float:
        """评估解释的合理性"""
        obs_words = set(observation.lower().split())
        exp_words = set(explanation.lower().split())

        overlap = len(obs_words & exp_words)
        total = len(obs_words | exp_words)
        similarity = overlap / total if total > 0 else 0.0

        score = (similarity * 0.6 + priority * 0.4)
        return min(1.0, score)

    def _decompose_problem(self, problem: str) -> List[str]:
        """将问题分解为子问题"""
        parts = problem.replace("?", ".").replace("!", ".").split(".")
        sub_problems = [p.strip() for p in parts if p.strip()]

        if len(sub_problems) <= 1:
            words = problem.split()
            mid = len(words) // 2
            if mid > 0:
                sub_problems = [
                    " ".join(words[:mid]),
                    " ".join(words[mid:])
                ]
            else:
                sub_problems = [problem]

        return sub_problems

    def _evaluate_step_consistency(self, steps: List[ReasoningStep]) -> float:
        """评估推理步骤的一致性"""
        if not steps:
            return 1.0

        confidences = [s.confidence for s in steps]
        if not confidences:
            return 1.0

        avg_confidence = sum(confidences) / len(confidences)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        consistency = 1.0 - min(1.0, variance * 4)

        return consistency
