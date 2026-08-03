"""
知识获取模块

实现从多种来源学习和积累知识
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("learning.knowledge")


@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str
    content: str
    source: str
    confidence: float
    category: str = "general"
    timestamp: datetime = field(default_factory=datetime.now)
    verification_status: str = "unverified"
    usage_count: int = 0


class KnowledgeAcquisition:
    """
    知识获取系统
    
    功能：
    1. 从对话中学习
    2. 从文档中学习
    3. 知识验证
    4. 知识融合
    """
    
    def __init__(self):
        self.config = get_config().learning
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.learning_queue: List[Dict[str, Any]] = []
        logger.info("KnowledgeAcquisition initialized")
    
    def learn_from_interaction(self, 
                               input_text: str,
                               response_text: str,
                               feedback: Optional[float] = None) -> KnowledgeItem:
        """
        从交互中学习
        
        Args:
            input_text: 用户输入
            response_text: 系统回复
            feedback: 用户反馈评分
            
        Returns:
            KnowledgeItem: 学习到的知识
        """
        # 提取知识（简化实现）
        knowledge_content = f"Q: {input_text}\nA: {response_text}"
        
        item = KnowledgeItem(
            id=f"knowledge_{len(self.knowledge_base)}",
            content=knowledge_content,
            source="interaction",
            confidence=feedback if feedback is not None else 0.5
        )
        
        self.knowledge_base[item.id] = item
        logger.debug(f"Learned from interaction: {item.id}")
        return item
    
    def learn_from_document(self, 
                           document: str,
                           source: str = "document") -> List[KnowledgeItem]:
        """
        从文档中学习
        
        Args:
            document: 文档内容
            source: 来源标识
            
        Returns:
            List[KnowledgeItem]: 提取的知识列表
        """
        # 简化实现：按段落分割
        paragraphs = [p.strip() for p in document.split("\n\n") if p.strip()]
        
        items = []
        for i, para in enumerate(paragraphs):
            item = KnowledgeItem(
                id=f"doc_{source}_{i}",
                content=para,
                source=source,
                confidence=0.6
            )
            self.knowledge_base[item.id] = item
            items.append(item)
        
        logger.info(f"Extracted {len(items)} knowledge items from {source}")
        return items
    
    def verify_knowledge(self, item_id: str, 
                        verification_result: bool) -> bool:
        """
        验证知识
        
        Args:
            item_id: 知识ID
            verification_result: 验证结果
            
        Returns:
            bool: 是否成功更新
        """
        if item_id not in self.knowledge_base:
            return False
        
        item = self.knowledge_base[item_id]
        item.verification_status = "verified" if verification_result else "rejected"
        
        if verification_result:
            item.confidence = min(1.0, item.confidence + 0.1)
        else:
            item.confidence = max(0.0, item.confidence - 0.2)
        
        logger.debug(f"Knowledge {item_id} verified: {verification_result}")
        return True
    
    def get_knowledge(self, category: Optional[str] = None,
                     min_confidence: float = 0.0) -> List[KnowledgeItem]:
        """获取知识"""
        items = list(self.knowledge_base.values())
        
        if category:
            items = [item for item in items if item.category == category]
        
        items = [item for item in items if item.confidence >= min_confidence]
        
        return sorted(items, key=lambda x: x.confidence, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_knowledge": len(self.knowledge_base),
            "verified_count": sum(1 for k in self.knowledge_base.values() 
                               if k.verification_status == "verified"),
            "avg_confidence": sum(k.confidence for k in self.knowledge_base.values()) / max(len(self.knowledge_base), 1)
        }
