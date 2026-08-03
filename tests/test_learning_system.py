"""
学习系统单元测试

测试所有学习模块的功能：
- 婴儿学习引擎
- 儿童学习引擎
- 成人学习引擎
- 终身学习机制
- 知识整合机制
- 能力迁移机制
- 学习管理器
"""

import pytest
from datetime import datetime

from hyperbrain.layers.learning.infant_learning import (
    InfantLearningEngine, InfantLearningConfig,
    ExplorationResult, TrialResult, ImitationRecord, CuriosityState
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
    KnowledgeCategory, ConflictType, ClassificationResult
)
from hyperbrain.layers.learning.transfer_learning import (
    TransferLearningMechanism, TransferLearningConfig,
    Domain, KnowledgeMapping, SkillTransfer, CrossDomainApplication,
    DomainType, TransferType
)
from hyperbrain.layers.learning.learning_manager import (
    LearningManager, LearningManagerConfig,
    LearningMode, LearningContext, LearningResult
)


# ========== 婴儿学习引擎测试 ==========

class TestInfantLearningEngine:
    """测试婴儿学习引擎"""

    def setup_method(self):
        self.engine = InfantLearningEngine()

    def test_explore_list(self):
        """测试列表探索"""
        data = [1, 2, 3, 1, 2, 3]
        result = self.engine.explore(data, "test_context")
        assert isinstance(result, ExplorationResult)
        assert result.pattern_type == "sequential"
        assert result.confidence > 0

    def test_explore_dict(self):
        """测试字典探索"""
        data = {"a": 1, "b": 2, "c": 3}
        result = self.engine.explore(data, "test_context")
        assert isinstance(result, ExplorationResult)
        assert result.pattern_type == "structural"

    def test_explore_string(self):
        """测试字符串探索"""
        data = "hello world hello world"
        result = self.engine.explore(data, "test_context")
        assert isinstance(result, ExplorationResult)
        assert result.novelty_score >= 0.0

    def test_trial(self):
        """测试试错学习"""
        def callback():
            return ("success", 0.8)

        result = self.engine.trial("test_action", callback)
        assert isinstance(result, TrialResult)
        assert result.success is True
        assert result.reward == 0.8

    def test_select_action(self):
        """测试动作选择"""
        actions = ["a", "b", "c"]
        action = self.engine.select_action(actions, "random")
        assert action in actions

    def test_action_value_update(self):
        """测试动作价值更新"""
        self.engine.trial("action1", lambda: ("good", 1.0))
        value = self.engine.get_action_value("action1")
        assert value > 0

    def test_observe_and_imitate(self):
        """测试观察和模仿"""
        self.engine.observe("wave hand", "greeting")
        result = self.engine.imitate("wave hand", "wave hand")
        assert isinstance(result, ImitationRecord)
        assert result.similarity_score > 0

    def test_recognize_pattern(self):
        """测试模式识别"""
        data = [1, 2, 3]
        self.engine.explore(data)
        matches = self.engine.recognize_pattern([1, 2, 3])
        assert isinstance(matches, list)

    def test_generalize(self):
        """测试泛化"""
        examples = [
            {"color": "red", "shape": "circle"},
            {"color": "blue", "shape": "circle"},
        ]
        pattern = self.engine.generalize(examples)
        assert pattern is not None

    def test_curiosity_state(self):
        """测试好奇心状态"""
        state = self.engine.get_curiosity_state()
        assert isinstance(state, CuriosityState)
        assert 0.0 <= state.exploration_rate <= 1.0

    def test_get_stats(self):
        """测试统计信息"""
        stats = self.engine.get_stats()
        assert "total_explorations" in stats
        assert "total_trials" in stats

    def test_reset(self):
        """测试重置"""
        self.engine.explore([1, 2, 3])
        self.engine.reset()
        assert len(self.engine.patterns) == 0
        assert self.engine.total_explorations == 0


# ========== 儿童学习引擎测试 ==========

class TestChildLearningEngine:
    """测试儿童学习引擎"""

    def setup_method(self):
        self.engine = ChildLearningEngine()

    def test_learn_concept(self):
        """测试概念学习"""
        examples = [
            {"color": "red", "shape": "round"},
            {"color": "green", "shape": "round"},
        ]
        result = self.engine.learn_concept("apple", examples)
        assert isinstance(result, ConceptLearningResult)
        assert result.concept_name == "apple"
        assert result.confidence > 0

    def test_learn_concept_with_negatives(self):
        """测试带负例的概念学习"""
        positives = [{"has_wheels": True, "has_engine": True}]
        negatives = [{"has_wheels": True, "has_engine": False}]
        result = self.engine.learn_concept("car", positives, negatives)
        assert result.confidence > 0.3

    def test_classify(self):
        """测试分类"""
        examples = [
            {"color": "red", "shape": "round"},
            {"color": "green", "shape": "round"},
        ]
        self.engine.learn_concept("round_thing", examples)
        scores = self.engine.classify({"color": "red", "shape": "round"})
        assert isinstance(scores, list)

    def test_learn_word(self):
        """测试词汇学习"""
        result = self.engine.learn_word("hello", "greeting context")
        assert isinstance(result, LanguageLearningResult)
        assert result.word_or_phrase == "hello"
        assert result.mastery_level > 0

    def test_review_word(self):
        """测试词汇复习"""
        self.engine.learn_word("hello")
        result = self.engine.learn_word("hello", "new context")
        assert result.mastery_level > 0.2

    def test_learn_grammar(self):
        """测试语法学习"""
        result = self.engine.learn_grammar(
            "SVO",
            ["I eat apple", "You drink water"],
            "Subject-Verb-Object"
        )
        assert "examples" in result
        assert result["confidence"] > 0

    def test_ask_question(self):
        """测试提问"""
        result = self.engine.ask_question("What is this?", "what")
        assert isinstance(result, QuestionRecord)
        assert result.category == "what"

    def test_answer_question(self):
        """测试回答问题"""
        question = self.engine.ask_question("What is this?")
        updated = self.engine.answer_question(question.question_id, "This is a test", 0.9)
        assert updated is not None
        assert updated.satisfaction == 0.9

    def test_generalize_knowledge(self):
        """测试知识泛化"""
        self.engine.learn_concept("animal", [{"can_move": True, "is_alive": True}])
        result = self.engine.generalize_knowledge("animal", "robot")
        assert isinstance(result, GeneralizationResult)

    def test_learn_association(self):
        """测试联想学习"""
        result = self.engine.learn_association("fire", "hot", "causality")
        assert isinstance(result, AssociationLink)
        assert result.association_type == "causality"

    def test_get_associated(self):
        """测试获取关联"""
        self.engine.learn_association("dog", "animal", "similarity")
        associated = self.engine.get_associated("dog")
        assert len(associated) > 0

    def test_find_association_paths(self):
        """测试查找联想路径"""
        self.engine.learn_association("a", "b", "similarity")
        self.engine.learn_association("b", "c", "similarity")
        paths = self.engine.find_association_paths("a", "c", max_depth=3)
        assert isinstance(paths, list)

    def test_get_stats(self):
        """测试统计"""
        stats = self.engine.get_stats()
        assert "total_concepts_learned" in stats
        assert "vocabulary_size" in stats

    def test_reset(self):
        """测试重置"""
        self.engine.learn_word("test")
        self.engine.reset()
        assert len(self.engine.vocabulary) == 0


# ========== 成人学习引擎测试 ==========

class TestAdultLearningEngine:
    """测试成人学习引擎"""

    def setup_method(self):
        self.engine = AdultLearningEngine()

    def test_learn_structured(self):
        """测试结构化学习"""
        result = self.engine.learn_structured(
            "Python",
            "Python is a programming language",
            KnowledgeDomain.TECHNOLOGY,
            key_points=["interpreted", "high-level"],
            prerequisites=["basic_computer"]
        )
        assert isinstance(result, StructuredKnowledge)
        assert result.topic == "Python"
        assert result.confidence > 0

    def test_get_knowledge(self):
        """测试获取知识"""
        self.engine.learn_structured("Test", "Test content")
        knowledge = self.engine.get_knowledge("Test")
        assert knowledge is not None
        assert knowledge.content == "Test content"

    def test_get_learning_path(self):
        """测试学习路径"""
        self.engine.learn_structured("A", "Content A")
        self.engine.learn_structured("B", "Content B", prerequisites=["A"])
        self.engine.learn_structured("C", "Content C", prerequisites=["B"])
        path = self.engine.get_learning_path("C")
        assert "A" in path
        assert "B" in path
        assert "C" in path

    def test_review_knowledge(self):
        """测试复习知识"""
        self.engine.learn_structured("Review", "Content")
        knowledge = self.engine.review_knowledge("Review")
        assert knowledge is not None
        assert knowledge.review_count > 0
        assert knowledge.mastery_level > 0

    def test_logical_learn(self):
        """测试逻辑学习"""
        result = self.engine.logical_learn(
            ["All humans are mortal", "Socrates is human"],
            "Socrates is mortal",
            "deductive"
        )
        assert isinstance(result, LogicalInference)
        assert result.validity > 0

    def test_get_inference_stats(self):
        """测试推理统计"""
        self.engine.logical_learn(["A"], "B", "deductive")
        stats = self.engine.get_inference_stats()
        assert stats["total"] > 0

    def test_critically_evaluate(self):
        """测试批判性评估"""
        result = self.engine.critically_evaluate(
            "Climate change",
            ["Temperatures are rising", "Ice caps are melting"],
            "Scientific research"
        )
        assert isinstance(result, CriticalEvaluation)
        assert 0.0 <= result.overall_credibility <= 1.0

    def test_get_critical_stats(self):
        """测试批判性统计"""
        self.engine.critically_evaluate("Test", ["evidence"])
        stats = self.engine.get_critical_stats()
        assert stats["total"] > 0

    def test_transfer_knowledge(self):
        """测试知识迁移"""
        self.engine.learn_structured("Math", "Mathematics", KnowledgeDomain.MATHEMATICS)
        self.engine.learn_structured("Physics", "Physics", KnowledgeDomain.SCIENCE)
        result = self.engine.transfer_knowledge("Math", "Physics", "Equations")
        assert isinstance(result, KnowledgeTransfer)

    def test_get_transfer_stats(self):
        """测试迁移统计"""
        stats = self.engine.get_transfer_stats()
        assert "total" in stats

    def test_reflect_on_learning(self):
        """测试元学习"""
        result = self.engine.reflect_on_learning(
            "spaced_repetition",
            "studying",
            0.8
        )
        assert isinstance(result, MetaLearningInsight)
        assert result.effectiveness_score > 0

    def test_get_best_strategies(self):
        """测试获取最佳策略"""
        self.engine.reflect_on_learning("strategy1", "context", 0.9)
        self.engine.reflect_on_learning("strategy2", "context", 0.5)
        best = self.engine.get_best_strategies(top_k=2)
        assert len(best) > 0
        assert best[0][1] >= best[1][1]

    def test_get_stats(self):
        """测试统计"""
        stats = self.engine.get_stats()
        assert "total_knowledge_acquired" in stats
        assert "avg_knowledge_mastery" in stats

    def test_reset(self):
        """测试重置"""
        self.engine.learn_structured("Test", "Content")
        self.engine.reset()
        assert len(self.engine.knowledge_base) == 0


# ========== 终身学习机制测试 ==========

class TestLifelongLearningMechanism:
    """测试终身学习机制"""

    def setup_method(self):
        self.mechanism = LifelongLearningMechanism()

    def test_record_learning_event(self):
        """测试记录学习事件"""
        event = self.mechanism.record_learning_event(
            "exploration",
            "Discovered new pattern",
            importance=0.8
        )
        assert isinstance(event, LearningEvent)
        assert event.event_type == "exploration"

    def test_get_recent_events(self):
        """测试获取最近事件"""
        self.mechanism.record_learning_event("test", "content")
        events = self.mechanism.get_recent_events(limit=10)
        assert len(events) > 0

    def test_get_learning_rate(self):
        """测试学习速率"""
        rate = self.mechanism.get_learning_rate()
        assert rate >= 0.0

    def test_integrate_knowledge(self):
        """测试知识整合"""
        result = self.mechanism.integrate_knowledge(
            "new_knowledge",
            ["related1", "related2"]
        )
        assert "integration_id" in result

    def test_schedule_review(self):
        """测试安排复习"""
        record = self.mechanism.schedule_review("knowledge_1")
        assert record.review_count == 1
        assert record.review_interval > 0

    def test_get_due_reviews(self):
        """测试获取到期复习"""
        self.mechanism.schedule_review("knowledge_1")
        due = self.mechanism.get_due_reviews()
        assert isinstance(due, list)

    def test_get_forgetting_risk(self):
        """测试遗忘风险"""
        risk = self.mechanism.get_forgetting_risk("unknown")
        assert risk == 1.0

    def test_consolidate_knowledge(self):
        """测试知识巩固"""
        result = self.mechanism.consolidate_knowledge()
        assert "events_processed" in result

    def test_track_progress(self):
        """测试进度跟踪"""
        progress = self.mechanism.track_progress("math", 0.5, 1.0)
        assert isinstance(progress, LearningProgress)
        assert progress.domain == "math"

    def test_get_progress(self):
        """测试获取进度"""
        self.mechanism.track_progress("test", 0.3)
        progress = self.mechanism.get_progress("test")
        assert progress is not None

    def test_assess_effectiveness(self):
        """测试效果评估"""
        result = self.mechanism.assess_effectiveness()
        assert isinstance(result, LearningEffectiveness)
        assert 0.0 <= result.overall_score <= 1.0

    def test_get_effectiveness_trend(self):
        """测试效果趋势"""
        trend = self.mechanism.get_effectiveness_trend()
        assert "trend" in trend

    def test_get_stats(self):
        """测试统计"""
        stats = self.mechanism.get_stats()
        assert "total_events" in stats
        assert "overall_progress" in stats

    def test_reset(self):
        """测试重置"""
        self.mechanism.record_learning_event("test", "content")
        self.mechanism.reset()
        assert len(self.mechanism.event_history) == 0


# ========== 知识整合机制测试 ==========

class TestKnowledgeIntegrationMechanism:
    """测试知识整合机制"""

    def setup_method(self):
        self.mechanism = KnowledgeIntegrationMechanism()

    def test_classify_knowledge(self):
        """测试知识分类"""
        result = self.mechanism.classify_knowledge(
            "Python is a programming language"
        )
        assert isinstance(result, ClassificationResult)
        assert result.confidence > 0

    def test_add_knowledge(self):
        """测试添加知识"""
        node = self.mechanism.add_knowledge(
            "Python is a programming language",
            category=KnowledgeCategory.FACT
        )
        assert isinstance(node, KnowledgeNode)
        assert node.content == "Python is a programming language"

    def test_add_duplicate_knowledge(self):
        """测试添加重复知识"""
        self.mechanism.add_knowledge("Unique content")
        node2 = self.mechanism.add_knowledge("Unique content")
        assert node2.access_count >= 1

    def test_search_knowledge(self):
        """测试搜索知识"""
        self.mechanism.add_knowledge("Python programming")
        results = self.mechanism.search_knowledge("Python")
        assert len(results) > 0

    def test_get_knowledge_by_category(self):
        """测试按分类获取"""
        self.mechanism.add_knowledge("Test fact", KnowledgeCategory.FACT)
        facts = self.mechanism.get_knowledge_by_category(KnowledgeCategory.FACT)
        assert len(facts) > 0

    def test_create_relation(self):
        """测试创建关联"""
        node1 = self.mechanism.add_knowledge("Node 1")
        node2 = self.mechanism.add_knowledge("Node 2")
        edge = self.mechanism.create_relation(node1.node_id, node2.node_id, "related", 0.8)
        assert isinstance(edge, KnowledgeEdge)
        assert edge.strength == 0.8

    def test_get_related_knowledge(self):
        """测试获取相关知识"""
        node1 = self.mechanism.add_knowledge("Python language")
        node2 = self.mechanism.add_knowledge("Python programming")
        self.mechanism.create_relation(node1.node_id, node2.node_id)
        related = self.mechanism.get_related_knowledge(node1.node_id)
        assert len(related) > 0

    def test_detect_conflict(self):
        """测试冲突检测"""
        self.mechanism.add_knowledge("The sky is blue today")
        self.mechanism.add_knowledge("The sky is not blue today")
        conflicts = self.mechanism.get_conflicts(unresolved_only=True)
        assert len(conflicts) > 0

    def test_resolve_conflict(self):
        """测试冲突解决"""
        node1 = self.mechanism.add_knowledge("A is true")
        node2 = self.mechanism.add_knowledge("A is not true")
        conflicts = self.mechanism.get_conflicts(unresolved_only=True)
        if conflicts:
            resolved = self.mechanism.resolve_conflict(
                conflicts[0].conflict_id,
                "Prefer first statement",
                node1.node_id
            )
            assert resolved.resolved is True

    def test_build_knowledge_graph(self):
        """测试构建知识图谱"""
        self.mechanism.add_knowledge("Node A")
        graph = self.mechanism.build_knowledge_graph()
        assert "nodes" in graph
        assert "edges" in graph
        assert "statistics" in graph

    def test_update_knowledge(self):
        """测试更新知识"""
        node = self.mechanism.add_knowledge("Old content")
        updated = self.mechanism.update_knowledge(
            node.node_id,
            new_content="New content",
            new_confidence=0.9
        )
        assert updated.content == "New content"
        assert updated.confidence == 0.9

    def test_archive_knowledge(self):
        """测试归档知识"""
        node = self.mechanism.add_knowledge("To archive")
        archive = self.mechanism.archive_knowledge(node.node_id, "Test archive")
        assert archive is not None

    def test_merge_knowledge(self):
        """测试合并知识"""
        node1 = self.mechanism.add_knowledge("Content A")
        node2 = self.mechanism.add_knowledge("Content B")
        merged = self.mechanism.merge_knowledge(node1.node_id, node2.node_id)
        assert merged is not None
        assert "Content A" in merged.content

    def test_get_stats(self):
        """测试统计"""
        stats = self.mechanism.get_stats()
        assert "total_nodes_created" in stats
        assert "active_nodes" in stats

    def test_reset(self):
        """测试重置"""
        self.mechanism.add_knowledge("Test")
        self.mechanism.reset()
        assert len(self.mechanism.knowledge_nodes) == 0


# ========== 能力迁移机制测试 ==========

class TestTransferLearningMechanism:
    """测试能力迁移机制"""

    def setup_method(self):
        self.mechanism = TransferLearningMechanism()

    def test_register_domain(self):
        """测试注册领域"""
        domain = self.mechanism.register_domain(
            "Mathematics",
            DomainType.MATHEMATICS,
            key_features=["numbers", "equations"]
        )
        assert isinstance(domain, Domain)
        assert domain.name == "Mathematics"

    def test_get_domain(self):
        """测试获取领域"""
        self.mechanism.register_domain("Test")
        domain = self.mechanism.get_domain("Test")
        assert domain is not None

    def test_calculate_domain_similarity(self):
        """测试领域相似度"""
        self.mechanism.register_domain("A", key_features=["x", "y"])
        self.mechanism.register_domain("B", key_features=["x", "z"])
        similarity = self.mechanism.calculate_domain_similarity("A", "B")
        assert 0.0 <= similarity <= 1.0

    def test_identify_transfer_path(self):
        """测试识别迁移路径"""
        self.mechanism.register_domain("A")
        self.mechanism.register_domain("B")
        paths = self.mechanism.identify_transfer_path("A", "B")
        assert isinstance(paths, list)

    def test_create_mapping(self):
        """测试创建映射"""
        self.mechanism.register_domain("Source")
        self.mechanism.register_domain("Target")
        mapping = self.mechanism.create_mapping(
            "knowledge A",
            "knowledge B",
            "Source",
            "Target"
        )
        assert isinstance(mapping, KnowledgeMapping)

    def test_find_mappings(self):
        """测试查找映射"""
        self.mechanism.register_domain("S")
        self.mechanism.register_domain("T")
        self.mechanism.create_mapping("a", "b", "S", "T")
        mappings = self.mechanism.find_mappings("S", "T")
        assert len(mappings) > 0

    def test_apply_mapping(self):
        """测试应用映射"""
        self.mechanism.register_domain("S")
        self.mechanism.register_domain("T")
        mapping = self.mechanism.create_mapping("a", "b", "S", "T")
        result = self.mechanism.apply_mapping(mapping.mapping_id, "input")
        assert result["success"] is True

    def test_assess_transfer(self):
        """测试迁移评估"""
        self.mechanism.register_domain("Math")
        self.mechanism.register_domain("Physics")
        result = self.mechanism.assess_transfer("problem_solving", "Math", "Physics")
        assert isinstance(result, SkillTransfer)
        assert result.transfer_score >= 0.0

    def test_execute_transfer(self):
        """测试执行迁移"""
        self.mechanism.register_domain("A")
        self.mechanism.register_domain("B")
        transfer = self.mechanism.assess_transfer("skill", "A", "B")
        result = self.mechanism.execute_transfer(transfer.transfer_id)
        assert isinstance(result.success, bool)

    def test_apply_cross_domain(self):
        """测试跨领域应用"""
        self.mechanism.register_domain("A")
        self.mechanism.register_domain("B")
        app = self.mechanism.apply_cross_domain("A", "B", "Test application")
        assert isinstance(app, CrossDomainApplication)

    def test_evaluate_application(self):
        """测试评估应用"""
        self.mechanism.register_domain("A")
        self.mechanism.register_domain("B")
        app = self.mechanism.apply_cross_domain("A", "B", "Test")
        updated = self.mechanism.evaluate_application(
            app.application_id, 0.8, "Good result"
        )
        assert updated.effectiveness == 0.8

    def test_start_monitoring(self):
        """测试开始监控"""
        monitor = self.mechanism.start_monitoring("transfer_1")
        assert monitor.transfer_id == "transfer_1"

    def test_update_monitor(self):
        """测试更新监控"""
        monitor = self.mechanism.start_monitoring("transfer_1", expected_metric=0.7)
        updated = self.mechanism.update_monitor(monitor.monitor_id, 0.8)
        assert updated.status == "exceeded"

    def test_get_monitor_summary(self):
        """测试监控摘要"""
        self.mechanism.start_monitoring("t1")
        summary = self.mechanism.get_monitor_summary()
        assert "total_monitors" in summary

    def test_get_stats(self):
        """测试统计"""
        stats = self.mechanism.get_stats()
        assert "total_domains" in stats
        assert "transfer_success_rate" in stats

    def test_reset(self):
        """测试重置"""
        self.mechanism.register_domain("Test")
        self.mechanism.reset()
        assert len(self.mechanism.domains) == 0


# ========== 学习管理器测试 ==========

class TestLearningManager:
    """测试学习管理器"""

    def setup_method(self):
        self.manager = LearningManager()

    def test_initialization(self):
        """测试初始化"""
        assert self.manager.current_mode == LearningMode.AUTOMATIC
        assert self.manager.infant_engine is not None
        assert self.manager.child_engine is not None
        assert self.manager.adult_engine is not None

    def test_select_mode_infant(self):
        """测试选择婴儿模式"""
        context = LearningContext(novelty=0.9, prior_knowledge=0.1, complexity=0.2)
        mode = self.manager.select_mode(context)
        assert mode == LearningMode.INFANT

    def test_select_mode_child(self):
        """测试选择儿童模式"""
        context = LearningContext(novelty=0.5, prior_knowledge=0.5, complexity=0.5)
        mode = self.manager.select_mode(context)
        assert mode == LearningMode.CHILD

    def test_select_mode_adult(self):
        """测试选择成人模式"""
        context = LearningContext(novelty=0.2, prior_knowledge=0.8, complexity=0.8)
        mode = self.manager.select_mode(context)
        assert mode == LearningMode.ADULT

    def test_set_mode(self):
        """测试手动设置模式"""
        self.manager.set_mode(LearningMode.ADULT)
        assert self.manager.get_current_mode() == LearningMode.ADULT

    def test_learn_infant_mode(self):
        """测试婴儿模式学习"""
        context = LearningContext(mode=LearningMode.INFANT)
        result = self.manager.learn([1, 2, 3], context)
        assert isinstance(result, LearningResult)
        assert result.mode_used == LearningMode.INFANT

    def test_learn_child_mode(self):
        """测试儿童模式学习"""
        context = LearningContext(mode=LearningMode.CHILD)
        result = self.manager.learn("hello", context, is_language=True)
        assert isinstance(result, LearningResult)
        assert result.mode_used == LearningMode.CHILD

    def test_learn_adult_mode(self):
        """测试成人模式学习"""
        context = LearningContext(mode=LearningMode.ADULT)
        result = self.manager.learn("Python is a language", context, topic="Python")
        assert isinstance(result, LearningResult)
        assert result.mode_used == LearningMode.ADULT

    def test_explore(self):
        """测试探索"""
        result = self.manager.explore([1, 2, 1, 2])
        assert isinstance(result, ExplorationResult)

    def test_learn_concept(self):
        """测试概念学习"""
        result = self.manager.learn_concept("test", [{"a": 1}, {"a": 2}])
        assert isinstance(result, ConceptLearningResult)

    def test_learn_structured(self):
        """测试结构化学习"""
        result = self.manager.learn_structured("Topic", "Content")
        assert isinstance(result, StructuredKnowledge)

    def test_evaluate(self):
        """测试评估"""
        result = self.manager.evaluate("Subject", ["evidence"])
        assert isinstance(result, CriticalEvaluation)

    def test_transfer(self):
        """测试迁移"""
        self.manager.transfer_mechanism.register_domain("A")
        self.manager.transfer_mechanism.register_domain("B")
        result = self.manager.transfer("skill", "A", "B")
        assert isinstance(result, SkillTransfer)

    def test_integrate_knowledge(self):
        """测试知识整合"""
        result = self.manager.integrate_knowledge("Test knowledge")
        assert isinstance(result, KnowledgeNode)

    def test_find_knowledge(self):
        """测试查找知识"""
        self.manager.integrate_knowledge("Python programming")
        results = self.manager.find_knowledge("Python")
        assert len(results) > 0

    def test_track_progress(self):
        """测试进度跟踪"""
        result = self.manager.track_progress("math", 0.5)
        assert isinstance(result, LearningProgress)

    def test_assess_learning(self):
        """测试学习评估"""
        result = self.manager.assess_learning()
        assert isinstance(result, LearningEffectiveness)

    def test_get_stats(self):
        """测试统计"""
        stats = self.manager.get_stats()
        assert "total_learning_sessions" in stats
        assert "infant_engine" in stats
        assert "child_engine" in stats
        assert "adult_engine" in stats

    def test_get_learning_report(self):
        """测试学习报告"""
        report = self.manager.get_learning_report()
        assert "report_time" in report
        assert "summary" in report
        assert "recommendations" in report

    def test_sync_with_memory(self):
        """测试与记忆同步"""
        class MockMemory:
            def store(self, content, metadata=None):
                pass

        result = self.manager.sync_with_memory(MockMemory())
        assert result["status"] == "success"

    def test_sync_with_cognition(self):
        """测试与认知同步"""
        class MockCognition:
            def add_concept(self, name, description, confidence):
                pass

            def add_knowledge(self, topic, content, domain):
                pass

        result = self.manager.sync_with_cognition(MockCognition())
        assert result["status"] == "success"

    def test_reset(self):
        """测试重置"""
        self.manager.learn("test", LearningContext(mode=LearningMode.ADULT))
        self.manager.reset()
        assert self.manager.total_learning_sessions == 0
        assert len(self.manager.learning_history) == 0

    def test_mode_switch_history(self):
        """测试模式切换历史"""
        self.manager.set_mode(LearningMode.INFANT)
        self.manager.set_mode(LearningMode.ADULT)
        assert len(self.manager.mode_switch_history) >= 2

    def test_learning_history(self):
        """测试学习历史"""
        initial_count = len(self.manager.learning_history)
        self.manager.learn("test content", LearningContext(mode=LearningMode.CHILD))
        assert len(self.manager.learning_history) == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
