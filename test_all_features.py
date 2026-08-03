"""综合功能测试：对照原始 spec 检查所有功能"""
import sys
import os
import asyncio
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestRunner:
    def __init__(self):
        self.results = []

    def run(self, name, func):
        print(f'\n=== {name} ===')
        try:
            result = func()
            if asyncio.iscoroutine(result):
                asyncio.run(result)
            print(f'  ✓ PASSED')
            self.results.append((name, True, None))
        except Exception as e:
            print(f'  ✗ FAILED: {e}')
            traceback.print_exc()
            self.results.append((name, False, str(e)))


def test_imports():
    """测试所有核心模块可以导入"""
    from hyperbrain import Brain
    from hyperbrain.core.config import get_config
    from hyperbrain.core.brain import Brain as B2
    from hyperbrain.layers.memory.memory_manager import MemoryManager
    from hyperbrain.layers.memory.memory_utils import (
        generate_text_embedding, generate_random_embedding, cosine_similarity
    )
    from hyperbrain.layers.memory.long_term_memory import LongTermMemory
    from hyperbrain.models.base import BaseModel, ChatMessage
    from hyperbrain.models.ollama_model import OllamaModel
    from hyperbrain.models.model_manager import ModelManager
    from hyperbrain.database.sqlite_manager import SQLiteManager
    from hyperbrain.ui.main_window import MainWindow
    from hyperbrain.ui.memory_viz import MemoryVisualizer
    from hyperbrain.ui.themes import theme_manager
    print('  All modules imported successfully')


def test_embedding_deterministic():
    """测试嵌入生成器的确定性"""
    from hyperbrain.layers.memory.memory_utils import generate_text_embedding
    import numpy as np
    v1 = generate_text_embedding('今天天气真好')
    v2 = generate_text_embedding('今天天气真好')
    assert np.array_equal(v1, v2), '相同文本应返回相同向量'
    print('  相同文本 → 相同向量 ✓')


def test_embedding_semantic():
    """测试嵌入生成器的语义性"""
    from hyperbrain.layers.memory.memory_utils import generate_text_embedding, cosine_similarity
    v1 = generate_text_embedding('今天天气真好')
    v2 = generate_text_embedding('今天天气不错')
    v3 = generate_text_embedding('Python 编程')
    sim12 = cosine_similarity(v1, v2)
    sim13 = cosine_similarity(v1, v3)
    assert sim12 > sim13, f'相似文本的相似度应高于不相关文本 ({sim12:.3f} vs {sim13:.3f})'
    assert sim12 > 0.3, f'相似文本相似度应 > 0.3 (实际 {sim12:.3f})'
    print(f'  相似文本: {sim12:.3f}, 不相关: {sim13:.3f} ✓')


def test_embedding_dimensions():
    """测试嵌入维度"""
    from hyperbrain.layers.memory.memory_utils import generate_text_embedding
    v1 = generate_text_embedding('hello', 768)
    v2 = generate_text_embedding('hello', 384)
    assert v1.shape == (768,), f'维度应为 768 (实际 {v1.shape})'
    assert v2.shape == (384,), f'维度应为 384 (实际 {v2.shape})'
    print(f'  自定义维度工作正常 ✓')


async def test_brain_init():
    """测试 Brain 初始化"""
    from hyperbrain.core.brain import Brain
    from hyperbrain.core.config import get_config
    config = get_config()
    brain = Brain(config)
    await brain.initialize()
    stats = brain.memory.get_stats()
    ltm = stats['long_term_memory']
    assert ltm['total_memories'] > 0, f'长期记忆应 > 0 (实际 {ltm["total_memories"]})'
    await brain.shutdown()
    print(f'  Brain 初始化成功，LTM: {ltm["total_memories"]} 条 ✓')


def test_memory_index_status():
    """测试索引状态显示"""
    # 这个在 UI 中测试
    from hyperbrain.ui.memory_viz import MemoryVisualizer
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    viz = MemoryVisualizer()
    viz.update_long_term_stats(0, False)
    assert viz.ltm_index_label.text() == '无数据', f'空状态应为"无数据" (实际 {viz.ltm_index_label.text()})'
    viz.update_long_term_stats(100, False)
    assert viz.ltm_index_label.text() == '已构建（暴力搜索）', f'暴力索引应为"已构建（暴力搜索）" (实际 {viz.ltm_index_label.text()})'
    viz.update_long_term_stats(100, True)
    assert viz.ltm_index_label.text() == '已构建（FAISS）', f'FAISS 索引应为"已构建（FAISS）" (实际 {viz.ltm_index_label.text()})'
    print('  索引状态显示正确 ✓')


def test_models_list():
    """测试模型可用性"""
    import aiohttp
    async def check():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'http://127.0.0.1:11434/api/tags',
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f'Ollama 不可用: {resp.status}')
                text = await resp.text()
                if 'gemma2:2b' not in text:
                    raise Exception('gemma2:2b 模型不可用')
    asyncio.run(check())
    print('  gemma2:2b 模型可用 ✓')


def main():
    runner = TestRunner()

    runner.run('模块导入测试', test_imports)
    runner.run('嵌入确定性测试', test_embedding_deterministic)
    runner.run('嵌入语义性测试', test_embedding_semantic)
    runner.run('嵌入维度测试', test_embedding_dimensions)
    runner.run('Brain 初始化测试', test_brain_init)
    runner.run('索引状态显示测试', test_memory_index_status)
    runner.run('模型可用性测试', test_models_list)

    print('\n' + '=' * 50)
    passed = sum(1 for _, ok, _ in runner.results if ok)
    failed = sum(1 for _, ok, _ in runner.results if not ok)
    print(f'总计: {passed} 通过, {failed} 失败')
    if failed > 0:
        print('\n失败项:')
        for name, ok, err in runner.results:
            if not ok:
                print(f'  - {name}: {err}')
    print('=' * 50)


if __name__ == '__main__':
    main()
