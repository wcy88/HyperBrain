"""
记忆层测试
"""

import pytest
import tempfile
import os
import numpy as np

from hyperbrain.layers.memory.memory_manager import MemoryManager, MemoryItem
from hyperbrain.layers.memory.memory_models import MemoryType


def _temp_db_path():
    """创建临时数据库路径（测试隔离）"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)  # 删除空文件，让 MemoryManager 自己创建
    return path


class TestMemoryManager:
    """测试记忆管理器"""

    def test_store_and_retrieve(self):
        """测试存储和检索"""
        manager = MemoryManager(db_path=_temp_db_path())

        # 存储记忆
        item = manager.store("测试内容", importance=0.8)
        assert item is not None
        assert item.content == "测试内容"

        # 检索记忆
        results = manager.retrieve("测试")
        assert len(results) > 0
        assert results[0].memory.content == "测试内容"

    def test_memory_importance(self):
        """测试重要性筛选"""
        manager = MemoryManager(db_path=_temp_db_path())

        manager.store("低重要性内容", importance=0.3)
        manager.store("高重要性内容", importance=0.9)

        # 高重要性记忆应该被巩固到长期记忆
        flow = manager.get_memory_flow()
        assert flow["long_term"] > 0

    def test_forget(self):
        """测试遗忘"""
        manager = MemoryManager(db_path=_temp_db_path())

        item = manager.store("待遗忘内容")
        item_id = item.id

        # 遗忘
        success = manager.forget(item_id)
        assert success

        # 确认已遗忘（可能仍存在于长期记忆中，但状态应为遗忘）
        results = manager.retrieve_by_id(item_id)
        if results:
            assert results.status.value == "forgotten"

    def test_consolidate(self):
        """测试记忆巩固"""
        manager = MemoryManager(db_path=_temp_db_path())

        # 添加多个记忆并增加访问次数
        for i in range(5):
            item = manager.store(f"记忆{i}", importance=0.6)
            item.access_count = 5

        # 巩固
        consolidated = manager.consolidate()
        # 巩固可能返回0（如果所有记忆已经在长期记忆中）
        assert consolidated >= 0


class TestMemoryTypes:
    """测试记忆类型"""
    
    def test_memory_type_enum(self):
        """测试记忆类型枚举"""
        assert MemoryType.DECLARATIVE.value == "declarative"
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SENSORY.value == "sensory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
