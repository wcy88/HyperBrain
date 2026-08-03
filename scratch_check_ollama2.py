import asyncio
import aiohttp
import json
import time

async def test():
    # Test with gemma2:2b (non-thinking) to see if it works
    print('=== Test 1: gemma2:2b (non-thinking) ===')
    url = 'http://127.0.0.1:11434/api/chat'
    payload = {
        'model': 'gemma2:2b',
        'messages': [{'role': 'user', 'content': 'hi'}],
        'stream': False
    }
    try:
        t0 = time.time()
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post(url, json=payload) as r:
                txt = await r.text()
                dt = time.time() - t0
                print(f'status={r.status} elapsed={dt:.1f}s len={len(txt)}')
                try:
                    j = json.loads(txt)
                    msg = j.get('message', {})
                    print(f'content={msg.get("content", "")[:100]}')
                except Exception as e:
                    print(f'parse fail: {e} txt={txt[:200]}')
    except Exception as e:
        print(f'FAIL: {type(e).__name__}: {e}')

asyncio.run(test())
