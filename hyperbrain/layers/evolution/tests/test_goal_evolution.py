"""
目标进化模块单元测试
"""

import unittest
from datetime import datetime, timedelta

from hyperbrain.layers.evolution.goal_evolution import (
    GoalEvolver, GoalEvolutionConfig,
    GoalStatus, SystemGoal
)


class TestGoalEvolver(unittest.TestCase):
    """测试目标进化模块"""

    def setUp(self):
        """测试前置"""
        self.config = GoalEvolutionConfig(
            max_active_goals=10,
            auto_prioritize=True,
            enable_goal_discovery=True,
            enable_goal_pruning=True
        )
        self.evolver = GoalEvolver(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.evolver.reset()

    def test_add_goal(self):
        """测试添加目标"""
        goal = self.evolver.add_goal(
            name="测试目标",
            description="这是一个测试目标",
            priority=4,
            success_criteria=["完成A", "完成B"],
            tags=["test"]
        )

        self.assertIsNotNone(goal.goal_id)
        self.assertEqual(goal.name, "测试目标")
        self.assertEqual(goal.priority, 4)
        self.assertEqual(goal.status, GoalStatus.ACTIVE)

    def test_add_sub_goal(self):
        """测试添加子目标"""
        parent = self.evolver.add_goal(
            name="父目标",
            description="父目标描述"
        )

        child = self.evolver.add_goal(
            name="子目标",
            description="子目标描述",
            parent_goal_id=parent.goal_id
        )

        self.assertIn(child.goal_id, parent.sub_goals)
        self.assertEqual(child.parent_goal_id, parent.goal_id)

    def test_update_progress(self):
        """测试更新进度"""
        goal = self.evolver.add_goal(name="进度测试", description="描述")

        result = self.evolver.update_goal_progress(goal.goal_id, 0.5)
        self.assertTrue(result)
        self.assertEqual(goal.progress, 0.5)

        # 测试达成
        result = self.evolver.update_goal_progress(goal.goal_id, 0.98)
        self.assertTrue(result)
        self.assertEqual(goal.status, GoalStatus.ACHIEVED)

    def test_remove_goal(self):
        """测试移除目标"""
        goal = self.evolver.add_goal(name="待移除", description="描述")
        result = self.evolver.remove_goal(goal.goal_id, "测试移除")

        self.assertTrue(result)
        self.assertEqual(goal.status, GoalStatus.ABANDONED)

    def test_adjust_priority(self):
        """测试调整优先级"""
        goal = self.evolver.add_goal(name="优先级测试", description="描述", priority=2)

        result = self.evolver.adjust_priority(goal.goal_id, 5, "提升优先级")
        self.assertTrue(result)
        self.assertEqual(goal.priority, 5)

    def test_auto_prioritize(self):
        """测试自动优先级调整"""
        # 添加一个即将到期的目标
        deadline = datetime.now() + timedelta(hours=12)
        goal = self.evolver.add_goal(
            name="紧急目标",
            description="即将到期",
            priority=2,
            deadline=deadline
        )

        adjustments = self.evolver.auto_prioritize()

        self.assertTrue(len(adjustments) > 0)
        self.assertTrue(goal.priority > 2)

    def test_discover_goals(self):
        """测试目标发现"""
        context = {
            "capability_gaps": [
                {"dimension": "reasoning", "gap_size": 0.5}
            ],
            "error_patterns": [
                {"name": "ErrorPattern", "category": "cognitive", "frequency": 5}
            ],
            "reflection_insights": [
                {"title": "严重问题", "severity": "high", "description": "需要解决"}
            ]
        }

        new_goals = self.evolver.discover_goals(context)

        self.assertTrue(len(new_goals) > 0)

    def test_prune_goals(self):
        """测试目标淘汰"""
        # 添加一个过时的目标
        old_goal = self.evolver.add_goal(name="过时目标", description="描述")
        old_goal.created_at = datetime.now() - timedelta(days=100)

        pruned = self.evolver.prune_goals()

        self.assertTrue(len(pruned) > 0)
        self.assertEqual(old_goal.status, GoalStatus.OBSOLETE)

    def test_evaluate_goal(self):
        """测试目标评估"""
        goal = self.evolver.add_goal(
            name="评估测试",
            description="评估描述",
            deadline=datetime.now() + timedelta(days=7)
        )
        goal.progress = 0.6

        evaluation = self.evolver.evaluate_goal(goal.goal_id)

        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.goal_id, goal.goal_id)
        self.assertEqual(evaluation.completion_rate, 0.6)

    def test_optimize_goal_system(self):
        """测试目标体系优化"""
        self.evolver.add_goal(name="目标1", description="描述1", priority=3)
        self.evolver.add_goal(name="目标2", description="描述2", priority=2)

        report = self.evolver.optimize_goal_system()

        self.assertIsNotNone(report)
        self.assertTrue(report.total_goals > 0)
        self.assertTrue(len(report.recommendations) > 0)

    def test_get_active_goals(self):
        """测试获取活跃目标"""
        self.evolver.add_goal(name="活跃1", description="描述1", priority=3)
        self.evolver.add_goal(name="活跃2", description="描述2", priority=5)

        active = self.evolver.get_active_goals()

        self.assertEqual(len(active), 2)
        # 应该按优先级排序
        self.assertEqual(active[0].priority, 5)

    def test_get_goal_tree(self):
        """测试获取目标树"""
        parent = self.evolver.add_goal(name="父目标", description="父描述")
        child1 = self.evolver.add_goal(name="子目标1", description="子1描述", parent_goal_id=parent.goal_id)
        child2 = self.evolver.add_goal(name="子目标2", description="子2描述", parent_goal_id=parent.goal_id)

        tree = self.evolver.get_goal_tree(parent.goal_id)

        self.assertEqual(tree["goal_id"], parent.goal_id)
        self.assertEqual(len(tree["sub_goals"]), 2)

    def test_get_goals_by_tag(self):
        """测试按标签获取目标"""
        self.evolver.add_goal(name="标签测试1", description="描述1", tags=["important", "urgent"])
        self.evolver.add_goal(name="标签测试2", description="描述2", tags=["important"])

        urgent_goals = self.evolver.get_goals_by_tag("urgent")
        self.assertEqual(len(urgent_goals), 1)

        important_goals = self.evolver.get_goals_by_tag("important")
        self.assertEqual(len(important_goals), 2)

    def test_callback(self):
        """测试回调注册"""
        callback_called = False

        def test_callback(report):
            nonlocal callback_called
            callback_called = True

        self.evolver.register_evolution_callback(test_callback)
        self.evolver.optimize_goal_system()

        self.assertTrue(callback_called)

    def test_reset(self):
        """测试重置"""
        self.evolver.add_goal(name="测试", description="描述")
        self.evolver.optimize_goal_system()
        self.evolver.reset()

        stats = self.evolver.get_stats()
        self.assertEqual(stats["total_goals"], 0)


if __name__ == "__main__":
    unittest.main()
