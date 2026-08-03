"""
UI管理器

统一管理所有UI组件，提供界面切换、导航和事件处理
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config
from hyperbrain.ui.main_window import MainWindow
from hyperbrain.ui.splash_screen import SplashScreen
from hyperbrain.ui.chat_widget import ChatWidget
from hyperbrain.ui.memory_viz import MemoryVisualizer
from hyperbrain.ui.cognition_viz import CognitionVisualizer, CognitionStepType
from hyperbrain.ui.system_monitor import SystemMonitor
from hyperbrain.ui.settings_dialog import SettingsDialog
from hyperbrain.ui.themes import theme_manager

logger = get_logger("ui.manager")


class UIManager(QObject):
    """
    UI管理器
    
    统一管理所有UI组件，提供：
    1. 界面切换和导航
    2. 事件处理
    3. 与后端系统交互
    4. 组件生命周期管理
    
    Signals:
        ui_ready: UI准备就绪时触发
        message_received: 收到用户消息时触发
        ui_closed: UI关闭时触发
    """
    
    ui_ready = pyqtSignal()
    message_received = pyqtSignal(str)
    ui_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self._app: Optional[QApplication] = None
        self._main_window: Optional[MainWindow] = None
        self._splash: Optional[SplashScreen] = None
        
        self._brain: Optional[Any] = None
        self._is_running = False
        
        logger.info("UIManager initialized")
    
    def initialize(self, app: QApplication) -> None:
        """
        初始化UI管理器
        
        Args:
            app: QApplication实例
        """
        self._app = app
        
        # 显示启动画面
        self._show_splash()
    
    def _show_splash(self):
        """显示启动画面"""
        self._splash = SplashScreen()
        self._splash.show()
        self._splash.initialization_finished.connect(self._on_initialization_finished)
        self._splash.start_initialization()
    
    def _on_initialization_finished(self, success: bool, message: str):
        """
        初始化完成回调
        
        Args:
            success: 是否成功
            message: 完成消息
        """
        if success:
            # 关闭启动画面
            if self._splash:
                self._splash.finish(None)
                self._splash = None
            
            # 创建主窗口
            self._create_main_window()
            
            # 发射就绪信号
            self.ui_ready.emit()
            logger.info("UI ready")
        else:
            logger.error(f"Initialization failed: {message}")
            QMessageBox.critical(None, "初始化失败", message)
    
    def _create_main_window(self):
        """创建主窗口"""
        self._main_window = MainWindow()
        
        # 连接信号
        self._main_window.window_closed.connect(self._on_window_closed)
        
        # 连接聊天组件
        if self._main_window.chat_widget:
            self._main_window.chat_widget.message_sent.connect(self._on_message_sent)
            self._main_window.chat_widget.set_send_callback(self._on_message_sent)
        
        # 显示窗口
        self._main_window.show()
        self._is_running = True
        
        logger.info("Main window created and shown")
    
    def _on_window_closed(self):
        """窗口关闭回调"""
        self._is_running = False
        self.ui_closed.emit()
        logger.info("UI closed")
    
    def _on_message_sent(self, message: str):
        """
        消息发送回调
        
        Args:
            message: 用户消息
        """
        self.message_received.emit(message)
        logger.info(f"Message received: {message[:50]}...")
    
    def show_main_window(self):
        """显示主窗口"""
        if self._main_window:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()
    
    def hide_main_window(self):
        """隐藏主窗口"""
        if self._main_window:
            self._main_window.hide()
    
    def show_splash(self):
        """显示启动画面"""
        if not self._splash:
            self._splash = SplashScreen()
            self._splash.show()
    
    def close_splash(self):
        """关闭启动画面"""
        if self._splash:
            self._splash.close()
            self._splash = None
    
    def get_main_window(self) -> Optional[MainWindow]:
        """
        获取主窗口
        
        Returns:
            MainWindow: 主窗口实例
        """
        return self._main_window
    
    def get_chat_widget(self) -> Optional[ChatWidget]:
        """
        获取聊天组件
        
        Returns:
            ChatWidget: 聊天组件
        """
        if self._main_window:
            return self._main_window.get_chat_widget()
        return None
    
    def get_memory_viz(self) -> Optional[MemoryVisualizer]:
        """
        获取记忆可视化组件
        
        Returns:
            MemoryVisualizer: 记忆可视化组件
        """
        if self._main_window:
            return self._main_window.get_memory_viz()
        return None
    
    def get_cognition_viz(self) -> Optional[CognitionVisualizer]:
        """
        获取认知可视化组件
        
        Returns:
            CognitionVisualizer: 认知可视化组件
        """
        if self._main_window:
            return self._main_window.get_cognition_viz()
        return None
    
    def get_system_monitor(self) -> Optional[SystemMonitor]:
        """
        获取系统监控组件
        
        Returns:
            SystemMonitor: 系统监控组件
        """
        if self._main_window:
            return self._main_window.get_system_monitor()
        return None
    
    def add_chat_message(self, role: str, content: str):
        """
        添加聊天消息
        
        Args:
            role: 角色
            content: 内容
        """
        chat = self.get_chat_widget()
        if chat:
            chat.add_message(role, content)
    
    def start_streaming_response(self):
        """开始流式响应"""
        chat = self.get_chat_widget()
        if chat:
            chat.start_streaming_message()
    
    def append_streaming_text(self, text: str):
        """
        追加流式文本
        
        Args:
            text: 文本
        """
        chat = self.get_chat_widget()
        if chat:
            chat.append_streaming_text(text)
    
    def end_streaming_response(self):
        """结束流式响应"""
        chat = self.get_chat_widget()
        if chat:
            chat.end_streaming()
    
    def add_cognition_step(self, step_type: str, content: str,
                          confidence: float = 1.0):
        """
        添加认知步骤
        
        Args:
            step_type: 步骤类型
            content: 内容
            confidence: 置信度
        """
        cognition = self.get_cognition_viz()
        if cognition:
            try:
                step_enum = CognitionStepType(step_type)
                cognition.add_cognition_step(step_enum, content, confidence)
            except ValueError:
                logger.warning(f"Unknown cognition step type: {step_type}")
    
    def update_memory_stats(self, stats: Dict[str, Any]):
        """
        更新记忆统计
        
        Args:
            stats: 统计数据
        """
        memory = self.get_memory_viz()
        if memory:
            stm = stats.get("short_term", {})
            memory.update_short_term_stats(
                stm.get("current_size", 0),
                stm.get("capacity", 100)
            )
            
            ltm = stats.get("long_term", {})
            memory.update_long_term_stats(
                ltm.get("total", 0),
                ltm.get("index_built", False)
            )
            
            types = stats.get("types", {})
            memory.update_memory_types(types)
    
    def update_system_status(self, status: Dict[str, Any]):
        """
        更新系统状态
        
        Args:
            status: 状态数据
        """
        monitor = self.get_system_monitor()
        if monitor:
            capabilities = status.get("capabilities", {})
            monitor.update_capabilities(capabilities)
            
            emotion = status.get("emotion", {})
            if emotion:
                monitor.update_emotion(
                    emotion.get("name", "平静"),
                    emotion.get("intensity", 0.5),
                    emotion.get("valence", "中性"),
                    emotion.get("dimensions", {})
                )
            
            tasks = status.get("tasks", [])
            monitor.update_tasks(tasks)
    
    def show_error(self, title: str, message: str):
        """
        显示错误对话框
        
        Args:
            title: 标题
            message: 消息
        """
        QMessageBox.critical(self._main_window, title, message)
    
    def show_warning(self, title: str, message: str):
        """
        显示警告对话框
        
        Args:
            title: 标题
            message: 消息
        """
        QMessageBox.warning(self._main_window, title, message)
    
    def show_info(self, title: str, message: str):
        """
        显示信息对话框
        
        Args:
            title: 标题
            message: 消息
        """
        QMessageBox.information(self._main_window, title, message)
    
    def set_brain(self, brain: Any):
        """
        设置大脑实例
        
        Args:
            brain: HyperBrain实例
        """
        self._brain = brain
    
    def is_running(self) -> bool:
        """
        检查UI是否运行中
        
        Returns:
            bool: 是否运行中
        """
        return self._is_running
    
    def shutdown(self):
        """关闭UI"""
        self._is_running = False
        
        if self._main_window:
            self._main_window.close()
        
        if self._splash:
            self._splash.close()
        
        logger.info("UI manager shutdown")
    
    def process_events(self):
        """处理UI事件"""
        if self._app:
            self._app.processEvents()


# 全局UI管理器实例
_ui_manager: Optional[UIManager] = None


def get_ui_manager() -> UIManager:
    """
    获取全局UI管理器实例（单例模式）
    
    Returns:
        UIManager: UI管理器实例
    """
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = UIManager()
    return _ui_manager
