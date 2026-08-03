"""
稳定性测试

测试系统长时间运行、错误恢复和边界条件处理
"""

import asyncio
import pytest
import time
from typing import List

from hyperbrain.core.brain import Brain, SystemState


class TestLongRunning:
    """长时间运行测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_continuous_operation(self):
        """测试持续运行"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 模拟持续运行一段时间
        num_cycles = 20
        success_count = 0
        
        for i in range(num_cycles):
            try:
                result = await brain.process(f"持续运行测试 {i}")
                if result.success:
                    success_count += 1
                
                # 模拟正常间隔
                await asyncio.sleep(0.1)
                
            except Exception as e:
                pytest.fail(f"持续运行中断: {e}")
        
        # 成功率应高于90%
        success_rate = success_count / num_cycles
        assert success_rate >= 0.9, f"成功率 {success_rate*100:.1f}% 低于90%"
        
        # 系统状态应仍为运行中
        assert brain.state == SystemState.RUNNING
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_growth_over_time(self):
        """测试长时间运行的内存增长"""
        try:
            import psutil
            import os
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        memory_readings = []
        
        if has_psutil:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024
            memory_readings = [initial_memory]
        
        # 运行多个周期
        for i in range(10):
            await brain.process(f"内存测试 {i}")
            
            # 每5次记录一次内存
            if has_psutil and i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory)
            
            await asyncio.sleep(0.1)
        
        # 分析内存趋势
        if has_psutil and len(memory_readings) >= 2:
            memory_growth = memory_readings[-1] - memory_readings[0]
            # 内存增长应相对稳定
            assert memory_growth < 50, f"内存增长 {memory_growth:.1f}MB，可能存在内存泄漏"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_background_tasks_stability(self):
        """测试后台任务稳定性"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 等待后台任务运行一段时间
        await asyncio.sleep(2)
        
        # 系统应仍在运行
        assert brain.state == SystemState.RUNNING
        
        # 处理输入应正常工作
        result = await brain.process("后台任务测试")
        assert result.success is True
        
        await brain.shutdown()


class TestErrorRecovery:
    """错误恢复测试"""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """测试优雅降级"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 处理正常输入
        result1 = await brain.process("正常输入")
        assert result1.success is True
        
        # 处理可能导致问题的输入
        problematic_inputs = [
            "",  # 空输入
            "a" * 10000,  # 超长输入
            "\x00\x01\x02",  # 特殊字符
            "<script>alert('xss')</script>",  # 潜在XSS
        ]
        
        for inp in problematic_inputs:
            try:
                result = await brain.process(inp)
                # 不应崩溃，可以失败但不应抛出异常
                assert result is not None
            except Exception as e:
                pytest.fail(f"处理异常输入时崩溃: {e}")
        
        # 系统应仍能处理正常输入
        result2 = await brain.process("再次正常输入")
        assert result2.success is True
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_state_consistency(self):
        """测试系统状态一致性"""
        brain = Brain(enable_logging=False)
        
        # 初始状态
        assert brain.state == SystemState.INITIALIZING
        
        # 初始化后
        await brain.initialize()
        assert brain.state == SystemState.READY
        
        # 启动后
        await brain.start()
        assert brain.state == SystemState.RUNNING
        
        # 暂停后
        await brain.pause()
        assert brain.state == SystemState.PAUSED
        
        # 恢复后
        await brain.resume()
        assert brain.state == SystemState.RUNNING
        
        # 关闭后
        await brain.shutdown()
        assert brain.state == SystemState.SHUTTING_DOWN
    
    @pytest.mark.asyncio
    async def test_multiple_init_cycles(self):
        """测试多次初始化循环"""
        brain = Brain(enable_logging=False)
        
        for i in range(3):
            success = await brain.initialize()
            assert success is True
            
            await brain.start()
            assert brain.state == SystemState.RUNNING
            
            result = await brain.process(f"初始化循环测试 {i}")
            assert result.success is True
            
            await brain.shutdown()
            assert brain.state == SystemState.SHUTTING_DOWN
    
    @pytest.mark.asyncio
    async def test_shutdown_during_processing(self):
        """测试处理过程中关闭"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 启动一个长时间处理
        task = asyncio.create_task(brain.process("这是一个需要一些时间的处理"))
        
        # 立即关闭
        await asyncio.sleep(0.1)
        await brain.shutdown()
        
        # 等待任务完成或取消
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        
        # 系统应已关闭
        assert brain.state == SystemState.SHUTTING_DOWN


class TestBoundaryConditions:
    """边界条件测试"""
    
    @pytest.mark.asyncio
    async def test_empty_system_operations(self):
        """测试空系统操作"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 空记忆检索
        results = brain.memory.retrieve(query="不存在的查询")
        assert results is not None
        
        # 空情感状态
        emotion = brain.emotional.get_current_emotion()
        # 可能为None或默认值
        
        # 空认知思考
        result = brain.cognitive.think("")
        assert result is not None
        
        # 空意识周期
        cycle_result = brain.consciousness.process_cycle()
        assert cycle_result is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_extreme_values(self):
        """测试极端值"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 极高重要性
        brain.memory.store(
            content="极高重要性记忆",
            importance=1.0
        )
        
        # 极低重要性
        brain.memory.store(
            content="极低重要性记忆",
            importance=0.0
        )
        
        # 验证系统仍能正常工作
        result = await brain.process("极端值测试")
        assert result is not None
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_rapid_state_changes(self):
        """测试快速状态变化"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 快速切换状态
        for _ in range(5):
            await brain.start()
            await brain.pause()
            await brain.resume()
        
        # 系统应保持稳定
        assert brain.state in [SystemState.RUNNING, SystemState.PAUSED]
        
        await brain.shutdown()


class TestResourceCleanup:
    """资源清理测试"""
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_on_shutdown(self):
        """测试关闭时的内存清理"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 存储一些数据
        for i in range(10):
            brain.memory.store(
                content=f"清理测试数据 {i}",
                importance=0.5
            )
        
        # 记录关闭前的记忆数量
        flow_before = brain.memory.get_memory_flow()
        
        # 关闭
        await brain.shutdown()
        
        # 验证系统已关闭
        assert brain.state == SystemState.SHUTTING_DOWN
    
    @pytest.mark.asyncio
    async def test_database_connection_cleanup(self):
        """测试数据库连接清理"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 进行一些数据库操作
        brain.db.insert_conversation(
            conversation_id="cleanup_test",
            session_id="test",
            role="user",
            content="清理测试"
        )
        
        # 关闭
        await brain.shutdown()
        
        # 验证可以创建新实例（说明资源已释放）
        brain2 = Brain(enable_logging=False)
        await brain2.initialize()
        
        result = brain2.db.get_conversation_history("test")
        assert result is not None
        
        await brain2.shutdown()


class TestConcurrentStability:
    """并发稳定性测试"""
    
    @pytest.mark.asyncio
    async def test_stress_test(self):
        """压力测试"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        num_requests = 20
        tasks = []
        
        # 快速发起多个请求
        for i in range(num_requests):
            task = brain.process(f"压力测试 {i}")
            tasks.append(task)
        
        # 等待所有请求完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        from hyperbrain.core.brain import ProcessingResult
        success_count = sum(
            1 for r in results
            if isinstance(r, ProcessingResult) and r.success
        )
        
        # 大部分请求应成功
        assert success_count >= num_requests * 0.8, f"成功率过低: {success_count}/{num_requests}"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_mixed_workload(self):
        """混合负载测试"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        async def processing_task():
            result = await brain.process("处理任务")
            return result.success
        
        async def memory_task():
            brain.memory.store(
                content="内存任务",
                importance=0.5
            )
            return True
        
        async def cognitive_task():
            result = brain.cognitive.think("认知任务")
            return result is not None
        
        # 混合执行
        tasks = []
        for i in range(10):
            if i % 3 == 0:
                tasks.append(processing_task())
            elif i % 3 == 1:
                tasks.append(memory_task())
            else:
                tasks.append(cognitive_task())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证没有异常
        for result in results:
            assert not isinstance(result, Exception), f"混合负载测试中出现异常: {result}"
        
        await brain.shutdown()


class TestDataIntegrity:
    """数据完整性测试"""
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """测试记忆持久性"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 存储记忆
        test_content = "持久性测试内容"
        brain.memory.store(
            content=test_content,
            importance=0.8,
            context_tags=["persistence_test"]
        )
        
        # 检索记忆
        results = brain.memory.retrieve(query="持久性测试")
        
        # 验证能检索到
        assert len(results) > 0
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_conversation_history_integrity(self):
        """测试对话历史完整性"""
        import uuid
        brain = Brain(enable_logging=False)
        await brain.initialize()

        session_id = brain.get_session_id()

        # 插入对话（使用 UUID 避免与旧数据主键冲突）
        cid1 = f"hist_{uuid.uuid4().hex[:8]}"
        cid2 = f"hist_{uuid.uuid4().hex[:8]}"
        brain.db.insert_conversation(
            conversation_id=cid1,
            session_id=session_id,
            role="user",
            content="历史测试1"
        )
        brain.db.insert_conversation(
            conversation_id=cid2,
            session_id=session_id,
            role="assistant",
            content="历史测试2"
        )

        # 检索对话
        history = brain.db.get_conversation_history(session_id)

        # 验证完整性
        assert len(history) >= 2

        await brain.shutdown()
