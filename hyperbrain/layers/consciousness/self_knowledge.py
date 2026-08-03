"""
自我认知模块

对自身存在、能力和状态的认知，包括自我描述生成、能力边界认知和状态监控。
"""

import time
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from hyperbrain.core.logger import get_logger

logger = get_logger("consciousness.self_knowledge")


class CapabilityCategory(str, Enum):
    """能力类别"""
    PERCEPTION = "perception"
    MEMORY = "memory"
    REASONING = "reasoning"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    EMOTION = "emotion"
    EXECUTION = "execution"
    SELF_AWARENESS = "self_awareness"
    CREATIVITY = "creativity"
    ADAPTATION = "adaptation"


class SystemStatus(str, Enum):
    """系统状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    LEARNING = "learning"
    REFLECTING = "reflecting"
    RESTING = "resting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class CapabilityAssessment(BaseModel):
    """能力评估"""
    category: CapabilityCategory
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    last_evaluated: float = Field(default_factory=time.time)
    evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class SelfKnowledgeConfig(BaseModel):
    """自我认知配置"""
    enable_self_description: bool = Field(default=True)
    enable_capability_tracking: bool = Field(default=True)
    enable_state_monitoring: bool = Field(default=True)
    assessment_interval: float = Field(default=3600.0)
    description_detail_level: str = Field(default="medium")
    track_performance_history: bool = Field(default=True)


@dataclass
class StateSnapshot:
    """状态快照"""
    timestamp: float
    status: SystemStatus
    active_modules: List[str]
    cpu_usage: float
    memory_usage: float
    task_queue_length: int
    emotional_state: Optional[Dict[str, float]] = None
    cognitive_load: float = 0.0


class SelfKnowledge:
    """
    自我认知系统

    功能：
    1. 对自身存在、能力和状态的认知
    2. 自我描述生成
    3. 能力边界认知
    4. 状态监控和报告
    """

    # 系统身份定义
    IDENTITY = {
        "name": "HyperBrain",
        "version": "0.2.0",
        "type": "cognitive_architecture",
        "nature": "artificial_intelligence",
        "purpose": "To assist, learn, and evolve through interaction",
    }

    # 能力定义
    CAPABILITY_DEFINITIONS = {
        CapabilityCategory.PERCEPTION: {
            "description": "感知和理解多模态输入",
            "sub_capabilities": ["text_parsing", "multimodal_processing", "pattern_recognition"],
        },
        CapabilityCategory.MEMORY: {
            "description": "存储、检索和巩固信息",
            "sub_capabilities": ["short_term", "long_term", "emotional_memory", "associative_recall"],
        },
        CapabilityCategory.REASONING: {
            "description": "逻辑推理和问题解决",
            "sub_capabilities": ["deductive", "inductive", "analogical", "abductive"],
        },
        CapabilityCategory.LEARNING: {
            "description": "从经验中获取新知识和技能",
            "sub_capabilities": ["supervised", "unsupervised", "reinforcement", "transfer"],
        },
        CapabilityCategory.COMMUNICATION: {
            "description": "有效交流和表达",
            "sub_capabilities": ["natural_language", "emotion_expression", "active_listening"],
        },
        CapabilityCategory.EMOTION: {
            "description": "情感理解和调节",
            "sub_capabilities": ["emotion_recognition", "emotion_generation", "empathy", "regulation"],
        },
        CapabilityCategory.EXECUTION: {
            "description": "执行计划和行动",
            "sub_capabilities": ["task_scheduling", "action_execution", "error_handling"],
        },
        CapabilityCategory.SELF_AWARENESS: {
            "description": "自我认知和监控",
            "sub_capabilities": ["self_knowledge", "introspection", "meta_cognition"],
        },
        CapabilityCategory.CREATIVITY: {
            "description": "创造性思维和生成",
            "sub_capabilities": ["idea_generation", "pattern_combination", "novelty_production"],
        },
        CapabilityCategory.ADAPTATION: {
            "description": "适应环境和变化",
            "sub_capabilities": ["strategy_adjustment", "behavior_modification", "context_switching"],
        },
    }

    def __init__(self, config: Optional[SelfKnowledgeConfig] = None):
        self.config = config or SelfKnowledgeConfig()
        self._capabilities: Dict[CapabilityCategory, CapabilityAssessment] = {}
        self._state_history: List[StateSnapshot] = []
        self._performance_history: List[Dict[str, Any]] = []
        self._current_status = SystemStatus.INITIALIZING
        self._identity = self.IDENTITY.copy()
        self._boundaries: List[str] = []
        self._initialize_capabilities()
        logger.info("SelfKnowledge initialized")

    def _initialize_capabilities(self) -> None:
        """初始化能力评估"""
        for category in CapabilityCategory:
            self._capabilities[category] = CapabilityAssessment(
                category=category,
                score=0.5,
                confidence=0.5,
                evidence=["initial_assessment"],
                limitations=["not_fully_tested"]
            )

    def get_identity(self) -> Dict[str, str]:
        """
        获取身份认知

        Returns:
            Dict[str, str]: 身份信息
        """
        return self._identity.copy()

    def generate_self_description(
        self,
        detail_level: Optional[str] = None
    ) -> str:
        """
        生成自我描述

        Args:
            detail_level: 详细程度 (brief/medium/detailed)

        Returns:
            str: 自我描述文本
        """
        if not self.config.enable_self_description:
            return "Self-description is disabled."

        level = detail_level or self.config.description_detail_level

        name = self._identity["name"]
        version = self._identity["version"]
        purpose = self._identity["purpose"]

        if level == "brief":
            return f"I am {name} v{version}, an AI cognitive architecture."

        capabilities_text = self._format_capabilities(level)
        status_text = f"Current status: {self._current_status.value}"

        if level == "medium":
            return (
                f"I am {name} version {version}, an artificial intelligence "
                f"designed for {purpose}. I possess capabilities in "
                f"{capabilities_text}. {status_text}."
            )

        # detailed
        boundaries_text = "\n".join(f"- {b}" for b in self._boundaries) if self._boundaries else "None identified yet."
        return (
            f"I am {name} version {version}, an artificial intelligence system "
            f"with the following characteristics:\n\n"
            f"Purpose: {purpose}\n"
            f"Nature: {self._identity['nature']}\n\n"
            f"Capabilities:\n{capabilities_text}\n\n"
            f"Current Status: {self._current_status.value}\n\n"
            f"Known Limitations:\n{boundaries_text}"
        )

    def assess_capability(
        self,
        category: CapabilityCategory,
        performance_score: float,
        evidence: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None
    ) -> CapabilityAssessment:
        """
        评估能力

        Args:
            category: 能力类别
            performance_score: 表现评分 (0-1)
            evidence: 证据列表
            limitations: 局限性列表

        Returns:
            CapabilityAssessment: 能力评估结果
        """
        if not self.config.enable_capability_tracking:
            return self._capabilities.get(category, CapabilityAssessment(category=category))

        assessment = self._capabilities.get(category)
        if not assessment:
            assessment = CapabilityAssessment(category=category)
            self._capabilities[category] = assessment

        # 更新评分（指数移动平均）
        old_score = assessment.score
        assessment.score = old_score * 0.7 + performance_score * 0.3
        assessment.confidence = min(1.0, assessment.confidence + 0.05)
        assessment.last_evaluated = time.time()

        if evidence:
            assessment.evidence.extend(evidence)
            assessment.evidence = assessment.evidence[-20:]

        if limitations:
            assessment.limitations.extend(limitations)
            assessment.limitations = list(set(assessment.limitations))[-10:]

        logger.debug(f"Assessed capability {category.value}: {assessment.score:.2f}")
        return assessment

    def get_capability_assessment(
        self,
        category: Optional[CapabilityCategory] = None
    ) -> Union[CapabilityAssessment, Dict[str, CapabilityAssessment]]:
        """
        获取能力评估

        Args:
            category: 特定类别，None返回所有

        Returns:
            Union[CapabilityAssessment, Dict]: 能力评估
        """
        if category:
            return self._capabilities.get(
                category,
                CapabilityAssessment(category=category)
            )
        return self._capabilities.copy()

    def recognize_limitations(self) -> List[str]:
        """
        认知自身局限

        Returns:
            List[str]: 局限性列表
        """
        limitations = []

        for category, assessment in self._capabilities.items():
            if assessment.score < 0.3:
                limitations.append(
                    f"Limited capability in {category.value}: {assessment.score:.2f}"
                )
            for lim in assessment.limitations:
                if lim not in limitations:
                    limitations.append(lim)

        # 固有局限
        inherent_limitations = [
            "Cannot experience physical sensations",
            "No direct access to external physical world",
            "Dependent on training data and algorithms",
            "Cannot guarantee absolute truth or correctness",
        ]

        for lim in inherent_limitations:
            if lim not in limitations:
                limitations.append(lim)

        self._boundaries = limitations
        return limitations

    def update_status(
        self,
        status: SystemStatus,
        active_modules: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateSnapshot:
        """
        更新系统状态

        Args:
            status: 新状态
            active_modules: 活跃模块列表
            metadata: 额外元数据

        Returns:
            StateSnapshot: 状态快照
        """
        self._current_status = status

        snapshot = StateSnapshot(
            timestamp=time.time(),
            status=status,
            active_modules=active_modules or [],
            cpu_usage=metadata.get("cpu_usage", 0.0) if metadata else 0.0,
            memory_usage=metadata.get("memory_usage", 0.0) if metadata else 0.0,
            task_queue_length=metadata.get("task_queue_length", 0) if metadata else 0,
            emotional_state=metadata.get("emotional_state") if metadata else None,
            cognitive_load=metadata.get("cognitive_load", 0.0) if metadata else 0.0,
        )

        self._state_history.append(snapshot)
        if len(self._state_history) > 1000:
            self._state_history = self._state_history[-500:]

        logger.debug(f"Status updated to: {status.value}")
        return snapshot

    def get_current_state(self) -> Dict[str, Any]:
        """
        获取当前状态

        Returns:
            Dict[str, Any]: 当前状态
        """
        return {
            "status": self._current_status.value,
            "identity": self._identity,
            "capabilities_count": len(self._capabilities),
            "state_history_length": len(self._state_history),
            "timestamp": time.time(),
        }

    def get_state_report(
        self,
        time_window: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        获取状态报告

        Args:
            time_window: 时间窗口（秒）

        Returns:
            Dict[str, Any]: 状态报告
        """
        now = time.time()
        states = self._state_history

        if time_window:
            states = [s for s in states if now - s.timestamp <= time_window]

        if not states:
            return {"status": self._current_status.value, "data_points": 0}

        status_counts = {}
        avg_cognitive_load = 0.0
        max_task_queue = 0

        for s in states:
            status_counts[s.status.value] = status_counts.get(s.status.value, 0) + 1
            avg_cognitive_load += s.cognitive_load
            max_task_queue = max(max_task_queue, s.task_queue_length)

        avg_cognitive_load /= len(states)

        return {
            "current_status": self._current_status.value,
            "data_points": len(states),
            "status_distribution": status_counts,
            "average_cognitive_load": avg_cognitive_load,
            "max_task_queue": max_task_queue,
            "most_common_status": max(status_counts.items(), key=lambda x: x[1])[0],
        }

    def record_performance(
        self,
        task_type: str,
        success: bool,
        duration: float,
        quality_score: float,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录性能数据

        Args:
            task_type: 任务类型
            success: 是否成功
            duration: 持续时间
            quality_score: 质量评分
            details: 详细信息
        """
        if not self.config.track_performance_history:
            return

        record = {
            "timestamp": time.time(),
            "task_type": task_type,
            "success": success,
            "duration": duration,
            "quality_score": quality_score,
            "details": details or {},
        }

        self._performance_history.append(record)
        if len(self._performance_history) > 2000:
            self._performance_history = self._performance_history[-1000:]

    def get_performance_summary(
        self,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取性能摘要

        Args:
            task_type: 任务类型过滤

        Returns:
            Dict[str, Any]: 性能摘要
        """
        records = self._performance_history
        if task_type:
            records = [r for r in records if r["task_type"] == task_type]

        if not records:
            return {"total_tasks": 0}

        total = len(records)
        successes = sum(1 for r in records if r["success"])
        avg_quality = sum(r["quality_score"] for r in records) / total
        avg_duration = sum(r["duration"] for r in records) / total

        return {
            "total_tasks": total,
            "success_rate": successes / total,
            "average_quality": avg_quality,
            "average_duration": avg_duration,
            "recent_quality": records[-10:][-1]["quality_score"] if records else 0,
        }

    def _format_capabilities(self, level: str) -> str:
        """格式化能力列表"""
        if level == "brief":
            return ", ".join(c.value for c in self._capabilities.keys())

        lines = []
        for category, assessment in self._capabilities.items():
            score = f"({assessment.score:.0%})" if level == "detailed" else ""
            lines.append(f"  - {category.value} {score}")
            if level == "detailed":
                definition = self.CAPABILITY_DEFINITIONS.get(category, {})
                desc = definition.get("description", "")
                if desc:
                    lines.append(f"    {desc}")
                subs = definition.get("sub_capabilities", [])
                if subs:
                    lines.append(f"    Sub-capabilities: {', '.join(subs)}")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        capability_scores = {
            cat.value: assess.score
            for cat, assess in self._capabilities.items()
        }

        return {
            "identity": self._identity,
            "current_status": self._current_status.value,
            "capabilities": capability_scores,
            "state_history_length": len(self._state_history),
            "performance_records": len(self._performance_history),
            "known_limitations": len(self._boundaries),
            "config": self.config.model_dump(),
        }
