import asyncio
import aiohttp
import json

async def test():
    async with aiohttp.ClientSession() as s:
        async with s.get('http://127.0.0.1:11434/api/tags') as r:
            data = await r.json(content_type=None)
            for m in data.get('models', []):
                name = m.get('name')
                family = m.get('details', {}).get('family')
                size = m.get('size')
                print(f'name={name} family={family} size={size}')

asyncio.run(test())
