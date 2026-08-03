"""
能力评估模块 (Capability Assessment Module)

定期评估各项能力水平，进行多维度能力评估，分析能力趋势，
识别能力短板，生成能力提升建议和报告。

功能：
1. 定期评估各项能力水平
2. 多维度能力评估（推理、学习、记忆、决策等）
3. 能力趋势分析
4. 能力短板识别
5. 能力提升建议
6. 生成能力报告
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
from collections import defaultdict, deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("evolution.capability_assessment")


class CapabilityDimension(str, Enum):
    """能力维度"""
    REASONING = "reasoning"         # 推理能力
    LEARNING = "learning"           # 学习能力
    MEMORY = "memory"               # 记忆能力
    DECISION = "decision"           # 决策能力
    PLANNING = "planning"           # 规划能力
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    CREATIVITY = "creativity"       # 创造力
    ATTENTION = "attention"         # 注意力
    COMMUNICATION = "communication" # 沟通能力
    ADAPTATION = "adaptation"       # 适应能力
    METACOGNITION = "metacognition" # 元认知能力
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"  # 情感智能


class AssessmentMethod(str, Enum):
    """评估方法"""
    SELF_EVALUATION = "self_evaluation"     # 自我评估
    PERFORMANCE_BASED = "performance_based" # 基于表现
    COMPARATIVE = "comparative"             # 比较评估
    BENCHMARK = "benchmark"                 # 基准测试
    HYBRID = "hybrid"                       # 混合评估


class CapabilityScore(BaseModel):
    """能力评分"""
    score_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dimension: CapabilityDimension = Field(...)
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    method: AssessmentMethod = Field(default=AssessmentMethod.HYBRID)
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)

    @field_validator("score", "confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CapabilityTrend(BaseModel):
    """能力趋势"""
    dimension: CapabilityDimension = Field(...)
    trend_direction: str = Field(..., description="趋势方向: improving/stable/declining")
    trend_strength: float = Field(default=0.0, ge=-1.0, le=1.0)
    avg_score: float = Field(default=0.0, ge=0.0, le=1.0)
    volatility: float = Field(default=0.0, ge=0.0, le=1.0)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    data_points: int = Field(default=0, ge=0)

    @field_validator("avg_score", "volatility")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CapabilityGap(BaseModel):
    """能力差距"""
    gap_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dimension: CapabilityDimension = Field(...)
    current_level: float = Field(..., ge=0.0, le=1.0)
    target_level: float = Field(..., ge=0.0, le=1.0)
    gap_size: float = Field(..., ge=0.0, le=1.0)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: str = Field(default="", description="影响描述")
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("current_level", "target_level", "gap_size", "priority")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ImprovementSuggestion(BaseModel):
    """改进建议"""
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_dimension: CapabilityDimension = Field(...)
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    expected_improvement: float = Field(default=0.1, ge=0.0, le=1.0)
    effort_required: float = Field(default=0.5, ge=0.0, le=1.0)
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    specific_actions: List[str] = Field(default_factory=list)
    resources_needed: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("expected_improvement", "effort_required", "difficulty", "priority")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CapabilityReport(BaseModel):
    """能力报告"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    trends: List[CapabilityTrend] = Field(default_factory=list)
    gaps: List[CapabilityGap] = Field(default_factory=list)
    suggestions: List[ImprovementSuggestion] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    summary: str = Field(default="")

    @field_validator("overall_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CapabilityAssessmentConfig(BaseModel):
    """能力评估配置"""
    assessment_interval: float = Field(default=86400.0, description="评估间隔(秒)")
    history_window_size: int = Field(default=30, description="历史窗口大小")
    min_confidence_threshold: float = Field(default=0.5)
    trend_analysis_window: int = Field(default=7, description="趋势分析窗口")
    enable_auto_assessment: bool = Field(default=True)
    benchmark_targets: Dict[str, float] = Field(default_factory=lambda: {
        dim.value: 0.8 for dim in CapabilityDimension
    })


class CapabilityAssessor:
    """
    能力评估系统

    定期评估各项能力水平，识别短板并生成改进建议。

    Attributes:
        config: 评估配置
        score_history: 评分历史
        assessment_callbacks: 评估回调
    """

    def __init__(self, config: Optional[CapabilityAssessmentConfig] = None):
        self.config = config or CapabilityAssessmentConfig()
        self._score_history: Dict[CapabilityDimension, deque] = {
            dim: deque(maxlen=self.config.history_window_size)
            for dim in CapabilityDimension
        }
        self._last_assessment_time: Optional[datetime] = None
        self._assessment_callbacks: List[Callable[[CapabilityReport], None]] = []
        self._performance_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        logger.info("CapabilityAssessor initialized")

    # ========== 评分记录 ==========

    def record_score(
        self,
        dimension: CapabilityDimension,
        score: float,
        confidence: float = 0.8,
        method: AssessmentMethod = AssessmentMethod.HYBRID,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None
    ) -> CapabilityScore:
        """
        记录能力评分

        Args:
            dimension: 能力维度
            score: 评分 (0-1)
            confidence: 置信度
            method: 评估方法
            context: 上下文
            evidence: 证据

        Returns:
            CapabilityScore: 评分记录
        """
        score_record = CapabilityScore(
            dimension=dimension,
            score=max(0.0, min(1.0, score)),
            confidence=max(0.0, min(1.0, confidence)),
            method=method,
            context=context or {},
            evidence=evidence or []
        )

        self._score_history[dimension].append(score_record)
        logger.debug(f"Recorded score for {dimension.value}: {score:.3f}")
        return score_record

    def record_performance(
        self,
        metric_name: str,
        value: float,
        dimension: Optional[CapabilityDimension] = None
    ) -> None:
        """
        记录性能指标

        Args:
            metric_name: 指标名称
            value: 指标值
            dimension: 关联的能力维度
        """
        self._performance_metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.now(),
            "dimension": dimension.value if dimension else None
        })

    # ========== 评估核心 ==========

    def assess(
        self,
        dimensions: Optional[List[CapabilityDimension]] = None,
        method: AssessmentMethod = AssessmentMethod.HYBRID
    ) -> CapabilityReport:
        """
        执行能力评估

        Args:
            dimensions: 要评估的维度（None则评估所有）
            method: 评估方法

        Returns:
            CapabilityReport: 评估报告
        """
        if dimensions is None:
            dimensions = list(CapabilityDimension)

        end_time = datetime.now()
        start_time = end_time - timedelta(
            seconds=self.config.assessment_interval
        )

        logger.info(f"Starting capability assessment for {len(dimensions)} dimensions")

        dimension_scores: Dict[str, float] = {}
        trends: List[CapabilityTrend] = []
        gaps: List[CapabilityGap] = []

        for dim in dimensions:
            # 计算当前评分
            score = self._calculate_dimension_score(dim, method)
            dimension_scores[dim.value] = score

            # 分析趋势
            trend = self._analyze_trend(dim)
            if trend:
                trends.append(trend)

            # 识别差距
            gap = self._identify_gap(dim, score)
            if gap:
                gaps.append(gap)

        # 计算总体评分
        overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.0

        # 生成建议
        suggestions = self._generate_suggestions(gaps, trends)

        # 识别优势和劣势
        strengths, weaknesses = self._identify_strengths_weaknesses(dimension_scores)

        # 生成总结
        summary = self._generate_summary(
            overall_score, dimension_scores, gaps, trends
        )

        report = CapabilityReport(
            period_start=start_time,
            period_end=end_time,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            trends=trends,
            gaps=gaps,
            suggestions=suggestions,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary
        )

        self._last_assessment_time = end_time

        # 触发回调
        for callback in self._assessment_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.warning(f"Assessment callback failed: {e}")

        logger.info(f"Assessment completed: overall_score={overall_score:.3f}")
        return report

    def auto_assess(self) -> Optional[CapabilityReport]:
        """
        自动评估（检查时间间隔）

        Returns:
            Optional[CapabilityReport]: 评估报告，如果未到时间则返回None
        """
        if not self.config.enable_auto_assessment:
            return None

        now = datetime.now()
        if (self._last_assessment_time is None or
            (now - self._last_assessment_time).total_seconds() >= self.config.assessment_interval):
            return self.assess()

        return None

    def _calculate_dimension_score(
        self,
        dimension: CapabilityDimension,
        method: AssessmentMethod
    ) -> float:
        """计算维度评分"""
        history = list(self._score_history[dimension])

        if not history:
            # 基于性能指标估算
            return self._estimate_from_metrics(dimension)

        # 根据方法选择计算方式
        if method == AssessmentMethod.SELF_EVALUATION:
            # 最新评分
            return history[-1].score
        elif method == AssessmentMethod.PERFORMANCE_BASED:
            # 基于性能的加权平均
            return self._weighted_average(history, weight_by_confidence=True)
        elif method == AssessmentMethod.COMPARATIVE:
            # 与历史最佳比较
            best = max(h.score for h in history)
            current = history[-1].score
            return current / best if best > 0 else current
        else:
            # 混合方法：加权平均，近期权重更高
            return self._weighted_average(history, recency_weight=True)

    def _weighted_average(
        self,
        history: List[CapabilityScore],
        weight_by_confidence: bool = False,
        recency_weight: bool = False
    ) -> float:
        """计算加权平均分"""
        if not history:
            return 0.5

        total_weight = 0.0
        weighted_sum = 0.0

        for i, score in enumerate(history):
            weight = 1.0

            if weight_by_confidence:
                weight *= score.confidence

            if recency_weight:
                # 近期权重更高
                weight *= (1 + i / len(history))

            weighted_sum += score.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _estimate_from_metrics(self, dimension: CapabilityDimension) -> float:
        """从性能指标估算评分"""
        relevant_metrics = [
            m for m in self._performance_metrics.values()
            if m and m[-1].get("dimension") == dimension.value
        ]

        if not relevant_metrics:
            return 0.5  # 默认中等水平

        # 取最近指标的平均值
        values = []
        for metric in relevant_metrics:
            if metric:
                values.append(metric[-1]["value"])

        return sum(values) / len(values) if values else 0.5

    def _analyze_trend(self, dimension: CapabilityDimension) -> Optional[CapabilityTrend]:
        """分析能力趋势"""
        history = list(self._score_history[dimension])

        if len(history) < self.config.trend_analysis_window:
            return None

        recent = history[-self.config.trend_analysis_window:]
        scores = [h.score for h in recent]

        # 计算平均值
        avg_score = sum(scores) / len(scores)

        # 计算波动率
        if len(scores) > 1:
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            volatility = min(1.0, variance ** 0.5)
        else:
            volatility = 0.0

        # 计算趋势（线性回归斜率简化版）
        n = len(scores)
        if n > 1:
            first_half = sum(scores[:n//2]) / max(1, n//2)
            second_half = sum(scores[n//2:]) / max(1, n - n//2)
            trend_strength = second_half - first_half
        else:
            trend_strength = 0.0

        # 确定趋势方向
        if trend_strength > 0.05:
            direction = "improving"
        elif trend_strength < -0.05:
            direction = "declining"
        else:
            direction = "stable"

        return CapabilityTrend(
            dimension=dimension,
            trend_direction=direction,
            trend_strength=trend_strength,
            avg_score=avg_score,
            volatility=volatility,
            period_start=recent[0].timestamp,
            period_end=recent[-1].timestamp,
            data_points=len(recent)
        )

    def _identify_gap(
        self,
        dimension: CapabilityDimension,
        current_score: float
    ) -> Optional[CapabilityGap]:
        """识别能力差距"""
        target = self.config.benchmark_targets.get(dimension.value, 0.8)
        gap_size = max(0.0, target - current_score)

        if gap_size < 0.1:
            return None  # 差距太小，不报告

        # 计算优先级（差距越大优先级越高，但考虑当前水平）
        priority = gap_size * (1.0 - current_score * 0.5)

        impact_descriptions = {
            CapabilityDimension.REASONING: "影响逻辑推导和问题分析质量",
            CapabilityDimension.LEARNING: "影响新知识获取和技能提升速度",
            CapabilityDimension.MEMORY: "影响信息保留和回忆效率",
            CapabilityDimension.DECISION: "影响决策质量和风险把控",
            CapabilityDimension.PLANNING: "影响任务规划和执行效率",
            CapabilityDimension.PROBLEM_SOLVING: "影响复杂问题处理能力",
            CapabilityDimension.CREATIVITY: "影响创新思维和方案生成",
            CapabilityDimension.ATTENTION: "影响专注度和细节把控",
            CapabilityDimension.COMMUNICATION: "影响信息传递和协作效果",
            CapabilityDimension.ADAPTATION: "影响环境适应和变化应对",
            CapabilityDimension.METACOGNITION: "影响自我监控和策略调整",
            CapabilityDimension.EMOTIONAL_INTELLIGENCE: "影响情感理解和人际互动",
        }

        return CapabilityGap(
            dimension=dimension,
            current_level=current_score,
            target_level=target,
            gap_size=gap_size,
            priority=priority,
            impact=impact_descriptions.get(dimension, "影响整体表现")
        )

    def _generate_suggestions(
        self,
        gaps: List[CapabilityGap],
        trends: List[CapabilityTrend]
    ) -> List[ImprovementSuggestion]:
        """生成改进建议"""
        suggestions = []

        # 基于差距生成建议
        for gap in sorted(gaps, key=lambda g: g.priority, reverse=True)[:5]:
            suggestion = self._create_suggestion_for_gap(gap)
            suggestions.append(suggestion)

        # 基于下降趋势生成建议
        declining = [t for t in trends if t.trend_direction == "declining"]
        for trend in declining:
            # 检查是否已有针对该维度的建议
            existing = [s for s in suggestions if s.target_dimension == trend.dimension]
            if not existing:
                suggestion = self._create_suggestion_for_decline(trend)
                suggestions.append(suggestion)

        return suggestions

    def _create_suggestion_for_gap(self, gap: CapabilityGap) -> ImprovementSuggestion:
        """为能力差距创建建议"""
        dimension_actions = {
            CapabilityDimension.REASONING: [
                "练习逻辑推理题目",
                "学习形式逻辑基础",
                "分析复杂论证结构"
            ],
            CapabilityDimension.LEARNING: [
                "尝试新的学习方法",
                "增加知识应用场景",
                "建立知识关联网络"
            ],
            CapabilityDimension.MEMORY: [
                "使用记忆宫殿技巧",
                "定期复习重要内容",
                "建立记忆提取线索"
            ],
            CapabilityDimension.DECISION: [
                "学习决策分析框架",
                "练习概率思维",
                "建立决策日志"
            ],
            CapabilityDimension.PLANNING: [
                "使用目标分解方法",
                "学习时间估算技巧",
                "建立计划复盘机制"
            ],
            CapabilityDimension.PROBLEM_SOLVING: [
                "练习结构化分析方法",
                "学习多种解题策略",
                "参与复杂项目实践"
            ],
            CapabilityDimension.CREATIVITY: [
                "进行头脑风暴练习",
                "学习 lateral thinking",
                "尝试跨领域联想"
            ],
            CapabilityDimension.ATTENTION: [
                "练习正念冥想",
                "减少多任务处理",
                "使用番茄工作法"
            ],
            CapabilityDimension.COMMUNICATION: [
                "练习清晰表达",
                "学习主动倾听",
                "寻求反馈并改进"
            ],
            CapabilityDimension.ADAPTATION: [
                "主动接触新环境",
                "学习快速原型方法",
                "建立灵活思维模式"
            ],
            CapabilityDimension.METACOGNITION: [
                "定期自我反思",
                "监控认知过程",
                "调整学习策略"
            ],
            CapabilityDimension.EMOTIONAL_INTELLIGENCE: [
                "练习情绪识别",
                "学习同理心技巧",
                "建立情感词汇库"
            ],
        }

        actions = dimension_actions.get(gap.dimension, ["持续练习和反馈"])

        return ImprovementSuggestion(
            target_dimension=gap.dimension,
            title=f"提升 {gap.dimension.value} 能力",
            description=f"当前水平 {gap.current_level:.1%}，目标 {gap.target_level:.1%}，差距 {gap.gap_size:.1%}",
            expected_improvement=min(gap.gap_size * 0.5, 0.2),
            effort_required=0.3 + gap.gap_size * 0.4,
            difficulty=0.3 + gap.gap_size * 0.5,
            priority=gap.priority,
            specific_actions=actions,
            resources_needed=["时间投入", "练习材料", "反馈来源"]
        )

    def _create_suggestion_for_decline(self, trend: CapabilityTrend) -> ImprovementSuggestion:
        """为下降趋势创建建议"""
        return ImprovementSuggestion(
            target_dimension=trend.dimension,
            title=f"阻止 {trend.dimension.value} 能力下降",
            description=f"检测到下降趋势（强度: {trend.trend_strength:.3f}），需要及时干预",
            expected_improvement=abs(trend.trend_strength) * 0.5,
            effort_required=0.5,
            difficulty=0.4,
            priority=0.7,
            specific_actions=[
                "分析下降原因",
                "恢复基础练习",
                "调整相关策略"
            ],
            resources_needed=["诊断时间", "练习资源"]
        )

    def _identify_strengths_weaknesses(
        self,
        dimension_scores: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """识别优势和劣势"""
        if not dimension_scores:
            return [], []

        sorted_scores = sorted(dimension_scores.items(), key=lambda x: x[1])

        # 优势：前3名且分数>0.6
        strengths = [
            dim for dim, score in sorted_scores[-3:]
            if score > 0.6
        ]

        # 劣势：后3名且分数<0.5
        weaknesses = [
            dim for dim, score in sorted_scores[:3]
            if score < 0.5
        ]

        return strengths, weaknesses

    def _generate_summary(
        self,
        overall_score: float,
        dimension_scores: Dict[str, float],
        gaps: List[CapabilityGap],
        trends: List[CapabilityTrend]
    ) -> str:
        """生成评估总结"""
        improving = sum(1 for t in trends if t.trend_direction == "improving")
        declining = sum(1 for t in trends if t.trend_direction == "declining")
        stable = sum(1 for t in trends if t.trend_direction == "stable")

        summary_parts = [
            f"整体能力评分: {overall_score:.1%}。",
            f"评估维度: {len(dimension_scores)} 个。",
            f"趋势: {improving} 个提升, {stable} 个稳定, {declining} 个下降。"
        ]

        if gaps:
            top_gap = max(gaps, key=lambda g: g.priority)
            summary_parts.append(
                f"最需要改进: {top_gap.dimension.value}（差距 {top_gap.gap_size:.1%}）。"
            )

        if overall_score > 0.8:
            summary_parts.append("整体表现优秀，继续保持。")
        elif overall_score > 0.6:
            summary_parts.append("整体表现良好，仍有提升空间。")
        else:
            summary_parts.append("整体表现需要重点关注和改进。")

        return " ".join(summary_parts)

    # ========== 回调注册 ==========

    def register_assessment_callback(
        self,
        callback: Callable[[CapabilityReport], None]
    ) -> None:
        """
        注册评估回调

        Args:
            callback: 回调函数
        """
        self._assessment_callbacks.append(callback)
        logger.debug("Registered assessment callback")

    # ========== 查询接口 ==========

    def get_dimension_score(
        self,
        dimension: CapabilityDimension
    ) -> Optional[float]:
        """
        获取维度当前评分

        Args:
            dimension: 能力维度

        Returns:
            Optional[float]: 评分
        """
        history = self._score_history[dimension]
        if not history:
            return None
        return history[-1].score

    def get_dimension_history(
        self,
        dimension: CapabilityDimension,
        limit: int = 30
    ) -> List[CapabilityScore]:
        """
        获取维度历史评分

        Args:
            dimension: 能力维度
            limit: 数量限制

        Returns:
            List[CapabilityScore]: 评分列表
        """
        return list(self._score_history[dimension])[-limit:]

    def get_all_scores(self) -> Dict[str, float]:
        """
        获取所有维度当前评分

        Returns:
            Dict[str, float]: 评分字典
        """
        return {
            dim.value: (history[-1].score if history else 0.5)
            for dim, history in self._score_history.items()
        }

    def get_trends(self) -> List[CapabilityTrend]:
        """
        获取所有趋势

        Returns:
            List[CapabilityTrend]: 趋势列表
        """
        trends = []
        for dim in CapabilityDimension:
            trend = self._analyze_trend(dim)
            if trend:
                trends.append(trend)
        return trends

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_scores = sum(len(h) for h in self._score_history.values())
        dimensions_with_data = sum(1 for h in self._score_history.values() if h)

        return {
            "total_scores_recorded": total_scores,
            "dimensions_with_data": dimensions_with_data,
            "last_assessment": self._last_assessment_time.isoformat() if self._last_assessment_time else None,
            "current_scores": self.get_all_scores(),
            "performance_metrics": {
                name: len(values) for name, values in self._performance_metrics.items()
            }
        }

    def reset(self) -> None:
        """重置所有状态"""
        for history in self._score_history.values():
            history.clear()
        self._performance_metrics.clear()
        self._last_assessment_time = None
        logger.info("CapabilityAssessor reset")
