"""
能力迁移机制 (Transfer Learning Mechanism)

实现跨领域知识迁移：
- 识别源领域和目标领域
- 知识映射和转换
- 技能迁移评估
- 跨领域应用
- 迁移效果监控
"""

import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("learning.transfer")


class DomainType(str, Enum):
    """领域类型"""
    LANGUAGE = "language"
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ARTS = "arts"
    TECHNOLOGY = "technology"
    SOCIAL = "social"
    PHYSICAL = "physical"
    COGNITIVE = "cognitive"
    GENERAL = "general"


class TransferType(str, Enum):
    """迁移类型"""
    NEAR_TRANSFER = "near_transfer"  # 相似领域
    FAR_TRANSFER = "far_transfer"    # 不同领域
    POSITIVE = "positive"            # 正向迁移
    NEGATIVE = "negative"            # 负向迁移
    ZERO = "zero"                    # 零迁移


class Domain(BaseModel):
    """领域模型"""
    domain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    domain_type: DomainType = Field(default=DomainType.GENERAL)
    description: str = Field(default="")
    key_features: List[str] = Field(default_factory=list)
    related_domains: List[str] = Field(default_factory=list)
    knowledge_items: List[str] = Field(default_factory=list)
    skill_items: List[str] = Field(default_factory=list)
    complexity_level: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("complexity_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeMapping(BaseModel):
    """知识映射"""
    mapping_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_knowledge: str = Field(...)
    target_knowledge: str = Field(...)
    source_domain: str = Field(...)
    target_domain: str = Field(...)
    mapping_type: str = Field(default="analogy")  # analogy, abstraction, decomposition
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    transformation_required: bool = Field(default=False)
    transformation_rules: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("similarity_score", "confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class SkillTransfer(BaseModel):
    """技能迁移"""
    transfer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = Field(...)
    source_domain: str = Field(...)
    target_domain: str = Field(...)
    transfer_type: TransferType = Field(default=TransferType.NEAR_TRANSFER)
    transfer_score: float = Field(default=0.0, ge=0.0, le=1.0)
    adaptation_difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    prerequisites_met: bool = Field(default=False)
    missing_prerequisites: List[str] = Field(default_factory=list)
    estimated_learning_time: float = Field(default=1.0)  # hours
    success: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("transfer_score", "adaptation_difficulty")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CrossDomainApplication(BaseModel):
    """跨领域应用"""
    application_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_domain: str = Field(...)
    target_domain: str = Field(...)
    application_description: str = Field(default="")
    approach_used: str = Field(default="")
    outcome: str = Field(default="")
    effectiveness: float = Field(default=0.0, ge=0.0, le=1.0)
    lessons_learned: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("effectiveness")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class TransferMonitor(BaseModel):
    """迁移监控"""
    monitor_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transfer_id: str = Field(...)
    check_point: str = Field(default="")
    performance_metric: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_metric: float = Field(default=0.0, ge=0.0, le=1.0)
    deviation: float = Field(default=0.0)
    status: str = Field(default="on_track")  # on_track, at_risk, failed, exceeded
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("performance_metric", "expected_metric")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class TransferLearningConfig:
    """能力迁移配置"""
    min_similarity_threshold: float = 0.3
    near_transfer_threshold: float = 0.7
    adaptation_time_base: float = 10.0  # hours
    monitor_interval: float = 86400.0  # 1 day
    max_transfer_depth: int = 3
    enable_negative_transfer_detection: bool = True


class TransferLearningMechanism:
    """
    能力迁移机制

    实现跨领域知识迁移：
    1. 领域识别：分析源领域和目标领域
    2. 知识映射：建立知识间的对应关系
    3. 迁移评估：评估迁移可行性
    4. 跨领域应用：将知识应用到新领域
    5. 效果监控：跟踪迁移效果

    Attributes:
        config: 配置
        domains: 领域库
        mappings: 知识映射
        transfers: 技能迁移记录
        applications: 跨领域应用记录
        monitors: 监控记录
    """

    def __init__(self, config: Optional[TransferLearningConfig] = None):
        self.config = config or TransferLearningConfig()

        # 领域管理
        self.domains: Dict[str, Domain] = {}
        self.domain_by_name: Dict[str, str] = {}  # name -> domain_id
        self.domain_type_index: Dict[DomainType, List[str]] = defaultdict(list)

        # 知识映射
        self.mappings: Dict[str, KnowledgeMapping] = {}
        self.domain_pair_mappings: Dict[str, List[str]] = defaultdict(list)

        # 技能迁移
        self.transfers: Dict[str, SkillTransfer] = {}
        self.transfer_history: List[str] = []

        # 跨领域应用
        self.applications: Dict[str, CrossDomainApplication] = {}
        self.application_history: List[str] = []

        # 监控
        self.monitors: Dict[str, TransferMonitor] = {}
        self.active_monitors: Set[str] = set()

        # 统计
        self.total_domains: int = 0
        self.total_mappings: int = 0
        self.total_transfers: int = 0
        self.total_applications: int = 0
        self.successful_transfers: int = 0

        logger.info("TransferLearningMechanism initialized")

    # ========== 识别源领域和目标领域 ==========

    def register_domain(self, name: str, domain_type: DomainType = DomainType.GENERAL,
                       description: str = "",
                       key_features: Optional[List[str]] = None,
                       complexity_level: float = 0.5) -> Domain:
        """
        注册领域

        Args:
            name: 领域名称
            domain_type: 领域类型
            description: 描述
            key_features: 关键特征
            complexity_level: 复杂度

        Returns:
            Domain: 领域对象
        """
        if name in self.domain_by_name:
            domain_id = self.domain_by_name[name]
            return self.domains[domain_id]

        self.total_domains += 1
        domain = Domain(
            name=name,
            domain_type=domain_type,
            description=description,
            key_features=key_features or [],
            complexity_level=complexity_level
        )

        self.domains[domain.domain_id] = domain
        self.domain_by_name[name] = domain.domain_id
        self.domain_type_index[domain_type].append(domain.domain_id)

        logger.info(f"Registered domain: {name} ({domain_type.value})")
        return domain

    def get_domain(self, name_or_id: str) -> Optional[Domain]:
        """获取领域"""
        if name_or_id in self.domains:
            return self.domains[name_or_id]
        if name_or_id in self.domain_by_name:
            return self.domains[self.domain_by_name[name_or_id]]
        return None

    def calculate_domain_similarity(self, domain_a: str, domain_b: str) -> float:
        """
        计算领域相似度

        Args:
            domain_a: 领域A
            domain_b: 领域B

        Returns:
            float: 相似度（0-1）
        """
        dom_a = self.get_domain(domain_a)
        dom_b = self.get_domain(domain_b)

        if not dom_a or not dom_b:
            return 0.0

        if dom_a.domain_id == dom_b.domain_id:
            return 1.0

        # 类型相同增加相似度
        type_similarity = 0.3 if dom_a.domain_type == dom_b.domain_type else 0.0

        # 特征重叠
        features_a = set(dom_a.key_features)
        features_b = set(dom_b.key_features)
        if features_a and features_b:
            feature_overlap = len(features_a & features_b) / max(len(features_a | features_b), 1)
        else:
            feature_overlap = 0.0

        # 复杂度差异
        complexity_diff = abs(dom_a.complexity_level - dom_b.complexity_level)
        complexity_similarity = 1.0 - complexity_diff

        return min(1.0, (type_similarity + feature_overlap * 0.5 + complexity_similarity * 0.2))

    def identify_transfer_path(self, source: str, target: str,
                               max_depth: int = 3) -> List[List[str]]:
        """
        识别迁移路径

        Args:
            source: 源领域
            target: 目标领域
            max_depth: 最大深度

        Returns:
            List[List[str]]: 可能的迁移路径
        """
        paths = []
        visited = {source}

        def dfs(current: str, path: List[str], depth: int) -> None:
            if depth > max_depth:
                return
            if current == target and len(path) > 1:
                paths.append(path.copy())
                return

            # 寻找相关领域
            for domain_name in self.domain_by_name.keys():
                if domain_name not in visited:
                    similarity = self.calculate_domain_similarity(current, domain_name)
                    if similarity > self.config.min_similarity_threshold:
                        visited.add(domain_name)
                        path.append(domain_name)
                        dfs(domain_name, path, depth + 1)
                        path.pop()
                        visited.remove(domain_name)

        dfs(source, [source], 0)
        return paths

    # ========== 知识映射和转换 ==========

    def create_mapping(self, source_knowledge: str, target_knowledge: str,
                      source_domain: str, target_domain: str,
                      mapping_type: str = "analogy",
                      transformation_rules: Optional[List[str]] = None) -> Optional[KnowledgeMapping]:
        """
        创建知识映射

        Args:
            source_knowledge: 源知识
            target_knowledge: 目标知识
            source_domain: 源领域
            target_domain: 目标领域
            mapping_type: 映射类型
            transformation_rules: 转换规则

        Returns:
            Optional[KnowledgeMapping]: 知识映射
        """
        # 检查领域是否存在
        if not self.get_domain(source_domain) or not self.get_domain(target_domain):
            logger.warning(f"Cannot create mapping: domain not found")
            return None

        self.total_mappings += 1

        # 计算相似度
        similarity = self._calculate_knowledge_similarity(
            source_knowledge, target_knowledge, source_domain, target_domain
        )

        mapping = KnowledgeMapping(
            source_knowledge=source_knowledge,
            target_knowledge=target_knowledge,
            source_domain=source_domain,
            target_domain=target_domain,
            mapping_type=mapping_type,
            similarity_score=similarity,
            transformation_required=similarity < 0.8,
            transformation_rules=transformation_rules or [],
            confidence=min(1.0, similarity + 0.2)
        )

        self.mappings[mapping.mapping_id] = mapping

        pair_key = f"{source_domain}->{target_domain}"
        self.domain_pair_mappings[pair_key].append(mapping.mapping_id)

        logger.info(f"Created mapping: {source_domain} -> {target_domain}, similarity={similarity:.2f}")
        return mapping

    def _calculate_knowledge_similarity(self, source: str, target: str,
                                        source_domain: str, target_domain: str) -> float:
        """计算知识相似度"""
        # 基于内容的相似度
        words_source = set(source.lower().split())
        words_target = set(target.lower().split())
        intersection = len(words_source & words_target)
        union = len(words_source | words_target)
        content_similarity = intersection / union if union > 0 else 0.0

        # 领域相似度
        domain_similarity = self.calculate_domain_similarity(source_domain, target_domain)

        return (content_similarity * 0.6 + domain_similarity * 0.4)

    def find_mappings(self, source_domain: str, target_domain: str) -> List[KnowledgeMapping]:
        """
        查找领域间的映射

        Args:
            source_domain: 源领域
            target_domain: 目标领域

        Returns:
            List[KnowledgeMapping]: 映射列表
        """
        pair_key = f"{source_domain}->{target_domain}"
        mapping_ids = self.domain_pair_mappings.get(pair_key, [])
        return [self.mappings[mid] for mid in mapping_ids if mid in self.mappings]

    def apply_mapping(self, mapping_id: str, input_data: Any) -> Dict[str, Any]:
        """
        应用知识映射

        Args:
            mapping_id: 映射ID
            input_data: 输入数据

        Returns:
            Dict[str, Any]: 映射结果
        """
        if mapping_id not in self.mappings:
            return {"success": False, "error": "Mapping not found"}

        mapping = self.mappings[mapping_id]

        # 应用转换规则
        transformed = input_data
        for rule in mapping.transformation_rules:
            # 简化实现：规则作为描述
            transformed = f"[{rule}] {transformed}"

        return {
            "success": True,
            "original": input_data,
            "transformed": transformed,
            "mapping_type": mapping.mapping_type,
            "confidence": mapping.confidence
        }

    # ========== 技能迁移评估 ==========

    def assess_transfer(self, skill_name: str, source_domain: str,
                       target_domain: str,
                       user_proficiency: float = 0.5) -> SkillTransfer:
        """
        评估技能迁移可行性

        Args:
            skill_name: 技能名称
            source_domain: 源领域
            target_domain: 目标领域
            user_proficiency: 用户在源领域的熟练度

        Returns:
            SkillTransfer: 迁移评估结果
        """
        self.total_transfers += 1

        # 计算领域相似度
        domain_similarity = self.calculate_domain_similarity(source_domain, target_domain)

        # 确定迁移类型
        if domain_similarity > self.config.near_transfer_threshold:
            transfer_type = TransferType.NEAR_TRANSFER
        else:
            transfer_type = TransferType.FAR_TRANSFER

        # 计算迁移分数
        base_transfer_score = domain_similarity * user_proficiency

        # 检查已有映射
        existing_mappings = self.find_mappings(source_domain, target_domain)
        if existing_mappings:
            mapping_bonus = sum(m.similarity_score for m in existing_mappings) / len(existing_mappings)
            base_transfer_score = min(1.0, base_transfer_score + mapping_bonus * 0.2)

        # 计算适应难度
        adaptation_difficulty = 1.0 - domain_similarity

        # 检查前置条件
        source_dom = self.get_domain(source_domain)
        target_dom = self.get_domain(target_domain)

        missing_prerequisites = []
        prerequisites_met = True

        if target_dom and target_dom.key_features:
            # 简单检查：假设源领域需要覆盖目标领域的关键特征
            source_features = set(source_dom.key_features) if source_dom else set()
            for feature in target_dom.key_features:
                if feature not in source_features:
                    missing_prerequisites.append(feature)
                    prerequisites_met = False

        # 估计学习时间
        estimated_time = self.config.adaptation_time_base * (1 + adaptation_difficulty)

        transfer = SkillTransfer(
            skill_name=skill_name,
            source_domain=source_domain,
            target_domain=target_domain,
            transfer_type=transfer_type,
            transfer_score=base_transfer_score,
            adaptation_difficulty=adaptation_difficulty,
            prerequisites_met=prerequisites_met,
            missing_prerequisites=missing_prerequisites,
            estimated_learning_time=estimated_time
        )

        self.transfers[transfer.transfer_id] = transfer
        self.transfer_history.append(transfer.transfer_id)

        logger.info(f"Transfer assessment: {skill_name} from {source_domain} to {target_domain}, "
                   f"score={base_transfer_score:.2f}")
        return transfer

    def execute_transfer(self, transfer_id: str,
                        execution_context: Optional[Dict[str, Any]] = None) -> SkillTransfer:
        """
        执行技能迁移

        Args:
            transfer_id: 迁移ID
            execution_context: 执行上下文

        Returns:
            SkillTransfer: 更新后的迁移记录
        """
        if transfer_id not in self.transfers:
            raise ValueError(f"Transfer not found: {transfer_id}")

        transfer = self.transfers[transfer_id]

        # 模拟迁移执行
        if transfer.prerequisites_met:
            success_probability = transfer.transfer_score
        else:
            success_probability = transfer.transfer_score * 0.5

        # 考虑执行上下文
        if execution_context:
            support_level = execution_context.get("support_level", 0.5)
            success_probability = min(1.0, success_probability + support_level * 0.2)

        transfer.success = success_probability > 0.5

        if transfer.success:
            self.successful_transfers += 1

        logger.info(f"Transfer executed: {transfer_id}, success={transfer.success}")
        return transfer

    def get_transfer_stats(self) -> Dict[str, Any]:
        """获取迁移统计"""
        if not self.transfers:
            return {"total": 0, "success_rate": 0.0}

        by_type: Dict[str, List[SkillTransfer]] = defaultdict(list)
        for t in self.transfers.values():
            by_type[t.transfer_type.value].append(t)

        return {
            "total": len(self.transfers),
            "successful": self.successful_transfers,
            "success_rate": self.successful_transfers / len(self.transfers),
            "avg_transfer_score": sum(t.transfer_score for t in self.transfers.values()) / len(self.transfers),
            "by_type": {t: len(ts) for t, ts in by_type.items()},
            "avg_adaptation_difficulty": sum(t.adaptation_difficulty for t in self.transfers.values()) / len(self.transfers)
        }

    # ========== 跨领域应用 ==========

    def apply_cross_domain(self, source_domain: str, target_domain: str,
                          application_description: str,
                          approach: str = "") -> CrossDomainApplication:
        """
        跨领域应用

        Args:
            source_domain: 源领域
            target_domain: 目标领域
            application_description: 应用描述
            approach: 采用的方法

        Returns:
            CrossDomainApplication: 应用记录
        """
        self.total_applications += 1

        # 评估应用效果
        domain_similarity = self.calculate_domain_similarity(source_domain, target_domain)

        # 查找相关映射
        mappings = self.find_mappings(source_domain, target_domain)
        mapping_support = len(mappings) > 0

        # 计算预期效果
        if mapping_support:
            expected_effectiveness = min(1.0, domain_similarity + 0.2)
        else:
            expected_effectiveness = domain_similarity * 0.7

        application = CrossDomainApplication(
            source_domain=source_domain,
            target_domain=target_domain,
            application_description=application_description,
            approach_used=approach or "Direct application",
            effectiveness=expected_effectiveness,
            lessons_learned=[]
        )

        self.applications[application.application_id] = application
        self.application_history.append(application.application_id)

        logger.info(f"Cross-domain application: {source_domain} -> {target_domain}")
        return application

    def evaluate_application(self, application_id: str,
                            actual_effectiveness: float,
                            outcome: str = "",
                            lessons: Optional[List[str]] = None) -> Optional[CrossDomainApplication]:
        """
        评估跨领域应用

        Args:
            application_id: 应用ID
            actual_effectiveness: 实际效果
            outcome: 结果描述
            lessons: 经验教训

        Returns:
            Optional[CrossDomainApplication]: 更新后的应用记录
        """
        if application_id not in self.applications:
            return None

        application = self.applications[application_id]
        application.effectiveness = actual_effectiveness
        application.outcome = outcome
        if lessons:
            application.lessons_learned.extend(lessons)

        logger.info(f"Application evaluated: {application_id}, effectiveness={actual_effectiveness:.2f}")
        return application

    def get_successful_applications(self, min_effectiveness: float = 0.6) -> List[CrossDomainApplication]:
        """获取成功的应用"""
        return [
            app for app in self.applications.values()
            if app.effectiveness >= min_effectiveness
        ]

    # ========== 迁移效果监控 ==========

    def start_monitoring(self, transfer_id: str,
                        expected_metric: float = 0.7) -> TransferMonitor:
        """
        开始监控迁移效果

        Args:
            transfer_id: 迁移ID
            expected_metric: 预期指标

        Returns:
            TransferMonitor: 监控器
        """
        monitor = TransferMonitor(
            transfer_id=transfer_id,
            expected_metric=expected_metric
        )

        self.monitors[monitor.monitor_id] = monitor
        self.active_monitors.add(monitor.monitor_id)

        logger.info(f"Started monitoring transfer: {transfer_id}")
        return monitor

    def update_monitor(self, monitor_id: str,
                      performance_metric: float,
                      check_point: str = "") -> Optional[TransferMonitor]:
        """
        更新监控状态

        Args:
            monitor_id: 监控器ID
            performance_metric: 性能指标
            check_point: 检查点

        Returns:
            Optional[TransferMonitor]: 更新后的监控器
        """
        if monitor_id not in self.monitors:
            return None

        monitor = self.monitors[monitor_id]
        monitor.performance_metric = performance_metric
        monitor.check_point = check_point
        monitor.deviation = performance_metric - monitor.expected_metric

        # 确定状态
        if performance_metric >= monitor.expected_metric * 1.1:
            monitor.status = "exceeded"
        elif performance_metric >= monitor.expected_metric * 0.9:
            monitor.status = "on_track"
        elif performance_metric >= monitor.expected_metric * 0.6:
            monitor.status = "at_risk"
        else:
            monitor.status = "failed"

        logger.debug(f"Monitor updated: {monitor_id}, status={monitor.status}")
        return monitor

    def get_monitor_summary(self, transfer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取监控摘要

        Args:
            transfer_id: 迁移ID过滤

        Returns:
            Dict[str, Any]: 监控摘要
        """
        monitors_to_check = self.monitors.values()
        if transfer_id:
            monitors_to_check = [m for m in monitors_to_check if m.transfer_id == transfer_id]

        status_counts: Dict[str, int] = defaultdict(int)
        for monitor in monitors_to_check:
            status_counts[monitor.status] += 1

        return {
            "total_monitors": len(list(monitors_to_check)),
            "active_monitors": len(self.active_monitors),
            "status_distribution": dict(status_counts),
            "avg_deviation": sum(m.deviation for m in monitors_to_check) / max(len(list(monitors_to_check)), 1)
        }

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_domains": self.total_domains,
            "total_mappings": self.total_mappings,
            "total_transfers": self.total_transfers,
            "total_applications": self.total_applications,
            "successful_transfers": self.successful_transfers,
            "transfer_success_rate": self.successful_transfers / max(self.total_transfers, 1),
            "active_monitors": len(self.active_monitors),
            "domain_types": len(self.domain_type_index),
            "transfer_stats": self.get_transfer_stats(),
            "successful_applications": len(self.get_successful_applications()),
        }

    def reset(self) -> None:
        """重置"""
        self.domains.clear()
        self.domain_by_name.clear()
        self.domain_type_index.clear()
        self.mappings.clear()
        self.domain_pair_mappings.clear()
        self.transfers.clear()
        self.transfer_history.clear()
        self.applications.clear()
        self.application_history.clear()
        self.monitors.clear()
        self.active_monitors.clear()
        self.total_domains = 0
        self.total_mappings = 0
        self.total_transfers = 0
        self.total_applications = 0
        self.successful_transfers = 0
        logger.info("TransferLearningMechanism reset")
