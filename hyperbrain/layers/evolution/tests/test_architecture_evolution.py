"""
认知架构进化模块单元测试
"""

import unittest

from hyperbrain.layers.evolution.architecture_evolution import (
    ArchitectureEvolver, ArchitectureEvolutionConfig,
    ModuleType, ConnectionType,
    ArchitectureModule, ModuleConnection
)


class TestArchitectureEvolver(unittest.TestCase):
    """测试认知架构进化模块"""

    def setUp(self):
        """测试前置"""
        self.config = ArchitectureEvolutionConfig(
            max_modules=20,
            enable_auto_restructure=False
        )
        self.evolver = ArchitectureEvolver(config=self.config)

    def tearDown(self):
        """测试后置"""
        self.evolver.reset()

    def test_default_architecture(self):
        """测试默认架构初始化"""
        stats = self.evolver.get_stats()

        self.assertTrue(stats["total_modules"] > 0)
        self.assertTrue(stats["total_connections"] > 0)
        self.assertIsNotNone(stats["current_version"])

    def test_register_module(self):
        """测试注册模块"""
        module = self.evolver.register_module(
            name="测试模块",
            module_type=ModuleType.CUSTOM,
            capabilities=["test_capability"],
            version="1.0.0"
        )

        self.assertIsNotNone(module.module_id)
        self.assertEqual(module.name, "测试模块")
        self.assertEqual(module.module_type, ModuleType.CUSTOM)

    def test_unregister_module(self):
        """测试注销模块"""
        module = self.evolver.register_module(
            name="待注销",
            module_type=ModuleType.CUSTOM
        )

        result = self.evolver.unregister_module(module.module_id)
        self.assertTrue(result)
        self.assertEqual(module.status, "deprecated")

    def test_add_connection(self):
        """测试添加连接"""
        module1 = self.evolver.register_module("模块1", ModuleType.COGNITIVE)
        module2 = self.evolver.register_module("模块2", ModuleType.MEMORY)

        conn = self.evolver.add_connection(
            source_module_id=module1.module_id,
            target_module_id=module2.module_id,
            connection_type=ConnectionType.BIDIRECTIONAL,
            weight=2.0,
            bandwidth=5.0
        )

        self.assertIsNotNone(conn)
        self.assertEqual(conn.connection_type, ConnectionType.BIDIRECTIONAL)
        self.assertEqual(conn.weight, 2.0)

    def test_update_module_performance(self):
        """测试更新模块性能"""
        module = self.evolver.register_module("性能测试", ModuleType.COGNITIVE)

        result = self.evolver.update_module_performance(
            module_id=module.module_id,
            performance_score=0.9,
            resource_usage=0.3
        )

        self.assertTrue(result)
        self.assertEqual(module.performance_score, 0.9)
        self.assertEqual(module.resource_usage, 0.3)

    def test_record_information_flow(self):
        """测试记录信息流"""
        modules = list(self.evolver._modules.values())
        if len(modules) >= 2:
            flow = self.evolver.record_information_flow(
                source_module_id=modules[0].module_id,
                target_module_id=modules[1].module_id,
                data_type="test_data",
                volume=10.0,
                priority=0.8
            )

            self.assertIsNotNone(flow)
            self.assertEqual(flow.data_type, "test_data")
            self.assertEqual(flow.volume, 10.0)

    def test_analyze_information_flow(self):
        """测试信息流分析"""
        modules = list(self.evolver._modules.values())
        if len(modules) >= 2:
            for i in range(5):
                self.evolver.record_information_flow(
                    source_module_id=modules[0].module_id,
                    target_module_id=modules[1].module_id,
                    data_type="test",
                    volume=5.0
                )

        analysis = self.evolver.analyze_information_flow()

        self.assertIn("total_flows", analysis)
        self.assertIn("module_traffic", analysis)

    def test_evaluate_architecture(self):
        """测试架构评估"""
        metrics = self.evolver.evaluate_architecture()

        self.assertIsNotNone(metrics)
        self.assertTrue(0.0 <= metrics.overall_performance <= 1.0)
        self.assertTrue(0.0 <= metrics.modularity_score <= 1.0)
        self.assertTrue(0.0 <= metrics.integration_efficiency <= 1.0)

    def test_optimize_connections(self):
        """测试连接优化"""
        modules = list(self.evolver._modules.values())
        if len(modules) >= 2:
            # 先添加信息流
            for i in range(10):
                self.evolver.record_information_flow(
                    source_module_id=modules[0].module_id,
                    target_module_id=modules[1].module_id,
                    data_type="test",
                    volume=8.0
                )

        optimized = self.evolver.optimize_connections()

        # 即使没有优化也应该返回列表
        self.assertIsInstance(optimized, list)

    def test_evolve_architecture(self):
        """测试架构进化"""
        report = self.evolver.evolve_architecture()

        self.assertIsNotNone(report)
        self.assertIsNotNone(report.metrics)
        self.assertTrue(len(report.summary) > 0)

    def test_save_version(self):
        """测试保存版本"""
        version = self.evolver.save_version(changes=["测试变更"])

        self.assertIsNotNone(version)
        self.assertTrue(len(version.changes) > 0)

    def test_version_history(self):
        """测试版本历史"""
        self.evolver.save_version(changes=["变更1"])
        self.evolver.save_version(changes=["变更2"])

        history = self.evolver.get_version_history()

        self.assertTrue(len(history) >= 2)

    def test_rollback_version(self):
        """测试版本回滚"""
        # 保存初始版本
        initial_version = self.evolver.save_version(changes=["初始"])
        initial_module_count = len(self.evolver._modules)

        # 添加新模块
        new_module = self.evolver.register_module("新模块", ModuleType.CUSTOM)

        # 回滚
        result = self.evolver.rollback_version(initial_version.version_number)
        self.assertTrue(result)

        # 新模块应该被移除
        self.assertNotIn(new_module.module_id, self.evolver._modules)

    def test_get_architecture_graph(self):
        """测试获取架构图"""
        graph = self.evolver.get_architecture_graph()

        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertTrue(len(graph["nodes"]) > 0)

    def test_get_module_connections(self):
        """测试获取模块连接"""
        modules = list(self.evolver._modules.values())
        if modules:
            connections = self.evolver.get_module_connections(modules[0].module_id)

            self.assertIn("incoming", connections)
            self.assertIn("outgoing", connections)

    def test_callback(self):
        """测试回调注册"""
        callback_called = False

        def test_callback(report):
            nonlocal callback_called
            callback_called = True

        self.evolver.register_evolution_callback(test_callback)
        self.evolver.evolve_architecture()

        self.assertTrue(callback_called)

    def test_reset(self):
        """测试重置"""
        self.evolver.register_module("测试", ModuleType.CUSTOM)
        self.evolver.evolve_architecture()
        self.evolver.reset()

        stats = self.evolver.get_stats()
        # 重置后应该恢复默认架构
        self.assertTrue(stats["total_modules"] > 0)


if __name__ == "__main__":
    unittest.main()
