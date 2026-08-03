"""
情感模型

定义情感表示和情感计算的基础模型
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PlutchikEmotion:
    """
    Plutchik情感轮模型
    
    8种基本情感及其强度
    """
    joy: float = 0.0
    trust: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    sadness: float = 0.0
    disgust: float = 0.0
    anger: float = 0.0
    anticipation: float = 0.0
    
    def get_dominant(self) -> tuple:
        """获取主导情感"""
        emotions = {
            "joy": self.joy,
            "trust": self.trust,
            "fear": self.fear,
            "surprise": self.surprise,
            "sadness": self.sadness,
            "disgust": self.disgust,
            "anger": self.anger,
            "anticipation": self.anticipation
        }
        return max(emotions.items(), key=lambda x: x[1])
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "joy": self.joy,
            "trust": self.trust,
            "fear": self.fear,
            "surprise": self.surprise,
            "sadness": self.sadness,
            "disgust": self.disgust,
            "anger": self.anger,
            "anticipation": self.anticipation
        }


@dataclass
class PADEmotion:
    """
    PAD情感模型
    
    Pleasure-Arousal-Dominance 三维情感模型
    """
    pleasure: float = 0.0      # 愉悦度
    arousal: float = 0.0       # 唤醒度
    dominance: float = 0.0     # 支配度
    
    def to_vector(self) -> List[float]:
        """转换为向量"""
        return [self.pleasure, self.arousal, self.dominance]
    
    @classmethod
    def from_plutchik(cls, plutchik: PlutchikEmotion) -> "PADEmotion":
        """从Plutchik模型转换"""
        pleasure = plutchik.joy + plutchik.trust - plutchik.sadness - plutchik.disgust
        arousal = plutchik.joy + plutchik.anger + plutchik.fear + plutchik.surprise
        dominance = plutchik.trust + plutchik.anticipation - plutchik.fear - plutchik.sadness
        
        return cls(
            pleasure=pleasure / 2,
            arousal=arousal / 2,
            dominance=dominance / 2
        )
