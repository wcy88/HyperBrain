"""
向量存储

基于 FAISS 的向量数据库实现
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("database.vector")


class VectorStore:
    """
    向量存储系统
    
    功能：
    1. 向量存储和检索
    2. 相似度搜索
    3. 索引管理
    4. 持久化
    """
    
    def __init__(self, dimension: Optional[int] = None):
        self.config = get_config().memory
        self.dimension = dimension or self.config.vector_dim
        self.index = None
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []
        self.id_map: Dict[str, int] = {}
        
        self.storage_path = Path("data/vectors")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._init_index()
        logger.info(f"VectorStore initialized (dim={self.dimension})")
    
    def _init_index(self):
        """初始化 FAISS 索引"""
        try:
            import faiss
            
            # 创建平面索引（精确搜索）
            self.index = faiss.IndexFlatIP(self.dimension)  # 内积（余弦相似度）
            
            logger.info("FAISS index initialized")
            
        except ImportError:
            logger.warning("FAISS not available, using fallback")
            self.index = None
    
    def add(self, vector_id: str, vector: np.ndarray,
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加向量
        
        Args:
            vector_id: 向量ID
            vector: 向量数据
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        try:
            vector = np.array(vector, dtype=np.float32)
            
            # 归一化向量（用于余弦相似度）
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            if self.index is not None:
                import faiss
                # 添加向量到索引
                vector_2d = vector.reshape(1, -1)
                self.index.add(vector_2d)
            
            self.vectors.append(vector)
            self.metadata.append(metadata or {})
            self.id_map[vector_id] = len(self.vectors) - 1
            
            return True
            
        except Exception as e:
            logger.error(f"Add vector error: {e}")
            return False
    
    def search(self, query_vector: np.ndarray, 
              top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            
        Returns:
            List[Tuple]: (ID, 相似度, 元数据) 列表
        """
        try:
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # 归一化查询向量
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
            
            if self.index is not None and self.index.ntotal > 0:
                # 使用 FAISS 搜索
                query_2d = query_vector.reshape(1, -1)
                distances, indices = self.index.search(query_2d, min(top_k, len(self.vectors)))
                
                results = []
                for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                    if idx >= 0 and idx < len(self.vectors):
                        # 跳过已删除的向量
                        if self.metadata[idx].get("deleted"):
                            continue
                        # 找到对应的ID
                        vector_id = None
                        for vid, vidx in self.id_map.items():
                            if vidx == idx:
                                vector_id = vid
                                break
                        
                        if vector_id:
                            results.append((vector_id, float(dist), self.metadata[idx]))
                
                return results
            else:
                # 回退到暴力搜索
                return self._brute_force_search(query_vector, top_k)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _brute_force_search(self, query_vector: np.ndarray,
                           top_k: int) -> List[Tuple[str, float, Dict[str, Any]]]:
        """暴力搜索（FAISS不可用时）"""
        similarities = []
        
        for i, vector in enumerate(self.vectors):
            # 跳过已删除的向量
            if self.metadata[i].get("deleted"):
                continue

            similarity = np.dot(query_vector, vector)
            
            # 找到ID
            vector_id = None
            for vid, vidx in self.id_map.items():
                if vidx == i:
                    vector_id = vid
                    break
            
            if vector_id:
                similarities.append((vector_id, similarity, self.metadata[i]))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def delete(self, vector_id: str) -> bool:
        """删除向量（注：FAISS不支持直接删除，这里做标记删除）"""
        if vector_id not in self.id_map:
            return False
        
        idx = self.id_map[vector_id]
        self.metadata[idx]["deleted"] = True
        
        logger.debug(f"Marked vector as deleted: {vector_id}")
        return True
    
    def save(self, filename: Optional[str] = None) -> bool:
        """保存向量数据"""
        try:
            filepath = self.storage_path / (filename or "vectors.pkl")
            
            data = {
                "vectors": self.vectors,
                "metadata": self.metadata,
                "id_map": self.id_map,
                "dimension": self.dimension
            }
            
            with open(filepath, "wb") as f:
                pickle.dump(data, f)
            
            logger.info(f"Vector data saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def load(self, filename: Optional[str] = None) -> bool:
        """加载向量数据"""
        try:
            filepath = self.storage_path / (filename or "vectors.pkl")
            
            if not filepath.exists():
                logger.warning(f"Vector file not found: {filepath}")
                return False
            
            with open(filepath, "rb") as f:
                data = pickle.load(f)
            
            self.vectors = data.get("vectors", [])
            self.metadata = data.get("metadata", [])
            self.id_map = data.get("id_map", {})
            self.dimension = data.get("dimension", self.dimension)
            
            # 重建索引
            if self.index is not None and self.vectors:
                import faiss
                vectors_array = np.array(self.vectors, dtype=np.float32)
                self.index = faiss.IndexFlatIP(self.dimension)
                self.index.add(vectors_array)
            
            logger.info(f"Vector data loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Load error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_vectors": len(self.vectors),
            "dimension": self.dimension,
            "has_faiss": self.index is not None,
            "storage_path": str(self.storage_path)
        }
