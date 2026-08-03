"""
聊天界面

沉浸式对话界面，支持Markdown渲染、代码高亮、消息气泡等
"""

import re
import markdown
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QFrame, QLabel, QSizePolicy,
    QApplication, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt6.QtGui import (
    QTextCursor, QFont, QColor, QTextCharFormat,
    QAction, QIcon
)
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from hyperbrain.core.logger import get_logger
from hyperbrain.ui.themes import theme_manager
from hyperbrain.database.sqlite_manager import SQLiteManager

logger = get_logger("ui.chat")


class MessageBubble(QFrame):
    """
    消息气泡组件
    
    显示单条聊天消息，支持不同角色的样式
    """
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, parent=None):
        super().__init__(parent)
        
        self.role = role
        self.raw_content = content
        self.timestamp = timestamp or datetime.now()
        
        self._setup_ui()
        self._apply_style()
        self.set_content(content)
    
    def _setup_ui(self):
        """设置UI布局 - 微信风格"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 创建消息气泡容器
        self.bubble_container = QFrame()
        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)
        
        # 头部：角色和时间（放在气泡内部）
        header_layout = QHBoxLayout()
        
        self.role_label = QLabel()
        self.role_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.role_label)
        
        header_layout.addStretch()
        
        self.time_label = QLabel(self.timestamp.strftime("%H:%M:%S"))
        self.time_label.setStyleSheet("font-size: 10px;")
        header_layout.addWidget(self.time_label)
        
        bubble_layout.addLayout(header_layout)
        
        # 内容区域
        self.content_label = QTextEdit()
        self.content_label.setReadOnly(True)
        self.content_label.setFrameStyle(QFrame.Shape.NoFrame)
        self.content_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 设置文档边距
        self.content_label.document().setDocumentMargin(0)
        
        bubble_layout.addWidget(self.content_label)
        
        # 根据角色设置对齐方式
        if self.role == "user":
            layout.addStretch()
            layout.addWidget(self.bubble_container)
        else:
            layout.addWidget(self.bubble_container)
            layout.addStretch()
        
        # 设置固定宽度策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    
    def _apply_style(self):
        """应用角色样式 - 微信风格"""
        colors = theme_manager.colors
        
        role_names = {
            "user": "你",
            "assistant": "HyperBrain",
            "system": "系统"
        }
        
        # 微信风格颜色
        bg_colors = {
            "user": "#95ec69",  # 微信绿色（用户消息）
            "assistant": "#ffffff",  # 白色（AI消息）
            "system": "#fff3cd"  # 浅黄色（系统消息）
        }
        
        self.role_label.setText(role_names.get(self.role, self.role))
        self.role_label.setStyleSheet(
            f"font-weight: bold; font-size: 12px; color: #666666;"
        )
        self.time_label.setStyleSheet(f"font-size: 10px; color: #999999;")
        
        # 气泡容器样式 - 无边框，圆角
        self.bubble_container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_colors.get(self.role, '#ffffff')};
                border: none;
                border-radius: 8px;
            }}
        """)
        
        # 消息气泡整体样式
        self.setStyleSheet("""
            MessageBubble {
                background-color: transparent;
                border: none;
            }
        """)
    
    def set_content(self, content: str):
        """
        设置消息内容，支持Markdown渲染
        
        Args:
            content: 消息文本内容
        """
        self.raw_content = content
        html_content = self._render_markdown(content)
        self.content_label.setHtml(html_content)
        
        # 调整高度适应内容
        doc = self.content_label.document()
        doc.setTextWidth(self.content_label.viewport().width())
        height = doc.size().height()
        self.content_label.setMinimumHeight(int(height) + 10)
        self.content_label.setMaximumHeight(int(height) + 50)
    
    def _render_markdown(self, text: str) -> str:
        """
        渲染Markdown文本为HTML
        
        Args:
            text: Markdown文本
            
        Returns:
            str: HTML字符串
        """
        colors = theme_manager.colors
        
        # 处理代码块
        text = self._process_code_blocks(text)
        
        # 转换Markdown为HTML
        md = markdown.Markdown(extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br'
        ])
        
        html = md.convert(text)
        
        # 包装样式 - 使用黑色字体
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #000000;
                background: transparent;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                color: #333333;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
                overflow-x: auto;
                margin: 8px 0;
            }}
            pre code {{
                background: none;
                padding: 0;
                border: none;
            }}
            blockquote {{
                border-left: 4px solid #95ec69;
                margin: 8px 0;
                padding: 8px 16px;
                background-color: #f9f9f9;
                border-radius: 0 6px 6px 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 8px 0;
            }}
            th, td {{
                border: 1px solid #e0e0e0;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            a {{
                color: #576b95;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            ul, ol {{
                margin: 8px 0;
                padding-left: 24px;
            }}
            li {{
                margin: 4px 0;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin: 12px 0 8px 0;
                color: #000000;
            }}
            h1 {{ font-size: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; }}
            h2 {{ font-size: 18px; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; }}
            h3 {{ font-size: 16px; }}
            p {{ margin: 8px 0; }}
            hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 12px 0; }}
            img {{ max-width: 100%; border-radius: 6px; }}
        </style>
        </head>
        <body>{html}</body>
        </html>
        """
        
        return styled_html
    
    def _process_code_blocks(self, text: str) -> str:
        """
        处理代码块，使用Pygments进行语法高亮
        
        Args:
            text: 原始文本
            
        Returns:
            str: 处理后的文本
        """
        colors = theme_manager.colors
        is_dark = theme_manager.current_theme.value == "dark"
        
        def replace_code_block(match):
            lang = match.group(1) or "text"
            code = match.group(2)
            
            try:
                if lang and lang != "text":
                    lexer = get_lexer_by_name(lang, stripall=True)
                else:
                    lexer = guess_lexer(code)
            except Exception:
                lexer = get_lexer_by_name("text")
            
            style = 'monokai' if is_dark else 'default'
            formatter = HtmlFormatter(
                style=style,
                noclasses=True,
                prestyles=f'background-color: {colors["code_bg"]}; padding: 12px; border-radius: 6px;'
            )
            
            highlighted = highlight(code, lexer, formatter)
            return f"\n{highlighted}\n"
        
        # 匹配 ```language\ncode\n``` 格式
        # spec L1: 兼容 c++/c#/objective-c++ 等含特殊字符的语言名，并允许单行代码块
        pattern = r'```([^\n`]*)\n?(.*?)```'
        text = re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
        
        return text
    
    def append_content(self, text: str):
        """
        追加内容（用于流式输出）
        
        Args:
            text: 追加的文本
        """
        self.raw_content += text
        self.set_content(self.raw_content)
    
    def get_text(self) -> str:
        """获取原始文本内容"""
        return self.raw_content
    
    def minimumSizeHint(self) -> QSize:
        """返回最小尺寸建议"""
        return QSize(200, 60)


class ChatWidget(QWidget):
    """
    聊天组件
    
    沉浸式对话界面，支持：
    - Markdown渲染
    - 代码高亮显示
    - 消息气泡样式
    - 图片显示
    - 多行文本输入
    - 发送按钮和快捷键
    - 聊天记录滚动
    
    Signals:
        message_sent: 用户发送消息时触发，传递消息文本
    """
    
    message_sent = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.message_history: List[Dict[str, Any]] = []
        self.on_send_callback: Optional[Callable] = None
        self.on_stop_callback: Optional[Callable] = None
        self._current_bubble: Optional[MessageBubble] = None
        self._is_streaming = False
        
        self._setup_ui()
        logger.info("ChatWidget initialized")
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 消息显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(8)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, 1)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)
        
        # 输入框
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("输入消息... (Shift+Enter换行, Enter发送)")
        self.input_edit.setMaximumBlockCount(10)
        self.input_edit.setFixedHeight(80)
        self.input_edit.installEventFilter(self)
        input_layout.addWidget(self.input_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # 左侧按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.setToolTip("清空聊天记录 (Ctrl+L)")
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("保存")
        self.save_button.setToolTip("保存聊天记录")
        self.save_button.clicked.connect(self._save_chat)
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        
        # 右侧按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setToolTip("停止生成")
        self.stop_button.clicked.connect(self._stop_generation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.send_button = QPushButton("发送")
        self.send_button.setToolTip("发送消息 (Enter)")
        self.send_button.setDefault(True)
        self.send_button.clicked.connect(self._send_message)
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        layout.addWidget(input_frame)
    
    def eventFilter(self, obj, event):
        """
        事件过滤器，处理输入框快捷键
        
        Args:
            obj: 事件对象
            event: 事件
            
        Returns:
            bool: 是否已处理
        """
        if obj == self.input_edit and event.type() == event.Type.KeyPress:
            # In PyQt6, the event is already a QKeyEvent when type is KeyPress
            key_event = event
            
            # Enter发送，Shift+Enter换行
            if key_event.key() == Qt.Key.Key_Return and not key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._send_message()
                return True
            
            # Ctrl+L清空
            if key_event.key() == Qt.Key.Key_L and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.clear_chat()
                return True
        
        return super().eventFilter(obj, event)
    
    def _send_message(self):
        """发送消息"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        # 添加用户消息
        self.add_message("user", text)
        self.input_edit.clear()
        
        # 发射信号
        self.message_sent.emit(text)
        
        # 调用回调
        if self.on_send_callback:
            self.on_send_callback(text)
    
    def add_message(self, role: str, content: str) -> MessageBubble:
        """
        添加消息到显示区域
        
        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            
        Returns:
            MessageBubble: 创建的消息气泡
        """
        bubble = MessageBubble(role, content)
        
        # 插入到stretch之前
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            bubble
        )
        
        # 保存到历史
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 滚动到底部
        self._scroll_to_bottom()
        
        return bubble
    
    def start_streaming_message(self) -> MessageBubble:
        """
        开始流式消息
        
        Returns:
            MessageBubble: 消息气泡，用于后续追加内容
        """
        self._is_streaming = True
        self._current_bubble = self.add_message("assistant", "")
        self.stop_button.setEnabled(True)
        self.send_button.setEnabled(False)
        return self._current_bubble
    
    def append_streaming_text(self, text: str):
        """
        追加流式文本
        
        Args:
            text: 追加的文本
        """
        if self._current_bubble and self._is_streaming:
            self._current_bubble.append_content(text)
            self._scroll_to_bottom()
    
    def end_streaming(self):
        """结束流式输出"""
        self._is_streaming = False
        self._current_bubble = None
        self.stop_button.setEnabled(False)
        self.send_button.setEnabled(True)
    
    def _stop_generation(self):
        """停止生成"""
        self._is_streaming = False
        self.end_streaming()
        if self.on_stop_callback:
            self.on_stop_callback()
        logger.info("Generation stopped by user")
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """清空聊天记录"""
        # 移除所有消息气泡
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.message_history.clear()
        self._current_bubble = None
        self._is_streaming = False
        
        logger.info("Chat cleared")
    
    def _save_chat(self):
        """保存聊天记录"""
        if not self.message_history:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存聊天记录",
            f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# HyperBrain 聊天记录\n\n")
                    f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    
                    for msg in self.message_history:
                        role = msg["role"]
                        content = msg["content"]
                        timestamp = msg.get("timestamp", "")
                        
                        role_names = {
                            "user": "用户",
                            "assistant": "HyperBrain",
                            "system": "系统"
                        }
                        
                        f.write(f"## {role_names.get(role, role)} ({timestamp})\n\n")
                        f.write(f"{content}\n\n")
                        f.write("---\n\n")
                
                logger.info(f"Chat saved to {filename}")
            except Exception as e:
                logger.error(f"Failed to save chat: {e}")
    
    def set_send_callback(self, callback: Callable):
        """
        设置发送回调
        
        Args:
            callback: 回调函数，接收消息文本
        """
        self.on_send_callback = callback
    
    def set_stop_callback(self, callback: Callable):
        """
        设置停止生成回调
        
        Args:
            callback: 回调函数，无参数
        """
        self.on_stop_callback = callback
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取聊天历史
        
        Returns:
            List[Dict]: 消息历史列表
        """
        return self.message_history.copy()
    
    def set_input_enabled(self, enabled: bool):
        """
        设置输入框状态
        
        Args:
            enabled: 是否启用
        """
        self.input_edit.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def load_session_messages(self, session_id: str):
        """
        按 session_id 从数据库加载历史消息
        
        Args:
            session_id: 会话ID
        """
        self.clear_chat()
        if not session_id:
            return

        try:
            db = SQLiteManager()
            rows = db.get_conversation_history(session_id, limit=100)
            # 数据库按 timestamp DESC 返回，需要反转顺序显示
            for row in reversed(rows):
                role = row.get("role", "system")
                content = row.get("content", "")
                timestamp = row.get("timestamp", "")
                if content:
                    bubble = MessageBubble(role, content)
                    if timestamp:
                        try:
                            bubble.timestamp = datetime.fromisoformat(timestamp)
                            bubble.time_label.setText(bubble.timestamp.strftime("%H:%M:%S"))
                        except Exception:
                            pass
                    self.messages_layout.insertWidget(
                        self.messages_layout.count() - 1,
                        bubble
                    )
                    self.message_history.append({
                        "role": role,
                        "content": content,
                        "timestamp": timestamp or datetime.now().isoformat()
                    })
            self._scroll_to_bottom()
            logger.info(f"Loaded {len(rows)} messages for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to load session messages: {e}")

    def clear_messages(self):
        """清空聊天记录（兼容 main_window.py 调用）"""
        self.clear_chat()

    def save_conversation(self, file_path: str):
        """保存聊天记录到指定文件"""
        if not self.message_history:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# HyperBrain 聊天记录\n\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                for msg in self.message_history:
                    role = msg["role"]
                    content = msg["content"]
                    timestamp = msg.get("timestamp", "")
                    
                    role_names = {
                        "user": "用户",
                        "assistant": "HyperBrain",
                        "system": "系统"
                    }
                    
                    f.write(f"## {role_names.get(role, role)} ({timestamp})\n\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")
            
            logger.info(f"Chat saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save chat: {e}")
