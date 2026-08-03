"""
HyperBrain Evolution Layer

进化层负责系统的自我改进和适应。
包括自我反思、错误分析、能力评估、自我优化、目标进化和架构进化等模块。
"""

from hyperbrain.layers.evolution.self_reflection import (
    SelfReflection,
    SelfReflectionConfig,
    ReflectionScope,
    ReflectionPeriod,
    ReflectionReport,
    BehaviorRecord,
    DecisionRecord,
    CognitiveStrategyRecord,
    ReflectionInsight,
    ImprovementOpportunity,
)

from hyperbrain.layers.evolution.error_analysis import (
    ErrorAnalyzer,
    ErrorAnalysisConfig,
    ErrorCategory,
    ErrorSeverity,
    ErrorRecord,
    ErrorPattern,
    RootCauseAnalysis,
    LessonLearned,
    PreventionStrategy,
    ErrorAnalysisReport,
)

from hyperbrain.layers.evolution.capability_assessment import (
    CapabilityAssessor,
    CapabilityAssessmentConfig,
    CapabilityDimension,
    AssessmentMethod,
    CapabilityScore,
    CapabilityTrend,
    CapabilityGap,
    ImprovementSuggestion,
    CapabilityReport,
)

from hyperbrain.layers.evolution.self_optimization import (
    SelfOptimizer,
    SelfOptimizationConfig,
    OptimizationTarget,
    ParameterChange,
    OptimizationAction,
    OptimizationResult,
    CognitiveParameters,
    MemoryParameters,
    LearningParameters,
    ResourceAllocation,
)

from hyperbrain.layers.evolution.goal_evolution import (
    GoalEvolver,
    GoalEvolutionConfig,
    GoalStatus,
    GoalPriority,
    SystemGoal,
    GoalEvaluation,
    GoalAdjustment,
    GoalEvolutionReport,
)

from hyperbrain.layers.evolution.architecture_evolution import (
    ArchitectureEvolver,
    ArchitectureEvolutionConfig,
    ModuleType,
    ConnectionType,
    ArchitectureModule,
    ModuleConnection,
    InformationFlow,
    ArchitectureVersion,
    ArchitectureMetrics,
    ArchitectureEvolutionReport,
)

from hyperbrain.layers.evolution.evolution_manager import (
    EvolutionManager,
    EvolutionConfig,
    EvolutionPhase,
    EvolutionCycle,
)

__all__ = [
    # 自我反思
    "SelfReflection",
    "SelfReflectionConfig",
    "ReflectionScope",
    "ReflectionPeriod",
    "ReflectionReport",
    "BehaviorRecord",
    "DecisionRecord",
    "CognitiveStrategyRecord",
    "ReflectionInsight",
    "ImprovementOpportunity",
    # 错误分析
    "ErrorAnalyzer",
    "ErrorAnalysisConfig",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorRecord",
    "ErrorPattern",
    "RootCauseAnalysis",
    "LessonLearned",
    "PreventionStrategy",
    "ErrorAnalysisReport",
    # 能力评估
    "CapabilityAssessor",
    "CapabilityAssessmentConfig",
    "CapabilityDimension",
    "AssessmentMethod",
    "CapabilityScore",
    "CapabilityTrend",
    "CapabilityGap",
    "ImprovementSuggestion",
    "CapabilityReport",
    # 自我优化
    "SelfOptimizer",
    "SelfOptimizationConfig",
    "OptimizationTarget",
    "ParameterChange",
    "OptimizationAction",
    "OptimizationResult",
    "CognitiveParameters",
    "MemoryParameters",
    "LearningParameters",
    "ResourceAllocation",
    # 目标进化
    "GoalEvolver",
    "GoalEvolutionConfig",
    "GoalStatus",
    "GoalPriority",
    "SystemGoal",
    "GoalEvaluation",
    "GoalAdjustment",
    "GoalEvolutionReport",
    # 架构进化
    "ArchitectureEvolver",
    "ArchitectureEvolutionConfig",
    "ModuleType",
    "ConnectionType",
    "ArchitectureModule",
    "ModuleConnection",
    "InformationFlow",
    "ArchitectureVersion",
    "ArchitectureMetrics",
    "ArchitectureEvolutionReport",
    # 进化管理器
    "EvolutionManager",
    "EvolutionConfig",
    "EvolutionPhase",
    "EvolutionCycle",
]
