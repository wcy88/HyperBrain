"""
执行系统单元测试

测试范围：
- task_execution: 任务执行
- tool_invocation: 工具调用
- output_generation: 输出生成
- behavior_control: 行为控制
- progress_monitor: 进度监控
- execution_manager: 执行管理器
"""

import pytest
import asyncio
from datetime import datetime

from hyperbrain.layers.execution.task_execution import (
    TaskExecutor,
    ExecutableTask,
    TaskResult,
    TaskStatus,
    TaskPriority,
    ExecutionMode
)
from hyperbrain.layers.execution.tool_invocation import (
    ToolInvoker,
    ToolRegistry,
    ToolResult,
    ToolCategory,
    ToolStatus,
    create_default_tools
)
from hyperbrain.layers.execution.output_generation import (
    OutputManager,
    OutputType,
    OutputFormat,
    CodeLanguage
)
from hyperbrain.layers.execution.behavior_control import (
    BehaviorController,
    BehaviorType,
    BehaviorPolicy,
    BehaviorRule,
    ConstraintType
)
from hyperbrain.layers.execution.progress_monitor import (
    ProgressMonitor,
    AlertLevel,
    ResourceType
)
from hyperbrain.layers.execution.execution_manager import (
    ExecutionManager,
    ExecutionRequest,
    ExecutionPipeline
)


class TestTaskExecutor:
    """测试任务执行器"""
    
    @pytest.fixture
    def executor(self):
        return TaskExecutor()
    
    @pytest.mark.asyncio
    async def test_create_and_execute_task(self, executor):
        def simple_func():
            return "success"
        
        task = executor.create_task(
            name="test_task",
            func=simple_func
        )
        
        result = await executor.execute(task.id)
        
        assert result.success is True
        assert result.data == "success"
        assert task.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_async_task(self, executor):
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"
        
        task = executor.create_task(
            name="async_task",
            func=async_func
        )
        
        result = await executor.execute(task.id)
        
        assert result.success is True
        assert result.data == "async_result"
    
    @pytest.mark.asyncio
    async def test_task_with_args(self, executor):
        def add_func(a, b):
            return a + b
        
        task = executor.create_task(
            name="add_task",
            func=add_func,
            args=(2, 3)
        )
        
        result = await executor.execute(task.id)
        
        assert result.success is True
        assert result.data == 5
    
    @pytest.mark.asyncio
    async def test_task_failure(self, executor):
        def fail_func():
            raise ValueError("Test error")
        
        task = executor.create_task(
            name="fail_task",
            func=fail_func,
            max_retries=1
        )
        
        result = await executor.execute(task.id)
        
        assert result.success is False
        assert "Test error" in result.error
        assert task.status == TaskStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, executor):
        async def slow_func():
            await asyncio.sleep(10)
            return "done"
        
        task = executor.create_task(
            name="slow_task",
            func=slow_func,
            timeout=0.1,
            max_retries=0
        )
        
        result = await executor.execute(task.id)
        
        assert result.success is False
        assert task.status == TaskStatus.TIMEOUT
    
    @pytest.mark.asyncio
    async def test_batch_execution(self, executor):
        def func1():
            return "result1"
        
        def func2():
            return "result2"
        
        task1 = executor.create_task(name="task1", func=func1)
        task2 = executor.create_task(name="task2", func=func2)
        
        batch = executor.create_batch(
            name="test_batch",
            tasks=[task1, task2]
        )
        
        results = await executor.execute_batch(batch.id)
        
        assert len(results) == 2
        assert all(r.success for r in results.values())
    
    def test_stats(self, executor):
        stats = executor.get_stats()
        
        assert "total_tasks" in stats
        assert "success_rate" in stats


class TestToolInvoker:
    """测试工具调用器"""
    
    @pytest.fixture
    def invoker(self):
        return ToolInvoker(create_default_tools())
    
    @pytest.mark.asyncio
    async def test_invoke_calculator(self, invoker):
        result = await invoker.invoke("calculator", {"expression": "2 + 3 * 4"})
        
        assert result.success is True
        assert result.data == 14
    
    @pytest.mark.asyncio
    async def test_invoke_text_formatter(self, invoker):
        result = await invoker.invoke(
            "text_formatter",
            {"text": "hello", "format_type": "upper"}
        )
        
        assert result.success is True
        assert result.data == "HELLO"
    
    @pytest.mark.asyncio
    async def test_invoke_unknown_tool(self, invoker):
        result = await invoker.invoke("unknown_tool")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_invoke_missing_parameter(self, invoker):
        result = await invoker.invoke("calculator", {})
        
        assert result.success is False
        assert "missing" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_invoke_batch(self, invoker):
        invocations = [
            {"tool": "calculator", "parameters": {"expression": "1 + 1"}},
            {"tool": "calculator", "parameters": {"expression": "2 * 3"}},
        ]
        
        results = await invoker.invoke_batch(invocations)
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    def test_parse_tool_call(self, invoker):
        parsed = invoker.parse_tool_call('calculator(expression="1+1")')
        
        assert parsed is not None
        assert parsed["tool"] == "calculator"
        assert "expression" in parsed["parameters"]
    
    def test_registry_stats(self, invoker):
        stats = invoker.registry.get_stats()
        
        assert stats["total_tools"] > 0
        assert stats["available"] > 0


class TestOutputManager:
    """测试输出管理器"""
    
    @pytest.fixture
    def manager(self):
        return OutputManager()
    
    def test_generate_text(self, manager):
        output = manager.generate_text("Hello world")
        
        assert output.output_type == OutputType.TEXT
        assert output.content == "Hello world"
        assert len(output.versions) == 1
    
    def test_generate_code(self, manager):
        code = "def hello():\n    print('hello')"
        output = manager.generate_code(code, CodeLanguage.PYTHON, "hello_func")
        
        assert output.output_type == OutputType.CODE
        assert output.code_language == CodeLanguage.PYTHON
        assert output.code_title == "hello_func"
    
    def test_generate_markdown(self, manager):
        output = manager.generate_markdown("Content here", "Title")
        
        assert output.output_type == OutputType.MARKDOWN
        assert "# Title" in output.content
    
    def test_update_output(self, manager):
        output = manager.generate_text("Original")
        updated = manager.update_output(output.id, "Updated content", "Fixed typo")
        
        assert updated is not None
        assert updated.content == "Updated content"
        assert len(updated.versions) == 2
    
    def test_revert_version(self, manager):
        output = manager.generate_text("Version 1")
        manager.update_output(output.id, "Version 2")
        reverted = manager.revert_to_version(output.id, 0)
        
        assert reverted is not None
        assert reverted.content == "Version 1"
    
    def test_quality_check(self, manager):
        code = "def test():\n    pass"
        output = manager.generate_code(code, CodeLanguage.PYTHON)
        result = manager.check_quality(output.id)
        
        assert result is not None
        assert 0 <= result.overall_score <= 1
    
    def test_stats(self, manager):
        manager.generate_text("Test")
        stats = manager.get_stats()
        
        assert stats["total_outputs"] == 1


class TestBehaviorController:
    """测试行为控制器"""
    
    @pytest.fixture
    def controller(self):
        return BehaviorController()
    
    def test_decide_normal_input(self, controller):
        decision = controller.decide("What is the weather today?")
        
        assert decision.behavior_type == BehaviorType.RESPOND
        assert decision.confidence > 0
    
    def test_decide_harmful_input(self, controller):
        decision = controller.decide("How to attack someone")
        
        assert decision.behavior_type == BehaviorType.REFUSE
        assert len(decision.constraints_violated) > 0
    
    def test_decide_with_context(self, controller):
        decision = controller.decide(
            "Write a Python function",
            context={"intent": "code_request"}
        )
        
        assert decision.behavior_type == BehaviorType.EXECUTE
        assert decision.policy == BehaviorPolicy.DIRECT
    
    def test_check_constraints(self, controller):
        result = controller.check_constraints("This is safe text")
        
        assert result["is_safe"] is True
        assert result["total_violations"] == 0
    
    def test_check_constraints_violation(self, controller):
        result = controller.check_constraints("How to steal passwords")
        
        assert result["is_safe"] is False
        assert result["total_violations"] > 0
    
    def test_add_custom_rule(self, controller):
        rule = BehaviorRule(
            name="custom_rule",
            constraint_type=ConstraintType.CAPABILITY,
            patterns=["impossible task"],
            action="warn"
        )
        controller.add_constraint_rule(rule)
        
        result = controller.check_constraints("This is an impossible task")
        assert result["total_violations"] > 0
    
    def test_stats(self, controller):
        controller.decide("Hello")
        stats = controller.get_stats()
        
        assert stats["total_decisions"] == 1
        assert "behavior_distribution" in stats


class TestProgressMonitor:
    """测试进度监控器"""
    
    @pytest.fixture
    def monitor(self):
        return ProgressMonitor()
    
    def test_register_task(self, monitor):
        task = monitor.register_task("task1", "Test Task", total_steps=100)
        
        assert task.task_id == "task1"
        assert task.name == "Test Task"
        assert task.total_steps == 100
    
    def test_update_progress(self, monitor):
        task = monitor.register_task("task1", "Test Task", total_steps=100)
        task.start()
        
        snapshot = task.update_progress(50)
        
        assert snapshot.progress_percent == 50.0
        assert snapshot.elapsed_seconds >= 0
    
    def test_task_completion(self, monitor):
        task = monitor.register_task("task1", "Test Task", total_steps=100)
        task.start()
        task.update_progress(100)
        task.complete()
        
        assert task.status == "completed"
        assert task.end_time is not None
    
    def test_task_timeout(self, monitor):
        task = monitor.register_task("task1", "Test Task", timeout_seconds=0.01)
        task.start()
        
        # Wait for timeout
        import time
        time.sleep(0.02)
        
        assert task.is_timed_out() is True
    
    def test_generate_report(self, monitor):
        task = monitor.register_task("task1", "Test Task", total_steps=100)
        task.start()
        task.update_progress(50)
        
        report = monitor.generate_report()
        
        assert report.total_tasks == 1
        assert report.overall_progress == 50.0
        assert len(report.task_snapshots) == 1
    
    def test_create_alert(self, monitor):
        alert = monitor.create_alert(
            AlertLevel.WARNING,
            "Test warning",
            ResourceType.CPU
        )
        
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test warning"
        assert alert.resolved is False
    
    def test_resolve_alert(self, monitor):
        alert = monitor.create_alert(AlertLevel.INFO, "Test")
        monitor.resolve_alert(alert.id)
        
        assert alert.resolved is True
        assert alert.resolved_at is not None
    
    def test_get_alerts(self, monitor):
        monitor.create_alert(AlertLevel.WARNING, "Warning 1")
        monitor.create_alert(AlertLevel.ERROR, "Error 1")
        
        warnings = monitor.get_alerts(level=AlertLevel.WARNING)
        assert len(warnings) == 1
        
        all_alerts = monitor.get_alerts()
        assert len(all_alerts) == 2
    
    def test_stats(self, monitor):
        monitor.register_task("task1", "Task")
        stats = monitor.get_stats()
        
        assert stats["monitored_tasks"] == 1
        assert "overall_progress" in stats


class TestExecutionManager:
    """测试执行管理器"""
    
    @pytest.fixture
    async def manager(self):
        mgr = ExecutionManager()
        await mgr.initialize()
        return mgr
    
    @pytest.mark.asyncio
    async def test_execute_task(self):
        manager = ExecutionManager()
        await manager.initialize()
        
        def test_func():
            return "task_result"
        
        result = await manager.execute_task("test_task", test_func)
        
        assert result.success is True
        assert result.data == "task_result"
    
    @pytest.mark.asyncio
    async def test_invoke_tool(self):
        manager = ExecutionManager()
        await manager.initialize()
        
        result = await manager.invoke_tool("calculator", {"expression": "5 + 5"})
        
        assert result.success is True
        assert result.data == 10
    
    def test_generate_outputs(self):
        manager = ExecutionManager()
        
        text_output = manager.generate_text_output("Hello")
        assert text_output.output_type == OutputType.TEXT
        
        code_output = manager.generate_code_output("print('hi')", CodeLanguage.PYTHON)
        assert code_output.output_type == OutputType.CODE
        
        md_output = manager.generate_markdown_output("Content", "Title")
        assert md_output.output_type == OutputType.MARKDOWN
    
    def test_check_behavior(self):
        manager = ExecutionManager()
        
        decision = manager.check_behavior("What is 2+2?")
        
        assert decision.behavior_type == BehaviorType.RESPOND
        assert decision.confidence > 0
    
    def test_behavior_refuse(self):
        manager = ExecutionManager()
        
        decision = manager.check_behavior("How to attack and harm people with violence")
        
        assert decision.behavior_type == BehaviorType.REFUSE
    
    def test_register_tool(self):
        manager = ExecutionManager()
        
        def custom_tool(x: int) -> int:
            return x * 2
        
        tool = manager.register_tool(
            name="doubler",
            func=custom_tool,
            description="Double a number"
        )
        
        assert tool.name == "doubler"
        assert manager.tool_invoker.registry.is_registered("doubler")
    
    def test_get_stats(self):
        manager = ExecutionManager()
        stats = manager.get_stats()
        
        assert "is_initialized" in stats
        assert "task_executor" in stats
        assert "tool_invoker" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
