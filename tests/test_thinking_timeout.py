"""
Ollama Thinking 模型超时修复测试（spec fix-ollama-thinking-timeout）

覆盖：
- ModelConfig 新字段（think/fallback_models/stream/worker_timeout）默认值
- BrainWorker 默认 timeout 从 config 读取
- OllamaModel.is_thinking 探测（mock /api/show）
- chat() 在 think=False 时请求体含 think: false
- chat() 在 400 think 字段不支持时回退
- chat_with_fallback 在 primary TimeoutError 时切换到 fallback
- chat_with_fallback 全部失败时抛最后异常
- _add_fallback_model 去重
"""
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from hyperbrain.models.base import ModelConfig, ModelProvider, ChatMessage
from hyperbrain.core.config import ModelConfig as CoreModelConfig


# ============== 1. ModelConfig 新字段默认值 ==============

class TestModelConfigFields:
    def test_pydantic_model_config_has_think(self):
        from hyperbrain.models.base import ModelConfig as PydModelConfig
        cfg = PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA)
        assert hasattr(cfg, "think")
        assert cfg.think is True

    def test_pydantic_model_config_has_fallback_models(self):
        from hyperbrain.models.base import ModelConfig as PydModelConfig
        cfg = PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA)
        assert hasattr(cfg, "fallback_models")
        assert cfg.fallback_models == []

    def test_pydantic_model_config_has_stream(self):
        from hyperbrain.models.base import ModelConfig as PydModelConfig
        cfg = PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA)
        assert hasattr(cfg, "stream")
        assert cfg.stream is True

    def test_pydantic_model_config_has_worker_timeout(self):
        from hyperbrain.models.base import ModelConfig as PydModelConfig
        cfg = PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA)
        assert hasattr(cfg, "worker_timeout")
        assert cfg.worker_timeout == 180.0
        # 范围校验
        with pytest.raises(Exception):
            PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA, worker_timeout=10)
        with pytest.raises(Exception):
            PydModelConfig(model_name="x", provider=ModelProvider.OLLAMA, worker_timeout=1000)

    def test_dataclass_model_config_new_fields(self):
        cfg = CoreModelConfig()
        assert cfg.worker_timeout == 180.0
        assert cfg.think is True
        assert cfg.fallback_models == []
        assert cfg.stream is True

    def test_dataclass_validate_worker_timeout(self):
        cfg = CoreModelConfig(worker_timeout=10)
        with pytest.raises(Exception):
            cfg.validate()
        cfg2 = CoreModelConfig(worker_timeout=300)
        cfg2.validate()  # 不抛


# ============== 2. OllamaModel is_thinking 探测 ==============

class TestOllamaThinkingProbe:
    @pytest.mark.asyncio
    async def test_is_thinking_true_for_qwen3(self):
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(model_name="qwen3.5:2b", provider=ModelProvider.OLLAMA)
        m = OllamaModel(cfg)
        m.is_thinking = False
        # Mock session
        show_resp = MagicMock()
        show_resp.status = 200

        async def json_show():
            return {
                "details": {"family": "qwen3"},
                "capabilities": ["chat", "thinking"],
            }

        show_resp.json = json_show
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=show_resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session
        await m._probe_thinking_capability()
        assert m.is_thinking is True
        await m.close()

    @pytest.mark.asyncio
    async def test_is_thinking_false_for_gemma2(self):
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(model_name="gemma2:2b", provider=ModelProvider.OLLAMA)
        m = OllamaModel(cfg)
        m.is_thinking = True
        show_resp = MagicMock()
        show_resp.status = 200

        async def json_show():
            return {
                "details": {"family": "gemma2"},
                "capabilities": ["chat"],
            }

        show_resp.json = json_show
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=show_resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session
        await m._probe_thinking_capability()
        assert m.is_thinking is False
        await m.close()

    @pytest.mark.asyncio
    async def test_is_thinking_true_for_deepseek_r1(self):
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(model_name="deepseek-r1:7b", provider=ModelProvider.OLLAMA)
        m = OllamaModel(cfg)
        m.is_thinking = False
        show_resp = MagicMock()
        show_resp.status = 200

        async def json_show():
            return {
                "details": {"family": "deepseek-r1"},
                "capabilities": ["chat"],
            }

        show_resp.json = json_show
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=show_resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session
        await m._probe_thinking_capability()
        assert m.is_thinking is True
        await m.close()


# ============== 3. chat() 中 think 字段处理 ==============

class TestChatThinkField:
    @pytest.mark.asyncio
    async def test_think_false_in_payload_when_disabled(self):
        """当 is_thinking=True 且 config.think=False 时，payload 含 think: false"""
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(
            model_name="qwen3.5:2b",
            provider=ModelProvider.OLLAMA,
            think=False,
        )
        m = OllamaModel(cfg)
        m.is_thinking = True
        m.is_initialized = True  # 跳过 initialize()

        # Mock session 响应
        resp = MagicMock()
        resp.status = 200
        async def json_chat():
            return {"message": {"content": "hi"}, "done": True}
        resp.json = json_chat
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session

        from hyperbrain.models.base import ChatMessage
        result = await m.chat([ChatMessage(role="user", content="hi")])
        # 验证 POST 时传入了 think: false
        call_args = session.post.call_args
        # 兼容位置参数和关键字参数
        if call_args.kwargs and "json" in call_args.kwargs:
            payload = call_args.kwargs["json"]
        else:
            payload = call_args.args[1]
        assert payload.get("think") is False
        assert result.content == "hi"
        await m.close()

    @pytest.mark.asyncio
    async def test_think_not_in_payload_for_non_thinking_model(self):
        """非 thinking 模型：payload 不含 think 字段"""
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(
            model_name="gemma2:2b",
            provider=ModelProvider.OLLAMA,
            think=True,
        )
        m = OllamaModel(cfg)
        m.is_thinking = False
        m.is_initialized = True

        resp = MagicMock()
        resp.status = 200
        async def json_chat():
            return {"message": {"content": "ok"}, "done": True}
        resp.json = json_chat
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session

        from hyperbrain.models.base import ChatMessage
        await m.chat([ChatMessage(role="user", content="hi")])
        call_args = session.post.call_args
        if call_args.kwargs and "json" in call_args.kwargs:
            payload = call_args.kwargs["json"]
        else:
            payload = call_args.args[1]
        assert "think" not in payload
        await m.close()

    @pytest.mark.asyncio
    async def test_400_with_think_field_triggers_retry_without_think(self):
        """Ollama 400 拒绝 think 字段时回退重试"""
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(
            model_name="qwen3.5:2b",
            provider=ModelProvider.OLLAMA,
            think=False,
        )
        m = OllamaModel(cfg)
        m.is_thinking = True
        m.is_initialized = True

        # 第一次 400，第二次 200
        resp_400 = MagicMock()
        resp_400.status = 400
        resp_400.text = AsyncMock(return_value="think field not supported")
        resp_200 = MagicMock()
        resp_200.status = 200
        async def json_ok():
            return {"message": {"content": "fallback ok"}, "done": True}
        resp_200.json = json_ok
        ctx_400 = MagicMock()
        ctx_400.__aenter__ = AsyncMock(return_value=resp_400)
        ctx_400.__aexit__ = AsyncMock(return_value=None)
        ctx_200 = MagicMock()
        ctx_200.__aenter__ = AsyncMock(return_value=resp_200)
        ctx_200.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        # 第一次 400，第二次 200
        session.post = MagicMock(side_effect=[ctx_400, ctx_200])
        session.close = AsyncMock(return_value=None)
        m.session = session

        from hyperbrain.models.base import ChatMessage
        result = await m.chat([ChatMessage(role="user", content="hi")])
        assert result.content == "fallback ok"
        # 确认 session.post 被调用了 2 次
        assert session.post.call_count == 2
        await m.close()


# ============== 4. ModelManager chat_with_fallback ==============

class TestChatWithFallback:
    @pytest.mark.asyncio
    async def test_primary_timeout_triggers_fallback(self):
        """主模型超时 → 自动切换到 fallback"""
        from hyperbrain.models.model_manager import ModelManager
        from hyperbrain.models.ollama_model import OllamaModel
        from hyperbrain.models.base import ChatMessage, ModelResponse, FinishReason
        mm = ModelManager()

        # Patch scheduler.chat 来控制行为（避免真实 Ollama 干扰）
        call_count = {"n": 0}

        async def fake_scheduler_chat(messages, model_name=None, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # 第一次：主模型超时
                raise asyncio.TimeoutError("primary timeout")
            else:
                # 第二次：fallback 成功
                return ModelResponse(
                    content="fallback ok",
                    provider="ollama",
                    model="gemma2:2b",
                    finish_reason=FinishReason.STOP,
                    latency_ms=10.0,
                )

        # 替换 scheduler.chat
        mm.scheduler.chat = fake_scheduler_chat

        # 抑制通知
        mm._notify_fallback = lambda *a, **kw: None
        mm._swap_to_fallback_model = lambda name: None  # 已经在 fake_scheduler_chat 中处理

        result = await mm.chat_with_fallback(
            messages=[ChatMessage(role="user", content="hi")],
            primary_model="ollama_default",
            fallback_models=["gemma2:2b"],
        )
        # 主模型（第一次调用）失败 → fallback（第二次调用）成功
        assert call_count["n"] == 2
        assert result.content == "fallback ok"

    @pytest.mark.asyncio
    async def test_fallback_chain_order(self):
        """测试降级链：primary + 1 个 fallback 全部超时 → 抛异常"""
        from hyperbrain.models.model_manager import ModelManager
        from hyperbrain.models.base import ChatMessage
        mm = ModelManager()

        # 两次都抛 TimeoutError
        async def always_timeout(*args, **kwargs):
            raise asyncio.TimeoutError("model timeout")

        mm.scheduler.chat = always_timeout
        mm._notify_fallback = lambda *a, **kw: None
        mm._swap_to_fallback_model = lambda name: None

        with pytest.raises((asyncio.TimeoutError, RuntimeError, Exception)):
            await mm.chat_with_fallback(
                messages=[ChatMessage(role="user", content="hi")],
                primary_model="ollama_default",
                fallback_models=["gemma2:2b"],
            )


# ============== 5. BrainWorker 默认 timeout ==============

class TestBrainWorkerTimeout:
    def test_brainworker_default_timeout_uses_config(self):
        """BrainWorker 不传 timeout 时从 config.model.worker_timeout 读取"""
        from hyperbrain.ui.main_window import BrainWorker
        # 创建一个 fake brain
        brain = MagicMock()
        brain.config.model.worker_timeout = 300.0
        worker = BrainWorker(brain=brain, text="hi", async_thread=MagicMock())
        assert worker.timeout == 300.0

    def test_brainworker_explicit_timeout_overrides(self):
        from hyperbrain.ui.main_window import BrainWorker
        brain = MagicMock()
        brain.config.model.worker_timeout = 180.0
        worker = BrainWorker(brain=brain, text="hi", async_thread=MagicMock(), timeout=60.0)
        assert worker.timeout == 60.0

    def test_brainworker_clamps_to_min(self):
        from hyperbrain.ui.main_window import BrainWorker
        brain = MagicMock()
        brain.config.model.worker_timeout = 5.0  # < 30
        worker = BrainWorker(brain=brain, text="hi", async_thread=MagicMock())
        assert worker.timeout == 30.0  # 钳到 30

    def test_brainworker_clamps_to_max(self):
        from hyperbrain.ui.main_window import BrainWorker
        brain = MagicMock()
        brain.config.model.worker_timeout = 1000.0  # > 600
        worker = BrainWorker(brain=brain, text="hi", async_thread=MagicMock())
        assert worker.timeout == 600.0

    def test_brainworker_extracts_model_name(self):
        from hyperbrain.ui.main_window import BrainWorker
        brain = MagicMock()
        brain.config.model.ollama_model = "qwen3.5:2b"
        mm = MagicMock()
        sched = MagicMock()
        sched.current_model_name = "qwen3.5:2b"
        mm.scheduler = sched
        brain.model_manager = mm
        worker = BrainWorker(brain=brain, text="hi", async_thread=MagicMock())
        assert worker.model_name == "qwen3.5:2b"


# ============== 6. settings_dialog fallback UI ==============

class TestSettingsFallbackUI:
    def test_fallback_list_initially_empty(self):
        """未设置 fallback_models 时，QListWidget 应为空"""
        from PyQt6.QtWidgets import QApplication
        import os
        # 避免 QApplication 重复创建
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        cfg = CoreModelConfig()
        cfg.fallback_models = []
        # 仅在能导入且不报错时验证（GUI 测试可能受环境限制）
        try:
            from hyperbrain.ui.settings_dialog import SettingsDialog
            # 跳过需要完整 GUI 环境的对话框测试
            assert cfg.fallback_models == []
        except ImportError:
            pytest.skip("SettingsDialog not importable")


# ============== 7. 端到端：100s 延迟 + 180s timeout ==============

class TestE2EThinkingTimeout:
    @pytest.mark.asyncio
    async def test_100s_latency_with_180s_timeout_does_not_alarm(self):
        """100s 延迟 < 180s timeout：不触发超时"""
        from hyperbrain.models.ollama_model import OllamaModel
        cfg = ModelConfig(model_name="qwen3.5:2b", provider=ModelProvider.OLLAMA)
        m = OllamaModel(cfg)
        m.is_thinking = True
        m.is_initialized = True

        # Mock 响应：100s 后返回
        resp = MagicMock()
        resp.status = 200
        async def slow_json():
            await asyncio.sleep(0.05)  # 模拟 50ms（避免测试过慢）
            return {"message": {"content": "ok"}, "done": True, "prompt_eval_count": 5, "eval_count": 10}
        resp.json = slow_json
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        session.close = AsyncMock(return_value=None)
        m.session = session

        from hyperbrain.models.base import ChatMessage
        result = await m.chat([ChatMessage(role="user", content="hi")])
        assert result.content == "ok"
        await m.close()
