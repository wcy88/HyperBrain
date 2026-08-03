"""
认知管理器 (Cognitive Manager)

统一管理所有认知模块，协调各模块工作，提供统一的认知API。

功能：
- 统一管理所有认知模块
- 协调各模块工作
- 提供统一的认知API
- 与记忆系统交互
"""

from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.memory.memory_manager import MemoryManager
from hyperbrain.layers.memory.memory_models import MemoryType, MemoryItem

from hyperbrain.layers.cognitive.reasoning import (
    ReasoningEngine,
    ReasoningType,
    ReasoningResult,
    Premise,
    Rule,
)
from hyperbrain.layers.cognitive.problem_solving import (
    ProblemSolver,
    ProblemDefinition,
    ProblemType,
    Solution,
    ProblemSolvingResult,
)
from hyperbrain.layers.cognitive.decision_making import (
    DecisionMaker,
    DecisionType,
    Alternative,
    Criterion,
    Goal,
    RiskAssessment,
    DecisionResult,
    DecisionTreeNode,
)
from hyperbrain.layers.cognitive.planning import (
    Planner,
    Plan,
    PlanType,
    PlanTask,
    TaskStatus,
)
from hyperbrain.layers.cognitive.metacognition import (
    MetacognitionMonitor,
    CognitivePerformance,
    BiasType,
)
from hyperbrain.layers.cognitive.abstraction import (
    AbstractionEngine,
    Concept,
    ConceptType,
    Pattern,
    PatternType,
)

logger = get_logger("cognitive.manager")


class CognitiveManager:
    """
    认知管理器 - 认知系统的中央控制器

    统一管理所有认知模块，协调各模块工作，提供统一的认知API，
    并与记忆系统交互。

    Attributes:
        reasoning_engine: 逻辑推理引擎
        problem_solver: 问题解决器
        decision_maker: 决策器
        planner: 规划器
        metacognition: 元认知监控器
        abstraction: 抽象思维引擎
        memory_manager: 记忆管理器（可选）
    """

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        enable_logging: bool = True
    ):
        self.config = get_config().cognitive

        self.reasoning_engine = ReasoningEngine(
            max_chain_length=self.config.max_chain_length,
            confidence_threshold=self.config.confidence_threshold,
            enable_logging=enable_logging
        )
        self.problem_solver = ProblemSolver(enable_logging=enable_logging)
        self.decision_maker = DecisionMaker(enable_logging=enable_logging)
        self.planner = Planner(enable_logging=enable_logging)
        self.metacognition = MetacognitionMonitor(enable_logging=enable_logging)
        self.abstraction = AbstractionEngine(enable_logging=enable_logging)

        self.memory_manager = memory_manager
        self.enable_logging = enable_logging

        if enable_logging:
            logger.info("CognitiveManager initialized")

    # ========== 统一认知API ==========

    def think(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        统一思考接口

        执行完整的认知流程：问题分析 -> 推理 -> 决策 -> 规划

        Args:
            problem: 问题描述
            context: 上下文信息

        Returns:
            Dict[str, Any]: 思考结果
        """
        if self.enable_logging:
            logger.info(f"Starting think process: {problem[:50]}...")

        self.metacognition.monitor_process(
            process_type="think",
            metric_name="start",
            metric_value=1.0
        )

        result = {
            "problem": problem,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }

        stage1 = self._analyze_problem(problem, context)
        result["stages"]["analysis"] = stage1

        stage2 = self._reason_about_problem(problem, stage1)
        result["stages"]["reasoning"] = stage2

        stage3 = self._decide_on_approach(stage1, stage2)
        result["stages"]["decision"] = stage3

        stage4 = self._plan_execution(stage3)
        result["stages"]["planning"] = stage4

        self._store_to_memory(result)

        self.metacognition.assess_performance(
            accuracy=stage2.get("confidence", 0.5),
            speed=0.7,
            efficiency=0.6
        )

        return result

    def reason(
        self,
        premises: List[str],
        reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE,
        question: Optional[str] = None
    ) -> ReasoningResult:
        """
        推理接口

        Args:
            premises: 前提列表
            reasoning_type: 推理类型
            question: 问题

        Returns:
            ReasoningResult: 推理结果
        """
        premise_objects = [
            Premise(statement=p, confidence=1.0) for p in premises
        ]

        if reasoning_type == ReasoningType.DEDUCTIVE:
            result = self.reasoning_engine.deductive_reasoning(
                premise_objects, question=question
            )
        elif reasoning_type == ReasoningType.INDUCTIVE:
            result = self.reasoning_engine.inductive_reasoning(premises)
        elif reasoning_type == ReasoningType.ANALOGICAL:
            result = self.reasoning_engine.analogical_reasoning(
                "source", "target",
                {"feature": "value"}, {"feature": "value"}
            )
        elif reasoning_type == ReasoningType.CHAIN_OF_THOUGHT:
            result = self.reasoning_engine.chain_of_thought(
                question or " ".join(premises)
            )
        else:
            result = self.reasoning_engine.deductive_reasoning(
                premise_objects, question=question
            )

        self._store_reasoning_to_memory(result)
        return result

    def solve_problem(
        self,
        description: str,
        problem_type: ProblemType = ProblemType.WELL_DEFINED,
        goals: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> ProblemSolvingResult:
        """
        问题解决接口

        Args:
            description: 问题描述
            problem_type: 问题类型
            goals: 目标列表
            constraints: 约束条件

        Returns:
            ProblemSolvingResult: 解决结果
        """
        result = self.problem_solver.solve(
            description=description,
            problem_type=problem_type,
            goals=goals,
            constraints=constraints
        )

        self._store_problem_result_to_memory(result)
        return result

    def decide(
        self,
        alternatives: List[Alternative],
        decision_type: DecisionType = DecisionType.MULTI_CRITERIA,
        criteria: Optional[List[Criterion]] = None,
        goals: Optional[List[Goal]] = None
    ) -> DecisionResult:
        """
        决策接口

        Args:
            alternatives: 可选方案
            decision_type: 决策类型
            criteria: 决策准则
            goals: 目标

        Returns:
            DecisionResult: 决策结果
        """
        if decision_type == DecisionType.GOAL_BASED:
            result = self.decision_maker.goal_based_decision(alternatives, goals)
        elif decision_type == DecisionType.MULTI_CRITERIA:
            result = self.decision_maker.multi_criteria_decision(alternatives, criteria)
        elif decision_type == DecisionType.RISK_BASED:
            result = self.decision_maker.risk_based_decision(alternatives)
        elif decision_type == DecisionType.PROBABILISTIC:
            result = self.decision_maker.probabilistic_decision(alternatives)
        else:
            result = self.decision_maker.multi_criteria_decision(alternatives, criteria)

        self._store_decision_to_memory(result)
        return result

    def plan(
        self,
        name: str,
        description: str,
        plan_type: PlanType = PlanType.SHORT_TERM,
        goals: Optional[List[str]] = None,
        tasks: Optional[List[Dict[str, Any]]] = None
    ) -> Plan:
        """
        规划接口

        Args:
            name: 计划名称
            description: 计划描述
            plan_type: 计划类型
            goals: 目标列表
            tasks: 任务列表

        Returns:
            Plan: 创建的计划
        """
        plan = self.planner.create_plan(
            name=name,
            description=description,
            plan_type=plan_type,
            goals=goals
        )

        if tasks:
            for task_data in tasks:
                self.planner.add_task(
                    plan_id=plan.plan_id,
                    name=task_data["name"],
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", 0.5),
                    estimated_duration=task_data.get("estimated_duration", 1.0)
                )

        self._store_plan_to_memory(plan)
        return plan

    def monitor_cognition(self) -> Dict[str, Any]:
        """
        监控认知状态

        Returns:
            Dict[str, Any]: 认知状态
        """
        state = self.metacognition.get_cognitive_state()
        stats = self.metacognition.get_monitoring_stats()

        return {
            "cognitive_state": state,
            "monitoring_stats": stats,
            "module_stats": {
                "reasoning": self.reasoning_engine.get_stats(),
                "problem_solving": self.problem_solver.get_stats(),
                "decision_making": self.decision_maker.get_stats(),
                "planning": self.planner.get_stats(),
                "abstraction": self.abstraction.get_stats()
            }
        }

    def reflect(self) -> Dict[str, Any]:
        """
        元认知反思

        Returns:
            Dict[str, Any]: 反思结果
        """
        questions = self.metacognition.generate_self_questions(
            category="strategy",
            triggered_by="periodic_reflection"
        )

        performance = (
            self.metacognition.performance_history[-1]
            if self.metacognition.performance_history
            else None
        )

        biases = self.metacognition.detect_bias(
            reasoning_process={},
            evidence=[]
        )

        return {
            "questions": [q.model_dump() for q in questions],
            "performance": performance.model_dump() if performance else None,
            "detected_biases": [b.model_dump() for b in biases],
            "suggestions": self._generate_reflection_suggestions()
        }

    def abstract(
        self,
        data: List[Any],
        operation: str = "pattern_recognition",
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        抽象思维接口

        Args:
            data: 数据
            operation: 操作类型
            context: 上下文

        Returns:
            Dict[str, Any]: 抽象结果
        """
        if operation == "pattern_recognition":
            patterns = self.abstraction.recognize_pattern(data)
            return {"patterns": [p.model_dump() for p in patterns]}
        elif operation == "concept_formation":
            concept = self.abstraction.form_concept(
                name=context or "新概念",
                examples=[str(d) for d in data]
            )
            return {"concept": concept.model_dump()}
        elif operation == "generalization":
            gen = self.abstraction.generalize([str(d) for d in data])
            return {"generalization": gen.model_dump() if gen else None}
        elif operation == "symbolize":
            mappings = [
                self.abstraction.abstract_and_symbolize(str(d), context or "general")
                for d in data[:5]
            ]
            return {"mappings": [m.model_dump() for m in mappings]}
        else:
            patterns = self.abstraction.recognize_pattern(data)
            return {"patterns": [p.model_dump() for p in patterns]}

    # ========== 记忆交互 ==========

    def set_memory_manager(self, memory_manager: MemoryManager) -> None:
        """设置记忆管理器"""
        self.memory_manager = memory_manager
        logger.info("Memory manager connected")

    def retrieve_relevant_knowledge(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识

        Args:
            query: 查询
            top_k: 返回数量

        Returns:
            List[Dict[str, Any]]: 相关知识
        """
        if not self.memory_manager:
            return []

        results = self.memory_manager.retrieve(query=query, top_k=top_k)
        return [
            {
                "content": r.memory.content,
                "type": r.memory.memory_type.value,
                "score": r.combined_score
            }
            for r in results
        ]

    def learn_from_experience(
        self,
        experience: Dict[str, Any],
        importance: float = 0.5
    ) -> Optional[MemoryItem]:
        """
        从经验中学习

        Args:
            experience: 经验数据
            importance: 重要性

        Returns:
            Optional[MemoryItem]: 存储的记忆
        """
        if not self.memory_manager:
            return None

        memory = self.memory_manager.store(
            content=experience,
            memory_type=MemoryType.DECLARATIVE,
            importance=importance,
            context_tags=["cognitive", "experience"]
        )

        logger.info(f"Learned from experience: {memory.id}")
        return memory

    # ========== 内部方法 ==========

    def _analyze_problem(
        self,
        problem: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析问题"""
        problem_def = self.problem_solver.define_problem(
            description=problem,
            context=context or {}
        )

        analysis = self.problem_solver.analyze_problem(problem_def.problem_id)

        return {
            "problem_id": problem_def.problem_id,
            "analysis": analysis,
            "complexity": analysis.get("difficulty_score", 0.5)
        }

    def _reason_about_problem(
        self,
        problem: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对问题进行推理"""
        result = self.reasoning_engine.chain_of_thought(problem)

        return {
            "conclusion": result.conclusion,
            "confidence": result.confidence,
            "steps_count": len(result.steps),
            "reasoning_type": result.reasoning_type.value
        }

    def _decide_on_approach(
        self,
        analysis: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """决定处理方法"""
        alternatives = [
            Alternative(
                name="direct_approach",
                description="直接方法",
                values={"speed": 0.8, "accuracy": 0.6}
            ),
            Alternative(
                name="careful_approach",
                description="谨慎方法",
                values={"speed": 0.4, "accuracy": 0.9}
            ),
            Alternative(
                name="balanced_approach",
                description="平衡方法",
                values={"speed": 0.6, "accuracy": 0.7}
            )
        ]

        criteria = [
            Criterion(name="speed", weight=0.4),
            Criterion(name="accuracy", weight=0.6)
        ]

        result = self.decision_maker.multi_criteria_decision(
            alternatives=alternatives,
            criteria=criteria
        )

        return {
            "selected_approach": result.selected_alternative.name if result.selected_alternative else "default",
            "confidence": result.confidence,
            "reasoning": result.reasoning
        }

    def _plan_execution(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """规划执行"""
        plan = self.planner.create_plan(
            name="execution_plan",
            description="执行选定的方案",
            plan_type=PlanType.SHORT_TERM
        )

        self.planner.add_task(plan.plan_id, "准备")
        self.planner.add_task(plan.plan_id, "执行")
        self.planner.add_task(plan.plan_id, "验证")

        return {
            "plan_id": plan.plan_id,
            "task_count": len(plan.tasks),
            "execution_order": self.planner.get_execution_order(plan.plan_id)
        }

    def _store_to_memory(self, data: Dict[str, Any]) -> None:
        """存储到记忆"""
        if self.memory_manager:
            self.memory_manager.store(
                content=data,
                memory_type=MemoryType.DECLARATIVE,
                importance=0.6,
                context_tags=["cognitive", "think_result"]
            )

    def _store_reasoning_to_memory(self, result: ReasoningResult) -> None:
        """存储推理结果到记忆"""
        if self.memory_manager:
            self.memory_manager.store(
                content={
                    "conclusion": result.conclusion,
                    "confidence": result.confidence,
                    "type": "reasoning"
                },
                memory_type=MemoryType.DECLARATIVE,
                importance=result.confidence,
                context_tags=["cognitive", "reasoning"]
            )

    def _store_problem_result_to_memory(self, result: ProblemSolvingResult) -> None:
        """存储问题解决结果到记忆"""
        if self.memory_manager:
            self.memory_manager.store(
                content={
                    "problem_id": result.problem_id,
                    "successful": result.is_successful,
                    "lessons": result.lessons_learned
                },
                memory_type=MemoryType.DECLARATIVE,
                importance=0.7 if result.is_successful else 0.5,
                context_tags=["cognitive", "problem_solving"]
            )

    def _store_decision_to_memory(self, result: DecisionResult) -> None:
        """存储决策结果到记忆"""
        if self.memory_manager:
            self.memory_manager.store(
                content={
                    "decision_type": result.decision_type.value,
                    "selected": result.selected_alternative.name if result.selected_alternative else None,
                    "confidence": result.confidence
                },
                memory_type=MemoryType.DECLARATIVE,
                importance=result.confidence,
                context_tags=["cognitive", "decision"]
            )

    def _store_plan_to_memory(self, plan: Plan) -> None:
        """存储计划到记忆"""
        if self.memory_manager:
            self.memory_manager.store(
                content={
                    "plan_id": plan.plan_id,
                    "name": plan.name,
                    "type": plan.plan_type.value,
                    "task_count": len(plan.tasks)
                },
                memory_type=MemoryType.DECLARATIVE,
                importance=0.5,
                context_tags=["cognitive", "planning"]
            )

    def _generate_reflection_suggestions(self) -> List[str]:
        """生成反思建议"""
        suggestions = []

        stats = self.metacognition.get_monitoring_stats()
        if stats["alert_rate"] > 0.3:
            suggestions.append("认知过程中警报率较高，建议放慢速度")

        if stats["unanswered_questions"] > 5:
            suggestions.append("存在未回答的自我提问，建议进行反思")

        if stats["bias_detections"] > 0:
            suggestions.append("检测到认知偏差，建议重新审视推理过程")

        if not suggestions:
            suggestions.append("认知状态良好，继续保持")

        return suggestions

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取整体统计信息"""
        return {
            "reasoning": self.reasoning_engine.get_stats(),
            "problem_solving": self.problem_solver.get_stats(),
            "decision_making": self.decision_maker.get_stats(),
            "planning": self.planner.get_stats(),
            "metacognition": self.metacognition.get_monitoring_stats(),
            "abstraction": self.abstraction.get_stats(),
            "memory_connected": self.memory_manager is not None
        }

    def __repr__(self) -> str:
        return (
            f"CognitiveManager("
            f"reasoning={self.reasoning_engine.get_stats()['total_reasoning_count']}, "
            f"problems={self.problem_solver.get_stats()['total_problems']}, "
            f"decisions={self.decision_maker.get_stats()['total_decisions']}, "
            f"plans={self.planner.get_stats()['total_plans']})"
        )
