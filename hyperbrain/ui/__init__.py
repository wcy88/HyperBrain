"""
UI界面模块

HyperBrain 的图形用户界面模块，提供完整的桌面应用交互体验
"""

from .themes import ThemeManager, ThemeType, theme_manager
from .splash_screen import SplashScreen, InitializationWorker
from .chat_widget import ChatWidget, MessageBubble
from .memory_viz import MemoryVisualizer, MemoryGraphView
from .cognition_viz import CognitionVisualizer, CognitionGraphView, CognitionNode, CognitionStepType
from .system_monitor import SystemMonitor
from .settings_dialog import SettingsDialog
from .main_window import MainWindow
from .ui_manager import UIManager, get_ui_manager

__all__ = [
    # 主题
    "ThemeManager",
    "ThemeType",
    "theme_manager",
    # 启动界面
    "SplashScreen",
    "InitializationWorker",
    # 聊天界面
    "ChatWidget",
    "MessageBubble",
    # 记忆可视化
    "MemoryVisualizer",
    "MemoryGraphView",
    # 认知可视化
    "CognitionVisualizer",
    "CognitionGraphView",
    "CognitionNode",
    "CognitionStepType",
    # 系统监控
    "SystemMonitor",
    # 设置
    "SettingsDialog",
    # 主窗口
    "MainWindow",
    # UI管理器
    "UIManager",
    "get_ui_manager",
]
