"""
Qt兼容性层
提供PyQt5和PyQt6之间的兼容性
"""

# 尝试导入PyQt6，如果失败则回退到PyQt5
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QStatusBar, QMenuBar, QMenu,
        QToolBar, QLabel, QApplication, QDockWidget,
        QMessageBox, QFileDialog, QDialog, QPushButton,
        QLineEdit, QComboBox, QCheckBox, QGroupBox,
        QFormLayout, QGridLayout, QTabWidget, QTableWidget,
        QTableWidgetItem, QHeaderView, QTextEdit, QTextBrowser,
        QProgressBar, QSlider, QSpinBox, QDoubleSpinBox,
        QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
        QFrame, QScrollArea, QStackedWidget, QSizePolicy
    )
    from PyQt6.QtCore import (
        Qt, QTimer, pyqtSignal, QSize, QPoint, QRect,
        QThread, QMutex, QWaitCondition, QSettings,
        QPropertyAnimation, QEasingCurve, QObject, QEvent
    )
    from PyQt6.QtGui import (
        QAction, QKeySequence, QIcon, QFont, QColor,
        QPalette, QPixmap, QPainter, QPen, QBrush
    )
    from PyQt6.QtSvgWidgets import QSvgWidget
    from PyQt6 import uic

    QT_VERSION = 6

except ImportError:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QStatusBar, QMenuBar, QMenu,
        QToolBar, QLabel, QApplication, QDockWidget,
        QMessageBox, QFileDialog, QDialog, QPushButton,
        QLineEdit, QComboBox, QCheckBox, QGroupBox,
        QFormLayout, QGridLayout, QTabWidget, QTableWidget,
        QTableWidgetItem, QHeaderView, QTextEdit, QTextBrowser,
        QProgressBar, QSlider, QSpinBox, QDoubleSpinBox,
        QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
        QFrame, QScrollArea, QStackedWidget, QSizePolicy
    )
    from PyQt5.QtCore import (
        Qt, QTimer, pyqtSignal, QSize, QPoint, QRect,
        QThread, QMutex, QWaitCondition, QSettings,
        QPropertyAnimation, QEasingCurve, QObject, QEvent
    )
    from PyQt5.QtGui import (
        QAction, QKeySequence, QIcon, QFont, QColor,
        QPalette, QPixmap, QPainter, QPen, QBrush
    )
    from PyQt5.QtSvg import QSvgWidget
    from PyQt5 import uic

    QT_VERSION = 5

__all__ = [
    # Widgets
    'QMainWindow', 'QWidget', 'QVBoxLayout', 'QHBoxLayout',
    'QSplitter', 'QStatusBar', 'QMenuBar', 'QMenu',
    'QToolBar', 'QLabel', 'QApplication', 'QDockWidget',
    'QMessageBox', 'QFileDialog', 'QDialog', 'QPushButton',
    'QLineEdit', 'QComboBox', 'QCheckBox', 'QGroupBox',
    'QFormLayout', 'QGridLayout', 'QTabWidget', 'QTableWidget',
    'QTableWidgetItem', 'QHeaderView', 'QTextEdit', 'QTextBrowser',
    'QProgressBar', 'QSlider', 'QSpinBox', 'QDoubleSpinBox',
    'QListWidget', 'QListWidgetItem', 'QTreeWidget', 'QTreeWidgetItem',
    'QFrame', 'QScrollArea', 'QStackedWidget', 'QSizePolicy',
    # Core
    'Qt', 'QTimer', 'pyqtSignal', 'QSize', 'QPoint', 'QRect',
    'QThread', 'QMutex', 'QWaitCondition', 'QSettings',
    'QPropertyAnimation', 'QEasingCurve', 'QObject', 'QEvent',
    # Gui
    'QAction', 'QKeySequence', 'QIcon', 'QFont', 'QColor',
    'QPalette', 'QPixmap', 'QPainter', 'QPen', 'QBrush',
    # Svg
    'QSvgWidget',
    # Utils
    'uic',
    'QT_VERSION'
]