"""临时探针，验证 sys.path + 模块导入"""
import sys
import os

# 测试从 scripts 目录直接 import
sys.path.insert(0, r"e:\超脑\超脑002\scripts")
try:
    from diagnose_ollama import StepResult, _step_print, _summary, parse_host_port
    print("[1] scripts/diagnose_ollama.py 直接 import OK")
    r = StepResult(step=1, name="进程", status="PASS", detail="ok")
    print(f"    StepResult: {r}")
    print(f"    to_dict: {r.to_dict()}")
except Exception as e:
    print(f"[1] FAILED: {type(e).__name__}: {e}")

# 测试 ollama_model
try:
    sys.path.insert(0, r"e:\超脑\超脑002")
    from hyperbrain.models.ollama_model import OllamaConnectionError
    print("[2] hyperbrain.models.ollama_model OK")
    e = OllamaConnectionError("TCP_CONNECT", "http://127.0.0.1:11434", "refused")
    print(f"    {e}")
    print(f"    to_dict: {e.to_dict()}")
except Exception as e:
    print(f"[2] FAILED: {type(e).__name__}: {e}")

# 测试 model_manager
try:
    from hyperbrain.models.model_manager import ModelManager
    from hyperbrain.models.base import ModelConfig, ModelProvider
    mm = ModelManager(auto_discover=False)
    cfg = ModelConfig(
        model_name="qwen3.5:2b",
        provider=ModelProvider.OLLAMA,
        base_url="http://127.0.0.1:11434",
    )
    mm.register_model(name="ollama_default", config=cfg, priority=9)
    print(f"[3] ModelManager: {len(mm.models)} registered")
except Exception as e:
    print(f"[3] FAILED: {type(e).__name__}: {e}")
