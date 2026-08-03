"""
成人学习引擎 (Adult Learning Engine)

模拟成人期的学习方式：
- 结构化学习：系统化学习知识体系
- 逻辑学习：基于逻辑推理的学习
- 批判性学习：质疑和验证知识
- 迁移学习：将知识应用到新领域
- 元学习：学习如何学习

特征：深度理解、批判思维、知识迁移
"""

import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("learning.adult")


class KnowledgeDomain(str, Enum):
    """知识领域"""
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ARTS = "arts"
    HUMANITIES = "humanities"
    MATHEMATICS = "mathematics"
    SOCIAL_SCIENCE = "social_science"
    GENERAL = "general"


class LearningStrategy(str, Enum):
    """学习策略"""
    DEEP_READING = "deep_reading"
    SPACED_REPETITION = "spaced_repetition"
    ACTIVE_RECALL = "active_recall"
    ELABORATION = "elaboration"
    INTERLEAVING = "interleaving"
    DUAL_CODING = "dual_coding"


class StructuredKnowledge(BaseModel):
    """结构化知识"""
    knowledge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = Field(...)
    domain: KnowledgeDomain = Field(default=KnowledgeDomain.GENERAL)
    content: str = Field(default="")
    key_points: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0)
    review_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_reviewed: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", "mastery_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LogicalInference(BaseModel):
    """逻辑推理"""
    inference_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    premises: List[str] = Field(default_factory=list)
    conclusion: str = Field(default="")
    reasoning_type: str = Field(default="deductive")  # deductive, inductive, abductive
    validity: float = Field(default=0.0, ge=0.0, le=1.0)
    soundness: float = Field(default=0.0, ge=0.0, le=1.0)
    assumptions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("validity", "soundness")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CriticalEvaluation(BaseModel):
    """批判性评估"""
    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str = Field(...)
    evidence_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    logical_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    source_reliability: float = Field(default=0.0, ge=0.0, le=1.0)
    bias_detected: List[str] = Field(default_factory=list)
    counter_arguments: List[str] = Field(default_factory=list)
    overall_credibility: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict: str = Field(default="pending")  # accepted, rejected, pending, needs_verification
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("evidence_quality", "logical_consistency", "source_reliability", "overall_credibility")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeTransfer(BaseModel):
    """知识迁移记录"""
    transfer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_domain: str = Field(...)
    target_domain: str = Field(...)
    transferred_knowledge: str = Field(default="")
    transfer_score: float = Field(default=0.0, ge=0.0, le=1.0)
    success: bool = Field(default=False)
    adaptation_required: bool = Field(default=False)
    adaptation_details: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("transfer_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class MetaLearningInsight(BaseModel):
    """元学习洞察"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    strategy_tested: str = Field(...)
    effectiveness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    context: str = Field(default="")
    conditions: List[str] = Field(default_factory=list)
    recommendation: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("effectiveness_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class AdultLearningConfig:
    """成人学习配置"""
    min_evidence_quality: float = 0.6
    critical_threshold: float = 0.5
    transfer_threshold: float = 0.4
    meta_learning_rate: float = 0.1
    review_interval_base: float = 86400.0  # 1天（秒）
    max_knowledge_items: int = 5000
    deep_processing_required: bool = True
    skepticism_level: float = 0.3


class AdultLearningEngine:
    """
    成人学习引擎

    模拟成人期（12岁以上）的学习方式，特点：
    1. 深度理解：追求系统性知识
    2. 批判思维：质疑和验证
    3. 知识迁移：跨领域应用
    4. 元认知：学习如何学习
    5. 逻辑推理：基于逻辑的学习

    Attributes:
        config: 学习配置
        knowledge_base: 结构化知识库
        inferences: 逻辑推理记录
        evaluations: 批判性评估记录
        transfers: 知识迁移记录
        meta_insights: 元学习洞察
    """

    def __init__(self, config: Optional[AdultLearningConfig] = None):
        self.config = config or AdultLearningConfig()

        # 结构化知识
        self.knowledge_base: Dict[str, StructuredKnowledge] = {}
        self.domain_index: Dict[KnowledgeDomain, List[str]] = defaultdict(list)
        self.topic_index: Dict[str, str] = {}  # topic -> knowledge_id

        # 逻辑推理
        self.inferences: List[LogicalInference] = []
        self.inference_rules: Dict[str, List[str]] = defaultdict(list)

        # 批判性评估
        self.evaluations: List[CriticalEvaluation] = {}
        self.evaluation_index: Dict[str, str] = {}  # subject -> evaluation_id

        # 知识迁移
        self.transfers: List[KnowledgeTransfer] = []
        self.transfer_success_rate: Dict[str, float] = {}

        # 元学习
        self.meta_insights: List[MetaLearningInsight] = []
        self.strategy_effectiveness: Dict[str, List[float]] = defaultdict(list)
        self.learning_preferences: Dict[str, float] = {}

        # 学习统计
        self.total_knowledge_acquired: int = 0
        self.total_inferences_made: int = 0
        self.total_evaluations: int = 0
        self.total_transfers: int = 0
        self.total_meta_insights: int = 0

        logger.info("AdultLearningEngine initialized")

    # ========== 结构化学习 ==========

    def learn_structured(self, topic: str, content: str,
                         domain: KnowledgeDomain = KnowledgeDomain.GENERAL,
                         key_points: Optional[List[str]] = None,
                         prerequisites: Optional[List[str]] = None) -> StructuredKnowledge:
        """
        系统化学习知识

        以结构化的方式学习新知识，建立知识体系。

        Args:
            topic: 主题
            content: 内容
            domain: 知识领域
            key_points: 关键要点
            prerequisites: 前置知识

        Returns:
            StructuredKnowledge: 结构化知识
        """
        self.total_knowledge_acquired += 1

        # 检查是否已存在
        if topic in self.topic_index:
            knowledge_id = self.topic_index[topic]
            knowledge = self.knowledge_base[knowledge_id]
            # 更新知识
            knowledge.content = content
            if key_points:
                knowledge.key_points = list(set(knowledge.key_points + key_points))
            knowledge.review_count += 1
            knowledge.last_reviewed = datetime.now()
            knowledge.mastery_level = min(1.0, knowledge.mastery_level + 0.1)
            logger.debug(f"Reviewed knowledge: {topic}, mastery={knowledge.mastery_level:.2f}")
            return knowledge

        # 检查前置知识
        missing_prerequisites = []
        if prerequisites:
            for prereq in prerequisites:
                if prereq not in self.topic_index:
                    missing_prerequisites.append(prereq)

        # 创建新知识
        knowledge = StructuredKnowledge(
            topic=topic,
            domain=domain,
            content=content,
            key_points=key_points or [],
            prerequisites=prerequisites or [],
            confidence=0.7 if not missing_prerequisites else 0.4,
            mastery_level=0.2,
            metadata={"missing_prerequisites": missing_prerequisites}
        )

        self.knowledge_base[knowledge.knowledge_id] = knowledge
        self.topic_index[topic] = knowledge.knowledge_id
        self.domain_index[domain].append(knowledge.knowledge_id)

        # 建立关联
        self._link_related_topics(knowledge)

        logger.info(f"Learned structured knowledge: {topic} in {domain.value}")
        return knowledge

    def _link_related_topics(self, knowledge: StructuredKnowledge) -> None:
        """建立相关主题链接"""
        for other in self.knowledge_base.values():
            if other.knowledge_id == knowledge.knowledge_id:
                continue

            # 检查内容相似性
            similarity = self._content_similarity(knowledge.content, other.content)
            if similarity > 0.3:
                knowledge.related_topics.append(other.topic)
                other.related_topics.append(knowledge.topic)

    def _content_similarity(self, a: str, b: str) -> float:
        """计算内容相似度"""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def get_knowledge(self, topic: str) -> Optional[StructuredKnowledge]:
        """获取知识"""
        if topic in self.topic_index:
            return self.knowledge_base[self.topic_index[topic]]
        return None

    def get_knowledge_by_domain(self, domain: KnowledgeDomain) -> List[StructuredKnowledge]:
        """按领域获取知识"""
        knowledge_ids = self.domain_index.get(domain, [])
        return [self.knowledge_base[kid] for kid in knowledge_ids if kid in self.knowledge_base]

    def get_learning_path(self, target_topic: str) -> List[str]:
        """
        获取学习路径

        Args:
            target_topic: 目标主题

        Returns:
            List[str]: 建议的学习顺序
        """
        knowledge = self.get_knowledge(target_topic)
        if not knowledge:
            return [target_topic]

        path = []
        visited = set()

        def add_prerequisites(topic_name: str) -> None:
            if topic_name in visited:
                return
            visited.add(topic_name)

            k = self.get_knowledge(topic_name)
            if k:
                for prereq in k.prerequisites:
                    add_prerequisites(prereq)
            path.append(topic_name)

        add_prerequisites(target_topic)
        return path

    def review_knowledge(self, topic: str) -> Optional[StructuredKnowledge]:
        """
        复习知识

        Args:
            topic: 主题

        Returns:
            Optional[StructuredKnowledge]: 更新后的知识
        """
        knowledge = self.get_knowledge(topic)
        if knowledge:
            knowledge.review_count += 1
            knowledge.last_reviewed = datetime.now()
            # 间隔重复公式
            mastery_boost = 0.1 * (1.5 ** (-knowledge.review_count * 0.1))
            knowledge.mastery_level = min(1.0, knowledge.mastery_level + mastery_boost)
            logger.debug(f"Reviewed: {topic}, mastery={knowledge.mastery_level:.2f}")
        return knowledge

    # ========== 逻辑学习 ==========

    def logical_learn(self, premises: List[str], conclusion: str,
                      reasoning_type: str = "deductive") -> LogicalInference:
        """
        基于逻辑推理学习

        Args:
            premises: 前提列表
            conclusion: 结论
            reasoning_type: 推理类型

        Returns:
            LogicalInference: 推理结果
        """
        self.total_inferences_made += 1

        # 评估推理有效性
        validity = self._assess_validity(premises, conclusion, reasoning_type)
        soundness = self._assess_soundness(premises, validity)

        inference = LogicalInference(
            premises=premises,
            conclusion=conclusion,
            reasoning_type=reasoning_type,
            validity=validity,
            soundness=soundness,
            assumptions=self._extract_assumptions(premises)
        )

        self.inferences.append(inference)

        # 如果推理有效，学习结论
        if soundness > self.config.critical_threshold:
            self.learn_structured(
                topic=f"inference_{inference.inference_id[:8]}",
                content=f"结论: {conclusion}",
                key_points=premises + [conclusion]
            )

        logger.debug(f"Logical inference: validity={validity:.2f}, soundness={soundness:.2f}")
        return inference

    def _assess_validity(self, premises: List[str], conclusion: str,
                         reasoning_type: str) -> float:
        """评估推理有效性"""
        if reasoning_type == "deductive":
            # 演绎推理：结论必须必然从前提得出
            # 简化评估：检查关键词重叠
            premise_words = set()
            for p in premises:
                premise_words.update(p.lower().split())
            conclusion_words = set(conclusion.lower().split())
            overlap = len(conclusion_words & premise_words) / max(len(conclusion_words), 1)
            return min(1.0, overlap * 1.5)

        elif reasoning_type == "inductive":
            # 归纳推理：基于概率
            return 0.7  # 归纳推理默认较高但不完美

        elif reasoning_type == "abductive":
            # 溯因推理：最佳解释
            return 0.6

        return 0.5

    def _assess_soundness(self, premises: List[str], validity: float) -> float:
        """评估推理可靠性"""
        # 检查前提的可信度
        premise_confidences = []
        for premise in premises:
            # 查找知识库中的前提
            found = False
            for knowledge in self.knowledge_base.values():
                if premise.lower() in knowledge.content.lower():
                    premise_confidences.append(knowledge.confidence)
                    found = True
                    break
            if not found:
                premise_confidences.append(0.5)  # 未知前提

        avg_premise_confidence = sum(premise_confidences) / max(len(premise_confidences), 1)
        return validity * avg_premise_confidence

    def _extract_assumptions(self, premises: List[str]) -> List[str]:
        """提取隐含假设"""
        assumptions = []
        for premise in premises:
            # 简单启发式：包含"所有"、"总是"等词的陈述可能有隐含假设
            if any(word in premise.lower() for word in ["所有", "总是", "任何", "every", "all", "always"]):
                assumptions.append(f"隐含假设: {premise} 没有例外")
        return assumptions

    def get_inference_stats(self) -> Dict[str, Any]:
        """获取推理统计"""
        if not self.inferences:
            return {"total": 0, "avg_validity": 0.0}

        by_type: Dict[str, List[LogicalInference]] = defaultdict(list)
        for inf in self.inferences:
            by_type[inf.reasoning_type].append(inf)

        return {
            "total": len(self.inferences),
            "avg_validity": sum(i.validity for i in self.inferences) / len(self.inferences),
            "avg_soundness": sum(i.soundness for i in self.inferences) / len(self.inferences),
            "by_type": {t: len(infs) for t, infs in by_type.items()}
        }

    # ========== 批判性学习 ==========

    def critically_evaluate(self, subject: str, evidence: List[str],
                            source: str = "", propositions: Optional[List[str]] = None) -> CriticalEvaluation:
        """
        批判性评估知识

        Args:
            subject: 评估对象
            evidence: 证据列表
            source: 来源
            propositions: 主张列表

        Returns:
            CriticalEvaluation: 评估结果
        """
        self.total_evaluations += 1

        # 评估证据质量
        evidence_quality = self._evaluate_evidence(evidence, source)

        # 评估逻辑一致性
        logical_consistency = self._evaluate_consistency(propositions or [])

        # 评估来源可靠性
        source_reliability = self._assess_source_reliability(source)

        # 检测偏见
        biases = self._detect_biases(subject, evidence, propositions or [])

        # 生成反论证
        counter_arguments = self._generate_counter_arguments(subject, propositions or [])

        # 计算总体可信度
        overall = (evidence_quality + logical_consistency + source_reliability) / 3
        overall = overall * (1 - len(biases) * 0.1)  # 偏见降低可信度

        # 做出判断
        if overall > 0.7:
            verdict = "accepted"
        elif overall < 0.3:
            verdict = "rejected"
        elif evidence_quality < 0.5:
            verdict = "needs_verification"
        else:
            verdict = "pending"

        evaluation = CriticalEvaluation(
            subject=subject,
            evidence_quality=evidence_quality,
            logical_consistency=logical_consistency,
            source_reliability=source_reliability,
            bias_detected=biases,
            counter_arguments=counter_arguments,
            overall_credibility=overall,
            verdict=verdict,
            metadata={"source": source, "evidence_count": len(evidence)}
        )

        self.evaluations[evaluation.evaluation_id] = evaluation
        self.evaluation_index[subject] = evaluation.evaluation_id

        logger.info(f"Critical evaluation of {subject}: {verdict} (credibility={overall:.2f})")
        return evaluation

    def _evaluate_evidence(self, evidence: List[str], source: str) -> float:
        """评估证据质量"""
        if not evidence:
            return 0.0

        base_score = 0.5
        # 证据数量加成
        quantity_bonus = min(0.2, len(evidence) * 0.05)
        # 来源加成
        source_bonus = 0.1 if source else 0.0

        return min(1.0, base_score + quantity_bonus + source_bonus)

    def _evaluate_consistency(self, propositions: List[str]) -> float:
        """评估逻辑一致性"""
        if len(propositions) < 2:
            return 0.7  # 单个命题默认一致

        # 简单一致性检查：检查矛盾词
        contradictions = 0
        for i, p1 in enumerate(propositions):
            for p2 in propositions[i+1:]:
                if self._are_contradictory(p1, p2):
                    contradictions += 1

        total_pairs = len(propositions) * (len(propositions) - 1) / 2
        if total_pairs == 0:
            return 1.0

        consistency = 1.0 - (contradictions / total_pairs)
        return consistency

    def _are_contradictory(self, p1: str, p2: str) -> bool:
        """检查两个命题是否矛盾"""
        # 简单启发式
        negation_words = ["不", "没有", "not", "no", "never"]
        p1_has_neg = any(w in p1.lower() for w in negation_words)
        p2_has_neg = any(w in p2.lower() for w in negation_words)

        # 如果内容相似但否定状态不同，可能是矛盾的
        if p1_has_neg != p2_has_neg:
            words1 = set(p1.lower().split()) - set(negation_words)
            words2 = set(p2.lower().split()) - set(negation_words)
            overlap = len(words1 & words2) / max(len(words1 | words2), 1)
            if overlap > 0.5:
                return True

        return False

    def _assess_source_reliability(self, source: str) -> float:
        """评估来源可靠性"""
        if not source:
            return 0.3

        # 简单启发式
        reliable_indicators = ["研究", "论文", "journal", "research", "study"]
        unreliable_indicators = ["传闻", "据说", "rumor", "allegedly"]

        score = 0.5
        for indicator in reliable_indicators:
            if indicator in source.lower():
                score += 0.1
        for indicator in unreliable_indicators:
            if indicator in source.lower():
                score -= 0.2

        return max(0.0, min(1.0, score))

    def _detect_biases(self, subject: str, evidence: List[str],
                       propositions: List[str]) -> List[str]:
        """检测偏见"""
        biases = []

        # 确认偏误：只收集支持性证据
        if evidence and all(self._is_supporting(e, subject) for e in evidence):
            biases.append("confirmation_bias")

        # 来源单一
        if len(set(evidence)) == 1 and len(evidence) > 1:
            biases.append("single_source_bias")

        # 情绪化语言
        emotional_words = ["绝对", "永远", "最佳", "最坏", "always", "never", "best", "worst"]
        for prop in propositions:
            if any(w in prop.lower() for w in emotional_words):
                biases.append("emotional_bias")
                break

        return biases

    def _is_supporting(self, evidence: str, subject: str) -> bool:
        """检查证据是否支持主题"""
        # 简化：检查是否包含否定词
        negations = ["不", "没有", "not", "no"]
        return not any(n in evidence.lower() for n in negations)

    def _generate_counter_arguments(self, subject: str,
                                    propositions: List[str]) -> List[str]:
        """生成反论证"""
        counter_args = []

        for prop in propositions:
            # 简单反论证生成
            if "所有" in prop or "every" in prop.lower():
                counter_args.append(f"反例可能存在: {prop}")
            if "总是" in prop or "always" in prop.lower():
                counter_args.append(f"例外情况: {prop}")

        if not counter_args:
            counter_args.append(f"需要更多证据支持关于 {subject} 的主张")

        return counter_args

    def get_evaluation(self, subject: str) -> Optional[CriticalEvaluation]:
        """获取评估结果"""
        if subject in self.evaluation_index:
            return self.evaluations.get(self.evaluation_index[subject])
        return None

    def get_critical_stats(self) -> Dict[str, Any]:
        """获取批判性学习统计"""
        if not self.evaluations:
            return {"total": 0, "acceptance_rate": 0.0}

        evaluations_list = list(self.evaluations.values())
        accepted = sum(1 for e in evaluations_list if e.verdict == "accepted")
        rejected = sum(1 for e in evaluations_list if e.verdict == "rejected")

        return {
            "total": len(evaluations_list),
            "accepted": accepted,
            "rejected": rejected,
            "pending": sum(1 for e in evaluations_list if e.verdict == "pending"),
            "acceptance_rate": accepted / len(evaluations_list),
            "avg_credibility": sum(e.overall_credibility for e in evaluations_list) / len(evaluations_list),
            "avg_bias_detected": sum(len(e.bias_detected) for e in evaluations_list) / len(evaluations_list)
        }

    # ========== 迁移学习 ==========

    def transfer_knowledge(self, source_domain: str, target_domain: str,
                           knowledge_description: str,
                           adaptation_strategy: str = "analogy") -> KnowledgeTransfer:
        """
        将知识迁移到新领域

        Args:
            source_domain: 源领域
            target_domain: 目标领域
            knowledge_description: 知识描述
            adaptation_strategy: 适应策略

        Returns:
            KnowledgeTransfer: 迁移结果
        """
        self.total_transfers += 1

        # 评估领域相似度
        domain_similarity = self._calculate_domain_similarity(source_domain, target_domain)

        # 评估迁移可行性
        transfer_score = domain_similarity
        adaptation_required = domain_similarity < 0.7

        # 查找相关知识
        relevant_knowledge = self._find_relevant_knowledge(source_domain, knowledge_description)

        # 计算迁移分数
        if relevant_knowledge:
            knowledge_confidence = sum(k.confidence for k in relevant_knowledge) / len(relevant_knowledge)
            transfer_score = (transfer_score + knowledge_confidence) / 2

        success = transfer_score > self.config.transfer_threshold

        transfer = KnowledgeTransfer(
            source_domain=source_domain,
            target_domain=target_domain,
            transferred_knowledge=knowledge_description,
            transfer_score=transfer_score,
            success=success,
            adaptation_required=adaptation_required,
            adaptation_details=f"Using {adaptation_strategy} strategy" if adaptation_required else "Direct transfer",
            metadata={"relevant_knowledge_count": len(relevant_knowledge)}
        )

        self.transfers.append(transfer)

        # 记录成功率
        key = f"{source_domain}->{target_domain}"
        self.transfer_success_rate[key] = transfer_score

        logger.info(f"Knowledge transfer: {source_domain} -> {target_domain}, score={transfer_score:.2f}")
        return transfer

    def _calculate_domain_similarity(self, domain1: str, domain2: str) -> float:
        """计算领域相似度"""
        if domain1 == domain2:
            return 1.0

        # 基于知识内容的相似度
        domain1_knowledge = [k for k in self.knowledge_base.values()
                            if k.domain.value == domain1 or k.topic == domain1]
        domain2_knowledge = [k for k in self.knowledge_base.values()
                            if k.domain.value == domain2 or k.topic == domain2]

        if not domain1_knowledge or not domain2_knowledge:
            return 0.3  # 默认低相似度

        # 计算内容相似度
        all_content1 = " ".join(k.content for k in domain1_knowledge)
        all_content2 = " ".join(k.content for k in domain2_knowledge)
        return self._content_similarity(all_content1, all_content2)

    def _find_relevant_knowledge(self, domain: str,
                                 description: str) -> List[StructuredKnowledge]:
        """查找相关知识"""
        relevant = []
        desc_words = set(description.lower().split())

        for knowledge in self.knowledge_base.values():
            if knowledge.domain.value == domain or knowledge.topic == domain:
                content_words = set(knowledge.content.lower().split())
                overlap = len(desc_words & content_words) / max(len(desc_words), 1)
                if overlap > 0.1:
                    relevant.append(knowledge)

        return relevant

    def get_transfer_stats(self) -> Dict[str, Any]:
        """获取迁移统计"""
        if not self.transfers:
            return {"total": 0, "success_rate": 0.0}

        successful = sum(1 for t in self.transfers if t.success)
        return {
            "total": len(self.transfers),
            "successful": successful,
            "success_rate": successful / len(self.transfers),
            "avg_transfer_score": sum(t.transfer_score for t in self.transfers) / len(self.transfers),
            "adaptation_required_rate": sum(1 for t in self.transfers if t.adaptation_required) / len(self.transfers)
        }

    # ========== 元学习 ==========

    def reflect_on_learning(self, strategy: str, context: str,
                            outcome: float, conditions: Optional[List[str]] = None) -> MetaLearningInsight:
        """
        元学习：学习如何学习

        Args:
            strategy: 使用的策略
            context: 学习情境
            outcome: 学习结果（0-1）
            conditions: 条件列表

        Returns:
            MetaLearningInsight: 元学习洞察
        """
        self.total_meta_insights += 1

        # 记录策略效果
        self.strategy_effectiveness[strategy].append(outcome)

        # 计算策略平均效果
        avg_effectiveness = sum(self.strategy_effectiveness[strategy]) / len(self.strategy_effectiveness[strategy])

        # 生成推荐
        recommendation = self._generate_strategy_recommendation(strategy, avg_effectiveness, context)

        insight = MetaLearningInsight(
            strategy_tested=strategy,
            effectiveness_score=avg_effectiveness,
            context=context,
            conditions=conditions or [],
            recommendation=recommendation,
            metadata={"outcome": outcome, "total_trials": len(self.strategy_effectiveness[strategy])}
        )

        self.meta_insights.append(insight)

        # 更新学习偏好
        self.learning_preferences[strategy] = avg_effectiveness

        logger.debug(f"Meta-learning insight: {strategy} effectiveness={avg_effectiveness:.2f}")
        return insight

    def _generate_strategy_recommendation(self, strategy: str,
                                          effectiveness: float, context: str) -> str:
        """生成策略推荐"""
        if effectiveness > 0.8:
            return f"策略 '{strategy}' 在 '{context}' 情境下非常有效，建议继续使用"
        elif effectiveness > 0.5:
            return f"策略 '{strategy}' 在 '{context}' 情境下效果一般，可尝试调整"
        else:
            return f"策略 '{strategy}' 在 '{context}' 情境下效果不佳，建议尝试其他策略"

    def get_best_strategies(self, context: str = "",
                           top_k: int = 3) -> List[Tuple[str, float]]:
        """
        获取最佳学习策略

        Args:
            context: 情境
            top_k: 返回数量

        Returns:
            List[Tuple[str, float]]: (策略, 效果分数)列表
        """
        strategies = sorted(
            self.learning_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return strategies[:top_k]

    def get_meta_learning_stats(self) -> Dict[str, Any]:
        """获取元学习统计"""
        if not self.meta_insights:
            return {"total_insights": 0, "avg_effectiveness": 0.0}

        return {
            "total_insights": len(self.meta_insights),
            "strategies_tested": len(self.strategy_effectiveness),
            "avg_effectiveness": sum(i.effectiveness_score for i in self.meta_insights) / len(self.meta_insights),
            "best_strategy": self.get_best_strategies()[0] if self.learning_preferences else None,
            "strategy_breakdown": {
                strategy: {
                    "avg": sum(scores) / len(scores),
                    "count": len(scores)
                }
                for strategy, scores in self.strategy_effectiveness.items()
            }
        }

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            "total_knowledge_acquired": self.total_knowledge_acquired,
            "total_inferences_made": self.total_inferences_made,
            "total_evaluations": self.total_evaluations,
            "total_transfers": self.total_transfers,
            "total_meta_insights": self.total_meta_insights,
            "knowledge_base_size": len(self.knowledge_base),
            "domains_covered": len(self.domain_index),
            "avg_knowledge_mastery": self._avg_knowledge_mastery(),
            "avg_inference_validity": self.get_inference_stats()["avg_validity"],
            "critical_acceptance_rate": self.get_critical_stats()["acceptance_rate"],
            "transfer_success_rate": self.get_transfer_stats()["success_rate"],
            "meta_learning_effectiveness": self.get_meta_learning_stats()["avg_effectiveness"],
        }

    def _avg_knowledge_mastery(self) -> float:
        """平均知识掌握度"""
        if not self.knowledge_base:
            return 0.0
        return sum(k.mastery_level for k in self.knowledge_base.values()) / len(self.knowledge_base)

    def reset(self) -> None:
        """重置学习状态"""
        self.knowledge_base.clear()
        self.domain_index.clear()
        self.topic_index.clear()
        self.inferences.clear()
        self.inference_rules.clear()
        self.evaluations.clear()
        self.evaluation_index.clear()
        self.transfers.clear()
        self.transfer_success_rate.clear()
        self.meta_insights.clear()
        self.strategy_effectiveness.clear()
        self.learning_preferences.clear()
        self.total_knowledge_acquired = 0
        self.total_inferences_made = 0
        self.total_evaluations = 0
        self.total_transfers = 0
        self.total_meta_insights = 0
        logger.info("AdultLearningEngine reset")
