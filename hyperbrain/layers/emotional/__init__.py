"""
情感系统层

提供完整的情感处理能力，包括情感生成、表达、记忆、调节和共情。
"""

from hyperbrain.layers.emotional.emotion_generation import (
    EmotionGenerator,
    EmotionState,
    PlutchikEmotion,
    PADEmotion,
    EmotionBlend,
    EmotionGenerationConfig,
    PlutchikEmotionType,
    EmotionIntensityLevel,
    PADDimension,
)

from hyperbrain.layers.emotional.emotion_expression import (
    EmotionExpresser,
    ExpressionConfig,
    ExpressionStyle,
    ExpressionIntensity,
    ExpressionResult,
    EmotionExpressionProfile,
)

from hyperbrain.layers.emotional.emotion_memory import (
    EmotionalMemory,
    EmotionalMemoryEntry,
    EmotionalMemoryConfig,
    RetrievalQuery,
)

from hyperbrain.layers.emotional.emotion_regulation import (
    EmotionRegulator,
    EmotionRegulationConfig,
    RegulationStrategy,
    RegulationTarget,
    RegulationRecord,
)

from hyperbrain.layers.emotional.empathy import (
    EmpathyEngine,
    EmpathyConfig,
    EmpathyLevel,
    EmpathyType,
    EmpathyResponse,
    EmpathyRecord,
)

from hyperbrain.layers.emotional.emotion_manager import (
    EmotionManager,
)

__all__ = [
    # 情感生成
    "EmotionGenerator",
    "EmotionState",
    "PlutchikEmotion",
    "PADEmotion",
    "EmotionBlend",
    "EmotionGenerationConfig",
    "PlutchikEmotionType",
    "EmotionIntensityLevel",
    "PADDimension",
    # 情感表达
    "EmotionExpresser",
    "ExpressionConfig",
    "ExpressionStyle",
    "ExpressionIntensity",
    "ExpressionResult",
    "EmotionExpressionProfile",
    # 情感记忆
    "EmotionalMemory",
    "EmotionalMemoryEntry",
    "EmotionalMemoryConfig",
    "RetrievalQuery",
    # 情感调节
    "EmotionRegulator",
    "EmotionRegulationConfig",
    "RegulationStrategy",
    "RegulationTarget",
    "RegulationRecord",
    # 共情
    "EmpathyEngine",
    "EmpathyConfig",
    "EmpathyLevel",
    "EmpathyType",
    "EmpathyResponse",
    "EmpathyRecord",
    # 情感管理器
    "EmotionManager",
]
