"""
启动界面

应用启动画面，显示加载进度和初始化状态
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QSplashScreen, QVBoxLayout, QWidget,
    QLabel, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QGradient, QLinearGradient

from hyperbrain.core.logger import get_logger

logger = get_logger("ui.splash")


class InitializationWorker(QThread):
    """
    初始化工作线程
    
    在后台执行系统初始化任务
    """
    
    progress_updated = pyqtSignal(int, str)
    initialization_complete = pyqtSignal(bool, str)
    
    def __init__(self, init_tasks: Optional[List] = None):
        super().__init__()
        self.init_tasks = init_tasks or []
        self._is_cancelled = False
    
    def run(self):
        """执行初始化任务"""
        try:
            total_tasks = len(self.init_tasks) if self.init_tasks else 5
            
            default_tasks = [
                ("正在加载配置...", self._load_config),
                ("正在初始化日志系统...", self._init_logging),
                ("正在连接数据库...", self._init_database),
                ("正在加载记忆系统...", self._init_memory),
                ("正在初始化模型...", self._init_models),
            ]
            
            tasks = self.init_tasks if self.init_tasks else default_tasks
            
            for i, (message, task_func) in enumerate(tasks):
                if self._is_cancelled:
                    self.initialization_complete.emit(False, "初始化已取消")
                    return
                
                progress = int((i / len(tasks)) * 100)
                self.progress_updated.emit(progress, message)
                
                try:
                    task_func()
                except Exception as e:
                    logger.warning(f"初始化任务 '{message}' 失败: {e}")
                
                self.msleep(300)
            
            self.progress_updated.emit(100, "初始化完成")
            self.initialization_complete.emit(True, "系统初始化成功")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.initialization_complete.emit(False, str(e))
    
    def _load_config(self):
        """加载配置"""
        from hyperbrain.core.config import get_config
        get_config()
    
    def _init_logging(self):
        """初始化日志"""
        from hyperbrain.core.logger import setup_logging
        setup_logging()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            from hyperbrain.database.sqlite_manager import SQLiteManager
            db = SQLiteManager()
            db.get_stats()
        except Exception:
            pass
    
    def _init_memory(self):
        """初始化记忆系统"""
        try:
            from hyperbrain.layers.memory.memory_manager import MemoryManager
            memory = MemoryManager()
            memory.get_stats()
        except Exception:
            pass
    
    def _init_models(self):
        """初始化模型"""
        pass
    
    def cancel(self):
        """取消初始化"""
        self._is_cancelled = True


class SplashScreen(QSplashScreen):
    """
    启动画面
    
    显示应用Logo、加载进度和初始化状态信息
    
    Signals:
        initialization_finished: 初始化完成信号，传递(bool成功, str消息)
    """
    
    initialization_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        # 创建启动画面背景
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        super().__init__(pixmap, Qt.WindowType.FramelessWindowHint)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._draw_background()
        
        self.worker: Optional[InitializationWorker] = None
        
        logger.info("SplashScreen initialized")
    
    def _setup_ui(self):
        """设置UI组件"""
        # 创建中央部件
        central = QWidget(self)
        central.setGeometry(0, 0, 600, 400)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        # 应用名称
        self.title_label = QLabel("HyperBrain")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #64b5f6;
            background: transparent;
        """)
        layout.addWidget(self.title_label)
        
        # 副标题
        self.subtitle_label = QLabel("拟人脑认知架构系统")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #a0a0a0;
            background: transparent;
        """)
        layout.addWidget(self.subtitle_label)
        
        layout.addStretch()
        
        # 版本信息
        self.version_label = QLabel("版本 0.1.0")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("""
            font-size: 12px;
            color: #757575;
            background: transparent;
        """)
        layout.addWidget(self.version_label)
        
        # 状态信息
        self.status_label = QLabel("正在启动...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 13px;
            color: #e0e0e0;
            background: transparent;
        """)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                color: #e0e0e0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196f3;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 版权信息
        self.copyright_label = QLabel("© 2024 HyperBrain Team")
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copyright_label.setStyleSheet("""
            font-size: 11px;
            color: #616161;
            background: transparent;
        """)
        layout.addWidget(self.copyright_label)
    
    def _draw_background(self):
        """绘制启动画面背景"""
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制渐变背景
        gradient = QLinearGradient(0, 0, 600, 400)
        gradient.setColorAt(0, QColor("#1a1a2e"))
        gradient.setColorAt(0.5, QColor("#16213e"))
        gradient.setColorAt(1, QColor("#0f3460"))
        
        painter.fillRect(0, 0, 600, 400, gradient)
        
        # 绘制装饰圆
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(100, 181, 246, 30))
        painter.drawEllipse(450, 50, 100, 100)
        painter.drawEllipse(50, 280, 80, 80)
        
        painter.end()
        
        self.setPixmap(pixmap)
    
    def start_initialization(self, tasks: Optional[List] = None):
        """
        开始初始化
        
        Args:
            tasks: 自定义初始化任务列表，格式为[(描述, 函数), ...]
        """
        self.worker = InitializationWorker(tasks)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.initialization_complete.connect(self._on_initialization_complete)
        self.worker.start()
    
    def _on_progress_updated(self, progress: int, message: str):
        """
        进度更新回调
        
        Args:
            progress: 进度百分比
            message: 状态消息
        """
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.repaint()
        QApplication.processEvents()
    
    def _on_initialization_complete(self, success: bool, message: str):
        """
        初始化完成回调
        
        Args:
            success: 是否成功
            message: 完成消息
        """
        if success:
            self.status_label.setText("启动完成")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"初始化失败: {message}")
            self.status_label.setStyleSheet("""
                font-size: 13px;
                color: #f44336;
                background: transparent;
            """)
        
        self.repaint()
        QApplication.processEvents()
        
        # 延迟后发射完成信号
        QTimer.singleShot(500, lambda: self.initialization_finished.emit(success, message))
    
    def mousePressEvent(self, event):
        """忽略鼠标点击事件"""
        pass
