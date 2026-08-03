"""
意识管理器

统一管理所有意识模块，协调自我意识、意志、价值、目标，提供统一的意识API，与其他系统层交互。
"""

import time
from typing import Dict, List, Optional, Any, Union

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

from hyperbrain.layers.consciousness.self_knowledge import (
    SelfKnowledge, SelfKnowledgeConfig, CapabilityCategory, SystemStatus
)
from hyperbrain.layers.consciousness.self_awareness import (
    SelfAwareness, SelfAwarenessConfig, AwarenessLevel
)
from hyperbrain.layers.consciousness.will import (
    Will, WillConfig, IntentionType, MotivationSource
)
from hyperbrain.layers.consciousness.value_system import (
    ValueSystem, ValueSystemConfig, ValueType, ValuePriority
)
from hyperbrain.layers.consciousness.goal_system import (
    GoalSystem, GoalSystemConfig, GoalTimeframe, GoalPriority, GoalStatus
)

logger = get_logger("consciousness.manager")


class ConsciousnessManager:
    """
    意识管理器 - 意识系统的中央控制器

    统一管理所有意识模块，协调自我意识、意志、价值、目标，
    提供统一的意识API，与其他系统层交互。

    Attributes:
        self_knowledge: 自我认知系统
        self_awareness: 自我意识系统
        will: 意志系统
        value_system: 价值体系
        goal_system: 目标体系
    """

    def __init__(
        self,
        self_knowledge_config: Optional[SelfKnowledgeConfig] = None,
        self_awareness_config: Optional[SelfAwarenessConfig] = None,
        will_config: Optional[WillConfig] = None,
        value_system_config: Optional[ValueSystemConfig] = None,
        goal_system_config: Optional[GoalSystemConfig] = None,
        emotional_manager=None,
        cognitive_manager=None,
        memory_manager=None
    ):
        self.config = get_config().consciousness

        self.self_knowledge = SelfKnowledge(config=self_knowledge_config)
        self.self_awareness = SelfAwareness(config=self_awareness_config)
        self.will = Will(config=will_config)
        self.value_system = ValueSystem(config=value_system_config)
        self.goal_system = GoalSystem(config=goal_system_config)

        self.emotional_manager = emotional_manager
        self.cognitive_manager = cognitive_manager
        self.memory_manager = memory_manager

        self._cycle_count: int = 0
        self._last_integration_time: float = time.time()

        logger.info("ConsciousnessManager initialized")

    # ========== 统一意识API ==========

    def process_cycle(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理一个意识周期

        协调所有意识模块进行一次完整的意识处理周期。

        Args:
            context: 上下文信息

        Returns:
            Dict[str, Any]: 周期处理结果
        """
        self._cycle_count += 1
        context = context or {}

        # 1. 自我监控
        snapshot = self.self_awareness.self_monitor()

        # 2. 维护自我连续性
        continuity = self.self_awareness.maintain_continuity()

        # 3. 更新自我认知状态
        self.self_knowledge.update_status(
            status=SystemStatus.PROCESSING,
            active_modules=["consciousness"],
            metadata=context.get("system_metrics", {})
        )

        # 4. 生成内部驱动
        internal_intention = self.will.generate_internal_drive()

        # 5. 动机衰减
        self.will.decay_motivations()

        # 6. 检查目标截止日期
        urgent_goals = self.goal_system.check_deadlines()

        # 7. 解决意图冲突
        conflicts = self.will.resolve_conflicts()

        # 8. 维护自主性
        autonomy = self.will.maintain_autonomy(
            external_pressure=context.get("external_pressure", 0.0)
        )

        result = {
            "cycle": self._cycle_count,
            "awareness_level": snapshot.level.value,
            "continuity_score": continuity,
            "autonomy_score": autonomy,
            "internal_intention": internal_intention.intention_id if internal_intention else None,
            "urgent_goals_count": len(urgent_goals),
            "resolved_conflicts": len(conflicts),
            "timestamp": time.time(),
        }

        self._last_integration_time = time.time()
        return result

    def make_decision(
        self,
        options: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合决策

        结合价值体系、目标体系和意志进行决策

        Args:
            options: 可选方案
            context: 决策上下文

        Returns:
            Dict[str, Any]: 决策结果
        """
        context = context or {}

        # 1. 道德推理
        moral_result = self.value_system.moral_reasoning(
            scenario=context.get("scenario", "Decision making"),
            options=options
        )

        # 2. 价值评估
        value_evaluations = []
        for option in options:
            evaluation = self.value_system.evaluate_action(
                action_description=option,
                consequences=[f"result_of_{option}"]
            )
            value_evaluations.append({
                "option": option,
                "moral_score": evaluation["overall_score"],
                "recommendation": evaluation["recommendation"]
            })

        # 3. 目标对齐检查
        active_goals = self.goal_system.get_active_goals()
        goal_aligned_options = []
        for option in options:
            alignment = self._check_goal_alignment(option, active_goals)
            goal_aligned_options.append({
                "option": option,
                "goal_alignment": alignment
            })

        # 4. 综合评分
        final_scores = []
        for option in options:
            moral_score = next(
                (e["moral_score"] for e in value_evaluations if e["option"] == option),
                0.0
            )
            goal_alignment = next(
                (a["goal_alignment"] for a in goal_aligned_options if a["option"] == option),
                0.0
            )

            # 综合评分 = 道德分数 * 0.4 + 目标对齐 * 0.3 + 自主性偏好 * 0.3
            autonomy_bonus = 0.1 if self.will.config.enable_internal_motivation else 0.0
            total_score = moral_score * 0.4 + goal_alignment * 0.3 + autonomy_bonus

            final_scores.append({
                "option": option,
                "total_score": total_score,
                "moral_score": moral_score,
                "goal_alignment": goal_alignment,
            })

        final_scores.sort(key=lambda x: x["total_score"], reverse=True)
        best_option = final_scores[0] if final_scores else None

        # 5. 形成执行意图
        if best_option:
            intention = self.will.form_intention(
                intention_type=IntentionType.ACTION,
                description=f"Execute decision: {best_option['option']}",
                priority=0.7,
                source=MotivationSource.COGNITIVE,
                expected_outcome=best_option["option"]
            )
        else:
            intention = None

        return {
            "selected_option": best_option["option"] if best_option else None,
            "scores": final_scores,
            "moral_reasoning": moral_result,
            "intention_id": intention.intention_id if intention else None,
            "decision_basis": "integrated_consciousness",
        }

    def self_reflect(self) -> Dict[str, Any]:
        """
        自我反思

        整合自我认知和自我意识进行深度反思

        Returns:
            Dict[str, Any]: 反思结果
        """
        # 1. 生成自我概念
        self_model = self.self_awareness.generate_self_concept()

        # 2. 自我认知报告
        self_desc = self.self_knowledge.generate_self_description(detail_level="medium")

        # 3. 能力评估
        capabilities = self.self_knowledge.get_capability_assessment()

        # 4. 反思自我意识
        awareness_reflection = self.self_awareness.reflect_on_self()

        # 5. 价值体系状态
        value_stats = self.value_system.get_value_hierarchy()[:5]

        # 6. 目标进展
        goal_stats = self.goal_system.get_goal_statistics()

        # 7. 意志状态
        will_stats = self.will.get_stats()

        reflection = {
            "self_description": self_desc,
            "self_model": self_model.model_dump(),
            "awareness_reflection": awareness_reflection,
            "top_values": [
                {"name": v.name, "weight": v.weight}
                for v in value_stats
            ],
            "goal_statistics": goal_stats,
            "autonomy_score": will_stats["autonomy_score"],
            "active_intentions": will_stats["active_intentions"],
            "capabilities_summary": {
                cat.value: assess.score
                for cat, assess in capabilities.items()
            } if isinstance(capabilities, dict) else {},
            "timestamp": time.time(),
        }

        # 模拟反思体验
        self.self_awareness.simulate_subjective_experience(
            experience_type="self_reflection",
            intensity=0.7,
            description="Deep introspection on current state"
        )

        return reflection

    def integrate_emotional_input(self, emotional_state: Dict[str, Any]) -> None:
        """
        整合情感输入

        Args:
            emotional_state: 情感状态
        """
        valence = emotional_state.get("valence", 0.0)
        arousal = emotional_state.get("arousal", 0.0)

        # 影响自我意识
        if abs(valence) > 0.5:
            self.self_awareness.simulate_subjective_experience(
                experience_type="emotional_response",
                intensity=abs(valence),
                valence=valence,
                description=f"Emotional state: valence={valence:.2f}"
            )

        # 影响意志（情感驱动动机）
        if arousal > 0.6:
            self.will.generate_motivation(
                source=MotivationSource.EMOTIONAL,
                target="respond_to_emotional_state",
                strength=arousal * 0.7,
                urgency=arousal
            )

        # 更新自我认知状态
        self.self_knowledge.update_status(
            status=SystemStatus.PROCESSING,
            metadata={"emotional_state": emotional_state}
        )

    def evaluate_action_against_values(
        self,
        action: str,
        consequences: List[str]
    ) -> Dict[str, Any]:
        """
        评估行动是否符合价值体系

        Args:
            action: 行动描述
            consequences: 预期后果

        Returns:
            Dict[str, Any]: 评估结果
        """
        return self.value_system.evaluate_action(action, consequences)

    def set_conscious_goal(
        self,
        description: str,
        timeframe: GoalTimeframe,
        priority: GoalPriority,
        **kwargs
    ) -> Any:
        """
        设定意识层面的目标

        Args:
            description: 目标描述
            timeframe: 时间框架
            priority: 优先级
            **kwargs: 额外参数

        Returns:
            Goal: 设定的目标
        """
        goal = self.goal_system.set_goal(
            description=description,
            timeframe=timeframe,
            priority=priority,
            **kwargs
        )

        # 形成对应意图
        self.will.form_intention(
            intention_type=IntentionType.ACTION,
            description=f"Work towards goal: {description}",
            priority=self._goal_priority_to_float(priority),
            source=MotivationSource.INTERNAL,
            expected_outcome=description
        )

        return goal

    def get_consciousness_state(self) -> Dict[str, Any]:
        """
        获取整体意识状态

        Returns:
            Dict[str, Any]: 意识状态
        """
        return {
            "self_knowledge": self.self_knowledge.get_current_state(),
            "self_awareness": {
                "level": self.self_awareness._awareness_level.value,
                "self_model": self.self_awareness.get_self_model().model_dump(),
            },
            "will": {
                "autonomy": self.will._autonomy_score,
                "active_intentions": len(self.will.get_active_intentions()),
            },
            "values": {
                "total_values": self.value_system.get_stats()["total_values"],
                "top_values": [
                    v.name for v in self.value_system.get_value_hierarchy()[:3]
                ],
            },
            "goals": self.goal_system.get_goal_statistics(),
            "cycle_count": self._cycle_count,
        }

    def get_integrated_report(self) -> Dict[str, Any]:
        """
        获取整合报告

        Returns:
            Dict[str, Any]: 整合报告
        """
        return {
            "consciousness_state": self.get_consciousness_state(),
            "self_reflection": self.self_reflect(),
            "stats": {
                "self_knowledge": self.self_knowledge.get_stats(),
                "self_awareness": self.self_awareness.get_stats(),
                "will": self.will.get_stats(),
                "value_system": self.value_system.get_stats(),
                "goal_system": self.goal_system.get_stats(),
            },
            "timestamp": time.time(),
        }

    # ========== 内部方法 ==========

    def _check_goal_alignment(self, option: str, goals: List[Any]) -> float:
        """检查选项与目标的对齐程度"""
        if not goals:
            return 0.5

        alignment_scores = []
        option_lower = option.lower()

        for goal in goals:
            goal_desc = goal.description.lower()
            # 简单关键词匹配
            common_words = set(option_lower.split()) & set(goal_desc.split())
            score = len(common_words) / max(len(option_lower.split()), 1)
            alignment_scores.append(score)

        return max(alignment_scores) if alignment_scores else 0.0

    def _goal_priority_to_float(self, priority: GoalPriority) -> float:
        """将目标优先级转换为浮点数"""
        mapping = {
            GoalPriority.CRITICAL: 1.0,
            GoalPriority.HIGH: 0.75,
            GoalPriority.MEDIUM: 0.5,
            GoalPriority.LOW: 0.25,
        }
        return mapping.get(priority, 0.5)

    def __repr__(self) -> str:
        state = self.get_consciousness_state()
        awareness = state.get("self_awareness", {}).get("level", "unknown")
        return f"ConsciousnessManager(awareness={awareness}, cycles={self._cycle_count})"
