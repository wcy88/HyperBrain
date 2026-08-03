"""
自我优化模块 (Self Optimization Module)

根据反思和评估结果自动优化，调整认知参数，优化策略，
配置资源，调整学习率和记忆参数。

功能：
1. 认知参数调整
2. 策略优化
3. 资源配置优化
4. 学习率调整
5. 记忆参数优化
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
from collections import defaultdict, deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("evolution.self_optimization")


class OptimizationTarget(str, Enum):
    """优化目标"""
    COGNITIVE_PARAM = "cognitive_param"     # 认知参数
    STRATEGY = "strategy"                   # 策略
    RESOURCE = "resource"                   # 资源
    LEARNING_RATE = "learning_rate"         # 学习率
    MEMORY_PARAM = "memory_param"           # 记忆参数
    OVERALL = "overall"                     # 整体


class ParameterChange(BaseModel):
    """参数变更"""
    param_name: str = Field(..., description="参数名称")
    old_value: float = Field(..., description="旧值")
    new_value: float = Field(..., description="新值")
    change_ratio: float = Field(..., description="变化比例")
    reason: str = Field(default="", description="变更原因")
    timestamp: datetime = Field(default_factory=datetime.now)


class OptimizationAction(BaseModel):
    """优化动作"""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target: OptimizationTarget = Field(...)
    description: str = Field(..., description="动作描述")
    parameter_changes: List[ParameterChange] = Field(default_factory=list)
    expected_improvement: float = Field(default=0.1, ge=0.0, le=1.0)
    risk_level: float = Field(default=0.3, ge=0.0, le=1.0)
    applied: bool = Field(default=False)
    applied_at: Optional[datetime] = Field(default=None)
    result_feedback: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("expected_improvement", "risk_level", "result_feedback")
    @classmethod
    def validate_range(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return max(0.0, min(1.0, v))


class OptimizationResult(BaseModel):
    """优化结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actions: List[OptimizationAction] = Field(default_factory=list)
    overall_improvement: float = Field(default=0.0, ge=-1.0, le=1.0)
    parameters_optimized: int = Field(default=0, ge=0)
    strategies_optimized: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: str = Field(default="")


class CognitiveParameters(BaseModel):
    """认知参数"""
    reasoning_depth: float = Field(default=3.0, ge=1.0, le=10.0)
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    exploration_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    attention_focus: float = Field(default=0.7, ge=0.0, le=1.0)
    processing_speed: float = Field(default=1.0, ge=0.1, le=5.0)
    creativity_boost: float = Field(default=0.3, ge=0.0, le=1.0)

    @field_validator("reasoning_depth", "confidence_threshold", "exploration_rate",
                     "attention_focus", "processing_speed", "creativity_boost")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(10.0 if "depth" in cls.model_fields else 1.0, v))


class MemoryParameters(BaseModel):
    """记忆参数"""
    consolidation_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    retrieval_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    reinforcement_boost: float = Field(default=0.1, ge=0.0, le=1.0)
    association_strength: float = Field(default=0.5, ge=0.0, le=1.0)
    working_memory_capacity: float = Field(default=7.0, ge=3.0, le=15.0)

    @field_validator("consolidation_rate", "retrieval_threshold", "decay_rate",
                     "reinforcement_boost", "association_strength", "working_memory_capacity")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(15.0 if "capacity" in cls.model_fields else 1.0, v))


class LearningParameters(BaseModel):
    """学习参数"""
    learning_rate: float = Field(default=0.001, ge=0.0001, le=1.0)
    batch_size_factor: float = Field(default=1.0, ge=0.1, le=5.0)
    exploration_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    feedback_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    adaptation_speed: float = Field(default=0.5, ge=0.0, le=1.0)
    transfer_strength: float = Field(default=0.4, ge=0.0, le=1.0)

    @field_validator("learning_rate", "batch_size_factor", "exploration_ratio",
                     "feedback_weight", "adaptation_speed", "transfer_strength")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0001, min(5.0 if "batch" in cls.model_fields else 1.0, v))


class ResourceAllocation(BaseModel):
    """资源配置"""
    cognitive_budget: float = Field(default=0.3, ge=0.0, le=1.0)
    memory_budget: float = Field(default=0.25, ge=0.0, le=1.0)
    learning_budget: float = Field(default=0.25, ge=0.0, le=1.0)
    execution_budget: float = Field(default=0.2, ge=0.0, le=1.0)

    @field_validator("cognitive_budget", "memory_budget", "learning_budget", "execution_budget")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class SelfOptimizationConfig(BaseModel):
    """自我优化配置"""
    enable_auto_optimize: bool = Field(default=True)
    optimization_interval: float = Field(default=3600.0, description="优化间隔(秒)")
    max_change_ratio: float = Field(default=0.2, description="最大变化比例")
    min_improvement_threshold: float = Field(default=0.05)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_parameter_tuning: bool = Field(default=True)
    enable_strategy_optimization: bool = Field(default=True)
    enable_resource_reallocation: bool = Field(default=True)


class SelfOptimizer:
    """
    自我优化系统

    根据反思和评估结果自动优化系统参数和策略。

    Attributes:
        config: 优化配置
        cognitive_params: 当前认知参数
        memory_params: 当前记忆参数
        learning_params: 当前学习参数
        resource_allocation: 当前资源配置
        optimization_history: 优化历史
    """

    def __init__(self, config: Optional[SelfOptimizationConfig] = None):
        self.config = config or SelfOptimizationConfig()
        self._cognitive_params = CognitiveParameters()
        self._memory_params = MemoryParameters()
        self._learning_params = LearningParameters()
        self._resource_allocation = ResourceAllocation()
        self._optimization_history: deque = deque(maxlen=100)
        self._last_optimization_time: Optional[datetime] = None
        self._optimization_callbacks: List[Callable[[OptimizationResult], None]] = []

        # 从全局配置加载初始值
        self._load_from_config()
        logger.info("SelfOptimizer initialized")

    def _load_from_config(self) -> None:
        """从全局配置加载参数"""
        try:
            config = get_config()
            if hasattr(config, 'cognitive'):
                cog = config.cognitive
                self._cognitive_params.reasoning_depth = getattr(cog, 'reasoning_depth', 3.0)
                self._cognitive_params.confidence_threshold = getattr(cog, 'confidence_threshold', 0.6)
            if hasattr(config, 'learning'):
                learn = config.learning
                self._learning_params.learning_rate = getattr(learn, 'learning_rate', 0.001)
            if hasattr(config, 'memory'):
                mem = config.memory
                self._memory_params.decay_rate = getattr(mem, 'memory_decay_rate', 0.05)
        except Exception:
            pass  # 使用默认值

    # ========== 核心优化接口 ==========

    def optimize(
        self,
        reflection_data: Optional[Dict[str, Any]] = None,
        assessment_data: Optional[Dict[str, Any]] = None,
        error_data: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        执行优化

        Args:
            reflection_data: 反思数据
            assessment_data: 评估数据
            error_data: 错误数据

        Returns:
            OptimizationResult: 优化结果
        """
        logger.info("Starting self-optimization")

        actions: List[OptimizationAction] = []

        # 基于反思优化
        if reflection_data and self.config.enable_parameter_tuning:
            reflection_actions = self._optimize_from_reflection(reflection_data)
            actions.extend(reflection_actions)

        # 基于评估优化
        if assessment_data and self.config.enable_parameter_tuning:
            assessment_actions = self._optimize_from_assessment(assessment_data)
            actions.extend(assessment_actions)

        # 基于错误优化
        if error_data and self.config.enable_strategy_optimization:
            error_actions = self._optimize_from_errors(error_data)
            actions.extend(error_actions)

        # 资源再分配
        if self.config.enable_resource_reallocation:
            resource_actions = self._optimize_resources(assessment_data)
            actions.extend(resource_actions)

        # 应用优化
        applied_count = 0
        for action in actions:
            if self._apply_action(action):
                applied_count += 1

        # 计算整体改进
        overall_improvement = self._calculate_overall_improvement(actions)

        result = OptimizationResult(
            actions=actions,
            overall_improvement=overall_improvement,
            parameters_optimized=sum(1 for a in actions if a.target == OptimizationTarget.COGNITIVE_PARAM),
            strategies_optimized=sum(1 for a in actions if a.target == OptimizationTarget.STRATEGY),
            summary=f"Applied {applied_count}/{len(actions)} optimization actions"
        )

        self._optimization_history.append(result)
        self._last_optimization_time = datetime.now()

        # 触发回调
        for callback in self._optimization_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"Optimization callback failed: {e}")

        logger.info(f"Optimization completed: {applied_count} actions applied")
        return result

    def auto_optimize(
        self,
        reflection_data: Optional[Dict[str, Any]] = None,
        assessment_data: Optional[Dict[str, Any]] = None,
        error_data: Optional[Dict[str, Any]] = None
    ) -> Optional[OptimizationResult]:
        """
        自动优化（检查时间间隔）

        Returns:
            Optional[OptimizationResult]: 优化结果
        """
        if not self.config.enable_auto_optimize:
            return None

        now = datetime.now()
        if (self._last_optimization_time is None or
            (now - self._last_optimization_time).total_seconds() >= self.config.optimization_interval):
            return self.optimize(reflection_data, assessment_data, error_data)

        return None

    # ========== 基于反思的优化 ==========

    def _optimize_from_reflection(
        self,
        reflection_data: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """基于反思数据生成优化动作"""
        actions = []

        insights = reflection_data.get("insights", [])
        opportunities = reflection_data.get("opportunities", [])

        for opportunity in opportunities:
            scope = opportunity.get("target_scope", "")
            severity = opportunity.get("severity", "medium")

            if severity == "high":
                action = self._create_action_for_opportunity(opportunity)
                if action:
                    actions.append(action)

        # 基于洞察调整参数
        for insight in insights:
            title = insight.get("title", "")
            if "成功率偏低" in title:
                # 提高谨慎度
                actions.append(self._adjust_cognitive_param(
                    "confidence_threshold",
                    0.1,
                    "行为成功率低，提高置信度阈值"
                ))
            elif "过度自信" in title:
                actions.append(self._adjust_cognitive_param(
                    "exploration_rate",
                    0.15,
                    "减少过度自信，增加探索"
                ))
            elif "策略效果不佳" in title:
                actions.append(self._adjust_learning_param(
                    "adaptation_speed",
                    0.2,
                    "策略效果差，加快适应"
                ))

        return actions

    def _create_action_for_opportunity(
        self,
        opportunity: Dict[str, Any]
    ) -> Optional[OptimizationAction]:
        """为改进机会创建优化动作"""
        scope = opportunity.get("target_scope", "")

        if scope == "behavior":
            return OptimizationAction(
                target=OptimizationTarget.COGNITIVE_PARAM,
                description=f"优化行为: {opportunity.get('description', '')}",
                parameter_changes=[
                    ParameterChange(
                        param_name="attention_focus",
                        old_value=self._cognitive_params.attention_focus,
                        new_value=min(1.0, self._cognitive_params.attention_focus + 0.1),
                        change_ratio=0.1,
                        reason="提高注意力以改善行为执行"
                    )
                ],
                expected_improvement=opportunity.get("expected_benefit", 0.3),
                risk_level=0.2
            )
        elif scope == "decision":
            return OptimizationAction(
                target=OptimizationTarget.COGNITIVE_PARAM,
                description=f"优化决策: {opportunity.get('description', '')}",
                parameter_changes=[
                    ParameterChange(
                        param_name="reasoning_depth",
                        old_value=self._cognitive_params.reasoning_depth,
                        new_value=min(10.0, self._cognitive_params.reasoning_depth + 1.0),
                        change_ratio=0.15,
                        reason="增加推理深度以改善决策"
                    )
                ],
                expected_improvement=opportunity.get("expected_benefit", 0.3),
                risk_level=0.3
            )

        return None

    # ========== 基于评估的优化 ==========

    def _optimize_from_assessment(
        self,
        assessment_data: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """基于评估数据生成优化动作"""
        actions = []

        gaps = assessment_data.get("gaps", [])
        trends = assessment_data.get("trends", [])

        # 基于能力差距优化
        for gap in gaps:
            dimension = gap.get("dimension", "")
            gap_size = gap.get("gap_size", 0.0)

            if gap_size > 0.3:
                action = self._create_action_for_gap(dimension, gap_size)
                if action:
                    actions.append(action)

        # 基于趋势优化
        for trend in trends:
            if trend.get("trend_direction") == "declining":
                dimension = trend.get("dimension", "")
                strength = abs(trend.get("trend_strength", 0.0))
                action = self._create_action_for_decline(dimension, strength)
                if action:
                    actions.append(action)

        return actions

    def _create_action_for_gap(
        self,
        dimension: str,
        gap_size: float
    ) -> Optional[OptimizationAction]:
        """为能力差距创建优化动作"""
        param_mapping = {
            "reasoning": ("reasoning_depth", OptimizationTarget.COGNITIVE_PARAM),
            "learning": ("learning_rate", OptimizationTarget.LEARNING_RATE),
            "memory": ("consolidation_rate", OptimizationTarget.MEMORY_PARAM),
            "decision": ("confidence_threshold", OptimizationTarget.COGNITIVE_PARAM),
            "planning": ("processing_speed", OptimizationTarget.COGNITIVE_PARAM),
            "attention": ("attention_focus", OptimizationTarget.COGNITIVE_PARAM),
        }

        if dimension not in param_mapping:
            return None

        param_name, target = param_mapping[dimension]
        change = min(gap_size * 0.5, self.config.max_change_ratio)

        # 获取当前值
        current_value = self._get_param_value(param_name)
        new_value = current_value * (1 + change)

        return OptimizationAction(
            target=target,
            description=f"提升 {dimension} 能力，缩小差距 {gap_size:.1%}",
            parameter_changes=[
                ParameterChange(
                    param_name=param_name,
                    old_value=current_value,
                    new_value=new_value,
                    change_ratio=change,
                    reason=f"{dimension} 能力差距较大"
                )
            ],
            expected_improvement=gap_size * 0.3,
            risk_level=0.3
        )

    def _create_action_for_decline(
        self,
        dimension: str,
        strength: float
    ) -> Optional[OptimizationAction]:
        """为下降趋势创建优化动作"""
        return OptimizationAction(
            target=OptimizationTarget.OVERALL,
            description=f"阻止 {dimension} 能力下降（强度: {strength:.3f}）",
            parameter_changes=[
                ParameterChange(
                    param_name="adaptation_speed",
                    old_value=self._learning_params.adaptation_speed,
                    new_value=min(1.0, self._learning_params.adaptation_speed + strength * 0.2),
                    change_ratio=strength * 0.2,
                    reason=f"应对 {dimension} 下降趋势"
                )
            ],
            expected_improvement=strength * 0.4,
            risk_level=0.4
        )

    # ========== 基于错误的优化 ==========

    def _optimize_from_errors(
        self,
        error_data: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """基于错误数据生成优化动作"""
        actions = []

        patterns = error_data.get("patterns", [])
        strategies = error_data.get("strategies", [])

        # 基于高频错误模式优化
        for pattern in patterns:
            if pattern.get("frequency", 0) > 5:
                action = OptimizationAction(
                    target=OptimizationTarget.STRATEGY,
                    description=f"针对错误模式优化: {pattern.get('name', '')}",
                    parameter_changes=[
                        ParameterChange(
                            param_name="exploration_rate",
                            old_value=self._cognitive_params.exploration_rate,
                            new_value=min(1.0, self._cognitive_params.exploration_rate + 0.1),
                            change_ratio=0.1,
                            reason="增加探索以减少重复错误"
                        )
                    ],
                    expected_improvement=0.2,
                    risk_level=0.3
                )
                actions.append(action)

        return actions

    # ========== 资源优化 ==========

    def _optimize_resources(
        self,
        assessment_data: Optional[Dict[str, Any]]
    ) -> List[OptimizationAction]:
        """优化资源分配"""
        actions = []

        if not assessment_data:
            return actions

        scores = assessment_data.get("dimension_scores", {})
        if not scores:
            return actions

        # 根据能力评分调整资源分配
        total_score = sum(scores.values())
        if total_score == 0:
            return actions

        # 识别需要加强的维度
        weak_dimensions = [
            dim for dim, score in scores.items()
            if score < 0.5
        ]

        if weak_dimensions:
            # 增加对弱项的资源投入
            budget_increase = 0.05 * len(weak_dimensions)

            new_cognitive = min(1.0, self._resource_allocation.cognitive_budget + budget_increase)
            new_learning = min(1.0, self._resource_allocation.learning_budget + budget_increase * 0.5)

            actions.append(OptimizationAction(
                target=OptimizationTarget.RESOURCE,
                description=f"增加弱项资源投入: {', '.join(weak_dimensions)}",
                parameter_changes=[
                    ParameterChange(
                        param_name="cognitive_budget",
                        old_value=self._resource_allocation.cognitive_budget,
                        new_value=new_cognitive,
                        change_ratio=(new_cognitive - self._resource_allocation.cognitive_budget) / max(self._resource_allocation.cognitive_budget, 0.001),
                        reason="加强认知资源以改善弱项"
                    ),
                    ParameterChange(
                        param_name="learning_budget",
                        old_value=self._resource_allocation.learning_budget,
                        new_value=new_learning,
                        change_ratio=(new_learning - self._resource_allocation.learning_budget) / max(self._resource_allocation.learning_budget, 0.001),
                        reason="增加学习资源投入"
                    )
                ],
                expected_improvement=0.15,
                risk_level=0.2
            ))

        return actions

    # ========== 参数调整辅助 ==========

    def _adjust_cognitive_param(
        self,
        param_name: str,
        delta: float,
        reason: str
    ) -> OptimizationAction:
        """调整认知参数"""
        current = self._get_param_value(param_name)
        new_value = current * (1 + delta)
        new_value = self._clamp_param(param_name, new_value)

        return OptimizationAction(
            target=OptimizationTarget.COGNITIVE_PARAM,
            description=f"调整认知参数: {param_name}",
            parameter_changes=[
                ParameterChange(
                    param_name=param_name,
                    old_value=current,
                    new_value=new_value,
                    change_ratio=delta,
                    reason=reason
                )
            ],
            expected_improvement=abs(delta) * 0.5,
            risk_level=abs(delta)
        )

    def _adjust_learning_param(
        self,
        param_name: str,
        delta: float,
        reason: str
    ) -> OptimizationAction:
        """调整学习参数"""
        current = self._get_param_value(param_name)
        new_value = current * (1 + delta)
        new_value = self._clamp_param(param_name, new_value)

        return OptimizationAction(
            target=OptimizationTarget.LEARNING_RATE,
            description=f"调整学习参数: {param_name}",
            parameter_changes=[
                ParameterChange(
                    param_name=param_name,
                    old_value=current,
                    new_value=new_value,
                    change_ratio=delta,
                    reason=reason
                )
            ],
            expected_improvement=abs(delta) * 0.5,
            risk_level=abs(delta) * 0.8
        )

    def _get_param_value(self, param_name: str) -> float:
        """获取参数当前值"""
        if hasattr(self._cognitive_params, param_name):
            return getattr(self._cognitive_params, param_name)
        elif hasattr(self._memory_params, param_name):
            return getattr(self._memory_params, param_name)
        elif hasattr(self._learning_params, param_name):
            return getattr(self._learning_params, param_name)
        elif hasattr(self._resource_allocation, param_name):
            return getattr(self._resource_allocation, param_name)
        return 0.5

    def _set_param_value(self, param_name: str, value: float) -> bool:
        """设置参数值"""
        if hasattr(self._cognitive_params, param_name):
            setattr(self._cognitive_params, param_name, value)
            return True
        elif hasattr(self._memory_params, param_name):
            setattr(self._memory_params, param_name, value)
            return True
        elif hasattr(self._learning_params, param_name):
            setattr(self._learning_params, param_name, value)
            return True
        elif hasattr(self._resource_allocation, param_name):
            setattr(self._resource_allocation, param_name, value)
            return True
        return False

    def _clamp_param(self, param_name: str, value: float) -> float:
        """限制参数范围"""
        # 根据参数名确定范围
        ranges = {
            "reasoning_depth": (1.0, 10.0),
            "confidence_threshold": (0.0, 1.0),
            "exploration_rate": (0.0, 1.0),
            "attention_focus": (0.0, 1.0),
            "processing_speed": (0.1, 5.0),
            "creativity_boost": (0.0, 1.0),
            "consolidation_rate": (0.0, 1.0),
            "retrieval_threshold": (0.0, 1.0),
            "decay_rate": (0.0, 1.0),
            "reinforcement_boost": (0.0, 1.0),
            "association_strength": (0.0, 1.0),
            "working_memory_capacity": (3.0, 15.0),
            "learning_rate": (0.0001, 1.0),
            "batch_size_factor": (0.1, 5.0),
            "exploration_ratio": (0.0, 1.0),
            "feedback_weight": (0.0, 1.0),
            "adaptation_speed": (0.0, 1.0),
            "transfer_strength": (0.0, 1.0),
            "cognitive_budget": (0.0, 1.0),
            "memory_budget": (0.0, 1.0),
            "learning_budget": (0.0, 1.0),
            "execution_budget": (0.0, 1.0),
        }

        min_val, max_val = ranges.get(param_name, (0.0, 1.0))
        return max(min_val, min(max_val, value))

    def _apply_action(self, action: OptimizationAction) -> bool:
        """应用优化动作"""
        # 检查风险
        if action.risk_level > self.config.risk_tolerance:
            logger.warning(f"Action {action.action_id} risk too high, skipping")
            return False

        # 应用参数变更
        for change in action.parameter_changes:
            clamped_value = self._clamp_param(change.param_name, change.new_value)
            if self._set_param_value(change.param_name, clamped_value):
                logger.debug(f"Applied: {change.param_name} = {clamped_value:.4f}")
            else:
                logger.warning(f"Unknown parameter: {change.param_name}")

        action.applied = True
        action.applied_at = datetime.now()
        return True

    def _calculate_overall_improvement(
        self,
        actions: List[OptimizationAction]
    ) -> float:
        """计算整体改进预期"""
        if not actions:
            return 0.0

        improvements = [a.expected_improvement for a in actions if a.applied]
        return sum(improvements) / len(improvements) if improvements else 0.0

    # ========== 回调注册 ==========

    def register_optimization_callback(
        self,
        callback: Callable[[OptimizationResult], None]
    ) -> None:
        """
        注册优化回调

        Args:
            callback: 回调函数
        """
        self._optimization_callbacks.append(callback)
        logger.debug("Registered optimization callback")

    # ========== 参数获取接口 ==========

    def get_cognitive_params(self) -> CognitiveParameters:
        """获取当前认知参数"""
        return self._cognitive_params

    def get_memory_params(self) -> MemoryParameters:
        """获取当前记忆参数"""
        return self._memory_params

    def get_learning_params(self) -> LearningParameters:
        """获取当前学习参数"""
        return self._learning_params

    def get_resource_allocation(self) -> ResourceAllocation:
        """获取当前资源配置"""
        return self._resource_allocation

    def get_all_params(self) -> Dict[str, Any]:
        """
        获取所有参数

        Returns:
            Dict[str, Any]: 参数字典
        """
        return {
            "cognitive": self._cognitive_params.model_dump(),
            "memory": self._memory_params.model_dump(),
            "learning": self._learning_params.model_dump(),
            "resource": self._resource_allocation.model_dump()
        }

    def set_param(self, param_name: str, value: float) -> bool:
        """
        手动设置参数

        Args:
            param_name: 参数名
            value: 参数值

        Returns:
            bool: 是否成功
        """
        clamped = self._clamp_param(param_name, value)
        return self._set_param_value(param_name, clamped)

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_optimizations": len(self._optimization_history),
            "last_optimization": self._last_optimization_time.isoformat() if self._last_optimization_time else None,
            "current_params": self.get_all_params(),
            "config": self.config.model_dump()
        }

    def reset(self) -> None:
        """重置所有状态"""
        self._cognitive_params = CognitiveParameters()
        self._memory_params = MemoryParameters()
        self._learning_params = LearningParameters()
        self._resource_allocation = ResourceAllocation()
        self._optimization_history.clear()
        self._last_optimization_time = None
        self._load_from_config()
        logger.info("SelfOptimizer reset")
