"""
反思模块

实现自我反思和元认知功能
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.reflection")


@dataclass
class Reflection:
    """反思记录"""
    timestamp: datetime = field(default_factory=datetime.now)
    subject: str = ""
    observation: str = ""
    evaluation: str = ""
    improvement: str = ""
    confidence_delta: float = 0.0


class ReflectionModule:
    """
    反思模块
    
    功能：
    1. 过程反思：反思推理过程
    2. 结果反思：评估输出质量
    3. 策略反思：优化思考策略
    """
    
    def __init__(self):
        self.reflections: List[Reflection] = []
        self.reflection_strategies = [
            "check_assumptions",
            "evaluate_alternatives",
            "verify_consistency",
            "assess_completeness"
        ]
        logger.info("ReflectionModule initialized")
    
    def reflect_on_process(self, process_description: str,
                          outcome: str) -> Reflection:
        """
        对思考过程进行反思
        
        Args:
            process_description: 过程描述
            outcome: 结果
            
        Returns:
            Reflection: 反思记录
        """
        reflection = Reflection(
            subject="process",
            observation=f"Process: {process_description}",
            evaluation=f"Outcome: {outcome}",
            improvement="Consider alternative approaches"
        )
        
        self.reflections.append(reflection)
        logger.debug("Process reflection completed")
        return reflection
    
    def reflect_on_result(self, expected: str, 
                         actual: str) -> Reflection:
        """
        对结果进行反思
        
        Args:
            expected: 预期结果
            actual: 实际结果
            
        Returns:
            Reflection: 反思记录
        """
        delta = 1.0 if expected == actual else -0.5
        
        reflection = Reflection(
            subject="result",
            observation=f"Expected: {expected}, Got: {actual}",
            evaluation="Match" if delta > 0 else "Mismatch",
            improvement="Adjust model or parameters" if delta < 0 else "Maintain approach",
            confidence_delta=delta
        )
        
        self.reflections.append(reflection)
        return reflection
    
    def get_reflection_history(self, 
                              subject: Optional[str] = None) -> List[Reflection]:
        """获取反思历史"""
        if subject:
            return [r for r in self.reflections if r.subject == subject]
        return self.reflections.copy()
    
    def generate_insights(self) -> List[str]:
        """生成洞察"""
        insights = []
        
        if not self.reflections:
            return insights
        
        # 分析反思模式
        positive_reflections = [r for r in self.reflections if r.confidence_delta > 0]
        negative_reflections = [r for r in self.reflections if r.confidence_delta < 0]
        
        if len(positive_reflections) > len(negative_reflections):
            insights.append("Overall positive trend in reasoning quality")
        else:
            insights.append("Need to improve reasoning strategies")
        
        return insights
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_reflections": len(self.reflections),
            "avg_confidence_delta": sum(r.confidence_delta for r in self.reflections) / max(len(self.reflections), 1),
            "strategies": self.reflection_strategies
        }
