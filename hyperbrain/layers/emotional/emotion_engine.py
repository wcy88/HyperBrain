"""
情感引擎

实现情感计算、情感记忆和情感影响决策
"""

import time
import math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("emotional.engine")


@dataclass
class EmotionState:
    """情感状态"""
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0
    trust: float = 0.5
    anticipation: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_vector(self) -> List[float]:
        """转换为向量"""
        return [
            self.joy, self.sadness, self.anger, self.fear,
            self.surprise, self.disgust, self.trust, self.anticipation
        ]
    
    def valence(self) -> float:
        """计算效价（正负面）"""
        positive = self.joy + self.trust + self.anticipation
        negative = self.sadness + self.anger + self.fear + self.disgust
        return positive - negative
    
    def arousal(self) -> float:
        """计算唤醒度"""
        return (self.joy + self.anger + self.fear + self.surprise) / 4
    
    def dominance(self) -> float:
        """计算支配度"""
        return (self.trust + self.anticipation - self.fear - self.sadness) / 2


class EmotionEngine:
    """
    情感引擎
    
    功能：
    1. 情感状态计算和更新
    2. 情感衰减
    3. 情感对决策的影响
    4. 情感记忆
    """
    
    def __init__(self):
        self.config = get_config().emotional
        self.current_state = EmotionState()
        self.emotion_history: List[EmotionState] = []
        self.emotion_memory: List[Dict[str, Any]] = []
        logger.info("EmotionEngine initialized")
    
    def update_from_input(self, sentiment_score: float,
                         intensity: float = 1.0) -> EmotionState:
        """
        根据输入更新情感状态
        
        Args:
            sentiment_score: 情感分数 (-1 到 1)
            intensity: 强度
            
        Returns:
            EmotionState: 更新后的情感状态
        """
        if sentiment_score > 0:
            self.current_state.joy = min(1.0, self.current_state.joy + sentiment_score * intensity * 0.3)
            self.current_state.trust = min(1.0, self.current_state.trust + sentiment_score * intensity * 0.1)
        else:
            self.current_state.sadness = min(1.0, self.current_state.sadness + abs(sentiment_score) * intensity * 0.2)
            self.current_state.fear = min(1.0, self.current_state.fear + abs(sentiment_score) * intensity * 0.1)
        
        self.current_state.timestamp = time.time()
        self.emotion_history.append(self.current_state)
        
        logger.debug(f"Emotion updated: valence={self.current_state.valence():.2f}")
        return self.current_state
    
    def decay_emotions(self) -> EmotionState:
        """
        情感衰减
        
        Returns:
            EmotionState: 衰减后的情感状态
        """
        half_life = self.config.decay_half_life
        decay_factor = 0.5 ** (1 / half_life) if half_life > 0 else 0.99
        
        self.current_state.joy *= decay_factor
        self.current_state.sadness *= decay_factor
        self.current_state.anger *= decay_factor
        self.current_state.fear *= decay_factor
        self.current_state.surprise *= decay_factor
        self.current_state.disgust *= decay_factor
        self.current_state.anticipation *= decay_factor
        
        # trust 衰减较慢
        self.current_state.trust = 0.5 + (self.current_state.trust - 0.5) * decay_factor
        
        return self.current_state
    
    def get_emotional_influence(self) -> Dict[str, float]:
        """
        获取情感对决策的影响因子
        
        Returns:
            Dict: 影响因子
        """
        valence = self.current_state.valence()
        arousal = self.current_state.arousal()
        
        return {
            "risk_taking": 0.5 + valence * 0.3 + arousal * 0.2,
            "creativity": 0.5 + self.current_state.joy * 0.3 + self.current_state.surprise * 0.2,
            "caution": 0.5 + self.current_state.fear * 0.4 + self.current_state.sadness * 0.2,
            "openness": 0.5 + self.current_state.trust * 0.3 + self.current_state.anticipation * 0.2,
            "urgency": arousal
        }
    
    def express_emotion(self) -> str:
        """
        表达当前情感
        
        Returns:
            str: 情感描述
        """
        valence = self.current_state.valence()
        arousal = self.current_state.arousal()
        
        if valence > 0.3:
            if arousal > 0.5:
                return "excited"
            else:
                return "content"
        elif valence < -0.3:
            if arousal > 0.5:
                return "distressed"
            else:
                return "sad"
        else:
            if arousal > 0.5:
                return "alert"
            else:
                return "neutral"
    
    def store_emotional_memory(self, event: str, 
                              emotion_snapshot: Optional[EmotionState] = None) -> None:
        """
        存储情感记忆
        
        Args:
            event: 事件描述
            emotion_snapshot: 情感快照
        """
        if not self.config.enable_emotional_memory:
            return
        
        memory = {
            "event": event,
            "emotion": (emotion_snapshot or self.current_state).to_vector(),
            "timestamp": time.time()
        }
        
        self.emotion_memory.append(memory)
        logger.debug(f"Stored emotional memory for event: {event}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "current_valence": self.current_state.valence(),
            "current_arousal": self.current_state.arousal(),
            "current_dominance": self.current_state.dominance(),
            "history_count": len(self.emotion_history),
            "memory_count": len(self.emotion_memory),
            "current_expression": self.express_emotion()
        }
