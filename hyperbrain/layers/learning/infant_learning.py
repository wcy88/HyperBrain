"""
婴儿学习引擎 (Infant Learning Engine)

模拟婴儿期的学习方式：
- 无监督探索学习：自动发现数据中的模式
- 试错学习：通过尝试和错误学习
- 模式识别：识别重复出现的模式
- 模仿学习：模仿观察到的行为
- 好奇心驱动：探索未知领域

特征：高探索率、快速适应、泛化能力强
"""

import uuid
import random
import math
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("learning.infant")


class ExplorationResult(BaseModel):
    """探索学习结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_id: Optional[str] = Field(default=None)
    pattern_type: str = Field(default="unknown")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", "novelty_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class TrialResult(BaseModel):
    """试错学习结果"""
    trial_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(...)
    outcome: str = Field(default="")
    success: bool = Field(default=False)
    reward: float = Field(default=0.0, ge=-1.0, le=1.0)
    learning_delta: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reward")
    @classmethod
    def validate_reward(cls, v: float) -> float:
        return max(-1.0, min(1.0, v))


class DiscoveredPattern(BaseModel):
    """发现的模式"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = Field(default="sequential")
    elements: List[Any] = Field(default_factory=list)
    frequency: int = Field(default=1, ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    source_contexts: List[str] = Field(default_factory=list)
    generality_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("confidence", "generality_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ImitationRecord(BaseModel):
    """模仿学习记录"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    observed_behavior: str = Field(...)
    reproduced_behavior: str = Field(default="")
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    success: bool = Field(default=False)
    attempts: int = Field(default=1, ge=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("similarity_score")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class CuriosityState(BaseModel):
    """好奇心状态"""
    current_interest: str = Field(default="")
    exploration_rate: float = Field(default=0.9, ge=0.0, le=1.0)
    novelty_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    attention_focus: Optional[str] = Field(default=None)
    attention_duration: float = Field(default=0.0)
    recent_discoveries: List[str] = Field(default_factory=list)
    boredom_level: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("exploration_rate", "novelty_threshold", "boredom_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class InfantLearningConfig:
    """婴儿学习配置"""
    exploration_rate: float = 0.9
    learning_rate: float = 0.3
    pattern_threshold: float = 0.3
    curiosity_decay: float = 0.05
    max_patterns: int = 1000
    trial_memory_size: int = 500
    imitation_threshold: float = 0.6
    generalization_factor: float = 0.5


class InfantLearningEngine:
    """
    婴儿学习引擎

    模拟婴儿期（0-2岁）的学习方式，特点：
    1. 高探索率：大量尝试和探索
    2. 快速适应：快速调整行为
    3. 强泛化：从少量样本推广
    4. 好奇心驱动：主动探索未知
    5. 模仿学习：通过观察学习

    Attributes:
        config: 学习配置
        patterns: 发现的模式库
        trial_history: 试错历史
        imitation_records: 模仿记录
        curiosity: 好奇心状态
        action_values: 动作价值估计
    """

    def __init__(self, config: Optional[InfantLearningConfig] = None):
        self.config = config or InfantLearningConfig()
        self.exploration_rate = self.config.exploration_rate
        self.learning_rate = self.config.learning_rate

        # 模式库
        self.patterns: Dict[str, DiscoveredPattern] = {}
        self.pattern_index: Dict[str, List[str]] = defaultdict(list)

        # 试错学习
        self.trial_history: List[TrialResult] = []
        self.action_outcomes: Dict[str, List[TrialResult]] = defaultdict(list)
        self.action_values: Dict[str, float] = {}

        # 模仿学习
        self.imitation_records: List[ImitationRecord] = []
        self.observed_behaviors: Dict[str, int] = Counter()
        self.behavior_patterns: Dict[str, List[str]] = defaultdict(list)

        # 好奇心
        self.curiosity = CuriosityState()
        self.known_patterns: Set[str] = set()
        self.novelty_scores: Dict[str, float] = {}

        # 探索历史
        self.exploration_history: List[ExplorationResult] = []
        self.explored_spaces: Set[str] = set()

        # 学习统计
        self.total_explorations: int = 0
        self.total_trials: int = 0
        self.total_imitations: int = 0
        self.patterns_discovered: int = 0

        logger.info("InfantLearningEngine initialized")

    # ========== 无监督探索学习 ==========

    def explore(self, data: Any, context: str = "") -> ExplorationResult:
        """
        无监督探索学习

        自动发现数据中的模式和规律，不需要标签或反馈。

        Args:
            data: 输入数据
            context: 上下文标识

        Returns:
            ExplorationResult: 探索结果
        """
        self.total_explorations += 1

        # 计算新颖性
        novelty = self._calculate_novelty(data, context)

        # 尝试发现模式
        pattern_id = None
        pattern_type = "unknown"
        confidence = 0.0
        description = ""

        if isinstance(data, (list, tuple)):
            pattern_id, pattern_type, confidence = self._discover_sequence_pattern(data, context)
            description = f"Discovered {pattern_type} pattern with {len(data)} elements"
        elif isinstance(data, dict):
            pattern_id, pattern_type, confidence = self._discover_structural_pattern(data, context)
            description = f"Discovered structural pattern with {len(data)} keys"
        elif isinstance(data, str):
            pattern_id, pattern_type, confidence = self._discover_text_pattern(data, context)
            description = f"Discovered text pattern: {data[:50]}..."
        else:
            # 简单特征提取
            feature_key = self._extract_feature_key(data)
            if feature_key not in self.known_patterns:
                self.known_patterns.add(feature_key)
                novelty = 1.0
            description = f"Explored data of type {type(data).__name__}"

        # 更新好奇心
        self._update_curiosity(novelty, pattern_id)

        result = ExplorationResult(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            confidence=confidence,
            novelty_score=novelty,
            description=description,
            metadata={"context": context, "data_type": type(data).__name__}
        )

        self.exploration_history.append(result)
        logger.debug(f"Exploration: {description}, novelty={novelty:.2f}")
        return result

    def _calculate_novelty(self, data: Any, context: str) -> float:
        """计算数据的新颖性"""
        feature_key = self._extract_feature_key(data)

        if feature_key in self.known_patterns:
            return 0.1  # 已知的，低新颖性

        # 检查相似度
        max_similarity = 0.0
        for known in self.known_patterns:
            similarity = self._compute_similarity(feature_key, known)
            max_similarity = max(max_similarity, similarity)

        novelty = 1.0 - max_similarity
        self.novelty_scores[feature_key] = novelty
        return novelty

    def _extract_feature_key(self, data: Any) -> str:
        """提取特征键"""
        if isinstance(data, (list, tuple)):
            return f"list_len_{len(data)}_types_{self._get_type_signature(data)}"
        elif isinstance(data, dict):
            return f"dict_keys_{'_'.join(sorted(data.keys())[:5])}"
        elif isinstance(data, str):
            return f"str_len_{len(data)}_start_{data[:20]}"
        else:
            return f"type_{type(data).__name__}_repr_{repr(data)[:30]}"

    def _get_type_signature(self, data: List[Any]) -> str:
        """获取类型签名"""
        types = [type(item).__name__ for item in data[:10]]
        return "_".join(sorted(set(types)))

    def _compute_similarity(self, a: str, b: str) -> float:
        """计算两个特征键的相似度"""
        # 简单的Jaccard相似度
        set_a = set(a.split("_"))
        set_b = set(b.split("_"))
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _discover_sequence_pattern(self, data: List[Any], context: str) -> Tuple[Optional[str], str, float]:
        """发现序列模式"""
        if len(data) < 2:
            return None, "single", 0.5

        # 寻找重复子序列
        pattern_key = self._sequence_to_key(data)

        # 检查是否已存在相似模式
        for pid, pattern in self.patterns.items():
            if pattern.pattern_type == "sequential":
                similarity = self._sequence_similarity(data, pattern.elements)
                if similarity > self.config.pattern_threshold:
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(1.0, pattern.confidence + 0.05)
                    pattern.generality_score = self._calculate_generality(pattern)
                    return pid, "sequential", pattern.confidence

        # 创建新模式
        pattern = DiscoveredPattern(
            pattern_type="sequential",
            elements=data[:50],  # 限制大小
            confidence=0.5,
            source_contexts=[context]
        )
        self.patterns[pattern.pattern_id] = pattern
        self.pattern_index["sequential"].append(pattern.pattern_id)
        self.patterns_discovered += 1

        return pattern.pattern_id, "sequential", pattern.confidence

    def _discover_structural_pattern(self, data: Dict[str, Any], context: str) -> Tuple[Optional[str], str, float]:
        """发现结构模式"""
        structure_key = tuple(sorted(data.keys()))

        for pid, pattern in self.patterns.items():
            if pattern.pattern_type == "structural":
                if isinstance(pattern.elements, list) and set(pattern.elements) == set(structure_key):
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(1.0, pattern.confidence + 0.1)
                    return pid, "structural", pattern.confidence

        pattern = DiscoveredPattern(
            pattern_type="structural",
            elements=list(structure_key),
            confidence=0.5,
            source_contexts=[context]
        )
        self.patterns[pattern.pattern_id] = pattern
        self.pattern_index["structural"].append(pattern.pattern_id)
        self.patterns_discovered += 1

        return pattern.pattern_id, "structural", pattern.confidence

    def _discover_text_pattern(self, data: str, context: str) -> Tuple[Optional[str], str, float]:
        """发现文本模式"""
        # 提取n-gram
        words = data.lower().split()
        if len(words) < 2:
            return None, "single_word", 0.3

        # 寻找常见词组
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        most_common = Counter(bigrams).most_common(1)

        if most_common:
            pattern_key = most_common[0][0]
            for pid, pattern in self.patterns.items():
                if pattern.pattern_type == "text" and pattern_key in pattern.elements:
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(1.0, pattern.confidence + 0.05)
                    return pid, "text", pattern.confidence

            pattern = DiscoveredPattern(
                pattern_type="text",
                elements=[pattern_key],
                confidence=0.4,
                source_contexts=[context]
            )
            self.patterns[pattern.pattern_id] = pattern
            self.pattern_index["text"].append(pattern.pattern_id)
            self.patterns_discovered += 1
            return pattern.pattern_id, "text", pattern.confidence

        return None, "text", 0.3

    def _sequence_to_key(self, data: List[Any]) -> str:
        """将序列转换为键"""
        return "_".join(str(item)[:20] for item in data[:10])

    def _sequence_similarity(self, a: List[Any], b: List[Any]) -> float:
        """计算序列相似度"""
        if not a or not b:
            return 0.0
        # 最长公共子序列的近似
        common = sum(1 for x, y in zip(a, b) if x == y)
        return common / max(len(a), len(b))

    def _calculate_generality(self, pattern: DiscoveredPattern) -> float:
        """计算模式的泛化程度"""
        context_diversity = len(set(pattern.source_contexts)) / max(len(pattern.source_contexts), 1)
        frequency_score = min(1.0, pattern.frequency / 10)
        return (context_diversity + frequency_score) / 2

    # ========== 试错学习 ==========

    def trial(self, action: str, outcome_callback: Optional[Callable[[], Tuple[str, float]]] = None,
              expected_outcome: Optional[str] = None) -> TrialResult:
        """
        试错学习

        尝试一个动作，观察结果，更新对动作价值的估计。

        Args:
            action: 动作描述
            outcome_callback: 结果回调函数，返回(outcome, reward)
            expected_outcome: 预期结果

        Returns:
            TrialResult: 试错结果
        """
        self.total_trials += 1

        # 执行动作并获取结果
        if outcome_callback:
            outcome, reward = outcome_callback()
        else:
            outcome = "unknown"
            reward = 0.0

        # 判断是否成功
        success = reward > 0.0
        if expected_outcome:
            success = success and (outcome == expected_outcome)

        # 计算学习增量
        old_value = self.action_values.get(action, 0.0)
        learning_delta = self.learning_rate * (reward - old_value)
        new_value = old_value + learning_delta
        self.action_values[action] = max(-1.0, min(1.0, new_value))

        result = TrialResult(
            action=action,
            outcome=outcome,
            success=success,
            reward=reward,
            learning_delta=learning_delta,
            metadata={"expected": expected_outcome, "old_value": old_value}
        )

        self.trial_history.append(result)
        self.action_outcomes[action].append(result)

        # 限制历史大小
        if len(self.trial_history) > self.config.trial_memory_size:
            self.trial_history.pop(0)

        logger.debug(f"Trial: action={action}, reward={reward:.2f}, delta={learning_delta:.3f}")
        return result

    def select_action(self, available_actions: List[str],
                      strategy: str = "epsilon_greedy") -> str:
        """
        选择动作（带探索）

        Args:
            available_actions: 可用动作列表
            strategy: 选择策略 (epsilon_greedy, softmax, random)

        Returns:
            str: 选中的动作
        """
        if not available_actions:
            raise ValueError("No actions available")

        if strategy == "random" or random.random() < self.exploration_rate:
            return random.choice(available_actions)

        if strategy == "epsilon_greedy":
            # 选择价值最高的
            values = {a: self.action_values.get(a, 0.0) for a in available_actions}
            return max(values, key=values.get)

        elif strategy == "softmax":
            # Softmax选择
            values = [self.action_values.get(a, 0.0) for a in available_actions]
            exp_values = [math.exp(v) for v in values]
            total = sum(exp_values)
            probs = [v / total for v in exp_values]
            return random.choices(available_actions, weights=probs)[0]

        return random.choice(available_actions)

    def get_action_value(self, action: str) -> float:
        """获取动作价值"""
        return self.action_values.get(action, 0.0)

    def get_best_actions(self, top_k: int = 5) -> List[Tuple[str, float]]:
        """获取最佳动作"""
        sorted_actions = sorted(
            self.action_values.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_actions[:top_k]

    # ========== 模式识别 ==========

    def recognize_pattern(self, data: Any) -> List[DiscoveredPattern]:
        """
        识别数据中的已知模式

        Args:
            data: 输入数据

        Returns:
            List[DiscoveredPattern]: 匹配的模式列表
        """
        matches = []
        data_key = self._extract_feature_key(data)

        for pattern in self.patterns.values():
            similarity = 0.0

            if pattern.pattern_type == "sequential" and isinstance(data, (list, tuple)):
                similarity = self._sequence_similarity(data, pattern.elements)
            elif pattern.pattern_type == "structural" and isinstance(data, dict):
                data_keys = set(data.keys())
                pattern_keys = set(pattern.elements) if isinstance(pattern.elements, list) else set()
                intersection = len(data_keys & pattern_keys)
                union = len(data_keys | pattern_keys)
                similarity = intersection / union if union > 0 else 0.0
            elif pattern.pattern_type == "text" and isinstance(data, str):
                similarity = self._text_pattern_match(data, pattern)

            if similarity > self.config.pattern_threshold:
                # 更新模式统计
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                matches.append((pattern, similarity))

        # 按相似度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in matches]

    def _text_pattern_match(self, text: str, pattern: DiscoveredPattern) -> float:
        """文本模式匹配"""
        text_lower = text.lower()
        if isinstance(pattern.elements, list):
            matches = sum(1 for elem in pattern.elements if str(elem) in text_lower)
            return matches / len(pattern.elements) if pattern.elements else 0.0
        return 0.0

    def get_patterns_by_type(self, pattern_type: str) -> List[DiscoveredPattern]:
        """获取特定类型的模式"""
        pattern_ids = self.pattern_index.get(pattern_type, [])
        return [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]

    def get_most_frequent_patterns(self, top_k: int = 10) -> List[DiscoveredPattern]:
        """获取最频繁的模式"""
        return sorted(
            self.patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )[:top_k]

    # ========== 模仿学习 ==========

    def observe(self, behavior: str, context: str = "") -> None:
        """
        观察行为

        Args:
            behavior: 观察到的行为
            context: 上下文
        """
        self.observed_behaviors[behavior] += 1
        self.behavior_patterns[context].append(behavior)
        logger.debug(f"Observed behavior: {behavior} in context {context}")

    def imitate(self, behavior: str, reproduction: str,
                evaluator: Optional[Callable[[str, str], float]] = None) -> ImitationRecord:
        """
        模仿行为

        Args:
            behavior: 观察到的行为
            reproduction: 复现的行为
            evaluator: 评估函数，返回相似度分数

        Returns:
            ImitationRecord: 模仿记录
        """
        self.total_imitations += 1

        # 计算相似度
        if evaluator:
            similarity = evaluator(behavior, reproduction)
        else:
            similarity = self._default_similarity(behavior, reproduction)

        success = similarity >= self.config.imitation_threshold

        record = ImitationRecord(
            observed_behavior=behavior,
            reproduced_behavior=reproduction,
            similarity_score=similarity,
            success=success,
            metadata={"attempt": self.total_imitations}
        )

        self.imitation_records.append(record)

        # 如果成功，更新行为模式
        if success:
            self.behavior_patterns["successful_imitation"].append(behavior)
            logger.info(f"Successful imitation: {behavior[:50]}... similarity={similarity:.2f}")

        return record

    def _default_similarity(self, a: str, b: str) -> float:
        """默认相似度计算"""
        if not a or not b:
            return 0.0
        # 简单的字符级相似度
        a_set = set(a.lower())
        b_set = set(b.lower())
        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return intersection / union if union > 0 else 0.0

    def get_observed_behaviors(self, min_count: int = 1) -> List[Tuple[str, int]]:
        """获取观察到的行为（按频率排序）"""
        return [
            (behavior, count)
            for behavior, count in self.observed_behaviors.most_common()
            if count >= min_count
        ]

    def get_successful_imitations(self) -> List[ImitationRecord]:
        """获取成功的模仿记录"""
        return [r for r in self.imitation_records if r.success]

    # ========== 好奇心驱动 ==========

    def _update_curiosity(self, novelty: float, pattern_id: Optional[str] = None) -> None:
        """更新好奇心状态"""
        # 新颖性越高，好奇心越被满足
        if novelty > self.curiosity.novelty_threshold:
            self.curiosity.boredom_level = max(0.0, self.curiosity.boredom_level - 0.1)
            if pattern_id:
                self.curiosity.recent_discoveries.append(pattern_id)
                # 限制历史
                if len(self.curiosity.recent_discoveries) > 20:
                    self.curiosity.recent_discoveries.pop(0)
        else:
            # 低新颖性增加无聊感
            self.curiosity.boredom_level = min(1.0, self.curiosity.boredom_level + self.config.curiosity_decay)

        # 无聊时增加探索率
        if self.curiosity.boredom_level > 0.7:
            self.exploration_rate = min(1.0, self.exploration_rate + 0.1)
        else:
            self.exploration_rate = max(0.1, self.exploration_rate - 0.01)

        self.curiosity.exploration_rate = self.exploration_rate

    def express_curiosity(self) -> str:
        """
        表达好奇心

        Returns:
            str: 好奇心表达
        """
        if self.curiosity.boredom_level > 0.8:
            return "想要探索全新的东西！"
        elif self.curiosity.boredom_level > 0.5:
            return "对周围的事物感到好奇"
        elif self.curiosity.recent_discoveries:
            return f"最近发现了 {len(self.curiosity.recent_discoveries)} 个新模式"
        return "安静地观察周围"

    def get_curiosity_state(self) -> CuriosityState:
        """获取好奇心状态"""
        return self.curiosity

    # ========== 泛化能力 ==========

    def generalize(self, examples: List[Any]) -> Optional[DiscoveredPattern]:
        """
        从例子中泛化模式

        Args:
            examples: 示例列表

        Returns:
            Optional[DiscoveredPattern]: 泛化出的模式
        """
        if len(examples) < 2:
            return None

        # 提取共同特征
        if all(isinstance(e, dict) for e in examples):
            common_keys = set(examples[0].keys())
            for ex in examples[1:]:
                common_keys &= set(ex.keys())

            if common_keys:
                pattern = DiscoveredPattern(
                    pattern_type="generalized_structural",
                    elements=list(common_keys),
                    confidence=0.5 + len(common_keys) * 0.1,
                    generality_score=self.config.generalization_factor
                )
                self.patterns[pattern.pattern_id] = pattern
                return pattern

        elif all(isinstance(e, (list, tuple)) for e in examples):
            # 寻找共同元素类型
            type_sets = [set(type(item).__name__ for item in ex) for ex in examples]
            common_types = type_sets[0]
            for ts in type_sets[1:]:
                common_types &= ts

            if common_types:
                pattern = DiscoveredPattern(
                    pattern_type="generalized_sequence",
                    elements=list(common_types),
                    confidence=0.5,
                    generality_score=self.config.generalization_factor
                )
                self.patterns[pattern.pattern_id] = pattern
                return pattern

        return None

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            "total_explorations": self.total_explorations,
            "total_trials": self.total_trials,
            "total_imitations": self.total_imitations,
            "patterns_discovered": self.patterns_discovered,
            "patterns_in_memory": len(self.patterns),
            "exploration_rate": self.exploration_rate,
            "learning_rate": self.learning_rate,
            "curiosity_boredom": self.curiosity.boredom_level,
            "action_values_count": len(self.action_values),
            "trial_success_rate": self._calculate_success_rate(),
            "imitation_success_rate": self._calculate_imitation_success_rate(),
        }

    def _calculate_success_rate(self) -> float:
        """计算试错成功率"""
        if not self.trial_history:
            return 0.0
        return sum(1 for t in self.trial_history if t.success) / len(self.trial_history)

    def _calculate_imitation_success_rate(self) -> float:
        """计算模仿成功率"""
        if not self.imitation_records:
            return 0.0
        return sum(1 for r in self.imitation_records if r.success) / len(self.imitation_records)

    def reset(self) -> None:
        """重置学习状态"""
        self.patterns.clear()
        self.pattern_index.clear()
        self.trial_history.clear()
        self.action_outcomes.clear()
        self.action_values.clear()
        self.imitation_records.clear()
        self.observed_behaviors.clear()
        self.behavior_patterns.clear()
        self.known_patterns.clear()
        self.novelty_scores.clear()
        self.exploration_history.clear()
        self.explored_spaces.clear()
        self.curiosity = CuriosityState()
        self.total_explorations = 0
        self.total_trials = 0
        self.total_imitations = 0
        self.patterns_discovered = 0
        logger.info("InfantLearningEngine reset")
