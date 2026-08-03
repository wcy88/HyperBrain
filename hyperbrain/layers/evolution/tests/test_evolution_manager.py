"""
进化管理器单元测试
"""

import unittest

from hyperbrain.layers.evolution.evolution_manager import (
    EvolutionManager, EvolutionConfig, EvolutionPhase
)
from hyperbrain.layers.evolution.error_analysis import ErrorCategory, ErrorSeverity
from hyperbrain.layers.evolution.capability_assessment import CapabilityDimension


class TestEvolutionManager(unittest.TestCase):
    """测试进化管理器"""

    def setUp(self):
        """测试前置"""
        self.config = EvolutionConfig(
            enable_auto_evolution=True,
            evolution_interval=0.0,
            pause_between_phases=0.0
        )
        self.manager = EvolutionManager(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.manager.reset()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager.self_reflection)
        self.assertIsNotNone(self.manager.error_analyzer)
        self.assertIsNotNone(self.manager.capability_assessor)
        self.assertIsNotNone(self.manager.self_optimizer)
        self.assertIsNotNone(self.manager.goal_evolver)
        self.assertIsNotNone(self.manager.architecture_evolver)

    def test_run_evolution_cycle(self):
        """测试执行进化周期"""
        cycle = self.manager.run_evolution_cycle()

        self.assertIsNotNone(cycle)
        self.assertEqual(cycle.status, "completed")
        self.assertTrue(len(cycle.phases_completed) > 0)

    def test_evolution_phases(self):
        """测试进化阶段"""
        cycle = self.manager.run_evolution_cycle()

        # 检查是否包含预期的阶段
        phase_values = [p.value for p in cycle.phases_completed]
        self.assertIn("reflection", phase_values)
        self.assertIn("assessment", phase_values)
        self.assertIn("optimization", phase_values)

    def test_auto_evolve(self):
        """测试自动进化"""
        cycle = self.manager.auto_evolve()

        self.assertIsNotNone(cycle)
        self.assertEqual(cycle.status, "completed")

    def test_pause_resume(self):
        """测试暂停和恢复"""
        self.manager.pause()
        self.assertTrue(self.manager.is_paused())

        self.manager.resume()
        self.assertFalse(self.manager.is_paused())

    def test_start_stop(self):
        """测试启动和停止"""
        self.manager.start_continuous_evolution()
        self.assertTrue(self.manager.is_running())

        self.manager.stop_continuous_evolution()
        self.assertFalse(self.manager.is_running())

    def test_record_behavior(self):
        """测试记录行为"""
        self.manager.record_behavior(
            action="测试行为",
            context={"test": True},
            success=True,
            importance=0.8
        )

        stats = self.manager.self_reflection.get_behavior_stats()
        self.assertEqual(stats["total"], 1)

    def test_record_decision(self):
        """测试记录决策"""
        self.manager.record_decision(
            decision_name="测试决策",
            alternatives=["A", "B"],
            selected="A",
            reasoning="A更好",
            confidence=0.9
        )

        stats = self.manager.self_reflection.get_decision_stats()
        self.assertEqual(stats["total"], 1)

    def test_record_error(self):
        """测试记录错误"""
        self.manager.record_error(
            description="测试错误",
            category=ErrorCategory.COGNITIVE,
            severity=ErrorSeverity.HIGH,
            context={"module": "test"}
        )

        stats = self.manager.error_analyzer.get_error_stats()
        self.assertEqual(stats["total"], 1)

    def test_record_capability_score(self):
        """测试记录能力评分"""
        self.manager.record_capability_score(
            dimension=CapabilityDimension.REASONING,
            score=0.8,
            confidence=0.9
        )

        score = self.manager.capability_assessor.get_dimension_score(
            CapabilityDimension.REASONING
        )
        self.assertEqual(score, 0.8)

    def test_record_information_flow(self):
        """测试记录信息流"""
        self.manager.record_information_flow(
            source_module="module_a",
            target_module="module_b",
            data_type="test_data",
            volume=5.0
        )

        stats = self.manager.architecture_evolver.get_stats()
        self.assertEqual(stats["information_flows"], 1)

    def test_cycle_callback(self):
        """测试周期回调"""
        callback_called = False
        received_cycle = None

        def test_callback(cycle):
            nonlocal callback_called, received_cycle
            callback_called = True
            received_cycle = cycle

        self.manager.register_cycle_callback(test_callback)
        cycle = self.manager.run_evolution_cycle()

        self.assertTrue(callback_called)
        self.assertEqual(received_cycle.cycle_id, cycle.cycle_id)

    def test_phase_callback(self):
        """测试阶段回调"""
        callback_called = False

        def test_callback(report):
            nonlocal callback_called
            callback_called = True

        self.manager.register_phase_callback(
            EvolutionPhase.REFLECTION,
            test_callback
        )

        self.manager.run_evolution_cycle()
        self.assertTrue(callback_called)

    def test_get_stats(self):
        """测试获取统计信息"""
        self.manager.run_evolution_cycle()
        stats = self.manager.get_stats()

        self.assertIn("manager", stats)
        self.assertIn("self_reflection", stats)
        self.assertIn("error_analyzer", stats)
        self.assertIn("capability_assessor", stats)
        self.assertIn("self_optimizer", stats)
        self.assertIn("goal_evolver", stats)
        self.assertIn("architecture_evolver", stats)

    def test_get_comprehensive_report(self):
        """测试获取综合报告"""
        self.manager.run_evolution_cycle()
        report = self.manager.get_comprehensive_report()

        self.assertIn("timestamp", report)
        self.assertIn("system_status", report)
        self.assertIn("latest_cycle", report)
        self.assertIn("module_stats", report)
        self.assertIn("summary", report)

    def test_get_cycle_history(self):
        """测试获取周期历史"""
        self.manager.run_evolution_cycle()
        self.manager.run_evolution_cycle()

        history = self.manager.get_cycle_history(limit=5)
        self.assertEqual(len(history), 2)

    def test_current_phase(self):
        """测试当前阶段"""
        phase = self.manager.get_current_phase()
        self.assertEqual(phase, EvolutionPhase.IDLE)

    def test_connect_systems(self):
        """测试连接外部系统"""
        mock_memory = type("MockMemory", (), {
            "store_memory": lambda **kwargs: None
        })()

        mock_cognitive = type("MockCognitive", (), {
            "get_stats": lambda: {"average_success_rate": 0.8}
        })()

        mock_learning = type("MockLearning", (), {
            "get_stats": lambda: {"average_performance": 0.7}
        })()

        self.manager.connect_memory_system(mock_memory)
        self.manager.connect_cognitive_system(mock_cognitive)
        self.manager.connect_learning_system(mock_learning)

        # 运行一个周期，应该能与外部系统交互
        cycle = self.manager.run_evolution_cycle()
        self.assertEqual(cycle.status, "completed")

    def test_reset(self):
        """测试重置"""
        self.manager.run_evolution_cycle()
        self.manager.reset()

        stats = self.manager.get_stats()
        self.assertEqual(stats["manager"]["total_cycles"], 0)
        self.assertEqual(self.manager.get_current_phase(), EvolutionPhase.IDLE)


if __name__ == "__main__":
    unittest.main()
