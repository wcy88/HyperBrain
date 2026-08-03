"""
端到端测试

测试完整的对话流程和系统整体功能
"""

import asyncio
import pytest
from typing import List, Dict, Any

from hyperbrain.core.brain import Brain, ProcessingResult


class TestConversationFlow:
    """测试完整对话流程"""
    
    @pytest.fixture
    async def brain(self):
        """创建并初始化Brain"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        yield brain
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_simple_conversation(self):
        """测试简单对话"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 第一轮对话
        result1 = await brain.process("你好")
        assert result1.success is True
        assert result1.content is not None
        
        # 第二轮对话
        result2 = await brain.process("今天怎么样")
        assert result2.success is True
        
        # 第三轮对话
        result3 = await brain.process("再见")
        assert result3.success is True
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_context_awareness(self):
        """测试上下文感知"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 建立上下文
        await brain.process("我喜欢Python编程")
        
        # 测试上下文延续
        result = await brain.process("Python有什么优点")
        
        assert result.success is True
        # 响应中应该包含与Python相关的内容
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """测试多轮对话"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        conversation = [
            "你好，我是新用户",
            "我想了解人工智能",
            "人工智能有哪些应用",
            "机器学习是AI的一部分吗",
            "谢谢你的解释",
        ]
        
        results = []
        for user_input in conversation:
            result = await brain.process(user_input)
            results.append(result)
            assert result.success is True
        
        # 验证所有轮次都成功
        assert len(results) == len(conversation)
        assert all(r.success for r in results)
        
        # 验证记忆中有对话记录
        stats = brain.get_stats()
        assert stats.total_inputs_processed >= len(conversation)
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_emotional_conversation(self):
        """测试情感对话"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 积极情感
        result1 = await brain.process("我今天很开心！")
        assert result1.success is True
        
        # 检查情感状态
        emotion1 = brain.get_emotional_state()
        assert emotion1 is not None
        
        # 消极情感
        result2 = await brain.process("我有点难过")
        assert result2.success is True
        
        # 检查情感变化
        emotion2 = brain.get_emotional_state()
        assert emotion2 is not None
        
        await brain.shutdown()


class TestSystemCommands:
    """测试系统命令"""
    
    @pytest.mark.asyncio
    async def test_think_command(self):
        """测试思考命令"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        result = await brain.think("如何解决复杂问题")
        
        assert result is not None
        assert "stages" in result
        assert "problem" in result
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_learn_command(self):
        """测试学习命令"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        result = await brain.learn("Python是一种高级编程语言")
        
        assert result is not None
        assert hasattr(result, 'success')
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_reflect_command(self):
        """测试反思命令"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 先进行一些交互
        await brain.process("测试输入")
        
        # 执行反思
        result = await brain.reflect()
        
        assert result is not None
        assert "self_description" in result
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_evolve_command(self):
        """测试进化命令"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        result = await brain.evolve()
        
        # 进化可能返回None（如果配置为不自动进化）
        if result is not None:
            assert hasattr(result, 'cycle_id')
        
        await brain.shutdown()


class TestSystemQueries:
    """测试系统查询"""
    
    @pytest.mark.asyncio
    async def test_stats_query(self):
        """测试统计查询"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 进行一些处理
        await brain.process("统计测试")
        
        # 获取统计
        stats = brain.get_stats()
        
        assert stats.system_state is not None
        assert stats.total_inputs_processed >= 1
        assert stats.uptime_seconds >= 0
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_report(self):
        """测试系统报告"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        report = await brain.get_system_report()
        
        assert "session_id" in report
        assert "system_state" in report
        assert "processing_stats" in report
        assert "layer_stats" in report
        
        # 验证各层统计
        layer_stats = report["layer_stats"]
        expected_layers = [
            "sensory", "memory", "cognitive", "learning",
            "evolution", "emotional", "execution", "consciousness"
        ]
        for layer in expected_layers:
            assert layer in layer_stats, f"缺少 {layer} 层统计"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_summary(self):
        """测试记忆摘要"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 存储一些记忆
        brain.memory.store(
            content="测试记忆1",
            importance=0.7
        )
        brain.memory.store(
            content="测试记忆2",
            importance=0.5
        )
        
        summary = brain.get_memory_summary()
        
        assert "flow" in summary
        assert "stats" in summary
        
        await brain.shutdown()


class TestErrorScenarios:
    """测试错误场景"""
    
    @pytest.mark.asyncio
    async def test_empty_input(self):
        """测试空输入"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        result = await brain.process("")
        
        # 空输入可能失败，但不应崩溃
        assert result is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_very_long_input(self):
        """测试超长输入"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        long_input = "测试 " * 1000  # 约5000字符
        
        result = await brain.process(long_input)
        
        # 超长输入可能失败，但不应崩溃
        assert result is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """测试特殊字符"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        special_inputs = [
            "!@#$%^&*()",
            "<html>test</html>",
            "SELECT * FROM users",
            "\n\t\r",
            "🎉🎊🎁",
        ]
        
        for inp in special_inputs:
            result = await brain.process(inp)
            assert result is not None, f"处理特殊字符时崩溃: {inp[:20]}"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_rapid_fire_inputs(self):
        """测试快速连续输入"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        inputs = [f"快速输入 {i}" for i in range(10)]
        
        # 快速连续处理
        for inp in inputs:
            result = await brain.process(inp)
            assert result is not None
        
        await brain.shutdown()


class TestSystemLifecycle:
    """测试系统生命周期"""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """测试完整生命周期"""
        brain = Brain(enable_logging=False)
        
        # 创建
        assert brain.state.value == "initializing"
        
        # 初始化
        success = await brain.initialize()
        assert success is True
        assert brain.state.value == "ready"
        
        # 启动
        await brain.start()
        assert brain.state.value == "running"
        
        # 处理
        result = await brain.process("生命周期测试")
        assert result.success is True
        
        # 暂停
        await brain.pause()
        assert brain.state.value == "paused"
        
        # 恢复
        await brain.resume()
        assert brain.state.value == "running"
        
        # 关闭
        await brain.shutdown()
        assert brain.state.value == "shutting_down"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        async with Brain(enable_logging=False).session() as brain:
            assert brain.state.value == "running"
            
            result = await brain.process("上下文管理器测试")
            assert result.success is True
        
        # 退出上下文后应已关闭
        # 注意：由于session()是asynccontextmanager，brain实例仍然存在
        # 但状态应该是 shutting_down
    
    @pytest.mark.asyncio
    async def test_session_id_persistence(self):
        """测试会话ID持久性"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        session_id = brain.get_session_id()
        
        # 验证会话ID不为空
        assert session_id is not None
        assert len(session_id) > 0
        
        # 在会话期间保持不变
        await brain.start()
        assert brain.get_session_id() == session_id
        
        await brain.process("会话测试")
        assert brain.get_session_id() == session_id
        
        await brain.shutdown()


class TestIntegrationWithLayers:
    """测试与各层集成"""
    
    @pytest.mark.asyncio
    async def test_sensory_layer_integration(self):
        """测试感知层集成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 直接测试感知层
        perception = await brain.sensory.perceive(
            content="感知层测试",
            modality="text"
        )
        
        assert perception is not None
        assert perception.processed_input is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_cognitive_layer_integration(self):
        """测试认知层集成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 测试推理
        result = brain.cognitive.reason(
            premises=["所有人都是凡人", "苏格拉底是人"],
            reasoning_type="deductive",
            question="苏格拉底是凡人吗"
        )
        
        assert result is not None
        assert result.conclusion is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_emotional_layer_integration(self):
        """测试情感层集成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 处理情感输入
        result = brain.emotional.process_input({
            "sentiment_score": 0.9,
            "event_type": "achievement"
        })
        
        assert result is not None
        assert "emotion_state" in result
        
        # 获取情感影响
        influence = brain.emotional.get_emotional_influence()
        assert "risk_taking" in influence
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_consciousness_layer_integration(self):
        """测试意识层集成"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 处理意识周期
        result = brain.consciousness.process_cycle()
        
        assert result is not None
        assert "cycle" in result
        
        # 测试决策
        decision = brain.consciousness.make_decision(
            options=["学习", "休息", "工作"]
        )
        
        assert decision is not None
        assert "selected_option" in decision
        
        await brain.shutdown()


class TestDataPersistence:
    """测试数据持久化"""
    
    @pytest.mark.asyncio
    async def test_conversation_persistence(self):
        """测试对话持久化"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        session_id = brain.get_session_id()
        
        # 进行对话
        await brain.process("持久化测试1")
        await brain.process("持久化测试2")
        
        # 查询历史
        history = brain.db.get_conversation_history(session_id)
        
        # 验证有记录
        assert len(history) >= 2
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_operations(self):
        """测试跨操作的记忆持久化"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 存储记忆
        brain.memory.store(
            content="跨操作测试记忆",
            importance=0.8,
            context_tags=["persistence"]
        )
        
        # 进行其他操作
        await brain.process("其他操作")
        
        # 检索之前的记忆
        results = brain.memory.retrieve(query="跨操作测试")
        
        # 验证记忆仍然存在
        assert len(results) > 0
        
        await brain.shutdown()
