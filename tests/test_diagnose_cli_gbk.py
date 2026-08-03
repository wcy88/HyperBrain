"""
诊断 CLI GBK 兼容与 thinking 模型超时测试（spec fix-diagnose-cli-gbk-and-thinking 任务4）

覆盖（spec tasks.md 4.1-4.8 + checklist "单元测试" 章节）：
- 4.1 _step_print 在强制 GBK 编码下不抛 UnicodeEncodeError
- 4.2 所有 step name 是 ASCII（脚本里无中文字符）
- 4.3 thinking 模型 → Step 6 payload think:false + timeout=60
- 4.4 非 thinking → 无 think + timeout=15
- 4.5 --timeout-think 默认 60，--timeout-think 180 解析到 180
- 4.6 --timeout-think 5 钳到 10
- 4.7 --timeout-think 1000 钳到 600
- 4.8 JSON 模式 ensure_ascii=False（中文保留）
- Bonus: --help 含 --timeout-think；thinking 通过 family 也被识别
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import json as json_mod  # 别名：避免在 _FakeSession.post 的 `json` 参数处遮蔽
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# === 把 scripts/ 加入 sys.path 以导入 diagnose_ollama.py（无 __init__.py） ===
_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import diagnose_ollama as diag  # noqa: E402

_SCRIPT_PATH = os.path.join(_SCRIPTS_DIR, "diagnose_ollama.py")


# === ANSI 颜色（用于在测试里重新启用 Color，模拟 tty） ===

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_CYAN = "\033[36m"


def _enable_colors(monkeypatch):
    """在测试中重新启用 Color 类的 ANSI 颜色（模拟 tty）"""
    monkeypatch.setattr(diag.Color, "RESET", ANSI_RESET)
    monkeypatch.setattr(diag.Color, "BOLD", ANSI_BOLD)
    monkeypatch.setattr(diag.Color, "RED", ANSI_RED)
    monkeypatch.setattr(diag.Color, "GREEN", ANSI_GREEN)
    monkeypatch.setattr(diag.Color, "YELLOW", ANSI_YELLOW)
    monkeypatch.setattr(diag.Color, "CYAN", ANSI_CYAN)


# =========================================================================
# 4.1 GBK 编码兼容（任务 4.1）
# =========================================================================

def test_step_print_gbk_compatible(monkeypatch):
    """强制 sys.stdout.encoding='gbk' 时 _step_print 不抛 UnicodeEncodeError"""
    # 重新启用颜色（模块导入时 Color 已被 disable_if_needed 清空）
    _enable_colors(monkeypatch)

    # 用 GBK 编码的 TextIOWrapper 替换 stdout。
    # ASCII 字符串可以正常编码；非 ASCII 字符串会触发 UnicodeEncodeError。
    gbk_buf = io.TextIOWrapper(io.BytesIO(), encoding="gbk", write_through=True)
    monkeypatch.setattr(sys, "stdout", gbk_buf)

    cases = [
        (1, "process", "PASS", "ollama.exe is running (PIDs: 1234)", ""),
        (2, "port", "FAIL", "127.0.0.1:11434 TCP unreachable: ConnectionRefusedError",
         "please check: is Ollama running?"),
        (3, "api root", "WARN", "GET /api/version -> 200", ""),
        (4, "model list", "PASS",
         "found 5 models, target qwen3.5:0.8b included", ""),
        (5, "model show", "FAIL", "POST /api/show -> 404",
         "please run: ollama pull qwen3.5:0.8b"),
        (6, "generate test", "PASS",
         "POST /api/generate -> 200, response: 'hi'", ""),
    ]

    try:
        for idx, name, status, detail, fix in cases:
            result = diag._step_print(idx, name, status, detail, fix=fix)
            assert result.status == status
            assert result.name == name
            assert result.detail == detail
    finally:
        # 解绑 TextIOWrapper 避免 __del__ 时关闭报错
        try:
            gbk_buf.detach()
        except Exception:
            pass

    # 不抛 UnicodeEncodeError = 通过


# =========================================================================
# 4.2 所有 step name 是 ASCII（任务 4.2）
# =========================================================================

def test_no_chinese_in_user_facing_strings():
    """diagnose_ollama.py 不应包含旧的 step name 中文（已被替换为英文）"""
    script = Path(_SCRIPT_PATH).read_text(encoding="utf-8")

    # 旧的 step name 中文（应已全部替换）
    old_chinese_names = ["进程", "端口", "API 根", "模型列表", "模型元数据", "生成测试"]
    for old in old_chinese_names:
        assert old not in script, f"old Chinese name {old!r} still present in script"

    # 新的英文 step name 应出现在 _step_print 调用中
    expected_names = ["process", "port", "api root",
                      "model list", "model show", "generate test"]
    for new in expected_names:
        assert f'"{new}"' in script, f"expected new step name {new!r} not found in script"


def test_all_step_print_strings_ascii():
    """所有 _step_print 调用的字符串字面量都是纯 ASCII"""
    script = Path(_SCRIPT_PATH).read_text(encoding="utf-8")

    # 找出所有 _step_print 调用（单行形式；脚本里都是单行）
    matches = re.findall(r'_step_print\([^)]*\)', script)
    assert len(matches) >= 6, f"expected >=6 _step_print calls, got {len(matches)}"

    for m in matches:
        # 提取双引号字符串字面量
        strings = re.findall(r'"([^"]+)"', m)
        for s in strings:
            # 跳过空字符串
            if not s:
                continue
            # 检查所有字符的 ord < 128
            assert all(ord(c) < 128 for c in s), (
                f"non-ASCII string in call {m[:80]!r}: {s!r}"
            )


# =========================================================================
# 4.3 / 4.4 aiohttp mock + thinking 检测（任务 4.3-4.4）
# =========================================================================

class _RespCtx:
    """Fake aiohttp response context manager."""

    def __init__(self, status, text):
        self.status = status
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def text(self):
        return self._text


class _FakeSession:
    """Fake aiohttp.ClientSession. 记录所有 POST 调用."""

    def __init__(self, model_name, is_thinking):
        self.model_name = model_name
        self.is_thinking = is_thinking
        self.posted = []  # list of (url, json_payload, timeout_obj)

    def get(self, url, timeout=None):
        if url.endswith("/api/version"):
            return _RespCtx(200, json_mod.dumps({"version": "0.30.7"}))
        if url.endswith("/api/tags"):
            return _RespCtx(200, json_mod.dumps({"models": [{"name": self.model_name}]}))
        return _RespCtx(404, "{}")

    def post(self, url, json=None, timeout=None):
        # 注意：参数名 `json` 遮蔽了 json 模块。
        # 这里用 `json_mod` 显式引用，避免 AttributeError。
        self.posted.append((url, json, timeout))
        if url.endswith("/api/show"):
            if self.is_thinking:
                payload = {"capabilities": ["thinking"],
                           "details": {"family": "qwen35"}}
            else:
                payload = {"capabilities": ["completion"],
                           "details": {"family": "gemma2"}}
            return _RespCtx(200, json_mod.dumps(payload))
        if url.endswith("/api/generate"):
            return _RespCtx(200, json_mod.dumps({"response": "Hi"}))
        return _RespCtx(200, "{}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


@pytest.mark.asyncio
async def test_check_api_steps_thinking_model():
    """Step 5 拿到 capabilities=['thinking'] → Step 6 payload think:false + timeout=60"""
    fake = _FakeSession("qwen3.5:0.8b", is_thinking=True)

    with patch("aiohttp.ClientSession", return_value=fake):
        results = await diag.check_api_steps(
            "http://127.0.0.1:11434", "qwen3.5:0.8b", timeout_think=60,
        )

    # 找到 Step 6 的 generate 调用
    gen_calls = [(u, p, t) for u, p, t in fake.posted if "/api/generate" in u]
    assert len(gen_calls) == 1
    _gen_url, gen_payload, gen_timeout = gen_calls[0]
    assert gen_payload.get("think") is False
    assert gen_timeout.total == 60

    # Step 3, 4, 5, 6 共 4 个都应 PASS
    assert len(results) == 4
    assert all(r.status == "PASS" for r in results)


@pytest.mark.asyncio
async def test_check_api_steps_non_thinking_model():
    """Step 5 拿到 non-thinking → Step 6 payload 无 think + timeout=15"""
    fake = _FakeSession("gemma2:2b", is_thinking=False)

    with patch("aiohttp.ClientSession", return_value=fake):
        results = await diag.check_api_steps(
            "http://127.0.0.1:11434", "gemma2:2b", timeout_think=60,
        )

    gen_calls = [(u, p, t) for u, p, t in fake.posted if "/api/generate" in u]
    assert len(gen_calls) == 1
    _gen_url, gen_payload, gen_timeout = gen_calls[0]
    assert "think" not in gen_payload
    assert gen_timeout.total == 15

    assert len(results) == 4
    assert all(r.status == "PASS" for r in results)


@pytest.mark.asyncio
async def test_check_api_steps_thinking_by_family():
    """family='qwen3' 也能被识别为 thinking（即使 capabilities 不含 thinking）"""

    class _CustomSession(_FakeSession):
        def post(self, url, json=None, timeout=None):
            self.posted.append((url, json, timeout))
            if url.endswith("/api/show"):
                # capabilities 不含 thinking，但 family=qwen3
                payload = {"capabilities": ["completion"],
                           "details": {"family": "qwen3"}}
                return _RespCtx(200, json_mod.dumps(payload))
            if url.endswith("/api/generate"):
                return _RespCtx(200, json_mod.dumps({"response": "Hi"}))
            return _RespCtx(200, "{}")

    fake = _CustomSession("qwen3:latest", is_thinking=False)

    with patch("aiohttp.ClientSession", return_value=fake):
        await diag.check_api_steps(
            "http://127.0.0.1:11434", "qwen3:latest", timeout_think=60,
        )

    gen_calls = [(u, p, t) for u, p, t in fake.posted if "/api/generate" in u]
    assert len(gen_calls) == 1
    _gen_url, gen_payload, gen_timeout = gen_calls[0]
    assert gen_payload.get("think") is False
    assert gen_timeout.total == 60


# =========================================================================
# 4.5 / 4.6 / 4.7 --timeout-think CLI 参数（任务 4.5-4.7）
# =========================================================================

def _run_main_capture_args(monkeypatch, argv, captured):
    """调 diag.main()，用 mock 替换 _amain + asyncio.run + sys.argv，
    把 args 抓到 captured dict。main() 内部 sys.exit 会抛 SystemExit。
    """
    def fake_amain(args):
        captured["timeout_think"] = args.timeout_think
        captured["args"] = args
        return 0

    def fake_asyncio_run(value):
        return 0

    monkeypatch.setattr(diag, "_amain", fake_amain)
    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit):
        diag.main()


def test_cli_timeout_think_default(monkeypatch):
    """不传 --timeout-think 时默认 180（spec show-thinking-process）"""
    captured = {}
    _run_main_capture_args(monkeypatch, ["diagnose_ollama.py"], captured)
    assert captured["timeout_think"] == 180


def test_cli_timeout_think_custom(monkeypatch):
    """--timeout-think 180 解析到 180"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "180"],
        captured,
    )
    assert captured["timeout_think"] == 180


def test_timeout_think_clamp_low(monkeypatch):
    """--timeout-think 5 钳到 10"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "5"],
        captured,
    )
    assert captured["timeout_think"] == 10


def test_timeout_think_clamp_high(monkeypatch):
    """--timeout-think 1000 钳到 600"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "1000"],
        captured,
    )
    assert captured["timeout_think"] == 600


def test_timeout_think_in_range(monkeypatch):
    """--timeout-think 30（范围内）保持 30"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "30"],
        captured,
    )
    assert captured["timeout_think"] == 30


def test_timeout_think_boundary_low(monkeypatch):
    """--timeout-think 10 正好下限，保持 10"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "10"],
        captured,
    )
    assert captured["timeout_think"] == 10


def test_timeout_think_boundary_high(monkeypatch):
    """--timeout-think 600 正好上限，保持 600"""
    captured = {}
    _run_main_capture_args(
        monkeypatch,
        ["diagnose_ollama.py", "--timeout-think", "600"],
        captured,
    )
    assert captured["timeout_think"] == 600


# =========================================================================
# 4.8 JSON 模式 ensure_ascii=False（任务 4.8）
# =========================================================================

def test_json_mode_keeps_chinese():
    """JSON 模式输出保留中文（ensure_ascii=False）"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        diag._step_print(1, "test", "PASS", "中文 test",
                         fix="修复方法", json_mode=True)

    output = buf.getvalue().strip()
    # 关键：JSON 字符串中含 "中文 test"（不带 \u 转义）= ensure_ascii=False
    assert "中文 test" in output
    assert "修复方法" in output
    assert "\\u" not in output
    parsed = json_mod.loads(output)
    assert parsed["detail"] == "中文 test"
    assert parsed["fix"] == "修复方法"


def test_json_mode_ascii_also_works():
    """JSON 模式 + ASCII 字符串也能正确输出"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        diag._step_print(2, "port", "FAIL", "127.0.0.1:11434 TCP unreachable",
                         fix="please check", json_mode=True)

    output = buf.getvalue().strip()
    parsed = json_mod.loads(output)
    assert parsed["step"] == 2
    assert parsed["name"] == "port"
    assert parsed["status"] == "FAIL"
    assert "127.0.0.1" in parsed["detail"]


# =========================================================================
# Bonus: --help 包含 --timeout-think
# =========================================================================

def test_cli_timeout_think_in_help():
    """--timeout-think 出现在 --help 中"""
    py_exe = sys.executable
    result = subprocess.run(
        [py_exe, _SCRIPT_PATH, "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert "--timeout-think" in result.stdout
    assert "thinking" in result.stdout.lower()
