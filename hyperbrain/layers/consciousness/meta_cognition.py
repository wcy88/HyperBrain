"""
元认知模块

实现对自身认知过程的监控和调节
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("consciousness.meta")


@dataclass
class CognitiveProcess:
    """认知过程记录"""
    process_type: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"
    quality_score: float = 0.0
    notes: List[str] = field(default_factory=list)


class MetaCognition:
    """
    元认知系统
    
    功能：
    1. 监控认知过程
    2. 评估思维质量
    3. 调节认知策略
    4. 自我反思
    """
    
    def __init__(self):
        self.config = get_config().consciousness
        self.active_processes: Dict[str, CognitiveProcess] = {}
        self.process_history: List[CognitiveProcess] = []
        self.reflections: List[Dict[str, Any]] = []
        self.last_reflection_time: float = 0.0
        logger.info("MetaCognition initialized")
    
    def start_monitoring(self, process_id: str, 
                        process_type: str) -> CognitiveProcess:
        """
        开始监控认知过程
        
        Args:
            process_id: 过程ID
            process_type: 过程类型
            
        Returns:
            CognitiveProcess: 认知过程记录
        """
        process = CognitiveProcess(
            process_type=process_type,
            start_time=time.time()
        )
        
        self.active_processes[process_id] = process
        logger.debug(f"Started monitoring: {process_type} ({process_id})")
        return process
    
    def end_monitoring(self, process_id: str, 
                      quality_score: float = 0.0) -> Optional[CognitiveProcess]:
        """
        结束监控
        
        Args:
            process_id: 过程ID
            quality_score: 质量评分
            
        Returns:
            Optional[CognitiveProcess]: 过程记录
        """
        if process_id not in self.active_processes:
            return None
        
        process = self.active_processes[process_id]
        process.end_time = time.time()
        process.status = "completed"
        process.quality_score = quality_score
        
        self.process_history.append(process)
        del self.active_processes[process_id]
        
        logger.debug(f"Ended monitoring: {process.process_type} (score={quality_score:.2f})")
        return process
    
    def evaluate_thinking(self, process_id: str) -> Dict[str, Any]:
        """
        评估思维过程
        
        Args:
            process_id: 过程ID
            
        Returns:
            Dict: 评估结果
        """
        if process_id not in self.active_processes:
            return {"error": "Process not found"}
        
        process = self.active_processes[process_id]
        duration = time.time() - process.start_time
        
        evaluation = {
            "process_type": process.process_type,
            "duration": duration,
            "status": process.status,
            "quality_score": process.quality_score,
            "efficiency": process.quality_score / max(duration, 1.0)
        }
        
        return evaluation
    
    def reflect(self) -> Dict[str, Any]:
        """
        执行自我反思
        
        Returns:
            Dict: 反思结果
        """
        current_time = time.time()
        
        # 检查反思间隔
        if (current_time - self.last_reflection_time) < self.config.self_reflection_interval:
            return {"status": "skipped", "reason": "Interval not reached"}
        
        self.last_reflection_time = current_time
        
        # 分析近期认知过程
        recent_processes = [p for p in self.process_history 
                          if current_time - p.start_time < 3600]
        
        avg_quality = sum(p.quality_score for p in recent_processes) / max(len(recent_processes), 1)
        
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "recent_processes": len(recent_processes),
            "average_quality": avg_quality,
            "observations": [],
            "suggestions": []
        }
        
        if avg_quality < 0.5:
            reflection["observations"].append("Recent cognitive quality is low")
            reflection["suggestions"].append("Consider slowing down and reviewing steps")
        
        if len(recent_processes) > 20:
            reflection["observations"].append("High cognitive load detected")
            reflection["suggestions"].append("Consider prioritizing tasks")
        
        self.reflections.append(reflection)
        logger.info("Self-reflection completed")
        return reflection
    
    def adjust_strategy(self, based_on: Optional[str] = None) -> Dict[str, Any]:
        """
        调整认知策略
        
        Args:
            based_on: 基于的反思ID
            
        Returns:
            Dict: 调整结果
        """
        # 分析历史表现，调整策略
        if not self.process_history:
            return {"status": "no_data"}
        
        recent = self.process_history[-10:]
        avg_score = sum(p.quality_score for p in recent) / len(recent)
        
        adjustments = {
            "depth_increase": avg_score < 0.6,
            "speed_decrease": avg_score < 0.4,
            "confidence_adjustment": (avg_score - 0.5) * 0.2
        }
        
        logger.info(f"Strategy adjusted based on avg score: {avg_score:.2f}")
        return adjustments
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "active_processes": len(self.active_processes),
            "total_processes": len(self.process_history),
            "reflections": len(self.reflections),
            "avg_quality": sum(p.quality_score for p in self.process_history) / max(len(self.process_history), 1),
            "meta_cognition_depth": self.config.meta_cognition_depth
        }
