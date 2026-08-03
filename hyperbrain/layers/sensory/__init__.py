"""感知层 - 负责信息输入与预处理"""

from .multimodal_input import (
    MultimodalInputProcessor,
    ProcessedInput,
    InputModality,
    InputQuality,
    InputQualityReport,
    TextToken,
    ExtractedEntity,
    SemanticFeatures,
    ImageFeatures,
    AudioFeatures
)
from .attention import (
    AttentionMechanism,
    AttentionMap,
    AttentionRegion,
    AttentionLevel,
    AttentionStrategy,
    AttentionConfig
)
from .context_awareness import (
    ContextAwareness,
    SituationContext,
    TimeContext,
    LocationContext,
    UserState,
    DialogueContext,
    DialogueTurn,
    TimeOfDay,
    DayType,
    Season,
    UserEmotionalState,
    EnvironmentType
)
from .sensory_manager import (
    SensoryManager,
    PerceptionResult,
    SensoryPipelineConfig
)

__all__ = [
    # 多模态输入
    "MultimodalInputProcessor",
    "ProcessedInput",
    "InputModality",
    "InputQuality",
    "InputQualityReport",
    "TextToken",
    "ExtractedEntity",
    "SemanticFeatures",
    "ImageFeatures",
    "AudioFeatures",
    # 注意力
    "AttentionMechanism",
    "AttentionMap",
    "AttentionRegion",
    "AttentionLevel",
    "AttentionStrategy",
    "AttentionConfig",
    # 情境感知
    "ContextAwareness",
    "SituationContext",
    "TimeContext",
    "LocationContext",
    "UserState",
    "DialogueContext",
    "DialogueTurn",
    "TimeOfDay",
    "DayType",
    "Season",
    "UserEmotionalState",
    "EnvironmentType",
    # 感知管理器
    "SensoryManager",
    "PerceptionResult",
    "SensoryPipelineConfig",
]
