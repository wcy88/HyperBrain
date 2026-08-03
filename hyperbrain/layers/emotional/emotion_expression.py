"""
情感表达模块

通过语言表达方式传递情感，包括语气词、表情符号和语言风格调整。
"""

import random
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("emotional.expression")


class ExpressionStyle(str, Enum):
    """表达风格"""
    FORMAL = "formal"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    HUMOROUS = "humorous"
    EMPATHETIC = "empathetic"


class ExpressionIntensity(str, Enum):
    """表达强度等级"""
    SUBTLE = "subtle"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class ExpressionConfig(BaseModel):
    """表达配置"""
    default_style: ExpressionStyle = Field(default=ExpressionStyle.CASUAL)
    default_intensity: ExpressionIntensity = Field(default=ExpressionIntensity.MODERATE)
    enable_emojis: bool = Field(default=True)
    enable_modal_particles: bool = Field(default=True)
    max_emojis_per_message: int = Field(default=3, ge=0, le=10)
    intensity_scale: float = Field(default=1.0, ge=0.0, le=2.0)


class EmotionExpressionProfile(BaseModel):
    """情感表达配置文件"""
    emotion: str
    style: ExpressionStyle
    intensity: ExpressionIntensity
    modal_particles: List[str]
    emojis: List[str]
    tone_words: List[str]
    sentence_patterns: List[str]


class ExpressionResult(BaseModel):
    """表达结果"""
    original_text: str
    modified_text: str
    applied_style: ExpressionStyle
    applied_intensity: ExpressionIntensity
    added_elements: List[str]
    emotional_markers: Dict[str, Any]


class EmotionExpresser:
    """
    情感表达器

    功能：
    1. 通过语言表达方式传递情感
    2. 语气词和表情符号选择
    3. 语言风格调整（正式/随意/热情等）
    4. 情感表达强度控制
    """

    # 情感-语气词映射
    MODAL_PARTICLES = {
        "joy": ["哈哈", "嘿嘿", "哇", "太棒了", "真好"],
        "trust": ["当然", "没问题", "放心吧", "我相信", "确实"],
        "fear": ["啊", "天哪", "糟了", "怎么办", "有点担心"],
        "surprise": ["哇", "真的吗", "天哪", "没想到", "居然"],
        "sadness": ["唉", "呜呜", "好难过", "真可惜", "遗憾"],
        "disgust": ["呃", "真是的", "受不了", "讨厌", "恶心"],
        "anger": ["哼", "真是", "太过分了", "气死我了", "岂有此理"],
        "anticipation": ["期待", "好想", "快了吧", "就要", "等着看"],
        "neutral": ["嗯", "好的", "了解了", "明白", "知道了"],
    }

    # 情感-表情符号映射
    EMOJIS = {
        "joy": ["😊", "😄", "🎉", "✨", "🌟"],
        "trust": ["🤝", "💙", "✅", "🙏", "👍"],
        "fear": ["😰", "😨", "😱", "💦", "🥺"],
        "surprise": ["😮", "😲", "🤯", "❗", "❓"],
        "sadness": ["😢", "😭", "💔", "😔", "🥀"],
        "disgust": ["😤", "🙄", "😒", "💢", "🤮"],
        "anger": ["😠", "😡", "🤬", "💥", "👿"],
        "anticipation": ["🤩", "😏", "👀", "🎯", "🚀"],
        "neutral": ["😐", "😶", "🤔", "💭", "📋"],
    }

    # 情感-语气词映射（英文）
    TONE_WORDS = {
        "joy": ["wonderful", "great", "amazing", "fantastic", "delighted"],
        "trust": ["confident", "sure", "reliable", "trustworthy", "certain"],
        "fear": ["worried", "concerned", "anxious", "afraid", "nervous"],
        "surprise": ["amazing", "unexpected", "astonishing", "incredible", "wow"],
        "sadness": ["unfortunate", "sad", "regrettable", "disappointing", "melancholy"],
        "disgust": ["unpleasant", "distasteful", "unacceptable", "offensive", "repulsive"],
        "anger": ["frustrating", "unacceptable", "outrageous", "infuriating", "ridiculous"],
        "anticipation": ["exciting", "promising", "upcoming", "eager", "looking forward"],
        "neutral": ["okay", "alright", "fine", "noted", "understood"],
    }

    # 风格模板
    STYLE_TEMPLATES = {
        ExpressionStyle.FORMAL: {
            "prefix": "",
            "suffix": "",
            "punctuation": "。",
            "avoid_particles": True,
            "avoid_emojis": True,
        },
        ExpressionStyle.CASUAL: {
            "prefix": "",
            "suffix": "",
            "punctuation": "~",
            "avoid_particles": False,
            "avoid_emojis": False,
        },
        ExpressionStyle.ENTHUSIASTIC: {
            "prefix": "",
            "suffix": "！！",
            "punctuation": "！",
            "avoid_particles": False,
            "avoid_emojis": False,
        },
        ExpressionStyle.CALM: {
            "prefix": "",
            "suffix": "",
            "punctuation": "。",
            "avoid_particles": False,
            "avoid_emojis": True,
        },
        ExpressionStyle.HUMOROUS: {
            "prefix": "",
            "suffix": "😄",
            "punctuation": "~",
            "avoid_particles": False,
            "avoid_emojis": False,
        },
        ExpressionStyle.EMPATHETIC: {
            "prefix": "",
            "suffix": "",
            "punctuation": "",
            "avoid_particles": False,
            "avoid_emojis": False,
        },
    }

    # 强度倍数映射
    INTENSITY_MULTIPLIERS = {
        ExpressionIntensity.SUBTLE: 0.3,
        ExpressionIntensity.MODERATE: 0.6,
        ExpressionIntensity.STRONG: 0.9,
        ExpressionIntensity.VERY_STRONG: 1.2,
    }

    def __init__(self, config: Optional[ExpressionConfig] = None):
        self.config = config or ExpressionConfig()
        self._expression_history: List[ExpressionResult] = []
        logger.info("EmotionExpresser initialized")

    def express(
        self,
        text: str,
        emotion: str = "neutral",
        style: Optional[ExpressionStyle] = None,
        intensity: Optional[ExpressionIntensity] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpressionResult:
        """
        表达情感

        Args:
            text: 原始文本
            emotion: 情感类型
            style: 表达风格
            intensity: 表达强度
            context: 上下文

        Returns:
            ExpressionResult: 表达结果
        """
        applied_style = style or self.config.default_style
        applied_intensity = intensity or self.config.default_intensity
        added_elements: List[str] = []

        modified_text = text
        template = self.STYLE_TEMPLATES[applied_style]

        # 添加语气词
        if (self.config.enable_modal_particles
                and not template["avoid_particles"]):
            particles = self.MODAL_PARTICLES.get(emotion, self.MODAL_PARTICLES["neutral"])
            if particles and random.random() < self.INTENSITY_MULTIPLIERS[applied_intensity]:
                particle = random.choice(particles)
                if emotion in ["joy", "surprise", "anticipation"]:
                    modified_text = f"{particle}，{modified_text}"
                else:
                    modified_text = f"{modified_text}{particle}"
                added_elements.append(f"particle:{particle}")

        # 添加表情符号
        if (self.config.enable_emojis
                and not template["avoid_emojis"]):
            emojis = self.EMOJIS.get(emotion, self.EMOJIS["neutral"])
            emoji_count = min(
                self.config.max_emojis_per_message,
                max(1, int(self.INTENSITY_MULTIPLIERS[applied_intensity] * 2))
            )
            if emojis and random.random() < 0.7:
                selected_emojis = random.sample(emojis, min(emoji_count, len(emojis)))
                modified_text = f"{modified_text} {''.join(selected_emojis)}"
                added_elements.append(f"emojis:{''.join(selected_emojis)}")

        # 应用风格模板
        if template["suffix"]:
            modified_text += template["suffix"]

        result = ExpressionResult(
            original_text=text,
            modified_text=modified_text,
            applied_style=applied_style,
            applied_intensity=applied_intensity,
            added_elements=added_elements,
            emotional_markers={
                "emotion": emotion,
                "style": applied_style.value,
                "intensity": applied_intensity.value,
            }
        )

        self._expression_history.append(result)
        logger.debug(f"Expressed emotion: {emotion} with style {applied_style.value}")
        return result

    def adjust_style(
        self,
        text: str,
        target_style: ExpressionStyle
    ) -> str:
        """
        调整语言风格

        Args:
            text: 原始文本
            target_style: 目标风格

        Returns:
            str: 调整后的文本
        """
        template = self.STYLE_TEMPLATES[target_style]
        adjusted = text

        if target_style == ExpressionStyle.FORMAL:
            adjusted = adjusted.replace("~", "。")
            adjusted = adjusted.replace("！", "。")
            adjusted = adjusted.replace("？", "？")
        elif target_style == ExpressionStyle.ENTHUSIASTIC:
            adjusted = adjusted.replace("。", "！")
            if not adjusted.endswith("！"):
                adjusted += "！"
        elif target_style == ExpressionStyle.CALM:
            adjusted = adjusted.replace("！", "。")
            adjusted = adjusted.replace("~", "。")

        return adjusted

    def select_emojis(
        self,
        emotion: str,
        count: int = 1
    ) -> List[str]:
        """
        选择表情符号

        Args:
            emotion: 情感类型
            count: 数量

        Returns:
            List[str]: 表情符号列表
        """
        emojis = self.EMOJIS.get(emotion, self.EMOJIS["neutral"])
        count = min(count, len(emojis), self.config.max_emojis_per_message)
        return random.sample(emojis, count) if count > 0 else []

    def select_modal_particles(
        self,
        emotion: str,
        count: int = 1
    ) -> List[str]:
        """
        选择语气词

        Args:
            emotion: 情感类型
            count: 数量

        Returns:
            List[str]: 语气词列表
        """
        particles = self.MODAL_PARTICLES.get(emotion, self.MODAL_PARTICLES["neutral"])
        count = min(count, len(particles))
        return random.sample(particles, count) if count > 0 else []

    def control_intensity(
        self,
        expression: str,
        target_intensity: ExpressionIntensity
    ) -> str:
        """
        控制表达强度

        Args:
            expression: 原始表达
            target_intensity: 目标强度

        Returns:
            str: 调整后的表达
        """
        multiplier = self.INTENSITY_MULTIPLIERS[target_intensity]
        controlled = expression

        if multiplier < 0.5:
            controlled = controlled.replace("！", "。")
            controlled = controlled.replace("~", "。")
        elif multiplier > 0.8:
            if not controlled.endswith(("！", "~", "?")):
                controlled += "！"

        return controlled

    def create_expression_profile(
        self,
        emotion: str,
        style: ExpressionStyle,
        intensity: ExpressionIntensity
    ) -> EmotionExpressionProfile:
        """
        创建情感表达配置文件

        Args:
            emotion: 情感类型
            style: 表达风格
            intensity: 表达强度

        Returns:
            EmotionExpressionProfile: 表达配置文件
        """
        return EmotionExpressionProfile(
            emotion=emotion,
            style=style,
            intensity=intensity,
            modal_particles=self.select_modal_particles(emotion, 3),
            emojis=self.select_emojis(emotion, 3),
            tone_words=self.TONE_WORDS.get(emotion, self.TONE_WORDS["neutral"]),
            sentence_patterns=[]
        )

    def get_expression_history(self, limit: int = 50) -> List[ExpressionResult]:
        """获取表达历史"""
        return self._expression_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._expression_history:
            return {"total_expressions": 0}

        style_counts = {}
        emotion_counts = {}
        for result in self._expression_history:
            style = result.applied_style.value
            style_counts[style] = style_counts.get(style, 0) + 1
            emotion = result.emotional_markers.get("emotion", "unknown")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        return {
            "total_expressions": len(self._expression_history),
            "style_distribution": style_counts,
            "emotion_distribution": emotion_counts,
            "config": self.config.model_dump(),
        }
