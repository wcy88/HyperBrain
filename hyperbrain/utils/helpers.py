"""
通用工具函数
"""

import uuid
import re
import hashlib
from typing import List, Optional
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        str: 唯一ID
    """
    unique = uuid.uuid4().hex[:8]
    return f"{prefix}_{unique}" if prefix else unique


def timestamp_now() -> str:
    """
    获取当前时间戳字符串
    
    Returns:
        str: ISO格式时间戳
    """
    return datetime.now().isoformat()


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    清洗文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        str: 清洗后的文本
    """
    # 移除多余空白
    text = " ".join(text.split())
    
    # 移除控制字符
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
    
    # 截断
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def chunk_text(text: str, 
               chunk_size: int = 1000,
               overlap: int = 100) -> List[str]:
    """
    将文本分块
    
    Args:
        text: 原始文本
        chunk_size: 块大小
        overlap: 重叠大小
        
    Returns:
        List[str]: 文本块列表
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 尝试在句子边界截断
        if end < len(text):
            # 查找最近的句子结束符
            sentence_end = max(
                text.rfind(".", start, end),
                text.rfind("!", start, end),
                text.rfind("?", start, end),
                text.rfind("\n", start, end)
            )
            
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def compute_hash(text: str) -> str:
    """
    计算文本哈希值
    
    Args:
        text: 输入文本
        
    Returns:
        str: MD5哈希值
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def truncate_middle(text: str, max_length: int = 50) -> str:
    """
    中间截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    half = (max_length - 3) // 2
    return text[:half] + "..." + text[-half:]


def parse_json_safe(text: str, default=None):
    """
    安全解析JSON
    
    Args:
        text: JSON字符串
        default: 默认值
        
    Returns:
        解析结果或默认值
    """
    import json
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def format_duration(seconds: float) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"
