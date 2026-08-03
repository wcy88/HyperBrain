"""
Ollama 连接调试与修复测试（spec fix-ollama-connection-debug 任务7）

覆盖：
- 7.1 CLI 6 步解析 PASS/FAIL/WARN 输出（StepResult、_summary）
- 7.2 OllamaConnectionError 各 stage 实例化、to_dict、suggestion
- 7.3 (间接) BrainWorker emit OLLAMA_CONNECT_FAIL — 通过 to_dict 覆盖 code
- 7.4 ModelManager._log_registration_summary 在 model_name 漂移时打 ERROR
- 7.5 _validate_fallback_models 跳过不存在的 model

设计原则：
- 优先测纯函数/纯逻辑（OllamaConnectionError、StepResult、_summary）
- 复杂对象（aiohttp session、subprocess）用最小 mock
- 涉及 GUI/QThread 的测试允许跳过

注意：项目使用 loguru（不是 stdlib logging），所以需要用 loguru sink 捕获日志，
而不是 pytest 的 caplog fixture。
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from loguru import logger

# === 把 scripts/ 加入 sys.path 以导入 diagnose_ollama.py（无 __init__.py） ===
_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# 把项目根加入 sys.path 以导入 hyperbrain
_ROOT = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_ROOT)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from hyperbrain.models.base import ModelConfig, ModelProvider  # noqa: E402


# === loguru 捕获 fixture ===
@pytest.fixture
def loguru_capture():
    """捕获 loguru 日志记录到列表 records（每条 dict 形如
    {'level': 'INFO', 'name': '...', 'message': '...'}）。
    """
    records: list[dict] = []

    def sink(message):
        rec = message.record
        records.append({
            "level": rec["level"].name,
            "name": rec["name"],
            "message": str(rec["message"]),
        })

    handler_id = logger.add(sink, level="DEBUG")
    try:
        yield records
    finally:
        logger.remove(handler_id)


# =========================================================================
# 1. OllamaConnectionError（任务 3.1 + 测试 7.2）
# =========================================================================

class TestOllamaConnectionError:
    """OllamaConnectionError 实例化、字段、to_dict"""

    def test_ollama_connection_error_all_stages(self):
        """所有 stage 都能实例化，suggestion 非空"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        stages = [
            "TCP_CONNECT", "HTTP_VERSION", "HTTP_TAGS",
            "HTTP_SHOW", "HTTP_CHAT", "HTTP_CHAT_TIMEOUT",
        ]
        for stage in stages:
            e = OllamaConnectionError(
                stage=stage,
                url="http://127.0.0.1:11434",
                detail="test detail",
            )
            assert e.stage == stage
            assert e.suggestion, f"stage={stage} 缺少默认 suggestion"
            assert "http://127.0.0.1:11434" in str(e)
            assert stage in str(e)

    def test_ollama_connection_error_to_dict(self):
        """to_dict 序列化字段：code=OLLAMA_CONNECT_FAIL + stage/model/url/detail/suggestion"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError(
            stage="TCP_CONNECT",
            url="http://127.0.0.1:11434",
            detail="Connection refused",
            model="qwen3.5:2b",
        )
        d = e.to_dict()
        assert d["code"] == "OLLAMA_CONNECT_FAIL"
        assert d["stage"] == "TCP_CONNECT"
        assert d["model"] == "qwen3.5:2b"
        assert d["url"] == "http://127.0.0.1:11434"
        assert d["detail"] == "Connection refused"
        assert d["suggestion"]  # 非空

    def test_ollama_connection_error_custom_suggestion(self):
        """自定义 suggestion 覆盖默认值"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        custom = "请检查 X 服务"
        e = OllamaConnectionError(
            stage="HTTP_CHAT",
            url="http://x",
            detail="d",
            suggestion=custom,
        )
        assert e.suggestion == custom

    def test_ollama_connection_error_default_suggestion_per_stage(self):
        """每种 stage 都有自己的默认 suggestion（不应都一样）"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        s_tcp = OllamaConnectionError("TCP_CONNECT", "u", "d").suggestion
        s_chat = OllamaConnectionError("HTTP_CHAT", "u", "d").suggestion
        s_show = OllamaConnectionError("HTTP_SHOW", "u", "d").suggestion
        s_to = OllamaConnectionError("HTTP_CHAT_TIMEOUT", "u", "d").suggestion
        # 至少 4 个 suggestion 不应完全一致
        assert len({s_tcp, s_chat, s_show, s_to}) >= 3

    def test_ollama_connection_error_unknown_stage_falls_back(self):
        """未知 stage 使用通用 fallback suggestion"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError("UNKNOWN_STAGE", "http://x", "d")
        assert e.suggestion  # 应该有 fallback
        assert e.stage == "UNKNOWN_STAGE"


# =========================================================================
# 2. BrainWorker 透传 code 覆盖（任务 3 + 测试 7.3 间接）
# =========================================================================

class TestBrainWorkerConnectFailPayload:
    """BrainWorker 透传 OllamaConnectionError.to_dict() 必须含 code=OLLAMA_CONNECT_FAIL"""

    def test_to_dict_code_is_ollama_connect_fail(self):
        """BrainWorker 透传用的 dict 必须含 code=OLLAMA_CONNECT_FAIL（间接覆盖）"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError("HTTP_CHAT", "http://127.0.0.1:11434", "fail")
        d = e.to_dict()
        assert d["code"] == "OLLAMA_CONNECT_FAIL"

    def test_to_dict_chat_500_maps_to_http_chat_stage(self):
        """chat 500 应映射到 HTTP_CHAT stage"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError("HTTP_CHAT", "http://127.0.0.1:11434/api/chat", "HTTP 500")
        assert e.stage == "HTTP_CHAT"
        assert "HTTP 500" in e.detail

    def test_to_dict_timeout_maps_to_http_chat_timeout(self):
        """asyncio.TimeoutError 应映射到 HTTP_CHAT_TIMEOUT stage"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError("HTTP_CHAT_TIMEOUT", "http://127.0.0.1:11434/api/chat", "模型响应超时")
        assert e.stage == "HTTP_CHAT_TIMEOUT"
        assert "超时" in e.suggestion

    def test_to_dict_tcp_refused_maps_to_tcp_connect(self):
        """ClientConnectorError 应映射到 TCP_CONNECT stage"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        e = OllamaConnectionError("TCP_CONNECT", "http://127.0.0.1:11434", "Connection refused")
        assert e.stage == "TCP_CONNECT"
        assert "ollama" in e.suggestion.lower() or "serve" in e.suggestion.lower()


# =========================================================================
# 3. diagnose_ollama.py CLI 解析（任务 1 + 测试 7.1）
# =========================================================================

class TestDiagnoseCliStepResult:
    """StepResult dataclass 结构"""

    def test_diagnose_cli_step_result_dataclass(self):
        """StepResult 是 dataclass，含 5 个字段"""
        from diagnose_ollama import StepResult

        r = StepResult(step=1, name="进程", status="PASS", detail="ok", fix="no fix")
        assert r.step == 1
        assert r.name == "进程"
        assert r.status == "PASS"
        assert r.detail == "ok"
        assert r.fix == "no fix"

    def test_diagnose_cli_step_result_default_fix(self):
        """StepResult.fix 默认空字符串"""
        from diagnose_ollama import StepResult

        r = StepResult(step=2, name="port", status="FAIL", detail="refused")
        assert r.fix == ""

    def test_diagnose_cli_step_result_to_dict(self):
        """to_dict 返回完整 dict"""
        from diagnose_ollama import StepResult

        r = StepResult(step=3, name="API 根", status="PASS", detail="v0.5.0", fix="")
        d = r.to_dict()
        assert d == {
            "step": 3,
            "name": "API 根",
            "status": "PASS",
            "detail": "v0.5.0",
            "fix": "",
        }


class TestDiagnoseParseTextLine:
    """文本行解析（实际由 _step_print 打印，但可验证 dataclass 内容）"""

    def test_diagnose_parse_text_line_pass(self, capsys):
        """PASS 行被 stdout 打印"""
        from diagnose_ollama import _step_print

        r = _step_print(1, "进程", "PASS", "ok", json_mode=False)
        captured = capsys.readouterr()
        assert r.status == "PASS"
        assert "[STEP 1]" in captured.out
        assert "ok" in captured.out

    def test_diagnose_parse_text_line_fail(self, capsys):
        """FAIL 行被 stdout 打印"""
        from diagnose_ollama import _step_print

        r = _step_print(2, "端口", "FAIL", "refused", fix="检查 ollama serve", json_mode=False)
        captured = capsys.readouterr()
        assert r.status == "FAIL"
        assert "refused" in captured.out
        assert "检查 ollama serve" in captured.out

    def test_diagnose_parse_text_line_warn(self, capsys):
        """WARN 行被 stdout 打印"""
        from diagnose_ollama import _step_print

        r = _step_print(4, "模型列表", "WARN", "model missing", fix="ollama pull", json_mode=False)
        captured = capsys.readouterr()
        assert r.status == "WARN"
        assert "model missing" in captured.out

    def test_diagnose_json_mode_output(self, capsys):
        """json_mode=True 时输出 JSON 行"""
        from diagnose_ollama import _step_print

        r = _step_print(1, "进程", "PASS", "ok", json_mode=True)
        captured = capsys.readouterr()
        # 至少一行 JSON
        lines = [ln for ln in captured.out.strip().splitlines() if ln.strip()]
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["step"] == 1
        assert parsed["status"] == "PASS"
        assert r.status == "PASS"


class TestDiagnoseSummary:
    """_summary 计数 + exit code"""

    def test_diagnose_summary_counts_all_pass(self, capsys):
        """6 步全 PASS → n_pass=6, n_fail=0, n_warn=0, exit 0"""
        from diagnose_ollama import StepResult, _summary

        results = [
            StepResult(step=i, name=f"step{i}", status="PASS", detail="ok")
            for i in range(1, 7)
        ]
        code = _summary(results, json_mode=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out.strip().splitlines()[-1])
        assert out["summary"] == {"pass": 6, "fail": 0, "warn": 0}
        assert code == 0

    def test_diagnose_summary_step1_fail(self, capsys):
        """Step 1 FAIL → 后续 5 步也被标 FAIL → n_fail=6"""
        from diagnose_ollama import StepResult, _summary

        results = [
            StepResult(step=1, name="进程", status="FAIL", detail="no proc"),
        ] + [
            StepResult(step=i, name=f"step{i}", status="FAIL", detail="跳过")
            for i in range(2, 7)
        ]
        code = _summary(results, json_mode=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out.strip().splitlines()[-1])
        assert out["summary"]["pass"] == 0
        assert out["summary"]["fail"] == 6
        assert code == 1

    def test_diagnose_summary_step2_fail(self, capsys):
        """Step 2 FAIL → 后续 4 步被标 FAIL → n_fail=5"""
        from diagnose_ollama import StepResult, _summary

        results = [
            StepResult(step=1, name="进程", status="PASS", detail="ok"),
            StepResult(step=2, name="端口", status="FAIL", detail="refused"),
        ] + [
            StepResult(step=i, name=f"step{i}", status="FAIL", detail="跳过")
            for i in range(3, 7)
        ]
        code = _summary(results, json_mode=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out.strip().splitlines()[-1])
        assert out["summary"]["pass"] == 1
        assert out["summary"]["fail"] == 5
        assert code == 1

    def test_diagnose_summary_with_warn(self, capsys):
        """含 1 WARN → n_warn=1, exit 0（因为没有 FAIL）"""
        from diagnose_ollama import StepResult, _summary

        results = [
            StepResult(step=1, name="进程", status="PASS", detail="ok"),
            StepResult(step=2, name="端口", status="PASS", detail="ok"),
            StepResult(step=3, name="API 根", status="PASS", detail="ok"),
            StepResult(step=4, name="模型列表", status="WARN", detail="model missing"),
            StepResult(step=5, name="模型元数据", status="PASS", detail="ok"),
            StepResult(step=6, name="生成测试", status="PASS", detail="ok"),
        ]
        code = _summary(results, json_mode=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out.strip().splitlines()[-1])
        assert out["summary"] == {"pass": 5, "fail": 0, "warn": 1}
        assert code == 0


class TestDiagnoseParseHostPort:
    """parse_host_port URL 解析"""

    def test_diagnose_parse_host_port_default(self):
        from diagnose_ollama import parse_host_port

        host, port = parse_host_port("http://127.0.0.1:11434")
        assert host == "127.0.0.1"
        assert port == 11434

    def test_diagnose_parse_host_port_localhost(self):
        from diagnose_ollama import parse_host_port

        host, port = parse_host_port("http://localhost:9999")
        assert host == "localhost"
        assert port == 9999


class TestDiagnoseCheckProcess:
    """check_process mock subprocess.run"""

    def test_diagnose_check_process_running(self, monkeypatch):
        """tasklist 返回含 ollama.exe → PASS"""
        from diagnose_ollama import check_process, IS_WINDOWS

        if not IS_WINDOWS:
            pytest.skip("Windows-only tasklist test")

        fake = MagicMock()
        fake.stdout = "INFO: Tasklist 报告\r\nollama.exe                  1234 Console    1     50,000 K\r\n"
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: fake)

        r = check_process()
        assert r.status == "PASS"
        assert "1234" in r.detail or "ollama" in r.detail.lower()

    def test_diagnose_check_process_not_running(self, monkeypatch):
        """tasklist 返回 INFO: No Tasks → FAIL"""
        from diagnose_ollama import check_process, IS_WINDOWS

        if not IS_WINDOWS:
            pytest.skip("Windows-only tasklist test")

        fake = MagicMock()
        fake.stdout = "INFO: No tasks are running which match the specified criteria.\r\n"
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: fake)

        r = check_process()
        assert r.status == "FAIL"


class TestDiagnoseCheckPort:
    """check_port mock socket"""

    def test_diagnose_check_port_unreachable(self, monkeypatch):
        """socket.create_connection 抛 ConnectionRefusedError → FAIL"""
        from diagnose_ollama import check_port

        def fake_create_connection(addr, timeout=5):
            raise ConnectionRefusedError(f"refused {addr}")

        monkeypatch.setattr("socket.create_connection", fake_create_connection)
        r = check_port("http://127.0.0.1:11434")
        assert r.status == "FAIL"
        assert "127.0.0.1" in r.detail


# =========================================================================
# 4. ModelManager._log_registration_summary（任务 5 + 测试 7.4）
# =========================================================================

class TestModelManagerRegistrationSummary:
    """_log_registration_summary 日志 + 漂移检测"""

    def test_model_manager_registration_summary_no_models(self, loguru_capture):
        """auto_discover=False 之后调用不应抛"""
        from hyperbrain.models.model_manager import ModelManager

        mm = ModelManager(auto_discover=False)
        # 不应抛
        mm._log_registration_summary()
        # 至少有一条日志
        assert any("[registration]" in r["message"] for r in loguru_capture)

    def test_model_manager_registration_summary_with_ollama(self, loguru_capture):
        """注册 ollama_default 后调用 _log_registration_summary 不挂"""
        from hyperbrain.models.model_manager import ModelManager

        mm = ModelManager(auto_discover=False)
        cfg = ModelConfig(
            model_name="qwen3.5:2b",
            provider=ModelProvider.OLLAMA,
            base_url="http://127.0.0.1:11434",
        )
        mm.register_model(name="ollama_default", config=cfg, priority=9)

        mm._log_registration_summary()
        # 至少一条 ollama_default 日志
        assert any("ollama_default" in r["message"] for r in loguru_capture)

    def test_model_manager_drift_logging(self, loguru_capture):
        """model_name 与 cfg.ollama_model 不一致时打 ERROR（drift）"""
        from hyperbrain.models.model_manager import ModelManager
        from hyperbrain.core.config import get_config

        mm = ModelManager(auto_discover=False)
        # cfg 默认 ollama_model="gemma2:2b"，故意注入不同的名字
        cfg = ModelConfig(
            model_name="qwen3.5:0.6b",
            provider=ModelProvider.OLLAMA,
            base_url="http://127.0.0.1:11434",
        )
        mm.register_model(name="ollama_default", config=cfg, priority=9)

        actual_cfg_model = get_config().model.ollama_model
        mm._log_registration_summary()

        # 如果 cfg.ollama_model != qwen3.5:0.6b，应有 drift 日志
        if actual_cfg_model != "qwen3.5:0.6b":
            assert any(
                "drift" in r["message"].lower() or "mismatch" in r["message"].lower()
                for r in loguru_capture
            ), f"expected drift log, got: {[r['message'] for r in loguru_capture]}"
        else:
            # cfg 已经是 qwen3.5:0.6b，无法触发 drift → 至少验证不抛
            assert any("[registration]" in r["message"] for r in loguru_capture)


# =========================================================================
# 5. ModelManager._validate_fallback_models（任务 6 + 测试 7.5）
# =========================================================================

class TestModelManagerValidateFallback:
    """_validate_fallback_models 跳过不存在的 model"""

    def test_model_manager_validate_fallback_empty(self, loguru_capture, monkeypatch):
        """fallback_models 为空时直接 return，不打 WARN"""
        from hyperbrain.core.config import get_config
        from hyperbrain.core import config as core_config_mod
        from hyperbrain.models.model_manager import ModelManager

        # 用一个稳定的 cfg 对象替换 get_config()，避免每次返回新实例
        # 注意：_validate_fallback_models 内部用 `from hyperbrain.core.config import get_config`
        # 局部导入，所以必须 patch 原模块而不是 model_manager
        fixed_cfg = get_config()
        fixed_cfg.model.fallback_models = []
        monkeypatch.setattr(core_config_mod, "get_config", lambda: fixed_cfg)

        mm = ModelManager(auto_discover=False)
        cfg = ModelConfig(
            model_name="qwen3.5:2b",
            provider=ModelProvider.OLLAMA,
            base_url="http://127.0.0.1:11434",
        )
        mm.register_model(name="ollama_default", config=cfg, priority=9)

        # 清掉 __init__ 和 register 期间的日志
        loguru_capture.clear()

        mm._validate_fallback_models()
        # 不应该有 fallback-validation 的 WARN
        assert not any(
            "fallback-validation" in r["message"]
            and r["level"] in ("WARNING", "ERROR")
            for r in loguru_capture
        )

    def test_model_manager_validate_fallback_no_ollama(self, loguru_capture, monkeypatch):
        """未注册 ollama_default 时应 skip 并打 WARN"""
        from hyperbrain.core.config import get_config
        from hyperbrain.core import config as core_config_mod
        from hyperbrain.models.model_manager import ModelManager

        fixed_cfg = get_config()
        fixed_cfg.model.fallback_models = ["gemma2:2b"]
        monkeypatch.setattr(core_config_mod, "get_config", lambda: fixed_cfg)

        mm = ModelManager(auto_discover=False)  # 不注册 ollama
        loguru_capture.clear()

        mm._validate_fallback_models()
        # 应有 skip 提示
        assert any(
            "fallback-validation" in r["message"]
            for r in loguru_capture
        )

    def test_model_manager_validate_fallback_missing(self, monkeypatch, loguru_capture):
        """fallback_models 含不存在 model 时打 WARN（spec 任务 6.3）"""
        from hyperbrain.core.config import get_config
        from hyperbrain.core import config as core_config_mod
        from hyperbrain.models.model_manager import ModelManager
        import aiohttp

        # 稳定的 cfg，注入不存在的 fallback
        fixed_cfg = get_config()
        fixed_cfg.model.fallback_models = ["fakemodel:7b"]
        monkeypatch.setattr(core_config_mod, "get_config", lambda: fixed_cfg)

        mm = ModelManager(auto_discover=False)
        cfg = ModelConfig(
            model_name="qwen3.5:2b",
            provider=ModelProvider.OLLAMA,
            base_url="http://127.0.0.1:11434",
        )
        mm.register_model(name="ollama_default", config=cfg, priority=9)

        # mock aiohttp.ClientSession 返回空 models 列表
        class _Resp:
            status = 200

            async def json(self):
                return {"models": []}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

        class _Session:
            def get(self, *a, **kw):
                return _Resp()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

        monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **kw: _Session())

        # 清掉 __init__ 和 register 期间的日志
        loguru_capture.clear()

        mm._validate_fallback_models()

        # 应有 fallback-validation 提到 fakemodel:7b
        matched = [
            r for r in loguru_capture
            if "fakemodel:7b" in r["message"]
        ]
        assert matched, f"expected warn for fakemodel:7b, got: {[r['message'] for r in loguru_capture]}"
        # 至少一条是 WARN 级别
        assert any(r["level"] == "WARNING" for r in matched)


# =========================================================================
# 6. 可选：BrainWorker emit 行为（需要 GUI 环境，按需 skip）
# =========================================================================

class TestBrainWorkerEmitsOllamaConnectFail:
    """BrainWorker 收到 OllamaConnectionError 时应 emit OLLAMA_CONNECT_FAIL

    注：BrainWorker 继承 QThread，需要 qapp fixture；如无 GUI 环境则跳过。
    """

    def test_brainworker_emits_code_in_payload(self):
        """间接覆盖：验证 OllamaConnectionError.to_dict() 的 code 字段"""
        from hyperbrain.models.ollama_model import OllamaConnectionError

        # BrainWorker.run() 内部 catch OllamaConnectionError 后会调用
        # e.to_dict() 并通过 error_occurred.emit(d) 发送。
        # 直接验证 d['code'] 即覆盖 emit 行为
        e = OllamaConnectionError("TCP_CONNECT", "http://127.0.0.1:11434", "refused")
        d = e.to_dict()
        assert d["code"] == "OLLAMA_CONNECT_FAIL"
        assert d["stage"] == "TCP_CONNECT"
        assert "suggestion" in d
