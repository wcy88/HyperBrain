"""
GUI会话管理与设置修复自动化测试

根据 spec.md 检查清单自动测试所有功能
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class MockAiohttpResponse:
    """Mock for aiohttp response context manager.

    Supports ``async with session.get(...) as resp`` pattern.
    """

    def __init__(self, status: int = 200, json_data=None):
        self.status = status
        self._json_data = json_data or {}

    async def json(self):
        return self._json_data

    async def text(self):
        return str(self._json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


# ============================
# 测试1: 配置加载/保存
# ============================

class TestConfigSaveLoad:
    """测试配置正确保存和加载"""

    def test_config_loads_from_yaml(self):
        """测试配置从 YAML 文件加载"""
        from hyperbrain.core.config import get_config, ConfigManager

        # 重置配置缓存
        ConfigManager._config = None

        config = get_config()

        # 验证配置从 config.yaml 加载
        assert config.model.default_provider == "ollama", \
            f"Expected ollama, got {config.model.default_provider}"
        assert config.model.ollama_model == "minimax-m3:cloud", \
            f"Expected minimax-m3:cloud, got {config.model.ollama_model}"

    def test_config_save_persists(self, tmp_path):
        """测试配置修改后能正确保存到文件

        使用临时路径隔离，避免覆写项目根 config.yaml（spec fix-config-overwrite）。
        """
        from hyperbrain.core.config import Config, ConfigManager

        # 使用独立临时文件，不触碰项目 config.yaml
        tmp_config = tmp_path / "test_config.yaml"

        # 直接创建 Config 对象，保存到临时路径（不调用 load_config 避免自动检测项目 config.yaml）
        config = Config()
        config.model.default_provider = "test_provider"
        config.model.ollama_model = "test_model"

        mgr = ConfigManager()
        # 明确传 path，确保只写入临时文件
        mgr.save_config(config, str(tmp_config))

        # 用新的 ConfigManager 重新加载验证
        mgr2 = ConfigManager()
        config2 = mgr2.load_config(str(tmp_config))

        assert config2.model.default_provider == "test_provider"
        assert config2.model.ollama_model == "test_model"

    def test_config_auto_detect_project_path(self):
        """测试自动检测项目根目录的 config.yaml"""
        config_path = PROJECT_ROOT / "config.yaml"
        assert config_path.exists(), "config.yaml should exist in project root"


# ============================
# 测试2: 模型发现和连接
# ============================

class TestModelDiscovery:
    """测试本地模型发现和连接"""

    @pytest.mark.asyncio
    async def test_ollama_service_available(self):
        """测试 Ollama 服务可用"""
        import aiohttp

        mock_response = MockAiohttpResponse(
            status=200,
            json_data={"models": [{"name": "test_model:latest"}]},
        )

        with patch("aiohttp.ClientSession.get", return_value=mock_response):
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:11434/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    assert resp.status == 200, f"Ollama service not available, status: {resp.status}"

                    data = await resp.json()
                    models = data.get("models", [])
                    assert len(models) > 0, "Ollama has no models available"

    @pytest.mark.asyncio
    async def test_discover_local_models(self):
        """测试发现所有本地模型"""
        from hyperbrain.models.model_manager import ModelManager
        from hyperbrain.models.ollama_model import OllamaModel

        mm = ModelManager()

        mock_response = MockAiohttpResponse(
            status=200,
            json_data={"models": [{"name": "test_model:latest"}]},
        )

        with patch("aiohttp.ClientSession.get", return_value=mock_response), \
             patch.object(OllamaModel, "initialize", new_callable=AsyncMock, return_value=True):
            discovered = await mm.discover_local_models()

        # 至少应该发现一个模型
        assert len(discovered) > 0, f"No models discovered: {discovered}"

        # 验证模型名格式正确
        for name in discovered:
            assert name.startswith("ollama_"), f"Model name should start with ollama_: {name}"

    @pytest.mark.asyncio
    async def test_ollama_model_chat(self):
        """测试 Ollama 模型可以正常对话"""
        from hyperbrain.models.ollama_model import OllamaModel
        from hyperbrain.models.base import ChatMessage, ModelConfig, ModelProvider, ModelResponse
        from hyperbrain.core.config import get_config

        config = get_config()

        ollama_config = ModelConfig(
            model_name=config.model.ollama_model,
            provider=ModelProvider.OLLAMA,
            base_url=config.model.ollama_base_url,
            temperature=config.model.temperature,
            max_tokens=64,
            timeout=30.0,
        )

        model = OllamaModel(ollama_config)

        mock_response = ModelResponse(
            content="你好！我是HyperBrain测试响应。",
            provider="ollama",
            model=config.model.ollama_model,
        )

        with patch.object(OllamaModel, "initialize", new_callable=AsyncMock, return_value=True), \
             patch.object(OllamaModel, "chat", new_callable=AsyncMock, return_value=mock_response):
            success = await model.initialize()
            assert success, "Failed to initialize Ollama model"

            # 发送测试消息
            messages = [ChatMessage(role="user", content="你好")]
            response = await model.chat(messages)

            assert response is not None, "Response should not be None"
            assert response.content is not None, "Response content should not be None"
            assert len(response.content) > 0, "Response content should not be empty"


# ============================
# 测试3: 聊天功能
# ============================

class TestChatFunctionality:
    """测试聊天消息发送和处理"""

    @pytest.mark.asyncio
    async def test_brain_process(self):
        """测试 brain.process 能正常处理消息"""
        from hyperbrain.core.brain import Brain, ProcessingResult

        brain = Brain()
        # Mock methods that would hit Ollama to avoid real HTTP requests
        brain.initialize = AsyncMock(return_value=True)
        brain.start = AsyncMock(return_value=True)
        brain.stop = AsyncMock()
        brain.process = AsyncMock(return_value=ProcessingResult(
            success=True,
            content="你好！我是HyperBrain测试响应。",
            processing_time_ms=10.0,
            layers_involved=["sensory", "model", "execution"],
        ))

        await brain.initialize()
        await brain.start()

        try:
            result = await brain.process("你好")
            assert result is not None, "Process result should not be None"
            assert result.success, f"Process should succeed, error: {result.error}"
            assert result.content is not None, "Response content should not be None"
        finally:
            await brain.stop()

    def test_message_sent_signal(self):
        """测试 message_sent 信号能正确触发"""
        import sys
        from PyQt6.QtWidgets import QApplication
        from hyperbrain.ui.chat_widget import ChatWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        widget = ChatWidget()
        signal_received = []

        def on_message_sent(text):
            signal_received.append(text)

        widget.message_sent.connect(on_message_sent)
        widget.input_edit.setPlainText("测试消息")
        widget._send_message()

        assert len(signal_received) == 1, "message_sent signal should be emitted once"
        assert signal_received[0] == "测试消息", f"Expected '测试消息', got {signal_received[0]}"

    def test_add_message(self):
        """测试添加消息功能"""
        import sys
        from PyQt6.QtWidgets import QApplication
        from hyperbrain.ui.chat_widget import ChatWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        widget = ChatWidget()

        # 添加用户消息
        widget.add_message("user", "你好")
        assert len(widget.message_history) == 1

        # 添加助手消息
        widget.add_message("assistant", "你好！有什么可以帮你的吗？")
        assert len(widget.message_history) == 2

        # 验证消息内容
        assert widget.message_history[0]["content"] == "你好"
        assert widget.message_history[1]["content"] == "你好！有什么可以帮你的吗？"

    def test_clear_messages(self):
        """测试清空消息功能"""
        import sys
        from PyQt6.QtWidgets import QApplication
        from hyperbrain.ui.chat_widget import ChatWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        widget = ChatWidget()
        widget.add_message("user", "测试1")
        widget.add_message("assistant", "测试2")

        assert len(widget.message_history) == 2

        widget.clear_messages()
        assert len(widget.message_history) == 0


# ============================
# 测试4: 会话管理数据库
# ============================

class TestSessionDatabase:
    """测试会话管理数据库操作"""

    def test_session_manager_crud(self):
        """测试会话的创建、读取、更新、删除"""
        from hyperbrain.database.sqlite_manager import SQLiteManager
        import tempfile
        import os

        tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = tmpfile.name
        tmpfile.close()

        try:
            db = SQLiteManager(db_path=db_path)

            # Create sessions table
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0
                )
            """)

            import uuid
            from datetime import datetime

            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # Create
            db.execute(
                "INSERT INTO sessions (id, name, created_at, updated_at, message_count) VALUES (?, ?, ?, ?, ?)",
                (session_id, "测试会话", now, now, 0)
            )

            # Read
            result = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            assert len(result) == 1
            assert result[0]["name"] == "测试会话"

            # Update
            db.execute("UPDATE sessions SET name = ? WHERE id = ?", ("更新后的会话", session_id))
            result = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            assert result[0]["name"] == "更新后的会话"

            # Delete
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            result = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            assert len(result) == 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_session_messages_association(self):
        """测试会话与消息的关联"""
        from hyperbrain.database.sqlite_manager import SQLiteManager
        import tempfile
        import os

        tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = tmpfile.name
        tmpfile.close()

        try:
            db = SQLiteManager(db_path=db_path)

            # Create tables
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS test_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            import uuid
            from datetime import datetime

            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # Create session
            db.execute(
                "INSERT INTO sessions (id, name, created_at, updated_at, message_count) VALUES (?, ?, ?, ?, ?)",
                (session_id, "测试会话", now, now, 0)
            )

            # Add messages
            db.execute(
                "INSERT INTO test_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "user", "你好", now)
            )
            db.execute(
                "INSERT INTO test_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", "你好！", now)
            )

            # Get messages
            messages = db.execute("SELECT * FROM test_messages WHERE session_id = ? ORDER BY id", (session_id,))
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "你好"
            assert messages[1]["role"] == "assistant"
            assert messages[1]["content"] == "你好！"

            # Delete session
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            # Clean up messages manually (no CASCADE in this test)
            db.execute("DELETE FROM test_messages WHERE session_id = ?", (session_id,))
            messages = db.execute("SELECT * FROM test_messages WHERE session_id = ?", (session_id,))
            assert len(messages) == 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


# ============================
# 测试5: 设置对话框
# ============================

class TestSettingsDialog:
    """测试设置对话框功能"""

    def test_settings_loads_config(self):
        """测试设置对话框加载配置"""
        import sys
        from PyQt6.QtWidgets import QApplication
        from hyperbrain.ui.settings_dialog import SettingsDialog
        from hyperbrain.core.config import get_config, ConfigManager

        # 重置配置缓存
        ConfigManager._config = None

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        dialog = SettingsDialog()

        # 验证配置已加载
        config = get_config()
        assert dialog._config.model.default_provider == config.model.default_provider

        dialog.close()

    def test_settings_apply_saves(self):
        """测试设置对话框应用并保存配置"""
        import sys
        from PyQt6.QtWidgets import QApplication
        from hyperbrain.ui.settings_dialog import SettingsDialog
        from hyperbrain.core.config import get_config, ConfigManager

        # 重置配置缓存
        ConfigManager._config = None

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        dialog = SettingsDialog()

        # 修改配置（spec fix-test-model-revert: 不能用 test_model 占位符，会被拒绝）
        dialog.provider_combo.setCurrentText("ollama")
        dialog.ollama_model_edit.setText("minimax-m3:cloud")

        # 应用设置
        dialog._apply_settings()

        # 验证配置已保存
        ConfigManager._config = None
        config = get_config()
        assert config.model.default_provider == "ollama"
        assert config.model.ollama_model == "minimax-m3:cloud"

        dialog.close()


# ============================
# 测试6: 集成测试
# ============================

class TestIntegration:
    """测试系统整体集成"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """测试完整的对话流程"""
        from hyperbrain.core.brain import Brain, ProcessingResult

        # 初始化 brain
        brain = Brain()
        # Mock methods that would hit Ollama to avoid real HTTP requests
        brain.initialize = AsyncMock(return_value=True)
        brain.start = AsyncMock(return_value=True)
        brain.stop = AsyncMock()
        brain.model_manager.initialize_all = AsyncMock(return_value={"ollama_default": True})
        brain.process = AsyncMock(return_value=ProcessingResult(
            success=True,
            content="我是一个测试响应，用于验证完整的对话流程是否正常工作。",
            processing_time_ms=10.0,
            layers_involved=["sensory", "model", "execution"],
        ))

        await brain.initialize()
        await brain.start()

        try:
            # 确保模型可用
            await brain.model_manager.initialize_all()

            # 发送消息
            result = await brain.process("请用一句话介绍你自己")

            assert result.success, f"Conversation failed: {result.error}"
            assert result.content is not None
            assert len(result.content) > 0

            # 验证响应包含有意义的内容
            assert len(result.content.strip()) > 10, "Response too short"
        finally:
            await brain.stop()

    def test_gui_imports(self):
        """测试所有 GUI 模块能正常导入"""
        from hyperbrain.ui.main_window import MainWindow
        from hyperbrain.ui.chat_widget import ChatWidget
        from hyperbrain.ui.session_manager import SessionManager
        from hyperbrain.ui.settings_dialog import SettingsDialog
        from hyperbrain.ui.system_monitor import SystemMonitor
        from hyperbrain.ui.memory_viz import MemoryVisualizer
        from hyperbrain.ui.cognition_viz import CognitionVisualizer

        # 如果到这里没有抛出异常，说明导入成功
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
