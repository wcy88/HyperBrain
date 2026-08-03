"""
Pytest 配置文件

提供测试用的fixtures和配置
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path

from hyperbrain.core.config import Config, get_config
from hyperbrain.core.brain import Brain


@pytest.fixture
async def brain():
    """创建Brain实例（已初始化）"""
    brain = Brain(enable_logging=False)
    await brain.initialize()
    await brain.start()
    yield brain
    await brain.shutdown()


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir):
    """创建测试配置"""
    config = get_config()
    config.memory.db_path = f"{temp_dir}/test_memory.db"
    config.debug = True
    return config
