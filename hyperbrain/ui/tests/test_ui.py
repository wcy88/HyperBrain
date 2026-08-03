"""
UI模块单元测试

测试所有UI组件的基本功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from hyperbrain.ui.themes import ThemeManager, ThemeType, theme_manager
from hyperbrain.ui.chat_widget import ChatWidget, MessageBubble
from hyperbrain.ui.memory_viz import MemoryVisualizer, MemoryGraphView
from hyperbrain.ui.cognition_viz import CognitionVisualizer, CognitionStepType
from hyperbrain.ui.system_monitor import SystemMonitor
from hyperbrain.ui.main_window import MainWindow


# 全局QApplication实例
@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestThemeManager:
    """测试主题管理器"""
    
    def test_initial_theme(self):
        """测试初始主题"""
        manager = ThemeManager()
        assert manager.current_theme == ThemeType.DARK
    
    def test_set_theme(self):
        """测试设置主题"""
        manager = ThemeManager()
        manager.set_theme(ThemeType.LIGHT)
        assert manager.current_theme == ThemeType.LIGHT
    
    def test_toggle_theme(self):
        """测试切换主题"""
        manager = ThemeManager()
        initial = manager.current_theme
        
        new_theme = manager.toggle_theme()
        assert new_theme != initial
        
        new_theme2 = manager.toggle_theme()
        assert new_theme2 == initial
    
    def test_colors(self):
        """测试颜色配置"""
        manager = ThemeManager()
        colors = manager.colors
        
        assert "window_bg" in colors
        assert "widget_bg" in colors
        assert "text_primary" in colors
        assert "accent" in colors
    
    def test_stylesheet(self):
        """测试样式表生成"""
        manager = ThemeManager()
        stylesheet = manager.get_stylesheet()
        
        assert len(stylesheet) > 0
        assert "QMainWindow" in stylesheet
        assert "QWidget" in stylesheet
    
    def test_observer(self):
        """测试观察者模式"""
        manager = ThemeManager()
        callback = Mock()
        
        manager.add_observer(callback)
        manager.set_theme(ThemeType.LIGHT)
        
        callback.assert_called_once_with(ThemeType.LIGHT)
        
        manager.remove_observer(callback)


class TestMessageBubble:
    """测试消息气泡"""
    
    def test_creation(self, qapp):
        """测试创建"""
        bubble = MessageBubble("user", "Hello")
        assert bubble.role == "user"
        assert bubble.raw_content == "Hello"
    
    def test_set_content(self, qapp):
        """测试设置内容"""
        bubble = MessageBubble("assistant", "Test content")
        bubble.set_content("New content")
        assert bubble.raw_content == "New content"
    
    def test_append_content(self, qapp):
        """测试追加内容"""
        bubble = MessageBubble("user", "Hello")
        bubble.append_content(" World")
        assert bubble.raw_content == "Hello World"
    
    def test_get_text(self, qapp):
        """测试获取文本"""
        bubble = MessageBubble("system", "System message")
        assert bubble.get_text() == "System message"
    
    def test_different_roles(self, qapp):
        """测试不同角色"""
        roles = ["user", "assistant", "system"]
        for role in roles:
            bubble = MessageBubble(role, "Test")
            assert bubble.role == role


class TestChatWidget:
    """测试聊天组件"""
    
    def test_creation(self, qapp):
        """测试创建"""
        chat = ChatWidget()
        assert chat is not None
        assert len(chat.message_history) == 0
    
    def test_add_message(self, qapp):
        """测试添加消息"""
        chat = ChatWidget()
        bubble = chat.add_message("user", "Hello")
        
        assert len(chat.message_history) == 1
        assert chat.message_history[0]["role"] == "user"
        assert chat.message_history[0]["content"] == "Hello"
    
    def test_clear_chat(self, qapp):
        """测试清空聊天"""
        chat = ChatWidget()
        chat.add_message("user", "Hello")
        chat.clear_chat()
        
        assert len(chat.message_history) == 0
    
    def test_get_history(self, qapp):
        """测试获取历史"""
        chat = ChatWidget()
        chat.add_message("user", "Hello")
        
        history = chat.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
    
    def test_set_send_callback(self, qapp):
        """测试设置发送回调"""
        chat = ChatWidget()
        callback = Mock()
        
        chat.set_send_callback(callback)
        assert chat.on_send_callback == callback
    
    def test_streaming(self, qapp):
        """测试流式输出"""
        chat = ChatWidget()
        chat.start_streaming_message()
        
        assert chat._is_streaming is True
        
        chat.append_streaming_text("Hello")
        chat.end_streaming()
        
        assert chat._is_streaming is False


class TestMemoryVisualizer:
    """测试记忆可视化"""
    
    def test_creation(self, qapp):
        """测试创建"""
        viz = MemoryVisualizer()
        assert viz is not None
    
    def test_update_short_term_stats(self, qapp):
        """测试更新短期记忆统计"""
        viz = MemoryVisualizer()
        viz.update_short_term_stats(50, 100)
        
        assert viz.stm_items_label.text() == "50 / 100"
    
    def test_update_long_term_stats(self, qapp):
        """测试更新长期记忆统计"""
        viz = MemoryVisualizer()
        viz.update_long_term_stats(1000, True)
        
        assert viz.ltm_count_label.text() == "1000"
        assert viz.ltm_index_label.text() == "已构建"
    
    def test_update_memory_types(self, qapp):
        """测试更新记忆类型"""
        viz = MemoryVisualizer()
        types_data = {
            "episodic": 10,
            "semantic": 20,
            "procedural": 5
        }
        viz.update_memory_types(types_data)
        
        assert viz.types_table.rowCount() == 3
    
    def test_update_memory_list(self, qapp):
        """测试更新记忆列表"""
        viz = MemoryVisualizer()
        memories = [
            {"content": "Test memory", "type": "semantic", "importance": 0.8},
            {"content": "Another memory", "type": "episodic", "importance": 0.5}
        ]
        viz.update_memory_list(memories)
        
        assert len(viz._memories) == 2


class TestCognitionVisualizer:
    """测试认知可视化"""
    
    def test_creation(self, qapp):
        """测试创建"""
        viz = CognitionVisualizer()
        assert viz is not None
        assert len(viz._cognition_chain) == 0
    
    def test_add_cognition_step(self, qapp):
        """测试添加认知步骤"""
        viz = CognitionVisualizer()
        step_id = viz.add_cognition_step(
            CognitionStepType.REASONING,
            "Test reasoning",
            0.8
        )
        
        assert len(viz._cognition_chain) == 1
        assert viz._cognition_chain[0].content == "Test reasoning"
    
    def test_clear_chain(self, qapp):
        """测试清空思维链"""
        viz = CognitionVisualizer()
        viz.add_cognition_step(CognitionStepType.PERCEPTION, "Test")
        viz.clear_chain()
        
        assert len(viz._cognition_chain) == 0
    
    def test_get_chain(self, qapp):
        """测试获取思维链"""
        viz = CognitionVisualizer()
        viz.add_cognition_step(CognitionStepType.DECISION, "Test decision")
        
        chain = viz.get_chain()
        assert len(chain) == 1
        assert chain[0]["content"] == "Test decision"
    
    def test_update_decision(self, qapp):
        """测试更新决策"""
        viz = CognitionVisualizer()
        viz.update_decision("Test decision", 0.9, 3)
        
        assert viz.decision_content_label.text() == "Test decision"
        assert viz.decision_confidence_bar.value() == 90
    
    def test_update_cognitive_status(self, qapp):
        """测试更新认知状态"""
        viz = CognitionVisualizer()
        abilities = {
            "reasoning": 0.8,
            "learning": 0.7,
            "memory": 0.9
        }
        viz.update_cognitive_status(0.5, "Test", 3, abilities)
        
        assert viz.cognitive_load_bar.value() == 50
        assert viz.reasoning_ability_bar.value() == 80


class TestSystemMonitor:
    """测试系统监控"""
    
    def test_creation(self, qapp):
        """测试创建"""
        monitor = SystemMonitor()
        assert monitor is not None
    
    def test_update_capabilities(self, qapp):
        """测试更新能力"""
        monitor = SystemMonitor()
        capabilities = {
            "reasoning": 0.8,
            "learning": 0.7,
            "memory": 0.9,
            "attention": 0.6,
            "planning": 0.75,
            "problem_solving": 0.85,
            "creativity": 0.7,
            "empathy": 0.8,
            "communication": 0.9
        }
        monitor.update_capabilities(capabilities)
        
        assert monitor.reasoning_bar.value() == 80
        assert monitor.learning_bar.value() == 70
    
    def test_update_emotion(self, qapp):
        """测试更新情感"""
        monitor = SystemMonitor()
        dimensions = {
            "pleasure": 0.6,
            "arousal": 0.4,
            "dominance": 0.7
        }
        monitor.update_emotion("快乐", 0.8, "正面", dimensions)
        
        assert monitor.current_emotion_label.text() == "快乐"
        assert monitor.emotion_intensity_bar.value() == 80
    
    def test_update_tasks(self, qapp):
        """测试更新任务"""
        monitor = SystemMonitor()
        tasks = [
            {"name": "Task 1", "type": "cognitive", "status": "running", "progress": 50, "start_time": "10:00"},
            {"name": "Task 2", "type": "execution", "status": "completed", "progress": 100, "start_time": "09:00"}
        ]
        monitor.update_tasks(tasks)
        
        assert len(monitor._tasks) == 2
    
    def test_add_log_message(self, qapp):
        """测试添加日志"""
        monitor = SystemMonitor()
        monitor.add_log_message("INFO", "Test message", "test")
        
        log_text = monitor.log_text.toPlainText()
        assert "Test message" in log_text
    
    def test_set_system_status(self, qapp):
        """测试设置系统状态"""
        monitor = SystemMonitor()
        monitor.set_system_status("错误", True)
        
        assert monitor.system_status_label.text() == "错误"
    
    def test_get_status(self, qapp):
        """测试获取状态"""
        monitor = SystemMonitor()
        status = monitor.get_status()
        
        assert "cpu" in status
        assert "memory" in status
        assert "uptime" in status


class TestMainWindow:
    """测试主窗口"""
    
    def test_creation(self, qapp):
        """测试创建"""
        window = MainWindow()
        assert window is not None
        assert window.windowTitle() == "HyperBrain - 拟人脑认知架构系统"
    
    def test_components(self, qapp):
        """测试组件"""
        window = MainWindow()
        
        assert window.chat_widget is not None
        assert window.memory_viz is not None
        assert window.cognition_viz is not None
        assert window.system_monitor is not None
    
    def test_getters(self, qapp):
        """测试获取器"""
        window = MainWindow()
        
        assert window.get_chat_widget() is not None
        assert window.get_memory_viz() is not None
        assert window.get_cognition_viz() is not None
        assert window.get_system_monitor() is not None
    
    def test_update_system_status(self, qapp):
        """测试更新系统状态"""
        window = MainWindow()
        window.update_system_status("测试中")
        
        assert window.status_label.text() == "测试中"


class TestMemoryGraphView:
    """测试记忆关联图"""
    
    def test_creation(self, qapp):
        """测试创建"""
        view = MemoryGraphView()
        assert view is not None
    
    def test_add_node(self, qapp):
        """测试添加节点"""
        view = MemoryGraphView()
        view.add_node("node1", "Test Node", "semantic", 0, 0, 30)
        
        assert "node1" in view._nodes
    
    def test_add_edge(self, qapp):
        """测试添加边"""
        view = MemoryGraphView()
        view.add_node("node1", "Node 1", "semantic", 0, 0)
        view.add_node("node2", "Node 2", "episodic", 100, 0)
        view.add_edge("node1", "node2", 0.8)
        
        assert len(view._edges) == 1
    
    def test_clear_graph(self, qapp):
        """测试清空图形"""
        view = MemoryGraphView()
        view.add_node("node1", "Test", "semantic")
        view.clear_graph()
        
        assert len(view._nodes) == 0
        assert len(view._edges) == 0


class TestIntegration:
    """集成测试"""
    
    def test_theme_application(self, qapp):
        """测试主题应用"""
        window = MainWindow()
        
        # 切换主题
        theme_manager.toggle_theme()
        
        # 验证主题已应用
        assert theme_manager.current_theme in [ThemeType.LIGHT, ThemeType.DARK]
    
    def test_chat_to_cognition_flow(self, qapp):
        """测试聊天到认知流程"""
        chat = ChatWidget()
        cognition = CognitionVisualizer()
        
        # 添加聊天消息
        chat.add_message("user", "Hello")
        
        # 添加认知步骤
        cognition.add_cognition_step(CognitionStepType.PERCEPTION, "感知用户输入")
        cognition.add_cognition_step(CognitionStepType.REASONING, "推理回复内容")
        
        assert len(chat.message_history) == 1
        assert len(cognition._cognition_chain) == 2
    
    def test_memory_and_monitor_integration(self, qapp):
        """测试记忆和监控集成"""
        memory = MemoryVisualizer()
        monitor = SystemMonitor()
        
        # 更新记忆统计
        memory.update_short_term_stats(50, 100)
        memory.update_long_term_stats(1000, True)
        
        # 更新监控
        monitor.update_capabilities({"memory": 0.9})
        
        assert memory.stm_items_label.text() == "50 / 100"
        assert monitor.memory_ability_bar.value() == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
