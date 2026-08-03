"""
注意力机制模块 (Attention Mechanism)

模拟人类注意力系统，实现信息的选择性聚焦和过滤。

功能：
- 自动聚焦重要信息
- 过滤无关信息
- 注意力分配策略
- 多级别注意力（单词级、句子级、段落级）
- 注意力可视化
"""

import re
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("sensory.attention")


class AttentionLevel(str, Enum):
    """注意力级别"""
    WORD = "word"           # 单词级
    SENTENCE = "sentence"   # 句子级
    PARAGRAPH = "paragraph" # 段落级
    DOCUMENT = "document"   # 文档级


class AttentionStrategy(str, Enum):
    """注意力分配策略"""
    UNIFORM = "uniform"         # 均匀分配
    IMPORTANCE_BASED = "importance"  # 基于重要性
    RECENCY_BASED = "recency"   # 基于时效性
    RELEVANCE_BASED = "relevance"    # 基于相关性
    HYBRID = "hybrid"           # 混合策略


class AttentionRegion(BaseModel):
    """注意力区域"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    start: int = 0
    end: int = 0
    level: AttentionLevel = AttentionLevel.WORD
    attention_score: float = Field(default=0.0, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AttentionMap(BaseModel):
    """注意力映射图"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_text: str = ""
    regions: List[AttentionRegion] = Field(default_factory=list)
    strategy: AttentionStrategy = AttentionStrategy.HYBRID
    total_capacity: float = Field(default=1.0, ge=0.0, le=1.0)
    used_capacity: float = Field(default=0.0, ge=0.0, le=1.0)
    focus_regions: List[str] = Field(default_factory=list)
    filtered_regions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def get_focused_text(self, threshold: float = 0.5) -> str:
        """获取高注意力区域的文本"""
        focused = [
            r for r in self.regions 
            if r.attention_score >= threshold
        ]
        focused.sort(key=lambda r: r.start)
        return " ".join(r.text for r in focused)
    
    def get_attention_distribution(self) -> Dict[str, float]:
        """获取注意力分布"""
        if not self.regions:
            return {}
        total = sum(r.attention_score for r in self.regions)
        if total == 0:
            return {r.id: 0.0 for r in self.regions}
        return {r.id: r.attention_score / total for r in self.regions}


class AttentionConfig(BaseModel):
    """注意力配置"""
    default_strategy: AttentionStrategy = AttentionStrategy.HYBRID
    word_capacity: float = Field(default=0.3, ge=0.0, le=1.0)
    sentence_capacity: float = Field(default=0.4, ge=0.0, le=1.0)
    paragraph_capacity: float = Field(default=0.3, ge=0.0, le=1.0)
    importance_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    relevance_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    recency_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    semantic_weight: float = Field(default=0.1, ge=0.0, le=1.0)
    filter_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    focus_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class WordLevelAttention:
    """单词级注意力"""
    
    def __init__(self, config: AttentionConfig):
        self.config = config
        self._importance_keywords = {
            "重要", "关键", "核心", "必须", "需要", "应该", "务必",
            "important", "critical", "key", "essential", "must", "need",
            "urgent", "crucial", "vital", "necessary"
        }
        self._negation_words = {"不", "没", "无", "非", "not", "no", "never", "none"}
        logger.info("WordLevelAttention initialized")
    
    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[AttentionRegion]:
        """分析单词级注意力"""
        words = re.findall(r'\w+|[^\w\s]', text)
        regions = []
        position = 0
        
        for i, word in enumerate(words):
            region = AttentionRegion(
                text=word,
                start=position,
                end=position + len(word),
                level=AttentionLevel.WORD
            )
            
            # 计算重要性
            region.importance_score = self._calculate_word_importance(word, i, words)
            
            # 计算相关性
            region.relevance_score = self._calculate_word_relevance(word, context)
            
            # 计算时效性（位置越靠前越新）
            region.recency_score = 1.0 - (i / max(len(words), 1))
            
            # 语义权重
            region.semantic_weight = self._calculate_semantic_weight(word)
            
            # 综合注意力分数
            region.attention_score = self._compute_attention_score(region)
            
            regions.append(region)
            position += len(word) + 1  # +1 for space
        
        return regions
    
    def _calculate_word_importance(self, word: str, index: int, 
                                    all_words: List[str]) -> float:
        """计算单词重要性"""
        score = 0.5
        word_lower = word.lower()
        
        # 关键词加分
        if word_lower in self._importance_keywords or any(
            kw in word_lower for kw in self._importance_keywords
        ):
            score += 0.3
        
        # 否定词加分（改变语义）
        if word_lower in self._negation_words:
            score += 0.2
        
        # 首字母大写（可能是专有名词）
        if word[0].isupper() and len(word) > 1:
            score += 0.15
        
        # 数字
        if word.isdigit():
            score += 0.1
        
        # 位置权重（开头和结尾更重要）
        total = len(all_words)
        if total > 1:
            position_weight = 1.0 - abs(index - total / 2) / (total / 2)
            score += position_weight * 0.1
        
        return min(1.0, score)
    
    def _calculate_word_relevance(self, word: str, 
                                   context: Optional[Dict[str, Any]]) -> float:
        """计算单词相关性"""
        if not context:
            return 0.5
        
        score = 0.5
        word_lower = word.lower()
        
        # 检查是否与上下文关键词匹配
        context_keywords = context.get("keywords", [])
        if any(kw.lower() in word_lower or word_lower in kw.lower() 
               for kw in context_keywords):
            score += 0.4
        
        # 检查主题匹配
        context_topics = context.get("topics", [])
        topic_keywords = {
            "technology": ["code", "software", "ai", "data", "tech"],
            "business": ["market", "company", "profit", "revenue"],
            "science": ["research", "study", "experiment", "theory"]
        }
        for topic in context_topics:
            if topic in topic_keywords:
                if any(kw in word_lower for kw in topic_keywords[topic]):
                    score += 0.2
        
        return min(1.0, score)
    
    def _calculate_semantic_weight(self, word: str) -> float:
        """计算语义权重"""
        score = 0.5
        
        # 词长（较长的词通常更有语义）
        if len(word) > 6:
            score += 0.1
        
        # 动词和名词权重更高
        if word.endswith(("ing", "tion", "ment", "ness")):
            score += 0.1
        
        return min(1.0, score)
    
    def _compute_attention_score(self, region: AttentionRegion) -> float:
        """计算综合注意力分数"""
        score = (
            region.importance_score * self.config.importance_weight +
            region.relevance_score * self.config.relevance_weight +
            region.recency_score * self.config.recency_weight +
            region.semantic_weight * self.config.semantic_weight
        )
        return min(1.0, max(0.0, score))


class SentenceLevelAttention:
    """句子级注意力"""
    
    def __init__(self, config: AttentionConfig):
        self.config = config
        self.word_attention = WordLevelAttention(config)
        logger.info("SentenceLevelAttention initialized")
    
    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[AttentionRegion]:
        """分析句子级注意力"""
        sentences = self._split_sentences(text)
        regions = []
        position = 0
        
        for i, sentence in enumerate(sentences):
            region = AttentionRegion(
                text=sentence,
                start=position,
                end=position + len(sentence),
                level=AttentionLevel.SENTENCE
            )
            
            # 基于单词注意力计算句子注意力
            word_regions = self.word_attention.analyze(sentence, context)
            
            # 句子重要性 = 单词注意力的加权平均
            if word_regions:
                region.importance_score = sum(
                    w.attention_score for w in word_regions
                ) / len(word_regions)
            
            # 句子位置权重
            region.recency_score = 1.0 - (i / max(len(sentences), 1))
            
            # 句子长度因子
            region.semantic_weight = self._calculate_sentence_semantic_weight(sentence)
            
            # 相关性
            region.relevance_score = self._calculate_sentence_relevance(sentence, context)
            
            # 综合分数
            region.attention_score = self._compute_attention_score(region)
            
            # 保存单词区域信息
            region.metadata["word_regions"] = [
                {
                    "text": w.text,
                    "score": w.attention_score,
                    "importance": w.importance_score
                }
                for w in word_regions
            ]
            
            regions.append(region)
            position += len(sentence) + 1
        
        return regions
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        pattern = r'[^.!?。！？]+[.!?。！？]?'
        sentences = re.findall(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_sentence_semantic_weight(self, sentence: str) -> float:
        """计算句子语义权重"""
        score = 0.5
        
        # 包含问题的句子
        if "?" in sentence or "？" in sentence:
            score += 0.15
        
        # 包含感叹的句子
        if "!" in sentence or "！" in sentence:
            score += 0.1
        
        # 包含数字的句子
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # 长度适中（信息密度）
        word_count = len(sentence.split())
        if 5 <= word_count <= 30:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_sentence_relevance(self, sentence: str, 
                                       context: Optional[Dict[str, Any]]) -> float:
        """计算句子相关性"""
        if not context:
            return 0.5
        
        score = 0.5
        sentence_lower = sentence.lower()
        
        # 关键词匹配
        keywords = context.get("keywords", [])
        matched = sum(1 for kw in keywords if kw.lower() in sentence_lower)
        if matched > 0:
            score += min(0.4, matched * 0.1)
        
        return min(1.0, score)
    
    def _compute_attention_score(self, region: AttentionRegion) -> float:
        """计算综合注意力分数"""
        score = (
            region.importance_score * self.config.importance_weight +
            region.relevance_score * self.config.relevance_weight +
            region.recency_score * self.config.recency_weight +
            region.semantic_weight * self.config.semantic_weight
        )
        return min(1.0, max(0.0, score))


class ParagraphLevelAttention:
    """段落级注意力"""
    
    def __init__(self, config: AttentionConfig):
        self.config = config
        self.sentence_attention = SentenceLevelAttention(config)
        logger.info("ParagraphLevelAttention initialized")
    
    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[AttentionRegion]:
        """分析段落级注意力"""
        paragraphs = text.split('\n\n')
        regions = []
        position = 0
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            region = AttentionRegion(
                text=paragraph.strip(),
                start=position,
                end=position + len(paragraph),
                level=AttentionLevel.PARAGRAPH
            )
            
            # 基于句子注意力
            sentence_regions = self.sentence_attention.analyze(paragraph, context)
            
            if sentence_regions:
                region.importance_score = sum(
                    s.attention_score for s in sentence_regions
                ) / len(sentence_regions)
            
            # 段落位置
            region.recency_score = 1.0 - (i / max(len(paragraphs), 1))
            
            # 段落结构权重
            region.semantic_weight = self._calculate_paragraph_structure_weight(paragraph)
            
            # 相关性
            region.relevance_score = self._calculate_paragraph_relevance(paragraph, context)
            
            region.attention_score = self._compute_attention_score(region)
            
            # 保存句子信息
            region.metadata["sentence_regions"] = [
                {
                    "text": s.text[:50],
                    "score": s.attention_score
                }
                for s in sentence_regions
            ]
            
            regions.append(region)
            position += len(paragraph) + 2
        
        return regions
    
    def _calculate_paragraph_structure_weight(self, paragraph: str) -> float:
        """计算段落结构权重"""
        score = 0.5
        
        # 标题特征
        if paragraph.strip().startswith(("#", "【", "[", "**")):
            score += 0.3
        
        # 列表特征
        if re.match(r'^\s*[\-\*\d]\.', paragraph):
            score += 0.15
        
        # 总结性词汇
        conclusion_words = {"总结", "结论", "综上", "因此", "in conclusion", "summary", "therefore"}
        if any(w in paragraph.lower() for w in conclusion_words):
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_paragraph_relevance(self, paragraph: str, 
                                        context: Optional[Dict[str, Any]]) -> float:
        """计算段落相关性"""
        if not context:
            return 0.5
        
        score = 0.5
        paragraph_lower = paragraph.lower()
        
        # 主题匹配
        topics = context.get("topics", [])
        for topic in topics:
            if topic.lower() in paragraph_lower:
                score += 0.2
        
        return min(1.0, score)
    
    def _compute_attention_score(self, region: AttentionRegion) -> float:
        """计算综合注意力分数"""
        score = (
            region.importance_score * self.config.importance_weight +
            region.relevance_score * self.config.relevance_weight +
            region.recency_score * self.config.recency_weight +
            region.semantic_weight * self.config.semantic_weight
        )
        return min(1.0, max(0.0, score))


class AttentionMechanism:
    """
    注意力机制主类
    
    统一管理多级别注意力，实现信息的选择性聚焦。
    """
    
    def __init__(self, config: Optional[AttentionConfig] = None):
        self.config = config or AttentionConfig()
        self.word_attention = WordLevelAttention(self.config)
        self.sentence_attention = SentenceLevelAttention(self.config)
        self.paragraph_attention = ParagraphLevelAttention(self.config)
        self._attention_history: List[AttentionMap] = []
        logger.info("AttentionMechanism initialized")
    
    def focus(self, text: str, 
              context: Optional[Dict[str, Any]] = None,
              strategy: Optional[AttentionStrategy] = None,
              level: AttentionLevel = AttentionLevel.SENTENCE) -> AttentionMap:
        """
        对文本应用注意力机制
        
        Args:
            text: 输入文本
            context: 上下文信息
            strategy: 注意力策略
            level: 注意力级别
            
        Returns:
            AttentionMap: 注意力映射
        """
        strategy = strategy or self.config.default_strategy
        
        logger.debug(f"Applying attention at {level.value} level with {strategy.value} strategy")
        
        # 根据级别选择分析器
        if level == AttentionLevel.WORD:
            regions = self.word_attention.analyze(text, context)
        elif level == AttentionLevel.SENTENCE:
            regions = self.sentence_attention.analyze(text, context)
        elif level == AttentionLevel.PARAGRAPH:
            regions = self.paragraph_attention.analyze(text, context)
        else:
            # 文档级：综合所有级别
            regions = self._analyze_document_level(text, context)
        
        # 应用策略调整
        regions = self._apply_strategy(regions, strategy, context)
        
        # 创建注意力映射
        attention_map = AttentionMap(
            source_text=text,
            regions=regions,
            strategy=strategy
        )
        
        # 计算容量使用
        attention_map.used_capacity = sum(r.attention_score for r in regions)
        attention_map.total_capacity = self._get_capacity_for_level(level)
        
        # 确定聚焦和过滤区域
        attention_map.focus_regions = [
            r.id for r in regions 
            if r.attention_score >= self.config.focus_threshold
        ]
        attention_map.filtered_regions = [
            r.id for r in regions 
            if r.attention_score < self.config.filter_threshold
        ]
        
        self._attention_history.append(attention_map)
        
        return attention_map
    
    def _analyze_document_level(self, text: str, 
                                 context: Optional[Dict[str, Any]]) -> List[AttentionRegion]:
        """文档级分析"""
        # 综合段落和句子级别的注意力
        paragraph_regions = self.paragraph_attention.analyze(text, context)
        
        # 将段落区域转换为文档级区域
        doc_regions = []
        for para in paragraph_regions:
            doc_region = AttentionRegion(
                text=para.text,
                start=para.start,
                end=para.end,
                level=AttentionLevel.DOCUMENT,
                attention_score=para.attention_score,
                importance_score=para.importance_score,
                relevance_score=para.relevance_score,
                recency_score=para.recency_score,
                semantic_weight=para.semantic_weight,
                metadata=para.metadata
            )
            doc_regions.append(doc_region)
        
        return doc_regions
    
    def _apply_strategy(self, regions: List[AttentionRegion], 
                        strategy: AttentionStrategy,
                        context: Optional[Dict[str, Any]]) -> List[AttentionRegion]:
        """应用注意力策略"""
        if strategy == AttentionStrategy.UNIFORM:
            # 均匀分配
            score = 1.0 / max(len(regions), 1)
            for r in regions:
                r.attention_score = score
        
        elif strategy == AttentionStrategy.IMPORTANCE_BASED:
            # 基于重要性
            total_importance = sum(r.importance_score for r in regions)
            if total_importance > 0:
                for r in regions:
                    r.attention_score = r.importance_score / total_importance
        
        elif strategy == AttentionStrategy.RECENCY_BASED:
            # 基于时效性
            total_recency = sum(r.recency_score for r in regions)
            if total_recency > 0:
                for r in regions:
                    r.attention_score = r.recency_score / total_recency
        
        elif strategy == AttentionStrategy.RELEVANCE_BASED:
            # 基于相关性
            total_relevance = sum(r.relevance_score for r in regions)
            if total_relevance > 0:
                for r in regions:
                    r.attention_score = r.relevance_score / total_relevance
        
        elif strategy == AttentionStrategy.HYBRID:
            # 混合策略：保持原有计算，但进行归一化
            total = sum(r.attention_score for r in regions)
            if total > 0:
                for r in regions:
                    r.attention_score = r.attention_score / total
        
        return regions
    
    def _get_capacity_for_level(self, level: AttentionLevel) -> float:
        """获取指定级别的容量限制"""
        capacities = {
            AttentionLevel.WORD: self.config.word_capacity,
            AttentionLevel.SENTENCE: self.config.sentence_capacity,
            AttentionLevel.PARAGRAPH: self.config.paragraph_capacity,
            AttentionLevel.DOCUMENT: 1.0
        }
        return capacities.get(level, 1.0)
    
    def filter_irrelevant(self, text: str, 
                          context: Optional[Dict[str, Any]] = None,
                          threshold: Optional[float] = None) -> str:
        """
        过滤无关信息
        
        Args:
            text: 输入文本
            context: 上下文
            threshold: 过滤阈值
            
        Returns:
            str: 过滤后的文本
        """
        threshold = threshold or self.config.filter_threshold
        
        attention_map = self.focus(text, context, level=AttentionLevel.SENTENCE)
        
        # 保留高注意力区域
        relevant_regions = [
            r for r in attention_map.regions 
            if r.attention_score >= threshold
        ]
        relevant_regions.sort(key=lambda r: r.start)
        
        return " ".join(r.text for r in relevant_regions)
    
    def get_summary(self, text: str, 
                    max_sentences: int = 3,
                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        基于注意力的文本摘要
        
        Args:
            text: 输入文本
            max_sentences: 最大句子数
            context: 上下文
            
        Returns:
            str: 摘要文本
        """
        attention_map = self.focus(text, context, level=AttentionLevel.SENTENCE)
        
        # 按注意力分数排序
        sorted_regions = sorted(
            attention_map.regions,
            key=lambda r: r.attention_score,
            reverse=True
        )
        
        # 取top N，但保持原始顺序
        top_regions = sorted_regions[:max_sentences]
        top_regions.sort(key=lambda r: r.start)
        
        return " ".join(r.text for r in top_regions)
    
    def visualize_attention(self, attention_map: AttentionMap) -> str:
        """
        可视化注意力分布
        
        Args:
            attention_map: 注意力映射
            
        Returns:
            str: 可视化字符串
        """
        lines = ["=" * 60, "Attention Visualization", "=" * 60]
        
        for region in attention_map.regions:
            bar_length = int(region.attention_score * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            
            level_icon = {
                AttentionLevel.WORD: "·",
                AttentionLevel.SENTENCE: "§",
                AttentionLevel.PARAGRAPH: "¶",
                AttentionLevel.DOCUMENT: "◆"
            }.get(region.level, "·")
            
            text_preview = region.text[:40] + "..." if len(region.text) > 40 else region.text
            
            lines.append(
                f"{level_icon} [{bar}] {region.attention_score:.3f} | {text_preview}"
            )
        
        lines.extend([
            "-" * 60,
            f"Strategy: {attention_map.strategy.value}",
            f"Focus regions: {len(attention_map.focus_regions)}",
            f"Filtered regions: {len(attention_map.filtered_regions)}",
            f"Capacity used: {attention_map.used_capacity:.3f} / {attention_map.total_capacity:.3f}",
            "=" * 60
        ])
        
        return "\n".join(lines)
    
    def get_attention_history(self, limit: int = 100) -> List[AttentionMap]:
        """获取注意力历史"""
        return self._attention_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._attention_history)
        if total == 0:
            return {"total_operations": 0}
        
        avg_regions = sum(len(m.regions) for m in self._attention_history) / total
        avg_focus = sum(len(m.focus_regions) for m in self._attention_history) / total
        
        strategy_counts = {}
        for m in self._attention_history:
            strategy_counts[m.strategy.value] = strategy_counts.get(m.strategy.value, 0) + 1
        
        return {
            "total_operations": total,
            "average_regions_per_map": avg_regions,
            "average_focus_regions": avg_focus,
            "strategy_distribution": strategy_counts
        }
    
    def clear_history(self) -> None:
        """清空历史"""
        self._attention_history.clear()
        logger.info("Attention history cleared")
