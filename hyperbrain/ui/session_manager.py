"""
会话管理面板

提供会话列表、新建、编辑、删除和继续历史会话功能
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QLabel, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from hyperbrain.core.logger import get_logger
from hyperbrain.database.sqlite_manager import SQLiteManager

logger = get_logger("ui.session_manager")


class SessionManager(QWidget):
    """
    会话管理面板

    功能：
    1. 显示会话列表
    2. 新建会话
    3. 继续历史会话
    4. 编辑会话名称
    5. 删除会话

    Signals:
        session_selected: 选择会话时触发
        session_created: 创建新会话时触发
        session_deleted: 删除会话时触发
    """

    session_selected = pyqtSignal(str)  # session_id
    session_created = pyqtSignal(str)   # session_id
    session_deleted = pyqtSignal(str)   # session_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = SQLiteManager()
        self._current_session_id: Optional[str] = None
        self._on_session_selected: Optional[Callable] = None

        self._setup_ui()
        self._load_sessions()

        logger.info("SessionManager initialized")

    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 标题
        title_label = QLabel("会话列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 新建会话按钮
        self.new_button = QPushButton("+ 新建会话")
        self.new_button.clicked.connect(self._create_new_session)
        layout.addWidget(self.new_button)

        # 会话列表
        self.session_list = QListWidget()
        self.session_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.session_list.itemClicked.connect(self._on_item_clicked)
        self.session_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.session_list, 1)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _load_sessions(self):
        """从数据库加载会话列表"""
        self.session_list.clear()

        try:
            sessions = self._get_all_sessions()
            for session in sessions:
                item = QListWidgetItem(session["name"])
                item.setData(Qt.ItemDataRole.UserRole, session["id"])
                item.setToolTip(f"最后活动: {session['updated_at']}\n消息数: {session['message_count']}")
                self.session_list.addItem(item)

            self.status_label.setText(f"共 {len(sessions)} 个会话")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.status_label.setText("加载失败")

    def _get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话"""
        try:
            # 检查表是否存在
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0
                )
            """)

            rows = self.db.execute(
                "SELECT id, name, created_at, updated_at, message_count FROM sessions ORDER BY updated_at DESC"
            )

            sessions = []
            for row in rows:
                sessions.append({
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4] or 0
                })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []

    def _create_new_session(self):
        """创建新会话"""
        session_id = str(uuid.uuid4())
        name = f"会话 {datetime.now().strftime('%m-%d %H:%M')}"

        try:
            self.db.execute("""
                INSERT INTO sessions (id, name, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, 0)
            """, (session_id, name, datetime.now().isoformat(), datetime.now().isoformat()))

            self._load_sessions()
            self._select_session(session_id)
            self.session_created.emit(session_id)
            logger.info(f"New session created: {session_id}")
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            QMessageBox.warning(self, "错误", f"创建会话失败: {e}")

    def _on_item_clicked(self, item: QListWidgetItem):
        """点击会话项"""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self._current_session_id = session_id
            self.session_selected.emit(session_id)
            logger.info(f"Session selected: {session_id}")

    def _select_session(self, session_id: str):
        """选中指定会话"""
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.session_list.setCurrentItem(item)
                self._current_session_id = session_id
                break

    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.session_list.itemAt(position)
        if not item:
            return

        session_id = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self._rename_session(session_id))
        menu.addAction(rename_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_session(session_id))
        menu.addAction(delete_action)

        menu.exec(self.session_list.mapToGlobal(position))

    def _rename_session(self, session_id: str):
        """重命名会话"""
        dialog = QDialog(self)
        dialog.setWindowTitle("重命名会话")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("输入新名称")
        layout.addWidget(name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_edit.text().strip()
            if new_name:
                try:
                    self.db.execute(
                        "UPDATE sessions SET name = ? WHERE id = ?",
                        (new_name, session_id)
                    )
                    self._load_sessions()
                    logger.info(f"Session renamed: {session_id} -> {new_name}")
                except Exception as e:
                    logger.error(f"Failed to rename session: {e}")
                    QMessageBox.warning(self, "错误", f"重命名失败: {e}")

    def _delete_session(self, session_id: str):
        """删除会话"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此会话吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                self.db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
                self._load_sessions()
                self.session_deleted.emit(session_id)
                logger.info(f"Session deleted: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session: {e}")
                QMessageBox.warning(self, "Error", f"Delete failed: {e}")

    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID"""
        return self._current_session_id

    def set_on_session_selected(self, callback: Callable):
        """设置会话选择回调"""
        self._on_session_selected = callback

    def update_session_message_count(self, session_id: str, count: int):
        """更新会话消息数"""
        try:
            self.db.execute(
                "UPDATE sessions SET message_count = ?, updated_at = ? WHERE id = ?",
                (count, datetime.now().isoformat(), session_id)
            )
        except Exception as e:
            logger.error(f"Failed to update message count: {e}")
