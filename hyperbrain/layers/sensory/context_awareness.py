"""
情境感知模块 (Context Awareness)

维护和理解当前情境信息，包括时间、地点、用户状态、对话上下文等。

功能：
- 时间感知：当前时间、日期、季节
- 地点感知：环境识别
- 用户状态感知：情绪、偏好、历史
- 对话上下文维护
- 情境信息整合
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("sensory.context_awareness")


class TimeOfDay(str, Enum):
    """一天中的时段"""
    DAWN = "dawn"           # 黎明
    MORNING = "morning"     # 上午
    NOON = "noon"           # 中午
    AFTERNOON = "afternoon" # 下午
    EVENING = "evening"     # 傍晚
    NIGHT = "night"         # 夜晚
    MIDNIGHT = "midnight"   # 午夜


class DayType(str, Enum):
    """日期类型"""
    WEEKDAY = "weekday"     # 工作日
    WEEKEND = "weekend"     # 周末
    HOLIDAY = "holiday"     # 节假日


class Season(str, Enum):
    """季节"""
    SPRING = "spring"       # 春
    SUMMER = "summer"       # 夏
    AUTUMN = "autumn"       # 秋
    WINTER = "winter"       # 冬


class UserEmotionalState(str, Enum):
    """用户情绪状态"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    BORED = "bored"
    CONFUSED = "confused"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"


class EnvironmentType(str, Enum):
    """环境类型"""
    HOME = "home"
    OFFICE = "office"
    OUTDOOR = "outdoor"
    PUBLIC = "public"
    TRANSPORT = "transport"
    UNKNOWN = "unknown"


class TimeContext(BaseModel):
    """时间情境"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    timestamp: datetime = Field(default_factory=datetime.now)
    timezone: str = "Asia/Shanghai"
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    day_of_week: int = Field(default=0, ge=0, le=6)
    day_type: DayType = DayType.WEEKDAY
    season: Season = Season.SPRING
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "timezone": self.timezone,
            "time_of_day": self.time_of_day.value,
            "day_of_week": self.day_of_week,
            "day_type": self.day_type.value,
            "season": self.season.value,
            "is_holiday": self.is_holiday,
            "holiday_name": self.holiday_name
        }


class LocationContext(BaseModel):
    """地点情境"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    environment_type: EnvironmentType = EnvironmentType.UNKNOWN
    location_name: Optional[str] = None
    timezone: str = "Asia/Shanghai"
    language_preference: str = "zh-CN"
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)  # 噪音水平
    lighting: float = Field(default=0.5, ge=0.0, le=1.0)     # 光照水平
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment_type": self.environment_type.value,
            "location_name": self.location_name,
            "timezone": self.timezone,
            "language_preference": self.language_preference,
            "noise_level": self.noise_level,
            "lighting": self.lighting
        }


class UserState(BaseModel):
    """用户状态"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    user_id: str = "default"
    emotional_state: UserEmotionalState = UserEmotionalState.NEUTRAL
    emotional_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    engagement_level: float = Field(default=0.5, ge=0.0, le=1.0)  # 参与程度
    fatigue_level: float = Field(default=0.0, ge=0.0, le=1.0)    # 疲劳程度
    urgency_level: float = Field(default=0.0, ge=0.0, le=1.0)    # 紧急程度
    preferences: Dict[str, Any] = Field(default_factory=dict)
    recent_topics: List[str] = Field(default_factory=list)
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "emotional_state": self.emotional_state.value,
            "emotional_intensity": self.emotional_intensity,
            "engagement_level": self.engagement_level,
            "fatigue_level": self.fatigue_level,
            "urgency_level": self.urgency_level,
            "preferences": self.preferences,
            "recent_topics": self.recent_topics,
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
        }


class DialogueTurn(BaseModel):
    """对话轮次"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speaker: str = ""           # "user" 或 "assistant"
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    intent: Optional[str] = None
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueContext(BaseModel):
    """对话上下文"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    turns: List[DialogueTurn] = Field(default_factory=list)
    current_topic: Optional[str] = None
    topic_history: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    user_goals: List[str] = Field(default_factory=list)
    system_goals: List[str] = Field(default_factory=list)
    max_turns: int = 50
    
    def add_turn(self, speaker: str, content: str, 
                 intent: Optional[str] = None,
                 sentiment: float = 0.0) -> DialogueTurn:
        """添加对话轮次"""
        turn = DialogueTurn(
            speaker=speaker,
            content=content,
            intent=intent,
            sentiment=sentiment
        )
        
        self.turns.append(turn)
        
        # 限制历史长度
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
        
        # 更新当前主题
        if intent:
            self.current_topic = intent
            if intent not in self.topic_history:
                self.topic_history.append(intent)
        
        return turn
    
    def get_recent_turns(self, n: int = 5) -> List[DialogueTurn]:
        """获取最近的对话轮次"""
        return self.turns[-n:]
    
    def get_user_messages(self, limit: int = 10) -> List[str]:
        """获取用户消息"""
        return [
            turn.content for turn in self.turns 
            if turn.speaker == "user"
        ][-limit:]
    
    def get_assistant_messages(self, limit: int = 10) -> List[str]:
        """获取助手消息"""
        return [
            turn.content for turn in self.turns 
            if turn.speaker == "assistant"
        ][-limit:]
    
    def is_topic_shift(self, new_topic: str) -> bool:
        """检测话题是否转移"""
        if not self.current_topic:
            return True
        return new_topic != self.current_topic
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_count": len(self.turns),
            "current_topic": self.current_topic,
            "topic_history": self.topic_history,
            "unresolved_questions": self.unresolved_questions,
            "user_goals": self.user_goals
        }


class SituationContext(BaseModel):
    """完整情境"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_context: TimeContext = Field(default_factory=TimeContext)
    location_context: LocationContext = Field(default_factory=LocationContext)
    user_state: UserState = Field(default_factory=UserState)
    dialogue_context: DialogueContext = Field(default_factory=DialogueContext)
    custom_context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "time_context": self.time_context.to_dict(),
            "location_context": self.location_context.to_dict(),
            "user_state": self.user_state.to_dict(),
            "dialogue_context": self.dialogue_context.to_dict(),
            "custom_context": self.custom_context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TimeAwareness:
    """时间感知器"""
    
    def __init__(self, timezone: str = "Asia/Shanghai"):
        self.timezone = timezone
        self._holidays = {
            "01-01": "元旦",
            "02-14": "情人节",
            "05-01": "劳动节",
            "06-01": "儿童节",
            "10-01": "国庆节",
            "12-25": "圣诞节"
        }
        logger.info("TimeAwareness initialized")
    
    def get_current_context(self) -> TimeContext:
        """获取当前时间情境"""
        now = datetime.now()
        
        return TimeContext(
            timestamp=now,
            timezone=self.timezone,
            time_of_day=self._get_time_of_day(now),
            day_of_week=now.weekday(),
            day_type=self._get_day_type(now),
            season=self._get_season(now),
            is_holiday=self._is_holiday(now),
            holiday_name=self._get_holiday_name(now)
        )
    
    def _get_time_of_day(self, dt: datetime) -> TimeOfDay:
        """获取时段"""
        hour = dt.hour
        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 11:
            return TimeOfDay.MORNING
        elif 11 <= hour < 13:
            return TimeOfDay.NOON
        elif 13 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 19:
            return TimeOfDay.EVENING
        elif 19 <= hour < 23:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.MIDNIGHT
    
    def _get_day_type(self, dt: datetime) -> DayType:
        """获取日期类型"""
        if dt.weekday() >= 5:
            return DayType.WEEKEND
        if self._is_holiday(dt):
            return DayType.HOLIDAY
        return DayType.WEEKDAY
    
    def _get_season(self, dt: datetime) -> Season:
        """获取季节"""
        month = dt.month
        if month in (3, 4, 5):
            return Season.SPRING
        elif month in (6, 7, 8):
            return Season.SUMMER
        elif month in (9, 10, 11):
            return Season.AUTUMN
        else:
            return Season.WINTER
    
    def _is_holiday(self, dt: datetime) -> bool:
        """检查是否是节假日"""
        date_str = dt.strftime("%m-%d")
        return date_str in self._holidays
    
    def _get_holiday_name(self, dt: datetime) -> Optional[str]:
        """获取节假日名称"""
        date_str = dt.strftime("%m-%d")
        return self._holidays.get(date_str)
    
    def get_greeting_by_time(self) -> str:
        """根据时间获取问候语"""
        time_of_day = self._get_time_of_day(datetime.now())
        greetings = {
            TimeOfDay.DAWN: "早上好",
            TimeOfDay.MORNING: "早上好",
            TimeOfDay.NOON: "中午好",
            TimeOfDay.AFTERNOON: "下午好",
            TimeOfDay.EVENING: "晚上好",
            TimeOfDay.NIGHT: "晚上好",
            TimeOfDay.MIDNIGHT: "夜深了"
        }
        return greetings.get(time_of_day, "你好")


class LocationAwareness:
    """地点感知器"""
    
    def __init__(self):
        self._current_location: Optional[LocationContext] = None
        logger.info("LocationAwareness initialized")
    
    def detect_environment(self, hints: Optional[Dict[str, Any]] = None) -> LocationContext:
        """
        检测环境
        
        Args:
            hints: 环境线索
            
        Returns:
            LocationContext: 地点情境
        """
        context = LocationContext()
        
        if hints:
            # 根据线索推断环境
            if hints.get("has_desk") and hints.get("has_computer"):
                context.environment_type = EnvironmentType.OFFICE
            elif hints.get("has_bed") or hints.get("is_home"):
                context.environment_type = EnvironmentType.HOME
            elif hints.get("is_moving"):
                context.environment_type = EnvironmentType.TRANSPORT
            elif hints.get("is_outdoor"):
                context.environment_type = EnvironmentType.OUTDOOR
            
            context.location_name = hints.get("location_name")
            context.noise_level = hints.get("noise_level", 0.0)
            context.lighting = hints.get("lighting", 0.5)
            context.metadata = hints
        
        self._current_location = context
        return context
    
    def set_location(self, location: LocationContext) -> None:
        """设置当前位置"""
        self._current_location = location
    
    def get_current_location(self) -> Optional[LocationContext]:
        """获取当前位置"""
        return self._current_location


class UserStateTracker:
    """用户状态追踪器"""
    
    def __init__(self):
        self._users: Dict[str, UserState] = {}
        self._emotion_indicators = {
            UserEmotionalState.HAPPY: ["开心", "高兴", "快乐", "棒", "great", "happy", "good", "excellent"],
            UserEmotionalState.SAD: ["难过", "伤心", "悲伤", "sad", "upset", "depressed"],
            UserEmotionalState.ANGRY: ["生气", "愤怒", "讨厌", "angry", "mad", "furious"],
            UserEmotionalState.ANXIOUS: ["焦虑", "担心", "紧张", "anxious", "worried", "nervous"],
            UserEmotionalState.EXCITED: ["兴奋", "激动", "期待", "excited", "thrilled"],
            UserEmotionalState.BORED: ["无聊", "没意思", "bored", "uninterested"],
            UserEmotionalState.CONFUSED: ["困惑", "不明白", "confused", "puzzled"],
            UserEmotionalState.FRUSTRATED: ["沮丧", "挫败", "frustrated", "disappointed"]
        }
        logger.info("UserStateTracker initialized")
    
    def get_or_create_user(self, user_id: str = "default") -> UserState:
        """获取或创建用户状态"""
        if user_id not in self._users:
            self._users[user_id] = UserState(user_id=user_id)
        return self._users[user_id]
    
    def update_emotion(self, user_id: str, text: str) -> UserEmotionalState:
        """
        根据文本更新用户情绪状态
        
        Args:
            user_id: 用户ID
            text: 用户输入文本
            
        Returns:
            UserEmotionalState: 检测到的情绪
        """
        user = self.get_or_create_user(user_id)
        text_lower = text.lower()
        
        # 检测情绪
        detected_emotion = UserEmotionalState.NEUTRAL
        max_matches = 0
        
        for emotion, indicators in self._emotion_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text_lower)
            if matches > max_matches:
                max_matches = matches
                detected_emotion = emotion
        
        # 更新情绪
        user.emotional_state = detected_emotion
        user.emotional_intensity = min(1.0, max(0.3, max_matches * 0.3))
        
        # 检测紧急程度
        urgency_words = ["紧急", " urgent", "立刻", "马上", "asap", "急"]
        user.urgency_level = min(1.0, sum(1 for w in urgency_words if w in text_lower) * 0.3)
        
        return detected_emotion
    
    def update_engagement(self, user_id: str, message_length: int, 
                          response_time: float) -> None:
        """
        更新用户参与度
        
        Args:
            user_id: 用户ID
            message_length: 消息长度
            response_time: 响应时间（秒）
        """
        user = self.get_or_create_user(user_id)
        
        # 基于消息长度判断参与度
        if message_length > 100:
            engagement = 0.8
        elif message_length > 50:
            engagement = 0.6
        elif message_length > 20:
            engagement = 0.4
        else:
            engagement = 0.2
        
        # 响应时间影响
        if response_time < 5:
            engagement += 0.1
        elif response_time > 60:
            engagement -= 0.1
        
        user.engagement_level = max(0.0, min(1.0, engagement))
    
    def record_interaction(self, user_id: str = "default") -> None:
        """记录交互"""
        user = self.get_or_create_user(user_id)
        user.interaction_count += 1
        user.last_interaction = datetime.now()
    
    def update_preferences(self, user_id: str, 
                           preferences: Dict[str, Any]) -> None:
        """更新用户偏好"""
        user = self.get_or_create_user(user_id)
        user.preferences.update(preferences)
    
    def add_recent_topic(self, user_id: str, topic: str) -> None:
        """添加最近主题"""
        user = self.get_or_create_user(user_id)
        if topic not in user.recent_topics:
            user.recent_topics.append(topic)
            if len(user.recent_topics) > 20:
                user.recent_topics = user.recent_topics[-20:]
    
    def get_user_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """获取用户摘要"""
        user = self.get_or_create_user(user_id)
        return user.to_dict()


class ContextAwareness:
    """
    情境感知主类
    
    整合时间、地点、用户状态、对话上下文等信息，
    提供完整的情境理解能力。
    """
    
    def __init__(self):
        self.config = get_config().sensory
        self.time_awareness = TimeAwareness()
        self.location_awareness = LocationAwareness()
        self.user_tracker = UserStateTracker()
        self._current_context: Optional[SituationContext] = None
        self._context_history: List[SituationContext] = []
        logger.info("ContextAwareness initialized")
    
    def initialize_context(self, user_id: str = "default",
                           location_hints: Optional[Dict[str, Any]] = None) -> SituationContext:
        """
        初始化情境
        
        Args:
            user_id: 用户ID
            location_hints: 位置线索
            
        Returns:
            SituationContext: 初始化的情境
        """
        context = SituationContext(
            time_context=self.time_awareness.get_current_context(),
            location_context=self.location_awareness.detect_environment(location_hints),
            user_state=self.user_tracker.get_or_create_user(user_id)
        )
        
        self._current_context = context
        self._context_history.append(context)
        
        logger.info(f"Context initialized for user {user_id}")
        return context
    
    def update_context(self, 
                       user_input: Optional[str] = None,
                       assistant_response: Optional[str] = None,
                       intent: Optional[str] = None,
                       sentiment: float = 0.0) -> SituationContext:
        """
        更新情境
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            intent: 用户意图
            sentiment: 情感分数
            
        Returns:
            SituationContext: 更新后的情境
        """
        if not self._current_context:
            self.initialize_context()
        
        context = self._current_context
        
        # 更新时间
        context.time_context = self.time_awareness.get_current_context()
        
        # 更新用户状态
        if user_input:
            user_id = context.user_state.user_id
            self.user_tracker.update_emotion(user_id, user_input)
            self.user_tracker.record_interaction(user_id)
            self.user_tracker.update_engagement(user_id, len(user_input), 0)
            
            if intent:
                self.user_tracker.add_recent_topic(user_id, intent)
        
        # 更新对话上下文
        if user_input:
            context.dialogue_context.add_turn(
                speaker="user",
                content=user_input,
                intent=intent,
                sentiment=sentiment
            )
        
        if assistant_response:
            context.dialogue_context.add_turn(
                speaker="assistant",
                content=assistant_response
            )
        
        context.updated_at = datetime.now()
        
        return context
    
    def get_current_context(self) -> SituationContext:
        """获取当前情境"""
        if not self._current_context:
            return self.initialize_context()
        return self._current_context
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取情境摘要"""
        context = self.get_current_context()
        
        return {
            "time": {
                "current": context.time_context.timestamp.strftime("%Y-%m-%d %H:%M"),
                "time_of_day": context.time_context.time_of_day.value,
                "season": context.time_context.season.value,
                "is_holiday": context.time_context.is_holiday
            },
            "location": {
                "environment": context.location_context.environment_type.value,
                "timezone": context.location_context.timezone
            },
            "user": {
                "emotional_state": context.user_state.emotional_state.value,
                "engagement": context.user_state.engagement_level,
                "interaction_count": context.user_state.interaction_count
            },
            "dialogue": {
                "turn_count": len(context.dialogue_context.turns),
                "current_topic": context.dialogue_context.current_topic,
                "recent_topics": context.dialogue_context.topic_history[-5:]
            }
        }
    
    def is_context_stale(self, max_age_seconds: float = 300.0) -> bool:
        """检查情境是否过时"""
        if not self._current_context:
            return True
        
        age = (datetime.now() - self._current_context.updated_at).total_seconds()
        return age > max_age_seconds
    
    def get_relevant_context_for_input(self, user_input: str) -> Dict[str, Any]:
        """
        获取与用户输入相关的情境信息
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict: 相关情境信息
        """
        context = self.get_current_context()
        
        relevant = {
            "time_context": context.time_context.to_dict(),
            "user_state": {
                "emotional_state": context.user_state.emotional_state.value,
                "engagement_level": context.user_state.engagement_level,
                "urgency_level": context.user_state.urgency_level
            },
            "dialogue_history": [
                {
                    "speaker": turn.speaker,
                    "content": turn.content[:100],
                    "intent": turn.intent
                }
                for turn in context.dialogue_context.get_recent_turns(3)
            ]
        }
        
        # 检测时间相关查询
        time_keywords = ["时间", "几点", "日期", "今天", "明天", "time", "date", "today"]
        if any(kw in user_input.lower() for kw in time_keywords):
            relevant["current_time"] = context.time_context.timestamp.isoformat()
        
        # 检测情绪相关
        emotion_keywords = ["感觉", "心情", "情绪", "feel", "mood", "emotion"]
        if any(kw in user_input.lower() for kw in emotion_keywords):
            relevant["user_emotion"] = context.user_state.emotional_state.value
        
        return relevant
    
    def get_greeting_context(self) -> str:
        """获取问候情境"""
        context = self.get_current_context()
        
        parts = []
        
        # 时间问候
        time_greeting = self.time_awareness.get_greeting_by_time()
        parts.append(time_greeting)
        
        # 节假日问候
        if context.time_context.is_holiday and context.time_context.holiday_name:
            parts.append(f"今天是{context.time_context.holiday_name}!")
        
        # 根据用户状态调整
        if context.user_state.emotional_state == UserEmotionalState.HAPPY:
            parts.append("看起来你今天心情不错！")
        elif context.user_state.emotional_state == UserEmotionalState.SAD:
            parts.append("有什么我可以帮你的吗？")
        
        return " ".join(parts)
    
    def reset_dialogue(self) -> None:
        """重置对话上下文"""
        if self._current_context:
            self._current_context.dialogue_context = DialogueContext()
            logger.info("Dialogue context reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "context_history_size": len(self._context_history),
            "has_active_context": self._current_context is not None,
            "tracked_users": len(self.user_tracker._users)
        }
    
    def clear_history(self) -> None:
        """清空历史"""
        self._context_history.clear()
        self._current_context = None
        logger.info("Context history cleared")
