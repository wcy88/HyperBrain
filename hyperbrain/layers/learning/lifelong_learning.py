"""
终身学习机制 (Lifelong Learning Mechanism)

实现持续学习、知识整合和灾难性遗忘防止：
- 持续学习：从所有交互中学习
- 知识整合：新旧知识关联
- 防止灾难性遗忘
- 学习进度跟踪
- 学习效果评估
"""

import uuid
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("learning.lifelong")


class LearningEvent(BaseModel):
    """学习事件"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(...)  # exploration, instruction, experience, reflection
    content: str = Field(default="")
    source_engine: str = Field(default="")  # infant, child, adult
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("importance")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeSnapshot(BaseModel):
    """知识快照"""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    knowledge_count: int = Field(default=0)
    concept_count: int = Field(default=0)
    vocabulary_count: int = Field(default=0)
    pattern_count: int = Field(default=0)
    total_learning_events: int = Field(default=0)
    avg_confidence: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningProgress(BaseModel):
    """学习进度"""
    progress_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = Field(default="general")
    start_time: datetime = Field(default_factory=datetime.now)
    current_level: float = Field(default=0.0, ge=0.0, le=1.0)
    target_level: float = Field(default=1.0, ge=0.0, le=1.0)
    milestones_achieved: List[str] = Field(default_factory=list)
    next_milestone: Optional[str] = Field(default=None)
    estimated_completion: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("current_level", "target_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ForgettingPreventionRecord(BaseModel):
    """遗忘防止记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = Field(...)
    review_count: int = Field(default=0, ge=0)
    last_reviewed: datetime = Field(default_factory=datetime.now)
    stability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    next_review_due: datetime = Field(default_factory=datetime.now)
    review_interval: float = Field(default=3600.0)  # seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("stability_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class LearningEffectiveness(BaseModel):
    """学习效果评估"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime = Field(default_factory=datetime.now)
    period_end: datetime = Field(default_factory=datetime.now)
    events_count: int = Field(default=0)
    knowledge_gained: int = Field(default=0)
    retention_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    application_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("retention_rate", "application_success_rate", "overall_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class LifelongLearningConfig:
    """终身学习配置"""
    max_event_history: int = 10000
    snapshot_interval: float = 86400.0  # 1 day
    review_interval_base: float = 3600.0  # 1 hour
    stability_threshold: float = 0.3
    forgetting_prevention_enabled: bool = True
    consolidation_interval: float = 43200.0  # 12 hours
    progress_evaluation_interval: float = 604800.0  # 1 week


class LifelongLearningMechanism:
    """
    终身学习机制

    模拟人类终身学习的特点：
    1. 持续学习：不断从交互中获取新知识
    2. 知识整合：将新知识与已有知识关联
    3. 遗忘防止：通过复习保持知识
    4. 进度跟踪：监控学习进展
    5. 效果评估：评估学习成效

    Attributes:
        config: 配置
        event_history: 学习事件历史
        knowledge_snapshots: 知识快照
        progress_tracking: 进度跟踪
        forgetting_prevention: 遗忘防止记录
    """

    def __init__(self, config: Optional[LifelongLearningConfig] = None):
        self.config = config or LifelongLearningConfig()

        # 学习事件历史
        self.event_history: deque = deque(maxlen=self.config.max_event_history)
        self.event_index: Dict[str, List[str]] = defaultdict(list)

        # 知识快照
        self.knowledge_snapshots: List[KnowledgeSnapshot] = []
        self.last_snapshot_time: float = time.time()

        # 学习进度
        self.progress_tracking: Dict[str, LearningProgress] = {}

        # 遗忘防止
        self.forgetting_records: Dict[str, ForgettingPreventionRecord] = {}
        self.review_queue: List[str] = []

        # 效果评估
        self.effectiveness_assessments: List[LearningEffectiveness] = []

        # 知识整合
        self.knowledge_integrations: List[Dict[str, Any]] = []
        self.integrated_knowledge_ids: Set[str] = set()

        # 统计
        self.total_events: int = 0
        self.total_snapshots: int = 0
        self.total_reviews: int = 0
        self.total_assessments: int = 0

        logger.info("LifelongLearningMechanism initialized")

    # ========== 持续学习 ==========

    def record_learning_event(self, event_type: str, content: str,
                              source_engine: str = "",
                              importance: float = 0.5,
                              metadata: Optional[Dict[str, Any]] = None) -> LearningEvent:
        """
        记录学习事件

        Args:
            event_type: 事件类型
            content: 内容
            source_engine: 来源引擎
            importance: 重要性
            metadata: 元数据

        Returns:
            LearningEvent: 学习事件
        """
        self.total_events += 1

        event = LearningEvent(
            event_type=event_type,
            content=content,
            source_engine=source_engine,
            importance=importance,
            metadata=metadata or {}
        )

        self.event_history.append(event)
        self.event_index[event_type].append(event.event_id)

        # 检查是否需要快照
        self._check_snapshot()

        logger.debug(f"Learning event: {event_type} from {source_engine}, importance={importance:.2f}")
        return event

    def get_recent_events(self, event_type: Optional[str] = None,
                          limit: int = 100) -> List[LearningEvent]:
        """
        获取最近的学习事件

        Args:
            event_type: 事件类型过滤
            limit: 数量限制

        Returns:
            List[LearningEvent]: 事件列表
        """
        events = list(self.event_history)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_learning_rate(self, time_window: float = 86400.0) -> float:
        """
        计算学习速率

        Args:
            time_window: 时间窗口（秒）

        Returns:
            float: 学习速率（事件/天）
        """
        cutoff = datetime.now().timestamp() - time_window
        recent_events = [
            e for e in self.event_history
            if e.timestamp.timestamp() > cutoff
        ]
        return len(recent_events) / (time_window / 86400.0)

    # ========== 知识整合 ==========

    def integrate_knowledge(self, new_knowledge_id: str,
                           related_knowledge_ids: List[str],
                           integration_type: str = "association") -> Dict[str, Any]:
        """
        整合新知识到已有知识体系

        Args:
            new_knowledge_id: 新知识ID
            related_knowledge_ids: 相关知识ID列表
            integration_type: 整合类型

        Returns:
            Dict[str, Any]: 整合结果
        """
        integration = {
            "integration_id": str(uuid.uuid4()),
            "new_knowledge_id": new_knowledge_id,
            "related_knowledge_ids": related_knowledge_ids,
            "integration_type": integration_type,
            "timestamp": datetime.now().isoformat(),
            "strength": 0.5 + len(related_knowledge_ids) * 0.1
        }

        self.knowledge_integrations.append(integration)
        self.integrated_knowledge_ids.add(new_knowledge_id)

        # 为相关知识创建遗忘防止记录
        for knowledge_id in [new_knowledge_id] + related_knowledge_ids:
            if knowledge_id not in self.forgetting_records:
                self.forgetting_records[knowledge_id] = ForgettingPreventionRecord(
                    knowledge_id=knowledge_id,
                    review_interval=self.config.review_interval_base
                )

        logger.debug(f"Knowledge integration: {new_knowledge_id} with {len(related_knowledge_ids)} related")
        return integration

    def get_knowledge_network(self, knowledge_id: str,
                              depth: int = 2) -> Dict[str, Any]:
        """
        获取知识网络

        Args:
            knowledge_id: 知识ID
            depth: 搜索深度

        Returns:
            Dict[str, Any]: 知识网络
        """
        network = {"center": knowledge_id, "nodes": [], "links": []}
        visited = {knowledge_id}
        current_level = {knowledge_id}

        for _ in range(depth):
            next_level = set()
            for integration in self.knowledge_integrations:
                if integration["new_knowledge_id"] in current_level:
                    for related in integration["related_knowledge_ids"]:
                        if related not in visited:
                            visited.add(related)
                            next_level.add(related)
                            network["links"].append({
                                "source": integration["new_knowledge_id"],
                                "target": related,
                                "type": integration["integration_type"]
                            })
                elif any(r in current_level for r in integration["related_knowledge_ids"]):
                    if integration["new_knowledge_id"] not in visited:
                        visited.add(integration["new_knowledge_id"])
                        next_level.add(integration["new_knowledge_id"])
                        network["links"].append({
                            "source": integration["new_knowledge_id"],
                            "target": knowledge_id,
                            "type": integration["integration_type"]
                        })
            current_level = next_level
            network["nodes"].extend(list(next_level))

        return network

    # ========== 防止灾难性遗忘 ==========

    def schedule_review(self, knowledge_id: str) -> ForgettingPreventionRecord:
        """
        安排知识复习

        Args:
            knowledge_id: 知识ID

        Returns:
            ForgettingPreventionRecord: 复习记录
        """
        if knowledge_id not in self.forgetting_records:
            record = ForgettingPreventionRecord(
                knowledge_id=knowledge_id,
                review_interval=self.config.review_interval_base
            )
            self.forgetting_records[knowledge_id] = record
        else:
            record = self.forgetting_records[knowledge_id]

        # 计算下次复习时间（间隔重复）
        record.review_count += 1
        record.last_reviewed = datetime.now()

        # 间隔重复公式：间隔随复习次数增加
        interval_multiplier = 2.0 ** (record.review_count - 1)
        record.review_interval = self.config.review_interval_base * interval_multiplier
        record.next_review_due = datetime.fromtimestamp(
            time.time() + record.review_interval
        )

        # 更新稳定性
        record.stability_score = min(1.0, record.stability_score + 0.1)

        self.total_reviews += 1
        logger.debug(f"Scheduled review for {knowledge_id}, next in {record.review_interval/3600:.1f}h")
        return record

    def get_due_reviews(self) -> List[ForgettingPreventionRecord]:
        """
        获取到期的复习

        Returns:
            List[ForgettingPreventionRecord]: 到期复习列表
        """
        now = datetime.now()
        due = [
            record for record in self.forgetting_records.values()
            if record.next_review_due <= now
        ]
        return sorted(due, key=lambda r: r.next_review_due)

    def get_forgetting_risk(self, knowledge_id: str) -> float:
        """
        获取遗忘风险

        Args:
            knowledge_id: 知识ID

        Returns:
            float: 遗忘风险（0-1）
        """
        if knowledge_id not in self.forgetting_records:
            return 1.0  # 未记录的知识高风险遗忘

        record = self.forgetting_records[knowledge_id]
        time_since_review = (datetime.now() - record.last_reviewed).total_seconds()

        # 如果超过复习间隔，风险增加
        if time_since_review > record.review_interval:
            overdue_ratio = time_since_review / record.review_interval
            return min(1.0, overdue_ratio * 0.5)

        return max(0.0, 1.0 - record.stability_score)

    def consolidate_knowledge(self) -> Dict[str, Any]:
        """
        知识巩固

        将近期学习的事件进行整合和巩固。

        Returns:
            Dict[str, Any]: 巩固结果
        """
        # 获取最近的事件
        recent_events = self.get_recent_events(limit=100)

        # 按类型分组
        by_type: Dict[str, List[LearningEvent]] = defaultdict(list)
        for event in recent_events:
            by_type[event.event_type].append(event)

        # 计算巩固效果
        consolidation_results = {}
        for event_type, events in by_type.items():
            # 相似事件合并
            merged_count = self._merge_similar_events(events)
            consolidation_results[event_type] = {
                "original_count": len(events),
                "merged_count": merged_count
            }

        logger.info(f"Knowledge consolidation: {len(recent_events)} events processed")
        return {
            "events_processed": len(recent_events),
            "consolidation_results": consolidation_results,
            "timestamp": datetime.now().isoformat()
        }

    def _merge_similar_events(self, events: List[LearningEvent]) -> int:
        """合并相似事件"""
        if len(events) < 2:
            return len(events)

        # 简单合并：按内容相似度分组
        groups: List[List[LearningEvent]] = []
        for event in events:
            found_group = False
            for group in groups:
                if any(self._event_similarity(event, e) > 0.7 for e in group):
                    group.append(event)
                    found_group = True
                    break
            if not found_group:
                groups.append([event])

        return len(groups)

    def _event_similarity(self, a: LearningEvent, b: LearningEvent) -> float:
        """计算事件相似度"""
        if a.event_type != b.event_type:
            return 0.0
        words_a = set(a.content.lower().split())
        words_b = set(b.content.lower().split())
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    # ========== 学习进度跟踪 ==========

    def track_progress(self, domain: str, current_level: float,
                       target_level: float = 1.0,
                       milestones: Optional[List[str]] = None) -> LearningProgress:
        """
        跟踪学习进度

        Args:
            domain: 领域
            current_level: 当前水平
            target_level: 目标水平
            milestones: 里程碑列表

        Returns:
            LearningProgress: 进度对象
        """
        if domain in self.progress_tracking:
            progress = self.progress_tracking[domain]
            progress.current_level = current_level
            progress.target_level = target_level
        else:
            progress = LearningProgress(
                domain=domain,
                current_level=current_level,
                target_level=target_level
            )
            self.progress_tracking[domain] = progress

        # 检查里程碑
        if milestones:
            for milestone in milestones:
                if milestone not in progress.milestones_achieved:
                    # 简单启发式：如果当前水平足够高，认为达成里程碑
                    if current_level >= 0.7:
                        progress.milestones_achieved.append(milestone)

        # 计算预计完成时间
        if current_level < target_level:
            learning_rate = self.get_learning_rate()
            if learning_rate > 0:
                remaining = target_level - current_level
                days_needed = remaining / (learning_rate / 100)  # 粗略估计
                progress.estimated_completion = datetime.fromtimestamp(
                    time.time() + days_needed * 86400
                )

        logger.debug(f"Progress tracked: {domain} = {current_level:.2f}/{target_level:.2f}")
        return progress

    def get_progress(self, domain: str) -> Optional[LearningProgress]:
        """获取学习进度"""
        return self.progress_tracking.get(domain)

    def get_all_progress(self) -> Dict[str, LearningProgress]:
        """获取所有进度"""
        return self.progress_tracking.copy()

    def get_overall_progress(self) -> float:
        """获取总体进度"""
        if not self.progress_tracking:
            return 0.0
        total = sum(p.current_level / p.target_level for p in self.progress_tracking.values())
        return total / len(self.progress_tracking)

    # ========== 学习效果评估 ==========

    def assess_effectiveness(self, period_start: Optional[datetime] = None,
                            period_end: Optional[datetime] = None) -> LearningEffectiveness:
        """
        评估学习效果

        Args:
            period_start: 开始时间
            period_end: 结束时间

        Returns:
            LearningEffectiveness: 效果评估
        """
        self.total_assessments += 1

        if period_start is None:
            period_start = datetime.fromtimestamp(time.time() - self.config.progress_evaluation_interval)
        if period_end is None:
            period_end = datetime.now()

        # 统计期间事件
        period_events = [
            e for e in self.event_history
            if period_start <= e.timestamp <= period_end
        ]

        # 计算知识获取
        knowledge_gained = len(set(
            e.metadata.get("knowledge_id", "")
            for e in period_events
            if "knowledge_id" in e.metadata
        ))

        # 计算保持率
        if self.forgetting_records:
            retention_rate = sum(
                r.stability_score for r in self.forgetting_records.values()
            ) / len(self.forgetting_records)
        else:
            retention_rate = 0.0

        # 计算应用成功率
        application_events = [e for e in period_events if e.event_type == "application"]
        successful_applications = sum(
            1 for e in application_events
            if e.metadata.get("success", False)
        )
        application_success_rate = (
            successful_applications / len(application_events)
            if application_events else 0.0
        )

        # 总体评分
        overall = (retention_rate * 0.4 + application_success_rate * 0.4 +
                   min(1.0, len(period_events) / 100) * 0.2)

        # 生成建议
        recommendations = self._generate_recommendations(
            retention_rate, application_success_rate, len(period_events)
        )

        assessment = LearningEffectiveness(
            period_start=period_start,
            period_end=period_end,
            events_count=len(period_events),
            knowledge_gained=knowledge_gained,
            retention_rate=retention_rate,
            application_success_rate=application_success_rate,
            overall_score=overall,
            recommendations=recommendations
        )

        self.effectiveness_assessments.append(assessment)
        logger.info(f"Learning effectiveness assessed: {overall:.2f}")
        return assessment

    def _generate_recommendations(self, retention: float,
                                  application_success: float,
                                  event_count: int) -> List[str]:
        """生成学习建议"""
        recommendations = []

        if retention < 0.5:
            recommendations.append("知识保持率较低，建议增加复习频率")
        if application_success < 0.5:
            recommendations.append("应用成功率较低，建议增加实践机会")
        if event_count < 10:
            recommendations.append("学习活动较少，建议增加学习投入")
        if not recommendations:
            recommendations.append("学习效果良好，继续保持")

        return recommendations

    def get_effectiveness_trend(self) -> Dict[str, Any]:
        """获取效果趋势"""
        if len(self.effectiveness_assessments) < 2:
            return {"trend": "insufficient_data", "change": 0.0}

        recent = self.effectiveness_assessments[-5:]
        scores = [a.overall_score for a in recent]

        if scores[-1] > scores[0]:
            trend = "improving"
        elif scores[-1] < scores[0]:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change": scores[-1] - scores[0],
            "avg_recent": sum(scores) / len(scores)
        }

    # ========== 知识快照 ==========

    def _check_snapshot(self) -> None:
        """检查是否需要创建快照"""
        current_time = time.time()
        if current_time - self.last_snapshot_time >= self.config.snapshot_interval:
            self._create_snapshot()
            self.last_snapshot_time = current_time

    def _create_snapshot(self) -> KnowledgeSnapshot:
        """创建知识快照"""
        self.total_snapshots += 1

        snapshot = KnowledgeSnapshot(
            knowledge_count=len(self.integrated_knowledge_ids),
            total_learning_events=self.total_events,
            avg_confidence=self._calculate_avg_confidence()
        )

        self.knowledge_snapshots.append(snapshot)
        logger.info(f"Knowledge snapshot created: {snapshot.knowledge_count} items")
        return snapshot

    def _calculate_avg_confidence(self) -> float:
        """计算平均置信度"""
        if not self.event_history:
            return 0.0
        recent_events = list(self.event_history)[-100:]
        return sum(e.importance for e in recent_events) / len(recent_events)

    def get_knowledge_growth(self) -> List[Dict[str, Any]]:
        """获取知识增长趋势"""
        if len(self.knowledge_snapshots) < 2:
            return []

        growth = []
        for i in range(1, len(self.knowledge_snapshots)):
            prev = self.knowledge_snapshots[i - 1]
            curr = self.knowledge_snapshots[i]
            growth.append({
                "period": f"{prev.timestamp.isoformat()} to {curr.timestamp.isoformat()}",
                "knowledge_change": curr.knowledge_count - prev.knowledge_count,
                "event_change": curr.total_learning_events - prev.total_learning_events
            })

        return growth

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取终身学习统计"""
        return {
            "total_events": self.total_events,
            "total_snapshots": self.total_snapshots,
            "total_reviews": self.total_reviews,
            "total_assessments": self.total_assessments,
            "event_history_size": len(self.event_history),
            "knowledge_integrations": len(self.knowledge_integrations),
            "integrated_knowledge_count": len(self.integrated_knowledge_ids),
            "forgetting_records": len(self.forgetting_records),
            "progress_domains": len(self.progress_tracking),
            "overall_progress": self.get_overall_progress(),
            "learning_rate": self.get_learning_rate(),
            "effectiveness_trend": self.get_effectiveness_trend(),
            "due_reviews_count": len(self.get_due_reviews()),
        }

    def reset(self) -> None:
        """重置终身学习状态"""
        self.event_history.clear()
        self.event_index.clear()
        self.knowledge_snapshots.clear()
        self.progress_tracking.clear()
        self.forgetting_records.clear()
        self.review_queue.clear()
        self.effectiveness_assessments.clear()
        self.knowledge_integrations.clear()
        self.integrated_knowledge_ids.clear()
        self.total_events = 0
        self.total_snapshots = 0
        self.total_reviews = 0
        self.total_assessments = 0
        self.last_snapshot_time = time.time()
        logger.info("LifelongLearningMechanism reset")
