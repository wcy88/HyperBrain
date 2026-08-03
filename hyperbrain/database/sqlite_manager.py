"""
SQLite 数据库管理器

管理结构化数据的存储
"""

import sqlite3
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from contextlib import contextmanager

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("database.sqlite")


class SQLiteManager:
    """
    SQLite 数据库管理器
    
    功能：
    1. 数据库连接管理
    2. 表结构管理
    3. CRUD 操作
    4. 事务支持
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config().memory
        self.db_path = db_path or self.config.db_path
        
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_tables()
        logger.info(f"SQLiteManager initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @contextmanager
    def get_connection(self):
        """公共连接获取接口（上下文管理器）

        spec L4: 暴露公共 API，避免外部模块访问私有 _get_connection。
        """
        with self._get_connection() as conn:
            yield conn
    
    def _init_tables(self):
        """初始化数据表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    importance REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # 对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # 系统事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # ========== Hermes 子系统表（追加，无侵入） ==========

            # 交互模式（用于 Skill 自动创建）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_key TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    response TEXT NOT NULL,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_patterns_intent
                ON interaction_patterns(intent_key, created_at)
            """)

            # 自动生成的 Skill 登记
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL UNIQUE,
                    file_path TEXT NOT NULL,
                    intent_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    error_log TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt_at TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Nudge 执行日志
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nudge_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_ms REAL,
                    success INTEGER DEFAULT 1,
                    error TEXT,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nudge_log_job
                ON nudge_log(job_name, started_at)
            """)

            # 轨迹表（采集）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    user_input TEXT NOT NULL,
                    model_response TEXT,
                    skills_invoked TEXT,
                    latency_ms REAL,
                    success INTEGER DEFAULT 1,
                    reward REAL,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trajectories_session
                ON trajectories(session_id, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trajectories_reward
                ON trajectories(reward)
            """)

            # 轨迹奖励
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trajectory_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trajectory_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    signals_json TEXT,
                    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trajectory_id) REFERENCES trajectories(id)
                )
            """)

            # 模型版本
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    version_id TEXT PRIMARY KEY,
                    base_model TEXT NOT NULL,
                    adapter_path TEXT,
                    dataset_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'queued',
                    promoted INTEGER DEFAULT 0,
                    eval_old_reward REAL,
                    eval_new_reward REAL,
                    eval_delta REAL,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_versions_promoted
                ON model_versions(promoted, created_at)
            """)

            # 显式反馈（保留接口，留空时评分读 0.5）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trajectory_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trajectory_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trajectory_id) REFERENCES trajectories(id)
                )
            """)

            conn.commit()
            logger.debug("Database tables initialized")
    
    def insert_memory(self, memory_id: str, content: str,
                     category: str = "general",
                     importance: float = 0.5,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        插入记忆
        
        Args:
            memory_id: 记忆ID
            content: 内容
            category: 分类
            importance: 重要性
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, content, category, importance, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (memory_id, content, category, importance, 
                      json.dumps(metadata) if metadata else None))
                return True
        except Exception as e:
            logger.error(f"Insert memory error: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取记忆"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM memories WHERE id = ?",
                    (memory_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Get memory error: {e}")
            return None
    
    def search_memories(self, query: str, 
                       category: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 查询关键词
            category: 分类过滤
            limit: 结果数量
            
        Returns:
            List[Dict]: 记忆列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute("""
                        SELECT * FROM memories 
                        WHERE content LIKE ? AND category = ?
                        ORDER BY importance DESC, created_at DESC
                        LIMIT ?
                    """, (f"%{query}%", category, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM memories 
                        WHERE content LIKE ?
                        ORDER BY importance DESC, created_at DESC
                        LIMIT ?
                    """, (f"%{query}%", limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Search memories error: {e}")
            return []
    
    def insert_conversation(self, conversation_id: str,
                           session_id: str,
                           role: str,
                           content: str,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """插入对话记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations 
                    (id, session_id, role, content, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, session_id, role, content,
                      json.dumps(metadata) if metadata else None))
                return True
        except Exception as e:
            logger.error(f"Insert conversation error: {e}")
            return False
    
    def get_conversation_history(self, 
                                session_id: str,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM conversations 
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (session_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Get conversation history error: {e}")
            return []
    
    def log_event(self, event_type: str, 
                 description: str,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """记录系统事件"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (event_type, description, metadata)
                    VALUES (?, ?, ?)
                """, (event_type, description,
                      json.dumps(metadata) if metadata else None))
                return True
        except Exception as e:
            logger.error(f"Log event error: {e}")
            return False
    
    def execute(self, sql: str, parameters: tuple = ()) -> List[Any]:
        """
        执行SQL语句并返回结果
        
        Args:
            sql: SQL语句
            parameters: SQL参数
            
        Returns:
            List[Any]: 查询结果列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, parameters)
                
                # 如果是SELECT语句，返回结果
                if sql.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                
                # 其他语句（INSERT/UPDATE/DELETE/CREATE等）提交并返回空列表
                conn.commit()
                return []
                
        except Exception as e:
            logger.error(f"Execute SQL error: {e}, SQL: {sql}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM memories")
                memory_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM conversations")
                conversation_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM events")
                event_count = cursor.fetchone()[0]
                
                return {
                    "memory_count": memory_count,
                    "conversation_count": conversation_count,
                    "event_count": event_count,
                    "db_path": self.db_path
                }
                
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {}
