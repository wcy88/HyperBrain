"""
儿童学习引擎 (Child Learning Engine)

模拟儿童期的学习方式：
- 快速概念学习：从少量样本中学习概念
- 语言学习：词汇和语法学习
- 好奇心驱动学习：主动提问和探索
- 泛化学习：将知识应用到新情境
- 联想学习：建立事物间的联系

特征：快速概念形成、语言习得、强泛化能力
"""

import uuid
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("learning.child")


class ConceptLearningResult(BaseModel):
    """概念学习结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_name: str = Field(...)
    concept_id: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    examples_used: int = Field(default=0, ge=0)
    defining_features: List[str] = Field(default_factory=list)
    generalization_scope: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", "generalization_scope")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LanguageLearningResult(BaseModel):
    """语言学习结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    word_or_phrase: str = Field(...)
    learning_type: str = Field(default="vocabulary")  # vocabulary, grammar, phrase
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0)
    usage_count: int = Field(default=0, ge=0)
    context_examples: List[str] = Field(default_factory=list)
    associations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("mastery_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class QuestionRecord(BaseModel):
    """提问记录"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str = Field(...)
    category: str = Field(default="general")  # what, why, how, where, when
    answer: Optional[str] = Field(default=None)
    satisfaction: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    follow_up_questions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("satisfaction")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class GeneralizationResult(BaseModel):
    """泛化学习结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_concept: str = Field(...)
    target_context: str = Field(...)
    success: bool = Field(default=False)
    transfer_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("transfer_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class AssociationLink(BaseModel):
    """联想连接"""
    link_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(...)
    target: str = Field(...)
    association_type: str = Field(default="similarity")  # similarity, causality, contrast, cooccurrence
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = Field(default=1, ge=0)
    contexts: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("strength")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LearnedConcept(BaseModel):
    """学习到的概念"""
    concept_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    description: str = Field(default="")
    defining_features: Dict[str, Any] = Field(default_factory=dict)
    positive_examples: List[Any] = Field(default_factory=list)
    negative_examples: List[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    abstraction_level: int = Field(default=0, ge=0)
    parent_concepts: List[str] = Field(default_factory=list)
    child_concepts: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class ChildLearningConfig:
    """儿童学习配置"""
    concept_threshold: float = 0.7
    generalization_factor: float = 0.6
    curiosity_decay: float = 0.03
    max_concepts: int = 2000
    max_vocabulary: int = 10000
    association_threshold: float = 0.3
    question_memory_size: int = 500
    few_shot_examples: int = 3
    language_learning_rate: float = 0.4


class ChildLearningEngine:
    """
    儿童学习引擎

    模拟儿童期（2-12岁）的学习方式，特点：
    1. 快速概念形成：从少量样本学习新概念
    2. 语言习得：快速学习词汇和语法
    3. 强泛化能力：将知识应用到新情境
    4. 好奇心驱动：主动提问和探索
    5. 联想学习：建立事物间的联系

    Attributes:
        config: 学习配置
        concepts: 概念库
        vocabulary: 词汇库
        associations: 联想网络
        questions: 提问历史
        generalizations: 泛化记录
    """

    def __init__(self, config: Optional[ChildLearningConfig] = None):
        self.config = config or ChildLearningConfig()

        # 概念学习
        self.concepts: Dict[str, LearnedConcept] = {}
        self.concept_index: Dict[str, List[str]] = defaultdict(list)

        # 语言学习
        self.vocabulary: Dict[str, LanguageLearningResult] = {}
        self.grammar_rules: Dict[str, Dict[str, Any]] = {}
        self.phrase_patterns: Dict[str, int] = Counter()

        # 联想网络
        self.associations: Dict[str, AssociationLink] = {}
        self.association_graph: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 好奇心和提问
        self.questions: List[QuestionRecord] = []
        self.question_categories: Counter = Counter()
        self.unanswered_questions: List[QuestionRecord] = []
        self.curiosity_level: float = 0.8

        # 泛化记录
        self.generalizations: List[GeneralizationResult] = []
        self.generalization_success_rate: Dict[str, float] = {}

        # 学习统计
        self.total_concepts_learned: int = 0
        self.total_words_learned: int = 0
        self.total_questions_asked: int = 0
        self.total_associations_formed: int = 0
        self.total_generalizations: int = 0

        logger.info("ChildLearningEngine initialized")

    # ========== 快速概念学习 ==========

    def learn_concept(self, name: str, examples: List[Any],
                      negative_examples: Optional[List[Any]] = None,
                      description: str = "") -> ConceptLearningResult:
        """
        从少量样本学习概念

        模拟儿童的快速概念学习能力，能够从几个例子中
        提取关键特征并形成概念。

        Args:
            name: 概念名称
            examples: 正例列表
            negative_examples: 负例列表
            description: 概念描述

        Returns:
            ConceptLearningResult: 学习结果
        """
        if not examples:
            raise ValueError("At least one example is required")

        self.total_concepts_learned += 1

        # 提取定义特征
        defining_features = self._extract_defining_features(examples, negative_examples or [])

        # 计算置信度（基于例子数量和一致性）
        confidence = min(1.0, 0.3 + len(examples) * 0.2)
        if negative_examples:
            # 有负例时置信度更高
            confidence = min(1.0, confidence + 0.1)

        # 计算泛化范围
        generalization_scope = self._estimate_generalization_scope(examples, defining_features)

        # 创建或更新概念
        concept = self._find_or_create_concept(name)
        concept.description = description
        concept.defining_features = defining_features
        concept.positive_examples.extend(examples)
        if negative_examples:
            concept.negative_examples.extend(negative_examples)
        concept.confidence = max(concept.confidence, confidence)
        concept.updated_at = datetime.now()

        # 建立关联
        self._link_related_concepts(concept)

        result = ConceptLearningResult(
            concept_name=name,
            concept_id=concept.concept_id,
            confidence=confidence,
            examples_used=len(examples),
            defining_features=list(defining_features.keys()),
            generalization_scope=generalization_scope,
            metadata={
                "negative_examples": len(negative_examples or []),
                "total_positive_examples": len(concept.positive_examples)
            }
        )

        logger.debug(f"Learned concept: {name}, confidence={confidence:.2f}")
        return result

    def _extract_defining_features(self, positive: List[Any],
                                   negative: List[Any]) -> Dict[str, Any]:
        """提取定义特征"""
        features: Dict[str, Any] = {}

        if not positive:
            return features

        # 分析正例的共同特征
        if all(isinstance(e, dict) for e in positive):
            common_keys = set(positive[0].keys())
            for ex in positive[1:]:
                common_keys &= set(ex.keys())
            for key in common_keys:
                values = [e[key] for e in positive]
                if all(v == values[0] for v in values):
                    features[key] = values[0]
                else:
                    features[key] = {"type": type(values[0]).__name__, "values": list(set(values))}

        elif all(isinstance(e, str) for e in positive):
            # 文本特征：共同词
            words_sets = [set(e.lower().split()) for e in positive]
            common_words = words_sets[0]
            for ws in words_sets[1:]:
                common_words &= ws
            features["common_words"] = list(common_words)
            features["avg_length"] = sum(len(e) for e in positive) / len(positive)

        else:
            # 通用特征
            features["type"] = type(positive[0]).__name__
            features["count"] = len(positive)

        # 使用负例精化特征
        if negative:
            features["distinguishing_from"] = f"{len(negative)} negative examples"

        return features

    def _estimate_generalization_scope(self, examples: List[Any],
                                       features: Dict[str, Any]) -> float:
        """估计泛化范围"""
        if len(examples) < 2:
            return 0.3

        # 基于例子多样性
        diversity = self._calculate_diversity(examples)
        feature_generality = len(features) / max(len(examples), 1)

        return min(1.0, (diversity + feature_generality) / 2)

    def _calculate_diversity(self, examples: List[Any]) -> float:
        """计算示例多样性"""
        if len(examples) < 2:
            return 0.0

        # 简单的多样性度量
        if all(isinstance(e, str) for e in examples):
            words = [set(e.lower().split()) for e in examples]
            overlaps = []
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    intersection = len(words[i] & words[j])
                    union = len(words[i] | words[j])
                    overlaps.append(intersection / union if union > 0 else 0)
            avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
            return 1.0 - avg_overlap  # 多样性 = 1 - 重叠度

        return 0.5  # 默认中等多样性

    def _find_or_create_concept(self, name: str) -> LearnedConcept:
        """查找或创建概念"""
        for concept in self.concepts.values():
            if concept.name == name:
                return concept

        concept = LearnedConcept(name=name)
        self.concepts[concept.concept_id] = concept
        self.concept_index[name.lower()].append(concept.concept_id)
        return concept

    def _link_related_concepts(self, concept: LearnedConcept) -> None:
        """建立概念间的关联"""
        for other in self.concepts.values():
            if other.concept_id == concept.concept_id:
                continue

            # 检查特征重叠
            common_features = set(concept.defining_features.keys()) & set(other.defining_features.keys())
            if len(common_features) >= 2:
                concept.related_concepts.append(other.concept_id)
                other.related_concepts.append(concept.concept_id)

                # 创建联想连接
                self._create_association(
                    concept.name, other.name,
                    association_type="similarity",
                    strength=0.3 + len(common_features) * 0.1
                )

    def get_concept(self, name: str) -> Optional[LearnedConcept]:
        """获取概念"""
        for concept in self.concepts.values():
            if concept.name == name:
                return concept
        return None

    def classify(self, item: Any) -> List[Tuple[str, float]]:
        """
        使用学到的概念对物品分类

        Args:
            item: 待分类物品

        Returns:
            List[Tuple[str, float]]: (概念名, 匹配度)列表
        """
        scores = []
        for concept in self.concepts.values():
            score = self._match_concept(item, concept)
            if score > self.config.concept_threshold:
                scores.append((concept.name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _match_concept(self, item: Any, concept: LearnedConcept) -> float:
        """计算物品与概念的匹配度"""
        if not concept.defining_features:
            return 0.0

        score = 0.0
        total_features = len(concept.defining_features)

        if isinstance(item, dict):
            for key, expected in concept.defining_features.items():
                if key in item:
                    if isinstance(expected, dict) and "values" in expected:
                        if item[key] in expected["values"]:
                            score += 1.0
                    elif item[key] == expected:
                        score += 1.0

        elif isinstance(item, str):
            if "common_words" in concept.defining_features:
                words = set(item.lower().split())
                common = set(concept.defining_features["common_words"])
                overlap = len(words & common) / max(len(common), 1)
                score = overlap

        return score / total_features if total_features > 0 else 0.0

    # ========== 语言学习 ==========

    def learn_word(self, word: str, context: str = "",
                   definition: str = "") -> LanguageLearningResult:
        """
        学习词汇

        Args:
            word: 单词或短语
            context: 上下文
            definition: 定义

        Returns:
            LanguageLearningResult: 学习结果
        """
        word_lower = word.lower().strip()

        if word_lower in self.vocabulary:
            # 复习已学词汇
            vocab = self.vocabulary[word_lower]
            vocab.usage_count += 1
            vocab.mastery_level = min(1.0, vocab.mastery_level + 0.1)
            if context and context not in vocab.context_examples:
                vocab.context_examples.append(context)
            logger.debug(f"Reviewed word: {word}, mastery={vocab.mastery_level:.2f}")
            return vocab

        # 学习新词汇
        self.total_words_learned += 1
        vocab = LanguageLearningResult(
            word_or_phrase=word_lower,
            learning_type="vocabulary",
            mastery_level=0.2,
            usage_count=1,
            context_examples=[context] if context else [],
            metadata={"definition": definition}
        )
        self.vocabulary[word_lower] = vocab

        # 提取关联词
        if context:
            associated_words = self._extract_associated_words(word_lower, context)
            vocab.associations = associated_words

        logger.info(f"Learned new word: {word}")
        return vocab

    def learn_grammar(self, pattern: str, examples: List[str],
                      rule_description: str = "") -> Dict[str, Any]:
        """
        学习语法规则

        Args:
            pattern: 语法模式
            examples: 示例
            rule_description: 规则描述

        Returns:
            Dict[str, Any]: 学习结果
        """
        self.grammar_rules[pattern] = {
            "examples": examples,
            "description": rule_description,
            "learned_at": datetime.now().isoformat(),
            "usage_count": 0,
            "confidence": min(1.0, 0.3 + len(examples) * 0.15)
        }

        # 提取短语模式
        for example in examples:
            phrases = self._extract_phrases(example)
            for phrase in phrases:
                self.phrase_patterns[phrase] += 1

        logger.debug(f"Learned grammar pattern: {pattern}")
        return self.grammar_rules[pattern]

    def _extract_associated_words(self, word: str, context: str) -> List[str]:
        """提取关联词"""
        words = context.lower().split()
        if word in words:
            idx = words.index(word)
            # 获取相邻词
            associated = []
            if idx > 0:
                associated.append(words[idx - 1])
            if idx < len(words) - 1:
                associated.append(words[idx + 1])
            return associated
        return []

    def _extract_phrases(self, text: str) -> List[str]:
        """提取短语模式"""
        words = text.lower().split()
        phrases = []
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")
        return phrases

    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """获取词汇统计"""
        if not self.vocabulary:
            return {"total_words": 0, "avg_mastery": 0.0}

        masteries = [v.mastery_level for v in self.vocabulary.values()]
        return {
            "total_words": len(self.vocabulary),
            "avg_mastery": sum(masteries) / len(masteries),
            "mastered_words": sum(1 for m in masteries if m >= 0.8),
            "learning_words": sum(1 for m in masteries if 0.3 <= m < 0.8),
            "new_words": sum(1 for m in masteries if m < 0.3)
        }

    # ========== 好奇心驱动学习 ==========

    def ask_question(self, question: str, category: str = "general") -> QuestionRecord:
        """
        提出问题

        Args:
            question: 问题内容
            category: 问题类别

        Returns:
            QuestionRecord: 问题记录
        """
        self.total_questions_asked += 1
        self.question_categories[category] += 1

        record = QuestionRecord(
            question=question,
            category=category,
            timestamp=datetime.now()
        )

        self.questions.append(record)

        # 限制历史大小
        if len(self.questions) > self.config.question_memory_size:
            self.questions.pop(0)

        # 提问降低好奇心
        self.curiosity_level = max(0.2, self.curiosity_level - 0.05)

        logger.debug(f"Asked question: {question} (category={category})")
        return record

    def answer_question(self, question_id: str, answer: str,
                        satisfaction: float = 0.5) -> Optional[QuestionRecord]:
        """
        回答问题

        Args:
            question_id: 问题ID
            answer: 答案
            satisfaction: 满意度

        Returns:
            Optional[QuestionRecord]: 更新后的问题记录
        """
        for q in self.questions:
            if q.question_id == question_id:
                q.answer = answer
                q.satisfaction = satisfaction

                # 高满意度增加好奇心
                if satisfaction > 0.7:
                    self.curiosity_level = min(1.0, self.curiosity_level + 0.1)

                logger.debug(f"Answered question: {q.question}, satisfaction={satisfaction:.2f}")
                return q

        return None

    def generate_question(self, topic: str = "") -> str:
        """
        生成问题

        Args:
            topic: 主题

        Returns:
            str: 生成的问题
        """
        templates = [
            "什么是{topic}?",
            "为什么{topic}会这样?",
            "{topic}是怎么工作的?",
            "{topic}和其他的有什么不同?",
            "我可以用{topic}做什么?",
        ]

        if not topic:
            # 从已知概念中选择主题
            if self.concepts:
                topic = random.choice(list(self.concepts.values())).name
            else:
                topic = "这个"

        import random
        template = random.choice(templates)
        return template.format(topic=topic)

    def get_question_stats(self) -> Dict[str, Any]:
        """获取提问统计"""
        answered = sum(1 for q in self.questions if q.answer is not None)
        return {
            "total_questions": len(self.questions),
            "answered": answered,
            "unanswered": len(self.questions) - answered,
            "avg_satisfaction": sum(q.satisfaction for q in self.questions) / max(len(self.questions), 1),
            "category_distribution": dict(self.question_categories),
            "curiosity_level": self.curiosity_level
        }

    # ========== 泛化学习 ==========

    def generalize_knowledge(self, source_concept: str,
                            target_context: str,
                            reasoning: str = "") -> GeneralizationResult:
        """
        将知识泛化到新情境

        Args:
            source_concept: 源概念
            target_context: 目标情境
            reasoning: 推理过程

        Returns:
            GeneralizationResult: 泛化结果
        """
        self.total_generalizations += 1

        # 评估泛化可行性
        concept = self.get_concept(source_concept)
        if not concept:
            result = GeneralizationResult(
                source_concept=source_concept,
                target_context=target_context,
                success=False,
                transfer_score=0.0,
                reasoning="Source concept not found"
            )
            self.generalizations.append(result)
            return result

        # 计算转移分数
        transfer_score = self._calculate_transfer_score(concept, target_context)
        success = transfer_score > self.config.concept_threshold

        # 更新泛化成功率
        key = f"{source_concept}->{target_context}"
        self.generalization_success_rate[key] = transfer_score

        result = GeneralizationResult(
            source_concept=source_concept,
            target_context=target_context,
            success=success,
            transfer_score=transfer_score,
            reasoning=reasoning or f"Applied {source_concept} to {target_context}"
        )

        self.generalizations.append(result)
        logger.debug(f"Generalization: {source_concept} -> {target_context}, score={transfer_score:.2f}")
        return result

    def _calculate_transfer_score(self, concept: LearnedConcept,
                                  target_context: str) -> float:
        """计算知识转移分数"""
        base_score = concept.confidence * self.config.generalization_factor

        # 检查目标情境与概念特征的匹配
        context_lower = target_context.lower()
        feature_matches = 0
        for feature in concept.defining_features:
            if feature.lower() in context_lower:
                feature_matches += 1

        feature_bonus = min(0.3, feature_matches * 0.1)

        return min(1.0, base_score + feature_bonus)

    def get_generalization_stats(self) -> Dict[str, Any]:
        """获取泛化统计"""
        if not self.generalizations:
            return {"total": 0, "success_rate": 0.0}

        successful = sum(1 for g in self.generalizations if g.success)
        return {
            "total": len(self.generalizations),
            "successful": successful,
            "success_rate": successful / len(self.generalizations),
            "avg_transfer_score": sum(g.transfer_score for g in self.generalizations) / len(self.generalizations)
        }

    # ========== 联想学习 ==========

    def learn_association(self, source: str, target: str,
                          association_type: str = "similarity",
                          context: str = "") -> AssociationLink:
        """
        学习事物间的联想

        Args:
            source: 源概念
            target: 目标概念
            association_type: 联想类型
            context: 上下文

        Returns:
            AssociationLink: 联想连接
        """
        link_id = f"{source}__{target}__{association_type}"

        if link_id in self.associations:
            # 强化已有联想
            link = self.associations[link_id]
            link.strength = min(1.0, link.strength + 0.1)
            link.evidence_count += 1
            if context and context not in link.contexts:
                link.contexts.append(context)
            return link

        # 创建新联想
        self.total_associations_formed += 1
        link = AssociationLink(
            source=source,
            target=target,
            association_type=association_type,
            strength=0.3,
            contexts=[context] if context else []
        )

        self.associations[link.link_id] = link
        self.association_graph[source][target] = link.strength

        logger.debug(f"Learned association: {source} -> {target} ({association_type})")
        return link

    def _create_association(self, source: str, target: str,
                            association_type: str = "similarity",
                            strength: float = 0.5) -> AssociationLink:
        """内部方法：创建联想"""
        return self.learn_association(source, target, association_type, "")

    def get_associated(self, concept: str,
                       min_strength: float = 0.0) -> List[Tuple[str, float]]:
        """
        获取关联概念

        Args:
            concept: 概念名称
            min_strength: 最小关联强度

        Returns:
            List[Tuple[str, float]]: (关联概念, 强度)列表
        """
        associations = []
        for link in self.associations.values():
            if link.source == concept and link.strength >= min_strength:
                associations.append((link.target, link.strength))
            elif link.target == concept and link.strength >= min_strength:
                associations.append((link.source, link.strength))

        associations.sort(key=lambda x: x[1], reverse=True)
        return associations

    def find_association_paths(self, source: str, target: str,
                               max_depth: int = 3) -> List[List[str]]:
        """
        查找概念间的联想路径

        Args:
            source: 源概念
            target: 目标概念
            max_depth: 最大搜索深度

        Returns:
            List[List[str]]: 路径列表
        """
        paths = []
        visited = {source}

        def dfs(current: str, path: List[str], depth: int) -> None:
            if depth > max_depth:
                return
            if current == target and len(path) > 1:
                paths.append(path.copy())
                return

            for neighbor in self.association_graph.get(current, {}):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, path, depth + 1)
                    path.pop()
                    visited.remove(neighbor)

        dfs(source, [source], 0)
        return paths

    def get_association_stats(self) -> Dict[str, Any]:
        """获取联想统计"""
        type_counts = Counter(link.association_type for link in self.associations.values())
        strengths = [link.strength for link in self.associations.values()]

        return {
            "total_associations": len(self.associations),
            "type_distribution": dict(type_counts),
            "avg_strength": sum(strengths) / max(len(strengths), 1),
            "strong_associations": sum(1 for s in strengths if s >= 0.7)
        }

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            "total_concepts_learned": self.total_concepts_learned,
            "total_words_learned": self.total_words_learned,
            "total_questions_asked": self.total_questions_asked,
            "total_associations_formed": self.total_associations_formed,
            "total_generalizations": self.total_generalizations,
            "concepts_in_memory": len(self.concepts),
            "vocabulary_size": len(self.vocabulary),
            "grammar_rules": len(self.grammar_rules),
            "curiosity_level": self.curiosity_level,
            "concept_confidence_avg": self._avg_concept_confidence(),
            "vocabulary_mastery_avg": self._avg_vocabulary_mastery(),
            "generalization_success_rate": self.get_generalization_stats()["success_rate"],
        }

    def _avg_concept_confidence(self) -> float:
        """平均概念置信度"""
        if not self.concepts:
            return 0.0
        return sum(c.confidence for c in self.concepts.values()) / len(self.concepts)

    def _avg_vocabulary_mastery(self) -> float:
        """平均词汇掌握度"""
        if not self.vocabulary:
            return 0.0
        return sum(v.mastery_level for v in self.vocabulary.values()) / len(self.vocabulary)

    def reset(self) -> None:
        """重置学习状态"""
        self.concepts.clear()
        self.concept_index.clear()
        self.vocabulary.clear()
        self.grammar_rules.clear()
        self.phrase_patterns.clear()
        self.associations.clear()
        self.association_graph.clear()
        self.questions.clear()
        self.question_categories.clear()
        self.unanswered_questions.clear()
        self.generalizations.clear()
        self.generalization_success_rate.clear()
        self.curiosity_level = 0.8
        self.total_concepts_learned = 0
        self.total_words_learned = 0
        self.total_questions_asked = 0
        self.total_associations_formed = 0
        self.total_generalizations = 0
        logger.info("ChildLearningEngine reset")
