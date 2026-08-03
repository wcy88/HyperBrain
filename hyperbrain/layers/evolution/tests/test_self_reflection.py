"""
自我反思模块单元测试
"""

import unittest
from datetime import datetime, timedelta

from hyperbrain.layers.evolution.self_reflection import (
    SelfReflection, SelfReflectionConfig,
    ReflectionScope, ReflectionPeriod,
    BehaviorRecord, DecisionRecord
)


class TestSelfReflection(unittest.TestCase):
    """测试自我反思模块"""

    def setUp(self):
        """测试前置"""
        self.config = SelfReflectionConfig(
            max_behavior_history=100,
            max_decision_history=50,
            max_strategy_history=20
        )
        self.reflection = SelfReflection(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.reflection.reset()

    def test_record_behavior(self):
        """测试行为记录"""
        record = self.reflection.record_behavior(
            action="测试行为",
            context={"test": True},
            duration=1.5,
            outcome="成功",
            success=True,
            importance=0.8
        )

        self.assertIsNotNone(record.record_id)
        self.assertEqual(record.action, "测试行为")
        self.assertTrue(record.success)
        self.assertEqual(record.importance, 0.8)

    def test_record_decision(self):
        """测试决策记录"""
        record = self.reflection.record_decision(
            decision_name="测试决策",
            alternatives=["A", "B", "C"],
            selected="B",
            reasoning="B最优",
            expected_outcome="好结果",
            confidence=0.9
        )

        self.assertIsNotNone(record.record_id)
        self.assertEqual(record.decision_name, "测试决策")
        self.assertEqual(record.selected, "B")
        self.assertEqual(record.confidence, 0.9)

    def test_update_decision_outcome(self):
        """测试更新决策结果"""
        record = self.reflection.record_decision(
            decision_name="测试决策",
            alternatives=["A", "B"],
            selected="A"
        )

        result = self.reflection.update_decision_outcome(
            record_id=record.record_id,
            actual_outcome="实际结果",
            quality_score=0.7
        )

        self.assertTrue(result)
        self.assertEqual(record.actual_outcome, "实际结果")
        self.assertEqual(record.quality_score, 0.7)

    def test_reflect_behavior(self):
        """测试行为反思"""
        # 记录多个行为
        for i in range(5):
            self.reflection.record_behavior(
                action=f"行为{i}",
                success=i < 2,  # 2成功，3失败
                importance=0.6
            )

        report = self.reflection.reflect(
            period=ReflectionPeriod.SHORT,
            scopes=[ReflectionScope.BEHAVIOR]
        )

        self.assertIsNotNone(report)
        self.assertEqual(report.period, ReflectionPeriod.SHORT)
        self.assertTrue(len(report.insights) > 0)

    def test_reflect_decision(self):
        """测试决策反思"""
        # 记录高置信度但低质量的决策
        record = self.reflection.record_decision(
            decision_name="高风险决策",
            alternatives=["A", "B"],
            selected="A",
            confidence=0.95
        )

        self.reflection.update_decision_outcome(
            record_id=record.record_id,
            actual_outcome="失败",
            quality_score=0.2
        )

        report = self.reflection.reflect(
            period=ReflectionPeriod.SHORT,
            scopes=[ReflectionScope.DECISION]
        )

        self.assertIsNotNone(report)
        # 应该检测到过度自信
        insight_titles = [i.title for i in report.insights]
        self.assertTrue(any("过度自信" in t for t in insight_titles))

    def test_get_behavior_stats(self):
        """测试获取行为统计"""
        for i in range(10):
            self.reflection.record_behavior(
                action="测试",
                success=i < 7,
                duration=1.0
            )

        stats = self.reflection.get_behavior_stats()
        self.assertEqual(stats["total"], 10)
        self.assertEqual(stats["successful"], 7)
        self.assertEqual(stats["failed"], 3)
        self.assertAlmostEqual(stats["success_rate"], 0.7)

    def test_get_decision_stats(self):
        """测试获取决策统计"""
        for i in range(5):
            record = self.reflection.record_decision(
                decision_name=f"决策{i}",
                alternatives=["A", "B"],
                selected="A",
                confidence=0.7
            )
            self.reflection.update_decision_outcome(
                record_id=record.record_id,
                actual_outcome="结果",
                quality_score=0.6 + i * 0.05
            )

        stats = self.reflection.get_decision_stats()
        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["scored"], 5)

    def test_auto_reflect(self):
        """测试自动反思"""
        # 设置很短的间隔以便测试
        self.reflection.config.short_term_interval = 0.0

        report = self.reflection.auto_reflect()
        self.assertIsNotNone(report)

    def test_callback(self):
        """测试回调注册"""
        callback_called = False
        received_report = None

        def test_callback(report):
            nonlocal callback_called, received_report
            callback_called = True
            received_report = report

        self.reflection.register_reflection_callback(test_callback)

        self.reflection.record_behavior(action="测试", success=True)
        self.reflection.reflect(period=ReflectionPeriod.SHORT)

        self.assertTrue(callback_called)
        self.assertIsNotNone(received_report)

    def test_reset(self):
        """测试重置"""
        self.reflection.record_behavior(action="测试")
        self.reflection.reflect(period=ReflectionPeriod.SHORT)

        self.reflection.reset()

        stats = self.reflection.get_behavior_stats()
        self.assertEqual(stats["total"], 0)
        self.assertIsNone(self.reflection.get_latest_report())


if __name__ == "__main__":
    unittest.main()
