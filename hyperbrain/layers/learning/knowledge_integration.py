"""
知识整合机制 (Knowledge Integration Mechanism)

实现知识的系统化管理和整合：
- 新知识分类和归档
- 与已有知识建立关联
- 知识冲突检测和解决
- 知识图谱构建
- 知识更新机制
"""

import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("learning.integration")


class KnowledgeCategory(str, Enum):
    """知识分类"""
    FACT = "fact"
    CONCEPT = "concept"
    PROCEDURE = "procedure"
    PRINCIPLE = "principle"
    EXPERIENCE = "experience"
    HYPOTHESIS = "hypothesis"
    GENERAL = "general"


class ConflictType(str, Enum):
    """冲突类型"""
    DIRECT_CONTRADICTION = "direct_contradiction"
    INCONSISTENCY = "inconsistency"
    OUTDATED = "outdated"
    AMBIGUITY = "ambiguity"
    OVERLAP = "overlap"


class KnowledgeNode(BaseModel):
    """知识图谱节点"""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(...)
    category: KnowledgeCategory = Field(default=KnowledgeCategory.GENERAL)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0, ge=0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", "importance")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeEdge(BaseModel):
    """知识图谱边"""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = Field(...)
    target_id: str = Field(...)
    relation_type: str = Field(default="related")
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    bidirectional: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("strength")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeConflict(BaseModel):
    """知识冲突"""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = Field(default=ConflictType.INCONSISTENCY)
    knowledge_a_id: str = Field(...)
    knowledge_b_id: str = Field(...)
    description: str = Field(default="")
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    resolution: Optional[str] = Field(default=None)
    resolved: bool = Field(default=False)
    detected_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("severity")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ClassificationResult(BaseModel):
    """分类结果"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = Field(...)
    assigned_category: KnowledgeCategory = Field(...)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    alternative_categories: List[Tuple[KnowledgeCategory, float]] = Field(default_factory=list)
    classification_reason: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeArchive(BaseModel):
    """知识归档"""
    archive_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = Field(...)
    archive_reason: str = Field(default="")
    archived_at: datetime = Field(default_factory=datetime.now)
    original_category: KnowledgeCategory = Field(default=KnowledgeCategory.GENERAL)
    preservation_level: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("preservation_level")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


@dataclass
class KnowledgeIntegrationConfig:
    """知识整合配置"""
    similarity_threshold: float = 0.7
    conflict_threshold: float = 0.8
    max_knowledge_nodes: int = 10000
    auto_archive_enabled: bool = True
    archive_after_days: int = 365
    min_confidence_for_acceptance: float = 0.3
    graph_building_enabled: bool = True


class KnowledgeIntegrationMechanism:
    """
    知识整合机制

    负责知识的系统化管理和整合：
    1. 分类归档：自动分类和存储知识
    2. 关联建立：构建知识间的关系
    3. 冲突检测：发现并解决知识冲突
    4. 知识图谱：构建可视化知识网络
    5. 知识更新：维护知识的时效性

    Attributes:
        config: 配置
        knowledge_nodes: 知识节点
        knowledge_edges: 知识边
        conflicts: 冲突记录
        archives: 归档记录
        classifications: 分类记录
    """

    def __init__(self, config: Optional[KnowledgeIntegrationConfig] = None):
        self.config = config or KnowledgeIntegrationConfig()

        # 知识图谱
        self.knowledge_nodes: Dict[str, KnowledgeNode] = {}
        self.knowledge_edges: Dict[str, KnowledgeEdge] = {}
        self.node_index: Dict[KnowledgeCategory, List[str]] = defaultdict(list)
        self.content_index: Dict[str, str] = {}  # content_hash -> node_id

        # 冲突管理
        self.conflicts: Dict[str, KnowledgeConflict] = {}
        self.unresolved_conflicts: Set[str] = set()

        # 归档
        self.archives: Dict[str, KnowledgeArchive] = {}
        self.archived_nodes: Set[str] = set()

        # 分类记录
        self.classifications: List[ClassificationResult] = []

        # 统计
        self.total_nodes_created: int = 0
        self.total_edges_created: int = 0
        self.total_conflicts_detected: int = 0
        self.total_conflicts_resolved: int = 0
        self.total_classifications: int = 0
        self.total_archives: int = 0

        logger.info("KnowledgeIntegrationMechanism initialized")

    # ========== 新知识分类和归档 ==========

    def classify_knowledge(self, content: str,
                          suggested_category: Optional[KnowledgeCategory] = None,
                          source: str = "") -> ClassificationResult:
        """
        对新知识进行分类

        Args:
            content: 知识内容
            suggested_category: 建议的分类
            source: 来源

        Returns:
            ClassificationResult: 分类结果
        """
        self.total_classifications += 1

        # 基于内容的自动分类
        detected_category, confidence = self._auto_classify(content)

        # 如果有建议分类，结合建议
        if suggested_category:
            if suggested_category == detected_category:
                confidence = min(1.0, confidence + 0.2)
            else:
                # 使用建议但降低置信度
                detected_category = suggested_category
                confidence = max(0.3, confidence - 0.2)

        # 生成替代分类
        alternatives = self._get_alternative_categories(content, detected_category)

        result = ClassificationResult(
            knowledge_id="",  # 将在添加节点时更新
            assigned_category=detected_category,
            confidence=confidence,
            alternative_categories=alternatives,
            classification_reason=f"Based on content analysis and keywords"
        )

        logger.debug(f"Classified knowledge as {detected_category.value}, confidence={confidence:.2f}")
        return result

    def _auto_classify(self, content: str) -> Tuple[KnowledgeCategory, float]:
        """自动分类"""
        content_lower = content.lower()

        # 基于关键词的分类规则
        category_indicators = {
            KnowledgeCategory.FACT: ["是", "为", "等于", "fact", "is", "equals", "was"],
            KnowledgeCategory.CONCEPT: ["概念", "定义", "concept", "definition", "refers to"],
            KnowledgeCategory.PROCEDURE: ["步骤", "方法", "如何", "procedure", "step", "how to", "method"],
            KnowledgeCategory.PRINCIPLE: ["原理", "原则", "定律", "principle", "law", "rule", "theorem"],
            KnowledgeCategory.EXPERIENCE: ["经验", "经历", "发现", "experience", "found", "observed"],
            KnowledgeCategory.HYPOTHESIS: ["假设", "可能", "假设", "hypothesis", "might", "possibly", "could"],
        }

        scores: Dict[KnowledgeCategory, float] = {}
        for category, indicators in category_indicators.items():
            score = sum(1 for ind in indicators if ind in content_lower)
            scores[category] = score / len(indicators)

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        if confidence < 0.1:
            return KnowledgeCategory.GENERAL, 0.3

        return best_category, min(1.0, confidence + 0.3)

    def _get_alternative_categories(self, content: str,
                                    primary: KnowledgeCategory) -> List[Tuple[KnowledgeCategory, float]]:
        """获取替代分类"""
        detected, _ = self._auto_classify(content)
        if detected != primary:
            return [(detected, 0.3)]
        return []

    def add_knowledge(self, content: str,
                     category: Optional[KnowledgeCategory] = None,
                     confidence: float = 0.5,
                     source: str = "",
                     metadata: Optional[Dict[str, Any]] = None) -> KnowledgeNode:
        """
        添加新知识

        Args:
            content: 知识内容
            category: 分类
            confidence: 置信度
            source: 来源
            metadata: 元数据

        Returns:
            KnowledgeNode: 知识节点
        """
        # 检查是否已存在
        content_hash = self._hash_content(content)
        if content_hash in self.content_index:
            node_id = self.content_index[content_hash]
            node = self.knowledge_nodes[node_id]
            node.confidence = max(node.confidence, confidence)
            node.access_count += 1
            node.updated_at = datetime.now()
            logger.debug(f"Updated existing knowledge: {node_id}")
            return node

        # 分类
        if category is None:
            classification = self.classify_knowledge(content, source=source)
            category = classification.assigned_category

        # 创建节点
        self.total_nodes_created += 1
        node = KnowledgeNode(
            content=content,
            category=category,
            confidence=confidence,
            source=source,
            metadata=metadata or {}
        )

        self.knowledge_nodes[node.node_id] = node
        self.content_index[content_hash] = node.node_id
        self.node_index[category].append(node.node_id)

        # 检测冲突
        self._detect_conflicts_for_node(node)

        # 建立关联
        if self.config.graph_building_enabled:
            self._establish_relations(node)

        logger.info(f"Added knowledge node: {node.node_id} ({category.value})")
        return node

    def _hash_content(self, content: str) -> str:
        """内容哈希"""
        import hashlib
        return hashlib.md5(content.lower().strip().encode()).hexdigest()

    def archive_knowledge(self, node_id: str,
                         reason: str = "",
                         preservation_level: float = 0.5) -> Optional[KnowledgeArchive]:
        """
        归档知识

        Args:
            node_id: 节点ID
            reason: 归档原因
            preservation_level: 保留级别

        Returns:
            Optional[KnowledgeArchive]: 归档记录
        """
        if node_id not in self.knowledge_nodes:
            return None

        node = self.knowledge_nodes[node_id]

        self.total_archives += 1
        archive = KnowledgeArchive(
            knowledge_id=node_id,
            archive_reason=reason or "Auto-archived",
            original_category=node.category,
            preservation_level=preservation_level
        )

        self.archives[archive.archive_id] = archive
        self.archived_nodes.add(node_id)

        logger.info(f"Archived knowledge: {node_id}, reason={reason}")
        return archive

    def get_knowledge_by_category(self, category: KnowledgeCategory) -> List[KnowledgeNode]:
        """按分类获取知识"""
        node_ids = self.node_index.get(category, [])
        return [self.knowledge_nodes[nid] for nid in node_ids
                if nid in self.knowledge_nodes and nid not in self.archived_nodes]

    def search_knowledge(self, query: str,
                        category: Optional[KnowledgeCategory] = None) -> List[KnowledgeNode]:
        """
        搜索知识

        Args:
            query: 查询
            category: 分类过滤

        Returns:
            List[KnowledgeNode]: 匹配的知识节点
        """
        query_lower = query.lower()
        results = []

        nodes_to_search = self.knowledge_nodes.values()
        if category:
            nodes_to_search = self.get_knowledge_by_category(category)

        for node in nodes_to_search:
            if node.node_id in self.archived_nodes:
                continue

            # 简单匹配
            if query_lower in node.content.lower():
                results.append(node)
            elif any(query_lower in str(v).lower() for v in node.metadata.values()):
                results.append(node)

        # 按相关度排序
        results.sort(key=lambda n: n.confidence * n.importance, reverse=True)
        return results

    # ========== 与已有知识建立关联 ==========

    def _establish_relations(self, new_node: KnowledgeNode) -> List[KnowledgeEdge]:
        """为新节点建立关联"""
        edges = []

        for existing_node in self.knowledge_nodes.values():
            if existing_node.node_id == new_node.node_id:
                continue
            if existing_node.node_id in self.archived_nodes:
                continue

            # 计算相似度
            similarity = self._calculate_similarity(new_node, existing_node)

            if similarity > self.config.similarity_threshold:
                edge = self._create_edge(
                    new_node.node_id, existing_node.node_id,
                    relation_type="similar",
                    strength=similarity
                )
                edges.append(edge)

            # 检查类别关联
            if new_node.category == existing_node.category:
                edge = self._create_edge(
                    new_node.node_id, existing_node.node_id,
                    relation_type="same_category",
                    strength=0.5
                )
                edges.append(edge)

        return edges

    def _calculate_similarity(self, node_a: KnowledgeNode,
                              node_b: KnowledgeNode) -> float:
        """计算节点相似度"""
        words_a = set(node_a.content.lower().split())
        words_b = set(node_b.content.lower().split())
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def _create_edge(self, source_id: str, target_id: str,
                    relation_type: str = "related",
                    strength: float = 0.5,
                    bidirectional: bool = False) -> KnowledgeEdge:
        """创建知识边"""
        self.total_edges_created += 1
        edge = KnowledgeEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional
        )
        self.knowledge_edges[edge.edge_id] = edge
        return edge

    def create_relation(self, source_id: str, target_id: str,
                       relation_type: str = "related",
                       strength: float = 0.5) -> Optional[KnowledgeEdge]:
        """
        显式创建知识关联

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 关系类型
            strength: 强度

        Returns:
            Optional[KnowledgeEdge]: 知识边
        """
        if source_id not in self.knowledge_nodes or target_id not in self.knowledge_nodes:
            return None

        return self._create_edge(source_id, target_id, relation_type, strength)

    def get_related_knowledge(self, node_id: str,
                              relation_type: Optional[str] = None,
                              min_strength: float = 0.0) -> List[Tuple[KnowledgeNode, float]]:
        """
        获取相关知识

        Args:
            node_id: 节点ID
            relation_type: 关系类型过滤
            min_strength: 最小强度

        Returns:
            List[Tuple[KnowledgeNode, float]]: (节点, 强度)列表
        """
        related = []

        for edge in self.knowledge_edges.values():
            if edge.source_id == node_id or edge.target_id == node_id:
                if relation_type and edge.relation_type != relation_type:
                    continue
                if edge.strength < min_strength:
                    continue

                other_id = edge.target_id if edge.source_id == node_id else edge.source_id
                if other_id in self.knowledge_nodes and other_id not in self.archived_nodes:
                    related.append((self.knowledge_nodes[other_id], edge.strength))

        related.sort(key=lambda x: x[1], reverse=True)
        return related

    # ========== 知识冲突检测和解决 ==========

    def _detect_conflicts_for_node(self, node: KnowledgeNode) -> List[KnowledgeConflict]:
        """检测节点的知识冲突"""
        conflicts = []

        for existing_node in self.knowledge_nodes.values():
            if existing_node.node_id == node.node_id:
                continue
            if existing_node.node_id in self.archived_nodes:
                continue

            conflict = self._check_conflict(node, existing_node)
            if conflict:
                conflicts.append(conflict)
                self.conflicts[conflict.conflict_id] = conflict
                self.unresolved_conflicts.add(conflict.conflict_id)
                self.total_conflicts_detected += 1

        return conflicts

    def _check_conflict(self, node_a: KnowledgeNode,
                        node_b: KnowledgeNode) -> Optional[KnowledgeConflict]:
        """检查两个节点是否冲突"""
        # 相似度高但置信度差异大
        similarity = self._calculate_similarity(node_a, node_b)

        if similarity > self.config.conflict_threshold:
            # 内容相似度高，检查是否矛盾
            if self._are_contradictory(node_a.content, node_b.content):
                return KnowledgeConflict(
                    conflict_type=ConflictType.DIRECT_CONTRADICTION,
                    knowledge_a_id=node_a.node_id,
                    knowledge_b_id=node_b.node_id,
                    description=f"Contradiction between {node_a.node_id} and {node_b.node_id}",
                    severity=0.8
                )
            else:
                # 可能是重叠
                return KnowledgeConflict(
                    conflict_type=ConflictType.OVERLAP,
                    knowledge_a_id=node_a.node_id,
                    knowledge_b_id=node_b.node_id,
                    description=f"Significant overlap between {node_a.node_id} and {node_b.node_id}",
                    severity=0.3
                )

        return None

    def _are_contradictory(self, content_a: str, content_b: str) -> bool:
        """检查内容是否矛盾"""
        # 简单启发式
        negations_a = ["不", "没有", "not", "no", "never", "false"]
        negations_b = ["不", "没有", "not", "no", "never", "false"]

        a_has_neg = any(n in content_a.lower() for n in negations_a)
        b_has_neg = any(n in content_b.lower() for n in negations_b)

        # 如果内容相似但否定状态不同
        if a_has_neg != b_has_neg:
            words_a = set(content_a.lower().split()) - set(negations_a)
            words_b = set(content_b.lower().split()) - set(negations_b)
            overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
            if overlap > 0.6:
                return True

        return False

    def resolve_conflict(self, conflict_id: str,
                        resolution: str,
                        preferred_knowledge_id: Optional[str] = None) -> Optional[KnowledgeConflict]:
        """
        解决知识冲突

        Args:
            conflict_id: 冲突ID
            resolution: 解决方案描述
            preferred_knowledge_id: 优先采用的知识ID

        Returns:
            Optional[KnowledgeConflict]: 更新后的冲突
        """
        if conflict_id not in self.conflicts:
            return None

        conflict = self.conflicts[conflict_id]
        conflict.resolution = resolution
        conflict.resolved = True
        conflict.resolved_at = datetime.now()

        # 如果指定了优先知识，降低另一个的置信度
        if preferred_knowledge_id:
            other_id = (conflict.knowledge_b_id
                       if preferred_knowledge_id == conflict.knowledge_a_id
                       else conflict.knowledge_a_id)
            if other_id in self.knowledge_nodes:
                self.knowledge_nodes[other_id].confidence *= 0.5

        self.unresolved_conflicts.discard(conflict_id)
        self.total_conflicts_resolved += 1

        logger.info(f"Resolved conflict: {conflict_id}, resolution={resolution}")
        return conflict

    def get_conflicts(self, resolved_only: bool = False,
                     unresolved_only: bool = True) -> List[KnowledgeConflict]:
        """
        获取冲突列表

        Args:
            resolved_only: 仅已解决
            unresolved_only: 仅未解决

        Returns:
            List[KnowledgeConflict]: 冲突列表
        """
        if resolved_only:
            return [c for c in self.conflicts.values() if c.resolved]
        elif unresolved_only:
            return [self.conflicts[cid] for cid in self.unresolved_conflicts]
        return list(self.conflicts.values())

    # ========== 知识图谱构建 ==========

    def build_knowledge_graph(self, center_node_id: Optional[str] = None,
                             max_depth: int = 2) -> Dict[str, Any]:
        """
        构建知识图谱

        Args:
            center_node_id: 中心节点ID
            max_depth: 最大深度

        Returns:
            Dict[str, Any]: 图谱数据
        """
        graph = {
            "nodes": [],
            "edges": [],
            "statistics": {}
        }

        if center_node_id:
            # 以特定节点为中心的子图
            visited = {center_node_id}
            current_level = {center_node_id}

            for depth in range(max_depth):
                next_level = set()
                for node_id in current_level:
                    if node_id not in self.knowledge_nodes:
                        continue

                    node = self.knowledge_nodes[node_id]
                    graph["nodes"].append({
                        "id": node.node_id,
                        "content": node.content[:100],
                        "category": node.category.value,
                        "confidence": node.confidence
                    })

                    for edge in self.knowledge_edges.values():
                        if edge.source_id == node_id or edge.target_id == node_id:
                            other_id = edge.target_id if edge.source_id == node_id else edge.source_id
                            if other_id not in visited:
                                visited.add(other_id)
                                next_level.add(other_id)

                            graph["edges"].append({
                                "id": edge.edge_id,
                                "source": edge.source_id,
                                "target": edge.target_id,
                                "type": edge.relation_type,
                                "strength": edge.strength
                            })

                current_level = next_level
        else:
            # 完整图谱
            for node in self.knowledge_nodes.values():
                if node.node_id not in self.archived_nodes:
                    graph["nodes"].append({
                        "id": node.node_id,
                        "content": node.content[:100],
                        "category": node.category.value,
                        "confidence": node.confidence
                    })

            for edge in self.knowledge_edges.values():
                graph["edges"].append({
                    "id": edge.edge_id,
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "type": edge.relation_type,
                    "strength": edge.strength
                })

        graph["statistics"] = {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "category_distribution": self._get_category_distribution()
        }

        return graph

    def _get_category_distribution(self) -> Dict[str, int]:
        """获取分类分布"""
        distribution: Dict[str, int] = defaultdict(int)
        for node in self.knowledge_nodes.values():
            if node.node_id not in self.archived_nodes:
                distribution[node.category.value] += 1
        return dict(distribution)

    # ========== 知识更新机制 ==========

    def update_knowledge(self, node_id: str,
                        new_content: Optional[str] = None,
                        new_confidence: Optional[float] = None,
                        new_category: Optional[KnowledgeCategory] = None) -> Optional[KnowledgeNode]:
        """
        更新知识

        Args:
            node_id: 节点ID
            new_content: 新内容
            new_confidence: 新置信度
            new_category: 新分类

        Returns:
            Optional[KnowledgeNode]: 更新后的节点
        """
        if node_id not in self.knowledge_nodes:
            return None

        node = self.knowledge_nodes[node_id]

        if new_content:
            # 更新内容索引
            old_hash = self._hash_content(node.content)
            if old_hash in self.content_index:
                del self.content_index[old_hash]
            node.content = new_content
            self.content_index[self._hash_content(new_content)] = node_id

        if new_confidence is not None:
            node.confidence = new_confidence

        if new_category:
            # 更新分类索引
            old_category = node.category
            self.node_index[old_category].remove(node_id)
            node.category = new_category
            self.node_index[new_category].append(node_id)

        node.updated_at = datetime.now()
        node.access_count += 1

        logger.info(f"Updated knowledge: {node_id}")
        return node

    def merge_knowledge(self, source_id: str, target_id: str) -> Optional[KnowledgeNode]:
        """
        合并知识

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID

        Returns:
            Optional[KnowledgeNode]: 合并后的节点
        """
        if source_id not in self.knowledge_nodes or target_id not in self.knowledge_nodes:
            return None

        source = self.knowledge_nodes[source_id]
        target = self.knowledge_nodes[target_id]

        # 合并内容
        merged_content = f"{target.content}\n[Merged from {source_id}]: {source.content}"
        target.content = merged_content
        target.confidence = max(target.confidence, source.confidence)
        target.updated_at = datetime.now()

        # 转移关联
        for edge in list(self.knowledge_edges.values()):
            if edge.source_id == source_id:
                edge.source_id = target_id
            if edge.target_id == source_id:
                edge.target_id = target_id

        # 归档源节点
        self.archive_knowledge(source_id, reason="Merged into " + target_id)

        logger.info(f"Merged knowledge: {source_id} -> {target_id}")
        return target

    # ========== 统计接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_nodes_created": self.total_nodes_created,
            "total_edges_created": self.total_edges_created,
            "total_conflicts_detected": self.total_conflicts_detected,
            "total_conflicts_resolved": self.total_conflicts_resolved,
            "total_classifications": self.total_classifications,
            "total_archives": self.total_archives,
            "active_nodes": len(self.knowledge_nodes) - len(self.archived_nodes),
            "archived_nodes": len(self.archived_nodes),
            "unresolved_conflicts": len(self.unresolved_conflicts),
            "category_distribution": self._get_category_distribution(),
            "avg_confidence": self._avg_confidence(),
        }

    def _avg_confidence(self) -> float:
        """平均置信度"""
        active_nodes = [n for n in self.knowledge_nodes.values()
                       if n.node_id not in self.archived_nodes]
        if not active_nodes:
            return 0.0
        return sum(n.confidence for n in active_nodes) / len(active_nodes)

    def reset(self) -> None:
        """重置"""
        self.knowledge_nodes.clear()
        self.knowledge_edges.clear()
        self.node_index.clear()
        self.content_index.clear()
        self.conflicts.clear()
        self.unresolved_conflicts.clear()
        self.archives.clear()
        self.archived_nodes.clear()
        self.classifications.clear()
        self.total_nodes_created = 0
        self.total_edges_created = 0
        self.total_conflicts_detected = 0
        self.total_conflicts_resolved = 0
        self.total_classifications = 0
        self.total_archives = 0
        logger.info("KnowledgeIntegrationMechanism reset")
