"""
抽象思维模块 (Abstraction Module)

实现抽象思维功能：
- 概念形成
- 概括和泛化
- 抽象和符号化
- 模式识别
- 知识表示
"""

import uuid
import re
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

from pydantic import BaseModel, Field, field_validator

from hyperbrain.core.logger import get_logger

logger = get_logger("cognitive.abstraction")


class ConceptType(str, Enum):
    """概念类型枚举"""
    CONCRETE = "concrete"            # 具体概念
    ABSTRACT = "abstract"            # 抽象概念
    RELATIONAL = "relational"        # 关系概念
    PROCEDURAL = "procedural"        # 程序概念
    META = "meta"                    # 元概念


class PatternType(str, Enum):
    """模式类型枚举"""
    SEQUENTIAL = "sequential"        # 序列模式
    SPATIAL = "spatial"              # 空间模式
    TEMPORAL = "temporal"            # 时间模式
    STRUCTURAL = "structural"        # 结构模式
    STATISTICAL = "statistical"      # 统计模式
    CAUSAL = "causal"                # 因果模式


class Concept(BaseModel):
    """概念模型"""
    concept_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    description: str = Field(default="")
    concept_type: ConceptType = Field(default=ConceptType.CONCRETE)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    examples: List[str] = Field(default_factory=list)
    super_concepts: List[str] = Field(default_factory=list)
    sub_concepts: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    abstraction_level: int = Field(default=0, ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Pattern(BaseModel):
    """模式模型"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="")
    pattern_type: PatternType = Field(default=PatternType.SEQUENTIAL)
    description: str = Field(default="")
    elements: List[Any] = Field(default_factory=list)
    frequency: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_instances: List[str] = Field(default_factory=list)
    generality: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("frequency", "confidence", "generality")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class SymbolMapping(BaseModel):
    """符号映射模型"""
    mapping_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original: str = Field(...)
    symbol: str = Field(...)
    mapping_type: str = Field(default="abbreviation")
    context: str = Field(default="general")
    reversibility: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Generalization(BaseModel):
    """泛化结果模型"""
    generalization_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_instances: List[str] = Field(default_factory=list)
    generalized_form: str = Field(default="")
    abstraction_level: int = Field(default=0, ge=0)
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    exceptions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("coverage", "confidence")
    @classmethod
    def validate_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class KnowledgeRepresentation(BaseModel):
    """知识表示模型"""
    representation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str = Field(...)
    representation_type: str = Field(default="semantic_network")
    structure: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    inferences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class AbstractionEngine:
    """
    抽象思维引擎

    实现概念形成、模式识别、泛化和知识表示功能。

    Attributes:
        concepts: 概念库
        patterns: 模式库
        symbol_mappings: 符号映射库
        generalizations: 泛化记录
        knowledge_representations: 知识表示库
    """

    def __init__(
        self,
        min_pattern_frequency: float = 0.3,
        enable_logging: bool = True
    ):
        self.concepts: Dict[str, Concept] = {}
        self.patterns: Dict[str, Pattern] = {}
        self.symbol_mappings: Dict[str, SymbolMapping] = {}
        self.generalizations: List[Generalization] = []
        self.knowledge_representations: Dict[str, KnowledgeRepresentation] = {}
        self.min_pattern_frequency = min_pattern_frequency
        self.enable_logging = enable_logging

        if enable_logging:
            logger.info("AbstractionEngine initialized")

    def form_concept(
        self,
        name: str,
        examples: List[str],
        attributes: Optional[Dict[str, Any]] = None,
        concept_type: ConceptType = ConceptType.CONCRETE,
        super_concepts: Optional[List[str]] = None
    ) -> Concept:
        """
        形成概念

        从具体实例中抽象出概念。

        Args:
            name: 概念名称
            examples: 示例列表
            attributes: 属性
            concept_type: 概念类型
            super_concepts: 父概念

        Returns:
            Concept: 形成的概念
        """
        common_attrs = self._extract_common_attributes(examples)
        merged_attrs = {**common_attrs, **(attributes or {})}

        abstraction_level = 0
        if super_concepts:
            for sc_id in super_concepts:
                if sc_id in self.concepts:
                    abstraction_level = max(
                        abstraction_level,
                        self.concepts[sc_id].abstraction_level + 1
                    )

        concept = Concept(
            name=name,
            description=f"从 {len(examples)} 个实例中抽象出的概念",
            concept_type=concept_type,
            attributes=merged_attrs,
            examples=examples,
            super_concepts=super_concepts or [],
            abstraction_level=abstraction_level,
            confidence=min(1.0, 0.3 + len(examples) * 0.1)
        )

        self.concepts[concept.concept_id] = concept

        for sc_id in concept.super_concepts:
            if sc_id in self.concepts:
                self.concepts[sc_id].sub_concepts.append(concept.concept_id)

        logger.info(f"Formed concept: {name} (level={abstraction_level})")
        return concept

    def generalize(
        self,
        instances: List[str],
        min_coverage: float = 0.7
    ) -> Optional[Generalization]:
        """
        概括和泛化

        从具体实例中提炼一般规律。

        Args:
            instances: 实例列表
            min_coverage: 最小覆盖率

        Returns:
            Optional[Generalization]: 泛化结果
        """
        if not instances:
            return None

        common_pattern = self._find_common_pattern(instances)
        coverage = common_pattern.get("coverage", 0.0)

        if coverage < min_coverage:
            logger.debug(f"Coverage {coverage:.2f} below threshold {min_coverage}")
            return None

        exceptions = [i for i in instances if i not in common_pattern.get("matches", [])]

        gen = Generalization(
            source_instances=instances,
            generalized_form=common_pattern.get("pattern", ""),
            abstraction_level=common_pattern.get("level", 0),
            coverage=coverage,
            exceptions=exceptions,
            confidence=coverage * 0.9
        )

        self.generalizations.append(gen)
        logger.info(f"Generalized {len(instances)} instances, coverage={coverage:.2f}")
        return gen

    def abstract_and_symbolize(
        self,
        content: str,
        context: str = "general",
        existing_mapping: Optional[str] = None
    ) -> SymbolMapping:
        """
        抽象和符号化

        将复杂内容转换为简洁符号表示。

        Args:
            content: 原始内容
            context: 上下文
            existing_mapping: 已有映射

        Returns:
            SymbolMapping: 符号映射
        """
        if existing_mapping and existing_mapping in self.symbol_mappings:
            return self.symbol_mappings[existing_mapping]

        symbol = self._generate_symbol(content, context)

        mapping = SymbolMapping(
            original=content,
            symbol=symbol,
            mapping_type="abstraction",
            context=context
        )

        self.symbol_mappings[mapping.mapping_id] = mapping
        logger.debug(f"Created symbol mapping: {content} -> {symbol}")
        return mapping

    def recognize_pattern(
        self,
        data: List[Any],
        pattern_type: PatternType = PatternType.SEQUENTIAL,
        min_frequency: Optional[float] = None
    ) -> List[Pattern]:
        """
        模式识别

        从数据中发现重复模式。

        Args:
            data: 数据序列
            pattern_type: 模式类型
            min_frequency: 最小频率

        Returns:
            List[Pattern]: 识别到的模式
        """
        min_freq = min_frequency or self.min_pattern_frequency
        patterns = []

        if pattern_type == PatternType.SEQUENTIAL:
            seq_patterns = self._find_sequence_patterns(data, min_freq)
            patterns.extend(seq_patterns)
        elif pattern_type == PatternType.STATISTICAL:
            stat_patterns = self._find_statistical_patterns(data, min_freq)
            patterns.extend(stat_patterns)
        elif pattern_type == PatternType.STRUCTURAL:
            struct_patterns = self._find_structural_patterns(data, min_freq)
            patterns.extend(struct_patterns)
        else:
            seq_patterns = self._find_sequence_patterns(data, min_freq)
            patterns.extend(seq_patterns)

        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern

        logger.info(f"Recognized {len(patterns)} patterns from {len(data)} items")
        return patterns

    def create_knowledge_representation(
        self,
        subject: str,
        facts: List[Dict[str, Any]],
        representation_type: str = "semantic_network"
    ) -> KnowledgeRepresentation:
        """
        创建知识表示

        Args:
            subject: 主题
            facts: 事实列表
            representation_type: 表示类型

        Returns:
            KnowledgeRepresentation: 知识表示
        """
        structure = self._build_structure(facts, representation_type)
        relationships = self._extract_relationships(facts)
        inferences = self._generate_inferences(facts)

        kr = KnowledgeRepresentation(
            subject=subject,
            representation_type=representation_type,
            structure=structure,
            relationships=relationships,
            inferences=inferences
        )

        self.knowledge_representations[kr.representation_id] = kr
        logger.info(f"Created knowledge representation: {subject}")
        return kr

    def instantiate_concept(
        self,
        concept_id: str,
        specific_attributes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        概念实例化

        将抽象概念具体化为实例。

        Args:
            concept_id: 概念ID
            specific_attributes: 特定属性

        Returns:
            Optional[Dict[str, Any]]: 实例
        """
        concept = self.concepts.get(concept_id)
        if not concept:
            return None

        instance = {**concept.attributes, **specific_attributes}
        instance["_concept_id"] = concept_id
        instance["_concept_name"] = concept.name

        return instance

    def compare_concepts(
        self,
        concept_id_1: str,
        concept_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个概念

        Args:
            concept_id_1: 概念1 ID
            concept_id_2: 概念2 ID

        Returns:
            Dict[str, Any]: 比较结果
        """
        c1 = self.concepts.get(concept_id_1)
        c2 = self.concepts.get(concept_id_2)

        if not c1 or not c2:
            return {"error": "Concept not found"}

        shared_attrs = set(c1.attributes.keys()) & set(c2.attributes.keys())
        shared_examples = set(c1.examples) & set(c2.examples)
        shared_super = set(c1.super_concepts) & set(c2.super_concepts)

        similarity = (
            len(shared_attrs) / max(len(c1.attributes) + len(c2.attributes), 1) * 0.4 +
            len(shared_examples) / max(len(c1.examples) + len(c2.examples), 1) * 0.3 +
            len(shared_super) / max(len(c1.super_concepts) + len(c2.super_concepts), 1) * 0.3
        )

        return {
            "concept_1": c1.name,
            "concept_2": c2.name,
            "similarity": similarity,
            "shared_attributes": list(shared_attrs),
            "shared_examples": list(shared_examples),
            "shared_super_concepts": list(shared_super),
            "is_related": concept_id_2 in c1.related_concepts or concept_id_1 in c2.related_concepts
        }

    def get_concept_hierarchy(self, root_concept_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取概念层次结构

        Args:
            root_concept_id: 根概念ID

        Returns:
            Dict[str, Any]: 层次结构
        """
        if root_concept_id and root_concept_id in self.concepts:
            root = self.concepts[root_concept_id]
            return self._build_hierarchy_node(root)

        top_level = [
            c for c in self.concepts.values()
            if not c.super_concepts
        ]

        return {
            "root": "concepts",
            "children": [self._build_hierarchy_node(c) for c in top_level]
        }

    def query_knowledge(
        self,
        query: str,
        representation_type: Optional[str] = None
    ) -> List[KnowledgeRepresentation]:
        """
        查询知识表示

        Args:
            query: 查询
            representation_type: 表示类型过滤

        Returns:
            List[KnowledgeRepresentation]: 匹配的知识表示
        """
        results = []
        query_lower = query.lower()

        for kr in self.knowledge_representations.values():
            if representation_type and kr.representation_type != representation_type:
                continue

            if query_lower in kr.subject.lower():
                results.append(kr)
                continue

            for key in kr.structure:
                if query_lower in str(key).lower():
                    results.append(kr)
                    break

        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        concept_types: Dict[str, int] = {}
        for c in self.concepts.values():
            ct = c.concept_type.value
            concept_types[ct] = concept_types.get(ct, 0) + 1

        pattern_types: Dict[str, int] = {}
        for p in self.patterns.values():
            pt = p.pattern_type.value
            pattern_types[pt] = pattern_types.get(pt, 0) + 1

        return {
            "total_concepts": len(self.concepts),
            "total_patterns": len(self.patterns),
            "total_symbol_mappings": len(self.symbol_mappings),
            "total_generalizations": len(self.generalizations),
            "total_knowledge_representations": len(self.knowledge_representations),
            "concept_type_distribution": concept_types,
            "pattern_type_distribution": pattern_types,
            "average_abstraction_level": sum(c.abstraction_level for c in self.concepts.values()) / max(len(self.concepts), 1)
        }

    def _extract_common_attributes(self, examples: List[str]) -> Dict[str, Any]:
        """提取共同属性"""
        if not examples:
            return {}

        words_by_example = [set(re.findall(r'\w+', ex.lower())) for ex in examples]
        common_words = words_by_example[0].copy()
        for words in words_by_example[1:]:
            common_words &= words

        attrs = {}
        if common_words:
            attrs["common_keywords"] = list(common_words)

        lengths = [len(ex) for ex in examples]
        attrs["avg_length"] = sum(lengths) / len(lengths)
        attrs["length_variance"] = sum((l - attrs["avg_length"]) ** 2 for l in lengths) / len(lengths)

        return attrs

    def _find_common_pattern(self, instances: List[str]) -> Dict[str, Any]:
        """寻找共同模式"""
        if not instances:
            return {"pattern": "", "coverage": 0.0, "matches": []}

        words_list = [set(re.findall(r'\w+', inst.lower())) for inst in instances]
        common = words_list[0].copy()
        for words in words_list[1:]:
            common &= words

        matches = []
        for inst in instances:
            inst_words = set(re.findall(r'\w+', inst.lower()))
            if common.issubset(inst_words):
                matches.append(inst)

        coverage = len(matches) / len(instances)

        pattern = " ".join(sorted(common)) if common else ""

        return {
            "pattern": pattern,
            "coverage": coverage,
            "matches": matches,
            "level": 1 if common else 0
        }

    def _generate_symbol(self, content: str, context: str) -> str:
        """生成符号"""
        words = re.findall(r'\w+', content)
        if len(words) <= 2:
            return content.upper()

        initials = "".join(w[0].upper() for w in words if w)
        suffix = hash(content) % 1000
        return f"{initials}_{suffix}"

    def _find_sequence_patterns(self, data: List[Any], min_freq: float) -> List[Pattern]:
        """发现序列模式"""
        patterns = []
        n = len(data)
        if n < 3:
            return patterns

        for length in range(2, min(6, n // 2 + 1)):
            subseq_counts: Dict[str, int] = {}
            for i in range(n - length + 1):
                subseq = tuple(str(x) for x in data[i:i + length])
                subseq_counts[subseq] = subseq_counts.get(subseq, 0) + 1

            for subseq, count in subseq_counts.items():
                freq = count / (n - length + 1)
                if freq >= min_freq:
                    pattern = Pattern(
                        name=f"Sequence_{length}_{len(patterns)}",
                        pattern_type=PatternType.SEQUENTIAL,
                        description=f"序列模式: {' -> '.join(subseq)}",
                        elements=list(subseq),
                        frequency=freq,
                        confidence=min(1.0, freq * 1.5),
                        source_instances=[str(i) for i in range(n) if tuple(str(x) for x in data[i:i + length]) == subseq],
                        generality=freq
                    )
                    patterns.append(pattern)

        return patterns

    def _find_statistical_patterns(self, data: List[Any], min_freq: float) -> List[Pattern]:
        """发现统计模式"""
        patterns = []

        try:
            numeric_data = [float(x) for x in data if isinstance(x, (int, float)) or str(x).replace('.', '').isdigit()]
            if len(numeric_data) >= 3:
                avg = sum(numeric_data) / len(numeric_data)
                variance = sum((x - avg) ** 2 for x in numeric_data) / len(numeric_data)

                pattern = Pattern(
                    name="Statistical_Distribution",
                    pattern_type=PatternType.STATISTICAL,
                    description=f"均值={avg:.2f}, 方差={variance:.2f}",
                    elements=numeric_data,
                    frequency=1.0,
                    confidence=0.8,
                    generality=0.5
                )
                patterns.append(pattern)
        except (ValueError, TypeError):
            pass

        counter = Counter(str(x) for x in data)
        total = len(data)
        for item, count in counter.most_common(5):
            freq = count / total
            if freq >= min_freq:
                pattern = Pattern(
                    name=f"Frequent_{item}",
                    pattern_type=PatternType.STATISTICAL,
                    description=f"'{item}' 出现 {count} 次 ({freq:.1%})",
                    elements=[item],
                    frequency=freq,
                    confidence=freq,
                    generality=freq
                )
                patterns.append(pattern)

        return patterns

    def _find_structural_patterns(self, data: List[Any], min_freq: float) -> List[Pattern]:
        """发现结构模式"""
        patterns = []

        structures = []
        for item in data:
            if isinstance(item, dict):
                struct = tuple(sorted(item.keys()))
                structures.append(struct)
            elif isinstance(item, (list, tuple)):
                struct = f"list_len_{len(item)}"
                structures.append(struct)
            else:
                structures.append(f"type_{type(item).__name__}")

        struct_counts: Dict[str, int] = {}
        for s in structures:
            key = str(s)
            struct_counts[key] = struct_counts.get(key, 0) + 1

        for struct, count in struct_counts.items():
            freq = count / len(data)
            if freq >= min_freq:
                pattern = Pattern(
                    name=f"Structure_{struct[:30]}",
                    pattern_type=PatternType.STRUCTURAL,
                    description=f"结构模式: {struct}",
                    elements=[struct],
                    frequency=freq,
                    confidence=freq,
                    generality=freq * 0.8
                )
                patterns.append(pattern)

        return patterns

    def _build_structure(
        self,
        facts: List[Dict[str, Any]],
        representation_type: str
    ) -> Dict[str, Any]:
        """构建知识结构"""
        if representation_type == "semantic_network":
            nodes = {}
            for i, fact in enumerate(facts):
                nodes[f"node_{i}"] = fact
            return {"nodes": nodes, "type": "semantic_network"}
        elif representation_type == "hierarchy":
            return {"root": facts[0] if facts else {}, "children": facts[1:], "type": "hierarchy"}
        else:
            return {"facts": facts, "type": "flat"}

    def _extract_relationships(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取关系"""
        relationships = []

        for i, fact1 in enumerate(facts):
            for j, fact2 in enumerate(facts[i + 1:], i + 1):
                shared_keys = set(fact1.keys()) & set(fact2.keys())
                if shared_keys:
                    relationships.append({
                        "from": f"fact_{i}",
                        "to": f"fact_{j}",
                        "type": "shared_keys",
                        "keys": list(shared_keys)
                    })

        return relationships

    def _generate_inferences(self, facts: List[Dict[str, Any]]) -> List[str]:
        """生成推理"""
        inferences = []

        if len(facts) >= 2:
            inferences.append(f"基于 {len(facts)} 个事实，可以推断它们之间存在关联")

        common_keys = set(facts[0].keys()) if facts else set()
        for fact in facts[1:]:
            common_keys &= set(fact.keys())

        if common_keys:
            inferences.append(f"所有事实共享以下属性: {', '.join(common_keys)}")

        return inferences

    def _build_hierarchy_node(self, concept: Concept) -> Dict[str, Any]:
        """递归构建层次节点"""
        node = {
            "id": concept.concept_id,
            "name": concept.name,
            "type": concept.concept_type.value,
            "abstraction_level": concept.abstraction_level,
            "children": []
        }

        for sub_id in concept.sub_concepts:
            if sub_id in self.concepts:
                node["children"].append(self._build_hierarchy_node(self.concepts[sub_id]))

        return node
