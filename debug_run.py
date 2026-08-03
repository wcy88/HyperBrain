import sys
sys.path.insert(0, r'E:\超脑\超脑002')

print('=== HyperBrain 系统调试运行 ===')
print()

from hyperbrain.core.brain import Brain
from hyperbrain.core.config import get_config

print('[1/4] 加载系统配置...')
config = get_config()
print('  [OK] 配置加载完成')

print()
print('[2/4] 初始化 Brain 核心...')
brain = Brain()
print('  [OK] Brain 核心初始化完成')

print()
print('[3/4] 检查8大认知层状态...')
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

ok_count = 0
for name, layer in layers:
    status = '[OK]' if layer is not None else '[FAIL]'
    if layer is not None:
        ok_count += 1
    layer_name = type(layer).__name__ if layer else "未初始化"
    print(f'  {status} {name}: {layer_name}')

print()
print('[4/4] 系统状态汇总...')
version = config.version if hasattr(config, 'version') else "unknown"
print(f'  系统版本: {version}')
print(f'  认知层数: {ok_count}/8')
print(f'  运行状态: {"正常" if ok_count == 8 else "异常"}')

print()
print('=== 系统调试运行完成 ===')
