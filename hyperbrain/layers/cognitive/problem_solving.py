"""
问题解决模块 (Problem Solving Module)

实现完整的问题解决流程：
- 问题定义和分析
- 方案生成：头脑风暴多种解决方案
- 方案评估：基于约束条件和目标评估
- 方案选择：选择最优方案
- 执行和验证
"""

import uuid
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.problem_solving")


class ProblemType(str, Enum):
    """问题类型枚举"""
    WELL_DEFINED = "well_defined"        # 良定义问题
    ILL_DEFINED = "ill_defined"          # 不良定义问题
    OPTIMIZATION = "optimization"        # 优化问题
    DECISION = "decision"                # 决策问题
    DIAGNOSIS = "diagnosis"              # 诊断问题
    DESIGN = "design"                    # 设计问题
    PLANNING = "planning"                # 规划问题


class SolutionStatus(str, Enum):
    """解决方案状态"""
    GENERATED = "generated"              # 已生成
    EVALUATED = "evaluated"              # 已评估
    SELECTED = "selected"                # 已选择
    EXECUTED = "executed"                # 已执行
    VERIFIED = "verified"                # 已验证
    FAILED = "failed"                    # 失败
    ABANDONED = "abandoned"              # 已放弃


class ConstraintType(str, Enum):
    """约束类型"""
    HARD = "hard"                        # 硬约束（必须满足）
    SOFT = "soft"                        # 软约束（尽量满足）
    TEMPORAL = "temporal"                # 时间约束
    RESOURCE = "resource"                # 资源约束
    QUALITY = "quality"                  # 质量约束


class ProblemDefinition(BaseModel):
    """问题定义模型"""
    problem_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(...)
    problem_type: ProblemType = Field(default=ProblemType.WELL_DEFINED)
    goals: List[str] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("urgency", "complexity")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Solution(BaseModel):
    """解决方案模型"""
    solution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(...)
    steps: List[str] = Field(default_factory=list)
    estimated_cost: float = Field(default=0.0)
    estimated_time: float = Field(default=0.0)
    required_resources: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    status: SolutionStatus = Field(default=SolutionStatus.GENERATED)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    constraint_satisfaction: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class EvaluationCriteria(BaseModel):
    """评估标准模型"""
    criteria_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    constraint_type: ConstraintType = Field(default=ConstraintType.SOFT)
    target_value: Optional[float] = Field(default=None)
    min_value: Optional[float] = Field(default=None)
    max_value: Optional[float] = Field(default=None)
    evaluator: Optional[Callable[[Any], float]] = Field(default=None)

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ProblemSolvingResult(BaseModel):
    """问题解决结果模型"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_id: str = Field(...)
    selected_solution: Optional[Solution] = Field(default=None)
    all_solutions: List[Solution] = Field(default_factory=list)
    execution_result: Optional[Dict[str, Any]] = Field(default=None)
    is_successful: bool = Field(default=False)
    lessons_learned: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: float = Field(default=0.0)


class ProblemSolver:
    """
    问题解决器

    实现完整的问题解决流程，从问题定义到方案验证。

    Attributes:
        problem_definitions: 问题定义缓存
        solutions: 解决方案缓存
        evaluation_criteria: 评估标准库
        solving_history: 解决历史
    """

    def __init__(
        self,
        max_solutions: int = 10,
        enable_logging: bool = True
    ):
        self.problem_definitions: Dict[str, ProblemDefinition] = {}
        self.solutions: Dict[str, List[Solution]] = {}
        self.evaluation_criteria: Dict[str, EvaluationCriteria] = {}
        self.solving_history: List[ProblemSolvingResult] = []
        self.max_solutions = max_solutions
        self.enable_logging = enable_logging

        if enable_logging:
            logger.info("ProblemSolver initialized")

    def define_problem(
        self,
        description: str,
        problem_type: ProblemType = ProblemType.WELL_DEFINED,
        goals: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        urgency: float = 0.5,
        complexity: float = 0.5
    ) -> ProblemDefinition:
        """
        定义问题

        Args:
            description: 问题描述
            problem_type: 问题类型
            goals: 目标列表
            constraints: 约束条件
            context: 上下文信息
            urgency: 紧急程度
            complexity: 复杂度

        Returns:
            ProblemDefinition: 问题定义
        """
        problem = ProblemDefinition(
            description=description,
            problem_type=problem_type,
            goals=goals or [],
            constraints=constraints or [],
            context=context or {},
            urgency=urgency,
            complexity=complexity
        )

        self.problem_definitions[problem.problem_id] = problem
        logger.info(f"Problem defined: {problem.problem_id}, type={problem_type.value}")
        return problem

    def analyze_problem(self, problem_id: str) -> Dict[str, Any]:
        """
        分析问题

        Args:
            problem_id: 问题ID

        Returns:
            Dict[str, Any]: 分析结果
        """
        problem = self.problem_definitions.get(problem_id)
        if not problem:
            return {"error": "Problem not found"}

        analysis = {
            "problem_id": problem_id,
            "description": problem.description,
            "type": problem.problem_type.value,
            "goal_count": len(problem.goals),
            "constraint_count": len(problem.constraints),
            "urgency": problem.urgency,
            "complexity": problem.complexity,
            "is_well_defined": problem.problem_type == ProblemType.WELL_DEFINED,
            "has_clear_goals": len(problem.goals) > 0,
            "has_constraints": len(problem.constraints) > 0,
            "difficulty_score": self._calculate_difficulty(problem)
        }

        if problem.constraints:
            hard_constraints = [c for c in problem.constraints if c.get("type") == "hard"]
            soft_constraints = [c for c in problem.constraints if c.get("type") == "soft"]
            analysis["hard_constraint_count"] = len(hard_constraints)
            analysis["soft_constraint_count"] = len(soft_constraints)

        return analysis

    def generate_solutions(
        self,
        problem_id: str,
        strategy: str = "diverse",
        custom_generator: Optional[Callable[[ProblemDefinition], List[Solution]]] = None
    ) -> List[Solution]:
        """
        生成解决方案

        Args:
            problem_id: 问题ID
            strategy: 生成策略 (diverse, greedy, random)
            custom_generator: 自定义生成器

        Returns:
            List[Solution]: 解决方案列表
        """
        problem = self.problem_definitions.get(problem_id)
        if not problem:
            logger.error(f"Problem not found: {problem_id}")
            return []

        if custom_generator:
            solutions = custom_generator(problem)
        else:
            solutions = self._default_solution_generation(problem, strategy)

        for solution in solutions:
            solution.status = SolutionStatus.GENERATED

        self.solutions[problem_id] = solutions
        logger.info(f"Generated {len(solutions)} solutions for problem {problem_id}")
        return solutions

    def evaluate_solutions(
        self,
        problem_id: str,
        criteria: Optional[List[EvaluationCriteria]] = None,
        custom_evaluator: Optional[Callable[[Solution], Dict[str, float]]] = None
    ) -> List[Solution]:
        """
        评估解决方案

        Args:
            problem_id: 问题ID
            criteria: 评估标准列表
            custom_evaluator: 自定义评估函数

        Returns:
            List[Solution]: 评估后的解决方案
        """
        solutions = self.solutions.get(problem_id, [])
        if not solutions:
            return []

        problem = self.problem_definitions.get(problem_id)
        eval_criteria = criteria or list(self.evaluation_criteria.values())

        for solution in solutions:
            if custom_evaluator:
                scores = custom_evaluator(solution)
                solution.score = sum(scores.values()) / len(scores) if scores else 0.0
            else:
                solution.score = self._default_evaluation(solution, problem, eval_criteria)

            solution.status = SolutionStatus.EVALUATED

        solutions.sort(key=lambda s: s.score, reverse=True)
        logger.info(f"Evaluated {len(solutions)} solutions for problem {problem_id}")
        return solutions

    def select_solution(
        self,
        problem_id: str,
        selection_strategy: str = "best_score",
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Solution]:
        """
        选择最优方案

        Args:
            problem_id: 问题ID
            selection_strategy: 选择策略
            constraints: 额外约束

        Returns:
            Optional[Solution]: 选中的方案
        """
        solutions = self.solutions.get(problem_id, [])
        if not solutions:
            return None

        evaluated = [s for s in solutions if s.status == SolutionStatus.EVALUATED]
        if not evaluated:
            evaluated = self.evaluate_solutions(problem_id)

        if selection_strategy == "best_score":
            selected = max(evaluated, key=lambda s: s.score) if evaluated else None
        elif selection_strategy == "min_cost":
            selected = min(evaluated, key=lambda s: s.estimated_cost) if evaluated else None
        elif selection_strategy == "min_risk":
            selected = min(evaluated, key=lambda s: len(s.risks)) if evaluated else None
        elif selection_strategy == "balanced":
            selected = self._balanced_selection(evaluated)
        else:
            selected = evaluated[0] if evaluated else None

        if selected:
            selected.status = SolutionStatus.SELECTED
            for s in evaluated:
                if s.solution_id != selected.solution_id:
                    s.status = SolutionStatus.ABANDONED

            logger.info(f"Selected solution {selected.solution_id} for problem {problem_id}")

        return selected

    def execute_solution(
        self,
        problem_id: str,
        solution_id: Optional[str] = None,
        executor: Optional[Callable[[Solution], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        执行解决方案

        Args:
            problem_id: 问题ID
            solution_id: 方案ID（可选，默认选择最优）
            executor: 执行函数

        Returns:
            Dict[str, Any]: 执行结果
        """
        solutions = self.solutions.get(problem_id, [])
        if not solutions:
            return {"success": False, "error": "No solutions available"}

        if solution_id:
            solution = next((s for s in solutions if s.solution_id == solution_id), None)
        else:
            solution = next((s for s in solutions if s.status == SolutionStatus.SELECTED), None)
            if not solution:
                solution = self.select_solution(problem_id)

        if not solution:
            return {"success": False, "error": "No solution selected"}

        solution.status = SolutionStatus.EXECUTED

        if executor:
            result = executor(solution)
        else:
            result = self._default_execution(solution)

        logger.info(f"Executed solution {solution.solution_id} for problem {problem_id}")
        return result

    def verify_solution(
        self,
        problem_id: str,
        solution_id: Optional[str] = None,
        verifier: Optional[Callable[[Solution, Dict[str, Any]], bool]] = None
    ) -> ProblemSolvingResult:
        """
        验证解决方案

        Args:
            problem_id: 问题ID
            solution_id: 方案ID
            verifier: 验证函数

        Returns:
            ProblemSolvingResult: 解决结果
        """
        start_time = datetime.now()
        solutions = self.solutions.get(problem_id, [])

        if solution_id:
            solution = next((s for s in solutions if s.solution_id == solution_id), None)
        else:
            solution = next((s for s in solutions if s.status == SolutionStatus.EXECUTED), None)

        problem = self.problem_definitions.get(problem_id)

        if not solution or not problem:
            return ProblemSolvingResult(
                problem_id=problem_id,
                is_successful=False
            )

        if verifier:
            is_successful = verifier(solution, problem.context)
        else:
            is_successful = self._default_verification(solution, problem)

        solution.status = SolutionStatus.VERIFIED if is_successful else SolutionStatus.FAILED

        lessons = []
        if is_successful:
            lessons.append(f"方案 '{solution.description}' 成功解决问题")
            if solution.score > 0.8:
                lessons.append("高分方案，可作为未来参考")
        else:
            lessons.append(f"方案 '{solution.description}' 未能完全解决问题")
            lessons.append("需要重新评估问题定义或生成新方案")

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = ProblemSolvingResult(
            problem_id=problem_id,
            selected_solution=solution,
            all_solutions=solutions,
            is_successful=is_successful,
            lessons_learned=lessons,
            duration_ms=duration
        )

        self.solving_history.append(result)
        logger.info(f"Verified solution for problem {problem_id}: success={is_successful}")
        return result

    def solve(
        self,
        description: str,
        problem_type: ProblemType = ProblemType.WELL_DEFINED,
        goals: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ProblemSolvingResult:
        """
        完整的问题解决流程

        Args:
            description: 问题描述
            problem_type: 问题类型
            goals: 目标列表
            constraints: 约束条件
            context: 上下文

        Returns:
            ProblemSolvingResult: 解决结果
        """
        start_time = datetime.now()

        problem = self.define_problem(
            description=description,
            problem_type=problem_type,
            goals=goals,
            constraints=constraints,
            context=context
        )

        self.analyze_problem(problem.problem_id)

        solutions = self.generate_solutions(problem.problem_id)
        if not solutions:
            return ProblemSolvingResult(
                problem_id=problem.problem_id,
                is_successful=False,
                lessons_learned=["无法生成解决方案"]
            )

        self.evaluate_solutions(problem.problem_id)
        selected = self.select_solution(problem.problem_id)

        if not selected:
            return ProblemSolvingResult(
                problem_id=problem.problem_id,
                all_solutions=solutions,
                is_successful=False,
                lessons_learned=["无法选择合适方案"]
            )

        execution_result = self.execute_solution(problem.problem_id)

        result = self.verify_solution(problem.problem_id)
        result.execution_result = execution_result

        duration = (datetime.now() - start_time).total_seconds() * 1000
        result.duration_ms = duration

        return result

    def add_evaluation_criteria(self, criteria: EvaluationCriteria) -> None:
        """添加评估标准"""
        self.evaluation_criteria[criteria.criteria_id] = criteria
        logger.debug(f"Added evaluation criteria: {criteria.name}")

    def get_solving_history(
        self,
        problem_type: Optional[ProblemType] = None,
        limit: int = 100
    ) -> List[ProblemSolvingResult]:
        """获取解决历史"""
        results = self.solving_history
        if problem_type:
            results = [
                r for r in results
                if r.problem_id in self.problem_definitions
                and self.problem_definitions[r.problem_id].problem_type == problem_type
            ]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.solving_history)
        successful = sum(1 for r in self.solving_history if r.is_successful)

        type_counts: Dict[str, int] = {}
        for problem in self.problem_definitions.values():
            pt = problem.problem_type.value
            type_counts[pt] = type_counts.get(pt, 0) + 1

        return {
            "total_problems": len(self.problem_definitions),
            "total_attempts": total,
            "successful_solutions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "problem_type_distribution": type_counts,
            "evaluation_criteria_count": len(self.evaluation_criteria)
        }

    def _calculate_difficulty(self, problem: ProblemDefinition) -> float:
        """计算问题难度"""
        base = problem.complexity
        goal_factor = min(1.0, len(problem.goals) * 0.1)
        constraint_factor = min(1.0, len(problem.constraints) * 0.1)
        return min(1.0, (base + goal_factor + constraint_factor) / 3)

    def _default_solution_generation(
        self,
        problem: ProblemDefinition,
        strategy: str
    ) -> List[Solution]:
        """默认方案生成"""
        solutions = []

        base_solutions = [
            f"直接方法: {problem.description}",
            f"分步方法: 将问题分解为子任务",
            f"迭代方法: 逐步逼近解决方案",
            f"启发式方法: 基于经验规则",
        ]

        if problem.problem_type == ProblemType.OPTIMIZATION:
            base_solutions.extend([
                "贪心算法: 局部最优选择",
                "动态规划: 最优子结构"
            ])
        elif problem.problem_type == ProblemType.DIAGNOSIS:
            base_solutions.extend([
                "排除法: 逐一排除不可能",
                "假设检验: 验证各种假设"
            ])

        count = min(self.max_solutions, len(base_solutions))

        for i, desc in enumerate(base_solutions[:count]):
            solution = Solution(
                description=desc,
                steps=[f"步骤 {j+1}: 执行{desc}的第{j+1}阶段" for j in range(3)],
                estimated_cost=float(i + 1) * 10.0,
                estimated_time=float(i + 1) * 5.0,
                required_resources=["计算资源", "时间"],
                risks=["执行风险"] if i > 1 else []
            )
            solutions.append(solution)

        return solutions

    def _default_evaluation(
        self,
        solution: Solution,
        problem: Optional[ProblemDefinition],
        criteria: List[EvaluationCriteria]
    ) -> float:
        """默认评估函数"""
        scores = []

        cost_score = max(0.0, 1.0 - solution.estimated_cost / 100.0)
        scores.append(cost_score)

        time_score = max(0.0, 1.0 - solution.estimated_time / 50.0)
        scores.append(time_score)

        risk_score = max(0.0, 1.0 - len(solution.risks) * 0.2)
        scores.append(risk_score)

        if problem:
            goal_score = min(1.0, len(problem.goals) * 0.2 + 0.3)
            scores.append(goal_score)

        return sum(scores) / len(scores) if scores else 0.5

    def _balanced_selection(self, solutions: List[Solution]) -> Optional[Solution]:
        """平衡选择策略"""
        if not solutions:
            return None

        best = None
        best_score = -1.0

        for sol in solutions:
            balanced = (
                sol.score * 0.4 +
                max(0.0, 1.0 - sol.estimated_cost / 100.0) * 0.3 +
                max(0.0, 1.0 - len(sol.risks) * 0.2) * 0.3
            )
            if balanced > best_score:
                best_score = balanced
                best = sol

        return best

    def _default_execution(self, solution: Solution) -> Dict[str, Any]:
        """默认执行模拟"""
        return {
            "success": True,
            "solution_id": solution.solution_id,
            "steps_executed": len(solution.steps),
            "execution_time": solution.estimated_time,
            "notes": "模拟执行完成"
        }

    def _default_verification(
        self,
        solution: Solution,
        problem: ProblemDefinition
    ) -> bool:
        """默认验证逻辑"""
        return solution.score >= self.evaluation_criteria.get(
            next(iter(self.evaluation_criteria)), EvaluationCriteria(name="default", weight=0.5)
        ).weight if self.evaluation_criteria else solution.score >= 0.5
