"""
文本解析器

提供高级文本解析功能：分词、句法分析、语义理解等
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from hyperbrain.core.logger import get_logger

logger = get_logger("sensory.text_parser")


@dataclass
class ParsedSentence:
    """解析后的句子"""
    text: str
    tokens: List[str]
    pos_tags: List[Tuple[str, str]]
    dependencies: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    intent: Optional[str] = None
    sentiment: float = 0.0


class TextParser:
    """文本解析器"""
    
    def __init__(self):
        self.sentence_pattern = re.compile(r'[^。！？.!?]+[。！？.!?]?')
        logger.info("TextParser initialized")
    
    def parse(self, text: str) -> List[ParsedSentence]:
        """
        解析文本
        
        Args:
            text: 输入文本
            
        Returns:
            List[ParsedSentence]: 解析后的句子列表
        """
        sentences = self._split_sentences(text)
        parsed = []
        
        for sentence in sentences:
            tokens = self._tokenize(sentence)
            pos_tags = self._pos_tag(tokens)
            entities = self._extract_entities(sentence)
            sentiment = self._analyze_sentiment(sentence)
            intent = self._detect_intent(sentence)
            
            parsed.append(ParsedSentence(
                text=sentence,
                tokens=tokens,
                pos_tags=pos_tags,
                dependencies=[],
                entities=entities,
                intent=intent,
                sentiment=sentiment
            ))
        
        return parsed
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        sentences = self.sentence_pattern.findall(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize(self, text: str) -> List[str]:
        """分词（简化版）"""
        # 基础分词：按空格和标点分割
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return tokens
    
    def _pos_tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """词性标注（简化版）"""
        pos_tags = []
        for token in tokens:
            if token.isdigit():
                pos_tags.append((token, "NUM"))
            elif token.isalpha():
                if token[0].isupper():
                    pos_tags.append((token, "PROPN"))
                else:
                    pos_tags.append((token, "NOUN"))
            else:
                pos_tags.append((token, "PUNCT"))
        return pos_tags
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """实体提取"""
        entities = []
        # 简单规则：大写字母开头的连续词
        matches = re.findall(r'[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*', text)
        for match in matches:
            entities.append({
                "text": match,
                "type": "ENTITY",
                "start": text.find(match),
                "end": text.find(match) + len(match)
            })
        return entities
    
    def _analyze_sentiment(self, text: str) -> float:
        """情感分析"""
        positive = len(re.findall(r'好|棒|优秀|喜欢|开心|快乐|great|good|excellent', text, re.I))
        negative = len(re.findall(r'坏|差|糟糕|讨厌|难过|悲伤|bad|terrible|awful', text, re.I))
        
        total = positive + negative
        if total == 0:
            return 0.0
        return (positive - negative) / total
    
    def _detect_intent(self, text: str) -> Optional[str]:
        """意图识别"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["什么", "what", "who", "where", "when", "为什么"]):
            return "question"
        elif any(w in text_lower for w in ["请", "please", "帮我", "help"]):
            return "request"
        elif any(w in text_lower for w in ["谢谢", "thank", "感谢"]):
            return "gratitude"
        elif any(w in text_lower for w in ["你好", "hello", "hi", "hey"]):
            return "greeting"
        
        return "statement"
