"""
感知系统单元测试

测试范围：
- multimodal_input: 多模态输入处理
- attention: 注意力机制
- context_awareness: 情境感知
- sensory_manager: 感知管理器
"""

import pytest
import asyncio
from datetime import datetime

from hyperbrain.layers.sensory.multimodal_input import (
    MultimodalInputProcessor,
    TextInputProcessor,
    InputModality,
    InputQuality,
    ProcessedInput
)
from hyperbrain.layers.sensory.attention import (
    AttentionMechanism,
    AttentionLevel,
    AttentionStrategy,
    AttentionConfig
)
from hyperbrain.layers.sensory.context_awareness import (
    ContextAwareness,
    TimeOfDay,
    UserEmotionalState,
    EnvironmentType
)
from hyperbrain.layers.sensory.sensory_manager import (
    SensoryManager,
    PerceptionResult,
    SensoryPipelineConfig
)


class TestTextInputProcessor:
    """测试文本输入处理器"""
    
    @pytest.fixture
    def processor(self):
        return TextInputProcessor()
    
    @pytest.mark.asyncio
    async def test_process_text(self, processor):
        result = await processor.process("Hello world, this is a test.")
        
        assert isinstance(result, ProcessedInput)
        assert result.modality == InputModality.TEXT
        assert result.is_valid is True
        assert len(result.normalized_text) > 0
        assert len(result.tokens) > 0
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self, processor):
        result = await processor.process(
            "Contact me at test@example.com or visit https://example.com"
        )
        
        entity_types = [e.entity_type for e in result.entities]
        assert "EMAIL" in entity_types
        assert "URL" in entity_types
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, processor):
        positive = await processor.process("This is great and wonderful!")
        negative = await processor.process("This is terrible and awful!")
        
        assert positive.text_features.sentiment_score > 0
        assert negative.text_features.sentiment_score < 0
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, processor):
        result = await processor.process("Hi")
        
        assert result.quality_score <= 0.6
        assert result.quality_level in (InputQuality.POOR, InputQuality.FAIR, InputQuality.GOOD)
    
    @pytest.mark.asyncio
    async def test_intent_detection(self, processor):
        question = await processor.process("What is the weather today?")
        request = await processor.process("Please help me with this task.")
        
        assert question.text_features.intent == "question"
        assert request.text_features.intent == "request"


class TestMultimodalInputProcessor:
    """测试多模态输入处理器"""
    
    @pytest.fixture
    def processor(self):
        return MultimodalInputProcessor()
    
    @pytest.mark.asyncio
    async def test_process_text(self, processor):
        result = await processor.process("Test message", modality=InputModality.TEXT)
        
        assert result.modality == InputModality.TEXT
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_process_image(self, processor):
        result = await processor.process(
            "data:image/png;base64,iVBORw0KGgo=",
            modality=InputModality.IMAGE
        )
        
        assert result.modality == InputModality.IMAGE
        assert result.image_features is not None
    
    @pytest.mark.asyncio
    async def test_process_batch(self, processor):
        inputs = [
            ("Text 1", InputModality.TEXT, "user"),
            ("Text 2", InputModality.TEXT, "user"),
        ]
        results = await processor.process_batch(inputs)
        
        assert len(results) == 2
        assert all(r.is_valid for r in results)
    
    def test_stats(self, processor):
        stats = processor.get_stats()
        
        assert "total_processed" in stats
        assert "valid_rate" in stats


class TestAttentionMechanism:
    """测试注意力机制"""
    
    @pytest.fixture
    def attention(self):
        return AttentionMechanism()
    
    def test_focus_word_level(self, attention):
        text = "The quick brown fox jumps over the lazy dog."
        result = attention.focus(text, level=AttentionLevel.WORD)
        
        assert len(result.regions) > 0
        assert all(r.level == AttentionLevel.WORD for r in result.regions)
    
    def test_focus_sentence_level(self, attention):
        text = "First sentence. Second sentence. Third sentence."
        result = attention.focus(text, level=AttentionLevel.SENTENCE)
        
        assert len(result.regions) >= 3
        assert all(r.level == AttentionLevel.SENTENCE for r in result.regions)
    
    def test_focused_text(self, attention):
        text = "Important information here. Less important there."
        result = attention.focus(text, level=AttentionLevel.SENTENCE)
        focused = result.get_focused_text(threshold=0.3)
        
        assert len(focused) > 0
    
    def test_summary(self, attention):
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        summary = attention.get_summary(text, max_sentences=2)
        
        assert len(summary) > 0
    
    def test_filter_irrelevant(self, attention):
        text = "Important topic. Another important point. Some filler text."
        filtered = attention.filter_irrelevant(text, threshold=0.3)
        
        assert len(filtered) > 0
    
    def test_visualize(self, attention):
        text = "Test visualization of attention mechanism."
        result = attention.focus(text)
        visualization = attention.visualize_attention(result)
        
        assert "Attention Visualization" in visualization
        assert len(visualization) > 0


class TestContextAwareness:
    """测试情境感知"""
    
    @pytest.fixture
    def context(self):
        return ContextAwareness()
    
    def test_initialize_context(self, context):
        result = context.initialize_context(user_id="test_user")
        
        assert result is not None
        assert result.user_state.user_id == "test_user"
    
    def test_time_context(self, context):
        context.initialize_context()
        time_ctx = context.get_current_context().time_context
        
        assert time_ctx.time_of_day in TimeOfDay
        assert 0 <= time_ctx.day_of_week <= 6
    
    def test_update_emotion(self, context):
        context.initialize_context(user_id="test_user")
        emotion = context.user_tracker.update_emotion("test_user", "I am so happy today!")
        
        assert emotion == UserEmotionalState.HAPPY
    
    def test_dialogue_context(self, context):
        context.initialize_context()
        context.update_context(user_input="Hello", intent="greeting")
        context.update_context(assistant_response="Hi there!")
        
        dialogue = context.get_current_context().dialogue_context
        assert len(dialogue.turns) == 2
    
    def test_context_summary(self, context):
        context.initialize_context()
        summary = context.get_context_summary()
        
        assert "time" in summary
        assert "user" in summary
        assert "dialogue" in summary
    
    def test_greeting_context(self, context):
        context.initialize_context()
        greeting = context.get_greeting_context()
        
        assert len(greeting) > 0


class TestSensoryManager:
    """测试感知管理器"""
    
    @pytest.fixture
    async def manager(self):
        mgr = SensoryManager()
        await mgr.initialize()
        return mgr
    
    @pytest.mark.asyncio
    async def test_perceive_text(self):
        manager = SensoryManager()
        await manager.initialize()
        
        result = await manager.perceive("This is a test message.")
        
        assert isinstance(result, PerceptionResult)
        assert result.processed_input.is_valid is True
        assert len(result.key_information) > 0
    
    @pytest.mark.asyncio
    async def test_perceive_with_attention(self):
        manager = SensoryManager()
        await manager.initialize()
        
        result = await manager.perceive(
            "Important: This is critical information. Also some other text."
        )
        
        assert result.attention_map is not None
        assert len(result.attention_map.regions) > 0
    
    @pytest.mark.asyncio
    async def test_perceive_batch(self):
        manager = SensoryManager()
        await manager.initialize()
        
        inputs = [
            ("Message 1", InputModality.TEXT, "user"),
            ("Message 2", InputModality.TEXT, "user"),
        ]
        results = await manager.perceive_batch(inputs)
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_get_attention_summary(self):
        manager = SensoryManager()
        await manager.initialize()
        
        summary = manager.get_attention_summary(
            "First point. Second point. Third point.",
            max_sentences=2
        )
        
        assert len(summary) > 0
    
    @pytest.mark.asyncio
    async def test_context_integration(self):
        manager = SensoryManager()
        await manager.initialize(user_id="test_user")
        
        await manager.perceive("Hello, how are you?")
        summary = manager.get_context_summary()
        
        assert "user" in summary
        assert "dialogue" in summary
    
    def test_stats(self):
        manager = SensoryManager()
        stats = manager.get_stats()
        
        assert "perception_history_size" in stats
        assert "memory_connected" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
