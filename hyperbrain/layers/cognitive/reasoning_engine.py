"""
推理引擎

实现多种推理模式：演绎推理、归纳推理、类比推理、因果推理
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("cognitive.reasoning")


class ReasoningType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"      # 演绎推理
    INDUCTIVE = "inductive"      # 归纳推理
    ABDUCTIVE = "abductive"      # 溯因推理
    ANALOGICAL = "analogical"    # 类比推理
    CAUSAL = "causal"            # 因果推理


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    premise: str
    operation: str
    conclusion: str
    confidence: float
    reasoning_type: ReasoningType


@dataclass
class ReasoningResult:
    """推理结果"""
    conclusion: str
    confidence: float
    steps: List[ReasoningStep] = field(default_factory=list)
    reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningEngine:
    """
    推理引擎
    
    功能：
    1. 多类型推理支持
    2. 思维链生成
    3. 置信度评估
    4. 推理过程追踪
    """
    
    def __init__(self):
        self.config = get_config().cognitive
        self.reasoning_history: List[ReasoningResult] = []
        logger.info("ReasoningEngine initialized")
    
    async def reason(self, 
                     premises: List[str],
                     question: str,
                     reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE) -> ReasoningResult:
        """
        执行推理
        
        Args:
            premises: 前提条件列表
            question: 待解答的问题
            reasoning_type: 推理类型
            
        Returns:
            ReasoningResult: 推理结果
        """
        logger.info(f"Starting {reasoning_type.value} reasoning")
        
        if reasoning_type == ReasoningType.DEDUCTIVE:
            return await self._deductive_reasoning(premises, question)
        elif reasoning_type == ReasoningType.INDUCTIVE:
            return await self._inductive_reasoning(premises, question)
        elif reasoning_type == ReasoningType.ANALOGICAL:
            return await self._analogical_reasoning(premises, question)
        elif reasoning_type == ReasoningType.CAUSAL:
            return await self._causal_reasoning(premises, question)
        else:
            return ReasoningResult(
                conclusion="Unsupported reasoning type",
                confidence=0.0,
                reasoning_type=reasoning_type
            )
    
    async def chain_of_thought(self, 
                               problem: str,
                               max_steps: Optional[int] = None) -> ReasoningResult:
        """
        思维链推理
        
        Args:
            problem: 问题描述
            max_steps: 最大推理步数
            
        Returns:
            ReasoningResult: 推理结果
        """
        max_steps = max_steps or self.config.max_chain_length
        steps: List[ReasoningStep] = []
        
        # 分解问题
        sub_problems = self._decompose_problem(problem)
        
        current_conclusion = ""
        confidence = 1.0
        
        for i, sub in enumerate(sub_problems[:max_steps]):
            step = ReasoningStep(
                step_number=i + 1,
                premise=sub,
                operation="analyze",
                conclusion=f"Step {i+1} analysis of: {sub}",
                confidence=confidence * 0.95,
                reasoning_type=ReasoningType.DEDUCTIVE
            )
            steps.append(step)
            current_conclusion = step.conclusion
        
        result = ReasoningResult(
            conclusion=current_conclusion,
            confidence=confidence,
            steps=steps,
            reasoning_type=ReasoningType.DEDUCTIVE
        )
        
        self.reasoning_history.append(result)
        return result
    
    async def _deductive_reasoning(self, 
                                   premises: List[str], 
                                   question: str) -> ReasoningResult:
        """演绎推理：从一般到特殊"""
        steps = []
        
        for i, premise in enumerate(premises):
            step = ReasoningStep(
                step_number=i + 1,
                premise=premise,
                operation="deduce",
                conclusion=f"From '{premise}', derive implication",
                confidence=0.9 - i * 0.05,
                reasoning_type=ReasoningType.DEDUCTIVE
            )
            steps.append(step)
        
        conclusion = f"Based on {len(premises)} premises, answer to '{question}'"
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=0.85,
            steps=steps,
            reasoning_type=ReasoningType.DEDUCTIVE
        )
    
    async def _inductive_reasoning(self, 
                                   observations: List[str], 
                                   question: str) -> ReasoningResult:
        """归纳推理：从特殊到一般"""
        steps = []
        
        for i, obs in enumerate(observations):
            step = ReasoningStep(
                step_number=i + 1,
                premise=obs,
                operation="generalize",
                conclusion=f"Pattern observed: {obs}",
                confidence=0.8 - i * 0.03,
                reasoning_type=ReasoningType.INDUCTIVE
            )
            steps.append(step)
        
        conclusion = f"Generalized pattern from {len(observations)} observations"
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=0.75,
            steps=steps,
            reasoning_type=ReasoningType.INDUCTIVE
        )
    
    async def _analogical_reasoning(self, 
                                    sources: List[str], 
                                    target: str) -> ReasoningResult:
        """类比推理"""
        steps = []
        
        for i, source in enumerate(sources):
            step = ReasoningStep(
                step_number=i + 1,
                premise=source,
                operation="analogize",
                conclusion=f"'{source}' is analogous to '{target}'",
                confidence=0.7,
                reasoning_type=ReasoningType.ANALOGICAL
            )
            steps.append(step)
        
        return ReasoningResult(
            conclusion=f"Analogical inference to '{target}'",
            confidence=0.7,
            steps=steps,
            reasoning_type=ReasoningType.ANALOGICAL
        )
    
    async def _causal_reasoning(self, 
                                events: List[str], 
                                question: str) -> ReasoningResult:
        """因果推理"""
        steps = []
        
        for i in range(len(events) - 1):
            step = ReasoningStep(
                step_number=i + 1,
                premise=events[i],
                operation="cause_effect",
                conclusion=f"'{events[i]}' causes '{events[i+1]}'",
                confidence=0.75,
                reasoning_type=ReasoningType.CAUSAL
            )
            steps.append(step)
        
        return ReasoningResult(
            conclusion=f"Causal analysis for: {question}",
            confidence=0.75,
            steps=steps,
            reasoning_type=ReasoningType.CAUSAL
        )
    
    def _decompose_problem(self, problem: str) -> List[str]:
        """分解问题为子问题"""
        # 简化实现：按句子分割
        parts = problem.replace("?", ".").replace("!", ".").split(".")
        return [p.strip() for p in parts if p.strip()]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_reasoning_count": len(self.reasoning_history),
            "max_chain_length": self.config.max_chain_length,
            "reasoning_depth": self.config.reasoning_depth
        }
