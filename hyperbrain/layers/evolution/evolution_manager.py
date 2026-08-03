"""
进化管理器 (Evolution Manager)

统一管理所有进化模块，协调进化过程，控制进化节奏，
提供统一的进化API，与记忆、认知、学习系统交互。

功能：
1. 统一管理所有进化模块
2. 协调进化过程
3. 控制进化节奏
4. 提供统一的进化API
5. 与记忆、认知、学习系统交互
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.evolution.self_reflection import (
    SelfReflection, ReflectionReport, ReflectionPeriod, ReflectionScope
)
from hyperbrain.layers.evolution.error_analysis import (
    ErrorAnalyzer, ErrorAnalysisReport, ErrorCategory, ErrorSeverity
)
from hyperbrain.layers.evolution.capability_assessment import (
    CapabilityAssessor, CapabilityReport, CapabilityDimension
)
from hyperbrain.layers.evolution.self_optimization import (
    SelfOptimizer, OptimizationResult
)
from hyperbrain.layers.evolution.goal_evolution import (
    GoalEvolver, GoalEvolutionReport, GoalStatus
)
from hyperbrain.layers.evolution.architecture_evolution import (
    ArchitectureEvolver, ArchitectureEvolutionReport
)

logger = get_logger("evolution.manager")


class EvolutionPhase(str, Enum):
    """进化阶段"""
    REFLECTION = "reflection"       # 反思阶段
    ANALYSIS = "analysis"           # 分析阶段
    ASSESSMENT = "assessment"       # 评估阶段
    OPTIMIZATION = "optimization"   # 优化阶段
    GOAL_EVOLUTION = "goal_evolution"   # 目标进化
    ARCHITECTURE_EVOLUTION = "architecture_evolution"  # 架构进化
    IDLE = "idle"                   # 空闲


class EvolutionCycle(BaseModel):
    """进化周期"""
    cycle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field(default=None)
    phases_completed: List[EvolutionPhase] = Field(default_factory=list)
    reports: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="running", description="running/completed/failed")
    error_message: Optional[str] = Field(default=None)


class EvolutionConfig(BaseModel):
    """进化管理配置"""
    enable_auto_evolution: bool = Field(default=True)
    evolution_interval: float = Field(default=3600.0, description="进化周期间隔(秒)")
    phase_order: List[EvolutionPhase] = Field(default_factory=lambda: [
        EvolutionPhase.REFLECTION,
        EvolutionPhase.ANALYSIS,
        EvolutionPhase.ASSESSMENT,
        EvolutionPhase.OPTIMIZATION,
        EvolutionPhase.GOAL_EVOLUTION,
        EvolutionPhase.ARCHITECTURE_EVOLUTION,
    ])
    enable_reflection: bool = Field(default=True)
    enable_error_analysis: bool = Field(default=True)
    enable_capability_assessment: bool = Field(default=True)
    enable_self_optimization: bool = Field(default=True)
    enable_goal_evolution: bool = Field(default=True)
    enable_architecture_evolution: bool = Field(default=True)
    max_concurrent_phases: int = Field(default=1)
    pause_between_phases: float = Field(default=1.0, description="阶段间暂停(秒)")


class EvolutionManager:
    """
    进化管理器

    统一管理所有进化模块，协调完整的进化周期。

    Attributes:
        config: 进化配置
        self_reflection: 自我反思模块
        error_analyzer: 错误分析模块
        capability_assessor: 能力评估模块
        self_optimizer: 自我优化模块
        goal_evolver: 目标进化模块
        architecture_evolver: 架构进化模块
    """

    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()

        # 初始化各进化模块
        self._self_reflection = SelfReflection()
        self._error_analyzer = ErrorAnalyzer()
        self._capability_assessor = CapabilityAssessor()
        self._self_optimizer = SelfOptimizer()
        self._goal_evolver = GoalEvolver()
        self._architecture_evolver = ArchitectureEvolver()

        # 状态管理
        self._current_phase: EvolutionPhase = EvolutionPhase.IDLE
        self._evolution_cycles: List[EvolutionCycle] = []
        self._current_cycle: Optional[EvolutionCycle] = None
        self._last_evolution_time: Optional[datetime] = None
        self._is_running: bool = False
        self._paused: bool = False

        # 回调注册
        self._cycle_callbacks: List[Callable[[EvolutionCycle], None]] = []
        self._phase_callbacks: Dict[EvolutionPhase, List[Callable[[Any], None]]] = defaultdict(list)

        # 外部系统引用（可选）
        self._memory_manager: Optional[Any] = None
        self._cognitive_manager: Optional[Any] = None
        self._learning_manager: Optional[Any] = None

        logger.info("EvolutionManager initialized with all modules")

    # ========== 外部系统连接 ==========

    def connect_memory_system(self, memory_manager: Any) -> None:
        """
        连接记忆系统

        Args:
            memory_manager: 记忆管理器实例
        """
        self._memory_manager = memory_manager
        logger.info("Connected memory system")

    def connect_cognitive_system(self, cognitive_manager: Any) -> None:
        """
        连接认知系统

        Args:
            cognitive_manager: 认知管理器实例
        """
        self._cognitive_manager = cognitive_manager
        logger.info("Connected cognitive system")

    def connect_learning_system(self, learning_manager: Any) -> None:
        """
        连接学习系统

        Args:
            learning_manager: 学习管理器实例
        """
        self._learning_manager = learning_manager
        logger.info("Connected learning system")

    # ========== 核心进化周期 ==========

    def run_evolution_cycle(self) -> EvolutionCycle:
        """
        执行完整的进化周期

        按配置顺序执行各个进化阶段。

        Returns:
            EvolutionCycle: 进化周期记录
        """
        cycle = EvolutionCycle()
        self._current_cycle = cycle
        self._evolution_cycles.append(cycle)

        logger.info(f"Starting evolution cycle: {cycle.cycle_id}")

        try:
            for phase in self.config.phase_order:
                if self._paused:
                    logger.info("Evolution paused")
                    break

                self._current_phase = phase
                logger.info(f"Executing phase: {phase.value}")

                result = self._execute_phase(phase)
                if result is not None:
                    cycle.phases_completed.append(phase)
                    cycle.reports[phase.value] = result

                # 阶段间暂停
                if self.config.pause_between_phases > 0:
                    import time
                    time.sleep(self.config.pause_between_phases)

            cycle.end_time = datetime.now()
            cycle.status = "completed"
            self._last_evolution_time = datetime.now()

            # 触发周期完成回调
            for callback in self._cycle_callbacks:
                try:
                    callback(cycle)
                except Exception as e:
                    logger.warning(f"Cycle callback failed: {e}")

            logger.info(f"Evolution cycle completed: {cycle.cycle_id}")

        except Exception as e:
            cycle.end_time = datetime.now()
            cycle.status = "failed"
            cycle.error_message = str(e)
            logger.error(f"Evolution cycle failed: {e}")

        finally:
            self._current_phase = EvolutionPhase.IDLE
            self._current_cycle = None

        return cycle

    async def run_evolution_cycle_async(self) -> EvolutionCycle:
        """
        异步执行进化周期

        Returns:
            EvolutionCycle: 进化周期记录
        """
        cycle = EvolutionCycle()
        self._current_cycle = cycle
        self._evolution_cycles.append(cycle)

        logger.info(f"Starting async evolution cycle: {cycle.cycle_id}")

        try:
            for phase in self.config.phase_order:
                if self._paused:
                    break

                self._current_phase = phase
                logger.info(f"Executing async phase: {phase.value}")

                result = await self._execute_phase_async(phase)
                if result is not None:
                    cycle.phases_completed.append(phase)
                    cycle.reports[phase.value] = result

                if self.config.pause_between_phases > 0:
                    await asyncio.sleep(self.config.pause_between_phases)

            cycle.end_time = datetime.now()
            cycle.status = "completed"
            self._last_evolution_time = datetime.now()

            for callback in self._cycle_callbacks:
                try:
                    callback(cycle)
                except Exception as e:
                    logger.warning(f"Cycle callback failed: {e}")

        except Exception as e:
            cycle.end_time = datetime.now()
            cycle.status = "failed"
            cycle.error_message = str(e)
            logger.error(f"Async evolution cycle failed: {e}")

        finally:
            self._current_phase = EvolutionPhase.IDLE
            self._current_cycle = None

        return cycle

    def _execute_phase(self, phase: EvolutionPhase) -> Optional[Any]:
        """执行单个进化阶段"""
        if phase == EvolutionPhase.REFLECTION and self.config.enable_reflection:
            return self._run_reflection_phase()
        elif phase == EvolutionPhase.ANALYSIS and self.config.enable_error_analysis:
            return self._run_analysis_phase()
        elif phase == EvolutionPhase.ASSESSMENT and self.config.enable_capability_assessment:
            return self._run_assessment_phase()
        elif phase == EvolutionPhase.OPTIMIZATION and self.config.enable_self_optimization:
            return self._run_optimization_phase()
        elif phase == EvolutionPhase.GOAL_EVOLUTION and self.config.enable_goal_evolution:
            return self._run_goal_evolution_phase()
        elif phase == EvolutionPhase.ARCHITECTURE_EVOLUTION and self.config.enable_architecture_evolution:
            return self._run_architecture_evolution_phase()
        return None

    async def _execute_phase_async(self, phase: EvolutionPhase) -> Optional[Any]:
        """异步执行单个进化阶段"""
        return self._execute_phase(phase)

    # ========== 各阶段实现 ==========

    def _run_reflection_phase(self) -> Optional[ReflectionReport]:
        """执行反思阶段"""
        try:
            # 从认知系统获取数据
            if self._cognitive_manager:
                # 记录认知行为
                pass

            report = self._self_reflection.reflect(
                period=ReflectionPeriod.MEDIUM,
                scopes=[
                    ReflectionScope.BEHAVIOR,
                    ReflectionScope.DECISION,
                    ReflectionScope.COGNITION
                ]
            )

            # 存储到记忆系统
            if self._memory_manager:
                try:
                    self._memory_manager.store_memory(
                        content={
                            "type": "reflection_report",
                            "report_id": report.report_id,
                            "summary": report.summary,
                            "overall_score": report.overall_score
                        },
                        memory_type="episodic",
                        importance=0.7
                    )
                except Exception as e:
                    logger.warning(f"Failed to store reflection in memory: {e}")

            # 触发阶段回调
            for callback in self._phase_callbacks[EvolutionPhase.REFLECTION]:
                try:
                    callback(report)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return report

        except Exception as e:
            logger.error(f"Reflection phase failed: {e}")
            return None

    def _run_analysis_phase(self) -> Optional[ErrorAnalysisReport]:
        """执行错误分析阶段"""
        try:
            # 识别错误模式
            patterns = self._error_analyzer.recognize_patterns()

            # 生成预防策略
            strategies = self._error_analyzer.generate_prevention_strategies()

            # 生成报告
            report = self._error_analyzer.generate_report()

            # 存储到记忆系统
            if self._memory_manager:
                try:
                    self._memory_manager.store_memory(
                        content={
                            "type": "error_analysis",
                            "report_id": report.report_id,
                            "total_errors": report.total_errors,
                            "top_patterns": [p.name for p in report.top_patterns]
                        },
                        memory_type="semantic",
                        importance=0.6
                    )
                except Exception as e:
                    logger.warning(f"Failed to store error analysis in memory: {e}")

            for callback in self._phase_callbacks[EvolutionPhase.ANALYSIS]:
                try:
                    callback(report)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return report

        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            return None

    def _run_assessment_phase(self) -> Optional[CapabilityReport]:
        """执行能力评估阶段"""
        try:
            # 从学习系统获取性能数据
            if self._learning_manager:
                try:
                    learning_stats = self._learning_manager.get_stats()
                    # 记录学习相关评分
                    self._capability_assessor.record_score(
                        dimension=CapabilityDimension.LEARNING,
                        score=learning_stats.get("average_performance", 0.5)
                    )
                except Exception as e:
                    logger.warning(f"Failed to get learning stats: {e}")

            # 从认知系统获取数据
            if self._cognitive_manager:
                try:
                    cognitive_stats = self._cognitive_manager.get_stats()
                    self._capability_assessor.record_score(
                        dimension=CapabilityDimension.REASONING,
                        score=cognitive_stats.get("average_success_rate", 0.5)
                    )
                except Exception as e:
                    logger.warning(f"Failed to get cognitive stats: {e}")

            report = self._capability_assessor.assess()

            # 存储到记忆系统
            if self._memory_manager:
                try:
                    self._memory_manager.store_memory(
                        content={
                            "type": "capability_assessment",
                            "report_id": report.report_id,
                            "overall_score": report.overall_score,
                            "strengths": report.strengths,
                            "weaknesses": report.weaknesses
                        },
                        memory_type="semantic",
                        importance=0.8
                    )
                except Exception as e:
                    logger.warning(f"Failed to store assessment in memory: {e}")

            for callback in self._phase_callbacks[EvolutionPhase.ASSESSMENT]:
                try:
                    callback(report)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return report

        except Exception as e:
            logger.error(f"Assessment phase failed: {e}")
            return None

    def _run_optimization_phase(self) -> Optional[OptimizationResult]:
        """执行优化阶段"""
        try:
            # 收集各阶段数据
            reflection_data = None
            assessment_data = None
            error_data = None

            if self._current_cycle:
                reflection_report = self._current_cycle.reports.get("reflection")
                if reflection_report:
                    reflection_data = {
                        "insights": [
                            insight.model_dump() for insight in reflection_report.insights
                        ],
                        "opportunities": [
                            opp.model_dump() for opp in reflection_report.opportunities
                        ]
                    }

                assessment_report = self._current_cycle.reports.get("assessment")
                if assessment_report:
                    assessment_data = {
                        "gaps": [gap.model_dump() for gap in assessment_report.gaps],
                        "trends": [trend.model_dump() for trend in assessment_report.trends],
                        "dimension_scores": assessment_report.dimension_scores
                    }

                error_report = self._current_cycle.reports.get("analysis")
                if error_report:
                    error_data = {
                        "patterns": [p.model_dump() for p in error_report.top_patterns],
                        "strategies": [s.model_dump() for s in error_report.recommended_strategies]
                    }

            result = self._self_optimizer.optimize(
                reflection_data=reflection_data,
                assessment_data=assessment_data,
                error_data=error_data
            )

            # 应用优化到各系统
            self._apply_optimization_to_systems()

            for callback in self._phase_callbacks[EvolutionPhase.OPTIMIZATION]:
                try:
                    callback(result)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return result

        except Exception as e:
            logger.error(f"Optimization phase failed: {e}")
            return None

    def _run_goal_evolution_phase(self) -> Optional[GoalEvolutionReport]:
        """执行目标进化阶段"""
        try:
            # 构建发现上下文
            context = {}

            if self._current_cycle:
                assessment_report = self._current_cycle.reports.get("assessment")
                if assessment_report:
                    context["capability_gaps"] = [
                        {
                            "dimension": gap.dimension.value,
                            "gap_size": gap.gap_size
                        }
                        for gap in assessment_report.gaps
                    ]

                error_report = self._current_cycle.reports.get("analysis")
                if error_report:
                    context["error_patterns"] = [
                        {
                            "name": p.name,
                            "category": p.category.value,
                            "frequency": p.frequency
                        }
                        for p in error_report.top_patterns
                    ]

                reflection_report = self._current_cycle.reports.get("reflection")
                if reflection_report:
                    context["reflection_insights"] = [
                        {
                            "title": i.title,
                            "severity": i.severity
                        }
                        for i in reflection_report.insights
                    ]

            report = self._goal_evolver.optimize_goal_system()

            for callback in self._phase_callbacks[EvolutionPhase.GOAL_EVOLUTION]:
                try:
                    callback(report)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return report

        except Exception as e:
            logger.error(f"Goal evolution phase failed: {e}")
            return None

    def _run_architecture_evolution_phase(self) -> Optional[ArchitectureEvolutionReport]:
        """执行架构进化阶段"""
        try:
            report = self._architecture_evolver.evolve_architecture()

            # 保存架构版本
            self._architecture_evolver.save_version(
                changes=[
                    f"Phase: {phase.value}"
                    for phase in (self._current_cycle.phases_completed if self._current_cycle else [])
                ]
            )

            for callback in self._phase_callbacks[EvolutionPhase.ARCHITECTURE_EVOLUTION]:
                try:
                    callback(report)
                except Exception as e:
                    logger.warning(f"Phase callback failed: {e}")

            return report

        except Exception as e:
            logger.error(f"Architecture evolution phase failed: {e}")
            return None

    def _apply_optimization_to_systems(self) -> None:
        """将优化结果应用到各系统"""
        params = self._self_optimizer.get_all_params()

        # 应用到认知系统
        if self._cognitive_manager:
            try:
                cognitive_params = params.get("cognitive", {})
                if hasattr(self._cognitive_manager, 'update_params'):
                    self._cognitive_manager.update_params(cognitive_params)
            except Exception as e:
                logger.warning(f"Failed to apply optimization to cognitive system: {e}")

        # 应用到学习系统
        if self._learning_manager:
            try:
                learning_params = params.get("learning", {})
                if hasattr(self._learning_manager, 'update_params'):
                    self._learning_manager.update_params(learning_params)
            except Exception as e:
                logger.warning(f"Failed to apply optimization to learning system: {e}")

    # ========== 自动进化 ==========

    def auto_evolve(self) -> Optional[EvolutionCycle]:
        """
        自动执行进化（检查时间间隔）

        Returns:
            Optional[EvolutionCycle]: 进化周期，如果未到时间则返回None
        """
        if not self.config.enable_auto_evolution:
            return None

        now = datetime.now()
        if (self._last_evolution_time is None or
            (now - self._last_evolution_time).total_seconds() >= self.config.evolution_interval):
            return self.run_evolution_cycle()

        return None

    async def auto_evolve_async(self) -> Optional[EvolutionCycle]:
        """
        异步自动执行进化

        Returns:
            Optional[EvolutionCycle]: 进化周期
        """
        if not self.config.enable_auto_evolution:
            return None

        now = datetime.now()
        if (self._last_evolution_time is None or
            (now - self._last_evolution_time).total_seconds() >= self.config.evolution_interval):
            return await self.run_evolution_cycle_async()

        return None

    def start_continuous_evolution(self) -> None:
        """启动持续进化（后台任务）"""
        self._is_running = True
        logger.info("Continuous evolution started")

    def stop_continuous_evolution(self) -> None:
        """停止持续进化"""
        self._is_running = False
        logger.info("Continuous evolution stopped")

    def pause(self) -> None:
        """暂停进化"""
        self._paused = True
        logger.info("Evolution paused")

    def resume(self) -> None:
        """恢复进化"""
        self._paused = False
        logger.info("Evolution resumed")

    # ========== 事件记录接口 ==========

    def record_behavior(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        importance: float = 0.5
    ) -> None:
        """
        记录行为（供外部系统调用）

        Args:
            action: 行为描述
            context: 上下文
            success: 是否成功
            importance: 重要性
        """
        self._self_reflection.record_behavior(
            action=action,
            context=context,
            success=success,
            importance=importance
        )

    def record_decision(
        self,
        decision_name: str,
        alternatives: List[str],
        selected: str,
        reasoning: str = "",
        confidence: float = 0.5
    ) -> None:
        """
        记录决策（供外部系统调用）

        Args:
            decision_name: 决策名称
            alternatives: 备选方案
            selected: 选中的方案
            reasoning: 决策理由
            confidence: 置信度
        """
        self._self_reflection.record_decision(
            decision_name=decision_name,
            alternatives=alternatives,
            selected=selected,
            reasoning=reasoning,
            confidence=confidence
        )

    def record_error(
        self,
        description: str,
        category: Optional[ErrorCategory] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录错误（供外部系统调用）

        Args:
            description: 错误描述
            category: 错误分类
            severity: 严重程度
            context: 上下文
        """
        self._error_analyzer.record_error(
            description=description,
            category=category,
            severity=severity,
            context=context
        )

    def record_capability_score(
        self,
        dimension: CapabilityDimension,
        score: float,
        confidence: float = 0.8
    ) -> None:
        """
        记录能力评分（供外部系统调用）

        Args:
            dimension: 能力维度
            score: 评分
            confidence: 置信度
        """
        self._capability_assessor.record_score(
            dimension=dimension,
            score=score,
            confidence=confidence
        )

    def record_information_flow(
        self,
        source_module: str,
        target_module: str,
        data_type: str,
        volume: float = 1.0
    ) -> None:
        """
        记录信息流（供外部系统调用）

        Args:
            source_module: 源模块
            target_module: 目标模块
            data_type: 数据类型
            volume: 数据量
        """
        self._architecture_evolver.record_information_flow(
            source_module_id=source_module,
            target_module_id=target_module,
            data_type=data_type,
            volume=volume
        )

    # ========== 回调注册 ==========

    def register_cycle_callback(
        self,
        callback: Callable[[EvolutionCycle], None]
    ) -> None:
        """
        注册周期完成回调

        Args:
            callback: 回调函数
        """
        self._cycle_callbacks.append(callback)
        logger.debug("Registered cycle callback")

    def register_phase_callback(
        self,
        phase: EvolutionPhase,
        callback: Callable[[Any], None]
    ) -> None:
        """
        注册阶段回调

        Args:
            phase: 进化阶段
            callback: 回调函数
        """
        self._phase_callbacks[phase].append(callback)
        logger.debug(f"Registered phase callback for {phase.value}")

    # ========== 子模块访问 ==========

    @property
    def self_reflection(self) -> SelfReflection:
        """获取自我反思模块"""
        return self._self_reflection

    @property
    def error_analyzer(self) -> ErrorAnalyzer:
        """获取错误分析模块"""
        return self._error_analyzer

    @property
    def capability_assessor(self) -> CapabilityAssessor:
        """获取能力评估模块"""
        return self._capability_assessor

    @property
    def self_optimizer(self) -> SelfOptimizer:
        """获取自我优化模块"""
        return self._self_optimizer

    @property
    def goal_evolver(self) -> GoalEvolver:
        """获取目标进化模块"""
        return self._goal_evolver

    @property
    def architecture_evolver(self) -> ArchitectureEvolver:
        """获取架构进化模块"""
        return self._architecture_evolver

    # ========== 状态查询 ==========

    def get_current_phase(self) -> EvolutionPhase:
        """
        获取当前阶段

        Returns:
            EvolutionPhase: 当前阶段
        """
        return self._current_phase

    def is_running(self) -> bool:
        """
        是否正在运行

        Returns:
            bool: 运行状态
        """
        return self._is_running

    def is_paused(self) -> bool:
        """
        是否已暂停

        Returns:
            bool: 暂停状态
        """
        return self._paused

    def get_current_cycle(self) -> Optional[EvolutionCycle]:
        """
        获取当前周期

        Returns:
            Optional[EvolutionCycle]: 当前周期
        """
        return self._current_cycle

    def get_cycle_history(self, limit: int = 10) -> List[EvolutionCycle]:
        """
        获取周期历史

        Args:
            limit: 数量限制

        Returns:
            List[EvolutionCycle]: 周期列表
        """
        return self._evolution_cycles[-limit:]

    # ========== 统计信息 ==========

    def get_stats(self) -> Dict[str, Any]:
        """
        获取完整统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "manager": {
                "current_phase": self._current_phase.value,
                "is_running": self._is_running,
                "is_paused": self._paused,
                "total_cycles": len(self._evolution_cycles),
                "last_evolution": self._last_evolution_time.isoformat() if self._last_evolution_time else None
            },
            "self_reflection": self._self_reflection.get_stats(),
            "error_analyzer": self._error_analyzer.get_stats(),
            "capability_assessor": self._capability_assessor.get_stats(),
            "self_optimizer": self._self_optimizer.get_stats(),
            "goal_evolver": self._goal_evolver.get_stats(),
            "architecture_evolver": self._architecture_evolver.get_stats()
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        获取综合报告

        Returns:
            Dict[str, Any]: 综合报告
        """
        stats = self.get_stats()

        latest_cycle = self._evolution_cycles[-1] if self._evolution_cycles else None

        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "running": self._is_running,
                "paused": self._paused,
                "current_phase": self._current_phase.value
            },
            "latest_cycle": latest_cycle.model_dump() if latest_cycle else None,
            "module_stats": stats,
            "summary": self._generate_summary(stats)
        }

    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """生成总结"""
        parts = []

        reflection_stats = stats.get("self_reflection", {})
        if reflection_stats.get("total_reports", 0) > 0:
            parts.append(f"已完成 {reflection_stats['total_reports']} 次反思")

        error_stats = stats.get("error_analyzer", {})
        errors = error_stats.get("errors", {})
        if errors.get("total", 0) > 0:
            parts.append(f"记录了 {errors['total']} 个错误")

        goal_stats = stats.get("goal_evolver", {})
        if goal_stats.get("total_goals", 0) > 0:
            parts.append(f"管理 {goal_stats['total_goals']} 个目标")

        arch_stats = stats.get("architecture_evolver", {})
        if arch_stats.get("total_modules", 0) > 0:
            parts.append(f"架构包含 {arch_stats['total_modules']} 个模块")

        return "，".join(parts) if parts else "系统初始化完成，等待运行数据"

    def reset(self) -> None:
        """重置所有状态"""
        self._self_reflection.reset()
        self._error_analyzer.reset()
        self._capability_assessor.reset()
        self._self_optimizer.reset()
        self._goal_evolver.reset()
        self._architecture_evolver.reset()

        self._current_phase = EvolutionPhase.IDLE
        self._evolution_cycles.clear()
        self._current_cycle = None
        self._last_evolution_time = None
        self._is_running = False
        self._paused = False

        logger.info("EvolutionManager reset")
