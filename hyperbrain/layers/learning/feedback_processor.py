"""
反馈处理器

处理用户反馈，用于系统学习和改进
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger

logger = get_logger("learning.feedback")


@dataclass
class Feedback:
    """反馈数据"""
    id: str
    interaction_id: str
    rating: float  # -1 到 1
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"


class FeedbackProcessor:
    """
    反馈处理系统
    
    功能：
    1. 收集反馈
    2. 反馈分析
    3. 生成改进建议
    4. 触发学习
    """
    
    def __init__(self):
        self.feedbacks: List[Feedback] = []
        self.feedback_window: List[Feedback] = []
        self.window_size = 100
        logger.info("FeedbackProcessor initialized")
    
    def add_feedback(self, interaction_id: str,
                    rating: float,
                    comment: Optional[str] = None,
                    category: str = "general") -> Feedback:
        """
        添加反馈
        
        Args:
            interaction_id: 交互ID
            rating: 评分 (-1 到 1)
            comment: 评论
            category: 类别
            
        Returns:
            Feedback: 反馈对象
        """
        feedback = Feedback(
            id=f"fb_{len(self.feedbacks)}",
            interaction_id=interaction_id,
            rating=max(-1.0, min(1.0, rating)),
            comment=comment,
            category=category
        )
        
        self.feedbacks.append(feedback)
        self.feedback_window.append(feedback)
        
        # 维护窗口大小
        if len(self.feedback_window) > self.window_size:
            self.feedback_window.pop(0)
        
        logger.debug(f"Added feedback: {feedback.id}, rating={feedback.rating}")
        return feedback
    
    def analyze_feedback(self, window_size: Optional[int] = None) -> Dict[str, Any]:
        """
        分析反馈
        
        Args:
            window_size: 分析窗口大小
            
        Returns:
            Dict: 分析结果
        """
        window = self.feedback_window[-window_size:] if window_size else self.feedback_window
        
        if not window:
            return {"average_rating": 0.0, "trend": "neutral"}
        
        ratings = [f.rating for f in window]
        avg_rating = sum(ratings) / len(ratings)
        
        # 计算趋势
        if len(ratings) >= 2:
            first_half = sum(ratings[:len(ratings)//2]) / max(len(ratings)//2, 1)
            second_half = sum(ratings[len(ratings)//2:]) / max(len(ratings) - len(ratings)//2, 1)
            trend = "improving" if second_half > first_half else "declining" if second_half < first_half else "stable"
        else:
            trend = "neutral"
        
        return {
            "average_rating": avg_rating,
            "trend": trend,
            "total_count": len(self.feedbacks),
            "window_count": len(window),
            "positive_ratio": sum(1 for r in ratings if r > 0) / len(ratings)
        }
    
    def get_improvement_suggestions(self) -> List[str]:
        """生成改进建议"""
        analysis = self.analyze_feedback()
        suggestions = []
        
        if analysis["average_rating"] < 0:
            suggestions.append("Overall satisfaction is low, review recent interactions")
        
        if analysis["trend"] == "declining":
            suggestions.append("Performance trend is declining, consider adjusting strategy")
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_feedback": len(self.feedbacks),
            "window_size": len(self.feedback_window),
            **self.analyze_feedback()
        }
