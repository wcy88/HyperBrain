"""
缓存系统

提供内存缓存和LRU缓存机制，用于优化系统性能
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Dict, Generic, Optional, TypeVar, Callable
from dataclasses import dataclass

from hyperbrain.core.logger import get_logger

logger = get_logger("cache")

T = TypeVar('T')


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    access_count: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class LRUCache(Generic[T]):
    """LRU缓存
    
    基于OrderedDict实现，支持：
    - 最大容量限制
    - TTL过期
    - 线程安全
    - 命中率统计
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        name: str = "default"
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.name = name
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[T]: 缓存值或None
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # 更新访问计数并移到末尾（最近使用）
            entry.access_count += 1
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None
    ) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        with self._lock:
            # 如果已存在，更新值
            if key in self._cache:
                self._cache[key] = CacheEntry(
                    value=value,
                    timestamp=time.time(),
                    ttl=ttl or self.default_ttl
                )
                self._cache.move_to_end(key)
                return
            
            # 如果达到容量限制，淘汰最久未使用的
            while len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )
    
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def _evict_oldest(self) -> None:
        """淘汰最久未使用的项"""
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._evictions += 1
            logger.debug(f"Cache '{self.name}' evicted key: {key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0
            }
    
    def cleanup_expired(self) -> int:
        """清理过期项
        
        Returns:
            int: 清理的数量
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class CacheManager:
    """缓存管理器
    
    管理多个缓存实例，提供统一的缓存接口
    """
    
    def __init__(self):
        self._caches: Dict[str, LRUCache] = {}
        self._lock = threading.RLock()
    
    def get_cache(
        self,
        name: str,
        max_size: int = 1000,
        ttl: Optional[float] = None
    ) -> LRUCache:
        """获取或创建缓存
        
        Args:
            name: 缓存名称
            max_size: 最大容量
            ttl: 默认过期时间
            
        Returns:
            LRUCache: 缓存实例
        """
        with self._lock:
            if name not in self._caches:
                self._caches[name] = LRUCache(
                    max_size=max_size,
                    default_ttl=ttl,
                    name=name
                )
                logger.info(f"Created cache '{name}' with max_size={max_size}")
            return self._caches[name]
    
    def delete_cache(self, name: str) -> bool:
        """删除缓存
        
        Args:
            name: 缓存名称
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                return True
            return False
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def cleanup_all(self) -> Dict[str, int]:
        """清理所有过期项
        
        Returns:
            Dict[str, int]: 各缓存清理数量
        """
        with self._lock:
            results = {}
            for name, cache in self._caches.items():
                results[name] = cache.cleanup_expired()
            return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存统计"""
        with self._lock:
            return {
                name: cache.get_stats()
                for name, cache in self._caches.items()
            }


# 全局缓存管理器
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def cached(
    cache_name: str = "default",
    max_size: int = 1000,
    ttl: Optional[float] = None,
    key_func: Optional[Callable] = None
):
    """缓存装饰器
    
    Args:
        cache_name: 缓存名称
        max_size: 最大容量
        ttl: 过期时间
        key_func: 自定义键生成函数
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache_manager().get_cache(cache_name, max_size, ttl)
        
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


class MemoryOptimizer:
    """内存优化器
    
    提供内存使用优化功能
    """
    
    def __init__(self):
        self._gc_threshold = 1000  # 垃圾回收阈值
        self._cleanup_interval = 300  # 清理间隔（秒）
        self._last_cleanup = time.time()
    
    def optimize(self) -> Dict[str, Any]:
        """执行内存优化
        
        Returns:
            Dict: 优化结果
        """
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取内存使用信息
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            result = {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "gc_objects": len(gc.get_objects()),
                "timestamp": time.time()
            }
            
            logger.info(f"Memory optimized: RSS={result['rss_mb']:.1f}MB")
            return result
            
        except ImportError:
            return {"gc_objects": len(gc.get_objects())}
    
    def should_cleanup(self) -> bool:
        """检查是否应该清理"""
        return time.time() - self._last_cleanup > self._cleanup_interval
    
    def mark_cleanup(self) -> None:
        """标记清理时间"""
        self._last_cleanup = time.time()
