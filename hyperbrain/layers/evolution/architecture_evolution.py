"""
认知架构进化模块 (Architecture Evolution Module)

在长期运行中优化整体认知架构，优化模块间连接和信息流动，
支持新模块集成，评估架构性能，管理架构版本。

功能：
1. 模块间连接优化
2. 信息流动优化
3. 新模块集成
4. 架构性能评估
5. 架构版本管理
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from collections import defaultdict, deque

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("evolution.architecture")


class ModuleType(str, Enum):
    """模块类型"""
    SENSORY = "sensory"
    MEMORY = "memory"
    COGNITIVE = "cognitive"
    LEARNING = "learning"
    EMOTIONAL = "emotional"
    EXECUTION = "execution"
    CONSCIOUSNESS = "consciousness"
    EVOLUTION = "evolution"
    CUSTOM = "custom"


class ConnectionType(str, Enum):
    """连接类型"""
    FEEDFORWARD = "feedforward"     # 前馈
    FEEDBACK = "feedback"           # 反馈
    BIDIRECTIONAL = "bidirectional" # 双向
    LATERAL = "lateral"             # 横向


class ArchitectureModule(BaseModel):
    """架构模块"""
    module_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="模块名称")
    module_type: ModuleType = Field(...)
    version: str = Field(default="1.0.0")
    status: str = Field(default="active", description="状态: active/inactive/deprecated")
    capabilities: List[str] = Field(default_factory=list)
    performance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    resource_usage: float = Field(default=0.3, ge=0.0, le=1.0)
    reliability: float = Field(default=0.9, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("performance_score", "resource_usage", "reliability")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ModuleConnection(BaseModel):
    """模块连接"""
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_module: str = Field(...)
    target_module: str = Field(...)
    connection_type: ConnectionType = Field(default=ConnectionType.FEEDFORWARD)
    weight: float = Field(default=1.0, ge=0.0, le=5.0)
    bandwidth: float = Field(default=1.0, ge=0.0, le=10.0)
    latency: float = Field(default=0.1, ge=0.0, description="延迟(秒)")
    reliability: float = Field(default=0.95, ge=0.0, le=1.0)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("weight", "bandwidth", "reliability")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(10.0 if "bandwidth" in cls.model_fields else 5.0, v))


class InformationFlow(BaseModel):
    """信息流"""
    flow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_module: str = Field(...)
    target_module: str = Field(...)
    data_type: str = Field(..., description="数据类型")
    frequency: float = Field(default=1.0, ge=0.0, description="频率(Hz)")
    volume: float = Field(default=1.0, ge=0.0, description="数据量")
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    efficiency: float = Field(default=0.8, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("priority", "efficiency")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ArchitectureVersion(BaseModel):
    """架构版本"""
    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version_number: str = Field(..., description="版本号")
    modules: List[str] = Field(default_factory=list)
    connections: List[str] = Field(default_factory=list)
    performance_baseline: float = Field(default=0.5, ge=0.0, le=1.0)
    changes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)

    @field_validator("performance_baseline")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ArchitectureMetrics(BaseModel):
    """架构指标"""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    overall_performance: float = Field(default=0.0, ge=0.0, le=1.0)
    modularity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integration_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    fault_tolerance: float = Field(default=0.0, ge=0.0, le=1.0)
    scalability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    resource_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    bottleneck_modules: List[str] = Field(default_factory=list)
    underutilized_modules: List[str] = Field(default_factory=list)

    @field_validator("overall_performance", "modularity_score", "integration_efficiency",
                     "fault_tolerance", "scalability_score", "resource_efficiency")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ArchitectureEvolutionReport(BaseModel):
    """架构进化报告"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    current_version: str = Field(...)
    metrics: ArchitectureMetrics = Field(...)
    proposed_changes: List[str] = Field(default_factory=list)
    new_modules: List[ArchitectureModule] = Field(default_factory=list)
    removed_modules: List[ArchitectureModule] = Field(default_factory=list)
    optimized_connections: List[ModuleConnection] = Field(default_factory=list)
    summary: str = Field(default="")


class ArchitectureEvolutionConfig(BaseModel):
    """架构进化配置"""
    evaluation_interval: float = Field(default=604800.0, description="评估间隔(秒)")
    min_module_performance: float = Field(default=0.3, ge=0.0, le=1.0)
    connection_optimization_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_auto_restructure: bool = Field(default=False)
    max_modules: int = Field(default=50)
    version_history_limit: int = Field(default=10)


class ArchitectureEvolver:
    """
    认知架构进化系统

    在长期运行中优化整体认知架构，提升系统整体性能。

    Attributes:
        config: 进化配置
        modules: 模块注册表
        connections: 连接注册表
        versions: 版本历史
    """

    def __init__(self, config: Optional[ArchitectureEvolutionConfig] = None):
        self.config = config or ArchitectureEvolutionConfig()
        self._modules: Dict[str, ArchitectureModule] = {}
        self._connections: Dict[str, ModuleConnection] = {}
        self._information_flows: deque = deque(maxlen=1000)
        self._versions: List[ArchitectureVersion] = []
        self._metrics_history: deque = deque(maxlen=100)
        self._last_evaluation_time: Optional[datetime] = None
        self._evolution_callbacks: List[Callable[[ArchitectureEvolutionReport], None]] = []

        # 初始化默认架构
        self._init_default_architecture()
        logger.info("ArchitectureEvolver initialized")

    def _init_default_architecture(self) -> None:
        """初始化默认认知架构"""
        default_modules = [
            ("sensory_input", ModuleType.SENSORY, ["perception", "input_processing"]),
            ("working_memory", ModuleType.MEMORY, ["short_term_storage", "attention"]),
            ("long_term_memory", ModuleType.MEMORY, ["storage", "retrieval", "consolidation"]),
            ("reasoning_engine", ModuleType.COGNITIVE, ["deduction", "induction", "analogy"]),
            ("decision_maker", ModuleType.COGNITIVE, ["evaluation", "selection", "planning"]),
            ("learning_engine", ModuleType.LEARNING, ["acquisition", "integration", "transfer"]),
            ("emotion_engine", ModuleType.EMOTIONAL, ["appraisal", "regulation", "expression"]),
            ("action_executor", ModuleType.EXECUTION, ["planning", "coordination", "monitoring"]),
            ("consciousness_monitor", ModuleType.CONSCIOUSNESS, ["awareness", "reflection", "integration"]),
            ("evolution_manager", ModuleType.EVOLUTION, ["optimization", "adaptation", "growth"]),
        ]

        module_ids = {}
        for name, mtype, capabilities in default_modules:
            module = ArchitectureModule(
                name=name,
                module_type=mtype,
                capabilities=capabilities
            )
            self._modules[module.module_id] = module
            module_ids[name] = module.module_id

        # 建立默认连接
        default_connections = [
            ("sensory_input", "working_memory", ConnectionType.FEEDFORWARD),
            ("working_memory", "reasoning_engine", ConnectionType.BIDIRECTIONAL),
            ("working_memory", "long_term_memory", ConnectionType.BIDIRECTIONAL),
            ("reasoning_engine", "decision_maker", ConnectionType.FEEDFORWARD),
            ("decision_maker", "action_executor", ConnectionType.FEEDFORWARD),
            ("learning_engine", "long_term_memory", ConnectionType.BIDIRECTIONAL),
            ("emotion_engine", "decision_maker", ConnectionType.FEEDFORWARD),
            ("consciousness_monitor", "working_memory", ConnectionType.FEEDBACK),
            ("evolution_manager", "learning_engine", ConnectionType.FEEDBACK),
            ("evolution_manager", "reasoning_engine", ConnectionType.FEEDBACK),
        ]

        for source_name, target_name, ctype in default_connections:
            if source_name in module_ids and target_name in module_ids:
                conn = ModuleConnection(
                    source_module=module_ids[source_name],
                    target_module=module_ids[target_name],
                    connection_type=ctype
                )
                self._connections[conn.connection_id] = conn

        # 创建初始版本
        self._create_version("1.0.0", ["Initial architecture"])

    # ========== 模块管理 ==========

    def register_module(
        self,
        name: str,
        module_type: ModuleType,
        capabilities: Optional[List[str]] = None,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArchitectureModule:
        """
        注册新模块

        Args:
            name: 模块名称
            module_type: 模块类型
            capabilities: 能力列表
            version: 版本
            metadata: 元数据

        Returns:
            ArchitectureModule: 注册的模块
        """
        if len(self._modules) >= self.config.max_modules:
            logger.warning("Maximum module limit reached")
            # 尝试移除性能最低的模块
            self._remove_worst_module()

        module = ArchitectureModule(
            name=name,
            module_type=module_type,
            capabilities=capabilities or [],
            version=version,
            metadata=metadata or {}
        )

        self._modules[module.module_id] = module
        logger.info(f"Registered module: {name} ({module_type.value})")
        return module

    def unregister_module(self, module_id: str) -> bool:
        """
        注销模块

        Args:
            module_id: 模块ID

        Returns:
            bool: 是否成功
        """
        if module_id not in self._modules:
            return False

        module = self._modules[module_id]
        module.status = "deprecated"

        # 移除相关连接
        connections_to_remove = [
            cid for cid, conn in self._connections.items()
            if conn.source_module == module_id or conn.target_module == module_id
        ]
        for cid in connections_to_remove:
            del self._connections[cid]

        logger.info(f"Unregistered module: {module.name}")
        return True

    def update_module_performance(
        self,
        module_id: str,
        performance_score: float,
        resource_usage: Optional[float] = None
    ) -> bool:
        """
        更新模块性能

        Args:
            module_id: 模块ID
            performance_score: 性能评分
            resource_usage: 资源使用

        Returns:
            bool: 是否成功
        """
        if module_id not in self._modules:
            return False

        module = self._modules[module_id]
        module.performance_score = max(0.0, min(1.0, performance_score))
        if resource_usage is not None:
            module.resource_usage = max(0.0, min(1.0, resource_usage))
        module.last_updated = datetime.now()

        return True

    def _remove_worst_module(self) -> None:
        """移除性能最低的模块"""
        inactive_modules = [
            m for m in self._modules.values()
            if m.status == "deprecated"
        ]
        if inactive_modules:
            worst = min(inactive_modules, key=lambda m: m.performance_score)
            # 清理与该模块关联的所有连接，避免悬空引用
            stale_conn_ids = [
                cid for cid, conn in self._connections.items()
                if conn.source_module == worst.module_id or
                   conn.target_module == worst.module_id
            ]
            for cid in stale_conn_ids:
                del self._connections[cid]
            del self._modules[worst.module_id]
            logger.info(f"Removed deprecated module: {worst.name} (cleaned {len(stale_conn_ids)} stale connections)")

    # ========== 连接管理 ==========

    def add_connection(
        self,
        source_module_id: str,
        target_module_id: str,
        connection_type: ConnectionType = ConnectionType.FEEDFORWARD,
        weight: float = 1.0,
        bandwidth: float = 1.0
    ) -> Optional[ModuleConnection]:
        """
        添加模块连接

        Args:
            source_module_id: 源模块ID
            target_module_id: 目标模块ID
            connection_type: 连接类型
            weight: 权重
            bandwidth: 带宽

        Returns:
            Optional[ModuleConnection]: 连接对象
        """
        if source_module_id not in self._modules or target_module_id not in self._modules:
            return None

        # 检查是否已存在相同连接
        for conn in self._connections.values():
            if (conn.source_module == source_module_id and
                conn.target_module == target_module_id):
                # 更新现有连接
                conn.weight = weight
                conn.bandwidth = bandwidth
                conn.connection_type = connection_type
                return conn

        conn = ModuleConnection(
            source_module=source_module_id,
            target_module=target_module_id,
            connection_type=connection_type,
            weight=weight,
            bandwidth=bandwidth
        )

        self._connections[conn.connection_id] = conn
        logger.debug(f"Added connection: {source_module_id} -> {target_module_id}")
        return conn

    def remove_connection(self, connection_id: str) -> bool:
        """
        移除连接

        Args:
            connection_id: 连接ID

        Returns:
            bool: 是否成功
        """
        if connection_id not in self._connections:
            return False

        del self._connections[connection_id]
        return True

    def optimize_connections(self) -> List[ModuleConnection]:
        """
        优化模块连接

        Returns:
            List[ModuleConnection]: 优化后的连接
        """
        optimized = []

        for conn in list(self._connections.values()):
            source = self._modules.get(conn.source_module)
            target = self._modules.get(conn.target_module)

            if not source or not target:
                continue

            # 基于模块性能调整权重
            performance_factor = (source.performance_score + target.performance_score) / 2

            # 基于信息流调整带宽
            relevant_flows = [
                f for f in self._information_flows
                if f.source_module == conn.source_module and
                   f.target_module == conn.target_module
            ]

            if relevant_flows:
                avg_volume = sum(f.volume for f in relevant_flows) / len(relevant_flows)
                new_bandwidth = max(0.5, min(10.0, avg_volume * 2))

                if abs(new_bandwidth - conn.bandwidth) > 0.5:
                    conn.bandwidth = new_bandwidth
                    conn.weight = max(0.1, min(5.0, conn.weight * performance_factor))
                    optimized.append(conn)

        logger.info(f"Optimized {len(optimized)} connections")
        return optimized

    # ========== 信息流管理 ==========

    def record_information_flow(
        self,
        source_module_id: str,
        target_module_id: str,
        data_type: str,
        volume: float = 1.0,
        priority: float = 0.5
    ) -> InformationFlow:
        """
        记录信息流

        Args:
            source_module_id: 源模块ID
            target_module_id: 目标模块ID
            data_type: 数据类型
            volume: 数据量
            priority: 优先级

        Returns:
            InformationFlow: 信息流记录
        """
        flow = InformationFlow(
            source_module=source_module_id,
            target_module=target_module_id,
            data_type=data_type,
            volume=volume,
            priority=priority
        )

        self._information_flows.append(flow)
        return flow

    def analyze_information_flow(self) -> Dict[str, Any]:
        """
        分析信息流

        Returns:
            Dict[str, Any]: 分析结果
        """
        if not self._information_flows:
            return {"total_flows": 0}

        # 统计各模块的流量
        module_traffic = defaultdict(lambda: {"in": 0.0, "out": 0.0})
        for flow in self._information_flows:
            module_traffic[flow.source_module]["out"] += flow.volume
            module_traffic[flow.target_module]["in"] += flow.volume

        # 识别瓶颈
        bottlenecks = []
        for module_id, traffic in module_traffic.items():
            if traffic["in"] > traffic["out"] * 3:
                bottlenecks.append(module_id)

        # 识别低利用率模块
        underutilized = []
        for module_id, module in self._modules.items():
            total_traffic = module_traffic.get(module_id, {"in": 0, "out": 0})
            if total_traffic["in"] + total_traffic["out"] < 1.0:
                underutilized.append(module_id)

        return {
            "total_flows": len(self._information_flows),
            "module_traffic": dict(module_traffic),
            "bottleneck_modules": bottlenecks,
            "underutilized_modules": underutilized
        }

    # ========== 架构评估 ==========

    def evaluate_architecture(self) -> ArchitectureMetrics:
        """
        评估架构性能

        Returns:
            ArchitectureMetrics: 评估指标
        """
        if not self._modules:
            return ArchitectureMetrics(overall_performance=0.0)

        # 计算整体性能
        performances = [m.performance_score for m in self._modules.values()]
        overall_performance = sum(performances) / len(performances)

        # 计算模块化程度（基于连接密度）
        n_modules = len(self._modules)
        n_connections = len(self._connections)
        max_connections = n_modules * (n_modules - 1)
        connection_density = n_connections / max_connections if max_connections > 0 else 0
        modularity = 1.0 - connection_density  # 低密度 = 高模块化

        # 计算集成效率
        flow_analysis = self.analyze_information_flow()
        bottleneck_count = len(flow_analysis.get("bottleneck_modules", []))
        integration_efficiency = max(0.0, 1.0 - bottleneck_count / max(n_modules, 1))

        # 计算容错性
        active_connections = sum(1 for c in self._connections.values() if c.active)
        total_connections = len(self._connections)
        fault_tolerance = active_connections / total_connections if total_connections > 0 else 0

        # 计算可扩展性
        scalability = max(0.0, 1.0 - len(self._modules) / self.config.max_modules)

        # 计算资源效率
        resource_usages = [m.resource_usage for m in self._modules.values()]
        avg_resource = sum(resource_usages) / len(resource_usages)
        resource_efficiency = 1.0 - avg_resource

        metrics = ArchitectureMetrics(
            overall_performance=overall_performance,
            modularity_score=modularity,
            integration_efficiency=integration_efficiency,
            fault_tolerance=fault_tolerance,
            scalability_score=scalability,
            resource_efficiency=resource_efficiency,
            bottleneck_modules=flow_analysis.get("bottleneck_modules", []),
            underutilized_modules=flow_analysis.get("underutilized_modules", [])
        )

        self._metrics_history.append(metrics)
        self._last_evaluation_time = datetime.now()

        logger.info(f"Architecture evaluation: performance={overall_performance:.3f}")
        return metrics

    # ========== 架构优化 ==========

    def evolve_architecture(self) -> ArchitectureEvolutionReport:
        """
        执行架构进化

        Returns:
            ArchitectureEvolutionReport: 进化报告
        """
        logger.info("Starting architecture evolution")

        # 清理悬空连接（target_module 或 source_module 对应的模块已被移除）
        stale_conn_ids = [
            cid for cid, conn in self._connections.items()
            if conn.source_module not in self._modules or
               conn.target_module not in self._modules
        ]
        for cid in stale_conn_ids:
            del self._connections[cid]
        if stale_conn_ids:
            logger.warning(f"Cleaned {len(stale_conn_ids)} stale connections before evolution")

        # 评估当前架构
        metrics = self.evaluate_architecture()

        # 优化连接
        optimized_connections = self.optimize_connections()

        # 识别需要改进的模块
        new_modules = []
        removed_modules = []
        proposed_changes = []

        # 检查低性能模块
        for module in list(self._modules.values()):
            if module.performance_score < self.config.min_module_performance:
                if module.status != "deprecated":
                    proposed_changes.append(
                        f"模块 {module.name} 性能过低，建议优化或替换"
                    )

        # 检查缺失的关键连接
        critical_pairs = [
            (ModuleType.SENSORY, ModuleType.MEMORY),
            (ModuleType.MEMORY, ModuleType.COGNITIVE),
            (ModuleType.COGNITIVE, ModuleType.EXECUTION),
            (ModuleType.LEARNING, ModuleType.MEMORY),
        ]

        for source_type, target_type in critical_pairs:
            source_modules = [m for m in self._modules.values() if m.module_type == source_type]
            target_modules = [m for m in self._modules.values() if m.module_type == target_type]

            for s in source_modules:
                for t in target_modules:
                    existing = any(
                        c.source_module == s.module_id and c.target_module == t.module_id
                        for c in self._connections.values()
                    )
                    if not existing:
                        conn = self.add_connection(s.module_id, t.module_id)
                        if conn:
                            optimized_connections.append(conn)
                            proposed_changes.append(
                                f"添加关键连接: {s.name} -> {t.name}"
                            )

        # 获取当前版本
        current_version = "1.0.0"
        if self._versions:
            current_version = self._versions[-1].version_number

        # 生成总结
        summary = (
            f"架构进化完成。"
            f"整体性能: {metrics.overall_performance:.1%}。"
            f"优化连接: {len(optimized_connections)} 条。"
            f"建议改进: {len(proposed_changes)} 项。"
        )

        report = ArchitectureEvolutionReport(
            current_version=current_version,
            metrics=metrics,
            proposed_changes=proposed_changes,
            new_modules=new_modules,
            removed_modules=removed_modules,
            optimized_connections=optimized_connections,
            summary=summary
        )

        # 触发回调
        for callback in self._evolution_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.warning(f"Architecture evolution callback failed: {e}")

        logger.info("Architecture evolution completed")
        return report

    def auto_evolve(self) -> Optional[ArchitectureEvolutionReport]:
        """
        自动进化（检查时间间隔）

        Returns:
            Optional[ArchitectureEvolutionReport]: 进化报告
        """
        now = datetime.now()
        if (self._last_evaluation_time is None or
            (now - self._last_evaluation_time).total_seconds() >= self.config.evaluation_interval):
            return self.evolve_architecture()
        return None

    # ========== 版本管理 ==========

    def _create_version(self, version_number: str, changes: List[str]) -> ArchitectureVersion:
        """创建架构版本"""
        version = ArchitectureVersion(
            version_number=version_number,
            modules=list(self._modules.keys()),
            connections=list(self._connections.keys()),
            changes=changes
        )

        # 停用旧版本
        for v in self._versions:
            v.is_active = False

        self._versions.append(version)

        # 限制版本历史
        if len(self._versions) > self.config.version_history_limit:
            self._versions = self._versions[-self.config.version_history_limit:]

        logger.info(f"Created architecture version: {version_number}")
        return version

    def save_version(self, changes: Optional[List[str]] = None) -> ArchitectureVersion:
        """
        保存当前架构版本

        Args:
            changes: 变更说明

        Returns:
            ArchitectureVersion: 版本记录
        """
        # 生成新版本号
        if self._versions:
            last_version = self._versions[-1].version_number
            parts = last_version.split(".")
            if len(parts) == 3:
                major, minor, patch = parts
                new_version = f"{major}.{minor}.{int(patch) + 1}"
            else:
                new_version = "1.0.0"
        else:
            new_version = "1.0.0"

        return self._create_version(new_version, changes or [])

    def rollback_version(self, version_number: str) -> bool:
        """
        回滚到指定版本

        Args:
            version_number: 版本号

        Returns:
            bool: 是否成功
        """
        target_version = None
        for v in self._versions:
            if v.version_number == version_number:
                target_version = v
                break

        if not target_version:
            return False

        # 恢复模块
        current_modules = set(self._modules.keys())
        target_modules = set(target_version.modules)

        # 移除多余模块
        for module_id in current_modules - target_modules:
            if module_id in self._modules:
                del self._modules[module_id]

        # 恢复连接
        current_connections = set(self._connections.keys())
        target_connections = set(target_version.connections)

        for conn_id in current_connections - target_connections:
            if conn_id in self._connections:
                del self._connections[conn_id]

        # 激活版本
        for v in self._versions:
            v.is_active = False
        target_version.is_active = True

        logger.info(f"Rolled back to version: {version_number}")
        return True

    def get_version_history(self) -> List[ArchitectureVersion]:
        """
        获取版本历史

        Returns:
            List[ArchitectureVersion]: 版本列表
        """
        return self._versions.copy()

    # ========== 回调注册 ==========

    def register_evolution_callback(
        self,
        callback: Callable[[ArchitectureEvolutionReport], None]
    ) -> None:
        """
        注册进化回调

        Args:
            callback: 回调函数
        """
        self._evolution_callbacks.append(callback)
        logger.debug("Registered architecture evolution callback")

    # ========== 查询接口 ==========

    def get_module(self, module_id: str) -> Optional[ArchitectureModule]:
        """
        获取模块

        Args:
            module_id: 模块ID

        Returns:
            Optional[ArchitectureModule]: 模块
        """
        return self._modules.get(module_id)

    def get_modules_by_type(self, module_type: ModuleType) -> List[ArchitectureModule]:
        """
        按类型获取模块

        Args:
            module_type: 模块类型

        Returns:
            List[ArchitectureModule]: 模块列表
        """
        return [m for m in self._modules.values() if m.module_type == module_type]

    def get_module_connections(self, module_id: str) -> Dict[str, List[ModuleConnection]]:
        """
        获取模块的连接

        Args:
            module_id: 模块ID

        Returns:
            Dict[str, List[ModuleConnection]]: 输入和输出连接
        """
        incoming = [
            c for c in self._connections.values()
            if c.target_module == module_id
        ]
        outgoing = [
            c for c in self._connections.values()
            if c.source_module == module_id
        ]
        return {"incoming": incoming, "outgoing": outgoing}

    def get_architecture_graph(self) -> Dict[str, Any]:
        """
        获取架构图数据

        Returns:
            Dict[str, Any]: 图数据
        """
        return {
            "nodes": [
                {
                    "id": m.module_id,
                    "name": m.name,
                    "type": m.module_type.value,
                    "performance": m.performance_score,
                    "status": m.status
                }
                for m in self._modules.values()
            ],
            "edges": [
                {
                    "id": c.connection_id,
                    "source": c.source_module,
                    "target": c.target_module,
                    "type": c.connection_type.value,
                    "weight": c.weight
                }
                for c in self._connections.values()
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        type_counts = defaultdict(int)
        for m in self._modules.values():
            type_counts[m.module_type.value] += 1

        return {
            "total_modules": len(self._modules),
            "total_connections": len(self._connections),
            "module_types": dict(type_counts),
            "total_versions": len(self._versions),
            "current_version": self._versions[-1].version_number if self._versions else None,
            "information_flows": len(self._information_flows),
            "last_evaluation": self._last_evaluation_time.isoformat() if self._last_evaluation_time else None
        }

    def reset(self) -> None:
        """重置所有状态"""
        self._modules.clear()
        self._connections.clear()
        self._information_flows.clear()
        self._versions.clear()
        self._metrics_history.clear()
        self._last_evaluation_time = None
        self._init_default_architecture()
        logger.info("ArchitectureEvolver reset")
