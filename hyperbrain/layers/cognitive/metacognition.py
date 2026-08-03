"""
元认知模块 (Metacognition Module)

实现对自身认知过程的监控和调节：
- 认知过程监控
- 认知效果评估
- 认知策略调整
- 自我提问机制
- 认知偏差检测
"""

import uuid
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.metacognition")


class CognitiveState(str, Enum):
    """认知状态枚举"""
    FOCUSED = "focused"              # 专注
    DISTRACTED = "distracted"        # 分心
    CONFUSED = "confused"            # 困惑
    CONFIDENT = "confident"          # 自信
    TIRED = "tired"                  # 疲劳
    OPTIMAL = "optimal"              # 最佳状态


class BiasType(str, Enum):
    """认知偏差类型"""
    CONFIRMATION = "confirmation"    # 确认偏差
    ANCHORING = "anchoring"          # 锚定效应
    AVAILABILITY = "availability"    # 可得性偏差
    OVERCONFIDENCE = "overconfidence"  # 过度自信
    FRAMING = "framing"              # 框架效应
    RECENCY = "recency"              # 近因效应
    SUNK_COST = "sunk_cost"          # 沉没成本
    GROUPTHINK = "groupthink"        # 群体思维


class MonitoringEvent(BaseModel):
    """监控事件模型"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_type: str = Field(...)
    metric_name: str = Field(...)
    metric_value: float = Field(...)
    threshold: Optional[float] = Field(default=None)
    is_alert: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)


class SelfQuestion(BaseModel):
    """自我提问模型"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str = Field(...)
    category: str = Field(default="general")
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    is_answered: bool = Field(default=False)
    answer: Optional[str] = Field(default=None)
    triggered_by: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class BiasDetection(BaseModel):
    """偏差检测结果"""
    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bias_type: BiasType = Field(...)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = Field(default="")
    evidence: List[str] = Field(default_factory=list)
    mitigation_suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class StrategyAdjustment(BaseModel):
    """策略调整记录"""
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_strategy: str = Field(...)
    adjusted_strategy: str = Field(...)
    reason: str = Field(default="")
    expected_improvement: float = Field(default=0.0)
    actual_improvement: Optional[float] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)


class CognitivePerformance(BaseModel):
    """认知表现评估"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    speed: float = Field(default=0.0, ge=0.0, le=1.0)
    efficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    adaptability: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("accuracy", "speed", "efficiency", "consistency", "adaptability", "overall_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class MetacognitionMonitor:
    """
    元认知监控器

    监控和调节认知过程，检测认知偏差，评估认知效果。

    Attributes:
        monitoring_history: 监控历史
        self_questions: 自我提问列表
        bias_detections: 偏差检测记录
        strategy_adjustments: 策略调整记录
        performance_history: 表现历史
    """

    def __init__(
        self,
        monitoring_window: int = 100,
        alert_threshold: float = 0.3,
        enable_logging: bool = True
    ):
        self.monitoring_history: deque = deque(maxlen=monitoring_window)
        self.self_questions: List[SelfQuestion] = []
        self.bias_detections: List[BiasDetection] = []
        self.strategy_adjustments: List[StrategyAdjustment] = []
        self.performance_history: List[CognitivePerformance] = []
        self.alert_threshold = alert_threshold
        self.enable_logging = enable_logging

        self._question_templates: Dict[str, List[str]] = {
            "comprehension": [
                "我真正理解这个问题了吗？",
                "这个问题的关键信息是什么？",
                "我是否遗漏了重要细节？"
            ],
            "strategy": [
                "我当前的方法是最有效的吗？",
                "有没有其他更好的解决思路？",
                "我的推理过程是否有漏洞？"
            ],
            "progress": [
                "我目前的进展如何？",
                "是否偏离了目标？",
                "还需要多长时间完成？"
            ],
            "confidence": [
                "我对这个结论有多大把握？",
                "有没有考虑过反面证据？",
                "是否存在过度自信的可能？"
            ],
            "bias": [
                "我是否只关注了支持自己观点的证据？",
                "最初的假设是否影响了我的判断？",
                "最近的信息是否被过度重视？"
            ]
        }

        if enable_logging:
            logger.info("MetacognitionMonitor initialized")

    def monitor_process(
        self,
        process_type: str,
        metric_name: str,
        metric_value: float,
        threshold: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MonitoringEvent:
        """
        监控认知过程

        Args:
            process_type: 过程类型
            metric_name: 指标名称
            metric_value: 指标值
            threshold: 阈值
            context: 上下文

        Returns:
            MonitoringEvent: 监控事件
        """
        effective_threshold = threshold or self.alert_threshold
        is_alert = metric_value < effective_threshold

        event = MonitoringEvent(
            process_type=process_type,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=effective_threshold,
            is_alert=is_alert,
            context=context or {}
        )

        self.monitoring_history.append(event)

        if is_alert:
            logger.warning(
                f"Alert: {process_type}.{metric_name} = {metric_value:.3f} "
                f"(threshold: {effective_threshold:.3f})"
            )

        return event

    def assess_performance(
        self,
        accuracy: float,
        speed: float,
        efficiency: Optional[float] = None,
        consistency: Optional[float] = None,
        adaptability: Optional[float] = None
    ) -> CognitivePerformance:
        """
        评估认知表现

        Args:
            accuracy: 准确率
            speed: 速度
            efficiency: 效率
            consistency: 一致性
            adaptability: 适应性

        Returns:
            CognitivePerformance: 表现评估
        """
        eff = efficiency or (accuracy + speed) / 2
        cons = consistency or accuracy
        adap = adaptability or speed

        overall = (accuracy * 0.3 + speed * 0.2 + eff * 0.2 + cons * 0.15 + adap * 0.15)

        performance = CognitivePerformance(
            accuracy=accuracy,
            speed=speed,
            efficiency=eff,
            consistency=cons,
            adaptability=adap,
            overall_score=overall
        )

        self.performance_history.append(performance)

        self.monitor_process(
            process_type="performance",
            metric_name="overall_score",
            metric_value=overall,
            threshold=0.5
        )

        logger.info(f"Performance assessed: overall={overall:.3f}")
        return performance

    def generate_self_questions(
        self,
        category: Optional[str] = None,
        triggered_by: str = ""
    ) -> List[SelfQuestion]:
        """
        生成自我提问

        Args:
            category: 问题类别
            triggered_by: 触发原因

        Returns:
            List[SelfQuestion]: 自我提问列表
        """
        questions = []

        if category and category in self._question_templates:
            templates = self._question_templates[category]
        else:
            templates = []
            for qs in self._question_templates.values():
                templates.extend(qs)

        for template in templates[:5]:
            question = SelfQuestion(
                question=template,
                category=category or "general",
                triggered_by=triggered_by,
                priority=0.7
            )
            self.self_questions.append(question)
            questions.append(question)

        logger.debug(f"Generated {len(questions)} self-questions")
        return questions

    def answer_self_question(
        self,
        question_id: str,
        answer: str
    ) -> bool:
        """
        回答自我提问

        Args:
            question_id: 问题ID
            answer: 答案

        Returns:
            bool: 是否成功
        """
        for q in self.self_questions:
            if q.question_id == question_id:
                q.answer = answer
                q.is_answered = True
                logger.debug(f"Answered self-question: {question_id}")
                return True
        return False

    def detect_bias(
        self,
        reasoning_process: Dict[str, Any],
        evidence: List[str]
    ) -> List[BiasDetection]:
        """
        检测认知偏差

        Args:
            reasoning_process: 推理过程
            evidence: 证据列表

        Returns:
            List[BiasDetection]: 检测到的偏差
        """
        detections = []

        confirmation = self._detect_confirmation_bias(reasoning_process, evidence)
        if confirmation:
            detections.append(confirmation)

        anchoring = self._detect_anchoring_bias(reasoning_process)
        if anchoring:
            detections.append(anchoring)

        availability = self._detect_availability_bias(reasoning_process)
        if availability:
            detections.append(availability)

        overconfidence = self._detect_overconfidence(reasoning_process)
        if overconfidence:
            detections.append(overconfidence)

        self.bias_detections.extend(detections)

        if detections:
            logger.warning(f"Detected {len(detections)} cognitive biases")

        return detections

    def adjust_strategy(
        self,
        current_strategy: str,
        performance: CognitivePerformance,
        reason: str = ""
    ) -> Optional[StrategyAdjustment]:
        """
        调整认知策略

        Args:
            current_strategy: 当前策略
            performance: 当前表现
            reason: 调整原因

        Returns:
            Optional[StrategyAdjustment]: 调整记录
        """
        if performance.overall_score >= 0.8:
            logger.info("Performance is good, no strategy adjustment needed")
            return None

        adjusted = self._suggest_strategy_change(current_strategy, performance)

        if adjusted == current_strategy:
            return None

        expected_improvement = max(0.0, 0.8 - performance.overall_score)

        adjustment = StrategyAdjustment(
            original_strategy=current_strategy,
            adjusted_strategy=adjusted,
            reason=reason or f"表现评分较低: {performance.overall_score:.3f}",
            expected_improvement=expected_improvement
        )

        self.strategy_adjustments.append(adjustment)
        logger.info(f"Strategy adjusted: {current_strategy} -> {adjusted}")
        return adjustment

    def evaluate_strategy_effectiveness(
        self,
        adjustment_id: str,
        new_performance: CognitivePerformance
    ) -> Dict[str, Any]:
        """
        评估策略调整效果

        Args:
            adjustment_id: 调整记录ID
            new_performance: 新表现

        Returns:
            Dict[str, Any]: 评估结果
        """
        adjustment = next(
            (a for a in self.strategy_adjustments if a.adjustment_id == adjustment_id),
            None
        )

        if not adjustment:
            return {"error": "Adjustment not found"}

        improvement = new_performance.overall_score - (
            self.performance_history[-2].overall_score
            if len(self.performance_history) >= 2 else 0.0
        )

        adjustment.actual_improvement = improvement

        return {
            "adjustment_id": adjustment_id,
            "expected_improvement": adjustment.expected_improvement,
            "actual_improvement": improvement,
            "is_effective": improvement > 0,
            "new_overall_score": new_performance.overall_score
        }

    def get_cognitive_state(self) -> Dict[str, Any]:
        """
        获取当前认知状态

        Returns:
            Dict[str, Any]: 认知状态
        """
        if not self.performance_history:
            return {"state": CognitiveState.OPTIMAL.value, "confidence": 0.5}

        recent = self.performance_history[-10:]
        avg_score = sum(p.overall_score for p in recent) / len(recent)
        variance = sum((p.overall_score - avg_score) ** 2 for p in recent) / len(recent)

        if avg_score > 0.8 and variance < 0.05:
            state = CognitiveState.OPTIMAL
        elif avg_score > 0.7:
            state = CognitiveState.CONFIDENT
        elif avg_score > 0.5:
            state = CognitiveState.FOCUSED
        elif variance > 0.1:
            state = CognitiveState.CONFUSED
        elif avg_score < 0.3:
            state = CognitiveState.TIRED
        else:
            state = CognitiveState.DISTRACTED

        return {
            "state": state.value,
            "average_score": avg_score,
            "variance": variance,
            "recent_performances": [p.overall_score for p in recent],
            "unanswered_questions": sum(1 for q in self.self_questions if not q.is_answered),
            "detected_biases": len(self.bias_detections)
        }

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        alerts = sum(1 for e in self.monitoring_history if e.is_alert)
        total = len(self.monitoring_history)

        return {
            "total_events": total,
            "alert_count": alerts,
            "alert_rate": alerts / max(total, 1),
            "unanswered_questions": sum(1 for q in self.self_questions if not q.is_answered),
            "total_questions": len(self.self_questions),
            "bias_detections": len(self.bias_detections),
            "strategy_adjustments": len(self.strategy_adjustments),
            "performance_assessments": len(self.performance_history)
        }

    def get_recent_alerts(self, limit: int = 10) -> List[MonitoringEvent]:
        """获取最近的警报"""
        alerts = [e for e in self.monitoring_history if e.is_alert]
        return list(alerts)[-limit:]

    def _detect_confirmation_bias(
        self,
        reasoning: Dict[str, Any],
        evidence: List[str]
    ) -> Optional[BiasDetection]:
        """检测确认偏差"""
        supporting = reasoning.get("supporting_evidence", [])
        opposing = reasoning.get("opposing_evidence", [])

        if not supporting:
            return None

        total = len(supporting) + len(opposing)
        if total == 0:
            return None

        ratio = len(supporting) / total
        if ratio > 0.8 and len(opposing) > 0:
            return BiasDetection(
                bias_type=BiasType.CONFIRMATION,
                confidence=(ratio - 0.5) * 2,
                description="支持证据远多于反对证据，可能存在确认偏差",
                evidence=[f"支持: {len(supporting)}, 反对: {len(opposing)}"],
                mitigation_suggestions=[
                    "主动寻找反面证据",
                    "考虑替代解释",
                    "进行证伪检验"
                ]
            )

        if len(supporting) >= 3 and len(opposing) <= 1:
            return BiasDetection(
                bias_type=BiasType.CONFIRMATION,
                confidence=min(1.0, 0.5 + len(supporting) * 0.1),
                description="支持证据显著多于反对证据，可能存在确认偏差",
                evidence=[f"支持: {len(supporting)}, 反对: {len(opposing)}"],
                mitigation_suggestions=[
                    "主动寻找反面证据",
                    "考虑替代解释",
                    "进行证伪检验"
                ]
            )

        return None

    def _detect_anchoring_bias(
        self,
        reasoning: Dict[str, Any]
    ) -> Optional[BiasDetection]:
        """检测锚定效应"""
        initial_estimate = reasoning.get("initial_estimate")
        final_estimate = reasoning.get("final_estimate")

        if initial_estimate is None or final_estimate is None:
            return None

        deviation = abs(final_estimate - initial_estimate) / max(abs(initial_estimate), 0.001)
        if deviation < 0.1:
            return BiasDetection(
                bias_type=BiasType.ANCHORING,
                confidence=0.7,
                description="最终估计过于接近初始估计，可能存在锚定效应",
                evidence=[f"初始: {initial_estimate}, 最终: {final_estimate}"],
                mitigation_suggestions=[
                    "重新独立评估",
                    "考虑多个参考点",
                    "延迟给出初始估计"
                ]
            )
        return None

    def _detect_availability_bias(
        self,
        reasoning: Dict[str, Any]
    ) -> Optional[BiasDetection]:
        """检测可得性偏差"""
        recent_examples = reasoning.get("recent_examples", [])
        total_examples = reasoning.get("total_examples", [])

        if len(recent_examples) > 0 and len(total_examples) > 0:
            recent_ratio = len(recent_examples) / len(total_examples)
            if recent_ratio > 0.7:
                return BiasDetection(
                    bias_type=BiasType.AVAILABILITY,
                    confidence=recent_ratio * 0.8,
                    description="过度依赖近期例子，可能存在可得性偏差",
                    evidence=[f"近期例子占比: {recent_ratio:.1%}"],
                    mitigation_suggestions=[
                        "考虑历史数据",
                        "使用系统抽样",
                        "检查样本代表性"
                    ]
                )
        return None

    def _detect_overconfidence(
        self,
        reasoning: Dict[str, Any]
    ) -> Optional[BiasDetection]:
        """检测过度自信"""
        stated_confidence = reasoning.get("stated_confidence", 0.5)
        actual_accuracy = reasoning.get("actual_accuracy", 0.5)

        gap = stated_confidence - actual_accuracy
        if gap > 0.3:
            return BiasDetection(
                bias_type=BiasType.OVERCONFIDENCE,
                confidence=min(1.0, gap),
                description="声明的置信度远高于实际准确率",
                evidence=[f"置信度: {stated_confidence:.2f}, 准确率: {actual_accuracy:.2f}"],
                mitigation_suggestions=[
                    "校准置信度评估",
                    "寻求外部反馈",
                    "考虑不确定性范围"
                ]
            )
        return None

    def _suggest_strategy_change(
        self,
        current: str,
        performance: CognitivePerformance
    ) -> str:
        """建议策略变更"""
        if performance.accuracy < 0.5:
            return "更谨慎的分析方法"
        elif performance.speed < 0.5:
            return "更高效的启发式方法"
        elif performance.consistency < 0.5:
            return "标准化的处理流程"
        elif performance.adaptability < 0.5:
            return "更灵活的策略组合"
        else:
            return "综合优化方法"
