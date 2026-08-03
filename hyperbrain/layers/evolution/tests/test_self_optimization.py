"""
自我优化模块单元测试
"""

import unittest

from hyperbrain.layers.evolution.self_optimization import (
    SelfOptimizer, SelfOptimizationConfig,
    OptimizationTarget, CognitiveParameters,
    MemoryParameters, LearningParameters
)


class TestSelfOptimizer(unittest.TestCase):
    """测试自我优化模块"""

    def setUp(self):
        """测试前置"""
        self.config = SelfOptimizationConfig(
            enable_auto_optimize=True,
            optimization_interval=0.0,
            max_change_ratio=0.3,
            risk_tolerance=0.8
        )
        self.optimizer = SelfOptimizer(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.optimizer.reset()

    def test_initial_params(self):
        """测试初始参数"""
        cognitive = self.optimizer.get_cognitive_params()
        self.assertIsInstance(cognitive, CognitiveParameters)
        self.assertTrue(1.0 <= cognitive.reasoning_depth <= 10.0)

        memory = self.optimizer.get_memory_params()
        self.assertIsInstance(memory, MemoryParameters)

        learning = self.optimizer.get_learning_params()
        self.assertIsInstance(learning, LearningParameters)

    def test_optimize_from_reflection(self):
        """测试基于反思的优化"""
        reflection_data = {
            "insights": [
                {"title": "行为成功率偏低", "severity": "high"},
                {"title": "过度自信偏差", "severity": "high"}
            ],
            "opportunities": [
                {"target_scope": "behavior", "severity": "high", "expected_benefit": 0.7}
            ]
        }

        result = self.optimizer.optimize(reflection_data=reflection_data)

        self.assertIsNotNone(result)
        self.assertTrue(len(result.actions) > 0)

    def test_optimize_from_assessment(self):
        """测试基于评估的优化"""
        assessment_data = {
            "gaps": [
                {"dimension": "reasoning", "gap_size": 0.4},
                {"dimension": "learning", "gap_size": 0.3}
            ],
            "trends": [
                {"dimension": "memory", "trend_direction": "declining", "trend_strength": -0.1}
            ],
            "dimension_scores": {"reasoning": 0.4, "learning": 0.5, "memory": 0.6}
        }

        result = self.optimizer.optimize(assessment_data=assessment_data)

        self.assertIsNotNone(result)
        self.assertTrue(result.parameters_optimized > 0 or result.strategies_optimized > 0)

    def test_optimize_from_errors(self):
        """测试基于错误的优化"""
        error_data = {
            "patterns": [
                {"name": "Pattern_1", "frequency": 6, "category": "execution"}
            ],
            "strategies": []
        }

        result = self.optimizer.optimize(error_data=error_data)

        self.assertIsNotNone(result)

    def test_parameter_clamping(self):
        """测试参数范围限制"""
        # 设置一个超出范围的值
        result = self.optimizer.set_param("confidence_threshold", 2.0)
        self.assertTrue(result)

        value = self.optimizer.get_cognitive_params().confidence_threshold
        self.assertEqual(value, 1.0)

    def test_get_all_params(self):
        """测试获取所有参数"""
        params = self.optimizer.get_all_params()

        self.assertIn("cognitive", params)
        self.assertIn("memory", params)
        self.assertIn("learning", params)
        self.assertIn("resource", params)

    def test_manual_param_set(self):
        """测试手动设置参数"""
        result = self.optimizer.set_param("reasoning_depth", 5.0)
        self.assertTrue(result)

        cognitive = self.optimizer.get_cognitive_params()
        self.assertEqual(cognitive.reasoning_depth, 5.0)

    def test_auto_optimize(self):
        """测试自动优化"""
        result = self.optimizer.auto_optimize()
        self.assertIsNotNone(result)

    def test_callback(self):
        """测试回调注册"""
        callback_called = False

        def test_callback(result):
            nonlocal callback_called
            callback_called = True

        self.optimizer.register_optimization_callback(test_callback)
        self.optimizer.optimize()

        self.assertTrue(callback_called)

    def test_risk_tolerance(self):
        """测试风险容忍度"""
        self.optimizer.config.risk_tolerance = 0.1  # 很低的风险容忍度

        reflection_data = {
            "insights": [
                {"title": "严重问题", "severity": "high"}
            ],
            "opportunities": [
                {"target_scope": "decision", "severity": "high", "expected_benefit": 0.8}
            ]
        }

        result = self.optimizer.optimize(reflection_data=reflection_data)

        # 高风险动作应该被跳过
        high_risk_actions = [a for a in result.actions if a.risk_level > 0.1]
        for action in high_risk_actions:
            self.assertFalse(action.applied)

    def test_resource_optimization(self):
        """测试资源优化"""
        assessment_data = {
            "dimension_scores": {
                "reasoning": 0.3,
                "learning": 0.4,
                "memory": 0.8
            }
        }

        result = self.optimizer.optimize(assessment_data=assessment_data)

        # 应该有资源相关的优化动作
        resource_actions = [
            a for a in result.actions
            if a.target == OptimizationTarget.RESOURCE
        ]
        self.assertTrue(len(resource_actions) > 0)

    def test_reset(self):
        """测试重置"""
        self.optimizer.set_param("reasoning_depth", 8.0)
        self.optimizer.optimize()
        self.optimizer.reset()

        cognitive = self.optimizer.get_cognitive_params()
        self.assertEqual(cognitive.reasoning_depth, 3.0)

        stats = self.optimizer.get_stats()
        self.assertEqual(stats["total_optimizations"], 0)


if __name__ == "__main__":
    unittest.main()
