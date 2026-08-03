"""
能力评估模块单元测试
"""

import unittest
from datetime import datetime, timedelta

from hyperbrain.layers.evolution.capability_assessment import (
    CapabilityAssessor, CapabilityAssessmentConfig,
    CapabilityDimension, AssessmentMethod,
    CapabilityScore
)


class TestCapabilityAssessor(unittest.TestCase):
    """测试能力评估模块"""

    def setUp(self):
        """测试前置"""
        self.config = CapabilityAssessmentConfig(
            assessment_interval=3600.0,
            history_window_size=50
        )
        self.assessor = CapabilityAssessor(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.assessor.reset()

    def test_record_score(self):
        """测试评分记录"""
        score = self.assessor.record_score(
            dimension=CapabilityDimension.REASONING,
            score=0.8,
            confidence=0.9,
            method=AssessmentMethod.PERFORMANCE_BASED,
            context={"task": "logic_puzzle"},
            evidence=["正确解答", "用时短"]
        )

        self.assertIsNotNone(score.score_id)
        self.assertEqual(score.dimension, CapabilityDimension.REASONING)
        self.assertEqual(score.score, 0.8)
        self.assertEqual(score.confidence, 0.9)

    def test_record_score_validation(self):
        """测试评分范围验证"""
        score = self.assessor.record_score(
            dimension=CapabilityDimension.MEMORY,
            score=1.5,  # 超出范围
            confidence=-0.1  # 超出范围
        )

        self.assertEqual(score.score, 1.0)
        self.assertEqual(score.confidence, 0.0)

    def test_assess(self):
        """测试评估"""
        # 记录多个维度的评分
        self.assessor.record_score(CapabilityDimension.REASONING, 0.8)
        self.assessor.record_score(CapabilityDimension.LEARNING, 0.7)
        self.assessor.record_score(CapabilityDimension.MEMORY, 0.6)

        report = self.assessor.assess()

        self.assertIsNotNone(report)
        self.assertTrue(report.overall_score > 0)
        self.assertTrue(len(report.dimension_scores) > 0)
        self.assertIn("reasoning", report.dimension_scores)

    def test_assess_with_gaps(self):
        """测试评估并识别差距"""
        self.assessor.record_score(CapabilityDimension.REASONING, 0.4)
        self.assessor.record_score(CapabilityDimension.LEARNING, 0.3)

        report = self.assessor.assess()

        self.assertTrue(len(report.gaps) > 0)
        gap_dimensions = [g.dimension for g in report.gaps]
        self.assertIn(CapabilityDimension.REASONING, gap_dimensions)

    def test_trend_analysis(self):
        """测试趋势分析"""
        # 记录上升趋势
        for i in range(10):
            self.assessor.record_score(
                CapabilityDimension.REASONING,
                score=0.3 + i * 0.05
            )

        trends = self.assessor.get_trends()
        reasoning_trend = next(
            (t for t in trends if t.dimension == CapabilityDimension.REASONING),
            None
        )

        self.assertIsNotNone(reasoning_trend)
        self.assertEqual(reasoning_trend.trend_direction, "improving")

    def test_auto_assess(self):
        """测试自动评估"""
        self.assessor.config.enable_auto_assessment = True
        self.assessor.config.assessment_interval = 0.0

        self.assessor.record_score(CapabilityDimension.REASONING, 0.7)
        report = self.assessor.auto_assess()

        self.assertIsNotNone(report)

    def test_get_dimension_score(self):
        """测试获取维度评分"""
        self.assessor.record_score(CapabilityDimension.MEMORY, 0.75)

        score = self.assessor.get_dimension_score(CapabilityDimension.MEMORY)
        self.assertEqual(score, 0.75)

        no_score = self.assessor.get_dimension_score(CapabilityDimension.CREATIVITY)
        self.assertIsNone(no_score)

    def test_get_all_scores(self):
        """测试获取所有评分"""
        self.assessor.record_score(CapabilityDimension.REASONING, 0.8)
        self.assessor.record_score(CapabilityDimension.LEARNING, 0.7)

        scores = self.assessor.get_all_scores()
        self.assertIn("reasoning", scores)
        self.assertIn("learning", scores)
        self.assertEqual(scores["reasoning"], 0.8)

    def test_callback(self):
        """测试回调注册"""
        callback_called = False

        def test_callback(report):
            nonlocal callback_called
            callback_called = True

        self.assessor.register_assessment_callback(test_callback)
        self.assessor.record_score(CapabilityDimension.REASONING, 0.8)
        self.assessor.assess()

        self.assertTrue(callback_called)

    def test_suggestions(self):
        """测试生成建议"""
        self.assessor.record_score(CapabilityDimension.REASONING, 0.3)
        self.assessor.record_score(CapabilityDimension.LEARNING, 0.35)

        report = self.assessor.assess()

        self.assertTrue(len(report.suggestions) > 0)
        suggestion_dimensions = [s.target_dimension for s in report.suggestions]
        self.assertIn(CapabilityDimension.REASONING, suggestion_dimensions)

    def test_strengths_weaknesses(self):
        """测试优势和劣势识别"""
        self.assessor.record_score(CapabilityDimension.REASONING, 0.9)
        self.assessor.record_score(CapabilityDimension.LEARNING, 0.85)
        self.assessor.record_score(CapabilityDimension.MEMORY, 0.3)
        self.assessor.record_score(CapabilityDimension.ATTENTION, 0.25)

        report = self.assessor.assess()

        self.assertTrue(len(report.strengths) > 0)
        self.assertTrue(len(report.weaknesses) > 0)

    def test_reset(self):
        """测试重置"""
        self.assessor.record_score(CapabilityDimension.REASONING, 0.8)
        self.assessor.assess()
        self.assessor.reset()

        stats = self.assessor.get_stats()
        self.assertEqual(stats["total_scores_recorded"], 0)


if __name__ == "__main__":
    unittest.main()
