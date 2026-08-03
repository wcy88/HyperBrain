"""
错误分析模块 (Error Analysis Module)

分析失败原因，进行错误分类和归档，执行根因分析，总结经验教训，
生成错误模式识别和预防策略。

功能：
1. 分析失败原因
2. 错误分类和归档
3. 根因分析
4. 总结经验教训
5. 生成错误模式识别
6. 预防策略生成
"""

import uuid
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from collections import defaultdict, Counter

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("evolution.error_analysis")


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    CRITICAL = "critical"       # 严重
    HIGH = "high"               # 高
    MEDIUM = "medium"           # 中
    LOW = "low"                 # 低
    TRIVIAL = "trivial"         # 轻微


class ErrorCategory(str, Enum):
    """错误分类"""
    COGNITIVE = "cognitive"         # 认知错误
    MEMORY = "memory"               # 记忆错误
    LEARNING = "learning"           # 学习错误
    DECISION = "decision"           # 决策错误
    EXECUTION = "execution"         # 执行错误
    PERCEPTION = "perception"       # 感知错误
    COMMUNICATION = "communication" # 沟通错误
    SYSTEM = "system"               # 系统错误
    UNKNOWN = "unknown"             # 未知错误


class ErrorRecord(BaseModel):
    """错误记录"""
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., description="错误描述")
    category: ErrorCategory = Field(default=ErrorCategory.UNKNOWN)
    severity: ErrorSeverity = Field(default=ErrorSeverity.MEDIUM)
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict, description="错误上下文")
    stack_trace: Optional[str] = Field(default=None, description="堆栈跟踪")
    root_cause: Optional[str] = Field(default=None, description="根因")
    solution: Optional[str] = Field(default=None, description="解决方案")
    resolved: bool = Field(default=False)
    resolution_time: Optional[datetime] = Field(default=None)
    recurrence_count: int = Field(default=1, ge=1)
    related_errors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    @field_validator("recurrence_count")
    @classmethod
    def validate_recurrence(cls, v: int) -> int:
        return max(1, v)


class ErrorPattern(BaseModel):
    """错误模式"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="模式名称")
    description: str = Field(..., description="模式描述")
    category: ErrorCategory = Field(...)
    matching_keywords: List[str] = Field(default_factory=list)
    frequency: int = Field(default=1, ge=1)
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    affected_components: List[str] = Field(default_factory=list)
    avg_severity: float = Field(default=0.5, ge=0.0, le=1.0)
    prevention_strategy: Optional[str] = Field(default=None)

    @field_validator("avg_severity")
    @classmethod
    def validate_severity(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class RootCauseAnalysis(BaseModel):
    """根因分析结果"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_id: str = Field(...)
    root_causes: List[str] = Field(default_factory=list)
    contributing_factors: List[str] = Field(default_factory=list)
    category: ErrorCategory = Field(...)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    depth: int = Field(default=1, ge=1, description="分析深度")
    timestamp: datetime = Field(default_factory=datetime.now)
    methodology: str = Field(default="5_whys", description="分析方法")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LessonLearned(BaseModel):
    """经验教训"""
    lesson_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    related_errors: List[str] = Field(default_factory=list)
    category: ErrorCategory = Field(...)
    key_takeaway: str = Field(..., description="核心要点")
    preventive_actions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    applicability: float = Field(default=0.8, ge=0.0, le=1.0)

    @field_validator("applicability")
    @classmethod
    def validate_applicability(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class PreventionStrategy(BaseModel):
    """预防策略"""
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    target_patterns: List[str] = Field(default_factory=list)
    target_categories: List[ErrorCategory] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    effectiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    implementation_cost: float = Field(default=0.5, ge=0.0, le=1.0)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    applied_count: int = Field(default=0, ge=0)
    success_count: int = Field(default=0, ge=0)

    @field_validator("effectiveness", "implementation_cost", "priority")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ErrorAnalysisReport(BaseModel):
    """错误分析报告"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    total_errors: int = Field(default=0)
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    top_patterns: List[ErrorPattern] = Field(default_factory=list)
    new_lessons: List[LessonLearned] = Field(default_factory=list)
    recommended_strategies: List[PreventionStrategy] = Field(default_factory=list)
    summary: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorAnalysisConfig(BaseModel):
    """错误分析配置"""
    max_error_history: int = Field(default=1000)
    max_patterns: int = Field(default=100)
    max_lessons: int = Field(default=500)
    pattern_similarity_threshold: float = Field(default=0.7)
    auto_categorize: bool = Field(default=True)
    auto_root_cause: bool = Field(default=True)
    enable_pattern_recognition: bool = Field(default=True)
    min_pattern_frequency: int = Field(default=3)


class ErrorAnalyzer:
    """
    错误分析系统

    分析失败原因，进行错误分类和归档，执行根因分析，
    总结经验教训，生成错误模式识别和预防策略。

    Attributes:
        config: 分析配置
        error_history: 错误历史记录
        error_patterns: 识别的错误模式
        lessons_learned: 经验教训库
        prevention_strategies: 预防策略库
    """

    def __init__(self, config: Optional[ErrorAnalysisConfig] = None):
        self.config = config or ErrorAnalysisConfig()
        self._error_history: List[ErrorRecord] = []
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._lessons_learned: List[LessonLearned] = []
        self._prevention_strategies: Dict[str, PreventionStrategy] = {}
        self._category_keywords: Dict[ErrorCategory, List[str]] = {
            ErrorCategory.COGNITIVE: [
                "推理", "逻辑", "思考", "分析", "推断", "演绎", "归纳",
                "reasoning", "logic", "thinking", "analysis", "inference"
            ],
            ErrorCategory.MEMORY: [
                "记忆", "遗忘", "检索", "存储", "回忆", "remember",
                "memory", "forget", "retrieval", "storage", "recall"
            ],
            ErrorCategory.LEARNING: [
                "学习", "训练", "适应", "泛化", "过拟合", "underfit",
                "learning", "training", "adaptation", "generalization", "overfit"
            ],
            ErrorCategory.DECISION: [
                "决策", "选择", "判断", "评估", "权衡", "decision",
                "choice", "judgment", "evaluation", "trade-off"
            ],
            ErrorCategory.EXECUTION: [
                "执行", "操作", "运行", "调用", "超时", "execute",
                "execution", "operation", "run", "invoke", "timeout"
            ],
            ErrorCategory.PERCEPTION: [
                "感知", "识别", "检测", "输入", "解析", "perception",
                "recognition", "detection", "input", "parse"
            ],
            ErrorCategory.COMMUNICATION: [
                "通信", "连接", "传输", "协议", "接口", "communication",
                "connection", "transmission", "protocol", "interface"
            ],
            ErrorCategory.SYSTEM: [
                "系统", "资源", "内存", "CPU", "磁盘", "system",
                "resource", "memory", "disk", "crash"
            ],
        }
        logger.info("ErrorAnalyzer initialized")

    # ========== 错误记录接口 ==========

    def record_error(
        self,
        description: str,
        category: Optional[ErrorCategory] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ErrorRecord:
        """
        记录错误

        Args:
            description: 错误描述
            category: 错误分类（None则自动分类）
            severity: 严重程度
            context: 上下文
            stack_trace: 堆栈跟踪
            tags: 标签

        Returns:
            ErrorRecord: 错误记录
        """
        # 自动分类
        if category is None and self.config.auto_categorize:
            category = self._auto_categorize(description)

        # 检查是否是已知错误的重复
        existing = self._find_similar_error(description)
        if existing:
            existing.recurrence_count += 1
            existing.timestamp = datetime.now()
            logger.debug(f"Error recurrence detected: {existing.error_id}")
            return existing

        record = ErrorRecord(
            description=description,
            category=category or ErrorCategory.UNKNOWN,
            severity=severity,
            context=context or {},
            stack_trace=stack_trace,
            tags=tags or []
        )

        self._error_history.append(record)

        # 限制历史大小
        if len(self._error_history) > self.config.max_error_history:
            self._error_history = self._error_history[-self.config.max_error_history:]

        # 自动识别模式
        if self.config.enable_pattern_recognition:
            self._update_patterns(record)

        logger.info(f"Recorded error: {record.error_id}, category={record.category.value}")
        return record

    def resolve_error(
        self,
        error_id: str,
        solution: str,
        root_cause: Optional[str] = None
    ) -> bool:
        """
        标记错误已解决

        Args:
            error_id: 错误ID
            solution: 解决方案
            root_cause: 根因（可选）

        Returns:
            bool: 是否成功
        """
        for error in self._error_history:
            if error.error_id == error_id:
                error.resolved = True
                error.solution = solution
                error.resolution_time = datetime.now()
                if root_cause:
                    error.root_cause = root_cause

                # 生成经验教训
                self._generate_lesson(error)

                logger.info(f"Error resolved: {error_id}")
                return True
        return False

    # ========== 根因分析 ==========

    def analyze_root_cause(
        self,
        error_id: str,
        depth: int = 3,
        methodology: str = "5_whys"
    ) -> Optional[RootCauseAnalysis]:
        """
        执行根因分析

        Args:
            error_id: 错误ID
            depth: 分析深度
            methodology: 分析方法

        Returns:
            Optional[RootCauseAnalysis]: 分析结果
        """
        error = self._find_error_by_id(error_id)
        if not error:
            return None

        root_causes = []
        contributing_factors = []

        if methodology == "5_whys":
            root_causes, contributing_factors = self._five_why_analysis(error, depth)
        elif methodology == "fishbone":
            root_causes, contributing_factors = self._fishbone_analysis(error)
        else:
            root_causes, contributing_factors = self._basic_analysis(error)

        # 更新错误记录
        if root_causes:
            error.root_cause = root_causes[0]

        analysis = RootCauseAnalysis(
            error_id=error_id,
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            category=error.category,
            confidence=min(0.9, 0.5 + len(root_causes) * 0.1),
            depth=depth,
            methodology=methodology
        )

        logger.info(f"Root cause analysis completed for {error_id}")
        return analysis

    def _five_why_analysis(
        self,
        error: ErrorRecord,
        depth: int
    ) -> Tuple[List[str], List[str]]:
        """5 Whys 分析"""
        root_causes = []
        contributing_factors = []

        description = error.description.lower()
        context = str(error.context).lower()

        # 基于关键词的启发式分析
        cause_chains = {
            ErrorCategory.COGNITIVE: [
                "推理过程存在逻辑漏洞",
                "前提假设不完整或不正确",
                "知识表示方式不当",
                "缺乏必要的背景知识",
                "认知负荷过高导致判断失误"
            ],
            ErrorCategory.MEMORY: [
                "记忆检索失败",
                "记忆编码不完整",
                "记忆间关联缺失",
                "记忆衰减或干扰",
                "工作记忆容量不足"
            ],
            ErrorCategory.LEARNING: [
                "训练数据不足或有偏差",
                "学习率设置不当",
                "特征表示不充分",
                "模型复杂度不匹配",
                "缺乏足够的迭代次数"
            ],
            ErrorCategory.DECISION: [
                "信息收集不充分",
                "评估标准不明确",
                "备选方案考虑不全",
                "风险评估缺失",
                "决策框架选择不当"
            ],
            ErrorCategory.EXECUTION: [
                "执行环境异常",
                "资源不足",
                "时序或并发问题",
                "输入验证缺失",
                "异常处理不完善"
            ],
            ErrorCategory.PERCEPTION: [
                "输入数据质量差",
                "特征提取不充分",
                "模式识别阈值不当",
                "感知器参数未校准",
                "多模态融合失败"
            ],
            ErrorCategory.SYSTEM: [
                "系统资源耗尽",
                "依赖服务不可用",
                "配置参数不当",
                "版本兼容性问题",
                "基础设施故障"
            ],
        }

        chain = cause_chains.get(error.category, ["未知原因"])
        root_causes = chain[:min(depth, len(chain))]

        # 从上下文中提取贡献因素
        if "timeout" in description or "timeout" in context:
            contributing_factors.append("超时设置")
        if "memory" in description or "memory" in context:
            contributing_factors.append("内存限制")
        if "network" in description or "connection" in context:
            contributing_factors.append("网络连接")

        if not contributing_factors:
            contributing_factors.append("上下文信息不足")

        return root_causes, contributing_factors

    def _fishbone_analysis(
        self,
        error: ErrorRecord
    ) -> Tuple[List[str], List[str]]:
        """鱼骨图分析"""
        categories = ["人", "机", "料", "法", "环"]
        root_causes = []
        contributing_factors = []

        # 简化的鱼骨图分析
        if error.category in [ErrorCategory.COGNITIVE, ErrorCategory.DECISION]:
            root_causes.append("认知/决策流程缺陷")
            contributing_factors.extend(["知识不足", "经验欠缺", "注意力分散"])
        elif error.category in [ErrorCategory.SYSTEM, ErrorCategory.EXECUTION]:
            root_causes.append("系统/执行环境问题")
            contributing_factors.extend(["资源限制", "配置错误", "外部依赖"])
        else:
            root_causes.append(f"{error.category.value} 领域问题")
            contributing_factors.extend(["流程缺陷", "工具限制", "沟通不畅"])

        return root_causes, contributing_factors

    def _basic_analysis(
        self,
        error: ErrorRecord
    ) -> Tuple[List[str], List[str]]:
        """基础分析"""
        root_causes = [f"{error.category.value} 层面的问题"]
        contributing_factors = ["需要进一步调查"]
        return root_causes, contributing_factors

    # ========== 错误模式识别 ==========

    def recognize_patterns(self) -> List[ErrorPattern]:
        """
        识别错误模式

        Returns:
            List[ErrorPattern]: 识别的模式列表
        """
        # 按描述相似性分组
        error_groups = self._group_similar_errors()

        new_patterns = []
        for group in error_groups:
            if len(group) >= self.config.min_pattern_frequency:
                pattern = self._create_pattern_from_group(group)
                if pattern.pattern_id not in self._error_patterns:
                    self._error_patterns[pattern.pattern_id] = pattern
                    new_patterns.append(pattern)
                else:
                    # 更新现有模式
                    existing = self._error_patterns[pattern.pattern_id]
                    existing.frequency += len(group)
                    existing.last_seen = datetime.now()

        logger.info(f"Recognized {len(new_patterns)} new error patterns")
        return new_patterns

    def _group_similar_errors(self) -> List[List[ErrorRecord]]:
        """将相似错误分组"""
        groups: List[List[ErrorRecord]] = []
        ungrouped = list(self._error_history)

        while ungrouped:
            current = ungrouped.pop(0)
            group = [current]

            similar = [
                e for e in ungrouped
                if self._calculate_similarity(current, e) > self.config.pattern_similarity_threshold
            ]

            for s in similar:
                group.append(s)
                ungrouped.remove(s)

            groups.append(group)

        return groups

    def _calculate_similarity(self, e1: ErrorRecord, e2: ErrorRecord) -> float:
        """计算两个错误的相似度"""
        # 基于分类和关键词的相似度
        score = 0.0

        # 分类相同
        if e1.category == e2.category:
            score += 0.3

        # 严重程度相同
        if e1.severity == e2.severity:
            score += 0.1

        # 描述关键词重叠
        words1 = set(e1.description.lower().split())
        words2 = set(e2.description.lower().split())
        if words1 and words2:
            overlap = len(words1 & words2) / len(words1 | words2)
            score += overlap * 0.5

        # 标签重叠
        tags1 = set(e1.tags)
        tags2 = set(e2.tags)
        if tags1 and tags2:
            tag_overlap = len(tags1 & tags2) / len(tags1 | tags2)
            score += tag_overlap * 0.2

        # 如果描述完全相同，提高相似度
        if e1.description == e2.description:
            score = max(score, 0.95)

        return score

    def _create_pattern_from_group(self, group: List[ErrorRecord]) -> ErrorPattern:
        """从错误组创建模式"""
        # 提取共同关键词
        all_words = []
        for error in group:
            all_words.extend(error.description.lower().split())

        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(5) if count > 1]

        # 确定影响组件
        components = set()
        for error in group:
            if "component" in error.context:
                components.add(str(error.context["component"]))

        # 计算平均严重程度
        severity_scores = {
            ErrorSeverity.CRITICAL: 1.0,
            ErrorSeverity.HIGH: 0.8,
            ErrorSeverity.MEDIUM: 0.5,
            ErrorSeverity.LOW: 0.3,
            ErrorSeverity.TRIVIAL: 0.1
        }
        avg_severity = sum(
            severity_scores.get(e.severity, 0.5) for e in group
        ) / len(group)

        return ErrorPattern(
            name=f"Pattern_{group[0].category.value}_{len(self._error_patterns)}",
            description=f"Recurring {group[0].category.value} errors: {', '.join(common_words[:3])}",
            category=group[0].category,
            matching_keywords=common_words,
            frequency=len(group),
            first_seen=min(e.timestamp for e in group),
            last_seen=max(e.timestamp for e in group),
            affected_components=list(components),
            avg_severity=avg_severity
        )

    def _update_patterns(self, error: ErrorRecord) -> None:
        """更新错误模式（增量）"""
        for pattern in self._error_patterns.values():
            if self._matches_pattern(error, pattern):
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                return

    def _matches_pattern(self, error: ErrorRecord, pattern: ErrorPattern) -> bool:
        """检查错误是否匹配模式"""
        if error.category != pattern.category:
            return False

        desc_lower = error.description.lower()
        keyword_matches = sum(1 for kw in pattern.matching_keywords if kw in desc_lower)

        return keyword_matches >= len(pattern.matching_keywords) * 0.5

    # ========== 经验教训 ==========

    def _generate_lesson(self, error: ErrorRecord) -> Optional[LessonLearned]:
        """从已解决错误生成经验教训"""
        if not error.solution or not error.root_cause:
            return None

        lesson = LessonLearned(
            title=f"从 {error.category.value} 错误中学到的经验",
            description=f"错误: {error.description}\n根因: {error.root_cause}\n解决: {error.solution}",
            related_errors=[error.error_id],
            category=error.category,
            key_takeaway=f"预防 {error.root_cause} 的关键是 {error.solution[:50]}...",
            preventive_actions=self._generate_preventive_actions(error)
        )

        self._lessons_learned.append(lesson)

        # 限制大小
        if len(self._lessons_learned) > self.config.max_lessons:
            self._lessons_learned = self._lessons_learned[-self.config.max_lessons:]

        logger.info(f"Generated lesson: {lesson.lesson_id}")
        return lesson

    def _generate_preventive_actions(self, error: ErrorRecord) -> List[str]:
        """生成预防行动"""
        actions = []

        category_actions = {
            ErrorCategory.COGNITIVE: [
                "建立推理验证机制",
                "增加中间结果检查",
                "引入多角度验证"
            ],
            ErrorCategory.MEMORY: [
                "定期巩固重要记忆",
                "建立记忆关联网络",
                "实施记忆质量检查"
            ],
            ErrorCategory.LEARNING: [
                "增加训练数据多样性",
                "实施交叉验证",
                "监控学习曲线"
            ],
            ErrorCategory.DECISION: [
                "建立决策审查流程",
                "引入红队评估",
                "记录决策依据"
            ],
            ErrorCategory.EXECUTION: [
                "增加输入验证",
                "实施重试机制",
                "完善异常处理"
            ],
            ErrorCategory.PERCEPTION: [
                "校准感知参数",
                "增加数据预处理",
                "实施多传感器融合"
            ],
            ErrorCategory.SYSTEM: [
                "监控资源使用",
                "建立健康检查",
                "实施降级策略"
            ],
        }

        actions.extend(category_actions.get(error.category, ["建立监控和告警"]))
        return actions

    # ========== 预防策略 ==========

    def generate_prevention_strategies(self) -> List[PreventionStrategy]:
        """
        生成预防策略

        Returns:
            List[PreventionStrategy]: 策略列表
        """
        strategies = []

        # 基于错误模式生成策略
        for pattern in self._error_patterns.values():
            if pattern.frequency >= self.config.min_pattern_frequency:
                strategy = self._create_strategy_for_pattern(pattern)
                if strategy.strategy_id not in self._prevention_strategies:
                    self._prevention_strategies[strategy.strategy_id] = strategy
                    strategies.append(strategy)

        # 基于经验教训生成策略
        for lesson in self._lessons_learned[-20:]:
            strategy = self._create_strategy_for_lesson(lesson)
            if strategy.strategy_id not in self._prevention_strategies:
                self._prevention_strategies[strategy.strategy_id] = strategy
                strategies.append(strategy)

        logger.info(f"Generated {len(strategies)} prevention strategies")
        return strategies

    def _create_strategy_for_pattern(self, pattern: ErrorPattern) -> PreventionStrategy:
        """为错误模式创建策略"""
        actions = [
            f"监控 {pattern.category.value} 相关的异常",
            f"建立 {', '.join(pattern.matching_keywords[:2])} 的检测规则",
            "实施早期预警机制"
        ]

        return PreventionStrategy(
            name=f"预防 {pattern.name}",
            description=f"针对频繁出现的 {pattern.category.value} 错误的预防策略",
            target_patterns=[pattern.pattern_id],
            target_categories=[pattern.category],
            actions=actions,
            effectiveness=0.6,
            implementation_cost=0.4,
            priority=pattern.avg_severity * min(1.0, pattern.frequency / 10)
        )

    def _create_strategy_for_lesson(self, lesson: LessonLearned) -> PreventionStrategy:
        """为经验教训创建策略"""
        return PreventionStrategy(
            name=f"基于 {lesson.lesson_id[:8]} 的预防",
            description=lesson.key_takeaway,
            target_categories=[lesson.category],
            actions=lesson.preventive_actions,
            effectiveness=lesson.applicability,
            implementation_cost=0.5,
            priority=lesson.applicability * 0.7
        )

    def apply_strategy(self, strategy_id: str, success: bool = True) -> bool:
        """
        记录策略应用结果

        Args:
            strategy_id: 策略ID
            success: 是否成功

        Returns:
            bool: 是否找到策略
        """
        if strategy_id not in self._prevention_strategies:
            return False

        strategy = self._prevention_strategies[strategy_id]
        strategy.applied_count += 1
        if success:
            strategy.success_count += 1

        # 更新有效性
        if strategy.applied_count > 0:
            strategy.effectiveness = strategy.success_count / strategy.applied_count

        return True

    # ========== 自动分类 ==========

    def _auto_categorize(self, description: str) -> ErrorCategory:
        """自动分类错误"""
        desc_lower = description.lower()

        scores = {}
        for category, keywords in self._category_keywords.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            scores[category] = score

        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category

        return ErrorCategory.UNKNOWN

    def _find_similar_error(self, description: str) -> Optional[ErrorRecord]:
        """查找相似错误"""
        desc_lower = description.lower()
        words = set(desc_lower.split())

        for error in reversed(self._error_history):
            if (datetime.now() - error.timestamp).days > 7:
                continue

            # 完全相同的描述直接返回
            if error.description.lower() == desc_lower:
                return error

            error_words = set(error.description.lower().split())
            if words and error_words:
                overlap = len(words & error_words) / len(words | error_words)
                if overlap > 0.8:
                    return error

        return None

    def _find_error_by_id(self, error_id: str) -> Optional[ErrorRecord]:
        """通过ID查找错误"""
        for error in self._error_history:
            if error.error_id == error_id:
                return error
        return None

    # ========== 报告生成 ==========

    def generate_report(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> ErrorAnalysisReport:
        """
        生成错误分析报告

        Args:
            period_start: 开始时间
            period_end: 结束时间

        Returns:
            ErrorAnalysisReport: 分析报告
        """
        if period_end is None:
            period_end = datetime.now()
        if period_start is None:
            period_start = period_end - timedelta(days=7)

        # 筛选期间内的错误
        period_errors = [
            e for e in self._error_history
            if period_start <= e.timestamp <= period_end
        ]

        # 分类统计
        category_dist = Counter(e.category.value for e in period_errors)
        severity_dist = Counter(e.severity.value for e in period_errors)

        # 获取高频模式
        top_patterns = sorted(
            self._error_patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )[:10]

        # 获取新经验教训
        new_lessons = [
            l for l in self._lessons_learned
            if period_start <= l.timestamp <= period_end
        ]

        # 推荐策略
        recommended = sorted(
            self._prevention_strategies.values(),
            key=lambda s: s.priority,
            reverse=True
        )[:5]

        # 生成总结
        total = len(period_errors)
        resolved = len([e for e in period_errors if e.resolved])
        summary = (
            f"期间共发生 {total} 个错误，"
            f"已解决 {resolved} 个 ({resolved/max(total,1)*100:.1f}%)。"
            f"主要问题类别：{category_dist.most_common(1)[0][0] if category_dist else '无'}。"
            f"识别出 {len(top_patterns)} 个错误模式。"
        )

        return ErrorAnalysisReport(
            period_start=period_start,
            period_end=period_end,
            total_errors=total,
            category_distribution=dict(category_dist),
            severity_distribution=dict(severity_dist),
            top_patterns=top_patterns,
            new_lessons=new_lessons,
            recommended_strategies=recommended,
            summary=summary
        )

    # ========== 查询接口 ==========

    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._error_history)
        if total == 0:
            return {"total": 0}

        resolved = len([e for e in self._error_history if e.resolved])
        category_dist = Counter(e.category.value for e in self._error_history)
        severity_dist = Counter(e.severity.value for e in self._error_history)

        return {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": resolved / total,
            "category_distribution": dict(category_dist),
            "severity_distribution": dict(severity_dist),
            "total_patterns": len(self._error_patterns),
            "total_lessons": len(self._lessons_learned),
            "total_strategies": len(self._prevention_strategies)
        }

    def get_patterns(self, category: Optional[ErrorCategory] = None) -> List[ErrorPattern]:
        """
        获取错误模式

        Args:
            category: 过滤分类

        Returns:
            List[ErrorPattern]: 模式列表
        """
        patterns = list(self._error_patterns.values())
        if category:
            patterns = [p for p in patterns if p.category == category]
        return sorted(patterns, key=lambda p: p.frequency, reverse=True)

    def get_lessons(self, category: Optional[ErrorCategory] = None) -> List[LessonLearned]:
        """
        获取经验教训

        Args:
            category: 过滤分类

        Returns:
            List[LessonLearned]: 经验教训列表
        """
        lessons = self._lessons_learned
        if category:
            lessons = [l for l in lessons if l.category == category]
        return lessons

    def get_strategies(self) -> List[PreventionStrategy]:
        """
        获取预防策略

        Returns:
            List[PreventionStrategy]: 策略列表
        """
        return sorted(
            self._prevention_strategies.values(),
            key=lambda s: s.priority,
            reverse=True
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取完整统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "errors": self.get_error_stats(),
            "patterns": len(self._error_patterns),
            "lessons": len(self._lessons_learned),
            "strategies": len(self._prevention_strategies)
        }

    def reset(self) -> None:
        """重置所有状态"""
        self._error_history.clear()
        self._error_patterns.clear()
        self._lessons_learned.clear()
        self._prevention_strategies.clear()
        logger.info("ErrorAnalyzer reset")
