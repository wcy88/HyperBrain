import sys
sys.path.insert(0, r'E:\超脑\超脑002')

print('╔══════════════════════════════════════════════════════════════╗')
print('║           HyperBrain 系统启动验证                            ║')
print('╚══════════════════════════════════════════════════════════════╝')
print()

# 1. 环境检查
print('[1/5] Python 环境检查...')
import platform
py_ver = platform.python_version()
py_arch = platform.architecture()[0]
print(f'  [OK] Python {py_ver} {py_arch}')

# 2. 核心依赖检查
print()
print('[2/5] 核心依赖检查...')
deps = [
    ('PyQt6', 'PyQt6.QtWidgets'),
    ('numpy', 'numpy'),
    ('pandas', 'pandas'),
    ('faiss-cpu', 'faiss'),
    ('pydantic', 'pydantic'),
    ('openai', 'openai'),
    ('anthropic', 'anthropic'),
    ('pytest', 'pytest'),
]
for name, mod in deps:
    try:
        __import__(mod)
        print(f'  [OK] {name}')
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')

# 3. 系统初始化
print()
print('[3/5] 系统初始化...')
from hyperbrain.core.brain import Brain
brain = Brain()
print('  [OK] Brain 核心已启动')

# 4. 认知层检查
print()
print('[4/5] 认知层状态检查...')
layers = [
    ('感知层', brain.sensory),
    ('记忆层', brain.memory),
    ('认知层', brain.cognitive),
    ('学习层', brain.learning),
    ('情感层', brain.emotional),
    ('执行层', brain.execution),
    ('进化层', brain.evolution),
    ('意识层', brain.consciousness),
]
all_ok = True
for name, layer in layers:
    if layer is not None:
        print(f'  [OK] {name}')
    else:
        print(f'  [FAIL] {name}')
        all_ok = False

# 5. 系统就绪
print()
print('[5/5] 系统状态...')
if all_ok:
    print('  [OK] 所有认知层运行正常')
    print('  [OK] 系统已就绪')
else:
    print('  [WARN] 部分认知层异常')

print()
print('╔══════════════════════════════════════════════════════════════╗')
print('║           HyperBrain 系统启动完成                            ║')
print('╚══════════════════════════════════════════════════════════════╝')
print()
print('提示: 配置大模型API密钥后，系统将具备AI对话能力')
print('      支持: OpenAI / Anthropic / Google / Ollama')
