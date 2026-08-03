"""
长期记忆模块 (Long-Term Memory)

模拟人脑的长期记忆系统：
- 陈述性记忆：事实、概念、事件
- 程序性记忆：技能、习惯、行为模式
- 情感记忆：与情感相关的经历
- 使用SQLite存储结构化数据
- 使用FAISS存储向量嵌入
- 支持记忆的重要性评分

长期记忆是信息持久化存储的核心，容量理论上无限。
"""

import json
import sqlite3
import pickle
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config
from hyperbrain.layers.memory.memory_models import (
    MemoryItem, MemoryType, MemoryStatus, EmotionalTag
)
from hyperbrain.layers.memory.memory_utils import cosine_similarity, normalize_vector

logger = get_logger("memory.long_term")


class LongTermMemory:
    """
    长期记忆系统
    
    功能：
    - 陈述性记忆（事实、概念）
    - 程序性记忆（技能、习惯）
    - 情感记忆
    - SQLite结构化存储
    - FAISS向量索引（可选）
    - 记忆关联管理
    
    Attributes:
        db_path: SQLite数据库路径
        vector_dim: 向量维度
        enable_faiss: 是否启用FAISS
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        vector_dim: int = 1536,
        enable_faiss: bool = False
    ):
        self.config = get_config().memory
        self.db_path = db_path or self.config.db_path
        self.vector_dim = vector_dim
        self.enable_faiss = enable_faiss
        
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
        self._faiss_index = None
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: Dict[int, str] = {}
        
        # 初始化数据库
        self._init_database()
        
        # 初始化FAISS（如果可用）
        if enable_faiss:
            self._init_faiss()
        
        logger.info(
            f"LongTermMemory initialized: db={self.db_path}, "
            f"vector_dim={vector_dim}, faiss={enable_faiss}"
        )
    
    def _init_database(self) -> None:
        """初始化SQLite数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 主记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT DEFAULT 'declarative',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    importance REAL DEFAULT 0.5,
                    confidence REAL DEFAULT 0.8,
                    familiarity REAL DEFAULT 0.0,
                    access_count INTEGER DEFAULT 0,
                    repetition_count INTEGER DEFAULT 0,
                    embedding BLOB,
                    embedding_dim INTEGER DEFAULT 0,
                    emotional_tag TEXT,
                    associations TEXT DEFAULT '[]',
                    context_tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    decay_factor REAL DEFAULT 1.0,
                    next_review TIMESTAMP,
                    forgetting_curve_stage INTEGER DEFAULT 0
                )
            """)
            
            # 记忆关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    association_type TEXT DEFAULT 'related',
                    strength REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_id, target_id)
                )
            """)
            
            # 索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type 
                ON long_term_memories(memory_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance 
                ON long_term_memories(importance DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON long_term_memories(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed 
                ON long_term_memories(last_accessed)
            """)
            
            conn.commit()
            logger.debug("Database tables initialized")
    
    def _init_faiss(self) -> None:
        """初始化FAISS索引"""
        try:
            import faiss
            self._faiss_index = faiss.IndexFlatIP(self.vector_dim)
            logger.info("FAISS index initialized")
        except ImportError:
            logger.warning("FAISS not available, falling back to brute force search")
            self.enable_faiss = False
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
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
    
    def store(
        self,
        content: Union[str, Dict[str, Any]],
        memory_type: MemoryType = MemoryType.DECLARATIVE,
        importance: float = 0.5,
        confidence: float = 0.8,
        embedding: Optional[np.ndarray] = None,
        emotional_tag: Optional[EmotionalTag] = None,
        associations: Optional[List[str]] = None,
        context_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryItem:
        """
        存储记忆到长期记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性 [0, 1]
            confidence: 置信度 [0, 1]
            embedding: 向量嵌入
            emotional_tag: 情感标签
            associations: 关联记忆ID
            context_tags: 上下文标签
            metadata: 元数据
            
        Returns:
            MemoryItem: 存储的记忆条目
        """
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            emotional_tag=emotional_tag.to_dict() if emotional_tag else None,
            associations=associations or [],
            context_tags=context_tags or [],
            metadata=metadata or {}
        )
        
        if embedding is not None:
            item.set_embedding(embedding)
        
        with self._lock:
            self._insert_to_db(item)
            
            # 添加到FAISS索引
            if self.enable_faiss and embedding is not None:
                self._add_to_faiss(item.id, embedding)
        
        logger.debug(f"Stored long-term memory: {item.id}, type={memory_type.value}")
        return item
    
    def store_item(self, item: MemoryItem) -> MemoryItem:
        """
        直接存储MemoryItem
        
        Args:
            item: 记忆条目
            
        Returns:
            MemoryItem: 存储的记忆条目
        """
        with self._lock:
            self._insert_to_db(item)
            
            embedding = item.get_embedding_array()
            if self.enable_faiss and embedding is not None:
                self._add_to_faiss(item.id, embedding)
        
        logger.debug(f"Stored memory item: {item.id}")
        return item
    
    def _insert_to_db(self, item: MemoryItem) -> None:
        """插入到数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            embedding_blob = None
            if item.embedding:
                embedding_blob = pickle.dumps(np.array(item.embedding, dtype=np.float32))
            
            cursor.execute("""
                INSERT OR REPLACE INTO long_term_memories (
                    id, content, memory_type, status, created_at, updated_at,
                    last_accessed, importance, confidence, familiarity,
                    access_count, repetition_count, embedding, embedding_dim,
                    emotional_tag, associations, context_tags, metadata,
                    decay_factor, next_review, forgetting_curve_stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id,
                json.dumps(item.content) if isinstance(item.content, (dict, list)) else str(item.content),
                item.memory_type.value,
                item.status.value,
                item.created_at.isoformat(),
                item.updated_at.isoformat(),
                item.last_accessed.isoformat() if item.last_accessed else None,
                item.importance,
                item.confidence,
                item.familiarity,
                item.access_count,
                item.repetition_count,
                embedding_blob,
                item.embedding_dim,
                json.dumps(item.emotional_tag) if item.emotional_tag else None,
                json.dumps(item.associations),
                json.dumps(item.context_tags),
                json.dumps(item.metadata),
                item.decay_factor,
                item.next_review.isoformat() if item.next_review else None,
                item.forgetting_curve_stage
            ))
    
    def _add_to_faiss(self, memory_id: str, embedding: np.ndarray) -> None:
        """添加到FAISS索引"""
        if self._faiss_index is None:
            return
        
        try:
            import faiss
            vector = normalize_vector(embedding).reshape(1, -1)
            idx = self._faiss_index.ntotal
            self._faiss_index.add(vector)
            self._id_to_index[memory_id] = idx
            self._index_to_id[idx] = memory_id
        except Exception as e:
            logger.error(f"FAISS add error: {e}")
    
    def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        通过ID检索记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[MemoryItem]: 记忆条目或None
        """
        with self._lock:
            item = self._get_from_db(memory_id)
            if item:
                item.update_access()
                self._update_access_info(memory_id)
            return item
    
    def _get_from_db(self, memory_id: str) -> Optional[MemoryItem]:
        """从数据库获取"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM long_term_memories WHERE id = ?",
                (memory_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_item(row)
            return None
    
    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        """将数据库行转换为MemoryItem"""
        data = dict(row)
        
        # 解析JSON字段
        content = data["content"]
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass
        
        emotional_tag = data.get("emotional_tag")
        if emotional_tag:
            try:
                emotional_tag = json.loads(emotional_tag)
            except (json.JSONDecodeError, TypeError):
                emotional_tag = None
        
        # 解析嵌入向量
        embedding = None
        embedding_blob = data.get("embedding")
        if embedding_blob:
            try:
                embedding_array = pickle.loads(embedding_blob)
                embedding = embedding_array.tolist()
            except Exception:
                pass
        
        return MemoryItem(
            id=data["id"],
            content=content,
            memory_type=MemoryType(data["memory_type"]),
            status=MemoryStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data["last_accessed"] else None,
            importance=data["importance"],
            confidence=data["confidence"],
            familiarity=data["familiarity"],
            access_count=data["access_count"],
            repetition_count=data["repetition_count"],
            embedding=embedding,
            embedding_dim=data["embedding_dim"],
            emotional_tag=emotional_tag,
            associations=json.loads(data.get("associations", "[]")),
            context_tags=json.loads(data.get("context_tags", "[]")),
            metadata=json.loads(data.get("metadata", "{}")),
            decay_factor=data["decay_factor"],
            next_review=datetime.fromisoformat(data["next_review"]) if data["next_review"] else None,
            forgetting_curve_stage=data["forgetting_curve_stage"]
        )
    
    def _update_access_info(self, memory_id: str) -> None:
        """更新访问信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE long_term_memories 
                SET access_count = access_count + 1,
                    last_accessed = ?,
                    familiarity = MIN(1.0, familiarity + 0.1)
                WHERE id = ?
            """, (datetime.now().isoformat(), memory_id))
    
    def search_by_content(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        基于内容搜索
        
        Args:
            query: 查询关键词
            memory_type: 记忆类型过滤
            limit: 结果数量
            
        Returns:
            List[MemoryItem]: 记忆列表
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if memory_type:
                    cursor.execute("""
                        SELECT * FROM long_term_memories 
                        WHERE content LIKE ? AND memory_type = ? AND status != 'forgotten'
                        ORDER BY importance DESC, access_count DESC
                        LIMIT ?
                    """, (f"%{query}%", memory_type.value, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM long_term_memories 
                        WHERE content LIKE ? AND status != 'forgotten'
                        ORDER BY importance DESC, access_count DESC
                        LIMIT ?
                    """, (f"%{query}%", limit))
                
                rows = cursor.fetchall()
                return [self._row_to_item(row) for row in rows]
    
    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        memory_type: Optional[MemoryType] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """
        基于向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            memory_type: 记忆类型过滤
            
        Returns:
            List[Tuple[MemoryItem, float]]: (记忆, 相似度)列表
        """
        with self._lock:
            if self.enable_faiss and self._faiss_index and self._faiss_index.ntotal > 0:
                return self._search_faiss(query_embedding, top_k, memory_type)
            else:
                return self._search_brute_force(query_embedding, top_k, memory_type)
    
    def _search_faiss(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        memory_type: Optional[MemoryType]
    ) -> List[Tuple[MemoryItem, float]]:
        """使用FAISS搜索"""
        try:
            vector = normalize_vector(query_embedding).reshape(1, -1)
            scores, indices = self._faiss_index.search(vector, min(top_k * 2, self._faiss_index.ntotal))
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                memory_id = self._index_to_id.get(int(idx))
                if memory_id:
                    item = self._get_from_db(memory_id)
                    if item and item.status != MemoryStatus.FORGOTTEN:
                        if memory_type is None or item.memory_type == memory_type:
                            results.append((item, float(score)))
            
            return results[:top_k]
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return self._search_brute_force(query_embedding, top_k, memory_type)
    
    def _search_brute_force(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        memory_type: Optional[MemoryType]
    ) -> List[Tuple[MemoryItem, float]]:
        """暴力搜索（FAISS不可用时的回退）"""
        query_norm = normalize_vector(query_embedding)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if memory_type:
                cursor.execute("""
                    SELECT * FROM long_term_memories 
                    WHERE embedding IS NOT NULL AND memory_type = ? AND status != 'forgotten'
                """, (memory_type.value,))
            else:
                cursor.execute("""
                    SELECT * FROM long_term_memories 
                    WHERE embedding IS NOT NULL AND status != 'forgotten'
                """)
            
            rows = cursor.fetchall()
            
            similarities = []
            for row in rows:
                item = self._row_to_item(row)
                embedding = item.get_embedding_array()
                if embedding is not None:
                    similarity = cosine_similarity(query_norm, embedding)
                    similarities.append((item, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
    
    def search_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 50
    ) -> List[MemoryItem]:
        """
        按类型搜索记忆
        
        Args:
            memory_type: 记忆类型
            limit: 结果数量
            
        Returns:
            List[MemoryItem]: 记忆列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM long_term_memories 
                WHERE memory_type = ? AND status != 'forgotten'
                ORDER BY importance DESC, created_at DESC
                LIMIT ?
            """, (memory_type.value, limit))
            
            rows = cursor.fetchall()
            return [self._row_to_item(row) for row in rows]
    
    def search_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.3,
        limit: int = 20
    ) -> List[MemoryItem]:
        """
        按情感搜索记忆
        
        Args:
            emotion: 情感类型
            min_intensity: 最小强度
            limit: 结果数量
            
        Returns:
            List[MemoryItem]: 记忆列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM long_term_memories 
                WHERE emotional_tag IS NOT NULL AND status != 'forgotten'
                ORDER BY importance DESC
            """)
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = self._row_to_item(row)
                if item.emotional_tag:
                    tag = item.emotional_tag
                    primary = tag.get("primary_emotion", "")
                    intensity = tag.get("intensity", 0)
                    if primary == emotion and intensity >= min_intensity:
                        results.append(item)
            
            return results[:limit]
    
    def search_by_context(
        self,
        tags: List[str],
        limit: int = 20
    ) -> List[MemoryItem]:
        """
        按上下文标签搜索
        
        Args:
            tags: 标签列表
            limit: 结果数量
            
        Returns:
            List[MemoryItem]: 记忆列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM long_term_memories 
                WHERE status != 'forgotten'
                ORDER BY importance DESC
            """)
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = self._row_to_item(row)
                # 计算标签匹配度
                matching_tags = set(item.context_tags) & set(tags)
                if matching_tags:
                    results.append((item, len(matching_tags)))
            
            # 按匹配度排序
            results.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in results[:limit]]
    
    def get_associated_memories(
        self,
        memory_id: str,
        min_strength: float = 0.3
    ) -> List[Tuple[MemoryItem, float]]:
        """
        获取关联记忆
        
        Args:
            memory_id: 记忆ID
            min_strength: 最小关联强度
            
        Returns:
            List[Tuple[MemoryItem, float]]: (记忆, 关联强度)列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT target_id, strength FROM memory_associations
                WHERE source_id = ? AND strength >= ?
                UNION
                SELECT source_id, strength FROM memory_associations
                WHERE target_id = ? AND strength >= ?
            """, (memory_id, min_strength, memory_id, min_strength))
            
            results = []
            for row in cursor.fetchall():
                associated_id = row["target_id"]
                strength = row["strength"]
                item = self._get_from_db(associated_id)
                if item and item.status != MemoryStatus.FORGOTTEN:
                    results.append((item, strength))
            
            return sorted(results, key=lambda x: x[1], reverse=True)
    
    def add_association(
        self,
        source_id: str,
        target_id: str,
        association_type: str = "related",
        strength: float = 0.5
    ) -> bool:
        """
        添加记忆关联
        
        Args:
            source_id: 源记忆ID
            target_id: 目标记忆ID
            association_type: 关联类型
            strength: 关联强度
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO memory_associations
                        (source_id, target_id, association_type, strength)
                        VALUES (?, ?, ?, ?)
                    """, (source_id, target_id, association_type, strength))
                    
                    # 更新记忆的associations字段
                    cursor.execute("""
                        UPDATE long_term_memories
                        SET associations = (
                            SELECT json_group_array(DISTINCT value)
                            FROM (
                                SELECT value FROM json_each(associations)
                                UNION SELECT ?
                            )
                        )
                        WHERE id = ?
                    """, (target_id, source_id))
                    
                    return True
                except Exception as e:
                    logger.error(f"Add association error: {e}")
                    return False
    
    def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            updates: 更新字段
            
        Returns:
            bool: 是否成功
        """
        allowed_fields = {
            "content", "importance", "confidence", "status",
            "emotional_tag", "associations", "context_tags",
            "metadata", "decay_factor", "next_review", "forgetting_curve_stage"
        }
        
        valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not valid_updates:
            return False
        
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                set_clauses = []
                values = []
                for key, value in valid_updates.items():
                    if key in ["emotional_tag", "associations", "context_tags", "metadata"]:
                        value = json.dumps(value)
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                # 添加 updated_at 和 WHERE id 的参数
                values.append(datetime.now().isoformat())
                values.append(memory_id)
                
                cursor.execute(f"""
                    UPDATE long_term_memories
                    SET {', '.join(set_clauses)}, updated_at = ?
                    WHERE id = ?
                """, values)
                
                return cursor.rowcount > 0
    
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 先检查记忆是否存在
                cursor.execute(
                    "SELECT COUNT(*) FROM long_term_memories WHERE id = ?",
                    (memory_id,)
                )
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    return False
                
                # 删除记忆
                cursor.execute(
                    "DELETE FROM long_term_memories WHERE id = ?",
                    (memory_id,)
                )
                
                # 删除关联
                cursor.execute("""
                    DELETE FROM memory_associations
                    WHERE source_id = ? OR target_id = ?
                """, (memory_id, memory_id))
                
                logger.debug(f"Deleted memory: {memory_id}")
                return True
    
    def get_all_memories(
        self,
        status: Optional[MemoryStatus] = None,
        limit: int = 1000
    ) -> List[MemoryItem]:
        """
        获取所有记忆
        
        Args:
            status: 状态过滤
            limit: 数量限制
            
        Returns:
            List[MemoryItem]: 记忆列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM long_term_memories 
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (status.value, limit))
            else:
                cursor.execute("""
                    SELECT * FROM long_term_memories 
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [self._row_to_item(row) for row in rows]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 总数量
            cursor.execute("SELECT COUNT(*) FROM long_term_memories")
            total = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute("""
                SELECT memory_type, COUNT(*) 
                FROM long_term_memories 
                GROUP BY memory_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按状态统计
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM long_term_memories 
                GROUP BY status
            """)
            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 平均重要性
            cursor.execute("SELECT AVG(importance) FROM long_term_memories")
            avg_importance = cursor.fetchone()[0] or 0
            
            return {
                "total_memories": total,
                "by_type": by_type,
                "by_status": by_status,
                "avg_importance": avg_importance,
                "db_path": self.db_path,
                "faiss_enabled": self.enable_faiss,
                "vector_dim": self.vector_dim
            }
    
    def rebuild_embeddings(self, batch_size: int = 100) -> int:
        """
        重新生成所有记忆的嵌入向量

        用于在切换嵌入策略后，将使用旧（随机）嵌入的数据升级为新（确定性）嵌入。
        该方法会逐批读取记忆内容，生成新的嵌入并写回数据库。

        Args:
            batch_size: 每批处理的记忆数量，默认 100

        Returns:
            int: 重新生成嵌入的记忆数量
        """
        from hyperbrain.layers.memory.memory_utils import generate_text_embedding

        def _extract_text(content: Union[str, Dict[str, Any]]) -> str:
            if isinstance(content, str):
                return content
            if isinstance(content, dict):
                parts: List[str] = []
                for key in ("input", "output", "content", "text", "query", "message"):
                    value = content.get(key)
                    if isinstance(value, str) and value.strip():
                        parts.append(value)
                if not parts:
                    import json
                    try:
                        return json.dumps(content, ensure_ascii=False, sort_keys=True)
                    except Exception:
                        return str(content)
                return " ".join(parts)
            if isinstance(content, (list, tuple)):
                return " ".join(str(x) for x in content if x)
            return str(content)

        rebuilt = 0
        offset = 0
        with self._lock:
            while True:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, content FROM long_term_memories
                        ORDER BY created_at ASC
                        LIMIT ? OFFSET ?
                    """, (batch_size, offset))
                    rows = cursor.fetchall()
                    if not rows:
                        break

                    for row in rows:
                        memory_id = row[0]
                        raw_content = row[1]
                        try:
                            # content 可能是 JSON 字符串
                            import json
                            try:
                                content_obj = json.loads(raw_content)
                            except Exception:
                                content_obj = raw_content

                            text = _extract_text(content_obj)
                            if not text:
                                text = "__empty__"
                            new_emb = generate_text_embedding(text, self.vector_dim)
                            new_emb_bytes = np.asarray(new_emb, dtype=np.float32).tobytes()
                            cursor.execute("""
                                UPDATE long_term_memories
                                SET embedding = ?, embedding_dim = ?
                                WHERE id = ?
                            """, (new_emb_bytes, self.vector_dim, memory_id))
                            rebuilt += 1
                        except Exception as e:
                            logger.error(f"Failed to rebuild embedding for {memory_id}: {e}")
                    conn.commit()
                    offset += batch_size

        logger.info(f"Rebuilt embeddings for {rebuilt} memories")
        return rebuilt

    def __len__(self) -> int:
        """返回记忆数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM long_term_memories")
            return cursor.fetchone()[0]
    
    def __contains__(self, memory_id: str) -> bool:
        """检查是否包含指定ID的记忆"""
        return self.retrieve(memory_id) is not None
    
    def __repr__(self) -> str:
        return f"LongTermMemory(items={len(self)}, db={self.db_path})"
