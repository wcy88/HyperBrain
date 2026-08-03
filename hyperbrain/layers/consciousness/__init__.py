"""
意识系统层

提供完整的意识处理能力，包括自我认知、自我意识、意志、价值体系和目标体系。
"""

from hyperbrain.layers.consciousness.self_knowledge import (
    SelfKnowledge,
    SelfKnowledgeConfig,
    CapabilityCategory,
    SystemStatus,
    CapabilityAssessment,
    StateSnapshot,
)

from hyperbrain.layers.consciousness.self_awareness import (
    SelfAwareness,
    SelfAwarenessConfig,
    AwarenessLevel,
    SubjectiveExperience,
    SelfModel,
    AwarenessSnapshot,
)

from hyperbrain.layers.consciousness.will import (
    Will,
    WillConfig,
    Intention,
    Motivation,
    IntentionType,
    MotivationSource,
    ActionTendency,
)

from hyperbrain.layers.consciousness.value_system import (
    ValueSystem,
    ValueSystemConfig,
    Value,
    ValueType,
    ValuePriority,
    MoralPrinciple,
    ValueConflict,
)

from hyperbrain.layers.consciousness.goal_system import (
    GoalSystem,
    GoalSystemConfig,
    Goal,
    GoalTimeframe,
    GoalStatus,
    GoalPriority,
    GoalProgress,
)

from hyperbrain.layers.consciousness.consciousness_manager import (
    ConsciousnessManager,
)

__all__ = [
    # 自我认知
    "SelfKnowledge",
    "SelfKnowledgeConfig",
    "CapabilityCategory",
    "SystemStatus",
    "CapabilityAssessment",
    "StateSnapshot",
    # 自我意识
    "SelfAwareness",
    "SelfAwarenessConfig",
    "AwarenessLevel",
    "SubjectiveExperience",
    "SelfModel",
    "AwarenessSnapshot",
    # 意志
    "Will",
    "WillConfig",
    "Intention",
    "Motivation",
    "IntentionType",
    "MotivationSource",
    "ActionTendency",
    # 价值体系
    "ValueSystem",
    "ValueSystemConfig",
    "Value",
    "ValueType",
    "ValuePriority",
    "MoralPrinciple",
    "ValueConflict",
    # 目标体系
    "GoalSystem",
    "GoalSystemConfig",
    "Goal",
    "GoalTimeframe",
    "GoalStatus",
    "GoalPriority",
    "GoalProgress",
    # 意识管理器
    "ConsciousnessManager",
]
