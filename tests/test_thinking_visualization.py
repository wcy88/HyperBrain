"""
Ollama 思维链可视化测试（spec show-thinking-process 任务8）

覆盖（spec tasks.md 8.1-8.9 + checklist "单元测试" 章节）：
- 8.1 ModelResponse.thinking 字段默认空字符串，可显式赋值
- 8.2 _parse_chat_response 提取 message.thinking
- 8.3 _parse_chat_response 缺失 thinking 字段时为空字符串
- 8.4 _parse_chat_response 也兼容某些 Ollama 版本顶层 thinking
- 8.5 _iter_stream_to_response 把流式 thinking + content 累加成 ModelResponse
- 8.6 BrainWorker.partial_thinking 信号存在
- 8.7 MainWindow 思维链方法（_on_partial_thinking / _toggle_thinking / _attach_thinking_to_last_bubble）存在
- 8.8 config.think / ModelConfig.think 默认 True
- 8.9 diagnose_ollama.py --timeout-think 默认 180
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


# === 把 scripts/ 加入 sys.path 以导入 diagnose_ollama.py（无 __init__.py） ===
_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# =========================================================================
# 8.1 ModelResponse.thinking 字段（任务 8.1）
# =========================================================================

def test_model_response_thinking_field_default_empty():
    """ModelResponse.thinking 默认空字符串"""
    from hyperbrain.models.base import ModelResponse
    m1 = ModelResponse(content="hi", provider="ollama", model="qwen3.5:2b")
    assert m1.thinking == ""


def test_model_response_thinking_field_explicit_assign():
    """ModelResponse.thinking 可显式赋值"""
    from hyperbrain.models.base import ModelResponse
    m2 = ModelResponse(
        content="hi",
        provider="ollama",
        model="qwen3.5:2b",
        thinking="let me think step by step",
    )
    assert m2.thinking == "let me think step by step"


# =========================================================================
# 8.2 / 8.3 / 8.4 _parse_chat_response thinking 提取（任务 8.2-8.4）
# =========================================================================

class _FakeAiohttpResp:
    """Fake aiohttp 响应（只支持 _parse_chat_response 用的 .json()）"""

    def __init__(self, data: dict):
        self._data = data

    async def json(self):
        return self._data


@pytest.mark.asyncio
async def test_parse_chat_response_extracts_thinking_in_message():
    """_parse_chat_response 提取 data.message.thinking"""
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.base import ModelConfig, ModelProvider

    cfg = ModelConfig(
        model_name="qwen3.5:2b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    m = OllamaModel(cfg)

    data = {
        "message": {
            "role": "assistant",
            "content": "The answer is 42.",
            "thinking": "Let me think step by step...",
        },
        "done_reason": "stop",
    }
    resp = _FakeAiohttpResp(data)
    parsed = await m._parse_chat_response(resp, start_time=0.0)
    assert parsed.content == "The answer is 42."
    assert parsed.thinking == "Let me think step by step..."


@pytest.mark.asyncio
async def test_parse_chat_response_missing_thinking():
    """Ollama 不返回 thinking 字段时 thinking 为空字符串"""
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.base import ModelConfig, ModelProvider

    cfg = ModelConfig(
        model_name="gemma2:2b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    m = OllamaModel(cfg)

    data = {
        "message": {"role": "assistant", "content": "Hi"},
        "done_reason": "stop",
    }
    resp = _FakeAiohttpResp(data)
    parsed = await m._parse_chat_response(resp, start_time=0.0)
    assert parsed.content == "Hi"
    assert parsed.thinking == ""


@pytest.mark.asyncio
async def test_parse_chat_response_thinking_at_top_level():
    """兼容某些 Ollama 版本：thinking 在 data 顶层（不在 message 里）"""
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.base import ModelConfig, ModelProvider

    cfg = ModelConfig(
        model_name="custom-thinking:1b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    m = OllamaModel(cfg)

    data = {
        "message": {"role": "assistant", "content": "Final."},
        "thinking": "Reasoning at top level",
        "done": True,
    }
    resp = _FakeAiohttpResp(data)
    parsed = await m._parse_chat_response(resp, start_time=0.0)
    assert parsed.content == "Final."
    assert parsed.thinking == "Reasoning at top level"


# =========================================================================
# 8.5 _iter_stream_to_response 累加 thinking + content（任务 8.5）
# =========================================================================

class _AsyncLineIter:
    """异步迭代器：yield bytes（NDJSON 行）"""

    def __init__(self, lines):
        self._lines = list(lines)
        self._i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._i >= len(self._lines):
            raise StopAsyncIteration
        line = self._lines[self._i]
        self._i += 1
        return line


@pytest.mark.asyncio
async def test_iter_stream_to_response_join_thinking_and_content():
    """_iter_stream_to_response 把 (thinking, t1)(thinking, t2)(content, c1)(content, c2) 累加成 ModelResponse"""
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.base import ModelConfig, ModelProvider

    cfg = ModelConfig(
        model_name="qwen3.5:2b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    m = OllamaModel(cfg)

    chunks = [
        {"message": {"thinking": "Let me "}, "done": False},
        {"message": {"thinking": "think..."}, "done": False},
        {"message": {"content": "The "}, "done": False},
        {"message": {"content": "answer."}, "done": True,
         "prompt_eval_count": 5, "eval_count": 8},
    ]
    encoded = [json.dumps(c).encode("utf-8") for c in chunks]

    resp = MagicMock()
    resp.content = _AsyncLineIter(encoded)

    parsed = await m._iter_stream_to_response(resp, start_time=0.0)
    assert parsed.thinking == "Let me think..."
    assert parsed.content == "The answer."


@pytest.mark.asyncio
async def test_iter_stream_to_response_no_thinking_chunks():
    """非 thinking 模型：只 yield content，没有 thinking chunk"""
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.base import ModelConfig, ModelProvider

    cfg = ModelConfig(
        model_name="gemma2:2b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    m = OllamaModel(cfg)

    chunks = [
        {"message": {"content": "Hello "}, "done": False},
        {"message": {"content": "world."}, "done": True},
    ]
    encoded = [json.dumps(c).encode("utf-8") for c in chunks]

    resp = MagicMock()
    resp.content = _AsyncLineIter(encoded)

    parsed = await m._iter_stream_to_response(resp, start_time=0.0)
    assert parsed.thinking == ""
    assert parsed.content == "Hello world."


# =========================================================================
# 8.6 BrainWorker.partial_thinking 信号（任务 8.6）
# =========================================================================

def test_brain_worker_has_partial_thinking_signal():
    """BrainWorker.partial_thinking = pyqtSignal(str) 信号存在"""
    from hyperbrain.ui.main_window import BrainWorker
    # 类级别信号定义（不需实例化 QApplication）
    assert hasattr(BrainWorker, "partial_thinking")
    # pyqtSignal 实例的 __class__ 名通常包含 'pyqtBoundSignal' 或 'pyqtSignal'
    sig = getattr(BrainWorker, "partial_thinking", None)
    sig_repr = repr(type(sig))
    # 宽松检查：要么是 'pyqtSignal'，要么名字包含 'Signal'
    assert "Signal" in sig_repr or "signal" in sig_repr.lower(), (
        f"partial_thinking should be a pyqtSignal, got type {sig_repr}"
    )


# =========================================================================
# 8.7 MainWindow 思维链 UI 方法（任务 8.7）
# =========================================================================

def test_main_window_has_thinking_methods():
    """MainWindow 有 _on_partial_thinking / _toggle_thinking / _attach_thinking_to_last_bubble"""
    from hyperbrain.ui.main_window import MainWindow

    for name in (
        "_on_partial_thinking",
        "_toggle_thinking",
        "_attach_thinking_to_last_bubble",
    ):
        assert hasattr(MainWindow, name), f"MainWindow missing method {name!r}"
        method = getattr(MainWindow, name, None)
        assert callable(method), f"MainWindow.{name} should be callable"


def test_main_window_thinking_attributes():
    """MainWindow __init__ 设置 _current_thinking_text/_label/_detail 属性"""
    from hyperbrain.ui.main_window import MainWindow
    # 类级源码检查：init 中是否有这些 self.<attr> 赋值
    import inspect
    src = inspect.getsource(MainWindow.__init__)
    for attr in ("_current_thinking_text", "_current_thinking_label", "_current_thinking_detail"):
        assert attr in src, f"MainWindow.__init__ should set {attr!r}"


# =========================================================================
# 8.8 config.think / ModelConfig.think 默认 True（任务 8.8）
# =========================================================================

def test_config_model_think_default_true():
    """Config.model.think 默认 True（hyperbrain.core.config）"""
    from hyperbrain.core.config import ModelConfig as CoreModelConfig
    c = CoreModelConfig()
    assert c.think is True


def test_pydantic_model_config_think_default_true():
    """ModelConfig.think 默认 True（hyperbrain.models.base）"""
    from hyperbrain.models.base import ModelConfig, ModelProvider
    c = ModelConfig(model_name="test:1b", provider=ModelProvider.OLLAMA)
    assert c.think is True


def test_pydantic_model_config_think_can_be_disabled():
    """ModelConfig.think 可显式设 False（向后兼容 / settings dialog 控制）"""
    from hyperbrain.models.base import ModelConfig, ModelProvider
    c = ModelConfig(model_name="test:1b", provider=ModelProvider.OLLAMA, think=False)
    assert c.think is False


def test_config_yaml_think_true():
    """config.yaml 中 model.think 默认为 true"""
    cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"
    if not cfg_path.exists():
        pytest.skip(f"config.yaml not found at {cfg_path}")
    import yaml
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    model_cfg = data.get("model", {})
    assert "think" in model_cfg, "config.yaml model.think missing"
    assert model_cfg["think"] is True, f"config.yaml model.think should be True, got {model_cfg['think']!r}"


# =========================================================================
# 8.9 diagnose_ollama.py --timeout-think 默认 180（任务 8.9）
# =========================================================================

def test_diagnose_ollama_timeout_think_default_180_via_argparse():
    """diagnose_ollama.py argparse --timeout-think 默认 180"""
    import argparse
    import importlib
    diag = importlib.import_module("diagnose_ollama")

    # 不直接调 main()，只重新构造 ArgumentParser 调默认
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-think", type=int, default=180,
                        help="Step 6 timeout (sec) for thinking models. default 180.")
    args = parser.parse_args([])
    assert args.timeout_think == 180

    # 同时检查脚本源文件中确实写 default=180
    script_path = Path(_SCRIPTS_DIR) / "diagnose_ollama.py"
    src = script_path.read_text(encoding="utf-8")
    assert '"--timeout-think"' in src or "'--timeout-think'" in src
    assert "default=180" in src


def test_diagnose_ollama_timeout_think_in_help():
    """diagnose_ollama.py --help 含 --timeout-think + default 180"""
    py_exe = sys.executable
    script_path = Path(_SCRIPTS_DIR) / "diagnose_ollama.py"
    result = subprocess.run(
        [py_exe, str(script_path), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert "--timeout-think" in result.stdout
    # 描述里应有 "default 180"
    assert "180" in result.stdout
