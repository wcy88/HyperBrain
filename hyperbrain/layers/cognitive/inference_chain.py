"""
推理链

构建和管理多步推理链，支持回溯和分支
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.inference_chain")


@dataclass
class ChainNode:
    """推理链节点"""
    id: str
    content: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    is_valid: bool = True


class InferenceChain:
    """
    推理链管理器
    
    功能：
    1. 构建推理链
    2. 支持分支和回溯
    3. 评估链的有效性
    4. 选择最优路径
    """
    
    def __init__(self):
        self.nodes: Dict[str, ChainNode] = {}
        self.root_id: Optional[str] = None
        self.current_path: List[str] = []
        logger.info("InferenceChain initialized")
    
    def add_node(self, node_id: str, content: str, 
                 parent_id: Optional[str] = None,
                 confidence: float = 1.0) -> ChainNode:
        """添加节点"""
        node = ChainNode(
            id=node_id,
            content=content,
            parent_id=parent_id,
            confidence=confidence
        )
        self.nodes[node_id] = node
        
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children_ids.append(node_id)
        
        if parent_id is None:
            self.root_id = node_id
        
        return node
    
    def get_path(self, node_id: str) -> List[ChainNode]:
        """获取从根到指定节点的路径"""
        path = []
        current = node_id
        
        while current:
            node = self.nodes.get(current)
            if node:
                path.append(node)
                current = node.parent_id
            else:
                break
        
        return list(reversed(path))
    
    def get_best_path(self) -> List[ChainNode]:
        """获取置信度最高的路径"""
        if not self.root_id:
            return []
        
        # 简化实现：找到最深的有效节点
        best_leaf = self._find_best_leaf()
        if best_leaf:
            return self.get_path(best_leaf)
        return []
    
    def _find_best_leaf(self) -> Optional[str]:
        """找到最佳叶子节点"""
        leaves = [nid for nid, node in self.nodes.items() if not node.children_ids]
        if not leaves:
            return None
        
        return max(leaves, key=lambda nid: self.nodes[nid].confidence)
    
    def validate_chain(self, node_id: str) -> bool:
        """验证链的有效性"""
        path = self.get_path(node_id)
        return all(node.is_valid for node in path)
    
    def prune(self, min_confidence: float = 0.5) -> int:
        """修剪低置信度分支"""
        pruned = 0
        for node_id, node in list(self.nodes.items()):
            if node.confidence < min_confidence:
                node.is_valid = False
                pruned += 1
        return pruned
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "root_id": self.root_id,
            "nodes": {nid: {
                "id": n.id,
                "content": n.content,
                "parent_id": n.parent_id,
                "children_ids": n.children_ids,
                "confidence": n.confidence,
                "is_valid": n.is_valid
            } for nid, n in self.nodes.items()}
        }
