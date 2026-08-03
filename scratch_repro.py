"""Reproduce the user's reported issue: local model not connecting"""
import asyncio
import sys
import time
import traceback
sys.path.insert(0, 'e:/超脑/超脑002')

from hyperbrain.core.config import get_config
from hyperbrain.models.model_manager import ModelManager

async def main():
    print('=== Step 1: load config ===')
    config = get_config()
    print(f'default_provider={config.model.default_provider}')
    print(f'ollama_base_url={config.model.ollama_base_url}')
    print(f'ollama_model={config.model.ollama_model}')
    print(f'timeout={config.model.timeout}')
    print(f'worker_timeout={config.model.worker_timeout}')
    print(f'think={config.model.think}')
    print(f'stream={config.model.stream}')
    print(f'fallback_models={config.model.fallback_models}')

    print('\n=== Step 2: ModelManager initialize ===')
    mm = ModelManager()
    try:
        ok = await mm.initialize_all()
        print(f'initialize_all ok={ok}')
    except Exception as e:
        print(f'initialize_all failed: {type(e).__name__}: {e}')
        traceback.print_exc()
        return

    print('\n=== Step 3: list registered models ===')
    for name, m in mm.models.items():
        print(f'  {name}: {type(m).__name__} model_name={getattr(m, "model_name", "?")}')

    print('\n=== Step 4: try chat with primary model (qwen3.5:2b) ===')
    from hyperbrain.models.base import ChatMessage
    try:
        t0 = time.time()
        resp = await mm.chat(messages=[ChatMessage(role='user', content='hi')])
        dt = time.time() - t0
        print(f'OK elapsed={dt:.1f}s content={resp.content[:100]}')
    except Exception as e:
        dt = time.time() - t0
        print(f'FAIL elapsed={dt:.1f}s: {type(e).__name__}: {e}')

asyncio.run(main())
