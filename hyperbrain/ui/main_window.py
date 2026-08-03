"""
Main Window for HyperBrain GUI

This module defines the main window class for the HyperBrain cognitive architecture system.
It provides the primary user interface with session management, chat, and visualization panels.
"""

import json
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMenuBar, QMenu,
    QToolBar, QLabel, QApplication, QDockWidget,
    QMessageBox, QFileDialog, QTabWidget,
    QPushButton, QTextEdit
)

from hyperbrain.ui.chat_widget import ChatWidget
from hyperbrain.ui.session_manager import SessionManager
from hyperbrain.ui.system_monitor import SystemMonitor
from hyperbrain.ui.memory_viz import MemoryVisualizer
from hyperbrain.ui.cognition_viz import CognitionVisualizer
from hyperbrain.ui.settings_dialog import SettingsDialog
from hyperbrain.ui.themes import theme_manager, ThemeType
from hyperbrain.core.config import get_config
from hyperbrain.core.brain import Brain
from hyperbrain.core.logger import get_logger
from hyperbrain.database.sqlite_manager import SQLiteManager

# spec fix-ollama-connection-debug: 结构化连接错误
# 顶层 import 以便 BrainWorker 捕获（理论上 main_window → ollama_model 单向，无循环）
try:
    from hyperbrain.models.ollama_model import OllamaConnectionError
except Exception:  # noqa: BLE001 防止 import 失败导致 main_window 整体不可用
    OllamaConnectionError = None  # type: ignore[assignment]

logger = get_logger(__name__)


class BrainWorker(QThread):
    """后台处理Brain消息的QThread工作线程

    使用QThread + pyqtSignal确保线程安全的UI更新。
    通过asyncio.run_coroutine_threadsafe在后台事件循环中执行brain.process()。

    spec fix-ollama-thinking-timeout:
    - timeout 默认从 config.model.worker_timeout 读取（180s）
    - error_occurred 支持结构化 dict（含 code/model/elapsed_sec/suggestion）
    - partial_chunk 支持流式输出
    """
    result_ready = pyqtSignal(str)      # 处理成功，返回内容
    error_occurred = pyqtSignal(object) # 处理失败：可传 str（兼容旧路径）或 dict {code, model, elapsed_sec, suggestion, trace}
    thinking_started = pyqtSignal()     # 开始思考
    cancelled = pyqtSignal()            # 请求已取消
    partial_chunk = pyqtSignal(str)     # 流式输出 chunk
    # spec show-thinking-process: 流式思维链片段
    # BrainWorker.run() 在拿到 thinking 文本后 emit，MainWindow._on_partial_thinking 接收
    partial_thinking = pyqtSignal(str)

    def __init__(self, brain, text: str, async_thread, timeout: float | None = None, model_name: str | None = None):
        super().__init__()
        self.brain = brain
        self.text = text
        self.async_thread = async_thread
        self.model_name = model_name or self._get_current_model_name(brain)
        # 解析 timeout：None → 从 config 读 → 兜底 180
        if timeout is None:
            try:
                timeout = float(getattr(brain.config.model, 'worker_timeout', 180.0) or 180.0)
            except Exception:
                timeout = 180.0
        if timeout < 30:
            timeout = 30.0
        if timeout > 600:
            timeout = 600.0
        self.timeout = timeout
        self._is_running = False
        self._future = None
        self._start_ts: float = 0.0

    @staticmethod
    def _get_current_model_name(brain) -> str:
        """从 brain 中提取当前模型名（best effort）"""
        try:
            if hasattr(brain, 'model_manager') and brain.model_manager is not None:
                sched = getattr(brain.model_manager, 'scheduler', None)
                if sched is not None and getattr(sched, 'current_model_name', None):
                    return str(sched.current_model_name)
                models = getattr(brain.model_manager, 'models', {}) or {}
                if 'ollama_default' in models:
                    return str(models['ollama_default'].model_name)
                for _, m in models.items():
                    if getattr(m, 'model_name', None):
                        return str(m.model_name)
            return str(getattr(brain.config.model, 'ollama_model', 'unknown'))
        except Exception:
            return 'unknown'

    def run(self):
        """在线程中执行消息处理"""
        self._is_running = True
        self.thinking_started.emit()
        self._start_ts = time.time()

        try:
            import asyncio
            import traceback
            logger.info(f"BrainWorker started processing: {self.text[:50]}...")

            # 在后台事件循环中提交brain.process协程
            logger.info("Submitting brain.process to async loop...")
            self._future = asyncio.run_coroutine_threadsafe(
                self.brain.process(self.text),
                self.async_thread.loop
            )
            logger.info("Future created, waiting for result...")

            # 等待结果（带超时）
            result = self._future.result(timeout=self.timeout)
            elapsed = time.time() - self._start_ts
            logger.info(f"Future result received: success={result.success if result else 'None'}, elapsed={elapsed:.1f}s")

            if not self._is_running:
                logger.info("Worker stopped, ignoring result")
                return

            if result.success:
                logger.info("Emitting result_ready signal")
                # spec show-thinking-process: 发送思维链片段
                # 任务7的 Brain.process() 会把 model_response.thinking 存到
                # result.metadata["thinking"]。这里采用简单方案：
                # 一次性 emit 完整 thinking（不做逐字流式），UI 端累积。
                # 若 metadata 没有 thinking（任务7未完成 / 非thinking模型），
                # 发送空字符串，UI 端会跳过折叠区。
                if result is not None:
                    try:
                        thinking_text = ""
                        meta = getattr(result, "metadata", None)
                        if isinstance(meta, dict):
                            thinking_text = str(meta.get("thinking", "") or "")
                    except Exception:
                        thinking_text = ""
                else:
                    thinking_text = ""
                if self._is_running and thinking_text:
                    self.partial_thinking.emit(thinking_text)
                self.result_ready.emit(str(result.content))
            else:
                logger.error(f"Brain processing failed: {result.error}")
                self.error_occurred.emit(f"处理失败：{result.error}")

        except asyncio.TimeoutError:
            elapsed = time.time() - self._start_ts
            logger.warning(f"Brain processing timed out after {elapsed:.1f}s (worker_timeout={self.timeout})")
            if self._future and not self._future.done():
                self._future.cancel()
            if self._is_running:
                # 结构化错误：code=MODEL_TIMEOUT 让 UI 走专门对话框
                self.error_occurred.emit({
                    "code": "MODEL_TIMEOUT",
                    "model": self.model_name,
                    "elapsed_sec": round(elapsed, 1),
                    "worker_timeout": self.timeout,
                    "suggestion": (
                        f"模型 {self.model_name} 在 {self.timeout} 秒内未响应。"
                        f"建议：1) 在设置中调高 worker_timeout；2) 切换到非 thinking 模型；"
                        f"3) 在 Ollama 设置中关闭 think；4) 配置 fallback_models 自动降级。"
                    ),
                    "trace": self._format_timeout_trace(),
                })
        except Exception as e:
            # spec fix-ollama-connection-debug: 结构化连接错误透传
            # 优先识别 OllamaConnectionError → emit OLLAMA_CONNECT_FAIL
            if OllamaConnectionError is not None and isinstance(e, OllamaConnectionError):
                elapsed_sec = time.time() - self._start_ts
                logger.error(
                    f"OLLAMA_CONNECT_FAIL stage={e.stage} model={e.model} "
                    f"url={e.url} detail={e.detail}"
                )
                payload = {
                    "code": "OLLAMA_CONNECT_FAIL",
                    "stage": e.stage,
                    "model": e.model or self.model_name,
                    "url": e.url,
                    "detail": e.detail,
                    "suggestion": e.suggestion,
                    "elapsed_sec": elapsed_sec,
                    "worker_timeout": self.timeout,
                }
                # 优先用 to_dict（已包含 code=OLLAMA_CONNECT_FAIL），
                # 补齐 elapsed/worker_timeout 字段。
                try:
                    d = e.to_dict()
                    if "code" not in d:
                        d["code"] = "OLLAMA_CONNECT_FAIL"
                    d.setdefault("elapsed_sec", elapsed_sec)
                    d.setdefault("worker_timeout", self.timeout)
                    payload = d
                except Exception:
                    pass
                if self._is_running:
                    self.error_occurred.emit(payload)
                return

            # 兜底：通用 BRAIN_ERROR
            elapsed = time.time() - self._start_ts
            logger.error(f"BrainWorker error after {elapsed:.1f}s: {e}")
            import traceback as _tb
            logger.error(_tb.format_exc())
            if self._is_running:
                self.error_occurred.emit({
                    "code": "BRAIN_ERROR",
                    "model": self.model_name,
                    "elapsed_sec": round(elapsed, 1),
                    "suggestion": f"内部错误：{e}",
                    "trace": _tb.format_exc().splitlines()[:5],
                })

    def _format_timeout_trace(self) -> list:
        try:
            import traceback
            return traceback.format_stack()[-5:]
        except Exception:
            return []

    def stop(self):
        """停止线程"""
        if self._future and not self._future.done():
            self._future.cancel()
        self._is_running = False
        self.wait(2000)  # 等待最多2秒


class MainWindow(QMainWindow):
    """
    Main application window for HyperBrain
    
    This window provides the primary interface with:
    - Session management on the left
    - Chat area in the center
    - Information panels on the right (monitor, memory, cognition)
    """

    def __init__(self, brain=None, async_thread=None):
        super().__init__()

        self.brain = brain
        self.async_thread = async_thread
        self.config = get_config().ui
        self.setWindowTitle("HyperBrain - 拟人脑认知架构系统")
        self.setGeometry(100, 100, self.config.window_width, self.config.window_height)
        self.setMinimumSize(1200, 800)

        # 当前工作线程（防止重复提交）
        self._current_worker: Optional[BrainWorker] = None

        # spec show-thinking-process: 思维链 UI 状态
        # _current_thinking_text 累积 partial_thinking 接收到的文本
        # _current_thinking_label / _current_thinking_detail 指向最近一次插入的
        # 折叠区控件（用于 _toggle_thinking 切换可见性）
        self._current_thinking_text: str = ""
        self._current_thinking_label: Optional[QLabel] = None
        self._current_thinking_detail: Optional[QTextEdit] = None

        # 数据库管理器
        self.db = SQLiteManager()

        # Initialize components
        self.chat_widget: Optional[ChatWidget] = None
        self.memory_viz: Optional[MemoryVisualizer] = None
        self.cognition_viz: Optional[CognitionVisualizer] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.session_manager: Optional[SessionManager] = None
        
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_dock_widgets()
        self._setup_statusbar()
        self._load_window_state()

        logger.info("MainWindow initialized")

    def _setup_toolbar(self):
        """设置工具栏 - 四个菜单布局"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # ===== 会话菜单 =====
        session_btn = QPushButton("会话")
        session_menu = QMenu(self)
        
        new_chat_action = QAction("新建", self)
        new_chat_action.setShortcut(QKeySequence("Ctrl+N"))
        new_chat_action.triggered.connect(self._new_chat)
        session_menu.addAction(new_chat_action)
        
        save_chat_action = QAction("保存", self)
        save_chat_action.setShortcut(QKeySequence("Ctrl+S"))
        save_chat_action.triggered.connect(self._save_chat)
        session_menu.addAction(save_chat_action)
        
        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self._clear_chat)
        session_menu.addAction(clear_action)
        
        session_btn.setMenu(session_menu)
        toolbar.addWidget(session_btn)
        
        # ===== 面板菜单 =====
        panel_btn = QPushButton("面板")
        panel_menu = QMenu(self)
        
        show_chat_action = QAction("聊天", self)
        show_chat_action.triggered.connect(lambda: self._show_widget("chat"))
        panel_menu.addAction(show_chat_action)
        
        show_memory_action = QAction("记忆", self)
        show_memory_action.triggered.connect(lambda: self._show_widget("memory"))
        panel_menu.addAction(show_memory_action)
        
        show_cognition_action = QAction("认知", self)
        show_cognition_action.triggered.connect(lambda: self._show_widget("cognition"))
        panel_menu.addAction(show_cognition_action)
        
        show_monitor_action = QAction("监控", self)
        show_monitor_action.triggered.connect(lambda: self._show_widget("monitor"))
        panel_menu.addAction(show_monitor_action)
        
        panel_btn.setMenu(panel_menu)
        toolbar.addWidget(panel_btn)
        
        # ===== 工具菜单 =====
        tools_btn = QPushButton("工具")
        tools_menu = QMenu(self)
        
        theme_action = QAction("主题", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self._toggle_theme)
        tools_menu.addAction(theme_action)
        
        settings_action = QAction("设置", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
        
        clear_memory_action = QAction("清理记忆", self)
        clear_memory_action.triggered.connect(self._clear_memory)
        tools_menu.addAction(clear_memory_action)

        diagnose_action = QAction("诊断 Ollama 连接", self)
        diagnose_action.setToolTip("运行 6 步分级诊断：进程/端口/API/模型/生成")
        diagnose_action.triggered.connect(self._show_diagnose_dialog)
        tools_menu.addAction(diagnose_action)

        tools_menu.addSeparator()  # 可选：与设置分组

        tools_btn.setMenu(tools_menu)
        toolbar.addWidget(tools_btn)
        
        # ===== 帮助菜单 =====
        help_btn = QPushButton("帮助")
        help_menu = QMenu(self)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        help_menu.addAction(exit_action)
        
        help_btn.setMenu(help_menu)
        toolbar.addWidget(help_btn)

    def _setup_central_widget(self):
        """设置中央部件"""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Session management panel
        self.session_manager = SessionManager()
        self.session_manager.setMinimumWidth(200)
        self.session_manager.setMaximumWidth(350)
        splitter.addWidget(self.session_manager)
        splitter.setStretchFactor(0, 0)

        # Middle: Chat area
        self.chat_widget = ChatWidget()
        self.chat_widget.brain = self.brain
        self.chat_widget.message_sent.connect(self._on_message_sent)
        self.chat_widget.set_stop_callback(self._stop_current_worker)
        splitter.addWidget(self.chat_widget)
        splitter.setStretchFactor(1, 1)

        # Right: Info panels (monitor, memory, cognition)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.info_tabs = QTabWidget()
        
        # Monitor tab
        self.system_monitor = SystemMonitor()
        if self.brain is not None:
            self.system_monitor.set_brain(self.brain)
        self.info_tabs.addTab(self.system_monitor, "监控")

        # Memory tab
        self.memory_viz = MemoryVisualizer()
        if self.brain is not None:
            self.memory_viz.brain = self.brain
        self.info_tabs.addTab(self.memory_viz, "记忆")

        # Cognition tab
        self.cognition_viz = CognitionVisualizer()
        if self.brain is not None:
            self.cognition_viz.set_brain(self.brain)
        self.info_tabs.addTab(self.cognition_viz, "认知")

        right_layout.addWidget(self.info_tabs)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter)

        # 标签页切换时立即刷新对应 viz
        self.info_tabs.currentChanged.connect(self._on_tab_changed)

        # Connect session manager signals
        self.session_manager.session_selected.connect(self._on_session_selected)
        self.session_manager.session_created.connect(self._on_session_created)
        self.session_manager.session_deleted.connect(self._on_session_deleted)

    def _setup_dock_widgets(self):
        """设置停靠窗口"""
        pass

    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Status label
        self.status_label = QLabel("HyperBrain 就绪")
        self.statusbar.addWidget(self.status_label)
        
        # Right-side info
        self.theme_label = QLabel(theme_manager.current_theme.value)
        self.statusbar.addPermanentWidget(self.theme_label)
        
        self.version_label = QLabel("v0.1.0")
        self.statusbar.addPermanentWidget(self.version_label)
        
        # Periodic status update
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)

    def _apply_theme(self):
        """应用当前主题"""
        stylesheet = theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

    def _on_theme_changed(self, theme: ThemeType):
        """
        Theme change callback
        
        Args:
            theme: New theme
        """
        self._apply_theme()
        self.theme_label.setText(theme.value)
        logger.info(f"Theme changed to {theme.value}")

    def _toggle_theme(self):
        """切换主题"""
        new_theme = theme_manager.toggle_theme()
        self._apply_theme()

    def _update_status(self):
        """更新状态栏 + 刷新所有 viz 组件（中央刷新器）"""
        self.status_label.setText("系统运行中...")

        # 刷新所有 viz（每个都包在 try-except 中防止单点失败影响全局）
        if hasattr(self, 'memory_viz') and self.memory_viz:
            try:
                self.memory_viz.refresh_data()
            except Exception as e:
                logger.debug(f"memory_viz refresh failed: {e}")

        if hasattr(self, 'cognition_viz') and self.cognition_viz:
            try:
                self.cognition_viz.refresh_data()
            except Exception as e:  # noqa: BLE001
                logger.debug(f"cognition_viz refresh failed: {e}")
        if hasattr(self, 'hermes_panel') and self.hermes_panel:
            try:
                self.hermes_panel.refresh_data()
            except Exception as e:  # noqa: BLE001
                logger.debug(f"hermes_panel refresh failed: {e}")

        if hasattr(self, 'system_monitor') and self.system_monitor:
            try:
                self.system_monitor.refresh_data(self.brain)
            except Exception as e:
                logger.debug(f"system_monitor refresh failed: {e}")

    def _on_tab_changed(self, index: int):
        """
        标签页切换时立即刷新该标签页对应的 viz

        Args:
            index: 当前标签页索引（0=监控, 1=记忆, 2=认知）
        """
        widget = self.info_tabs.widget(index) if hasattr(self, 'info_tabs') else None
        if widget and hasattr(widget, 'refresh_data'):
            try:
                widget.refresh_data()
            except Exception as e:
                logger.debug(f"tab refresh failed: {e}")

    def _new_chat(self):
        """新建对话"""
        if self.session_manager:
            self.session_manager._create_new_session()
        logger.info("New chat started")

    def _save_chat(self):
        """保存对话"""
        if self.chat_widget:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存对话",
                "",
                "JSON Files (*.json);;Text Files (*.txt)"
            )
            if file_path:
                self.chat_widget.save_conversation(file_path)
                logger.info(f"Chat saved to {file_path}")

    def _clear_chat(self):
        """清空聊天"""
        if self.chat_widget:
            self.chat_widget.clear_messages()
            logger.info("Chat cleared")

    def _clear_memory(self):
        """清理记忆"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理所有记忆数据吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear memory
            logger.info("Memory cleared")
            QMessageBox.information(self, "完成", "记忆数据已清理")

    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        # spec fix-test-model-revert: 连接保存成功信号以更新状态栏
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self, saved_fields: dict):
        """处理设置保存成功反馈（spec fix-test-model-revert）"""
        try:
            ollama = saved_fields.get("ollama_model", "?")
            provider = saved_fields.get("default_provider", "?")
            msg = f"已保存: {provider}/{ollama}"
            if hasattr(self, "status_label"):
                self.status_label.setText(msg)
            logger.info(f"Settings saved feedback: {msg}")
        except Exception as e:
            logger.error(f"_on_settings_saved failed: {e}")

    def _show_diagnose_dialog(self):
        """弹出 Ollama 连接诊断对话框（spec fix-ollama-connection-debug）"""
        try:
            from hyperbrain.ui.diagnose_dialog import DiagnoseDialog
            mm = getattr(self.brain, 'model_manager', None) if hasattr(self, 'brain') else None
            dlg = DiagnoseDialog(self, model_manager=mm)
            dlg.reconnected.connect(self._refresh_status_after_reconnect)
            dlg.exec()
        except Exception as e:
            logger.error(f"Show diagnose dialog failed: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "诊断失败", str(e))

    def _refresh_status_after_reconnect(self):
        """诊断对话框点 "重新尝试连接" 后刷新状态栏"""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.setText("已重新连接 Ollama")
        except Exception:
            pass

    def _on_settings_changed(self, settings: dict):
        """
        处理设置变更 - 重新注册模型到 ModelManager

        1) unregister 旧模型
        2) register 新模型
        3) 在状态栏显示更新反馈
        """
        try:
            if not self.brain or not hasattr(self.brain, 'model_manager'):
                logger.warning("No brain or model_manager available for settings change")
                return
            mm = self.brain.model_manager
            config = get_config().model

            # 导入 ModelConfig 和 ModelProvider
            from hyperbrain.models.base import ModelConfig, ModelProvider
            from hyperbrain.models.openai_model import OpenAIModel

            # OpenAI
            if config.openai_api_key:
                try:
                    mm.unregister_model("openai_default")
                except Exception:
                    pass
                mm.register_model(
                    name="openai_default",
                    config=ModelConfig(
                        model_name=config.openai_model,
                        provider=ModelProvider.OPENAI,
                        api_key=config.openai_api_key,
                        base_url=config.openai_base_url,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout=config.timeout,
                    ),
                    priority=8
                )
            # Anthropic
            if config.anthropic_api_key:
                try:
                    mm.unregister_model("anthropic_default")
                except Exception:
                    pass
                try:
                    from hyperbrain.models.anthropic_model import AnthropicModel
                    from hyperbrain.models.model_manager import _MODEL_CLASS_MAP
                    _MODEL_CLASS_MAP.setdefault(ModelProvider.ANTHROPIC, AnthropicModel)
                except Exception as e:
                    logger.debug(f"AnthropicModel import failed: {e}")
                mm.register_model(
                    name="anthropic_default",
                    config=ModelConfig(
                        model_name=config.anthropic_model,
                        provider=ModelProvider.ANTHROPIC,
                        api_key=config.anthropic_api_key,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout=config.timeout,
                    ),
                    priority=7
                )
            # Google
            if config.google_api_key:
                try:
                    mm.unregister_model("google_default")
                except Exception:
                    pass
                try:
                    from hyperbrain.models.google_model import GoogleModel
                    from hyperbrain.models.model_manager import _MODEL_CLASS_MAP
                    _MODEL_CLASS_MAP.setdefault(ModelProvider.GOOGLE, GoogleModel)
                except Exception as e:
                    logger.debug(f"GoogleModel import failed: {e}")
                mm.register_model(
                    name="google_default",
                    config=ModelConfig(
                        model_name=config.google_model,
                        provider=ModelProvider.GOOGLE,
                        api_key=config.google_api_key,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout=config.timeout,
                    ),
                    priority=6
                )
            # Ollama
            try:
                from hyperbrain.models.ollama_model import OllamaModel
                from hyperbrain.models.model_manager import _MODEL_CLASS_MAP
                _MODEL_CLASS_MAP.setdefault(ModelProvider.OLLAMA, OllamaModel)
            except Exception as e:
                logger.debug(f"OllamaModel import failed: {e}")
            if config.ollama_base_url:
                try:
                    mm.unregister_model("ollama_default")
                except Exception:
                    pass
                mm.register_model(
                    name="ollama_default",
                    config=ModelConfig(
                        model_name=config.ollama_model,
                        provider=ModelProvider.OLLAMA,
                        base_url=config.ollama_base_url,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout=config.timeout,
                    ),
                    priority=9
                )
            # 标记为已初始化，让 brain 能用
            if hasattr(mm, '_initialized'):
                mm._initialized = True

            provider_name = config.default_provider or "ollama"
            model_name = config.ollama_model if provider_name == "ollama" else \
                (config.openai_model if provider_name == "openai" else
                 (config.anthropic_model if provider_name == "anthropic" else config.google_model))
            logger.info(f"Models reloaded. Default: {provider_name}/{model_name}")
            if hasattr(self, 'status_label'):
                # 显示"设置已应用"反馈，3 秒后自动恢复为"系统运行中..."
                self.status_label.setText(f"设置已应用: {provider_name}/{model_name}")
                if hasattr(self, '_settings_clear_timer') and self._settings_clear_timer:
                    self._settings_clear_timer.stop()
                self._settings_clear_timer = QTimer()
                self._settings_clear_timer.setSingleShot(True)
                self._settings_clear_timer.timeout.connect(
                    lambda: self.status_label.setText("系统运行中...")
                )
                self._settings_clear_timer.start(3000)
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"设置应用失败: {e}")

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 HyperBrain",
            """HyperBrain - 拟人脑认知架构系统

版本: 0.1.0

一个基于认知科学原理构建的拟人脑系统，具备感知、记忆、认知、学习、进化、情感、执行和意识八大核心能力。

技术特性:
- 多层认知架构
- 向量记忆系统
- 多模态感知处理
- 持续学习能力
- 情感模拟引擎

© 2024 HyperBrain Project
"""
        )

    def _show_widget(self, widget_name: str):
        """
        Show specific widget in the info panel
        
        Args:
            widget_name: Name of widget to show
        """
        widget_map = {
            "chat": 0,
            "memory": 1,
            "cognition": 2,
            "monitor": 0
        }
        
        index = widget_map.get(widget_name, 0)
        self.info_tabs.setCurrentIndex(index)

    def _on_session_selected(self, session_id: str):
        """
        Handle session selection
        
        Args:
            session_id: ID of selected session
        """
        if self.chat_widget:
            self.chat_widget.load_session_messages(session_id)
        logger.info(f"Session selected: {session_id}")

    def _on_session_created(self, session_id: str):
        """
        Handle new session creation
        
        Args:
            session_id: ID of new session
        """
        if self.chat_widget:
            self.chat_widget.clear_messages()
        logger.info(f"Session created: {session_id}")

    def _on_session_deleted(self, session_id: str):
        """
        Handle session deletion
        
        Args:
            session_id: ID of deleted session
        """
        if self.chat_widget:
            self.chat_widget.clear_messages()
        logger.info(f"Session deleted: {session_id}")

    def _save_message_to_db(self, role: str, content: str):
        """保存消息到数据库"""
        try:
            session_id = self.session_manager.get_current_session_id()
            if not session_id:
                return
            
            import uuid
            from datetime import datetime
            self.db.execute(
                """INSERT INTO conversations (id, session_id, role, content, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), session_id, role, content, datetime.now().isoformat())
            )
            logger.debug(f"Message saved to DB: {role} - {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
    
    def _on_message_sent(self, text: str):
        """处理用户发送的消息"""
        logger.info(f"Message sent: {text[:50]}...")
        
        if not self.brain:
            logger.error("Brain not initialized")
            self.chat_widget.add_message("assistant", "错误：大脑未初始化")
            return
        
        if not self.async_thread:
            logger.error("Async thread not initialized")
            self.chat_widget.add_message("assistant", "错误：异步线程未初始化")
            return
        
        # 防止重复提交
        if self._current_worker and self._current_worker.isRunning():
            logger.warning("Previous worker still running")
            self.chat_widget.add_message("assistant", "请等待当前请求完成...")
            return
        
        # 保存用户消息到数据库
        self._save_message_to_db("user", text)
        
        try:
            # 获取超时配置（spec fix-ollama-thinking-timeout：worker_timeout 默认 180s）
            timeout = None
            try:
                timeout = getattr(self.brain.config.model, 'worker_timeout', None)
            except Exception:
                timeout = None
            logger.info(f"Creating BrainWorker with worker_timeout={timeout}")

            # 创建并启动工作线程
            self._current_worker = BrainWorker(
                brain=self.brain,
                text=text,
                async_thread=self.async_thread,
                timeout=float(timeout) if timeout else None,
            )

            # 连接信号到UI更新槽函数（自动在主线程执行）
            self._current_worker.result_ready.connect(self._handle_response)
            self._current_worker.error_occurred.connect(self._handle_error)
            self._current_worker.thinking_started.connect(self._show_thinking)
            self._current_worker.cancelled.connect(self._on_cancelled)
            self._current_worker.finished.connect(self._on_worker_finished)
            # spec show-thinking-process: 思维链流式片段
            self._current_worker.partial_thinking.connect(self._on_partial_thinking)

            # 重置思维链缓冲（防止上一轮残留）
            self._current_thinking_text = ""
            self._current_thinking_label = None
            self._current_thinking_detail = None

            logger.info("Starting BrainWorker...")
            self._current_worker.start()
            
            # 启用停止按钮
            self.chat_widget.stop_button.setEnabled(True)
            logger.info("BrainWorker started successfully")
            
        except Exception as e:
            logger.error(f"Error starting BrainWorker: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.chat_widget.add_message("assistant", f"启动失败：{str(e)}")
    
    def _show_thinking(self):
        """显示思考中提示"""
        logger.info("Showing thinking message")
        try:
            self.chat_widget.add_message("assistant", "思考中...")
            self.status_label.setText("正在处理...")
        except Exception as e:
            logger.error(f"Error showing thinking message: {e}")
    
    def _handle_response(self, text: str):
        """在主线程中安全地显示响应"""
        logger.info(f"Handling response: {text[:100]}...")
        try:
            # 移除"思考中..."提示（如果存在）
            self._remove_thinking_message()
            self.chat_widget.add_message("assistant", text)
            # spec show-thinking-process: 若缓冲中有 thinking 文本，给刚加入的
            # 气泡前面插入可折叠的"💭 思考过程"区
            if self._current_thinking_text:
                self._attach_thinking_to_last_bubble(self._current_thinking_text)
                # 消费完清空（避免下次误用）
                self._current_thinking_text = ""
            # 保存AI回复到数据库
            self._save_message_to_db("assistant", text)
            self.status_label.setText("HyperBrain 就绪")
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _on_partial_thinking(self, text: str):
        """处理流式思维链片段（spec show-thinking-process）

        BrainWorker 拿到 thinking 文本后会 emit partial_thinking(text)。
        简单方案：可能只发一次（一次性 emit 完整文本），但仍按"追加"语义
        实现，便于将来切到真正的流式逐字。
        """
        try:
            if not text:
                return
            self._current_thinking_text = (self._current_thinking_text or "") + text
            # 如果折叠区已经存在（例如流式逐字），即时更新提示和详情
            if self._current_thinking_label is not None:
                self._current_thinking_label.setText(
                    f"💭 思考过程 ({len(self._current_thinking_text)} 字符，点击展开)"
                )
            if self._current_thinking_detail is not None:
                self._current_thinking_detail.setPlainText(self._current_thinking_text)
        except Exception as e:
            logger.debug(f"_on_partial_thinking failed: {e}")

    def _toggle_thinking(self):
        """切换思维链折叠区显示（spec show-thinking-process）"""
        try:
            if self._current_thinking_detail is None:
                return
            self._current_thinking_detail.setVisible(
                not self._current_thinking_detail.isVisible()
            )
        except Exception as e:
            logger.debug(f"_toggle_thinking failed: {e}")

    def _attach_thinking_to_last_bubble(self, thinking_text: str):
        """在最后一条 AI 消息气泡的前面插入可折叠的思维链区。

        spec show-thinking-process:
        - 默认折叠（点击"💭 思考过程"标签展开）
        - 展开时淡灰色等宽字体 12px
        - 不修改 ChatWidget / MessageBubble（只新增同级 widget）
        """
        if not thinking_text or not self.chat_widget:
            return
        try:
            layout = self.chat_widget.messages_layout
            if layout is None:
                return
            # 折叠条（标签）—— 可点击切换
            label = QLabel(
                f"💭 思考过程 ({len(thinking_text)} 字符，点击展开)"
            )
            label.setStyleSheet(
                "color: #888888; font-size: 12px; padding: 4px; "
                "background: transparent; cursor: pointer;"
            )
            # 捕获 self._toggle_thinking（不带 args）
            label.mousePressEvent = lambda _evt: self._toggle_thinking()
            # 详细文本（默认隐藏）
            detail = QTextEdit()
            detail.setPlainText(thinking_text)
            detail.setReadOnly(True)
            detail.setStyleSheet(
                "color: #aaaaaa; background: #1e1e1e; "
                "font-family: Consolas, 'Courier New', monospace; "
                "font-size: 12px; border: 1px solid #333; padding: 8px;"
            )
            detail.setVisible(False)
            detail.setMaximumHeight(220)
            # 插入位置：刚加进去的 AI 气泡现在在 count-1
            # 之前。把它在布局中的索引取出来，把折叠区插在它前面
            # （insertWidget 会把该 index 上的 widget 往后挤一位）。
            bubble_index = layout.count() - 1
            if bubble_index < 0:
                return
            # 如果最后一项是 stretch（QVBoxLayout 默认有 stretch），
            # 那真正的最后一条气泡其实在 bubble_index - 1。
            last_item = layout.itemAt(bubble_index)
            if last_item is not None and last_item.widget() is None:
                bubble_index -= 1
            if bubble_index < 0:
                return
            layout.insertWidget(bubble_index, label)
            layout.insertWidget(bubble_index + 1, detail)
            self._current_thinking_label = label
            self._current_thinking_detail = detail
        except Exception as e:
            logger.debug(f"_attach_thinking_to_last_bubble failed: {e}")
    
    def _handle_error(self, error_payload):
        """在主线程中显示错误信息

        spec fix-ollama-thinking-timeout:
        - error_payload 可以是 str（兼容旧路径）或 dict {code, model, elapsed_sec, suggestion, trace}
        - code == "MODEL_TIMEOUT" 时调用 _show_timeout_dialog 显示可操作对话框
        """
        logger.error(f"Handling error: {error_payload}")
        try:
            self._remove_thinking_message()

            if isinstance(error_payload, dict):
                code = error_payload.get("code", "BRAIN_ERROR")
                model = error_payload.get("model", "未知模型")
                elapsed = error_payload.get("elapsed_sec", 0.0)
                suggestion = error_payload.get("suggestion", "")

                if code == "MODEL_TIMEOUT":
                    # 明确超时：弹专门对话框
                    self._show_timeout_dialog(error_payload)
                    self.status_label.setText(f"超时: {model} ({elapsed:.0f}s)")
                    return

                if code == "OLLAMA_CONNECT_FAIL":
                    # 结构化连接错误：弹专门对话框
                    self._show_connection_dialog(error_payload)
                    self.status_label.setText(f"连接失败: {error_payload.get('stage', '?')}")
                    return

                # 其他结构化错误：显示带 suggestion 的提示
                msg = f"{suggestion or code}"
                self.chat_widget.add_message("assistant", msg)
                self.status_label.setText(f"出错: {code}")
            else:
                # 兼容旧路径：直接显示字符串
                self.chat_widget.add_message("assistant", str(error_payload))
                self.status_label.setText("处理出错")
        except Exception as e:
            logger.error(f"Error handling error display: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _show_timeout_dialog(self, payload: dict):
        """弹出可操作的模型超时对话框

        三个按钮：
        1) 调高超时（→ 设置）—— 打开 settings_dialog 跳到 worker_timeout
        2) 切换到 fallback —— 读取 config.model.fallback_models[0]，set_active_model
        3) 关闭
        """
        try:
            model = payload.get("model", "未知")
            elapsed = payload.get("elapsed_sec", 0.0)
            worker_timeout = payload.get("worker_timeout", 0.0)
            suggestion = payload.get("suggestion", "")

            # 主文本
            main_text = (
                f"模型 <b>{model}</b> 在 <b>{worker_timeout:.0f} 秒</b>内未响应 "
                f"（实际等待 {elapsed:.0f} 秒）。<br><br>"
                f"<b>可能原因：</b><br>"
                f"• 该模型是 thinking 模型（如 qwen3、deepseek-r1、qwq），会先生成 800+ tokens 思维链<br>"
                f"• Ollama 端 CPU 推理较慢或显存不足<br><br>"
                f"<b>建议操作：</b><br>"
                f"• 在设置中把 worker_timeout 调到 180-300 秒<br>"
                f"• 关闭 think（Ollama 0.9+ 支持 <code>think: false</code>）<br>"
                f"• 切换到非 thinking 模型（如 gemma2:2b、qwen2.5:7b）<br>"
                f"• 在 fallback_models 中配置自动降级链"
            )

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("模型响应超时")
            box.setTextFormat(Qt.TextFormat.RichText)
            box.setText(f"<h3>⏱️ 模型响应超时</h3>")
            box.setInformativeText(main_text)

            # 按钮
            btn_settings = box.addButton("调高超时（→设置）", QMessageBox.ButtonRole.ActionRole)
            fallback_models = []
            try:
                fb = getattr(self.brain.config.model, 'fallback_models', None)
                if isinstance(fb, (list, tuple)) and fb:
                    fallback_models = list(fb)
            except Exception:
                pass

            btn_fallback = None
            if fallback_models:
                btn_fallback = box.addButton(
                    f"切换到 fallback ({fallback_models[0]})",
                    QMessageBox.ButtonRole.ActionRole,
                )
            btn_close = box.addButton("关闭", QMessageBox.ButtonRole.RejectRole)

            # 设置为非模态（不阻塞主线程）
            box.setWindowModality(Qt.WindowModality.NonModal)
            box.show()

            def on_settings():
                try:
                    self._show_settings()
                except Exception as e:
                    logger.error(f"Open settings from timeout dialog failed: {e}")

            def on_fallback():
                try:
                    target = fallback_models[0]
                    self._activate_fallback_model(target)
                except Exception as e:
                    logger.error(f"Switch to fallback failed: {e}")

            btn_settings.clicked.connect(on_settings)
            if btn_fallback is not None:
                btn_fallback.clicked.connect(on_fallback)
            btn_close.clicked.connect(box.close)

            # 显示在状态栏的简化版
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"⏱️ {model} 超时 ({elapsed:.0f}s)，点击查看建议")
        except Exception as e:
            logger.error(f"Show timeout dialog failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _show_connection_dialog(self, payload: dict):
        """弹出可操作的 Ollama 连接错误对话框（spec fix-ollama-connection-debug）

        复用 QMessageBox 风格，根据 stage 渲染针对性建议：
        - TCP_CONNECT → "Ollama 服务未运行或端口不通。运行 `ollama serve` 或检查防火墙"
        - HTTP_TAGS → "API 根路径异常，请检查 base_url"
        - HTTP_SHOW → "模型 X 不存在，请用 `ollama pull X` 拉取"
        - HTTP_CHAT → "模型推理失败，请检查模型是否损坏或切换到 gemma2:2b"
        - HTTP_CHAT_TIMEOUT → "请调高 worker_timeout 或切换到非 thinking 模型"
        """
        try:
            stage = payload.get("stage", "UNKNOWN")
            model = payload.get("model", "未知")
            url = payload.get("url", "?")
            detail = payload.get("detail", "")
            suggestion = payload.get("suggestion", "")

            # stage → 标题 + 主建议
            stage_titles = {
                "TCP_CONNECT": "🔌 Ollama 服务未连通",
                "HTTP_VERSION": "⚠️ Ollama API 根异常",
                "HTTP_TAGS": "📋 无法列出模型",
                "HTTP_SHOW": "🔍 模型不存在或损坏",
                "HTTP_CHAT": "💬 模型推理失败",
                "HTTP_CHAT_TIMEOUT": "⏱️ 模型响应超时",
            }
            stage_suggestions = {
                "TCP_CONNECT": "请检查：<br>"
                                "• Ollama 是否在运行？任务管理器中查找 <code>ollama.exe</code><br>"
                                "• 端口是否监听？命令行：<code>netstat -an | findstr 11434</code><br>"
                                "• Windows 防火墙是否拦截 11434？<br>"
                                "• 菜单 <b>工具 → 诊断 Ollama 连接</b> 可跑 6 步详细诊断",
                "HTTP_TAGS": f"无法访问 {url} 的 <code>/api/tags</code>。请检查：<br>"
                             f"• base_url 配置是否正确<br>"
                             f"• Ollama 是否在最新版本",
                "HTTP_SHOW": f"模型 <b>{model}</b> 不存在或已损坏。请：<br>"
                             f"• 运行 <code>ollama pull {model}</code> 重新拉取<br>"
                             f"• 或在设置中切换到 <code>gemma2:2b</code> 等其他模型",
                "HTTP_CHAT": f"模型 <b>{model}</b> 推理失败。请：<br>"
                             f"• 检查模型文件是否损坏<br>"
                             f"• 尝试 <code>ollama rm {model} && ollama pull {model}</code><br>"
                             f"• 切换到其他模型（如 gemma2:2b）",
                "HTTP_CHAT_TIMEOUT": f"模型 <b>{model}</b> 响应超时。请：<br>"
                                      f"• 在设置中把 worker_timeout 调到 180-300 秒<br>"
                                      f"• 关闭 think 或切换到非 thinking 模型<br>"
                                      f"• 检查 Ollama 端 CPU/显存负载",
            }
            title = stage_titles.get(stage, "❌ Ollama 连接错误")
            main_suggestion = stage_suggestions.get(stage, suggestion or "请检查 Ollama 服务状态")

            main_text = (
                f"<b>阶段:</b> {stage}<br>"
                f"<b>URL:</b> <code>{url}</code><br>"
                f"<b>模型:</b> {model}<br>"
                f"<b>详情:</b> {detail or '(无)'}<br><br>"
                f"<b>建议操作：</b><br>{main_suggestion}"
            )

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("Ollama 连接错误")
            box.setTextFormat(Qt.TextFormat.RichText)
            box.setText(f"<h3>{title}</h3>")
            box.setInformativeText(main_text)

            # 按钮
            btn_diagnose = box.addButton("运行诊断", QMessageBox.ButtonRole.ActionRole)
            btn_settings = box.addButton("打开设置", QMessageBox.ButtonRole.ActionRole)
            btn_close = box.addButton("关闭", QMessageBox.ButtonRole.RejectRole)

            # 非模态
            box.setWindowModality(Qt.WindowModality.NonModal)
            box.show()

            def on_diagnose():
                try:
                    self._show_diagnose_dialog()
                except Exception as ex:
                    logger.error(f"Diagnose from connection dialog failed: {ex}")

            def on_settings():
                try:
                    self._show_settings()
                except Exception as ex:
                    logger.error(f"Settings from connection dialog failed: {ex}")

            btn_diagnose.clicked.connect(on_diagnose)
            btn_settings.clicked.connect(on_settings)
            btn_close.clicked.connect(box.close)

            # 状态栏
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"❌ {stage}: {model}")
        except Exception as e:
            logger.error(f"Show connection dialog failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _activate_fallback_model(self, model_name: str):
        """切换主模型为 fallback 模型。

        - 从 config.model.fallback_models 找 model_name
        - 通过 model_manager 注册/激活该 ollama 模型
        - 状态栏提示
        """
        try:
            from hyperbrain.models.base import ModelConfig, ModelProvider
            mm = self.brain.model_manager
            try:
                mm.unregister_model("ollama_default")
            except Exception:
                pass
            cfg = ModelConfig(
                model_name=model_name,
                provider=ModelProvider.OLLAMA,
                base_url=self.brain.config.model.ollama_base_url,
                temperature=self.brain.config.model.temperature,
                max_tokens=self.brain.config.model.max_tokens,
                timeout=self.brain.config.model.timeout,
            )
            mm.register_model(name="ollama_default", config=cfg, priority=9)
            if hasattr(mm, '_initialized'):
                mm._initialized = True
            # 同步更新 config 中的 ollama_model
            try:
                self.brain.config.model.ollama_model = model_name
            except Exception:
                pass
            logger.info(f"Switched to fallback model: {model_name}")
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"已切换到 fallback: {model_name}")
        except Exception as e:
            logger.error(f"Activate fallback model failed: {e}")
    
    def _remove_thinking_message(self):
        """移除思考中提示消息"""
        # 遍历消息列表，找到最后一条内容为"思考中..."的 assistant 消息并移除
        for i in range(self.chat_widget.messages_layout.count() - 1, -1, -1):
            item = self.chat_widget.messages_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            if hasattr(widget, 'role') and widget.role == 'assistant':
                if hasattr(widget, 'raw_content') and widget.raw_content == '思考中...':
                    self.chat_widget.messages_layout.removeWidget(widget)
                    widget.deleteLater()
                    # 同时从历史记录中移除
                    for j in range(len(self.chat_widget.message_history) - 1, -1, -1):
                        msg = self.chat_widget.message_history[j]
                        if msg.get('role') == 'assistant' and msg.get('content') == '思考中...':
                            self.chat_widget.message_history.pop(j)
                            break
                    break
    
    def _on_worker_finished(self):
        """工作线程完成回调"""
        self._remove_thinking_message()
        self._current_worker = None
        self.chat_widget.stop_button.setEnabled(False)
        self.status_label.setText("HyperBrain 就绪")
    
    def _on_cancelled(self):
        """处理请求取消"""
        self._remove_thinking_message()
        self.chat_widget.add_message("assistant", "请求已取消")
        self.chat_widget.stop_button.setEnabled(False)
        self.status_label.setText("请求已取消")
    
    def _stop_current_worker(self):
        """停止当前工作线程"""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.stop()
            logger.info("Current worker stopped by user")

    def update_system_status(self, status: str):
        """
        Update system status display
        
        Args:
            status: Status text
        """
        self.status_label.setText(status)

    def _save_window_state(self):
        """Save window state"""
        state_file = Path("data/window_state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "geometry": {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height()
            },
            "theme": theme_manager.current_theme.value
        }
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save window state: {e}")

    def _load_window_state(self):
        """Load window state"""
        state_file = Path("data/window_state.json")
        
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                geometry = state.get("geometry", {})
                if geometry:
                    self.setGeometry(
                        geometry.get("x", 100),
                        geometry.get("y", 100),
                        geometry.get("width", 1400),
                        geometry.get("height", 900)
                    )
                
                theme = state.get("theme", "dark")
                if theme == "light":
                    theme_manager.set_theme(ThemeType.LIGHT)
                
            except Exception as e:
                logger.warning(f"Failed to load window state: {e}")

    def closeEvent(self, event):
        """
        Handle window close event
        
        Args:
            event: Close event
        """
        self._save_window_state()
        logger.info("MainWindow closed")
        event.accept()
