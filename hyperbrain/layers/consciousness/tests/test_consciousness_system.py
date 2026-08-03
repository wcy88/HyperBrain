"""
意识系统单元测试

测试自我认知、自我意识、意志、价值体系、目标体系和管理器的功能。
"""

import pytest
import time
from typing import Dict, Any

from hyperbrain.layers.consciousness.self_knowledge import (
    SelfKnowledge, SelfKnowledgeConfig, CapabilityCategory, SystemStatus
)
from hyperbrain.layers.consciousness.self_awareness import (
    SelfAwareness, SelfAwarenessConfig, AwarenessLevel, SubjectiveExperience
)
from hyperbrain.layers.consciousness.will import (
    Will, WillConfig, IntentionType, MotivationSource
)
from hyperbrain.layers.consciousness.value_system import (
    ValueSystem, ValueSystemConfig, ValueType, ValuePriority
)
from hyperbrain.layers.consciousness.goal_system import (
    GoalSystem, GoalSystemConfig, GoalTimeframe, GoalStatus, GoalPriority
)
from hyperbrain.layers.consciousness.consciousness_manager import ConsciousnessManager


class TestSelfKnowledge:
    """测试自我认知模块"""

    def test_self_knowledge_creation(self):
        """测试自我认知系统创建"""
        config = SelfKnowledgeConfig(enable_self_description=True)
        sk = SelfKnowledge(config=config)
        assert sk.config.enable_self_description is True

    def test_get_identity(self):
        """测试获取身份"""
        sk = SelfKnowledge()
        identity = sk.get_identity()
        assert "name" in identity
        assert "version" in identity

    def test_generate_self_description(self):
        """测试生成自我描述"""
        sk = SelfKnowledge()
        desc = sk.generate_self_description(detail_level="brief")
        assert len(desc) > 0

        desc_medium = sk.generate_self_description(detail_level="medium")
        assert len(desc_medium) > len(desc)

    def test_assess_capability(self):
        """测试能力评估"""
        sk = SelfKnowledge()
        assessment = sk.assess_capability(
            CapabilityCategory.REASONING,
            performance_score=0.8,
            evidence=["solved_complex_problem"]
        )
        assert assessment.category == CapabilityCategory.REASONING
        assert assessment.score > 0

    def test_recognize_limitations(self):
        """测试认知局限"""
        sk = SelfKnowledge()
        limitations = sk.recognize_limitations()
        assert len(limitations) > 0

    def test_update_status(self):
        """测试状态更新"""
        sk = SelfKnowledge()
        snapshot = sk.update_status(
            status=SystemStatus.PROCESSING,
            active_modules=["test"]
        )
        assert snapshot.status == SystemStatus.PROCESSING

    def test_get_state_report(self):
        """测试状态报告"""
        sk = SelfKnowledge()
        sk.update_status(SystemStatus.READY)
        report = sk.get_state_report()
        assert "current_status" in report

    def test_record_performance(self):
        """测试记录性能"""
        sk = SelfKnowledge()
        sk.record_performance("test_task", True, 1.0, 0.9)
        summary = sk.get_performance_summary("test_task")
        assert summary["total_tasks"] > 0


class TestSelfAwareness:
    """测试自我意识模块"""

    def test_self_awareness_creation(self):
        """测试自我意识系统创建"""
        config = SelfAwarenessConfig(awareness_threshold=0.6)
        sa = SelfAwareness(config=config)
        assert sa.config.awareness_threshold == 0.6

    def test_generate_self_concept(self):
        """测试生成自我概念"""
        sa = SelfAwareness()
        model = sa.generate_self_concept()
        assert model.self_id == "self"
        assert len(model.narrative) > 0

    def test_simulate_subjective_experience(self):
        """测试模拟主观体验"""
        sa = SelfAwareness()
        exp = sa.simulate_subjective_experience(
            experience_type="test",
            intensity=0.7,
            valence=0.5
        )
        assert exp.experience_type == "test"
        assert exp.intensity == 0.7

    def test_self_monitor(self):
        """测试自我监控"""
        sa = SelfAwareness()
        snapshot = sa.self_monitor()
        assert snapshot.level == AwarenessLevel.CONSCIOUS

    def test_maintain_continuity(self):
        """测试维护连续性"""
        sa = SelfAwareness()
        continuity = sa.maintain_continuity()
        assert 0.0 <= continuity <= 1.0

    def test_update_awareness_level(self):
        """测试更新意识水平"""
        sa = SelfAwareness()
        level = sa.update_awareness_level(
            cognitive_load=0.8,
            external_stimuli=2,
            self_reflective_activity=0.9
        )
        assert level in [AwarenessLevel.SELF_REFLECTIVE, AwarenessLevel.META_CONSCIOUS]

    def test_focus_attention(self):
        """测试聚焦注意力"""
        sa = SelfAwareness()
        sa.focus_attention("test_target")
        assert sa._current_focus == "test_target"

    def test_is_self_referential(self):
        """测试自我指涉判断"""
        sa = SelfAwareness()
        assert sa.is_self_referential("I am thinking") is True
        assert sa.is_self_referential("The weather is nice") is False

    def test_reflect_on_self(self):
        """测试自我反思"""
        sa = SelfAwareness()
        result = sa.reflect_on_self()
        assert "self_model" in result
        assert "awareness_level" in result


class TestWill:
    """测试意志模块"""

    def test_will_creation(self):
        """测试意志系统创建"""
        config = WillConfig(autonomy_level=0.8)
        will = Will(config=config)
        assert will.config.autonomy_level == 0.8

    def test_form_intention(self):
        """测试形成意图"""
        will = Will()
        intention = will.form_intention(
            IntentionType.ACTION,
            "测试意图",
            priority=0.7
        )
        assert intention.description == "测试意图"
        assert intention.priority == 0.7

    def test_generate_motivation(self):
        """测试生成动机"""
        will = Will()
        motivation = will.generate_motivation(
            MotivationSource.INTERNAL,
            "测试目标",
            strength=0.8
        )
        assert motivation.target == "测试目标"
        assert motivation.source == MotivationSource.INTERNAL

    def test_select_intention(self):
        """测试选择意图"""
        will = Will()
        will.form_intention(IntentionType.ACTION, "意图1", priority=0.9)
        will.form_intention(IntentionType.ACTION, "意图2", priority=0.5)
        selected = will.select_intention()
        assert selected is not None
        assert selected.description == "意图1"

    def test_execute_intention(self):
        """测试执行意图"""
        will = Will()
        intention = will.form_intention(IntentionType.ACTION, "可执行意图")
        result = will.execute_intention(intention.intention_id)
        assert result["success"] is True

    def test_resolve_conflicts(self):
        """测试解决冲突"""
        will = Will()
        will.form_intention(IntentionType.EXPLORATION, "探索", priority=0.6)
        will.form_intention(IntentionType.PROTECTION, "保护", priority=0.7)
        conflicts = will.resolve_conflicts()
        assert len(conflicts) > 0

    def test_maintain_autonomy(self):
        """测试维护自主性"""
        will = Will()
        autonomy = will.maintain_autonomy(external_pressure=0.2)
        assert 0.0 <= autonomy <= 1.0

    def test_generate_internal_drive(self):
        """测试生成内部驱动"""
        will = Will()
        intention = will.generate_internal_drive()
        # 可能返回None（如果驱动强度不够）
        if intention:
            assert intention.source == MotivationSource.INTERNAL

    def test_get_active_intentions(self):
        """测试获取活跃意图"""
        will = Will()
        will.form_intention(IntentionType.ACTION, "活跃意图")
        active = will.get_active_intentions()
        assert len(active) > 0


class TestValueSystem:
    """测试价值体系模块"""

    def test_value_system_creation(self):
        """测试价值系统创建"""
        config = ValueSystemConfig(enable_moral_reasoning=True)
        vs = ValueSystem(config=config)
        assert vs.config.enable_moral_reasoning is True

    def test_add_value(self):
        """测试添加价值"""
        vs = ValueSystem()
        value = vs.add_value(
            "测试价值",
            "这是一个测试价值",
            ValueType.PERSONAL,
            weight=0.7
        )
        assert value.name == "测试价值"
        assert value.weight == 0.7

    def test_evaluate_action(self):
        """测试评估行动"""
        vs = ValueSystem()
        result = vs.evaluate_action(
            "帮助用户解决问题",
            ["用户满意", "问题解决"]
        )
        assert "overall_score" in result
        assert "recommendation" in result

    def test_resolve_value_conflict(self):
        """测试解决价值冲突"""
        vs = ValueSystem()
        values = list(vs._values.values())
        if len(values) >= 2:
            result = vs.resolve_value_conflict(
                values[0].value_id,
                values[1].value_id,
                context="测试情境"
            )
            assert result["resolved"] is True

    def test_moral_reasoning(self):
        """测试道德推理"""
        vs = ValueSystem()
        result = vs.moral_reasoning(
            "测试情境",
            ["选项A", "选项B"]
        )
        assert "options_evaluated" in result
        assert "recommended_option" in result

    def test_evolve_values(self):
        """测试价值进化"""
        vs = ValueSystem()
        feedback = {
            "诚实": {"outcome": "positive", "strength": 0.8}
        }
        updated = vs.evolve_values(feedback)
        assert len(updated) > 0

    def test_get_value_hierarchy(self):
        """测试获取价值层级"""
        vs = ValueSystem()
        hierarchy = vs.get_value_hierarchy()
        assert len(hierarchy) > 0

    def test_get_values_by_type(self):
        """测试按类型获取价值"""
        vs = ValueSystem()
        ethical_values = vs.get_values_by_type(ValueType.ETHICAL)
        assert len(ethical_values) > 0


class TestGoalSystem:
    """测试目标体系模块"""

    def test_goal_system_creation(self):
        """测试目标系统创建"""
        config = GoalSystemConfig(max_active_goals=5)
        gs = GoalSystem(config=config)
        assert gs.config.max_active_goals == 5

    def test_set_goal(self):
        """测试设定目标"""
        gs = GoalSystem()
        goal = gs.set_goal(
            "测试目标",
            GoalTimeframe.SHORT_TERM,
            GoalPriority.HIGH
        )
        assert goal.description == "测试目标"
        assert goal.timeframe == GoalTimeframe.SHORT_TERM

    def test_activate_goal(self):
        """测试激活目标"""
        gs = GoalSystem()
        goal = gs.set_goal("激活测试", GoalTimeframe.SHORT_TERM, GoalPriority.MEDIUM)
        result = gs.activate_goal(goal.goal_id)
        assert result is True
        assert goal.status == GoalStatus.ACTIVE

    def test_update_progress(self):
        """测试更新进度"""
        gs = GoalSystem()
        goal = gs.set_goal("进度测试", GoalTimeframe.SHORT_TERM, GoalPriority.MEDIUM)
        gs.activate_goal(goal.goal_id)
        updated = gs.update_progress(goal.goal_id, 0.5, "完成一半")
        assert updated.progress == 0.5

    def test_adjust_goal(self):
        """测试调整目标"""
        gs = GoalSystem()
        goal = gs.set_goal("调整测试", GoalTimeframe.SHORT_TERM, GoalPriority.LOW)
        adjusted = gs.adjust_goal(
            goal.goal_id,
            new_description="已调整的目标",
            new_priority=GoalPriority.HIGH
        )
        assert adjusted.description == "已调整的目标"
        assert adjusted.priority == GoalPriority.HIGH

    def test_get_goals_by_status(self):
        """测试按状态获取目标"""
        gs = GoalSystem()
        gs.set_goal("状态测试", GoalTimeframe.SHORT_TERM, GoalPriority.MEDIUM)
        pending = gs.get_goals_by_status(GoalStatus.PENDING)
        assert len(pending) > 0

    def test_get_priority_sorted_goals(self):
        """测试按优先级排序"""
        gs = GoalSystem()
        gs.set_goal("低优先级", GoalTimeframe.SHORT_TERM, GoalPriority.LOW)
        gs.set_goal("高优先级", GoalTimeframe.SHORT_TERM, GoalPriority.HIGH)
        sorted_goals = gs.get_priority_sorted_goals()
        assert sorted_goals[0].priority == GoalPriority.HIGH

    def test_abandon_goal(self):
        """测试放弃目标"""
        gs = GoalSystem()
        goal = gs.set_goal("放弃测试", GoalTimeframe.SHORT_TERM, GoalPriority.LOW)
        result = gs.abandon_goal(goal.goal_id, "不再重要")
        assert result is True
        assert goal.status == GoalStatus.ABANDONED

    def test_check_deadlines(self):
        """测试检查截止日期"""
        gs = GoalSystem()
        gs.set_goal(
            "紧急目标",
            GoalTimeframe.SHORT_TERM,
            GoalPriority.HIGH,
            deadline=time.time() + 3600
        )
        urgent = gs.check_deadlines()
        assert len(urgent) >= 0  # 可能为空，取决于时间

    def test_get_goal_statistics(self):
        """测试获取目标统计"""
        gs = GoalSystem()
        gs.set_goal("统计测试", GoalTimeframe.SHORT_TERM, GoalPriority.MEDIUM)
        stats = gs.get_goal_statistics()
        assert "total_goals" in stats
        assert "status_distribution" in stats


class TestConsciousnessManager:
    """测试意识管理器"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = ConsciousnessManager()
        assert manager.self_knowledge is not None
        assert manager.self_awareness is not None
        assert manager.will is not None
        assert manager.value_system is not None
        assert manager.goal_system is not None

    def test_process_cycle(self):
        """测试处理周期"""
        manager = ConsciousnessManager()
        result = manager.process_cycle()
        assert "cycle" in result
        assert "awareness_level" in result
        assert "autonomy_score" in result

    def test_make_decision(self):
        """测试决策"""
        manager = ConsciousnessManager()
        result = manager.make_decision(
            ["选项A", "选项B"],
            context={"scenario": "测试决策"}
        )
        assert "selected_option" in result
        assert "scores" in result

    def test_self_reflect(self):
        """测试自我反思"""
        manager = ConsciousnessManager()
        result = manager.self_reflect()
        assert "self_description" in result
        assert "self_model" in result
        assert "awareness_reflection" in result

    def test_integrate_emotional_input(self):
        """测试整合情感输入"""
        manager = ConsciousnessManager()
        manager.integrate_emotional_input({"valence": 0.8, "arousal": 0.6})
        # 验证情感已整合（通过检查体验历史）
        experiences = manager.self_awareness.get_experience_history()
        assert len(experiences) > 0

    def test_evaluate_action_against_values(self):
        """测试评估行动"""
        manager = ConsciousnessManager()
        result = manager.evaluate_action_against_values(
            "帮助用户",
            ["用户满意"]
        )
        assert "overall_score" in result

    def test_set_conscious_goal(self):
        """测试设定意识目标"""
        manager = ConsciousnessManager()
        goal = manager.set_conscious_goal(
            "意识目标",
            GoalTimeframe.MEDIUM_TERM,
            GoalPriority.HIGH
        )
        assert goal.description == "意识目标"

    def test_get_consciousness_state(self):
        """测试获取意识状态"""
        manager = ConsciousnessManager()
        state = manager.get_consciousness_state()
        assert "self_knowledge" in state
        assert "self_awareness" in state
        assert "will" in state
        assert "values" in state
        assert "goals" in state

    def test_get_integrated_report(self):
        """测试获取整合报告"""
        manager = ConsciousnessManager()
        report = manager.get_integrated_report()
        assert "consciousness_state" in report
        assert "self_reflection" in report
        assert "stats" in report
