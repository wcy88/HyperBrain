"""
学习管理器 (Learning Manager)

统一管理所有学习模块：
- 管理三个学习引擎（婴儿、儿童、成人）
- 根据情境自动切换学习模式
- 协调各学习模块
- 提供统一的学习API
- 与记忆系统和认知系统交互
"""

import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.learning.infant_learning import (
    InfantLearningEngine, InfantLearningConfig,
    ExplorationResult, TrialResult, ImitationRecord
)
from hyperbrain.layers.learning.child_learning import (
    ChildLearningEngine, ChildLearningConfig,
    ConceptLearningResult, LanguageLearningResult, QuestionRecord,
    GeneralizationResult, AssociationLink, LearnedConcept
)
from hyperbrain.layers.learning.adult_learning import (
    AdultLearningEngine, AdultLearningConfig,
    StructuredKnowledge, LogicalInference, CriticalEvaluation,
    KnowledgeTransfer, MetaLearningInsight, KnowledgeDomain
)
from hyperbrain.layers.learning.lifelong_learning import (
    LifelongLearningMechanism, LifelongLearningConfig,
    LearningEvent, LearningProgress, LearningEffectiveness
)
from hyperbrain.layers.learning.knowledge_integration import (
    KnowledgeIntegrationMechanism, KnowledgeIntegrationConfig,
    KnowledgeNode, KnowledgeEdge, KnowledgeConflict,
    KnowledgeCategory
)
from hyperbrain.layers.learning.transfer_learning import (
    TransferLearningMechanism, TransferLearningConfig,
    Domain, KnowledgeMapping, SkillTransfer, CrossDomainApplication
)

logger = get_logger("learning.manager")


class LearningMode(str, Enum):
    """学习模式"""
    INFANT = "infant"      # 0-2岁：探索驱动
    CHILD = "child"        # 2-12岁：概念驱动
    ADULT = "adult"        # 12岁+：结构驱动
    AUTOMATIC = "automatic"  # 自动选择


class LearningContext(BaseModel):
    """学习情境"""
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: LearningMode = Field(default=LearningMode.AUTOMATIC)
    domain: str = Field(default="general")
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty: float = Field(default=0.5, ge=0.0, le=1.0)
    urgency: float = Field(default=0.0, ge=0.0, le=1.0)
    prior_knowledge: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_state: str = Field(default="neutral")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("complexity", "novelty", "urgency", "prior_knowledge")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LearningResult(BaseModel):
    """统一学习结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode_used: LearningMode = Field(...)
    engine_type: str = Field(...)
    success: bool = Field(default=True)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    content: Any = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ModeSwitchRecord(BaseModel):
    """模式切换记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_mode: LearningMode = Field(...)
    to_mode: LearningMode = Field(...)
    reason: str = Field(default="")
    context: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class LearningManagerConfig:
    """学习管理器配置"""
    default_mode: LearningMode = LearningMode.AUTOMATIC
    mode_switch_threshold: float = 0.3
    infant_priority_novelty: float = 0.8
    child_priority_concepts: float = 0.6
    adult_priority_structure: float = 0.7
    enable_lifelong: bool = True
    enable_integration: bool = True
    enable_transfer: bool = True
    auto_mode_switch: bool = True


class LearningManager:
    """
    学习管理器

    协调和管理所有学习模块的核心组件：
    1. 引擎管理：管理婴儿、儿童、成人三个学习引擎
    2. 模式切换：根据情境自动选择最合适的学习模式
    3. 模块协调：确保各模块协同工作
    4. 统一API：提供一致的学习接口
    5. 系统交互：与记忆和认知系统联动

    Attributes:
        config: 管理器配置
        infant_engine: 婴儿学习引擎
        child_engine: 儿童学习引擎
        adult_engine: 成人学习引擎
        lifelong: 终身学习机制
        integration: 知识整合机制
        transfer: 能力迁移机制
        current_mode: 当前学习模式
    """

    def __init__(self, config: Optional[LearningManagerConfig] = None,
                 infant_config: Optional[InfantLearningConfig] = None,
                 child_config: Optional[ChildLearningConfig] = None,
                 adult_config: Optional[AdultLearningConfig] = None,
                 lifelong_config: Optional[LifelongLearningConfig] = None,
                 integration_config: Optional[KnowledgeIntegrationConfig] = None,
                 transfer_config: Optional[TransferLearningConfig] = None):
        self.config = config or LearningManagerConfig()

        # 初始化学习引擎
        self.infant_engine = InfantLearningEngine(config=infant_config)
        self.child_engine = ChildLearningEngine(config=child_config)
        self.adult_engine = AdultLearningEngine(config=adult_config)

        # 初始化支持机制
        self.lifelong = LifelongLearningMechanism(config=lifelong_config)
        self.integration = KnowledgeIntegrationMechanism(config=integration_config)
        self.transfer_mechanism = TransferLearningMechanism(config=transfer_config)

        # 当前状态
        self.current_mode: LearningMode = self.config.default_mode
        self.mode_switch_history: List[ModeSwitchRecord] = []
        self.learning_history: List[LearningResult] = []

        # 统计
        self.total_learning_sessions: int = 0
        self.mode_usage_count: Dict[LearningMode, int] = defaultdict(int)

        logger.info("LearningManager initialized")

    # ========== 模式管理 ==========

    def select_mode(self, context: Optional[LearningContext] = None) -> LearningMode:
        """
        根据情境选择学习模式

        选择逻辑：
        - 高新颖性 + 低先验知识 -> 婴儿模式（探索）
        - 中等复杂度 + 概念学习 -> 儿童模式（概念）
        - 高复杂度 + 结构化需求 -> 成人模式（结构）

        Args:
            context: 学习情境

        Returns:
            LearningMode: 选择的学习模式
        """
        if not self.config.auto_mode_switch:
            return self.current_mode

        if not context:
            return LearningMode.ADULT

        # 如果指定了模式，直接使用
        if context.mode != LearningMode.AUTOMATIC:
            return context.mode

        # 计算各模式的适配度
        infant_score = self._calculate_infant_score(context)
        child_score = self._calculate_child_score(context)
        adult_score = self._calculate_adult_score(context)

        # 选择最高分
        scores = {
            LearningMode.INFANT: infant_score,
            LearningMode.CHILD: child_score,
            LearningMode.ADULT: adult_score
        }

        best_mode = max(scores, key=scores.get)

        # 记录模式切换
        if best_mode != self.current_mode:
            self._record_mode_switch(self.current_mode, best_mode,
                                    f"Context: novelty={context.novelty:.2f}, "
                                    f"complexity={context.complexity:.2f}, "
                                    f"prior={context.prior_knowledge:.2f}")
            self.current_mode = best_mode

        return best_mode

    def _calculate_infant_score(self, context: LearningContext) -> float:
        """计算婴儿模式适配度"""
        score = 0.0
        # 高新颖性偏好婴儿模式
        score += context.novelty * self.config.infant_priority_novelty
        # 低先验知识偏好婴儿模式
        score += (1.0 - context.prior_knowledge) * 0.5
        # 低复杂度偏好婴儿模式
        score += (1.0 - context.complexity) * 0.3
        return score / 1.8

    def _calculate_child_score(self, context: LearningContext) -> float:
        """计算儿童模式适配度"""
        score = 0.0
        # 中等复杂度
        score += (1.0 - abs(context.complexity - 0.5)) * self.config.child_priority_concepts
        # 中等先验知识
        score += (1.0 - abs(context.prior_knowledge - 0.5)) * 0.4
        # 中等新颖性
        score += (1.0 - abs(context.novelty - 0.5)) * 0.3
        return score / 1.3

    def _calculate_adult_score(self, context: LearningContext) -> float:
        """计算成人模式适配度"""
        score = 0.0
        # 高复杂度偏好成人模式
        score += context.complexity * self.config.adult_priority_structure
        # 高先验知识偏好成人模式
        score += context.prior_knowledge * 0.5
        # 低新颖性（结构化学习不需要太多探索）
        score += (1.0 - context.novelty) * 0.2
        return score / 1.4

    def _record_mode_switch(self, from_mode: LearningMode, to_mode: LearningMode,
                           reason: str = "") -> None:
        """记录模式切换"""
        record = ModeSwitchRecord(
            from_mode=from_mode,
            to_mode=to_mode,
            reason=reason
        )
        self.mode_switch_history.append(record)
        logger.info(f"Mode switch: {from_mode.value} -> {to_mode.value}, reason={reason}")

    def get_current_mode(self) -> LearningMode:
        """获取当前模式"""
        return self.current_mode

    def set_mode(self, mode: LearningMode) -> None:
        """手动设置模式"""
        if mode != self.current_mode:
            self._record_mode_switch(self.current_mode, mode, "Manual override")
            self.current_mode = mode

    # ========== 统一学习API ==========

    def learn(self, content: Any, context: Optional[LearningContext] = None,
             **kwargs) -> LearningResult:
        """
        统一学习接口

        根据当前模式调用相应的学习引擎。

        Args:
            content: 学习内容
            context: 学习情境
            **kwargs: 额外参数

        Returns:
            LearningResult: 学习结果
        """
        self.total_learning_sessions += 1

        mode = self.select_mode(context)
        self.mode_usage_count[mode] += 1

        if mode == LearningMode.INFANT:
            result = self._infant_learn(content, context, **kwargs)
        elif mode == LearningMode.CHILD:
            result = self._child_learn(content, context, **kwargs)
        elif mode == LearningMode.ADULT:
            result = self._adult_learn(content, context, **kwargs)
        else:
            result = self._adult_learn(content, context, **kwargs)

        # 记录到终身学习
        if self.config.enable_lifelong:
            self.lifelong.record_learning_event(
                event_type="learning_session",
                content=str(content)[:200],
                source_engine=mode.value,
                importance=result.confidence
            )

        # 知识整合
        if self.config.enable_integration and isinstance(content, str):
            self._integrate_learning_result(result, content)

        self.learning_history.append(result)
        return result

    def _infant_learn(self, content: Any, context: Optional[LearningContext],
                     **kwargs) -> LearningResult:
        """使用婴儿引擎学习"""
        if isinstance(content, (list, tuple, dict, str)):
            exploration = self.infant_engine.explore(content)
            return LearningResult(
                mode_used=LearningMode.INFANT,
                engine_type="infant",
                success=True,
                confidence=exploration.confidence,
                content=exploration,
                metadata={"pattern_id": exploration.pattern_id}
            )
        else:
            # 试错学习
            action = kwargs.get("action", str(content))
            trial = self.infant_engine.trial(action)
            return LearningResult(
                mode_used=LearningMode.INFANT,
                engine_type="infant",
                success=trial.success,
                confidence=0.5 + trial.reward * 0.5,
                content=trial,
                metadata={"reward": trial.reward}
            )

    def _child_learn(self, content: Any, context: Optional[LearningContext],
                    **kwargs) -> LearningResult:
        """使用儿童引擎学习"""
        if isinstance(content, str):
            # 语言学习
            if kwargs.get("is_language", False):
                result = self.child_engine.learn_word(content, kwargs.get("context", ""))
                return LearningResult(
                    mode_used=LearningMode.CHILD,
                    engine_type="child",
                    success=True,
                    confidence=result.mastery_level,
                    content=result,
                    metadata={"word": content}
                )
            # 概念学习
            elif kwargs.get("concept_name"):
                examples = kwargs.get("examples", [content])
                result = self.child_engine.learn_concept(
                    kwargs["concept_name"], examples
                )
                return LearningResult(
                    mode_used=LearningMode.CHILD,
                    engine_type="child",
                    success=True,
                    confidence=result.confidence,
                    content=result,
                    metadata={"concept": kwargs["concept_name"]}
                )
            else:
                # 默认作为词汇学习
                result = self.child_engine.learn_word(content)
                return LearningResult(
                    mode_used=LearningMode.CHILD,
                    engine_type="child",
                    success=True,
                    confidence=result.mastery_level,
                    content=result
                )
        else:
            return LearningResult(
                mode_used=LearningMode.CHILD,
                engine_type="child",
                success=False,
                confidence=0.0,
                content=None,
                metadata={"error": "Unsupported content type for child mode"}
            )

    def _adult_learn(self, content: Any, context: Optional[LearningContext],
                    **kwargs) -> LearningResult:
        """使用成人引擎学习"""
        if isinstance(content, str):
            topic = kwargs.get("topic", content[:50])
            domain_str = kwargs.get("domain", "general")
            try:
                domain = KnowledgeDomain(domain_str)
            except ValueError:
                domain = KnowledgeDomain.GENERAL

            result = self.adult_engine.learn_structured(
                topic=topic,
                content=content,
                domain=domain,
                key_points=kwargs.get("key_points"),
                prerequisites=kwargs.get("prerequisites")
            )
            return LearningResult(
                mode_used=LearningMode.ADULT,
                engine_type="adult",
                success=True,
                confidence=result.confidence,
                content=result,
                metadata={"topic": topic, "domain": domain.value}
            )
        else:
            return LearningResult(
                mode_used=LearningMode.ADULT,
                engine_type="adult",
                success=False,
                confidence=0.0,
                content=None,
                metadata={"error": "Unsupported content type for adult mode"}
            )

    def _integrate_learning_result(self, result: LearningResult, content: str) -> None:
        """整合学习结果到知识库"""
        try:
            node = self.integration.add_knowledge(
                content=content,
                confidence=result.confidence,
                source=result.engine_type
            )
            # 建立与相关知识的关联
            related = self.integration.search_knowledge(content[:30])
            for rel_node in related[:3]:
                if rel_node.node_id != node.node_id:
                    self.integration.create_relation(
                        node.node_id, rel_node.node_id,
                        relation_type="learned_together",
                        strength=result.confidence * 0.5
                    )
        except Exception as e:
            logger.warning(f"Knowledge integration failed: {e}")

    # ========== 探索学习 ==========

    def explore(self, data: Any, context: str = "") -> ExplorationResult:
        """
        探索学习

        Args:
            data: 数据
            context: 上下文

        Returns:
            ExplorationResult: 探索结果
        """
        return self.infant_engine.explore(data, context)

    # ========== 概念学习 ==========

    def learn_concept(self, name: str, examples: List[Any],
                     negative_examples: Optional[List[Any]] = None) -> ConceptLearningResult:
        """
        学习概念

        Args:
            name: 概念名称
            examples: 示例
            negative_examples: 负例

        Returns:
            ConceptLearningResult: 学习结果
        """
        return self.child_engine.learn_concept(name, examples, negative_examples)

    # ========== 结构化学习 ==========

    def learn_structured(self, topic: str, content: str,
                        domain: KnowledgeDomain = KnowledgeDomain.GENERAL,
                        **kwargs) -> StructuredKnowledge:
        """
        结构化学习

        Args:
            topic: 主题
            content: 内容
            domain: 领域
            **kwargs: 额外参数

        Returns:
            StructuredKnowledge: 结构化知识
        """
        return self.adult_engine.learn_structured(topic, content, domain, **kwargs)

    # ========== 批判性评估 ==========

    def evaluate(self, subject: str, evidence: List[str],
                source: str = "", **kwargs) -> CriticalEvaluation:
        """
        批判性评估

        Args:
            subject: 主题
            evidence: 证据
            source: 来源
            **kwargs: 额外参数

        Returns:
            CriticalEvaluation: 评估结果
        """
        return self.adult_engine.critically_evaluate(subject, evidence, source, **kwargs)

    # ========== 知识迁移 ==========

    def transfer(self, skill_name: str, source_domain: str,
                target_domain: str, user_proficiency: float = 0.5) -> SkillTransfer:
        """
        知识迁移

        Args:
            skill_name: 技能名称
            source_domain: 源领域
            target_domain: 目标领域
            user_proficiency: 熟练度

        Returns:
            SkillTransfer: 迁移结果
        """
        return self.transfer_mechanism.assess_transfer(skill_name, source_domain, target_domain, user_proficiency)

    # ========== 知识整合 ==========

    def integrate_knowledge(self, content: str,
                           category: Optional[KnowledgeCategory] = None,
                           **kwargs) -> KnowledgeNode:
        """
        整合知识

        Args:
            content: 内容
            category: 分类
            **kwargs: 额外参数

        Returns:
            KnowledgeNode: 知识节点
        """
        return self.integration.add_knowledge(content, category, **kwargs)

    def find_knowledge(self, query: str,
                      category: Optional[KnowledgeCategory] = None) -> List[KnowledgeNode]:
        """
        查找知识

        Args:
            query: 查询
            category: 分类

        Returns:
            List[KnowledgeNode]: 知识节点列表
        """
        return self.integration.search_knowledge(query, category)

    # ========== 终身学习 ==========

    def track_progress(self, domain: str, current_level: float,
                      target_level: float = 1.0) -> LearningProgress:
        """
        跟踪学习进度

        Args:
            domain: 领域
            current_level: 当前水平
            target_level: 目标水平

        Returns:
            LearningProgress: 进度
        """
        return self.lifelong.track_progress(domain, current_level, target_level)

    def assess_learning(self) -> LearningEffectiveness:
        """
        评估学习效果

        Returns:
            LearningEffectiveness: 效果评估
        """
        return self.lifelong.assess_effectiveness()

    # ========== 系统联动 ==========

    def sync_with_memory(self, memory_manager: Any) -> Dict[str, Any]:
        """
        与记忆系统同步

        Args:
            memory_manager: 记忆管理器

        Returns:
            Dict[str, Any]: 同步结果
        """
        synced_items = 0

        # 将学习历史同步到记忆
        for result in self.learning_history[-50:]:
            try:
                if hasattr(memory_manager, 'store'):
                    memory_manager.store(
                        content=str(result.content)[:500],
                        metadata={
                            "type": "learning_result",
                            "mode": result.mode_used.value,
                            "confidence": result.confidence
                        }
                    )
                    synced_items += 1
            except Exception as e:
                logger.warning(f"Memory sync failed for item: {e}")

        return {"synced_items": synced_items, "status": "success"}

    def sync_with_cognition(self, cognitive_manager: Any) -> Dict[str, Any]:
        """
        与认知系统同步

        Args:
            cognitive_manager: 认知管理器

        Returns:
            Dict[str, Any]: 同步结果
        """
        synced_items = 0

        # 将学到的概念同步到认知系统
        for concept in self.child_engine.concepts.values():
            try:
                if hasattr(cognitive_manager, 'add_concept'):
                    cognitive_manager.add_concept(
                        name=concept.name,
                        description=concept.description,
                        confidence=concept.confidence
                    )
                    synced_items += 1
            except Exception as e:
                logger.warning(f"Cognition sync failed for concept: {e}")

        # 将结构化知识同步
        for knowledge in self.adult_engine.knowledge_base.values():
            try:
                if hasattr(cognitive_manager, 'add_knowledge'):
                    cognitive_manager.add_knowledge(
                        topic=knowledge.topic,
                        content=knowledge.content,
                        domain=knowledge.domain.value
                    )
                    synced_items += 1
            except Exception as e:
                logger.warning(f"Cognition sync failed for knowledge: {e}")

        return {"synced_items": synced_items, "status": "success"}

    # ========== 统计和报告 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取完整统计信息"""
        return {
            "total_learning_sessions": self.total_learning_sessions,
            "current_mode": self.current_mode.value,
            "mode_usage": {mode.value: count for mode, count in self.mode_usage_count.items()},
            "mode_switches": len(self.mode_switch_history),
            "infant_engine": self.infant_engine.get_stats(),
            "child_engine": self.child_engine.get_stats(),
            "adult_engine": self.adult_engine.get_stats(),
            "lifelong_learning": self.lifelong.get_stats(),
            "knowledge_integration": self.integration.get_stats(),
            "transfer_learning": self.transfer_mechanism.get_stats(),
        }

    def get_learning_report(self) -> Dict[str, Any]:
        """生成学习报告"""
        stats = self.get_stats()

        return {
            "report_time": datetime.now().isoformat(),
            "summary": {
                "total_sessions": stats["total_learning_sessions"],
                "preferred_mode": max(stats["mode_usage"], key=stats["mode_usage"].get)
                if stats["mode_usage"] else "none",
                "overall_progress": self.lifelong.get_overall_progress()
            },
            "engine_performance": {
                "infant": {
                    "explorations": stats["infant_engine"]["total_explorations"],
                    "patterns_found": stats["infant_engine"]["patterns_discovered"]
                },
                "child": {
                    "concepts_learned": stats["child_engine"]["total_concepts_learned"],
                    "vocabulary_size": stats["child_engine"]["vocabulary_size"]
                },
                "adult": {
                    "knowledge_acquired": stats["adult_engine"]["total_knowledge_acquired"],
                    "avg_mastery": stats["adult_engine"]["avg_knowledge_mastery"]
                }
            },
            "knowledge_state": {
                "active_nodes": stats["knowledge_integration"]["active_nodes"],
                "unresolved_conflicts": stats["knowledge_integration"]["unresolved_conflicts"],
                "transfer_success_rate": stats["transfer_learning"]["transfer_success_rate"]
            },
            "recommendations": self._generate_recommendations(stats)
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成学习建议"""
        recommendations = []

        # 基于使用模式的建议
        mode_usage = stats["mode_usage"]
        total = sum(mode_usage.values())
        if total > 0:
            infant_ratio = mode_usage.get(LearningMode.INFANT, 0) / total
            if infant_ratio > 0.5:
                recommendations.append("探索活动较多，建议增加结构化学习")

        # 基于知识状态的建议
        if stats["knowledge_integration"]["unresolved_conflicts"] > 5:
            recommendations.append("存在较多知识冲突，建议进行知识整理")

        # 基于迁移效果的建议
        if stats["transfer_learning"]["transfer_success_rate"] < 0.3:
            recommendations.append("知识迁移成功率较低，建议加强领域间联系")

        if not recommendations:
            recommendations.append("学习状态良好，继续保持")

        return recommendations

    # ========== 重置 ==========

    def reset(self) -> None:
        """重置所有学习状态"""
        self.infant_engine.reset()
        self.child_engine.reset()
        self.adult_engine.reset()
        self.lifelong.reset()
        self.integration.reset()
        self.transfer_mechanism.reset()

        self.current_mode = self.config.default_mode
        self.mode_switch_history.clear()
        self.learning_history.clear()
        self.total_learning_sessions = 0
        self.mode_usage_count.clear()

        logger.info("LearningManager reset")
