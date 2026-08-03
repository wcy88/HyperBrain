# -*- mode: python ; coding: utf-8 -*-
"""
HyperBrain PyInstaller 打包配置文件

支持模式:
- 单文件模式: python -m PyInstaller hyperbrain.spec --onefile
- 单目录模式: python -m PyInstaller hyperbrain.spec --onedir (默认)

使用方法:
    python -m PyInstaller hyperbrain.spec
"""

import sys
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)
HYPERBRAIN_DIR = PROJECT_ROOT / "hyperbrain"

# 版本信息
VERSION = "0.2.0"
APP_NAME = "HyperBrain"
APP_DESCRIPTION = "拟人脑认知架构系统"

# 分析配置
a = Analysis(
    # 主入口脚本
    [str(HYPERBRAIN_DIR / "app.py")],
    
    # Python路径
    pathex=[
        str(PROJECT_ROOT),
        str(HYPERBRAIN_DIR),
    ],
    
    # 二进制文件
    binaries=[],
    
    # 数据文件
    datas=[
        # 配置文件
        ("requirements.txt", "."),
        (".env.example", "."),
        ("spec.md", "."),
        
        # 数据目录
        ("hyperbrain/data", "hyperbrain/data"),
        
        # 日志目录（创建空目录）
        ("hyperbrain/logs", "hyperbrain/logs"),
        
        # UI资源
        ("hyperbrain/ui", "hyperbrain/ui"),
    ],
    
    # 隐藏导入 - 动态导入的模块
    hiddenimports=[
        # 核心模块
        "hyperbrain.core.brain",
        "hyperbrain.core.config",
        "hyperbrain.core.logger",
        "hyperbrain.core.cache",
        "hyperbrain.core.error_handler",
        
        # 感知层
        "hyperbrain.layers.sensory.sensory_manager",
        "hyperbrain.layers.sensory.input_processor",
        "hyperbrain.layers.sensory.attention",
        "hyperbrain.layers.sensory.context_awareness",
        "hyperbrain.layers.sensory.multimodal_handler",
        "hyperbrain.layers.sensory.multimodal_input",
        "hyperbrain.layers.sensory.text_parser",
        
        # 记忆层
        "hyperbrain.layers.memory.memory_manager",
        "hyperbrain.layers.memory.memory_models",
        "hyperbrain.layers.memory.memory_utils",
        "hyperbrain.layers.memory.sensory_memory",
        "hyperbrain.layers.memory.short_term_memory",
        "hyperbrain.layers.memory.working_memory",
        "hyperbrain.layers.memory.long_term_memory",
        "hyperbrain.layers.memory.consolidation",
        "hyperbrain.layers.memory.retrieval",
        "hyperbrain.layers.memory.enhancement",
        "hyperbrain.layers.memory.forgetting",
        
        # 认知层
        "hyperbrain.layers.cognitive.cognitive_manager",
        "hyperbrain.layers.cognitive.reasoning",
        "hyperbrain.layers.cognitive.reasoning_engine",
        "hyperbrain.layers.cognitive.inference_chain",
        "hyperbrain.layers.cognitive.decision_making",
        "hyperbrain.layers.cognitive.planning",
        "hyperbrain.layers.cognitive.problem_solving",
        "hyperbrain.layers.cognitive.abstraction",
        "hyperbrain.layers.cognitive.metacognition",
        "hyperbrain.layers.cognitive.reflection_module",
        
        # 学习层
        "hyperbrain.layers.learning.learning_manager",
        "hyperbrain.layers.learning.infant_learning",
        "hyperbrain.layers.learning.child_learning",
        "hyperbrain.layers.learning.adult_learning",
        "hyperbrain.layers.learning.lifelong_learning",
        "hyperbrain.layers.learning.knowledge_acquisition",
        "hyperbrain.layers.learning.knowledge_integration",
        "hyperbrain.layers.learning.transfer_learning",
        "hyperbrain.layers.learning.skill_learner",
        "hyperbrain.layers.learning.feedback_processor",
        
        # 进化层
        "hyperbrain.layers.evolution.evolution_manager",
        "hyperbrain.layers.evolution.self_reflection",
        "hyperbrain.layers.evolution.error_analysis",
        "hyperbrain.layers.evolution.capability_assessment",
        "hyperbrain.layers.evolution.self_optimization",
        "hyperbrain.layers.evolution.self_optimizer",
        "hyperbrain.layers.evolution.goal_evolution",
        "hyperbrain.layers.evolution.architecture_evolution",
        "hyperbrain.layers.evolution.strategy_evolver",
        
        # 情感层
        "hyperbrain.layers.emotional.emotion_manager",
        "hyperbrain.layers.emotional.emotion_model",
        "hyperbrain.layers.emotional.emotion_engine",
        "hyperbrain.layers.emotional.emotion_generation",
        "hyperbrain.layers.emotional.emotion_expression",
        "hyperbrain.layers.emotional.emotion_memory",
        "hyperbrain.layers.emotional.emotion_regulation",
        "hyperbrain.layers.emotional.empathy",
        
        # 执行层
        "hyperbrain.layers.execution.execution_manager",
        "hyperbrain.layers.execution.task_execution",
        "hyperbrain.layers.execution.task_scheduler",
        "hyperbrain.layers.execution.action_executor",
        "hyperbrain.layers.execution.output_generation",
        "hyperbrain.layers.execution.progress_monitor",
        "hyperbrain.layers.execution.behavior_control",
        "hyperbrain.layers.execution.tool_invocation",
        
        # 意识层
        "hyperbrain.layers.consciousness.consciousness_manager",
        "hyperbrain.layers.consciousness.self_awareness",
        "hyperbrain.layers.consciousness.self_knowledge",
        "hyperbrain.layers.consciousness.will",
        "hyperbrain.layers.consciousness.value_system",
        "hyperbrain.layers.consciousness.goal_system",
        "hyperbrain.layers.consciousness.meta_cognition",
        
        # 模型层
        "hyperbrain.models.base",
        "hyperbrain.models.openai_model",
        "hyperbrain.models.anthropic_model",
        "hyperbrain.models.google_model",
        "hyperbrain.models.ollama_model",
        "hyperbrain.models.model_manager",
        "hyperbrain.models.scheduler",
        "hyperbrain.models.token_manager",
        "hyperbrain.models.capability_evaluator",
        "hyperbrain.models.error_handler",
        
        # 数据库
        "hyperbrain.database.sqlite_manager",
        "hyperbrain.database.vector_store",
        
        # UI
        "hyperbrain.ui.main_window",
        "hyperbrain.ui.chat_widget",
        "hyperbrain.ui.memory_viz",
        "hyperbrain.ui.cognition_viz",
        "hyperbrain.ui.system_monitor",
        "hyperbrain.ui.settings_dialog",
        "hyperbrain.ui.splash_screen",
        "hyperbrain.ui.themes",
        "hyperbrain.ui.ui_manager",
        
        # 工具
        "hyperbrain.utils.helpers",
        
        # 第三方库隐藏导入
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "pyqtgraph",
        "markdown",
        "pygments",
        "pygments.lexers",
        "pygments.formatters",
        "faiss",
        "numpy",
        "pandas",
        "openai",
        "anthropic",
        "google.generativeai",
        "requests",
        "aiohttp",
        "dotenv",
        "loguru",
        "pydantic",
        "pydantic_settings",
        "yaml",
        "sqlite3",
        "json",
        "asyncio",
    ],
    
    # 钩子运行时路径
    hookspath=[],
    
    # 钩子配置
    hooksconfig={},
    
    # 运行时钩子
    runtime_hooks=[],
    
    # 排除模块（减小体积）
    excludes=[
        # 测试相关
        "pytest",
        "pytest_asyncio",
        "pytest_qt",
        "_pytest",
        
        # 开发工具
        "IPython",
        "jupyter",
        "notebook",
        "matplotlib",
        "tkinter",
        
        # 不需要的GUI库
        "PySide6",
        "PyQt5",
        "PyQt4",
        
        # 其他
        "unittest",
        "pdb",
        "doctest",
    ],
    
    # 不跟踪这些模块的导入
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    
    # 加密密钥（可选）
    cipher=None,
    
    # 不收集这些二进制文件
    noarchive=False,
)

# 移除重复项
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    
    # 输出名称
    name=APP_NAME,
    
    # 单文件模式开关（通过命令行参数控制）
    # 默认单目录模式，更稳定
    debug=False,
    
    # 不显示控制台窗口（GUI模式）
    console=True,
    
    # 禁用窗口化跟踪
    disable_windowed_traceback=False,
    
    # 目标架构
    target_arch=None,
    
    # 代码签名（可选）
    codesign_identity=None,
    entitlements_file=None,
    
    # 图标
    icon=None,
    
    # 版本信息文件（Windows）
    version=None,
    
    # 单文件模式
    onefile=False,
)

# 收集所有内容
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
