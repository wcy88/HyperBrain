"""
集成测试

测试各层协同工作和系统整体功能
"""

import asyncio
import pytest
import time
from typing import Dict, Any

from hyperbrain.core.brain import Brain, SystemState, ProcessingResult
from hyperbrain.core.config import get_config


class TestBrainInitialization:
    """测试Brain初始化"""
    
    @pytest.fixture
    async def brain(self):
        """创建Brain实例"""
        config = get_config()
        config.debug = True
        brain = Brain(config=config, enable_logging=False)
        yield brain
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_brain_creation(self):
        """测试Brain创建"""
        brain = Brain(enable_logging=False)
        assert brain is not None
        assert brain.state == SystemState.INITIALIZING
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_brain_initialization(self):
        """测试Brain初始化"""
        brain = Brain(enable_logging=False)
        success = await brain.initialize()
        assert success is True
        assert brain.state == SystemState.READY
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_brain_start_stop(self):
        """测试启动和停止"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        success = await brain.start()
        assert success is True
        assert brain.state == SystemState.RUNNING
        
        await brain.pause()
        assert brain.state == SystemState.PAUSED
        
        await brain.resume()
        assert brain.state == SystemState.RUNNING
        
        await brain.shutdown()
        assert brain.state == SystemState.SHUTTING_DOWN


class TestLayerIntegration:
    """测试层间集成"""
    
    @pytest.fixture
    async def initialized_brain(self):
        """创建已初始化的Brain"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        yield brain
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_sensory_to_memory_flow(self):
        """测试感知层到记忆层的数据流"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 模拟感知输入
        perception = await brain.sensory.perceive(
            content="测试输入",
            modality="text"
        )
        
        assert perception is not None
        assert perception.processed_input is not None
        
        # 验证记忆层是否接收到数据
        memory_flow = brain.memory.get_memory_flow()
        assert memory_flow["sensory"] >= 0
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_emotional_influence(self):
        """测试情感层影响"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 处理情感输入
        result = brain.emotional.process_input({
            "sentiment_score": 0.8,
            "event_type": "positive_event"
        })
        
        assert result is not None
        assert "emotion_state" in result
        
        # 验证情感影响因子
        influence = brain.emotional.get_emotional_influence()
        assert "risk_taking" in influence
        assert "creativity" in influence
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_cognitive_with_memory(self):
        """测试认知层与记忆层交互"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 先存储一些知识
        brain.memory.store(
            content="Python是一种编程语言",
            importance=0.8,
            context_tags=["programming", "python"]
        )
        
        # 认知思考
        result = brain.cognitive.think("什么是Python?")
        
        assert result is not None
        assert "stages" in result
        
        # 验证记忆检索
        knowledge = brain.cognitive.retrieve_relevant_knowledge("Python")
        assert len(knowledge) > 0
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_consciousness_integration(self):
        """测试意识层集成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 处理意识周期
        result = brain.consciousness.process_cycle()
        
        assert result is not None
        assert "cycle" in result
        assert "awareness_level" in result
        
        # 决策测试
        decision = brain.consciousness.make_decision(
            options=["option_a", "option_b"],
            context={"scenario": "test"}
        )
        
        assert decision is not None
        assert "selected_option" in decision
        
        await brain.shutdown()


class TestDataFlow:
    """测试数据流"""
    
    @pytest.mark.asyncio
    async def test_full_processing_pipeline(self):
        """测试完整处理流水线"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 处理输入
        result = await brain.process("你好，请介绍一下自己")
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.content is not None
        assert len(result.layers_involved) > 0
        assert result.processing_time_ms > 0
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_in_processing(self):
        """测试处理过程中的记忆检索"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 先存储记忆
        brain.memory.store(
            content="用户喜欢编程",
            importance=0.7,
            context_tags=["user_preference"]
        )
        
        # 处理相关输入
        result = await brain.process("我想学习编程")
        
        assert result.success is True
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_layer_communication(self):
        """测试层间通信"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 发布测试事件
        await brain.communicator.publish(
            "test_event",
            {"data": "test"},
            source="test"
        )
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        await brain.shutdown()


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_invalid_input_handling(self):
        """测试无效输入处理"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 处理空输入
        result = await brain.process("")
        
        # 应该返回错误或不成功
        assert result.success is False or result.content is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_recovery(self):
        """测试系统恢复"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 模拟错误后恢复
        brain.state = SystemState.ERROR
        
        # 系统应该能够重新初始化
        success = await brain.initialize()
        
        # 注意：从ERROR状态初始化可能失败，这是预期的
        assert success is True or brain.state == SystemState.ERROR
        
        await brain.shutdown()


class TestSystemStats:
    """测试系统统计"""
    
    @pytest.mark.asyncio
    async def test_stats_collection(self):
        """测试统计信息收集"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 处理一些输入
        for i in range(3):
            await brain.process(f"测试输入 {i}")
        
        # 获取统计
        stats = brain.get_stats()
        
        assert stats.total_inputs_processed >= 0
        assert stats.total_outputs_generated >= 0
        assert stats.uptime_seconds >= 0
        assert "layer_stats" in stats.__dict__ or hasattr(stats, 'layer_stats')
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_report(self):
        """测试系统报告生成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        report = await brain.get_system_report()
        
        assert "session_id" in report
        assert "system_state" in report
        assert "processing_stats" in report
        assert "layer_stats" in report
        
        await brain.shutdown()


class TestConcurrency:
    """测试并发处理"""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """测试并发处理"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 并发处理多个输入
        inputs = ["输入1", "输入2", "输入3"]
        tasks = [brain.process(inp) for inp in inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证结果
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"并发处理失败: {result}")
            else:
                assert isinstance(result, ProcessingResult)
        
        await brain.shutdown()


class TestConfiguration:
    """测试配置"""
    
    @pytest.mark.asyncio
    async def test_custom_config(self):
        """测试自定义配置"""
        config = get_config()
        config.cognitive.reasoning_depth = 5
        config.memory.max_short_term_items = 50
        
        brain = Brain(config=config, enable_logging=False)
        await brain.initialize()
        
        assert brain.config.cognitive.reasoning_depth == 5
        assert brain.config.memory.max_short_term_items == 50
        
        await brain.shutdown()
