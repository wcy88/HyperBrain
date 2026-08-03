"""
认知层 - 负责思维与推理

这是HyperBrain系统的核心认知模块，模拟人脑的高级认知功能：

架构：
    输入 -> 推理引擎 -> 问题解决器 -> 决策器 -> 规划器
              -> 元认知监控 -> 抽象思维引擎

模块：
    - reasoning: 逻辑推理模块（演绎、归纳、类比、溯因、思维链）
    - problem_solving: 问题解决模块（定义、生成、评估、选择、验证）
    - decision_making: 决策模块（目标/价值/风险/多准则/概率决策）
    - planning: 规划模块（短/中/长期规划，依赖管理）
    - metacognition: 元认知模块（监控、评估、调整、偏差检测）
    - abstraction: 抽象思维模块（概念、泛化、模式、知识表示）
    - cognitive_manager: 认知管理器（统一协调所有模块）

使用示例：
    >>> from hyperbrain.layers.cognitive import CognitiveManager
    >>> cm = CognitiveManager()
    >>>
    >>> # 统一思考
    >>> result = cm.think("如何优化系统性能？")
    >>>
    >>> # 推理
    >>> reasoning = cm.reason(["所有程序员都会编码", "小明是程序员"], ReasoningType.DEDUCTIVE)
    >>>
    >>> # 问题解决
    >>> solution = cm.solve_problem("系统响应慢", ProblemType.DIAGNOSIS)
    >>>
    >>> # 决策
    >>> decision = cm.decide(alternatives, DecisionType.MULTI_CRITERIA)
    >>>
    >>> # 规划
    >>> plan = cm.plan("优化计划", "系统性能优化", PlanType.SHORT_TERM)
    >>>
    >>> # 监控认知状态
    >>> state = cm.monitor_cognition()
    >>>
    >>> # 反思
    >>> reflection = cm.reflect()
"""

from hyperbrain.layers.cognitive.reasoning import (
    ReasoningEngine,
    ReasoningType,
    ReasoningStep,
    ReasoningResult,
    ConfidenceLevel,
    Premise,
    Rule,
    AnalogyMapping,
)

from hyperbrain.layers.cognitive.problem_solving import (
    ProblemSolver,
    ProblemType,
    ProblemDefinition,
    Solution,
    SolutionStatus,
    ConstraintType,
    EvaluationCriteria,
    ProblemSolvingResult,
)

from hyperbrain.layers.cognitive.decision_making import (
    DecisionMaker,
    DecisionType,
    DecisionStatus,
    RiskLevel,
    Alternative,
    Criterion,
    Goal,
    RiskAssessment,
    DecisionTreeNode,
    DecisionResult,
)

from hyperbrain.layers.cognitive.planning import (
    Planner,
    PlanType,
    TaskStatus,
    DependencyType,
    PlanTask,
    PlanDependency,
    Plan,
    PlanAdjustment,
    PlanExecutionResult,
)

from hyperbrain.layers.cognitive.metacognition import (
    MetacognitionMonitor,
    CognitiveState,
    BiasType,
    MonitoringEvent,
    SelfQuestion,
    BiasDetection,
    StrategyAdjustment,
    CognitivePerformance,
)

from hyperbrain.layers.cognitive.abstraction import (
    AbstractionEngine,
    ConceptType,
    PatternType,
    Concept,
    Pattern,
    SymbolMapping,
    Generalization,
    KnowledgeRepresentation,
)

from hyperbrain.layers.cognitive.cognitive_manager import CognitiveManager

__all__ = [
    # 推理模块
    "ReasoningEngine",
    "ReasoningType",
    "ReasoningStep",
    "ReasoningResult",
    "ConfidenceLevel",
    "Premise",
    "Rule",
    "AnalogyMapping",
    # 问题解决模块
    "ProblemSolver",
    "ProblemType",
    "ProblemDefinition",
    "Solution",
    "SolutionStatus",
    "ConstraintType",
    "EvaluationCriteria",
    "ProblemSolvingResult",
    # 决策模块
    "DecisionMaker",
    "DecisionType",
    "DecisionStatus",
    "RiskLevel",
    "Alternative",
    "Criterion",
    "Goal",
    "RiskAssessment",
    "DecisionTreeNode",
    "DecisionResult",
    # 规划模块
    "Planner",
    "PlanType",
    "TaskStatus",
    "DependencyType",
    "PlanTask",
    "PlanDependency",
    "Plan",
    "PlanAdjustment",
    "PlanExecutionResult",
    # 元认知模块
    "MetacognitionMonitor",
    "CognitiveState",
    "BiasType",
    "MonitoringEvent",
    "SelfQuestion",
    "BiasDetection",
    "StrategyAdjustment",
    "CognitivePerformance",
    # 抽象思维模块
    "AbstractionEngine",
    "ConceptType",
    "PatternType",
    "Concept",
    "Pattern",
    "SymbolMapping",
    "Generalization",
    "KnowledgeRepresentation",
    # 认知管理器
    "CognitiveManager",
]
