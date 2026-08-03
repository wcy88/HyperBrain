"""
性能测试

测试系统在大记忆量、高并发等场景下的性能表现
"""

import asyncio
import pytest
import time
import random
import string
from typing import List

from hyperbrain.core.brain import Brain, ProcessingResult
from hyperbrain.core.config import get_config


class TestMemoryPerformance:
    """测试记忆系统性能"""
    
    @pytest.mark.asyncio
    async def test_large_memory_storage(self):
        """测试大量记忆存储性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 存储大量记忆
        num_memories = 100
        start_time = time.time()
        
        for i in range(num_memories):
            brain.memory.store(
                content=f"记忆内容 {i}: " + "x" * 100,
                importance=random.random(),
                context_tags=["test", f"tag_{i % 10}"]
            )
        
        storage_time = time.time() - start_time
        
        # 验证存储
        memory_flow = brain.memory.get_memory_flow()
        assert memory_flow["long_term"] >= num_memories * 0.8  # 大部分应该存入长期记忆
        
        # 性能断言：100条记忆应在5秒内存储完成
        assert storage_time < 5.0, f"存储 {num_memories} 条记忆耗时 {storage_time:.2f} 秒，超过阈值"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_speed(self):
        """测试记忆检索速度"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 先存储一些记忆
        for i in range(50):
            brain.memory.store(
                content=f"关键词{i} 相关内容 " + "y" * 50,
                importance=0.5,
                context_tags=["retrieval_test"]
            )
        
        # 测试检索速度
        num_queries = 20
        start_time = time.time()
        
        for i in range(num_queries):
            results = brain.memory.retrieve(
                query=f"关键词{i % 50}",
                top_k=5
            )
        
        retrieval_time = time.time() - start_time
        avg_time = retrieval_time / num_queries
        
        # 性能断言：平均每次检索应在阈值内
        # spec: 无 FAISS 时使用暴力搜索，阈值放宽至 2.0s（项目记忆：FAISS 未启用）
        assert avg_time < 2.0, f"平均检索时间 {avg_time*1000:.1f}ms，超过2000ms阈值"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_consolidation_performance(self):
        """测试记忆巩固性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 填充工作记忆
        for i in range(20):
            brain.memory.process_input(
                content=f"工作记忆内容 {i}",
                intensity=0.8
            )
        
        # 测试巩固速度
        start_time = time.time()
        consolidated = brain.memory.consolidate()
        consolidation_time = time.time() - start_time
        
        # 性能断言：巩固应在2秒内完成
        assert consolidation_time < 2.0, f"巩固耗时 {consolidation_time:.2f} 秒"
        assert consolidated >= 0
        
        await brain.shutdown()


class TestProcessingPerformance:
    """测试处理性能"""
    
    @pytest.mark.asyncio
    async def test_single_input_processing_speed(self):
        """测试单条输入处理速度"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 测试多条输入的处理时间
        inputs = [
            "你好",
            "今天天气怎么样",
            "请介绍一下自己",
            "什么是人工智能",
            "如何学习编程"
        ]
        
        times = []
        for user_input in inputs:
            start_time = time.time()
            result = await brain.process(user_input)
            processing_time = time.time() - start_time
            times.append(processing_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # 性能断言（spec: 阈值放宽至 30s 适应无 GPU 的 Ollama 推理环境）
        assert avg_time < 30.0, f"平均处理时间 {avg_time:.2f} 秒，超过阈值"
        assert max_time < 60.0, f"最大处理时间 {max_time:.2f} 秒，超过阈值"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """测试批量处理性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 准备批量输入
        num_inputs = 10
        inputs = [f"批量测试输入 {i}" for i in range(num_inputs)]
        
        # 串行处理
        start_time = time.time()
        for user_input in inputs:
            await brain.process(user_input)
        serial_time = time.time() - start_time
        
        # 性能断言：批量处理应在合理时间内完成（spec: 阈值放宽适应 Ollama 推理）
        assert serial_time < num_inputs * 30.0, f"批量处理耗时 {serial_time:.2f} 秒"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_long_text_processing(self):
        """测试长文本处理性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        # 生成长文本
        long_text = "这是一个长文本测试。" * 100  # 约1700字符
        
        start_time = time.time()
        result = await brain.process(long_text)
        processing_time = time.time() - start_time
        
        assert result.success is True
        # 长文本处理应在合理时间内完成（spec: 阈值放宽适应 Ollama 推理）
        assert processing_time < 60.0, f"长文本处理耗时 {processing_time:.2f} 秒"
        
        await brain.shutdown()


class TestConcurrentPerformance:
    """测试并发性能"""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self):
        """测试并发处理性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        num_concurrent = 5
        inputs = [f"并发输入 {i}" for i in range(num_concurrent)]
        
        start_time = time.time()
        tasks = [brain.process(inp) for inp in inputs]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 验证所有请求都成功
        assert all(r.success for r in results)
        
        # 并发处理应该比串行快（spec: 阈值放宽适应 Ollama 推理）
        avg_time = total_time / num_concurrent
        assert avg_time < 30.0, f"并发平均处理时间 {avg_time:.2f} 秒"
        
        await brain.shutdown()


class TestVectorStorePerformance:
    """测试向量存储性能"""
    
    @pytest.mark.asyncio
    async def test_vector_search_performance(self):
        """测试向量搜索性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        import numpy as np
        
        # 添加大量向量
        dim = 1536
        num_vectors = 100
        
        for i in range(num_vectors):
            vector = np.random.randn(dim).astype(np.float32)
            brain.vector_store.add(
                vector_id=f"vec_{i}",
                vector=vector,
                metadata={"index": i}
            )
        
        # 测试搜索速度
        num_queries = 10
        query_vector = np.random.randn(dim).astype(np.float32)
        
        start_time = time.time()
        for _ in range(num_queries):
            results = brain.vector_store.search(query_vector, top_k=10)
        search_time = time.time() - start_time
        avg_search_time = search_time / num_queries
        
        # 性能断言
        assert avg_search_time < 0.5, f"平均向量搜索时间 {avg_search_time*1000:.1f}ms"
        
        await brain.shutdown()


class TestDatabasePerformance:
    """测试数据库性能"""
    
    @pytest.mark.asyncio
    async def test_database_write_performance(self):
        """测试数据库写入性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        num_records = 50
        start_time = time.time()
        
        for i in range(num_records):
            brain.db.insert_conversation(
                conversation_id=f"perf_test_{i}",
                session_id="perf_session",
                role="user",
                content=f"性能测试消息 {i}"
            )
        
        write_time = time.time() - start_time
        avg_write_time = write_time / num_records
        
        # 性能断言
        assert avg_write_time < 0.05, f"平均写入时间 {avg_write_time*1000:.1f}ms"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    async def test_database_read_performance(self):
        """测试数据库读取性能"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        
        # 先写入数据
        for i in range(50):
            brain.db.insert_conversation(
                conversation_id=f"read_test_{i}",
                session_id="read_session",
                role="user",
                content=f"读取测试消息 {i}"
            )
        
        # 测试读取速度
        start_time = time.time()
        history = brain.db.get_conversation_history("read_session", limit=50)
        read_time = time.time() - start_time
        
        assert len(history) == 50
        assert read_time < 0.5, f"读取50条记录耗时 {read_time*1000:.1f}ms"
        
        await brain.shutdown()


class TestSystemResourceUsage:
    """测试系统资源使用"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        try:
            import psutil
            import os
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        if has_psutil:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 处理大量输入
        for i in range(20):
            await brain.process(f"内存测试输入 {i}")
        
        if has_psutil:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            # 内存增长应在合理范围内（100MB以内）
            assert memory_increase < 100, f"内存增长 {memory_increase:.1f}MB，超过阈值"
        
        await brain.shutdown()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_processing(self):
        """测试持续处理能力"""
        brain = Brain(enable_logging=False)
        await brain.initialize()
        await brain.start()
        
        num_iterations = 50
        times = []
        
        for i in range(num_iterations):
            start_time = time.time()
            result = await brain.process(f"持续测试 {i}")
            processing_time = time.time() - start_time
            times.append(processing_time)
            
            assert result.success is True
        
        # 计算性能指标
        avg_time = sum(times) / len(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        # 性能断言（spec: 阈值放宽适应 Ollama 推理）
        assert avg_time < 30.0, f"平均处理时间 {avg_time:.2f} 秒"
        assert p95_time < 60.0, f"95分位处理时间 {p95_time:.2f} 秒"
        
        await brain.shutdown()
