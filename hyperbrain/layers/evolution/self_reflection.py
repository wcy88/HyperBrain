"""
自我反思模块 (Self Reflection Module)

定期反思自己的行为、决策和认知过程，生成反思报告并识别改进机会。

功能：
1. 行为回顾和分析
2. 决策质量评估
3. 认知策略效果评估
4. 生成反思报告
5. 识别改进机会
"""

import uuid
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict, deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("evolution.self_reflection")


class ReflectionScope(str, Enum):
    """反思范围"""
    BEHAVIOR = "behavior"           # 行为反思
    DECISION = "decision"           # 决策反思
    COGNITION = "cognition"         # 认知反思
    LEARNING = "learning"           # 学习反思
    EMOTION = "emotion"             # 情感反思
    OVERALL = "overall"             # 整体反思


class ReflectionPeriod(str, Enum):
    """反思周期"""
    SHORT = "short"                 # 短期（最近1小时）
    MEDIUM = "medium"               # 中期（最近1天）
    LONG = "long"                   # 长期（最近1周）


class BehaviorRecord(BaseModel):
    """行为记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., description="行为描述")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文")
    timestamp: datetime = Field(default_factory=datetime.now)
    duration: float = Field(default=0.0, description="持续时间(秒)")
    outcome: Optional[str] = Field(default=None, description="结果")
    success: Optional[bool] = Field(default=None, description="是否成功")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class DecisionRecord(BaseModel):
    """决策记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_name: str = Field(..., description="决策名称")
    alternatives: List[str] = Field(default_factory=list, description="备选方案")
    selected: str = Field(..., description="选中的方案")
    reasoning: str = Field(default="", description="决策理由")
    timestamp: datetime = Field(default_factory=datetime.now)
    expected_outcome: str = Field(default="", description="预期结果")
    actual_outcome: Optional[str] = Field(default=None, description="实际结果")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("confidence", "quality_score")
    @classmethod
    def validate_score(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return max(0.0, min(1.0, v))


class CognitiveStrategyRecord(BaseModel):
    """认知策略记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    timestamp: datetime = Field(default_factory=datetime.now)
    effectiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    usage_count: int = Field(default=1, ge=0)
    success_count: int = Field(default=0, ge=0)

    @field_validator("effectiveness")
    @classmethod
    def validate_effectiveness(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ReflectionInsight(BaseModel):
    """反思洞察"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scope: ReflectionScope = Field(..., description="反思范围")
    title: str = Field(..., description="洞察标题")
    description: str = Field(..., description="洞察描述")
    evidence: List[str] = Field(default_factory=list, description="支持证据")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: str = Field(default="medium", description="严重程度")
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ImprovementOpportunity(BaseModel):
    """改进机会"""
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_scope: ReflectionScope = Field(..., description="目标范围")
    description: str = Field(..., description="改进描述")
    expected_benefit: float = Field(default=0.5, ge=0.0, le=1.0)
    implementation_difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    suggested_actions: List[str] = Field(default_factory=list)
    related_insights: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("expected_benefit", "implementation_difficulty", "priority")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ReflectionReport(BaseModel):
    """反思报告"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period: ReflectionPeriod = Field(..., description="反思周期")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    scopes: List[ReflectionScope] = Field(default_factory=list)
    insights: List[ReflectionInsight] = Field(default_factory=list)
    opportunities: List[ImprovementOpportunity] = Field(default_factory=list)
    summary: str = Field(default="", description="总结")
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("overall_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class SelfReflectionConfig(BaseModel):
    """自我反思配置"""
    enable_auto_reflection: bool = Field(default=True)
    short_term_interval: float = Field(default=3600.0, description="短期反思间隔(秒)")
    medium_term_interval: float = Field(default=86400.0, description="中期反思间隔(秒)")
    long_term_interval: float = Field(default=604800.0, description="长期反思间隔(秒)")
    max_behavior_history: int = Field(default=1000)
    max_decision_history: int = Field(default=500)
    max_strategy_history: int = Field(default=200)
    min_confidence_threshold: float = Field(default=0.3)
    importance_threshold: float = Field(default=0.4)


class SelfReflection:
    """
    自我反思系统

    定期反思自己的行为、决策和认知过程，识别改进机会。

    Attributes:
        config: 反思配置
        behavior_history: 行为历史记录
        decision_history: 决策历史记录
        strategy_history: 策略历史记录
        reflection_reports: 反思报告列表
        last_reflection_time: 上次反思时间
    """

    def __init__(self, config: Optional[SelfReflectionConfig] = None):
        self.config = config or SelfReflectionConfig()
        self._behavior_history: deque = deque(maxlen=self.config.max_behavior_history)
        self._decision_history: deque = deque(maxlen=self.config.max_decision_history)
        self._strategy_history: deque = deque(maxlen=self.config.max_strategy_history)
        self._reflection_reports: List[ReflectionReport] = []
        self._last_reflection_time: Dict[ReflectionPeriod, datetime] = {
            ReflectionPeriod.SHORT: datetime.now() - timedelta(hours=2),
            ReflectionPeriod.MEDIUM: datetime.now() - timedelta(days=2),
            ReflectionPeriod.LONG: datetime.now() - timedelta(weeks=2),
        }
        self._reflection_callbacks: List[Callable[[ReflectionReport], None]] = []
        logger.info("SelfReflection initialized")

    # ========== 记录接口 ==========

    def record_behavior(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        outcome: Optional[str] = None,
        success: Optional[bool] = None,
        importance: float = 0.5
    ) -> BehaviorRecord:
        """
        记录行为

        Args:
            action: 行为描述
            context: 上下文信息
            duration: 持续时间
            outcome: 结果
            success: 是否成功
            importance: 重要性

        Returns:
            BehaviorRecord: 行为记录
        """
        record = BehaviorRecord(
            action=action,
            context=context or {},
            duration=duration,
            outcome=outcome,
            success=success,
            importance=importance
        )
        self._behavior_history.append(record)
        logger.debug(f"Recorded behavior: {action}")
        return record

    def record_decision(
        self,
        decision_name: str,
        alternatives: List[str],
        selected: str,
        reasoning: str = "",
        expected_outcome: str = "",
        confidence: float = 0.5
    ) -> DecisionRecord:
        """
        记录决策

        Args:
            decision_name: 决策名称
            alternatives: 备选方案
            selected: 选中的方案
            reasoning: 决策理由
            expected_outcome: 预期结果
            confidence: 置信度

        Returns:
            DecisionRecord: 决策记录
        """
        record = DecisionRecord(
            decision_name=decision_name,
            alternatives=alternatives,
            selected=selected,
            reasoning=reasoning,
            expected_outcome=expected_outcome,
            confidence=confidence
        )
        self._decision_history.append(record)
        logger.debug(f"Recorded decision: {decision_name}")
        return record

    def record_strategy(
        self,
        strategy_name: str,
        strategy_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        effectiveness: float = 0.5
    ) -> CognitiveStrategyRecord:
        """
        记录认知策略

        Args:
            strategy_name: 策略名称
            strategy_type: 策略类型
            parameters: 策略参数
            effectiveness: 有效性

        Returns:
            CognitiveStrategyRecord: 策略记录
        """
        # 检查是否已有相同策略
        for existing in self._strategy_history:
            if (existing.strategy_name == strategy_name and
                existing.strategy_type == strategy_type):
                existing.usage_count += 1
                if effectiveness > 0.6:
                    existing.success_count += 1
                # 更新有效性（滑动平均）
                existing.effectiveness = (
                    existing.effectiveness * 0.7 + effectiveness * 0.3
                )
                logger.debug(f"Updated strategy: {strategy_name}")
                return existing

        record = CognitiveStrategyRecord(
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            parameters=parameters or {},
            effectiveness=effectiveness
        )
        self._strategy_history.append(record)
        logger.debug(f"Recorded new strategy: {strategy_name}")
        return record

    def update_decision_outcome(
        self,
        record_id: str,
        actual_outcome: str,
        quality_score: float
    ) -> bool:
        """
        更新决策结果

        Args:
            record_id: 记录ID
            actual_outcome: 实际结果
            quality_score: 质量评分

        Returns:
            bool: 是否成功更新
        """
        for record in self._decision_history:
            if record.record_id == record_id:
                record.actual_outcome = actual_outcome
                record.quality_score = quality_score
                logger.debug(f"Updated decision outcome: {record_id}")
                return True
        return False

    # ========== 反思核心 ==========

    def reflect(
        self,
        period: ReflectionPeriod = ReflectionPeriod.MEDIUM,
        scopes: Optional[List[ReflectionScope]] = None
    ) -> ReflectionReport:
        """
        执行反思

        Args:
            period: 反思周期
            scopes: 反思范围列表

        Returns:
            ReflectionReport: 反思报告
        """
        if scopes is None:
            scopes = [ReflectionScope.OVERALL]

        end_time = datetime.now()
        start_time = self._get_period_start(period)

        logger.info(f"Starting reflection for period: {period.value}")

        insights: List[ReflectionInsight] = []
        opportunities: List[ImprovementOpportunity] = []

        for scope in scopes:
            scope_insights = self._reflect_on_scope(scope, start_time, end_time)
            insights.extend(scope_insights)

            scope_opportunities = self._identify_opportunities(scope, scope_insights)
            opportunities.extend(scope_opportunities)

        # 生成总结
        summary = self._generate_summary(insights, opportunities)
        overall_score = self._calculate_overall_score(insights)

        report = ReflectionReport(
            period=period,
            start_time=start_time,
            end_time=end_time,
            scopes=scopes,
            insights=insights,
            opportunities=opportunities,
            summary=summary,
            overall_score=overall_score
        )

        self._reflection_reports.append(report)
        self._last_reflection_time[period] = end_time

        # 触发回调
        for callback in self._reflection_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.warning(f"Reflection callback failed: {e}")

        logger.info(f"Reflection completed: {len(insights)} insights, {len(opportunities)} opportunities")
        return report

    def auto_reflect(self) -> Optional[ReflectionReport]:
        """
        自动执行反思（检查时间间隔）

        Returns:
            Optional[ReflectionReport]: 反思报告，如果未到时间则返回None
        """
        now = datetime.now()
        report = None

        for period, interval in [
            (ReflectionPeriod.SHORT, self.config.short_term_interval),
            (ReflectionPeriod.MEDIUM, self.config.medium_term_interval),
            (ReflectionPeriod.LONG, self.config.long_term_interval),
        ]:
            last_time = self._last_reflection_time.get(period, datetime.min)
            if (now - last_time).total_seconds() >= interval:
                scopes = self._get_default_scopes(period)
                report = self.reflect(period=period, scopes=scopes)

        return report

    def _reflect_on_scope(
        self,
        scope: ReflectionScope,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """
        对指定范围进行反思

        Args:
            scope: 反思范围
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[ReflectionInsight]: 洞察列表
        """
        if scope == ReflectionScope.BEHAVIOR:
            return self._reflect_on_behavior(start_time, end_time)
        elif scope == ReflectionScope.DECISION:
            return self._reflect_on_decisions(start_time, end_time)
        elif scope == ReflectionScope.COGNITION:
            return self._reflect_on_cognition(start_time, end_time)
        elif scope == ReflectionScope.LEARNING:
            return self._reflect_on_learning(start_time, end_time)
        elif scope == ReflectionScope.EMOTION:
            return self._reflect_on_emotion(start_time, end_time)
        else:
            # 整体反思
            all_insights = []
            for s in ReflectionScope:
                if s != ReflectionScope.OVERALL:
                    all_insights.extend(self._reflect_on_scope(s, start_time, end_time))
            return all_insights

    def _reflect_on_behavior(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """反思行为"""
        insights = []
        behaviors = [
            b for b in self._behavior_history
            if start_time <= b.timestamp <= end_time
        ]

        if not behaviors:
            return insights

        # 分析行为成功率
        successful = [b for b in behaviors if b.success is True]
        failed = [b for b in behaviors if b.success is False]
        total = len([b for b in behaviors if b.success is not None])

        if total > 0:
            success_rate = len(successful) / total
            if success_rate < 0.5:
                insights.append(ReflectionInsight(
                    scope=ReflectionScope.BEHAVIOR,
                    title="行为成功率偏低",
                    description=f"近期行为成功率仅为 {success_rate:.1%}，需要审视执行策略",
                    evidence=[b.action for b in failed[:5]],
                    confidence=0.7,
                    severity="high"
                ))
            elif success_rate > 0.9:
                insights.append(ReflectionInsight(
                    scope=ReflectionScope.BEHAVIOR,
                    title="行为表现优秀",
                    description=f"近期行为成功率高达 {success_rate:.1%}，策略有效",
                    evidence=[b.action for b in successful[:5]],
                    confidence=0.8,
                    severity="low"
                ))

        # 分析行为模式
        action_counts = defaultdict(int)
        for b in behaviors:
            action_counts[b.action] += 1

        most_common = max(action_counts.items(), key=lambda x: x[1])
        if most_common[1] > len(behaviors) * 0.5:
            insights.append(ReflectionInsight(
                scope=ReflectionScope.BEHAVIOR,
                title="行为模式单一",
                description=f"'{most_common[0]}' 占比过高，建议增加行为多样性",
                evidence=[f"{k}: {v}次" for k, v in sorted(action_counts.items(), key=lambda x: -x[1])[:5]],
                confidence=0.6,
                severity="medium"
            ))

        return insights

    def _reflect_on_decisions(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """反思决策"""
        insights = []
        decisions = [
            d for d in self._decision_history
            if start_time <= d.timestamp <= end_time
        ]

        if not decisions:
            return insights

        # 分析决策质量
        scored_decisions = [d for d in decisions if d.quality_score is not None]
        if scored_decisions:
            avg_quality = sum(d.quality_score for d in scored_decisions) / len(scored_decisions)
            if avg_quality < 0.5:
                insights.append(ReflectionInsight(
                    scope=ReflectionScope.DECISION,
                    title="决策质量有待提升",
                    description=f"平均决策质量评分 {avg_quality:.2f}，建议加强信息收集",
                    evidence=[d.decision_name for d in scored_decisions[:5]],
                    confidence=0.7,
                    severity="high"
                ))

        # 分析决策置信度偏差
        high_confidence_poor = [
            d for d in scored_decisions
            if d.confidence > 0.8 and d.quality_score is not None and d.quality_score < 0.4
        ]
        if high_confidence_poor:
            insights.append(ReflectionInsight(
                scope=ReflectionScope.DECISION,
                title="过度自信偏差",
                description=f"存在 {len(high_confidence_poor)} 次高置信度但低质量的决策",
                evidence=[d.decision_name for d in high_confidence_poor[:3]],
                confidence=0.8,
                severity="high"
            ))

        return insights

    def _reflect_on_cognition(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """反思认知策略"""
        insights = []
        strategies = [
            s for s in self._strategy_history
            if start_time <= s.timestamp <= end_time
        ]

        if not strategies:
            return insights

        # 分析策略效果
        avg_effectiveness = sum(s.effectiveness for s in strategies) / len(strategies)
        if avg_effectiveness < 0.4:
            insights.append(ReflectionInsight(
                scope=ReflectionScope.COGNITION,
                title="认知策略效果不佳",
                description=f"平均策略有效性仅 {avg_effectiveness:.2f}，需要优化认知方法",
                evidence=[f"{s.strategy_name}: {s.effectiveness:.2f}" for s in strategies[:5]],
                confidence=0.7,
                severity="high"
            ))

        # 识别低效策略
        poor_strategies = [s for s in strategies if s.effectiveness < 0.3 and s.usage_count > 3]
        if poor_strategies:
            insights.append(ReflectionInsight(
                scope=ReflectionScope.COGNITION,
                title="低效策略持续使用",
                description=f"{len(poor_strategies)} 个策略效果差但仍在使用",
                evidence=[s.strategy_name for s in poor_strategies[:3]],
                confidence=0.75,
                severity="medium"
            ))

        return insights

    def _reflect_on_learning(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """反思学习过程"""
        insights = []
        # 从行为记录中分析学习相关行为
        learning_behaviors = [
            b for b in self._behavior_history
            if start_time <= b.timestamp <= end_time
            and "learn" in b.action.lower()
        ]

        if learning_behaviors:
            successful_learning = [b for b in learning_behaviors if b.success is True]
            if len(successful_learning) / len(learning_behaviors) < 0.6:
                insights.append(ReflectionInsight(
                    scope=ReflectionScope.LEARNING,
                    title="学习效率偏低",
                    description="近期学习成功率不足，建议调整学习方法",
                    evidence=[b.action for b in learning_behaviors[:5]],
                    confidence=0.6,
                    severity="medium"
                ))

        return insights

    def _reflect_on_emotion(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[ReflectionInsight]:
        """反思情感状态"""
        insights = []
        # 分析情感相关行为
        emotion_behaviors = [
            b for b in self._behavior_history
            if start_time <= b.timestamp <= end_time
            and any(kw in b.action.lower() for kw in ["emotion", "stress", "frustration"])
        ]

        if len(emotion_behaviors) > 10:
            insights.append(ReflectionInsight(
                scope=ReflectionScope.EMOTION,
                title="情感波动频繁",
                description=f"检测到 {len(emotion_behaviors)} 次情感相关事件",
                evidence=[b.action for b in emotion_behaviors[:5]],
                confidence=0.5,
                severity="medium"
            ))

        return insights

    def _identify_opportunities(
        self,
        scope: ReflectionScope,
        insights: List[ReflectionInsight]
    ) -> List[ImprovementOpportunity]:
        """
        识别改进机会

        Args:
            scope: 反思范围
            insights: 洞察列表

        Returns:
            List[ImprovementOpportunity]: 改进机会列表
        """
        opportunities = []

        for insight in insights:
            if insight.severity == "high":
                opportunity = ImprovementOpportunity(
                    target_scope=scope,
                    description=f"基于洞察 '{insight.title}' 的改进",
                    expected_benefit=0.7,
                    implementation_difficulty=0.5,
                    priority=0.8,
                    suggested_actions=self._generate_suggested_actions(insight),
                    related_insights=[insight.insight_id]
                )
                opportunities.append(opportunity)
            elif insight.severity == "medium":
                opportunity = ImprovementOpportunity(
                    target_scope=scope,
                    description=f"优化 '{insight.title}'",
                    expected_benefit=0.5,
                    implementation_difficulty=0.4,
                    priority=0.5,
                    suggested_actions=self._generate_suggested_actions(insight),
                    related_insights=[insight.insight_id]
                )
                opportunities.append(opportunity)

        return opportunities

    def _generate_suggested_actions(self, insight: ReflectionInsight) -> List[str]:
        """生成建议行动"""
        actions = []

        if "成功率" in insight.title or "质量" in insight.title:
            actions.extend([
                "收集更多决策前的信息",
                "引入外部评估机制",
                "建立决策检查清单"
            ])
        elif "模式单一" in insight.title:
            actions.extend([
                "尝试新的方法变体",
                "引入随机性探索",
                "学习其他成功案例"
            ])
        elif "过度自信" in insight.title:
            actions.extend([
                "实施红队/蓝队评估",
                "引入 devil's advocate 机制",
                "建立决策后评审"
            ])
        elif "策略" in insight.title:
            actions.extend([
                "替换低效策略",
                "调整策略参数",
                "组合多种策略"
            ])
        else:
            actions.extend([
                "深入分析根因",
                "制定改进计划",
                "定期跟踪进展"
            ])

        return actions

    def _generate_summary(
        self,
        insights: List[ReflectionInsight],
        opportunities: List[ImprovementOpportunity]
    ) -> str:
        """生成反思总结"""
        high_severity = sum(1 for i in insights if i.severity == "high")
        medium_severity = sum(1 for i in insights if i.severity == "medium")
        low_severity = sum(1 for i in insights if i.severity == "low")

        summary_parts = [
            f"本次反思共发现 {len(insights)} 个洞察，{len(opportunities)} 个改进机会。",
            f"严重程度分布：高 {high_severity} 个，中 {medium_severity} 个，低 {low_severity} 个。"
        ]

        if opportunities:
            top_opportunity = max(opportunities, key=lambda o: o.priority)
            summary_parts.append(
                f"最优先改进：{top_opportunity.description}"
            )

        return " ".join(summary_parts)

    def _calculate_overall_score(self, insights: List[ReflectionInsight]) -> float:
        """计算整体评分"""
        if not insights:
            return 0.5

        # 基于洞察的严重程度计算
        severity_weights = {"high": 0.3, "medium": 0.6, "low": 0.9}
        scores = [
            severity_weights.get(i.severity, 0.5) * i.confidence
            for i in insights
        ]
        return sum(scores) / len(scores)

    def _get_period_start(self, period: ReflectionPeriod) -> datetime:
        """获取周期开始时间"""
        now = datetime.now()
        if period == ReflectionPeriod.SHORT:
            return now - timedelta(hours=1)
        elif period == ReflectionPeriod.MEDIUM:
            return now - timedelta(days=1)
        else:
            return now - timedelta(weeks=1)

    def _get_default_scopes(self, period: ReflectionPeriod) -> List[ReflectionScope]:
        """获取默认反思范围"""
        if period == ReflectionPeriod.SHORT:
            return [ReflectionScope.BEHAVIOR, ReflectionScope.DECISION]
        elif period == ReflectionPeriod.MEDIUM:
            return [
                ReflectionScope.BEHAVIOR,
                ReflectionScope.DECISION,
                ReflectionScope.COGNITION,
                ReflectionScope.LEARNING
            ]
        else:
            return list(ReflectionScope)

    # ========== 回调注册 ==========

    def register_reflection_callback(
        self,
        callback: Callable[[ReflectionReport], None]
    ) -> None:
        """
        注册反思回调

        Args:
            callback: 回调函数
        """
        self._reflection_callbacks.append(callback)
        logger.debug("Registered reflection callback")

    # ========== 查询接口 ==========

    def get_latest_report(self) -> Optional[ReflectionReport]:
        """
        获取最新反思报告

        Returns:
            Optional[ReflectionReport]: 最新报告
        """
        return self._reflection_reports[-1] if self._reflection_reports else None

    def get_reports(
        self,
        period: Optional[ReflectionPeriod] = None,
        scope: Optional[ReflectionScope] = None,
        limit: int = 10
    ) -> List[ReflectionReport]:
        """
        获取反思报告列表

        Args:
            period: 过滤周期
            scope: 过滤范围
            limit: 数量限制

        Returns:
            List[ReflectionReport]: 报告列表
        """
        reports = self._reflection_reports

        if period:
            reports = [r for r in reports if r.period == period]

        if scope:
            reports = [r for r in reports if scope in r.scopes]

        return reports[-limit:]

    def get_behavior_stats(self) -> Dict[str, Any]:
        """
        获取行为统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        behaviors = list(self._behavior_history)
        total = len(behaviors)
        if total == 0:
            return {"total": 0}

        successful = len([b for b in behaviors if b.success is True])
        failed = len([b for b in behaviors if b.success is False])

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / max(successful + failed, 1),
            "avg_duration": sum(b.duration for b in behaviors) / total,
            "avg_importance": sum(b.importance for b in behaviors) / total
        }

    def get_decision_stats(self) -> Dict[str, Any]:
        """
        获取决策统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        decisions = list(self._decision_history)
        total = len(decisions)
        if total == 0:
            return {"total": 0}

        scored = [d for d in decisions if d.quality_score is not None]
        avg_quality = sum(d.quality_score for d in scored) / len(scored) if scored else 0.0
        avg_confidence = sum(d.confidence for d in decisions) / total

        return {
            "total": total,
            "scored": len(scored),
            "avg_quality": avg_quality,
            "avg_confidence": avg_confidence,
            "calibration": avg_quality - avg_confidence
        }

    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        获取策略统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        strategies = list(self._strategy_history)
        total = len(strategies)
        if total == 0:
            return {"total": 0}

        return {
            "total": total,
            "avg_effectiveness": sum(s.effectiveness for s in strategies) / total,
            "total_usage": sum(s.usage_count for s in strategies),
            "total_successes": sum(s.success_count for s in strategies),
            "strategy_types": list(set(s.strategy_type for s in strategies))
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取完整统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "behavior": self.get_behavior_stats(),
            "decision": self.get_decision_stats(),
            "strategy": self.get_strategy_stats(),
            "total_reports": len(self._reflection_reports),
            "last_reflection": {
                period.value: time.isoformat()
                for period, time in self._last_reflection_time.items()
            }
        }

    def reset(self) -> None:
        """重置所有状态"""
        self._behavior_history.clear()
        self._decision_history.clear()
        self._strategy_history.clear()
        self._reflection_reports.clear()
        self._last_reflection_time = {
            ReflectionPeriod.SHORT: datetime.now() - timedelta(hours=2),
            ReflectionPeriod.MEDIUM: datetime.now() - timedelta(days=2),
            ReflectionPeriod.LONG: datetime.now() - timedelta(weeks=2),
        }
        logger.info("SelfReflection reset")
