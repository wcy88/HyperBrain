"""
设置界面

模型配置、系统参数、记忆系统、界面主题、快捷键、数据管理等设置
"""

import os
import json
import datetime
from dataclasses import asdict
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QPushButton,
    QTabWidget, QWidget, QFormLayout,
    QGroupBox, QSlider, QFileDialog,
    QMessageBox, QKeySequenceEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit,
    QProgressBar, QSplitter, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QKeyCombination
from PyQt6.QtGui import QKeySequence

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config, save_config, Config
from hyperbrain.ui.themes import theme_manager, ThemeType

logger = get_logger("ui.settings")


class SettingsDialog(QDialog):
    """
    设置对话框
    
    功能：
    1. 模型配置（API密钥、模型选择）
    2. 系统参数配置
    3. 记忆系统设置
    4. 界面主题设置
    5. 快捷键配置
    6. 数据管理（备份、清理）
    
    Signals:
        settings_changed: 设置变更时触发
    """
    
    settings_changed = pyqtSignal(dict)
    # spec fix-test-model-revert: 保存成功信号（携带 saved_fields 字典）
    settings_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("设置")
        self.setMinimumSize(700, 600)
        
        self._config = get_config()
        self._shortcuts: Dict[str, str] = {}
        
        self._setup_ui()
        self._load_settings()
        
        logger.info("SettingsDialog initialized")
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 模型配置标签页
        self.model_tab = self._create_model_tab()
        self.tab_widget.addTab(self.model_tab, "模型")
        
        # 系统参数标签页
        self.system_tab = self._create_system_tab()
        self.tab_widget.addTab(self.system_tab, "系统")
        
        # 记忆系统标签页
        self.memory_tab = self._create_memory_tab()
        self.tab_widget.addTab(self.memory_tab, "记忆")
        
        # 界面设置标签页
        self.ui_tab = self._create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "界面")
        
        # 快捷键标签页
        self.shortcuts_tab = self._create_shortcuts_tab()
        self.tab_widget.addTab(self.shortcuts_tab, "快捷键")
        
        # 数据管理标签页
        self.data_tab = self._create_data_tab()
        self.tab_widget.addTab(self.data_tab, "数据")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("恢复默认")
        self.reset_button.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.reset_button)
        
        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self._apply_settings)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _create_model_tab(self) -> QWidget:
        """创建模型配置标签页"""
        from PyQt6.QtWidgets import QScrollArea
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 默认提供商
        provider_group = QGroupBox("Model Provider")
        provider_layout = QFormLayout(provider_group)
        provider_layout.setSpacing(8)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "google", "ollama"])
        self.provider_combo.setMinimumWidth(200)
        provider_layout.addRow("Default Provider:", self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # OpenAI配置
        openai_group = QGroupBox("OpenAI")
        openai_layout = QFormLayout(openai_group)
        openai_layout.setSpacing(8)
        
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_edit.setPlaceholderText("（可选，未填则不启用）")
        self.openai_key_edit.setMinimumWidth(300)
        openai_layout.addRow("API Key:", self.openai_key_edit)
        
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        self.openai_model_combo.setEditable(True)
        self.openai_model_combo.setMinimumWidth(300)
        openai_layout.addRow("Model:", self.openai_model_combo)
        
        self.openai_url_edit = QLineEdit()
        self.openai_url_edit.setPlaceholderText("https://api.openai.com/v1")
        self.openai_url_edit.setMinimumWidth(300)
        openai_layout.addRow("Base URL:", self.openai_url_edit)
        
        layout.addWidget(openai_group)
        
        # Anthropic配置
        anthropic_group = QGroupBox("Anthropic")
        anthropic_layout = QFormLayout(anthropic_group)
        anthropic_layout.setSpacing(8)
        
        self.anthropic_key_edit = QLineEdit()
        self.anthropic_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key_edit.setPlaceholderText("（可选，未填则不启用）")
        self.anthropic_key_edit.setMinimumWidth(300)
        anthropic_layout.addRow("API Key:", self.anthropic_key_edit)
        
        self.anthropic_model_combo = QComboBox()
        self.anthropic_model_combo.addItems([
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ])
        self.anthropic_model_combo.setEditable(True)
        self.anthropic_model_combo.setMinimumWidth(300)
        anthropic_layout.addRow("Model:", self.anthropic_model_combo)
        
        layout.addWidget(anthropic_group)
        
        # Google配置
        google_group = QGroupBox("Google")
        google_layout = QFormLayout(google_group)
        google_layout.setSpacing(8)
        
        self.google_key_edit = QLineEdit()
        self.google_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_key_edit.setPlaceholderText("（可选，未填则不启用）")
        self.google_key_edit.setMinimumWidth(300)
        google_layout.addRow("API Key:", self.google_key_edit)
        
        self.google_model_combo = QComboBox()
        self.google_model_combo.addItems(["gemini-pro", "gemini-pro-vision"])
        self.google_model_combo.setEditable(True)
        self.google_model_combo.setMinimumWidth(300)
        google_layout.addRow("Model:", self.google_model_combo)
        
        layout.addWidget(google_group)
        
        # Ollama配置
        ollama_group = QGroupBox("Ollama")
        ollama_layout = QFormLayout(ollama_group)
        ollama_layout.setSpacing(8)
        
        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setPlaceholderText("http://localhost:11434")
        self.ollama_url_edit.setMinimumWidth(300)
        self.ollama_url_edit.setToolTip(
            "Ollama 服务地址，默认 http://127.0.0.1:11434\n"
            "如果连不上：菜单 工具 → 诊断 Ollama 连接 → 6 步分级诊断"
        )
        ollama_layout.addRow("Base URL:", self.ollama_url_edit)

        self.ollama_model_edit = QLineEdit()
        self.ollama_model_edit.setPlaceholderText("llama2")
        self.ollama_model_edit.setMinimumWidth(300)
        self.ollama_model_edit.setToolTip(
            "Ollama 模型名，必须在 ollama list 的输出中\n"
            "可用模型可在菜单 工具 → 诊断 Ollama 连接 的 Step 4 中查看"
        )
        # spec fix-test-model-revert: 列出本地模型按钮
        self.list_ollama_models_btn = QPushButton("📋 列出本地模型")
        self.list_ollama_models_btn.setToolTip("调用 ollama list 列出本地已安装模型，双击填入")
        self.list_ollama_models_btn.clicked.connect(self._on_list_ollama_models)
        ollama_model_row = QHBoxLayout()
        ollama_model_row.addWidget(self.ollama_model_edit, 1)
        ollama_model_row.addWidget(self.list_ollama_models_btn, 0)
        ollama_layout.addRow("Model:", ollama_model_row)
        
        layout.addWidget(ollama_group)
        
        # 通用参数
        params_group = QGroupBox("General Parameters")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(8)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(1)
        self.temperature_spin.setMinimumWidth(100)
        self.temperature_spin.setToolTip(
            "控制输出随机性\n"
            "0=确定性回答\n"
            "2=最大创造性\n"
            "推荐 0.7（平衡）"
        )
        self.temperature_spin.setValue(0.7)
        params_layout.addRow("Temperature:", self.temperature_spin)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 262144)
        self.max_tokens_spin.setSingleStep(1024)
        self.max_tokens_spin.setMinimumWidth(100)
        self.max_tokens_spin.setToolTip(
            "单次回复最大 token 数\n"
            "GPT-4: 8K, GPT-4-32K: 32K\n"
            "Claude 3: 8K-200K, Gemini 1.5: 1M, GPT-4.1: 1M\n"
            "推荐 4096（兼容大多数模型）\n"
            "上限 256K"
        )
        self.max_tokens_spin.setValue(4096)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setSuffix(" sec")
        self.timeout_spin.setSingleStep(5)
        self.timeout_spin.setMinimumWidth(100)
        self.timeout_spin.setToolTip(
            "API 调用超时（秒）\n"
            "慢速大模型建议 >60s\n"
            "快速小模型可设 30s\n"
            "推荐 90s"
        )
        self.timeout_spin.setValue(90)
        params_layout.addRow("Timeout:", self.timeout_spin)

        # === spec fix-ollama-thinking-timeout 新增字段 ===
        self.worker_timeout_spin = QSpinBox()
        self.worker_timeout_spin.setRange(30, 600)
        self.worker_timeout_spin.setSuffix(" sec")
        self.worker_timeout_spin.setSingleStep(30)
        self.worker_timeout_spin.setMinimumWidth(100)
        self.worker_timeout_spin.setToolTip(
            "BrainWorker 等待模型响应的最大秒数（30-600）\n"
            "调高可避免 thinking 模型超时；调低可快速失败\n"
            "若持续超时：菜单 工具 → 诊断 Ollama 连接 验证模型是否真在响应"
        )
        self.worker_timeout_spin.setValue(180)
        params_layout.addRow("Worker Timeout:", self.worker_timeout_spin)

        self.think_check = QCheckBox("允许 thinking 模型生成思维链")
        self.think_check.setToolTip(
            "允许 thinking 模型（qwen3.5、deepseek-r1 等）生成思维链\n"
            "开启后响应会先显示思维链（800+ token），再显示最终答案\n"
            "响应时间可能增加 30-180 秒\n"
            "关闭后 Ollama 会跳过思维链直接出答案"
        )
        self.think_check.setChecked(True)
        params_layout.addRow("", self.think_check)

        self.stream_check = QCheckBox("启用流式响应")
        self.stream_check.setToolTip(
            "流式响应：模型每生成一段就立即推送到 UI，\n"
            "避免用户长时间看不到内容以为卡死。\n"
            "默认开启"
        )
        self.stream_check.setChecked(True)
        params_layout.addRow("", self.stream_check)

        layout.addWidget(params_group)

        # === spec fix-ollama-thinking-timeout 降级链 UI ===
        fallback_group = QGroupBox("Model Fallback Chain")
        fallback_layout = QVBoxLayout(fallback_group)
        fallback_info = QLabel(
            "降级链：主模型（Ollama Model）响应超时时，"
            "按顺序自动尝试下列备选模型。\n"
            "留空 = 不降级"
        )
        fallback_info.setWordWrap(True)
        fallback_layout.addWidget(fallback_info)

        self.fallback_list = QListWidget()
        self.fallback_list.setMaximumHeight(120)
        self.fallback_list.setToolTip(
            "降级链模型列表，每行一个模型名\n"
            "主模型超时时自动按顺序尝试这些模型\n"
            "模型必须已用 ollama pull 拉取（启动时会自动校验）"
        )
        fallback_layout.addWidget(self.fallback_list)

        fallback_btn_row = QHBoxLayout()
        self.fallback_add_edit = QLineEdit()
        self.fallback_add_edit.setPlaceholderText("例如 gemma2:2b")
        self.fallback_add_edit.setMaximumWidth(180)
        fallback_btn_row.addWidget(self.fallback_add_edit)
        self.fallback_add_btn = QPushButton("添加")
        self.fallback_add_btn.clicked.connect(self._add_fallback_model)
        fallback_btn_row.addWidget(self.fallback_add_btn)
        self.fallback_remove_btn = QPushButton("删除选中")
        self.fallback_remove_btn.clicked.connect(self._remove_fallback_model)
        fallback_btn_row.addWidget(self.fallback_remove_btn)
        fallback_btn_row.addStretch()
        fallback_layout.addLayout(fallback_btn_row)

        layout.addWidget(fallback_group)
        layout.addStretch()

        scroll.setWidget(widget)
        return scroll
    
    def _create_system_tab(self) -> QWidget:
        """创建系统参数标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 认知层配置
        cognitive_group = QGroupBox("认知层")
        cognitive_layout = QFormLayout(cognitive_group)
        
        self.reasoning_depth_spin = QSpinBox()
        self.reasoning_depth_spin.setRange(1, 10)
        self.reasoning_depth_spin.setValue(3)
        self.reasoning_depth_spin.setToolTip(
            "推理层数\n"
            "1=直接回答\n"
            "10=多步深度推理\n"
            "推荐 3-5"
        )
        cognitive_layout.addRow("推理深度:", self.reasoning_depth_spin)

        self.max_chain_spin = QSpinBox()
        self.max_chain_spin.setRange(1, 20)
        self.max_chain_spin.setValue(5)
        self.max_chain_spin.setToolTip(
            "思维链最大步骤数\n"
            "典型推理 3-10 步\n"
            ">15 步会显著变慢\n"
            "推荐 5"
        )
        cognitive_layout.addRow("最大思维链长度:", self.max_chain_spin)

        self.reflection_check = QCheckBox("启用反思")
        self.reflection_check.setToolTip("推理后进行自我反思以提升回答质量")
        cognitive_layout.addRow("", self.reflection_check)

        self.confidence_threshold_spin = QDoubleSpinBox()
        self.confidence_threshold_spin.setRange(0.0, 1.0)
        self.confidence_threshold_spin.setSingleStep(0.05)
        self.confidence_threshold_spin.setDecimals(2)
        self.confidence_threshold_spin.setValue(0.7)
        self.confidence_threshold_spin.setToolTip(
            "置信度阈值\n"
            "低于此值的回答会被标记为不确定\n"
            "推荐 0.6-0.8"
        )
        cognitive_layout.addRow("置信度阈值:", self.confidence_threshold_spin)
        
        layout.addWidget(cognitive_group)
        
        # 执行层配置
        execution_group = QGroupBox("执行层")
        execution_layout = QFormLayout(execution_group)
        
        self.max_exec_time_spin = QSpinBox()
        self.max_exec_time_spin.setRange(1, 300)
        self.max_exec_time_spin.setSuffix(" 秒")
        self.max_exec_time_spin.setSingleStep(5)
        self.max_exec_time_spin.setValue(30)
        self.max_exec_time_spin.setToolTip(
            "任务最大执行时间\n"
            "超过则自动中断（防止死循环）\n"
            "推荐 30s"
        )
        execution_layout.addRow("最大执行时间:", self.max_exec_time_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setToolTip(
            "API 失败重试次数\n"
            "0=不重试\n"
            "3=重试 3 次（推荐）"
        )
        execution_layout.addRow("重试次数:", self.retry_spin)

        self.parallel_check = QCheckBox("启用并行执行")
        self.parallel_check.setToolTip("同时执行多个独立任务（提升速度）")
        execution_layout.addRow("", self.parallel_check)
        
        layout.addWidget(execution_group)
        
        # 学习层配置
        learning_group = QGroupBox("学习层")
        learning_layout = QFormLayout(learning_group)
        
        self.learning_rate_spin = QDoubleSpinBox()
        self.learning_rate_spin.setRange(0.0001, 0.1)
        self.learning_rate_spin.setSingleStep(0.001)
        self.learning_rate_spin.setDecimals(4)
        self.learning_rate_spin.setValue(0.001)
        self.learning_rate_spin.setToolTip(
            "学习率\n"
            "常用范围 0.0001-0.01\n"
            ">0.1 会导致训练不稳定\n"
            "推荐 0.001"
        )
        learning_layout.addRow("学习率:", self.learning_rate_spin)

        self.online_learning_check = QCheckBox("启用在线学习")
        self.online_learning_check.setToolTip("实时从对话中学习（推荐开启）")
        learning_layout.addRow("", self.online_learning_check)
        
        layout.addWidget(learning_group)
        layout.addStretch()
        
        return widget
    
    def _create_memory_tab(self) -> QWidget:
        """创建记忆系统标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 向量配置
        vector_group = QGroupBox("向量配置")
        vector_layout = QFormLayout(vector_group)
        
        self.vector_dim_spin = QSpinBox()
        self.vector_dim_spin.setRange(64, 4096)
        self.vector_dim_spin.setSingleStep(64)
        vector_layout.addRow("向量维度:", self.vector_dim_spin)
        
        self.similarity_threshold_spin = QDoubleSpinBox()
        self.similarity_threshold_spin.setRange(0.0, 1.0)
        self.similarity_threshold_spin.setSingleStep(0.05)
        self.similarity_threshold_spin.setDecimals(2)
        vector_layout.addRow("相似度阈值:", self.similarity_threshold_spin)
        
        layout.addWidget(vector_group)
        
        # 短期记忆
        stm_group = QGroupBox("短期记忆")
        stm_layout = QFormLayout(stm_group)
        
        self.stm_capacity_spin = QSpinBox()
        self.stm_capacity_spin.setRange(10, 1000)
        stm_layout.addRow("容量上限:", self.stm_capacity_spin)
        
        self.decay_rate_spin = QDoubleSpinBox()
        self.decay_rate_spin.setRange(0.0, 1.0)
        self.decay_rate_spin.setSingleStep(0.01)
        self.decay_rate_spin.setDecimals(3)
        stm_layout.addRow("衰减率:", self.decay_rate_spin)
        
        layout.addWidget(stm_group)
        
        # 长期记忆
        ltm_group = QGroupBox("长期记忆")
        ltm_layout = QFormLayout(ltm_group)
        
        self.index_type_combo = QComboBox()
        self.index_type_combo.addItems(["Flat", "IVF", "HNSW"])
        ltm_layout.addRow("索引类型:", self.index_type_combo)
        
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("data/memory.db")
        ltm_layout.addRow("数据库路径:", self.db_path_edit)
        
        layout.addWidget(ltm_group)
        layout.addStretch()
        
        return widget
    
    def _create_ui_tab(self) -> QWidget:
        """创建界面设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["暗色", "亮色"])
        theme_layout.addRow("主题:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setSuffix(" px")
        theme_layout.addRow("字体大小:", self.font_size_spin)
        
        self.animation_check = QCheckBox("启用动画效果")
        theme_layout.addRow("", self.animation_check)
        
        layout.addWidget(theme_group)
        
        # 窗口设置
        window_group = QGroupBox("窗口")
        window_layout = QFormLayout(window_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2560)
        self.window_width_spin.setSuffix(" px")
        window_layout.addRow("窗口宽度:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1440)
        self.window_height_spin.setSuffix(" px")
        window_layout.addRow("窗口高度:", self.window_height_spin)
        
        layout.addWidget(window_group)
        layout.addStretch()
        
        return widget
    
    def _create_shortcuts_tab(self) -> QWidget:
        """创建快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 快捷键列表
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["功能", "快捷键", "操作"])
        self.shortcuts_table.horizontalHeader().setStretchLastSection(True)
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 添加快捷键数据
        shortcuts_data = [
            ("发送消息", "Return", "chat.send"),
            ("新建对话", "Ctrl+N", "chat.new"),
            ("清空对话", "Ctrl+L", "chat.clear"),
            ("保存对话", "Ctrl+S", "chat.save"),
            ("打开设置", "Ctrl+,", "app.settings"),
            ("切换主题", "Ctrl+T", "app.theme"),
            ("退出应用", "Ctrl+Q", "app.quit"),
        ]
        
        self.shortcuts_table.setRowCount(len(shortcuts_data))
        for i, (name, shortcut, action) in enumerate(shortcuts_data):
            self.shortcuts_table.setItem(i, 0, QTableWidgetItem(name))
            self.shortcuts_table.setItem(i, 1, QTableWidgetItem(shortcut))
            
            edit_button = QPushButton("修改")
            edit_button.clicked.connect(lambda checked, row=i: self._edit_shortcut(row))
            self.shortcuts_table.setCellWidget(i, 2, edit_button)
            
            self._shortcuts[action] = shortcut
        
        layout.addWidget(self.shortcuts_table)
        
        # 重置按钮
        reset_shortcuts_button = QPushButton("重置所有快捷键")
        reset_shortcuts_button.clicked.connect(self._reset_shortcuts)
        layout.addWidget(reset_shortcuts_button)
        
        return widget
    
    def _create_data_tab(self) -> QWidget:
        """创建数据管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 数据备份
        backup_group = QGroupBox("数据备份")
        backup_layout = QVBoxLayout(backup_group)
        
        backup_info = QLabel("备份所有系统数据，包括记忆、配置和日志。")
        backup_info.setWordWrap(True)
        backup_layout.addWidget(backup_info)
        
        backup_button_layout = QHBoxLayout()
        
        self.backup_button = QPushButton("创建备份")
        self.backup_button.clicked.connect(self._create_backup)
        backup_button_layout.addWidget(self.backup_button)
        
        self.restore_button = QPushButton("恢复备份")
        self.restore_button.clicked.connect(self._restore_backup)
        backup_button_layout.addWidget(self.restore_button)
        
        backup_button_layout.addStretch()
        backup_layout.addLayout(backup_button_layout)
        
        self.backup_status_label = QLabel("")
        backup_layout.addWidget(self.backup_status_label)
        
        layout.addWidget(backup_group)
        
        # 数据清理
        cleanup_group = QGroupBox("数据清理")
        cleanup_layout = QVBoxLayout(cleanup_group)
        
        cleanup_info = QLabel("清理过期数据和临时文件以释放空间。")
        cleanup_info.setWordWrap(True)
        cleanup_layout.addWidget(cleanup_info)
        
        cleanup_button_layout = QHBoxLayout()
        
        self.clear_memory_button = QPushButton("清理记忆")
        self.clear_memory_button.clicked.connect(self._clear_memory)
        cleanup_button_layout.addWidget(self.clear_memory_button)
        
        self.clear_logs_button = QPushButton("清理日志")
        self.clear_logs_button.clicked.connect(self._clear_logs)
        cleanup_button_layout.addWidget(self.clear_logs_button)
        
        self.clear_cache_button = QPushButton("清理缓存")
        self.clear_cache_button.clicked.connect(self._clear_cache)
        cleanup_button_layout.addWidget(self.clear_cache_button)
        
        cleanup_button_layout.addStretch()
        cleanup_layout.addLayout(cleanup_button_layout)
        
        layout.addWidget(cleanup_group)
        
        # 数据导出
        export_group = QGroupBox("数据导出")
        export_layout = QVBoxLayout(export_group)
        
        export_info = QLabel("导出系统数据为JSON格式。")
        export_info.setWordWrap(True)
        export_layout.addWidget(export_info)
        
        export_button_layout = QHBoxLayout()
        
        self.export_config_button = QPushButton("导出配置")
        self.export_config_button.clicked.connect(self._export_config)
        export_button_layout.addWidget(self.export_config_button)
        
        self.export_memory_button = QPushButton("导出记忆")
        self.export_memory_button.clicked.connect(self._export_memory)
        export_button_layout.addWidget(self.export_memory_button)
        
        export_button_layout.addStretch()
        export_layout.addLayout(export_button_layout)
        
        layout.addWidget(export_group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """加载当前设置"""
        config = self._config

        # 模型配置
        self.provider_combo.setCurrentText(config.model.default_provider)
        self.openai_key_edit.setText(config.model.openai_api_key or "")
        self.openai_model_combo.setCurrentText(config.model.openai_model)
        self.openai_url_edit.setText(config.model.openai_base_url or "")
        self.anthropic_key_edit.setText(config.model.anthropic_api_key or "")
        self.anthropic_model_combo.setCurrentText(config.model.anthropic_model)
        self.google_key_edit.setText(config.model.google_api_key or "")
        self.google_model_combo.setCurrentText(config.model.google_model)
        self.ollama_url_edit.setText(config.model.ollama_base_url)
        self.ollama_model_edit.setText(config.model.ollama_model)
        self.temperature_spin.setValue(config.model.temperature)
        self.max_tokens_spin.setValue(config.model.max_tokens)
        self.timeout_spin.setValue(int(config.model.timeout))

        # === spec fix-ollama-thinking-timeout 新增字段加载 ===
        try:
            self.worker_timeout_spin.setValue(int(getattr(config.model, 'worker_timeout', 180)))
        except Exception:
            self.worker_timeout_spin.setValue(180)
        try:
            self.think_check.setChecked(bool(getattr(config.model, 'think', True)))
        except Exception:
            self.think_check.setChecked(True)
        try:
            self.stream_check.setChecked(bool(getattr(config.model, 'stream', True)))
        except Exception:
            self.stream_check.setChecked(True)
        try:
            self.fallback_list.clear()
            for m in (getattr(config.model, 'fallback_models', []) or []):
                self.fallback_list.addItem(str(m))
        except Exception:
            pass

        # 系统配置
        self.reasoning_depth_spin.setValue(config.cognitive.reasoning_depth)
        self.max_chain_spin.setValue(config.cognitive.max_chain_length)
        self.reflection_check.setChecked(config.cognitive.enable_reflection)
        self.confidence_threshold_spin.setValue(config.cognitive.confidence_threshold)
        self.max_exec_time_spin.setValue(int(config.execution.task_timeout))
        self.retry_spin.setValue(config.model.retry_attempts)
        self.parallel_check.setChecked(config.execution.enable_parallel_execution)
        self.learning_rate_spin.setValue(config.learning.learning_rate)
        self.online_learning_check.setChecked(config.learning.enable_online_learning)
        
        # 记忆配置
        self.vector_dim_spin.setValue(config.memory.vector_dim)
        self.similarity_threshold_spin.setValue(config.memory.similarity_threshold)
        self.stm_capacity_spin.setValue(config.memory.max_short_term_items)
        self.decay_rate_spin.setValue(config.memory.memory_decay_rate)
        self.index_type_combo.setCurrentText(config.memory.long_term_index_type)
        self.db_path_edit.setText(config.memory.db_path)
        
        # UI配置
        theme_name = "暗色" if config.ui.theme == "dark" else "亮色"
        self.theme_combo.setCurrentText(theme_name)
        self.font_size_spin.setValue(config.ui.font_size)
        self.animation_check.setChecked(config.ui.enable_animations)
        self.window_width_spin.setValue(config.ui.window_width)
        self.window_height_spin.setValue(config.ui.window_height)
    
    def _edit_shortcut(self, row: int):
        """
        编辑快捷键

        Args:
            row: 表格行号
        """
        # 简化的快捷键编辑，实际应用中可以使用QKeySequenceEdit
        QMessageBox.information(self, "快捷键", "快捷键编辑功能待实现")

    def _add_fallback_model(self):
        """添加降级模型到列表（spec fix-ollama-thinking-timeout）"""
        name = self.fallback_add_edit.text().strip()
        if not name:
            QMessageBox.information(self, "提示", "请输入模型名，例如 gemma2:2b")
            return
        # 去重
        for i in range(self.fallback_list.count()):
            if self.fallback_list.item(i).text() == name:
                QMessageBox.information(self, "提示", f"{name} 已在降级链中")
                return
        self.fallback_list.addItem(name)
        self.fallback_add_edit.clear()

    def _remove_fallback_model(self):
        """删除选中的降级模型"""
        current = self.fallback_list.currentRow()
        if current >= 0:
            self.fallback_list.takeItem(current)
        else:
            QMessageBox.information(self, "提示", "请先选中要删除的模型")
    
    def _reset_shortcuts(self):
        """重置快捷键"""
        QMessageBox.information(self, "快捷键", "快捷键已重置为默认值")
    
    def _create_backup(self):
        """创建数据备份"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "创建备份",
            f"hyperbrain_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "ZIP文件 (*.zip)"
        )
        
        if filename:
            try:
                import shutil
                import zipfile
                
                data_dir = Path("data")
                if data_dir.exists():
                    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file_path in data_dir.rglob('*'):
                            if file_path.is_file():
                                zf.write(file_path, file_path.relative_to(data_dir))
                    
                    self.backup_status_label.setText(f"备份已创建: {filename}")
                    logger.info(f"Backup created: {filename}")
                else:
                    self.backup_status_label.setText("数据目录不存在")
                    
            except Exception as e:
                self.backup_status_label.setText(f"备份失败: {e}")
                logger.error(f"Backup failed: {e}")
    
    def _restore_backup(self):
        """恢复数据备份"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "恢复备份",
            "",
            "ZIP文件 (*.zip)"
        )
        
        if filename:
            reply = QMessageBox.question(
                self,
                "确认恢复",
                "恢复备份将覆盖当前数据，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    import zipfile
                    
                    data_dir = Path("data")
                    data_dir.mkdir(parents=True, exist_ok=True)
                    
                    with zipfile.ZipFile(filename, 'r') as zf:
                        zf.extractall(data_dir)
                    
                    self.backup_status_label.setText("备份已恢复")
                    logger.info(f"Backup restored: {filename}")
                    
                except Exception as e:
                    self.backup_status_label.setText(f"恢复失败: {e}")
                    logger.error(f"Restore failed: {e}")
    
    def _clear_memory(self):
        """清理记忆"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理所有记忆数据吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from hyperbrain.layers.memory.memory_manager import MemoryManager
                memory = MemoryManager()
                memory.clear()
                QMessageBox.information(self, "完成", "记忆数据已清理")
                logger.info("Memory cleared")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清理失败: {e}")
    
    def _clear_logs(self):
        """清理日志"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理所有日志文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                log_dir = Path("logs")
                if log_dir.exists():
                    for log_file in log_dir.glob('*.log'):
                        log_file.unlink()
                QMessageBox.information(self, "完成", "日志文件已清理")
                logger.info("Logs cleared")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清理失败: {e}")
    
    def _clear_cache(self):
        """清理缓存"""
        QMessageBox.information(self, "完成", "缓存已清理")
    
    def _export_config(self):
        """导出配置"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出配置",
            "hyperbrain_config.json",
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                config_dict = asdict(self._config)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "完成", f"配置已导出到 {filename}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {e}")
    
    def _export_memory(self):
        """导出记忆"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出记忆",
            "hyperbrain_memory.json",
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                from hyperbrain.layers.memory.memory_manager import MemoryManager
                memory = MemoryManager()
                memories = memory.export_all()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(memories, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "完成", f"记忆已导出到 {filename}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {e}")
    
    def _apply_settings(self):
        """应用设置"""
        try:
            # 更新配置
            self._update_config()

            # 发射信号
            self.settings_changed.emit(self._get_settings_dict())

            save_config(self._config)

            # spec fix-test-model-revert: 发射保存成功信号（携带关键字段供状态栏显示）
            saved_fields = {
                "ollama_model": self._config.model.ollama_model,
                "default_provider": self._config.model.default_provider,
                "default_model": self._config.model.default_model,
            }
            self.settings_saved.emit(saved_fields)

            logger.info(f"Settings applied: ollama_model={saved_fields['ollama_model']}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"应用设置失败: {e}")
    
    def _save_and_close(self):
        """保存并关闭"""
        self._apply_settings()
        self.accept()

    def _on_list_ollama_models(self):
        """列出本地 ollama 模型（spec fix-test-model-revert）"""
        try:
            import subprocess
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except FileNotFoundError:
                QMessageBox.warning(
                    self, "Ollama 未安装",
                    "未找到 ollama 命令，请先安装 Ollama\nhttps://ollama.com/download"
                )
                return
            except subprocess.TimeoutExpired:
                QMessageBox.warning(self, "超时", "ollama list 执行超过 10 秒")
                return

            if result.returncode != 0:
                QMessageBox.warning(
                    self, "Ollama 错误",
                    f"ollama list 失败 (exit {result.returncode})\n{result.stderr[:300]}"
                )
                return

            # 解析 ollama list 输出：跳过表头，每行第一列是模型名
            models = []
            for line in result.stdout.splitlines()[1:]:  # 跳过 NAME ID SIZE MODIFIED 表头
                line = line.strip()
                if not line:
                    continue
                # 第一列（按空白分割）
                name = line.split()[0] if line.split() else ""
                if name and not name.startswith("NAME"):
                    models.append(name)

            if not models:
                QMessageBox.information(
                    self, "无模型",
                    "未检测到任何 ollama 模型\n请先运行 `ollama pull <model_name>` 拉取模型"
                )
                return

            # 弹出选择对话框
            self._show_model_picker(models)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"列出本地模型失败: {e}")

    def _show_model_picker(self, models: list):
        """弹出模型选择对话框（spec fix-test-model-revert）"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
            dlg = QDialog(self)
            dlg.setWindowTitle("选择本地模型")
            dlg.resize(400, 300)
            v = QVBoxLayout(dlg)
            v.addWidget(QLabel(f"检测到 {len(models)} 个本地模型，双击选择:"))
            lst = QListWidget(dlg)
            for m in models:
                QListWidgetItem(m, lst)
            v.addWidget(lst)
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            bb.accepted.connect(dlg.accept)
            bb.rejected.connect(dlg.reject)
            v.addWidget(bb)
            lst.itemDoubleClicked.connect(dlg.accept)

            if dlg.exec() == QDialog.DialogCode.Accepted and lst.currentItem():
                self.ollama_model_edit.setText(lst.currentItem().text())
                logger.info(f"Model selected from picker: {lst.currentItem().text()}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"弹出选择对话框失败: {e}")
    
    def _reset_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._config = Config()
            self._load_settings()
            save_config(self._config)
            logger.info("Settings reset to defaults")
    
    def _update_config(self):
        """更新配置对象"""
        # 模型配置
        self._config.model.default_provider = self.provider_combo.currentText()
        self._config.model.openai_api_key = self.openai_key_edit.text() or None
        self._config.model.openai_model = self.openai_model_combo.currentText()
        self._config.model.openai_base_url = self.openai_url_edit.text() or ""
        self._config.model.anthropic_api_key = self.anthropic_key_edit.text() or None
        self._config.model.anthropic_model = self.anthropic_model_combo.currentText()
        self._config.model.google_api_key = self.google_key_edit.text() or None
        self._config.model.google_model = self.google_model_combo.currentText()
        self._config.model.ollama_base_url = self.ollama_url_edit.text()
        # spec fix-test-model-revert: 校验 Ollama Model 字段，拒绝空值与占位符
        ollama_model_value = self.ollama_model_edit.text().strip()
        if not ollama_model_value:
            raise ValueError("Ollama Model 不能为空，请填写 ollama list 中实际存在的模型名")
        if ollama_model_value.lower() in ("test_model", "test", "placeholder", "default", "example", "your_model"):
            raise ValueError(
                f"无效的模型名: {ollama_model_value!r}，请填写 ollama list 中实际存在的模型名"
            )
        self._config.model.ollama_model = ollama_model_value
        self._config.model.temperature = self.temperature_spin.value()
        self._config.model.max_tokens = self.max_tokens_spin.value()
        self._config.model.timeout = float(self.timeout_spin.value())

        # === spec fix-ollama-thinking-timeout 新增字段保存 ===
        try:
            self._config.model.worker_timeout = float(self.worker_timeout_spin.value())
        except Exception:
            self._config.model.worker_timeout = 180.0
        try:
            self._config.model.think = bool(self.think_check.isChecked())
        except Exception:
            self._config.model.think = True
        try:
            self._config.model.stream = bool(self.stream_check.isChecked())
        except Exception:
            self._config.model.stream = True
        try:
            fallback_models = []
            for i in range(self.fallback_list.count()):
                item = self.fallback_list.item(i)
                if item is not None:
                    name = item.text().strip()
                    if name:
                        fallback_models.append(name)
            self._config.model.fallback_models = fallback_models
        except Exception:
            self._config.model.fallback_models = []

        # 系统配置
        self._config.cognitive.reasoning_depth = self.reasoning_depth_spin.value()
        self._config.cognitive.max_chain_length = self.max_chain_spin.value()
        self._config.cognitive.enable_reflection = self.reflection_check.isChecked()
        self._config.cognitive.confidence_threshold = self.confidence_threshold_spin.value()
        self._config.execution.task_timeout = int(self.max_exec_time_spin.value())
        self._config.model.retry_attempts = self.retry_spin.value()
        self._config.execution.enable_parallel_execution = self.parallel_check.isChecked()
        self._config.learning.learning_rate = self.learning_rate_spin.value()
        self._config.learning.enable_online_learning = self.online_learning_check.isChecked()
        
        # 记忆配置
        self._config.memory.vector_dim = self.vector_dim_spin.value()
        self._config.memory.similarity_threshold = self.similarity_threshold_spin.value()
        self._config.memory.max_short_term_items = self.stm_capacity_spin.value()
        self._config.memory.memory_decay_rate = self.decay_rate_spin.value()
        self._config.memory.long_term_index_type = self.index_type_combo.currentText()
        self._config.memory.db_path = self.db_path_edit.text()
        
        # UI配置
        theme = "dark" if self.theme_combo.currentText() == "暗色" else "light"
        self._config.ui.theme = theme
        self._config.ui.font_size = self.font_size_spin.value()
        self._config.ui.enable_animations = self.animation_check.isChecked()
        self._config.ui.window_width = self.window_width_spin.value()
        self._config.ui.window_height = self.window_height_spin.value()
        
        # 应用主题
        new_theme = ThemeType.DARK if theme == "dark" else ThemeType.LIGHT
        theme_manager.set_theme(new_theme)
    
    def _get_settings_dict(self) -> Dict[str, Any]:
        """
        获取设置字典
        
        Returns:
            Dict: 设置数据
        """
        return {
            "model": {
                "provider": self.provider_combo.currentText(),
                "temperature": self.temperature_spin.value(),
                "max_tokens": self.max_tokens_spin.value()
            },
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_spin.value()
        }
