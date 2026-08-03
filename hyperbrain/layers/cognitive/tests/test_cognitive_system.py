"""
认知系统单元测试

测试所有认知模块的核心功能。
"""

import pytest
from datetime import datetime

from hyperbrain.layers.cognitive import (
    ReasoningEngine,
    ReasoningType,
    Premise,
    Rule,
    ProblemSolver,
    ProblemType,
    EvaluationCriteria,
    DecisionMaker,
    DecisionType,
    Alternative,
    Criterion,
    Goal,
    RiskAssessment,
    Planner,
    PlanType,
    TaskStatus,
    DependencyType,
    MetacognitionMonitor,
    BiasType,
    AbstractionEngine,
    ConceptType,
    PatternType,
    CognitiveManager,
)


class TestReasoningEngine:
    """测试逻辑推理模块"""

    def setup_method(self):
        self.engine = ReasoningEngine(enable_logging=False)

    def test_deductive_reasoning(self):
        premises = [
            Premise(statement="所有人都会死", confidence=1.0),
            Premise(statement="苏格拉底是人", confidence=1.0)
        ]
        result = self.engine.deductive_reasoning(premises, question="苏格拉底会死吗？")

        assert result.conclusion != ""
        assert result.confidence > 0
        assert result.reasoning_type == ReasoningType.DEDUCTIVE
        assert len(result.steps) > 0

    def test_inductive_reasoning(self):
        observations = [
            "天鹅A是白色的",
            "天鹅B是白色的",
            "天鹅C是白色的"
        ]
        result = self.engine.inductive_reasoning(observations)

        assert result.conclusion != ""
        assert result.confidence > 0
        assert result.reasoning_type == ReasoningType.INDUCTIVE

    def test_analogical_reasoning(self):
        result = self.engine.analogical_reasoning(
            source_domain="水波",
            target_domain="声波",
            source_features={"传播": "介质", "反射": "是"},
            target_features={"传播": "介质", "反射": "是"}
        )

        assert result.conclusion != ""
        assert result.reasoning_type == ReasoningType.ANALOGICAL

    def test_abductive_reasoning(self):
        result = self.engine.abductive_reasoning(
            observation="草地湿了",
            possible_explanations=["下雨了", "洒水器开了", "有人浇水"]
        )

        assert result.conclusion != ""
        assert result.confidence > 0
        assert result.reasoning_type == ReasoningType.ABDUCTIVE

    def test_chain_of_thought(self):
        result = self.engine.chain_of_thought("如何计算2+3*4？")

        assert result.conclusion != ""
        assert len(result.steps) > 0
        assert result.reasoning_type == ReasoningType.CHAIN_OF_THOUGHT

    def test_causal_reasoning(self):
        events = ["下雨", "地面湿", "行人打伞"]
        result = self.engine.causal_reasoning(events)

        assert result.conclusion != ""
        assert result.reasoning_type == ReasoningType.CAUSAL

    def test_confidence_evaluation(self):
        result = self.engine.deductive_reasoning(
            [Premise(statement="测试", confidence=0.9)]
        )
        adjusted = self.engine.evaluate_confidence(result)
        assert 0.0 <= adjusted <= 1.0

    def test_add_and_remove_rule(self):
        rule = Rule(name="测试规则", condition="A", conclusion="B")
        self.engine.add_rule(rule)
        assert rule.rule_id in self.engine.rules

        success = self.engine.remove_rule(rule.rule_id)
        assert success
        assert rule.rule_id not in self.engine.rules

    def test_get_stats(self):
        stats = self.engine.get_stats()
        assert "total_reasoning_count" in stats
        assert "rule_count" in stats


class TestProblemSolver:
    """测试问题解决模块"""

    def setup_method(self):
        self.solver = ProblemSolver(enable_logging=False)

    def test_define_problem(self):
        problem = self.solver.define_problem(
            description="测试问题",
            problem_type=ProblemType.WELL_DEFINED,
            goals=["目标1", "目标2"]
        )

        assert problem.description == "测试问题"
        assert problem.problem_type == ProblemType.WELL_DEFINED
        assert len(problem.goals) == 2

    def test_analyze_problem(self):
        problem = self.solver.define_problem("分析测试")
        analysis = self.solver.analyze_problem(problem.problem_id)

        assert "problem_id" in analysis
        assert "difficulty_score" in analysis
        assert analysis["problem_id"] == problem.problem_id

    def test_generate_solutions(self):
        problem = self.solver.define_problem("生成方案测试")
        solutions = self.solver.generate_solutions(problem.problem_id)

        assert len(solutions) > 0
        assert all(s.status.value == "generated" for s in solutions)

    def test_evaluate_solutions(self):
        problem = self.solver.define_problem("评估测试")
        self.solver.generate_solutions(problem.problem_id)
        evaluated = self.solver.evaluate_solutions(problem.problem_id)

        assert len(evaluated) > 0
        assert all(s.score >= 0.0 for s in evaluated)

    def test_select_solution(self):
        problem = self.solver.define_problem("选择测试")
        self.solver.generate_solutions(problem.problem_id)
        self.solver.evaluate_solutions(problem.problem_id)
        selected = self.solver.select_solution(problem.problem_id)

        assert selected is not None
        assert selected.status.value == "selected"

    def test_full_solve(self):
        result = self.solver.solve(
            description="完整流程测试",
            problem_type=ProblemType.WELL_DEFINED,
            goals=["完成测试"]
        )

        assert result.problem_id != ""
        assert result.selected_solution is not None
        assert result.execution_result is not None

    def test_get_stats(self):
        stats = self.solver.get_stats()
        assert "total_problems" in stats
        assert "success_rate" in stats


class TestDecisionMaker:
    """测试决策模块"""

    def setup_method(self):
        self.dm = DecisionMaker(enable_logging=False)

    def test_goal_based_decision(self):
        goal = Goal(description="提高效率", priority=0.8)
        self.dm.add_goal(goal)

        alternatives = [
            Alternative(name="A", description="方案A", expected_outcomes=["提高效率"]),
            Alternative(name="B", description="方案B", expected_outcomes=["降低成本"])
        ]

        result = self.dm.goal_based_decision(alternatives)
        assert result.selected_alternative is not None
        assert result.decision_type == DecisionType.GOAL_BASED

    def test_value_based_decision(self):
        alternatives = [
            Alternative(name="A", values={"成本": 0.8, "质量": 0.6}),
            Alternative(name="B", values={"成本": 0.5, "质量": 0.9})
        ]

        result = self.dm.value_based_decision(
            alternatives,
            values={"成本": 0.4, "质量": 0.6}
        )
        assert result.selected_alternative is not None
        assert result.decision_type == DecisionType.VALUE_BASED

    def test_risk_based_decision(self):
        alternatives = [
            Alternative(name="安全", values={"收益": 0.6}),
            Alternative(name="冒险", values={"收益": 0.9})
        ]

        risks = {
            alternatives[1].alternative_id: [
                RiskAssessment(description="高风险", probability=0.8, impact=0.9)
            ]
        }

        result = self.dm.risk_based_decision(alternatives, risk_assessments=risks)
        assert result.selected_alternative is not None
        assert result.decision_type == DecisionType.RISK_BASED

    def test_multi_criteria_decision(self):
        criterion = Criterion(name="效率", weight=0.6)
        self.dm.add_criterion(criterion)

        alternatives = [
            Alternative(name="A", values={"效率": 0.8}),
            Alternative(name="B", values={"效率": 0.9})
        ]

        result = self.dm.multi_criteria_decision(alternatives)
        assert result.selected_alternative is not None
        assert result.decision_type == DecisionType.MULTI_CRITERIA

    def test_probabilistic_decision(self):
        alternatives = [
            Alternative(
                name="A",
                values={"成功": 100, "失败": 0},
                probabilities={"成功": 0.7, "失败": 0.3}
            )
        ]

        result = self.dm.probabilistic_decision(alternatives)
        assert result.decision_type == DecisionType.PROBABILISTIC
        assert result.expected_value >= 0

    def test_decision_tree(self):
        tree = self.dm.build_decision_tree("根", [
            {"name": "选择A", "type": "decision", "value": 10},
            {"name": "选择B", "type": "decision", "value": 20}
        ])

        assert tree.name == "根"
        assert len(tree.children) == 2

        ev = self.dm.evaluate_decision_tree(tree)
        assert ev == 20

    def test_get_stats(self):
        stats = self.dm.get_stats()
        assert "total_decisions" in stats
        assert "criteria_count" in stats


class TestPlanner:
    """测试规划模块"""

    def setup_method(self):
        self.planner = Planner(enable_logging=False)

    def test_create_plan(self):
        plan = self.planner.create_plan(
            name="测试计划",
            description="测试描述",
            plan_type=PlanType.SHORT_TERM
        )

        assert plan.name == "测试计划"
        assert plan.plan_type == PlanType.SHORT_TERM

    def test_add_task(self):
        plan = self.planner.create_plan("任务测试", "", PlanType.SHORT_TERM)
        task = self.planner.add_task(plan.plan_id, "任务1", priority=0.8)

        assert task is not None
        assert task.name == "任务1"
        assert task.priority == 0.8

    def test_add_dependency(self):
        plan = self.planner.create_plan("依赖测试", "", PlanType.SHORT_TERM)
        task1 = self.planner.add_task(plan.plan_id, "任务1")
        task2 = self.planner.add_task(plan.plan_id, "任务2")

        dep = self.planner.add_dependency(
            plan.plan_id,
            task1.task_id,
            task2.task_id
        )

        assert dep is not None
        assert dep.from_task_id == task1.task_id
        assert dep.to_task_id == task2.task_id

    def test_execution_order(self):
        plan = self.planner.create_plan("排序测试", "", PlanType.SHORT_TERM)
        t1 = self.planner.add_task(plan.plan_id, "A")
        t2 = self.planner.add_task(plan.plan_id, "B")
        t3 = self.planner.add_task(plan.plan_id, "C")

        self.planner.add_dependency(plan.plan_id, t1.task_id, t2.task_id)
        self.planner.add_dependency(plan.plan_id, t2.task_id, t3.task_id)

        order = self.planner.get_execution_order(plan.plan_id)
        assert len(order) == 3
        assert order.index(t1.task_id) < order.index(t2.task_id)
        assert order.index(t2.task_id) < order.index(t3.task_id)

    def test_critical_path(self):
        plan = self.planner.create_plan("关键路径测试", "", PlanType.SHORT_TERM)
        t1 = self.planner.add_task(plan.plan_id, "A", estimated_duration=2.0)
        t2 = self.planner.add_task(plan.plan_id, "B", estimated_duration=3.0)

        self.planner.add_dependency(plan.plan_id, t1.task_id, t2.task_id)

        cp = self.planner.calculate_critical_path(plan.plan_id)
        assert len(cp) >= 1

    def test_decompose_task(self):
        plan = self.planner.create_plan("分解测试", "", PlanType.SHORT_TERM)
        parent = self.planner.add_task(plan.plan_id, "父任务")
        subs = self.planner.decompose_task(
            plan.plan_id,
            parent.task_id,
            ["子任务1", "子任务2"]
        )

        assert len(subs) == 2
        assert all(s.parent_task_id == parent.task_id for s in subs)

    def test_plan_progress(self):
        plan = self.planner.create_plan("进度测试", "", PlanType.SHORT_TERM)
        self.planner.add_task(plan.plan_id, "任务1")
        self.planner.add_task(plan.plan_id, "任务2")

        progress = self.planner.get_plan_progress(plan.plan_id)
        assert progress["total_tasks"] == 2
        assert progress["progress"] == 0.0

    def test_get_stats(self):
        stats = self.planner.get_stats()
        assert "total_plans" in stats
        assert "total_tasks" in stats


class TestMetacognitionMonitor:
    """测试元认知模块"""

    def setup_method(self):
        self.monitor = MetacognitionMonitor(enable_logging=False)

    def test_monitor_process(self):
        event = self.monitor.monitor_process(
            process_type="test",
            metric_name="accuracy",
            metric_value=0.9
        )

        assert event.process_type == "test"
        assert event.metric_value == 0.9
        assert not event.is_alert

    def test_monitor_alert(self):
        event = self.monitor.monitor_process(
            process_type="test",
            metric_name="accuracy",
            metric_value=0.1,
            threshold=0.3
        )

        assert event.is_alert

    def test_assess_performance(self):
        perf = self.monitor.assess_performance(
            accuracy=0.8,
            speed=0.7,
            efficiency=0.75
        )

        assert perf.accuracy == 0.8
        assert perf.overall_score > 0
        assert 0.0 <= perf.overall_score <= 1.0

    def test_generate_self_questions(self):
        questions = self.monitor.generate_self_questions(category="strategy")
        assert len(questions) > 0
        assert all(q.category == "strategy" for q in questions)

    def test_answer_self_question(self):
        questions = self.monitor.generate_self_questions()
        qid = questions[0].question_id

        success = self.monitor.answer_self_question(qid, "测试答案")
        assert success

        question = next(q for q in self.monitor.self_questions if q.question_id == qid)
        assert question.is_answered
        assert question.answer == "测试答案"

    def test_detect_bias(self):
        reasoning = {
            "supporting_evidence": ["A", "B", "C", "D"],
            "opposing_evidence": ["E"]
        }
        biases = self.monitor.detect_bias(reasoning, [])

        assert len(biases) > 0
        assert any(b.bias_type == BiasType.CONFIRMATION for b in biases)

    def test_adjust_strategy(self):
        perf = self.monitor.assess_performance(accuracy=0.4, speed=0.3)
        adjustment = self.monitor.adjust_strategy("当前策略", perf)

        assert adjustment is not None
        assert adjustment.original_strategy == "当前策略"
        assert adjustment.adjusted_strategy != "当前策略"

    def test_get_cognitive_state(self):
        self.monitor.assess_performance(accuracy=0.9, speed=0.85)
        state = self.monitor.get_cognitive_state()

        assert "state" in state
        assert "average_score" in state

    def test_get_monitoring_stats(self):
        stats = self.monitor.get_monitoring_stats()
        assert "total_events" in stats
        assert "alert_rate" in stats


class TestAbstractionEngine:
    """测试抽象思维模块"""

    def setup_method(self):
        self.engine = AbstractionEngine(enable_logging=False)

    def test_form_concept(self):
        concept = self.engine.form_concept(
            name="鸟类",
            examples=["麻雀会飞", "燕子会飞", "鹰会飞"],
            concept_type=ConceptType.CONCRETE
        )

        assert concept.name == "鸟类"
        assert len(concept.examples) == 3
        assert concept.confidence > 0

    def test_generalize(self):
        gen = self.engine.generalize([
            "猫是哺乳动物",
            "狗是哺乳动物",
            "牛是哺乳动物"
        ])

        assert gen is not None
        assert gen.coverage > 0
        assert gen.confidence > 0

    def test_abstract_and_symbolize(self):
        mapping = self.engine.abstract_and_symbolize(
            "人工智能系统",
            context="tech"
        )

        assert mapping.original == "人工智能系统"
        assert mapping.symbol != ""

    def test_recognize_pattern(self):
        data = [1, 2, 1, 2, 1, 2, 1, 2]
        patterns = self.engine.recognize_pattern(data, PatternType.SEQUENTIAL)

        assert len(patterns) > 0
        assert all(p.confidence > 0 for p in patterns)

    def test_create_knowledge_representation(self):
        facts = [
            {"subject": "猫", "predicate": "是", "object": "哺乳动物"},
            {"subject": "狗", "predicate": "是", "object": "哺乳动物"}
        ]
        kr = self.engine.create_knowledge_representation("哺乳动物", facts)

        assert kr.subject == "哺乳动物"
        assert len(kr.relationships) > 0

    def test_compare_concepts(self):
        c1 = self.engine.form_concept("A", ["x", "y"], attributes={"color": "red"})
        c2 = self.engine.form_concept("B", ["x", "z"], attributes={"color": "red"})

        comparison = self.engine.compare_concepts(c1.concept_id, c2.concept_id)
        assert "similarity" in comparison
        assert comparison["similarity"] >= 0

    def test_get_concept_hierarchy(self):
        self.engine.form_concept("动物", ["猫", "狗"])
        hierarchy = self.engine.get_concept_hierarchy()

        assert "children" in hierarchy

    def test_get_stats(self):
        stats = self.engine.get_stats()
        assert "total_concepts" in stats
        assert "total_patterns" in stats


class TestCognitiveManager:
    """测试认知管理器"""

    def setup_method(self):
        self.cm = CognitiveManager(enable_logging=False)

    def test_think(self):
        result = self.cm.think("测试问题")

        assert "problem" in result
        assert "stages" in result
        assert "analysis" in result["stages"]
        assert "reasoning" in result["stages"]
        assert "decision" in result["stages"]
        assert "planning" in result["stages"]

    def test_reason(self):
        result = self.cm.reason(
            ["前提1", "前提2"],
            ReasoningType.DEDUCTIVE,
            "问题？"
        )

        assert result.conclusion != ""
        assert result.reasoning_type == ReasoningType.DEDUCTIVE

    def test_solve_problem(self):
        result = self.cm.solve_problem(
            "测试问题",
            ProblemType.WELL_DEFINED
        )

        assert result.problem_id != ""
        assert result.selected_solution is not None

    def test_decide(self):
        alternatives = [
            Alternative(name="A", values={"x": 0.8}),
            Alternative(name="B", values={"x": 0.6})
        ]
        criteria = [Criterion(name="x", weight=1.0)]

        result = self.cm.decide(alternatives, DecisionType.MULTI_CRITERIA, criteria)

        assert result.selected_alternative is not None

    def test_plan(self):
        plan = self.cm.plan(
            "测试计划",
            "描述",
            PlanType.SHORT_TERM,
            tasks=[{"name": "任务1"}, {"name": "任务2"}]
        )

        assert plan.name == "测试计划"
        assert len(plan.tasks) == 2

    def test_monitor_cognition(self):
        state = self.cm.monitor_cognition()

        assert "cognitive_state" in state
        assert "monitoring_stats" in state
        assert "module_stats" in state

    def test_reflect(self):
        result = self.cm.reflect()

        assert "questions" in result
        assert "suggestions" in result

    def test_abstract(self):
        result = self.cm.abstract(
            [1, 2, 1, 2, 1, 2],
            operation="pattern_recognition"
        )

        assert "patterns" in result

    def test_get_stats(self):
        stats = self.cm.get_stats()

        assert "reasoning" in stats
        assert "problem_solving" in stats
        assert "decision_making" in stats
        assert "planning" in stats
        assert "metacognition" in stats
        assert "abstraction" in stats

    def test_memory_integration(self):
        assert self.cm.memory_manager is None

        self.cm.set_memory_manager(None)
        knowledge = self.cm.retrieve_relevant_knowledge("测试")
        assert knowledge == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
