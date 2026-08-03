"""验证 --timeout-think 默认值 = 180（spec show-thinking-process 任务4）"""
import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))

# 必须放到 sys.modules 才能让 dataclass 找到模块
mod_name = "diagnose_ollama"
spec = importlib.util.spec_from_file_location(
    mod_name,
    os.path.join(os.getcwd(), "scripts", "diagnose_ollama.py"),
)
m = importlib.util.module_from_spec(spec)
sys.modules[mod_name] = m
spec.loader.exec_module(m)

# 调用 main 但 mock 掉 _amain / asyncio.run
import asyncio

captured = {}

def fake_amain(args):
    captured["timeout_think"] = args.timeout_think
    return 0

def fake_asyncio_run(value):
    return 0

m._amain = fake_amain
asyncio.run = fake_asyncio_run
sys.argv = ["diagnose_ollama.py"]

try:
    m.main()
except SystemExit:
    pass

print(f"default --timeout-think = {captured.get('timeout_think')}")
assert captured.get("timeout_think") == 180, f"expected 180, got {captured.get('timeout_think')}"
print("OK: default 180 confirmed")
