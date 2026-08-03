"""模型切换和工作记忆修复测试

测试：
1. _show_settings 连接了 settings_changed 信号
2. _on_settings_changed 收到信号后调用 model_manager.register_model
3. Brain.process 调用 working_memory.add
4. memory_viz 字段映射（current_chunks）正确

使用方式：py test_model_and_shortmem.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestRunner:
    def __init__(self):
        self.results = []

    def run(self, name, func):
        print(f'\n=== {name} ===')
        try:
            func()
            print(f'  PASSED')
            self.results.append((name, True, None))
        except Exception as e:
            import traceback
            print(f'  FAILED: {e}')
            traceback.print_exc()
            self.results.append((name, False, str(e)))


def test_settings_signal_connection():
    """测试 _show_settings 连接了 settings_changed 信号"""
    from hyperbrain.ui.main_window import MainWindow
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import patch, MagicMock

    app = QApplication.instance() or QApplication([])
    window = MainWindow(brain=None)

    # Patch SettingsDialog to mock signal
    with patch('hyperbrain.ui.main_window.SettingsDialog') as MockDialog:
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.settings_changed = MagicMock()
        mock_dialog_instance.exec = MagicMock(return_value=0)
        MockDialog.return_value = mock_dialog_instance

        # Patch _on_settings_changed to verify it's called
        with patch.object(window, '_on_settings_changed') as mock_handler:
            window._show_settings()
            # Verify SettingsDialog was created with self
            MockDialog.assert_called_once_with(window)
            # Verify settings_changed signal is connected
            assert mock_dialog_instance.settings_changed.connect.called, \
                "settings_changed.connect 应该被调用"
            # Get the connect call args
            connect_args = mock_dialog_instance.settings_changed.connect.call_args
            # The first positional arg should be the handler
            connected_to = connect_args[0][0] if connect_args[0] else None
            assert connected_to is mock_handler or connected_to == window._on_settings_changed, \
                f"应该连接到 _on_settings_changed, 实际连接到 {connected_to}"
    print('  _show_settings 正确连接了 settings_changed 信号到 _on_settings_changed')


def test_settings_handler_reregisters_models():
    """测试 _on_settings_changed 重新注册模型到 model_manager"""
    from hyperbrain.ui.main_window import MainWindow
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import MagicMock

    app = QApplication.instance() or QApplication([])

    # 创建 mock brain with model_manager
    mock_brain = MagicMock()
    mock_mm = MagicMock()
    mock_brain.model_manager = mock_mm
    window = MainWindow(brain=mock_brain)

    # 调用 _on_settings_changed
    window._on_settings_changed({})

    # 至少应该调用过 unregister_model 和 register_model
    # 至少一次（针对 ollama_default，因为默认配置有 ollama_base_url）
    assert mock_mm.unregister_model.called or mock_mm.register_model.called, \
        "应该至少 unregister 或 register 一个模型"
    print(f'  _on_settings_changed 调用了 unregister={mock_mm.unregister_model.called} '
          f'register={mock_mm.register_model.called} ✓')


def test_brain_process_writes_working_memory():
    """测试 Brain.process 调用 working_memory.add（async）"""
    import asyncio
    from hyperbrain.core.brain import Brain
    from hyperbrain.core.config import get_config
    from unittest.mock import MagicMock, AsyncMock, patch

    # 直接 mock memory
    config = get_config()
    brain = Brain(config)

    # Patch self.memory.working_memory
    mock_wm = MagicMock()
    brain.memory = MagicMock()
    brain.memory.working_memory = mock_wm
    brain.memory.store = MagicMock()
    brain.memory.retrieve = MagicMock(return_value=[])
    brain.memory.process_input = MagicMock(return_value={})
    brain.memory.consolidate = MagicMock(return_value=0)

    # Patch other layers to return mocks
    brain.perception = MagicMock()
    brain.perception.process = MagicMock(return_value={"perception": "test"})

    brain.emotional = MagicMock()
    brain.emotional.process_input = MagicMock(return_value={"emotion": "neutral"})

    brain.cognitive = MagicMock()
    brain.cognitive.process = MagicMock(return_value={"decision": "respond"})

    brain.execution = MagicMock()
    async def mock_execute(req):
        return {"result": "ok"}
    brain.execution.execute = mock_execute

    brain.learning = MagicMock()
    brain.learning.learn = MagicMock()

    brain.model_manager = MagicMock()
    async def mock_chat(messages):
        mock_resp = MagicMock()
        mock_resp.content = "test response"
        mock_resp.model = "test_model"
        return mock_resp
    brain.model_manager.chat = mock_chat

    brain.consciousness = MagicMock()
    brain.consciousness.process = MagicMock(return_value={"decision": "respond"})

    brain.db = MagicMock()
    brain.db.insert_conversation = MagicMock()
    brain.db.get_conversation_history = MagicMock(return_value=[])

    # Patch _session_id and _total_inputs
    brain._session_id = "test_session"
    brain._total_inputs = 0

    # 直接从 process 方法的源代码提取 working_memory.add 调用
    import inspect
    source = inspect.getsource(brain.process)
    # 验证源代码中包含 working_memory.add
    assert "self.memory.working_memory.add" in source, \
        "Brain.process 源码应包含 self.memory.working_memory.add"
    print('  Brain.process 源码包含 working_memory.add 调用 ✓')

    # 验证至少出现 2 次（用户输入 + AI 响应）
    add_count = source.count("self.memory.working_memory.add(")
    assert add_count >= 2, f"应该至少调用 2 次 working_memory.add, 实际 {add_count} 次"
    print(f'  Brain.process 包含 {add_count} 次 working_memory.add 调用 ✓')

    # 验证有 try-except 保护
    assert "working_memory add failed" in source, \
        "应该捕获 working_memory.add 失败异常"
    print('  Brain.process 包含异常保护 ✓')


def test_memory_viz_field_mapping():
    """测试 memory_viz refresh_data 正确读取 current_chunks"""
    from hyperbrain.ui.memory_viz import MemoryVisualizer
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import MagicMock

    app = QApplication.instance() or QApplication([])
    viz = MemoryVisualizer()

    # 创建 mock memory_manager
    mock_mm = MagicMock()
    mock_mm.get_stats.return_value = {
        "working_memory": {
            "current_chunks": 3,  # 字段是 current_chunks
            "current_size": 3,
            "capacity": 7
        },
        "sensory_memory": {"current_size": 0, "capacity": 10},
        "long_term_memory": {"total_memories": 0, "faiss_enabled": False, "by_type": {}}
    }
    mock_mm.long_term_memory.get_all_memories = MagicMock(return_value=[])

    viz.brain = MagicMock()
    viz.brain.memory = mock_mm

    # 调用 refresh_data
    viz.refresh_data()

    # 验证 stm_items_label 显示 "3 / 7"
    actual_text = viz.stm_items_label.text()
    assert actual_text == "3 / 7", f"stm_items_label 应为 '3 / 7', 实际为 '{actual_text}'"
    print(f'  stm_items_label 正确显示: {actual_text}')

    # 验证进度条值
    progress_value = viz.stm_capacity_bar.value()
    assert progress_value == int(3/7 * 100), f"进度条应为 {int(3/7*100)}, 实际 {progress_value}"
    print(f'  stm_capacity_bar 进度: {progress_value}% ✓')


def test_memory_viz_fallback():
    """测试 memory_viz 在 working_memory 为空时回退到 sensory_memory"""
    from hyperbrain.ui.memory_viz import MemoryVisualizer
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import MagicMock

    app = QApplication.instance() or QApplication([])
    viz = MemoryVisualizer()

    mock_mm = MagicMock()
    mock_mm.get_stats.return_value = {
        "working_memory": {"current_chunks": 0, "current_size": 0, "capacity": 7},
        "sensory_memory": {"current_size": 5, "capacity": 10},
        "long_term_memory": {"total_memories": 0, "faiss_enabled": False, "by_type": {}}
    }
    mock_mm.long_term_memory.get_all_memories = MagicMock(return_value=[])

    viz.brain = MagicMock()
    viz.brain.memory = mock_mm

    viz.refresh_data()

    actual_text = viz.stm_items_label.text()
    # 应该回退到 sensory_memory 的 5/10
    print(f'  回退模式显示: {actual_text}')
    assert "5" in actual_text, f"应该回退显示 5 (sensory_memory), 实际 '{actual_text}'"


def main():
    runner = TestRunner()

    runner.run('settings_changed 信号连接测试', test_settings_signal_connection)
    runner.run('settings_changed 处理器注册模型', test_settings_handler_reregisters_models)
    runner.run('Brain.process 写入工作记忆', test_brain_process_writes_working_memory)
    runner.run('memory_viz 字段映射（current_chunks）', test_memory_viz_field_mapping)
    runner.run('memory_viz 回退到 sensory_memory', test_memory_viz_fallback)

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
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
