"""
情感系统单元测试

测试情感生成、表达、记忆、调节、共情和管理器的功能。
"""

import pytest
import time
from typing import Dict, Any

from hyperbrain.layers.emotional.emotion_generation import (
    EmotionGenerator, PlutchikEmotion, PADEmotion, EmotionGenerationConfig,
    PlutchikEmotionType, EmotionState
)
from hyperbrain.layers.emotional.emotion_expression import (
    EmotionExpresser, ExpressionConfig, ExpressionStyle, ExpressionIntensity
)
from hyperbrain.layers.emotional.emotion_memory import (
    EmotionalMemory, EmotionalMemoryConfig, RetrievalQuery
)
from hyperbrain.layers.emotional.emotion_regulation import (
    EmotionRegulator, EmotionRegulationConfig, RegulationStrategy, RegulationTarget
)
from hyperbrain.layers.emotional.empathy import (
    EmpathyEngine, EmpathyConfig, EmpathyLevel, EmpathyType
)
from hyperbrain.layers.emotional.emotion_manager import EmotionManager


class TestEmotionGeneration:
    """测试情感生成模块"""

    def test_plutchik_creation(self):
        """测试Plutchik情感创建"""
        emotion = PlutchikEmotion(joy=0.8, sadness=0.2)
        assert emotion.joy == 0.8
        assert emotion.sadness == 0.2
        assert emotion.anger == 0.0

    def test_plutchik_dominant(self):
        """测试主导情感获取"""
        emotion = PlutchikEmotion(joy=0.8, trust=0.3)
        dominant, intensity = emotion.get_dominant()
        assert dominant == "joy"
        assert intensity == 0.8

    def test_pad_creation(self):
        """测试PAD情感创建"""
        pad = PADEmotion(pleasure=0.5, arousal=0.3, dominance=0.1)
        assert pad.pleasure == 0.5
        assert pad.arousal == 0.3
        assert pad.dominance == 0.1

    def test_pad_from_plutchik(self):
        """测试从Plutchik到PAD的转换"""
        plutchik = PlutchikEmotion(joy=1.0)
        pad = PADEmotion.from_plutchik(plutchik)
        assert pad.pleasure > 0

    def test_generator_creation(self):
        """测试生成器创建"""
        config = EmotionGenerationConfig(base_intensity=0.5)
        generator = EmotionGenerator(config=config)
        assert generator.config.base_intensity == 0.5

    def test_generate_from_sentiment(self):
        """测试基于情感分数生成"""
        generator = EmotionGenerator()
        state = generator.generate_from_sentiment(sentiment_score=0.8, intensity=1.0)
        assert state.get_valence() > 0
        assert state.plutchik.joy > 0

    def test_generate_from_event(self):
        """测试基于事件生成"""
        generator = EmotionGenerator()
        state = generator.generate_from_event(
            event_type="success",
            event_data={"intensity": 0.9}
        )
        assert state.plutchik.joy > 0

    def test_calculate_intensity(self):
        """测试强度计算"""
        generator = EmotionGenerator()
        intensity = generator.calculate_intensity(
            "joy",
            {"unexpectedness": 0.5, "personal_relevance": 0.8}
        )
        assert 0.0 <= intensity <= 1.0

    def test_blend_emotions(self):
        """测试情感混合"""
        generator = EmotionGenerator()
        blend = generator.blend_emotions("joy", "trust", 0.8, 0.6)
        assert blend.primary in ["joy", "trust"]
        assert blend.blend_name == "love"

    def test_transition_emotion(self):
        """测试情感过渡"""
        generator = EmotionGenerator()
        result = generator.transition_emotion("joy", "sadness", 0.5)
        assert isinstance(result, PlutchikEmotion)

    def test_opposite_inhibition(self):
        """测试对立情感抑制"""
        generator = EmotionGenerator()
        plutchik = PlutchikEmotion(joy=0.9, sadness=0.5)
        result = generator.apply_opposite_inhibition(plutchik)
        assert result.sadness < plutchik.sadness


class TestEmotionExpression:
    """测试情感表达模块"""

    def test_expresser_creation(self):
        """测试表达器创建"""
        config = ExpressionConfig(enable_emojis=False)
        expresser = EmotionExpresser(config=config)
        assert expresser.config.enable_emojis is False

    def test_express(self):
        """测试情感表达"""
        expresser = EmotionExpresser()
        result = expresser.express("你好", emotion="joy", style=ExpressionStyle.ENTHUSIASTIC)
        assert result.original_text == "你好"
        assert result.applied_style == ExpressionStyle.ENTHUSIASTIC

    def test_adjust_style(self):
        """测试风格调整"""
        expresser = EmotionExpresser()
        adjusted = expresser.adjust_style("你好~", ExpressionStyle.FORMAL)
        assert "。" in adjusted

    def test_select_emojis(self):
        """测试表情符号选择"""
        expresser = EmotionExpresser()
        emojis = expresser.select_emojis("joy", 2)
        assert len(emojis) <= 2

    def test_control_intensity(self):
        """测试强度控制"""
        expresser = EmotionExpresser()
        controlled = expresser.control_intensity("太好了！", ExpressionIntensity.SUBTLE)
        assert "！" not in controlled

    def test_expression_profile(self):
        """测试表达配置文件"""
        expresser = EmotionExpresser()
        profile = expresser.create_expression_profile("joy", ExpressionStyle.CASUAL, ExpressionIntensity.MODERATE)
        assert profile.emotion == "joy"
        assert profile.style == ExpressionStyle.CASUAL


class TestEmotionMemory:
    """测试情感记忆模块"""

    def test_memory_creation(self):
        """测试记忆系统创建"""
        config = EmotionalMemoryConfig(max_entries=500)
        memory = EmotionalMemory(config=config)
        assert memory.config.max_entries == 500

    def test_store_and_retrieve(self):
        """测试存储和检索"""
        memory = EmotionalMemory()
        entry = memory.store(
            event_description="测试事件",
            emotional_state={"joy": 0.8},
            valence=0.8,
            arousal=0.5
        )
        assert entry.event_description == "测试事件"

        retrieved = memory.retrieve_by_emotion("joy")
        assert len(retrieved) > 0

    def test_retrieve_by_valence(self):
        """测试按效价检索"""
        memory = EmotionalMemory()
        memory.store(
            event_description="正面事件",
            emotional_state={"joy": 0.8},
            valence=0.8
        )
        results = memory.retrieve_by_valence((0.5, 1.0))
        assert len(results) > 0

    def test_retrieve_similar(self):
        """测试相似检索"""
        memory = EmotionalMemory()
        memory.store(
            event_description="事件1",
            emotional_state={"joy": 0.8, "trust": 0.3}
        )
        results = memory.retrieve_similar({"joy": 0.7, "trust": 0.2})
        assert len(results) > 0

    def test_reinforce(self):
        """测试记忆强化"""
        memory = EmotionalMemory()
        entry = memory.store(
            event_description="重要事件",
            emotional_state={"joy": 0.9}
        )
        original_intensity = entry.intensity
        memory.reinforce(entry.id)
        assert entry.intensity > original_intensity

    def test_decay(self):
        """测试记忆衰减"""
        memory = EmotionalMemory()
        memory.store(
            event_description="旧事件",
            emotional_state={"joy": 0.5}
        )
        removed = memory.decay_all()
        assert removed >= 0

    def test_emotional_summary(self):
        """测试情感摘要"""
        memory = EmotionalMemory()
        memory.store(
            event_description="事件",
            emotional_state={"joy": 0.8},
            valence=0.8
        )
        summary = memory.get_emotional_summary()
        assert summary["count"] > 0


class TestEmotionRegulation:
    """测试情感调节模块"""

    def test_regulator_creation(self):
        """测试调节器创建"""
        config = EmotionRegulationConfig(recovery_rate=0.1)
        regulator = EmotionRegulator(config=config)
        assert regulator.config.recovery_rate == 0.1

    def test_regulate(self):
        """测试情感调节"""
        regulator = EmotionRegulator()
        current = {"valence": 0.8, "arousal": 0.9, "dominance": 0.5}
        target = {"valence": 0.2, "arousal": 0.3, "dominance": 0.0}
        result = regulator.regulate(current, target)
        assert result["valence"] < current["valence"]

    def test_maintain_stability(self):
        """测试稳定性维护"""
        regulator = EmotionRegulator()
        history = [
            {"valence": 0.5, "arousal": 0.3},
            {"valence": 0.6, "arousal": 0.4},
            {"valence": 0.4, "arousal": 0.3},
        ]
        result = regulator.maintain_stability(history)
        assert "stable" in result

    def test_process_negative_emotion(self):
        """测试负面情感处理"""
        regulator = EmotionRegulator()
        state = {"valence": -0.8, "arousal": 0.6, "dominance": 0.0}
        result = regulator.process_negative_emotion(state, "sadness")
        assert result["valence"] > state["valence"]

    def test_recover(self):
        """测试情感恢复"""
        regulator = EmotionRegulator()
        current = {"valence": 0.9, "arousal": 0.9, "dominance": 0.8}
        result = regulator.recover(current)
        assert result["valence"] < current["valence"]

    def test_balance_emotions(self):
        """测试情感平衡"""
        regulator = EmotionRegulator()
        state = {"valence": 0.9, "arousal": 0.9}
        result = regulator.balance_emotions(state)
        assert result["valence"] <= state["valence"]

    def test_auto_regulate(self):
        """测试自动调节"""
        regulator = EmotionRegulator()
        state = {"valence": 0.9, "arousal": 0.9}
        result = regulator.auto_regulate(state)
        assert result is not None

        stable_state = {"valence": 0.2, "arousal": 0.3}
        result = regulator.auto_regulate(stable_state)
        assert result is None


class TestEmpathy:
    """测试共情模块"""

    def test_empathy_creation(self):
        """测试共情引擎创建"""
        config = EmpathyConfig(resonance_threshold=0.6)
        empathy = EmpathyEngine(config=config)
        assert empathy.config.resonance_threshold == 0.6

    def test_understand_emotion(self):
        """测试情感理解"""
        empathy = EmpathyEngine()
        result = empathy.understand_emotion("sadness", 0.7)
        assert result["detected_emotion"] == "sadness"
        assert "likely_causes" in result

    def test_mirror_emotion(self):
        """测试情感镜像"""
        empathy = EmpathyEngine()
        result = empathy.mirror_emotion("joy", 0.8)
        assert result["valence"] > 0
        assert result["mirrored_emotion"] == "joy"

    def test_generate_empathy_response(self):
        """测试共情响应生成"""
        empathy = EmpathyEngine()
        response = empathy.generate_empathy_response("sadness", 0.7)
        assert response.empathy_level in [EmpathyLevel.HIGH, EmpathyLevel.MODERATE]
        assert len(response.response_text) > 0

    def test_detect_resonance(self):
        """测试情感共鸣检测"""
        empathy = EmpathyEngine()
        own_state = {"valence": 0.8, "arousal": 0.6}
        resonance = empathy.detect_resonance("joy", 0.8, own_state)
        assert 0.0 <= resonance <= 1.0

    def test_adjust_empathy_level(self):
        """测试共情程度调节"""
        empathy = EmpathyEngine()
        situation = {"urgency": 0.8, "familiarity": 0.6}
        level = empathy.adjust_empathy_level(EmpathyLevel.LOW, situation)
        assert level in [EmpathyLevel.MODERATE, EmpathyLevel.HIGH]


class TestEmotionManager:
    """测试情感管理器"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = EmotionManager()
        assert manager.generator is not None
        assert manager.expresser is not None
        assert manager.memory is not None
        assert manager.regulator is not None
        assert manager.empathy is not None

    def test_process_input(self):
        """测试输入处理"""
        manager = EmotionManager()
        result = manager.process_input({
            "sentiment_score": 0.8,
            "intensity": 1.0,
            "context": {"trigger": "praise"}
        })
        assert "emotion_state" in result
        assert "dominant_emotion" in result

    def test_express(self):
        """测试表达功能"""
        manager = EmotionManager()
        manager.process_input({"sentiment_score": 0.8})
        result = manager.express("这是一个好消息")
        assert result.original_text == "这是一个好消息"

    def test_empathize(self):
        """测试共情功能"""
        manager = EmotionManager()
        response = manager.empathize("sadness", 0.6)
        assert response.response_text is not None

    def test_regulate(self):
        """测试调节功能"""
        manager = EmotionManager()
        manager.process_input({"sentiment_score": 0.9})
        result = manager.regulate()
        assert isinstance(result, dict)

    def test_get_current_emotion(self):
        """测试获取当前情感"""
        manager = EmotionManager()
        manager.process_input({"sentiment_score": 0.5})
        current = manager.get_current_emotion()
        assert current is not None
        assert "valence" in current

    def test_get_emotional_influence(self):
        """测试获取情感影响因子"""
        manager = EmotionManager()
        manager.process_input({"sentiment_score": 0.5})
        influence = manager.get_emotional_influence()
        assert "risk_taking" in influence
        assert "creativity" in influence

    def test_store_and_retrieve_memory(self):
        """测试记忆存储和检索"""
        manager = EmotionManager()
        entry = manager.store_emotional_memory("测试事件", {"joy": 0.8})
        assert entry is not None

        memories = manager.retrieve_emotional_memories(emotion_type="joy")
        assert len(memories) > 0

    def test_get_stats(self):
        """测试统计信息"""
        manager = EmotionManager()
        stats = manager.get_stats()
        assert "generation" in stats
        assert "expression" in stats
        assert "memory" in stats
        assert "regulation" in stats
        assert "empathy" in stats

    def test_get_emotional_report(self):
        """测试情感报告"""
        manager = EmotionManager()
        manager.process_input({"sentiment_score": 0.5})
        report = manager.get_emotional_report()
        assert "current_state" in report
        assert "influence_on_cognition" in report
