"""
主题管理模块

提供亮色和暗色主题支持，统一管理UI样式
"""

from enum import Enum
from typing import Dict, Any


class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"


class ThemeManager:
    """
    主题管理器
    
    管理应用的全局主题样式，支持亮色/暗色切换
    """
    
    _themes: Dict[ThemeType, Dict[str, Any]] = {
        ThemeType.LIGHT: {
            "name": "亮色",
            "window_bg": "#f5f5f5",
            "widget_bg": "#ffffff",
            "text_primary": "#212121",
            "text_secondary": "#757575",
            "accent": "#2196f3",
            "accent_hover": "#1976d2",
            "border": "#e0e0e0",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3",
            "chat_user_bg": "#e3f2fd",
            "chat_assistant_bg": "#f5f5f5",
            "chat_system_bg": "#fff3e0",
            "menu_bg": "#fafafa",
            "toolbar_bg": "#f5f5f5",
            "statusbar_bg": "#e0e0e0",
            "scrollbar_bg": "#f5f5f5",
            "scrollbar_handle": "#bdbdbd",
            "code_bg": "#f5f5f5",
            "code_border": "#e0e0e0",
            "memory_graph_bg": "#ffffff",
            "cognition_node_bg": "#e3f2fd",
            "cognition_edge": "#90a4ae",
        },
        ThemeType.DARK: {
            "name": "暗色",
            "window_bg": "#1e1e1e",
            "widget_bg": "#2d2d2d",
            "text_primary": "#ffffff",
            "text_secondary": "#a0a0a0",
            "accent": "#64b5f6",
            "accent_hover": "#42a5f5",
            "border": "#404040",
            "success": "#81c784",
            "warning": "#ffb74d",
            "error": "#e57373",
            "info": "#64b5f6",
            "chat_user_bg": "#1a237e",
            "chat_assistant_bg": "#2d2d2d",
            "chat_system_bg": "#3e2723",
            "menu_bg": "#2d2d2d",
            "toolbar_bg": "#1e1e1e",
            "statusbar_bg": "#1e1e1e",
            "scrollbar_bg": "#2d2d2d",
            "scrollbar_handle": "#616161",
            "code_bg": "#1e1e1e",
            "code_border": "#404040",
            "memory_graph_bg": "#2d2d2d",
            "cognition_node_bg": "#1a237e",
            "cognition_edge": "#607d8b",
        }
    }
    
    def __init__(self):
        self._current_theme = ThemeType.DARK
        self._observers = []
    
    @property
    def current_theme(self) -> ThemeType:
        """获取当前主题"""
        return self._current_theme
    
    @property
    def colors(self) -> Dict[str, Any]:
        """获取当前主题颜色配置"""
        return self._themes[self._current_theme]
    
    def set_theme(self, theme: ThemeType) -> None:
        """
        设置主题
        
        Args:
            theme: 主题类型
        """
        if theme != self._current_theme:
            self._current_theme = theme
            self._notify_observers()
    
    def toggle_theme(self) -> ThemeType:
        """切换主题"""
        new_theme = (
            ThemeType.LIGHT 
            if self._current_theme == ThemeType.DARK 
            else ThemeType.DARK
        )
        self.set_theme(new_theme)
        return new_theme
    
    def add_observer(self, callback) -> None:
        """
        添加主题变化观察者
        
        Args:
            callback: 回调函数，接收ThemeType参数
        """
        self._observers.append(callback)
    
    def remove_observer(self, callback) -> None:
        """
        移除主题变化观察者
        
        Args:
            callback: 回调函数
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self) -> None:
        """通知所有观察者主题变化"""
        for callback in self._observers:
            try:
                callback(self._current_theme)
            except Exception:
                pass
    
    def get_stylesheet(self) -> str:
        """
        获取完整QSS样式表
        
        Returns:
            str: QSS样式表字符串
        """
        c = self.colors
        return f"""
        QMainWindow {{
            background-color: {c['window_bg']};
        }}
        
        QWidget {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            font-size: 14px;
        }}
        
        QMenuBar {{
            background-color: {c['menu_bg']};
            color: {c['text_primary']};
            border-bottom: 1px solid {c['border']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QMenu {{
            background-color: {c['menu_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
        }}
        
        QMenu::item:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QToolBar {{
            background-color: {c['toolbar_bg']};
            border-bottom: 1px solid {c['border']};
            spacing: 8px;
            padding: 4px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: {c['text_primary']};
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QToolButton:hover {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {c['statusbar_bg']};
            color: {c['text_secondary']};
            border-top: 1px solid {c['border']};
        }}
        
        QPushButton {{
            background-color: {c['accent']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {c['accent_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {c['accent']};
        }}
        
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_secondary']};
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 8px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {c['accent']};
        }}
        
        QScrollBar:vertical {{
            background-color: {c['scrollbar_bg']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['scrollbar_handle']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['accent']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['scrollbar_bg']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['scrollbar_handle']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['accent']};
        }}
        
        QGroupBox {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }}
        
        QProgressBar {{
            border: 1px solid {c['border']};
            border-radius: 4px;
            text-align: center;
            background-color: {c['widget_bg']};
        }}
        
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 4px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {c['widget_bg']};
            color: {c['text_secondary']};
            padding: 8px 16px;
            border: 1px solid {c['border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c['border']};
        }}
        
        QTreeWidget, QTreeView {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
        }}
        
        QTreeWidget::item:selected, QTreeView::item:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QTreeWidget::item:hover, QTreeView::item:hover {{
            background-color: {c['border']};
        }}
        
        QListWidget, QListView {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
        }}
        
        QListWidget::item:selected, QListView::item:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QComboBox {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            selection-background-color: {c['accent']};
        }}
        
        QSlider::groove:horizontal {{
            height: 6px;
            background-color: {c['border']};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            width: 18px;
            height: 18px;
            background-color: {c['accent']};
            border-radius: 9px;
            margin: -6px 0;
        }}
        
        QSplitter::handle {{
            background-color: {c['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        QLabel {{
            color: {c['text_primary']};
        }}
        
        QLabel[class="secondary"] {{
            color: {c['text_secondary']};
        }}
        
        QDialog {{
            background-color: {c['window_bg']};
        }}
        
        QCheckBox {{
            color: {c['text_primary']};
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {c['border']};
            border-radius: 3px;
            background-color: {c['widget_bg']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {c['accent']};
        }}
        
        QRadioButton {{
            color: {c['text_primary']};
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {c['border']};
            border-radius: 9px;
            background-color: {c['widget_bg']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {c['accent']};
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QTableWidget {{
            background-color: {c['widget_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            gridline-color: {c['border']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {c['accent']};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {c['toolbar_bg']};
            color: {c['text_primary']};
            padding: 8px;
            border: 1px solid {c['border']};
            font-weight: bold;
        }}
        """


# 全局主题管理器实例
theme_manager = ThemeManager()
