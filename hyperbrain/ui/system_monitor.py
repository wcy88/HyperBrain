"""
系统状态监控

显示系统运行状态、资源使用、能力水平、情感状态等
"""

import time
import psutil
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QGroupBox,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QHeaderView, QSplitter, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from hyperbrain.core.logger import get_logger
from hyperbrain.ui.themes import theme_manager

logger = get_logger("ui.monitor")


class SystemMonitor(QWidget):
    """
    系统状态监控组件
    
    功能：
    1. 系统运行状态显示
    2. 资源使用监控（CPU、内存）
    3. 能力水平仪表盘
    4. 情感状态显示
    5. 当前活动任务
    6. 实时日志显示
    
    Signals:
        status_updated: 状态更新时触发
    """
    
    status_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.brain = None  # 由 main_window 注入
        self._cpu_history: deque = deque(maxlen=60)
        self._memory_history: deque = deque(maxlen=60)
        self._log_messages: deque = deque(maxlen=100)
        self._tasks: List[Dict[str, Any]] = []

        self._setup_ui()
        self._setup_timers()

        logger.info("SystemMonitor initialized")

    def set_brain(self, brain):
        """设置 brain 引用（由 main_window 调用）"""
        self.brain = brain

    def refresh_data(self, brain=None):
        """
        刷新所有数据驱动的标签页

        从 brain.get_dashboard_data() 读取：
        - abilities → 能力标签页（9 个进度条）
        - emotion → 情感标签页
        - tasks → 任务标签页
        """
        b = brain or self.brain
        if not b:
            return
        try:
            data = b.get_dashboard_data()
        except Exception as e:
            logger.debug(f"system_monitor get_dashboard_data failed: {e}")
            return
        # 1. 能力（dashboard 返回 0-100，update_capabilities 期望 0-1）
        try:
            abilities = data.get("abilities", {})
            # 转换为 0-1 范围
            capabilities = {}
            for k, v in abilities.items():
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    fv = 0.0
                # 限制到 0-1
                capabilities[k] = max(0.0, min(1.0, fv / 100.0))
            self.update_capabilities(capabilities)
        except Exception as e:
            logger.debug(f"system_monitor update_capabilities failed: {e}")
        # 2. 情感
        try:
            emotion = data.get("emotion", {})
            intensity_raw = emotion.get("intensity", 0)
            try:
                intensity = float(intensity_raw)
            except (TypeError, ValueError):
                intensity = 0.0
            if intensity > 1.0:
                intensity = intensity / 100.0
            intensity = max(0.0, min(1.0, intensity))
            dimensions_raw = emotion.get("dimensions", {}) or {}
            dimensions = {}
            for dim_name in ("pleasure", "arousal", "dominance"):
                v = dimensions_raw.get(dim_name, 0)
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    fv = 0.0
                if abs(fv) > 1.0:
                    fv = fv / 100.0
                if dim_name == "pleasure":
                    fv = max(-1.0, min(1.0, fv))
                else:
                    fv = max(0.0, min(1.0, fv))
                dimensions[dim_name] = fv
            self.update_emotion(
                str(emotion.get("name", "平静") or "平静"),
                intensity,
                str(emotion.get("valence", "中性") or "中性"),
                dimensions
            )
        except Exception as e:
            logger.debug(f"system_monitor update_emotion failed: {e}")
        # 3. 任务
        try:
            tasks = data.get("tasks", []) or []
            normalized_tasks = []
            for t in tasks:
                if not isinstance(t, dict):
                    continue
                normalized_tasks.append({
                    "name": str(t.get("name", t.get("title", "未命名任务"))),
                    "type": str(t.get("type", t.get("category", ""))),
                    "status": str(t.get("status", "pending")),
                    "progress": int(t.get("progress", 0) or 0),
                    "start_time": str(t.get("start_time", t.get("created_at", "")))
                })
            self.update_tasks(normalized_tasks)
        except Exception as e:
            logger.debug(f"system_monitor update_tasks failed: {e}")
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 概览标签页
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "概览")
        
        # 资源标签页
        self.resources_tab = self._create_resources_tab()
        self.tab_widget.addTab(self.resources_tab, "资源")
        
        # 能力标签页
        self.capabilities_tab = self._create_capabilities_tab()
        self.tab_widget.addTab(self.capabilities_tab, "能力")
        
        # 情感标签页
        self.emotion_tab = self._create_emotion_tab()
        self.tab_widget.addTab(self.emotion_tab, "情感")
        
        # 任务标签页
        self.tasks_tab = self._create_tasks_tab()
        self.tab_widget.addTab(self.tasks_tab, "任务")
        
        # 日志标签页
        self.logs_tab = self._create_logs_tab()
        self.tab_widget.addTab(self.logs_tab, "日志")
        
        layout.addWidget(self.tab_widget)
    
    def _create_overview_tab(self) -> QWidget:
        """创建概览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 系统状态
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)
        
        self.system_status_label = QLabel("运行中")
        self.system_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50;")
        status_layout.addWidget(self.system_status_label)
        
        self.uptime_label = QLabel("运行时间: 00:00:00")
        status_layout.addWidget(self.uptime_label)
        
        self.last_update_label = QLabel("最后更新: --")
        status_layout.addWidget(self.last_update_label)
        
        layout.addWidget(status_group)
        
        # 快速统计
        stats_group = QGroupBox("快速统计")
        stats_layout = QHBoxLayout(stats_group)
        
        # CPU
        cpu_widget = QWidget()
        cpu_layout = QVBoxLayout(cpu_widget)
        self.cpu_quick_bar = QProgressBar()
        self.cpu_quick_bar.setRange(0, 100)
        cpu_layout.addWidget(QLabel("CPU"))
        cpu_layout.addWidget(self.cpu_quick_bar)
        stats_layout.addWidget(cpu_widget)
        
        # 内存
        mem_widget = QWidget()
        mem_layout = QVBoxLayout(mem_widget)
        self.memory_quick_bar = QProgressBar()
        self.memory_quick_bar.setRange(0, 100)
        mem_layout.addWidget(QLabel("内存"))
        mem_layout.addWidget(self.memory_quick_bar)
        stats_layout.addWidget(mem_widget)
        
        # 任务
        task_widget = QWidget()
        task_layout = QVBoxLayout(task_widget)
        self.task_quick_label = QLabel("0")
        self.task_quick_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        task_layout.addWidget(QLabel("活动任务"))
        task_layout.addWidget(self.task_quick_label)
        stats_layout.addWidget(task_widget)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget
    
    def _create_resources_tab(self) -> QWidget:
        """创建资源标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # CPU监控
        cpu_group = QGroupBox("CPU 使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_bar)
        
        self.cpu_detail_label = QLabel("核心数: -- | 频率: -- MHz")
        cpu_layout.addWidget(self.cpu_detail_label)
        
        layout.addWidget(cpu_group)
        
        # 内存监控
        mem_group = QGroupBox("内存 使用率")
        mem_layout = QVBoxLayout(mem_group)
        
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        mem_layout.addWidget(self.memory_bar)
        
        self.memory_detail_label = QLabel("已用: -- / 总计: --")
        mem_layout.addWidget(self.memory_detail_label)
        
        layout.addWidget(mem_group)
        
        # 磁盘监控
        disk_group = QGroupBox("磁盘 使用率")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_bar = QProgressBar()
        self.disk_bar.setRange(0, 100)
        disk_layout.addWidget(self.disk_bar)
        
        self.disk_detail_label = QLabel("已用: -- / 总计: --")
        disk_layout.addWidget(self.disk_detail_label)
        
        layout.addWidget(disk_group)
        
        # 网络监控
        net_group = QGroupBox("网络")
        net_layout = QVBoxLayout(net_group)
        
        self.net_sent_label = QLabel("发送: -- MB")
        net_layout.addWidget(self.net_sent_label)
        
        self.net_recv_label = QLabel("接收: -- MB")
        net_layout.addWidget(self.net_recv_label)
        
        layout.addWidget(net_group)
        layout.addStretch()
        
        return widget
    
    def _create_capabilities_tab(self) -> QWidget:
        """创建能力标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 认知能力
        cognitive_group = QGroupBox("认知能力")
        cognitive_layout = QFormLayout(cognitive_group)
        
        self.reasoning_bar = QProgressBar()
        self.reasoning_bar.setRange(0, 100)
        cognitive_layout.addRow("推理能力:", self.reasoning_bar)
        
        self.learning_bar = QProgressBar()
        self.learning_bar.setRange(0, 100)
        cognitive_layout.addRow("学习能力:", self.learning_bar)
        
        self.memory_bar_cap = QProgressBar()
        self.memory_bar_cap.setRange(0, 100)
        cognitive_layout.addRow("记忆能力:", self.memory_bar_cap)
        
        self.attention_bar = QProgressBar()
        self.attention_bar.setRange(0, 100)
        cognitive_layout.addRow("注意力:", self.attention_bar)
        
        layout.addWidget(cognitive_group)
        
        # 执行能力
        execution_group = QGroupBox("执行能力")
        execution_layout = QFormLayout(execution_group)
        
        self.planning_bar = QProgressBar()
        self.planning_bar.setRange(0, 100)
        execution_layout.addRow("规划能力:", self.planning_bar)
        
        self.problem_solving_bar = QProgressBar()
        self.problem_solving_bar.setRange(0, 100)
        execution_layout.addRow("问题解决:", self.problem_solving_bar)
        
        self.creativity_bar = QProgressBar()
        self.creativity_bar.setRange(0, 100)
        execution_layout.addRow("创造力:", self.creativity_bar)
        
        layout.addWidget(execution_group)
        
        # 社交能力
        social_group = QGroupBox("社交能力")
        social_layout = QFormLayout(social_group)
        
        self.empathy_bar = QProgressBar()
        self.empathy_bar.setRange(0, 100)
        social_layout.addRow("同理心:", self.empathy_bar)
        
        self.communication_bar = QProgressBar()
        self.communication_bar.setRange(0, 100)
        social_layout.addRow("沟通能力:", self.communication_bar)
        
        layout.addWidget(social_group)
        layout.addStretch()
        
        return widget
    
    def _create_emotion_tab(self) -> QWidget:
        """创建情感标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 当前情感
        current_group = QGroupBox("当前情感状态")
        current_layout = QFormLayout(current_group)
        
        self.current_emotion_label = QLabel("平静")
        self.current_emotion_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        current_layout.addRow("主要情感:", self.current_emotion_label)
        
        self.emotion_intensity_bar = QProgressBar()
        self.emotion_intensity_bar.setRange(0, 100)
        current_layout.addRow("强度:", self.emotion_intensity_bar)
        
        self.emotion_valence_label = QLabel("中性")
        current_layout.addRow("效价:", self.emotion_valence_label)
        
        layout.addWidget(current_group)
        
        # 情感维度
        dimensions_group = QGroupBox("情感维度")
        dimensions_layout = QFormLayout(dimensions_group)
        
        self.pleasure_bar = QProgressBar()
        self.pleasure_bar.setRange(-100, 100)
        dimensions_layout.addRow("愉悦度:", self.pleasure_bar)
        
        self.arousal_bar = QProgressBar()
        self.arousal_bar.setRange(0, 100)
        dimensions_layout.addRow("唤醒度:", self.arousal_bar)
        
        self.dominance_bar = QProgressBar()
        self.dominance_bar.setRange(0, 100)
        dimensions_layout.addRow("支配度:", self.dominance_bar)
        
        layout.addWidget(dimensions_group)
        
        # 情感历史
        history_group = QGroupBox("情感历史")
        history_layout = QVBoxLayout(history_group)
        
        self.emotion_history_table = QTableWidget()
        self.emotion_history_table.setColumnCount(4)
        self.emotion_history_table.setHorizontalHeaderLabels(["时间", "情感", "强度", "触发原因"])
        self.emotion_history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.emotion_history_table)
        
        layout.addWidget(history_group)
        layout.addStretch()
        
        return widget
    
    def _create_tasks_tab(self) -> QWidget:
        """创建任务标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 任务统计
        stats_layout = QHBoxLayout()
        
        self.active_tasks_label = QLabel("活动: 0")
        stats_layout.addWidget(self.active_tasks_label)
        
        self.completed_tasks_label = QLabel("完成: 0")
        stats_layout.addWidget(self.completed_tasks_label)
        
        self.failed_tasks_label = QLabel("失败: 0")
        stats_layout.addWidget(self.failed_tasks_label)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # 任务列表
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(["任务", "类型", "状态", "进度", "开始时间"])
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tasks_table)
        
        return widget
    
    def _create_logs_tab(self) -> QWidget:
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 日志级别过滤
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日志级别:"))
        
        self.log_level_combo = QTableWidget()
        self.log_level_combo.setColumnCount(2)
        self.log_level_combo.setHorizontalHeaderLabels(["级别", "数量"])
        filter_layout.addWidget(self.log_level_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)
        
        return widget
    
    def _setup_timers(self):
        """设置定时器"""
        # 资源监控定时器
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self._update_resources)
        self.resource_timer.start(2000)
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)
        
        self._start_time = time.time()
    
    def _update_resources(self):
        """更新资源信息"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self._cpu_history.append(cpu_percent)
            self.cpu_bar.setValue(int(cpu_percent))
            self.cpu_quick_bar.setValue(int(cpu_percent))
            
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            freq_str = f"{cpu_freq.current:.0f}" if cpu_freq else "--"
            self.cpu_detail_label.setText(f"核心数: {cpu_count} | 频率: {freq_str} MHz")
            
            # 内存
            memory = psutil.virtual_memory()
            self.memory_bar.setValue(int(memory.percent))
            self.memory_quick_bar.setValue(int(memory.percent))
            self.memory_detail_label.setText(
                f"已用: {memory.used // (1024**3)} GB / 总计: {memory.total // (1024**3)} GB"
            )
            
            # 磁盘
            disk = psutil.disk_usage('/')
            self.disk_bar.setValue(int(disk.percent))
            self.disk_detail_label.setText(
                f"已用: {disk.used // (1024**3)} GB / 总计: {disk.total // (1024**3)} GB"
            )
            
            # 网络
            net_io = psutil.net_io_counters()
            self.net_sent_label.setText(f"发送: {net_io.bytes_sent // (1024**2)} MB")
            self.net_recv_label.setText(f"接收: {net_io.bytes_recv // (1024**2)} MB")
            
        except Exception as e:
            logger.debug(f"Resource update failed: {e}")
    
    def _update_status(self):
        """更新状态信息"""
        # 运行时间
        uptime = int(time.time() - self._start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        seconds = uptime % 60
        self.uptime_label.setText(f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        self.last_update_label.setText(
            f"最后更新: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # 更新任务统计
        active = sum(1 for t in self._tasks if t.get("status") == "running")
        completed = sum(1 for t in self._tasks if t.get("status") == "completed")
        failed = sum(1 for t in self._tasks if t.get("status") == "failed")
        
        self.active_tasks_label.setText(f"活动: {active}")
        self.completed_tasks_label.setText(f"完成: {completed}")
        self.failed_tasks_label.setText(f"失败: {failed}")
        self.task_quick_label.setText(str(active))
    
    def update_capabilities(self, capabilities: Dict[str, float]):
        """
        更新能力水平

        Args:
            capabilities: 能力数据 {"reasoning": 0.8, ...} (0-1 范围)
        """
        # 标准化到 0-1 范围（防止外部传入超出范围的值）
        def _norm(v):
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return 0.0
            return max(0.0, min(1.0, fv))

        self.reasoning_bar.setValue(int(_norm(capabilities.get("reasoning", 0)) * 100))
        self.learning_bar.setValue(int(_norm(capabilities.get("learning", 0)) * 100))
        self.memory_bar_cap.setValue(int(_norm(capabilities.get("memory", 0)) * 100))
        self.attention_bar.setValue(int(_norm(capabilities.get("attention", 0)) * 100))
        self.planning_bar.setValue(int(_norm(capabilities.get("planning", 0)) * 100))
        self.problem_solving_bar.setValue(int(_norm(capabilities.get("problem_solving", 0)) * 100))
        self.creativity_bar.setValue(int(_norm(capabilities.get("creativity", 0)) * 100))
        self.empathy_bar.setValue(int(_norm(capabilities.get("empathy", 0)) * 100))
        self.communication_bar.setValue(int(_norm(capabilities.get("communication", 0)) * 100))

    def update_emotion(self, emotion: str, intensity: float,
                      valence: str, dimensions: Dict[str, float]):
        """
        更新情感状态

        Args:
            emotion: 情感名称
            intensity: 强度 (0-1)
            valence: 效价
            dimensions: 维度数据 {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.7}
        """
        def _norm(v, lo=0.0, hi=1.0):
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return lo
            return max(lo, min(hi, fv))

        self.current_emotion_label.setText(emotion)
        self.emotion_intensity_bar.setValue(int(_norm(intensity) * 100))
        self.emotion_valence_label.setText(valence)

        pleasure = _norm(dimensions.get("pleasure", 0), lo=-1.0, hi=1.0)
        self.pleasure_bar.setValue(int(pleasure * 100))

        arousal = _norm(dimensions.get("arousal", 0))
        self.arousal_bar.setValue(int(arousal * 100))

        dominance = _norm(dimensions.get("dominance", 0))
        self.dominance_bar.setValue(int(dominance * 100))
    
    def add_emotion_history(self, emotion: str, intensity: float, cause: str):
        """
        添加情感历史记录
        
        Args:
            emotion: 情感名称
            intensity: 强度
            cause: 触发原因
        """
        row = self.emotion_history_table.rowCount()
        self.emotion_history_table.insertRow(0)
        
        self.emotion_history_table.setItem(row, 0, QTableWidgetItem(
            datetime.now().strftime("%H:%M:%S")
        ))
        self.emotion_history_table.setItem(row, 1, QTableWidgetItem(emotion))
        self.emotion_history_table.setItem(row, 2, QTableWidgetItem(f"{intensity:.2f}"))
        self.emotion_history_table.setItem(row, 3, QTableWidgetItem(cause))
    
    def update_tasks(self, tasks: List[Dict[str, Any]]):
        """
        更新任务列表
        
        Args:
            tasks: 任务数据列表
        """
        self._tasks = tasks
        self.tasks_table.setRowCount(len(tasks))
        
        for i, task in enumerate(tasks):
            self.tasks_table.setItem(i, 0, QTableWidgetItem(task.get("name", "")))
            self.tasks_table.setItem(i, 1, QTableWidgetItem(task.get("type", "")))
            
            status = task.get("status", "")
            status_item = QTableWidgetItem(status)
            if status == "running":
                status_item.setForeground(QColor("#4caf50"))
            elif status == "failed":
                status_item.setForeground(QColor("#f44336"))
            self.tasks_table.setItem(i, 2, status_item)
            
            progress = task.get("progress", 0)
            progress_item = QTableWidgetItem(f"{progress}%")
            self.tasks_table.setItem(i, 3, progress_item)
            
            self.tasks_table.setItem(i, 4, QTableWidgetItem(
                task.get("start_time", "")
            ))
    
    def add_log_message(self, level: str, message: str, source: str = ""):
        """
        添加日志消息
        
        Args:
            level: 日志级别
            message: 消息内容
            source: 来源
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        level_colors = {
            "DEBUG": "#757575",
            "INFO": "#2196f3",
            "WARNING": "#ff9800",
            "ERROR": "#f44336",
            "CRITICAL": "#b71c1c"
        }
        
        color = level_colors.get(level, "#e0e0e0")
        
        log_entry = f'<span style="color: {color}">[{timestamp}] [{level}]'
        if source:
            log_entry += f' [{source}]'
        log_entry += f'</span> {message}<br>'
        
        self.log_text.append(log_entry)
        
        # 限制日志行数
        if self.log_text.document().blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def set_system_status(self, status: str, is_error: bool = False):
        """
        设置系统状态
        
        Args:
            status: 状态文本
            is_error: 是否为错误状态
        """
        self.system_status_label.setText(status)
        
        if is_error:
            self.system_status_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #f44336;"
            )
        else:
            self.system_status_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #4caf50;"
            )
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict: 状态数据
        """
        return {
            "cpu": list(self._cpu_history),
            "memory": list(self._memory_history),
            "uptime": int(time.time() - self._start_time),
            "tasks": len(self._tasks),
            "timestamp": datetime.now().isoformat()
        }
