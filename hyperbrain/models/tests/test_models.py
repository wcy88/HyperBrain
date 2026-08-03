"""
模型模块单元测试

测试大模型集成与调度系统的各个组件。
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from hyperbrain.models.base import (
    BaseModel,
    ChatMessage,
    EmbeddingResponse,
    FinishReason,
    ModelCapability,
    ModelConfig,
    ModelError,
    ModelProvider,
    ModelResponse,
    ModelUsage,
    StreamChunk,
    TaskType,
)
from hyperbrain.models.error_handler import (
    CircuitBreaker,
    CircuitBreakerConfig,
    ErrorCategory,
    ErrorClassifier,
    ErrorHandler,
    RetryConfig,
)
from hyperbrain.models.token_manager import (
    BudgetConfig,
    BudgetAlert,
    AlertLevel,
    AlertType,
    TokenManager,
)
from hyperbrain.models.capability_evaluator import (
    BenchmarkResult,
    CapabilityEvaluator,
    ModelEvaluation,
)
from hyperbrain.models.scheduler import ModelScheduler, ModelInstance


# ============================================================================
# Base Model Tests
# ============================================================================

class MockModel(BaseModel):
    """测试用模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._capabilities = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.EMBEDDING,
        }
        self.is_initialized = True
    
    async def initialize(self) -> bool:
        self.is_initialized = True
        return True
    
    async def chat(self, messages, temperature=None, max_tokens=None, **kwargs):
        return ModelResponse(
            content="Test response",
            provider=self.provider.value,
            model=self.model_name,
            usage=ModelUsage(prompt_tokens=10, completion_tokens=5)
        )
    
    async def stream_chat(self, messages, temperature=None, max_tokens=None, **kwargs):
        yield StreamChunk(content="Test")
        yield StreamChunk(content="", is_finished=True, finish_reason=FinishReason.STOP)
    
    async def complete(self, prompt, temperature=None, max_tokens=None, **kwargs):
        return ModelResponse(
            content="Test completion",
            provider=self.provider.value,
            model=self.model_name
        )
    
    async def embed(self, text, **kwargs):
        return EmbeddingResponse(
            embedding=[0.1, 0.2, 0.3],
            provider=self.provider.value,
            model=self.model_name
        )
    
    async def health_check(self) -> bool:
        return True


class TestBaseModel:
    """测试基础模型类"""
    
    def test_model_config_validation(self):
        """测试模型配置验证"""
        config = ModelConfig(
            model_name="test-model",
            provider=ModelProvider.OPENAI
        )
        assert config.model_name == "test-model"
        assert config.provider == ModelProvider.OPENAI
    
    def test_model_config_invalid_name(self):
        """测试无效模型名称"""
        with pytest.raises(ValueError):
            ModelConfig(model_name="", provider=ModelProvider.OPENAI)
    
    def test_chat_message_creation(self):
        """测试消息创建"""
        msg = ChatMessage.system("System prompt")
        assert msg.role == "system"
        assert msg.content == "System prompt"
        
        msg = ChatMessage.user("Hello", name="Alice")
        assert msg.role == "user"
        assert msg.name == "Alice"
    
    def test_model_response_error_detection(self):
        """测试响应错误检测"""
        response = ModelResponse(
            content="Error: something wrong",
            provider="test",
            model="test"
        )
        assert response.is_error
        
        response = ModelResponse(
            content="Normal response",
            provider="test",
            model="test",
            finish_reason=FinishReason.STOP
        )
        assert not response.is_error
    
    @pytest.mark.asyncio
    async def test_mock_model_chat(self):
        """测试模拟模型对话"""
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        model = MockModel(config)
        await model.initialize()
        
        messages = [ChatMessage.user("Hello")]
        response = await model.chat(messages)
        
        assert response.content == "Test response"
        assert response.usage.prompt_tokens == 10
    
    @pytest.mark.asyncio
    async def test_mock_model_stream(self):
        """测试模拟模型流式响应"""
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        model = MockModel(config)
        
        messages = [ChatMessage.user("Hello")]
        chunks = []
        async for chunk in model.stream_chat(messages):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0].content == "Test"
        assert chunks[1].is_finished


# ============================================================================
# Error Handler Tests
# ============================================================================

class TestErrorHandler:
    """测试错误处理器"""
    
    def test_error_classification(self):
        """测试错误分类"""
        assert ErrorClassifier.classify(Exception("rate limit exceeded")) == ErrorCategory.RATE_LIMIT
        assert ErrorClassifier.classify(Exception("unauthorized")) == ErrorCategory.AUTHENTICATION
        assert ErrorClassifier.classify(Exception("timeout")) == ErrorCategory.TIMEOUT
        assert ErrorClassifier.classify(Exception("connection refused")) == ErrorCategory.NETWORK
    
    def test_retryable_errors(self):
        """测试可重试错误判断"""
        assert ErrorClassifier.is_retryable(Exception("network error"))
        assert ErrorClassifier.is_retryable(Exception("rate limit"))
        assert not ErrorClassifier.is_retryable(Exception("invalid api key"))
    
    def test_retry_config_delay(self):
        """测试重试延迟计算"""
        config = RetryConfig(base_delay=1.0, max_delay=10.0)
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(10) == 10.0  # 被 max_delay 限制
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """测试熔断器"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
        
        # 正常调用
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state.value == "closed"
        
        # 失败调用
        async def fail_func():
            raise Exception("fail")
        
        with pytest.raises(Exception):
            await cb.call(fail_func)
        with pytest.raises(Exception):
            await cb.call(fail_func)
        
        assert cb.state.value == "open"
        
        # 熔断后应该快速失败
        with pytest.raises(ModelError):
            await cb.call(success_func)
    
    @pytest.mark.asyncio
    async def test_error_handler_retry(self):
        """测试错误处理器重试"""
        handler = ErrorHandler()
        
        call_count = 0
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("network error")
            return "success"
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await handler.execute_with_retry(
            flaky_func,
            retry_config=config
        )
        
        assert result == "success"
        assert call_count == 3


# ============================================================================
# Token Manager Tests
# ============================================================================

class TestTokenManager:
    """测试 Token 管理器"""
    
    @pytest.fixture
    def token_manager(self):
        return TokenManager(BudgetConfig(daily_budget=1.0, monthly_budget=10.0))
    
    @pytest.mark.asyncio
    async def test_record_usage(self, token_manager):
        """测试使用记录"""
        usage = ModelUsage(prompt_tokens=100, completion_tokens=50)
        await token_manager.record_usage(
            provider="openai",
            model="gpt-4",
            usage=usage,
            cost=0.01,
            latency_ms=100.0
        )
        
        stats = token_manager.get_usage_stats()
        assert stats["total_requests"] == 1
        assert stats["total_tokens"] == 150
        
        # 验证预算状态已更新
        budget = token_manager.get_budget_status()
        assert budget["daily"]["used"] == 0.01
    
    def test_budget_exceeded(self, token_manager):
        """测试预算超出检测"""
        # 初始状态不应超出
        assert not token_manager.is_budget_exceeded()
        
        # 模拟超出预算
        token_manager.usage_history.append(
            type('obj', (object,), {
                'provider': 'test',
                'model': 'test',
                'usage': ModelUsage(prompt_tokens=1000000, completion_tokens=0),
                'cost': 2.0,
                'timestamp': datetime.now(),
                'latency_ms': 100.0,
                'task_type': 'test'
            })()
        )
        
        assert token_manager.is_budget_exceeded()
    
    def test_can_make_request(self, token_manager):
        """测试请求许可"""
        assert token_manager.can_make_request()
        assert token_manager.can_make_request(estimated_cost=0.5)
        assert not token_manager.can_make_request(estimated_cost=2.0)
    
    def test_budget_status(self, token_manager):
        """测试预算状态"""
        status = token_manager.get_budget_status()
        assert "daily" in status
        assert "monthly" in status
        assert "tokens" in status
        assert status["can_request"] is True


# ============================================================================
# Capability Evaluator Tests
# ============================================================================

class TestCapabilityEvaluator:
    """测试能力评估器"""
    
    @pytest.fixture
    def evaluator(self):
        return CapabilityEvaluator()
    
    @pytest.mark.asyncio
    async def test_evaluate_model(self, evaluator):
        """测试模型评估"""
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        model = MockModel(config)
        
        evaluation = await evaluator.evaluate_model(model, task_types=["chat"])
        
        assert evaluation.model_name == "mock"
        assert evaluation.provider == "openai"
        assert evaluation.overall_score >= 0
        assert len(evaluation.benchmarks) > 0
    
    def test_capability_matrix(self, evaluator):
        """测试能力矩阵"""
        # 添加模拟评估结果
        evaluator.evaluations["openai:gpt-4"] = ModelEvaluation(
            model_name="gpt-4",
            provider="openai",
            overall_score=85.0,
            benchmarks=[],
            capabilities={"chat": 90.0, "code": 80.0}
        )
        
        matrix = evaluator.get_capability_matrix()
        assert len(matrix["models"]) == 1
        assert "chat" in matrix["tasks"]
    
    def test_best_model_for_task(self, evaluator):
        """测试最佳模型选择"""
        evaluator.evaluations["openai:gpt-4"] = ModelEvaluation(
            model_name="gpt-4",
            provider="openai",
            overall_score=85.0,
            benchmarks=[],
            capabilities={"chat": 90.0}
        )
        evaluator.evaluations["anthropic:claude"] = ModelEvaluation(
            model_name="claude",
            provider="anthropic",
            overall_score=80.0,
            benchmarks=[],
            capabilities={"chat": 85.0}
        )
        
        best = evaluator.get_best_model_for_task("chat")
        assert best == "openai:gpt-4"


# ============================================================================
# Scheduler Tests
# ============================================================================

class TestScheduler:
    """测试调度器"""
    
    @pytest.fixture
    def scheduler(self):
        return ModelScheduler()
    
    @pytest.fixture
    def mock_model(self):
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        return MockModel(config)
    
    def test_register_model(self, scheduler, mock_model):
        """测试模型注册"""
        scheduler.register_model("test", mock_model, priority=8)
        
        assert "test" in scheduler.models
        assert scheduler.models["test"].priority == 8
        assert scheduler.default_model == "test"
    
    def test_unregister_model(self, scheduler, mock_model):
        """测试模型注销"""
        scheduler.register_model("test", mock_model)
        scheduler.unregister_model("test")
        
        assert "test" not in scheduler.models
    
    @pytest.mark.asyncio
    async def test_select_model_priority(self, scheduler, mock_model):
        """测试优先级选择"""
        scheduler.register_model("high", mock_model, priority=8)
        
        config2 = ModelConfig(model_name="mock2", provider=ModelProvider.OPENAI)
        model2 = MockModel(config2)
        scheduler.register_model("low", model2, priority=3)
        
        scheduler.set_strategy("priority")
        selected = await scheduler.select_model()
        
        assert selected == mock_model
    
    @pytest.mark.asyncio
    async def test_select_model_round_robin(self, scheduler, mock_model):
        """测试轮询选择"""
        scheduler.register_model("a", mock_model, priority=5)
        
        config2 = ModelConfig(model_name="mock2", provider=ModelProvider.OPENAI)
        model2 = MockModel(config2)
        scheduler.register_model("b", model2, priority=5)
        
        scheduler.set_strategy("round_robin")
        
        selected1 = await scheduler.select_model()
        selected2 = await scheduler.select_model()
        
        assert selected1 != selected2 or scheduler._round_robin_index == 0
    
    @pytest.mark.asyncio
    async def test_chat_with_scheduler(self, scheduler, mock_model):
        """测试调度器对话"""
        scheduler.register_model("test", mock_model, priority=8)
        
        messages = [ChatMessage.user("Hello")]
        response = await scheduler.chat(messages)
        
        assert response.content == "Test response"
        assert scheduler.models["test"].call_count == 1
    
    def test_get_stats(self, scheduler, mock_model):
        """测试统计信息"""
        scheduler.register_model("test", mock_model, priority=8)
        
        stats = scheduler.get_stats()
        assert stats["total_models"] == 1
        assert stats["strategy"] == "adaptive"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 创建组件
        scheduler = ModelScheduler()
        token_manager = TokenManager(BudgetConfig(daily_budget=100.0))
        
        # 注册模型
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        model = MockModel(config)
        scheduler.register_model("test", model, priority=8)
        
        # 执行对话
        messages = [ChatMessage.user("Hello")]
        response = await scheduler.chat(messages)
        
        assert response.content == "Test response"
        
        # 检查统计
        stats = scheduler.get_stats()
        assert stats["total_models"] == 1
        assert stats["models"]["test"]["call_count"] == 1
    
    @pytest.mark.asyncio
    async def test_model_manager_context(self):
        """测试模型管理器上下文管理器"""
        from hyperbrain.models.model_manager import ModelManager
        
        manager = ModelManager(auto_discover=False)
        
        config = ModelConfig(model_name="mock", provider=ModelProvider.OPENAI)
        model = MockModel(config)
        # 直接注入 MockModel 实例
        manager.models["test"] = model
        manager.scheduler.register_model("test", model, priority=8)
        manager._initialized = True
        
        messages = [ChatMessage.user("Hello")]
        response = await manager.chat(messages)
        assert response.content == "Test response"


# ============================================================================
# Model Config Tests
# ============================================================================

class TestModelConfig:
    """测试模型配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ModelConfig(
            model_name="test",
            provider=ModelProvider.OPENAI
        )
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout == 60.0
        assert config.max_retries == 3
    
    def test_temperature_range(self):
        """测试温度范围"""
        with pytest.raises(ValueError):
            ModelConfig(
                model_name="test",
                provider=ModelProvider.OPENAI,
                temperature=3.0
            )
    
    def test_timeout_range(self):
        """测试超时范围"""
        with pytest.raises(ValueError):
            ModelConfig(
                model_name="test",
                provider=ModelProvider.OPENAI,
                timeout=0.5
            )


# ============================================================================
# Stream Chunk Tests
# ============================================================================

class TestStreamChunk:
    """测试流式响应块"""
    
    def test_chunk_creation(self):
        """测试块创建"""
        chunk = StreamChunk(content="Hello")
        assert chunk.content == "Hello"
        assert not chunk.is_finished
        
        chunk = StreamChunk(content="", is_finished=True, finish_reason=FinishReason.STOP)
        assert chunk.is_finished
        assert chunk.finish_reason == FinishReason.STOP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
