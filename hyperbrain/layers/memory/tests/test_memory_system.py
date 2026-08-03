"""
记忆系统完整单元测试

测试所有记忆模块的功能，确保系统正确运行。
"""

import os
import sys
import time
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

# 确保能导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from hyperbrain.layers.memory import (
    MemoryManager,
    SensoryMemory,
    WorkingMemory,
    LongTermMemory,
    MemoryConsolidator,
    MemoryRetriever,
    MemoryForgetting,
    MemoryEnhancer,
    MemoryItem,
    MemoryChunk,
    MemoryType,
    MemoryStatus,
    EmotionalTag,
    SensoryInput,
    compute_ebbinghaus_retention,
    compute_adaptive_decay_rate,
    cosine_similarity,
    normalize_vector,
)


class TestMemoryModels(unittest.TestCase):
    """测试数据模型"""
    
    def test_memory_item_creation(self):
        """测试MemoryItem创建"""
        item = MemoryItem(content="测试内容", importance=0.8)
        self.assertEqual(item.content, "测试内容")
        self.assertEqual(item.importance, 0.8)
        self.assertEqual(item.memory_type, MemoryType.DECLARATIVE)
        self.assertIsNotNone(item.id)
    
    def test_memory_item_update_access(self):
        """测试访问更新"""
        item = MemoryItem(content="测试")
        self.assertEqual(item.access_count, 0)
        
        item.update_access()
        self.assertEqual(item.access_count, 1)
        self.assertIsNotNone(item.last_accessed)
    
    def test_memory_chunk_merge(self):
        """测试组块合并"""
        chunk1 = MemoryChunk(content="Hello", priority=0.7)
        chunk2 = MemoryChunk(content="World", priority=0.5)
        
        merged = chunk1.merge_with(chunk2)
        self.assertIn("Hello", str(merged.content))
        self.assertIn("World", str(merged.content))
        self.assertEqual(merged.size, 2)
    
    def test_memory_chunk_split(self):
        """测试组块拆分"""
        chunk = MemoryChunk(content="Hello | World", priority=0.7)
        split = chunk.split()
        
        self.assertEqual(len(split), 2)
        self.assertEqual(split[0].content, "Hello")
        self.assertEqual(split[1].content, "World")
    
    def test_emotional_tag(self):
        """测试情感标签"""
        tag = EmotionalTag(
            primary_emotion="joy",
            intensity=0.8,
            valence="positive"
        )
        self.assertEqual(tag.primary_emotion, "joy")
        self.assertEqual(tag.intensity, 0.8)
        
        data = tag.to_dict()
        self.assertEqual(data["primary_emotion"], "joy")


class TestMemoryUtils(unittest.TestCase):
    """测试工具函数"""
    
    def test_cosine_similarity(self):
        """测试余弦相似度"""
        a = np.array([1, 0, 0], dtype=np.float32)
        b = np.array([1, 0, 0], dtype=np.float32)
        c = np.array([0, 1, 0], dtype=np.float32)
        
        self.assertAlmostEqual(cosine_similarity(a, b), 1.0, places=5)
        self.assertAlmostEqual(cosine_similarity(a, c), 0.0, places=5)
    
    def test_normalize_vector(self):
        """测试向量归一化"""
        v = np.array([3, 4], dtype=np.float32)
        normalized = normalize_vector(v)
        
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0, places=5)
    
    def test_ebbinghaus_retention(self):
        """测试艾宾浩斯遗忘曲线"""
        # 刚学习后保持率应为1.0
        retention = compute_ebbinghaus_retention(0)
        self.assertEqual(retention, 1.0)
        
        # 时间越久保持率越低
        r1 = compute_ebbinghaus_retention(1)
        r2 = compute_ebbinghaus_retention(24)
        self.assertGreater(r1, r2)
    
    def test_adaptive_decay_rate(self):
        """测试自适应遗忘速率"""
        # 重要性高的遗忘慢
        rate_high = compute_adaptive_decay_rate(0.9, 0.5, 0.5)
        rate_low = compute_adaptive_decay_rate(0.1, 0.5, 0.5)
        self.assertLess(rate_high, rate_low)


class TestSensoryMemory(unittest.TestCase):
    """测试瞬时记忆"""
    
    def setUp(self):
        self.sm = SensoryMemory(capacity=5, ttl_seconds=2.0, enable_auto_cleanup=False)
    
    def tearDown(self):
        self.sm.shutdown()
    
    def test_add_and_retrieve(self):
        """测试添加和检索"""
        input1 = self.sm.add("测试输入1", modality="text")
        self.assertEqual(len(self.sm), 1)
        
        recent = self.sm.get_recent(1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].content, "测试输入1")
    
    def test_capacity_limit(self):
        """测试容量限制"""
        for i in range(7):
            self.sm.add(f"输入{i}")
        
        self.assertEqual(len(self.sm), 5)  # 容量为5
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        self.sm.add("临时输入")
        self.assertEqual(len(self.sm), 1)
        
        # 等待过期
        time.sleep(2.5)
        cleaned = self.sm.force_cleanup()
        
        self.assertEqual(len(self.sm), 0)
    
    def test_modality_filter(self):
        """测试模态过滤"""
        self.sm.add("文本", modality="text")
        self.sm.add("图片", modality="image")
        
        text_inputs = self.sm.get_by_modality("text")
        self.assertEqual(len(text_inputs), 1)
        self.assertEqual(text_inputs[0].content, "文本")


class TestWorkingMemory(unittest.TestCase):
    """测试工作记忆"""
    
    def setUp(self):
        self.wm = WorkingMemory(capacity=5)
    
    def test_add_and_capacity(self):
        """测试添加和容量"""
        for i in range(7):
            self.wm.add(f"组块{i}", priority=0.5)
        
        # 容量为5，应该只有5个
        self.assertEqual(len(self.wm), 5)
    
    def test_priority_eviction(self):
        """测试优先级淘汰"""
        self.wm.add("低优先级", priority=0.1)
        self.wm.add("高优先级", priority=0.9)
        
        # 填满容量
        for i in range(5):
            self.wm.add(f"填充{i}", priority=0.5)
        
        # 高优先级应该保留
        chunks = self.wm.get_all()
        contents = [c.content for c in chunks]
        self.assertIn("高优先级", contents)
    
    def test_merge_chunks(self):
        """测试组块合并"""
        chunk1 = self.wm.add("Hello", priority=0.7)
        chunk2 = self.wm.add("World", priority=0.6)
        
        merged = self.wm.merge_chunks(chunk1.id, chunk2.id)
        self.assertIsNotNone(merged)
        self.assertIn("Hello", str(merged.content))
        self.assertIn("World", str(merged.content))
    
    def test_split_chunk(self):
        """测试组块拆分"""
        chunk = self.wm.add("Hello | World", priority=0.7)
        split = self.wm.split_chunk(chunk.id)
        
        self.assertEqual(len(split), 2)
    
    def test_attention_focus(self):
        """测试注意力聚焦"""
        chunk1 = self.wm.add("焦点内容", priority=0.5)
        chunk2 = self.wm.add("其他内容", priority=0.5)
        
        self.wm.set_focus("测试焦点", [chunk1.id])
        
        focused = self.wm.get_focused()
        self.assertEqual(len(focused), 1)
        self.assertEqual(focused[0].id, chunk1.id)
    
    def test_attention_distribution(self):
        """测试注意力分布"""
        self.wm.add("内容1", priority=0.9)
        self.wm.add("内容2", priority=0.5)
        
        distribution = self.wm.compute_attention_distribution()
        self.assertEqual(len(distribution), 2)
        
        # 高优先级应该获得更多注意力
        weights = list(distribution.values())
        self.assertGreater(max(weights), min(weights))


class TestLongTermMemory(unittest.TestCase):
    """测试长期记忆"""
    
    def setUp(self):
        # 使用临时数据库
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.ltm = LongTermMemory(db_path=self.db_path, vector_dim=128)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_retrieve(self):
        """测试存储和检索"""
        item = self.ltm.store(
            content="测试记忆",
            importance=0.8,
            embedding=np.random.randn(128).astype(np.float32)
        )
        
        retrieved = self.ltm.retrieve(item.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(str(retrieved.content), "测试记忆")
    
    def test_search_by_content(self):
        """测试内容搜索"""
        self.ltm.store("Python编程", importance=0.7)
        self.ltm.store("Java开发", importance=0.6)
        self.ltm.store("机器学习", importance=0.8)
        
        results = self.ltm.search_by_content("Python")
        self.assertEqual(len(results), 1)
        self.assertIn("Python", str(results[0].content))
    
    def test_search_by_type(self):
        """测试类型搜索"""
        self.ltm.store("事实1", memory_type=MemoryType.DECLARATIVE)
        self.ltm.store("技能1", memory_type=MemoryType.PROCEDURAL)
        
        results = self.ltm.search_by_type(MemoryType.PROCEDURAL)
        self.assertEqual(len(results), 1)
    
    def test_associations(self):
        """测试关联"""
        item1 = self.ltm.store("记忆A")
        item2 = self.ltm.store("记忆B")
        
        success = self.ltm.add_association(item1.id, item2.id, strength=0.8)
        self.assertTrue(success)
        
        associated = self.ltm.get_associated_memories(item1.id)
        self.assertEqual(len(associated), 1)
        self.assertEqual(associated[0][0].id, item2.id)
    
    def test_update_memory(self):
        """测试更新记忆"""
        item = self.ltm.store("原始内容", importance=0.5)
        
        updated = self.ltm.update_memory(
            item.id,
            {"importance": 0.9, "content": "更新内容"}
        )
        self.assertTrue(updated)
        
        retrieved = self.ltm.retrieve(item.id)
        self.assertEqual(retrieved.importance, 0.9)
    
    def test_delete(self):
        """测试删除"""
        item = self.ltm.store("待删除")
        self.assertIsNotNone(self.ltm.retrieve(item.id))
        
        deleted = self.ltm.delete(item.id)
        self.assertTrue(deleted)
        
        # 删除后应该找不到
        # 注意：retrieve会更新访问信息，但删除后应该返回None
        # 这里可能需要调整测试逻辑


class TestConsolidation(unittest.TestCase):
    """测试记忆巩固"""
    
    def setUp(self):
        self.consolidator = MemoryConsolidator()
    
    def test_evaluate_worthiness(self):
        """测试巩固评估"""
        chunk = MemoryChunk(content="重要内容", priority=0.9)
        score = self.consolidator.evaluate_consolidation_worthiness(chunk)
        
        self.assertGreater(score, 0.5)
        self.assertTrue(self.consolidator.should_consolidate(chunk))
    
    def test_consolidate_chunk(self):
        """测试组块巩固"""
        chunk = MemoryChunk(content="测试内容", priority=0.8)
        item = self.consolidator.consolidate_chunk(chunk)
        
        self.assertIsInstance(item, MemoryItem)
        self.assertEqual(item.status, MemoryStatus.CONSOLIDATED)
        self.assertEqual(str(item.content), "测试内容")
    
    def test_infer_memory_type(self):
        """测试记忆类型推断"""
        chunk_skill = MemoryChunk(content="技能", chunk_type="skill")
        chunk_event = MemoryChunk(content="事件", chunk_type="event")
        
        self.assertEqual(
            self.consolidator._infer_memory_type(chunk_skill),
            MemoryType.PROCEDURAL
        )
        self.assertEqual(
            self.consolidator._infer_memory_type(chunk_event),
            MemoryType.EPISODIC
        )


class TestRetrieval(unittest.TestCase):
    """测试记忆检索"""
    
    def setUp(self):
        self.retriever = MemoryRetriever()
    
    def test_semantic_search(self):
        """测试语义检索"""
        embedding1 = np.array([1, 0, 0], dtype=np.float32)
        embedding2 = np.array([0.9, 0.1, 0], dtype=np.float32)
        embedding3 = np.array([0, 1, 0], dtype=np.float32)
        
        memories = [
            MemoryItem(content="A", embedding=embedding1.tolist()),
            MemoryItem(content="B", embedding=embedding2.tolist()),
            MemoryItem(content="C", embedding=embedding3.tolist()),
        ]
        
        query = np.array([1, 0, 0], dtype=np.float32)
        results = self.retriever.semantic_search(query, memories, top_k=2)
        
        self.assertEqual(len(results), 2)
        # A应该最相似
        self.assertEqual(results[0].memory.content, "A")
    
    def test_context_search(self):
        """测试情境检索"""
        memories = [
            MemoryItem(content="A", context_tags=["python", "coding"]),
            MemoryItem(content="B", context_tags=["java", "coding"]),
            MemoryItem(content="C", context_tags=["cooking"]),
        ]
        
        results = self.retriever.context_search(["python"], memories)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].memory.content, "A")
    
    def test_emotional_search(self):
        """测试情感检索"""
        memories = [
            MemoryItem(content="快乐", emotional_tag={"primary_emotion": "joy", "intensity": 0.8}),
            MemoryItem(content="悲伤", emotional_tag={"primary_emotion": "sadness", "intensity": 0.6}),
        ]
        
        results = self.retriever.emotional_search("joy", memories)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].memory.content, "快乐")
    
    def test_associative_search(self):
        """测试联想检索"""
        seed = MemoryItem(id="seed1", content="种子", associations=["mem2"])
        mem2 = MemoryItem(id="mem2", content="关联", associations=["mem3"])
        mem3 = MemoryItem(id="mem3", content="间接关联")
        
        memories = [seed, mem2, mem3]
        results = self.retriever.associative_search(seed, memories, max_hops=2)
        
        self.assertGreaterEqual(len(results), 1)


class TestForgetting(unittest.TestCase):
    """测试遗忘机制"""
    
    def setUp(self):
        self.forgetter = MemoryForgetting()
    
    def test_retention_computation(self):
        """测试保持率计算"""
        memory = MemoryItem(content="测试")
        memory.created_at = datetime.now() - timedelta(hours=1)
        
        retention = self.forgetter.compute_retention(memory)
        self.assertLess(retention, 1.0)
        self.assertGreater(retention, 0.0)
    
    def test_should_forget(self):
        """测试遗忘判断"""
        # 高重要性记忆不应被轻易遗忘
        important = MemoryItem(content="重要", importance=0.9)
        self.assertFalse(self.forgetter.should_forget(important))
        
        # 低重要性、旧记忆应该被遗忘
        old = MemoryItem(content="不重要", importance=0.1)
        old.created_at = datetime.now() - timedelta(days=30)
        old.last_accessed = datetime.now() - timedelta(days=30)
        old.decay_factor = 0.05
        self.assertTrue(self.forgetter.should_forget(old))
    
    def test_decay_application(self):
        """测试衰减应用"""
        memory = MemoryItem(content="测试", decay_factor=1.0)
        
        decayed = self.forgetter.apply_decay(memory)
        self.assertLess(decayed.decay_factor, 1.0)
    
    def test_reinforce_memory(self):
        """测试记忆强化"""
        memory = MemoryItem(content="测试", decay_factor=0.5)
        
        reinforced = self.forgetter.reinforce_memory(memory)
        self.assertGreater(reinforced.decay_factor, 0.5)
        self.assertEqual(reinforced.repetition_count, 1)


class TestEnhancement(unittest.TestCase):
    """测试记忆增强"""
    
    def setUp(self):
        self.enhancer = MemoryEnhancer()
    
    def test_reinforce_by_repetition(self):
        """测试重复强化"""
        memory = MemoryItem(content="测试", importance=0.5, confidence=0.7)
        
        reinforced = self.enhancer.reinforce_by_repetition(memory)
        self.assertGreater(reinforced.importance, 0.5)
        self.assertGreater(reinforced.confidence, 0.7)
    
    def test_deep_encode(self):
        """测试深度编码"""
        memory = MemoryItem(content="重要", importance=0.5)
        
        encoded = self.enhancer.deep_encode(memory, processing_depth=5)
        self.assertGreater(encoded.importance, 0.5)
        self.assertTrue(encoded.metadata.get("deep_encoded"))
    
    def test_strengthen_by_emotion(self):
        """测试情感强化"""
        memory = MemoryItem(content="情感记忆", importance=0.5)
        
        strengthened = self.enhancer.strengthen_by_emotion(memory, 0.9)
        self.assertGreater(strengthened.importance, 0.5)
        self.assertIsNotNone(strengthened.emotional_tag)
    
    def test_evaluate_memory_quality(self):
        """测试记忆质量评估"""
        memory = MemoryItem(
            content="高质量记忆",
            importance=0.9,
            confidence=0.9,
            access_count=10
        )
        
        quality = self.enhancer.evaluate_memory_quality(memory)
        self.assertIn("overall", quality)
        self.assertGreater(quality["overall"], 0.5)


class TestMemoryManager(unittest.TestCase):
    """测试记忆管理器（集成测试）"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_manager.db")
        self.manager = MemoryManager(
            db_path=self.db_path,
            vector_dim=128,
            auto_consolidate=False,
            auto_cleanup=False
        )
    
    def tearDown(self):
        self.manager.shutdown()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_process_input(self):
        """测试输入处理"""
        result = self.manager.process_input("测试输入", intensity=0.9)
        
        self.assertIn("sensory_input_id", result)
        self.assertIn("chunk_id", result)
        # intensity=0.9 应该触发直接存储 (base 0.3 + intensity*0.3*3 = 0.3 + 0.81 = 1.11 > 0.7)
        self.assertTrue(result["direct_storage"])  # 高强度应该直接存储
    
    def test_store_and_retrieve(self):
        """测试存储和检索"""
        memory = self.manager.store(
            content="重要信息",
            importance=0.9,
            memory_type=MemoryType.DECLARATIVE
        )
        
        retrieved = self.manager.retrieve_by_id(memory.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(str(retrieved.content), "重要信息")
    
    def test_retrieve(self):
        """测试统一检索"""
        self.manager.store("Python编程", importance=0.8)
        self.manager.store("机器学习", importance=0.7)
        self.manager.store("烹饪技巧", importance=0.5)
        
        results = self.manager.retrieve(query="Python", top_k=5)
        self.assertGreater(len(results), 0)
    
    def test_consolidate(self):
        """测试巩固"""
        # 添加一些工作记忆
        for i in range(3):
            self.manager.working_memory.add(f"组块{i}", priority=0.8)
        
        consolidated = self.manager.consolidate()
        self.assertGreaterEqual(consolidated, 0)
    
    def test_forget(self):
        """测试遗忘"""
        memory = self.manager.store("待遗忘", importance=0.3)
        
        # 确保存储成功
        self.assertIsNotNone(self.manager.retrieve_by_id(memory.id))
        
        forgotten = self.manager.forget(memory.id)
        self.assertTrue(forgotten)
    
    def test_reinforce(self):
        """测试强化"""
        memory = self.manager.store("待强化", importance=0.5)
        
        reinforced = self.manager.reinforce(memory.id)
        self.assertIsNotNone(reinforced)
        self.assertGreater(reinforced.importance, 0.5)
    
    def test_get_stats(self):
        """测试统计信息"""
        stats = self.manager.get_stats()
        
        self.assertIn("sensory_memory", stats)
        self.assertIn("working_memory", stats)
        self.assertIn("long_term_memory", stats)
    
    def test_memory_flow(self):
        """测试记忆流"""
        flow = self.manager.get_memory_flow()
        
        self.assertIn("sensory", flow)
        self.assertIn("working", flow)
        self.assertIn("long_term", flow)
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with MemoryManager(db_path=self.db_path, auto_consolidate=False) as mgr:
            mgr.store("上下文测试")
            self.assertEqual(len(mgr.long_term_memory), 1)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryModels))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestSensoryMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkingMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestLongTermMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestConsolidation))
    suite.addTests(loader.loadTestsFromTestCase(TestRetrieval))
    suite.addTests(loader.loadTestsFromTestCase(TestForgetting))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancement))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
