"""
多模态输入处理模块 (Multimodal Input Processor)

负责处理文本、图像、音频等多种模态的输入，进行预处理、特征提取和标准化输出。

功能：
- 文本输入处理：分词、语义理解、实体提取
- 图像输入处理：描述提取、特征识别
- 音频输入处理：语音转文本、情感识别
- 输入格式统一和标准化
- 输入质量评估
"""

import re
import uuid
import base64
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("sensory.multimodal_input")


class InputModality(str, Enum):
    """输入模态类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    MIXED = "mixed"


class InputQuality(str, Enum):
    """输入质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class TextToken(BaseModel):
    """文本令牌"""
    text: str
    pos: str = ""           # 词性
    start: int = 0          # 起始位置
    end: int = 0            # 结束位置
    is_entity: bool = False
    entity_type: Optional[str] = None


class ExtractedEntity(BaseModel):
    """提取的实体"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SemanticFeatures(BaseModel):
    """语义特征"""
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    subjectivity: float = Field(default=0.5, ge=0.0, le=1.0)
    formality: float = Field(default=0.5, ge=0.0, le=1.0)
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    intent: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ImageFeatures(BaseModel):
    """图像特征"""
    description: str = ""
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    dimensions: Optional[Tuple[int, int]] = None
    format: str = ""
    size_bytes: int = 0
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)


class AudioFeatures(BaseModel):
    """音频特征"""
    transcription: str = ""
    language: str = ""
    duration_seconds: float = 0.0
    sample_rate: int = 0
    emotion_detected: Optional[str] = None
    emotion_confidence: float = 0.0
    speaker_count: int = 1
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ProcessedInput(BaseModel):
    """处理后的输入数据"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_content: Any = None
    modality: InputModality = InputModality.TEXT
    
    # 标准化后的文本表示
    normalized_text: str = ""
    
    # 模态特定特征
    text_features: Optional[SemanticFeatures] = None
    image_features: Optional[ImageFeatures] = None
    audio_features: Optional[AudioFeatures] = None
    
    # 通用特征
    tokens: List[TextToken] = Field(default_factory=list)
    entities: List[ExtractedEntity] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_level: InputQuality = InputQuality.FAIR
    
    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "user"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = 0.0
    
    # 错误信息
    is_valid: bool = True
    error_message: Optional[str] = None


class InputQualityReport(BaseModel):
    """输入质量报告"""
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_level: InputQuality = InputQuality.FAIR
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    clarity: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class TextInputProcessor:
    """文本输入处理器"""
    
    def __init__(self):
        self.config = get_config().sensory
        self._positive_words = {
            "好", "棒", "优秀", "喜欢", "开心", "快乐", "满意", "赞", "完美",
            "great", "good", "excellent", "happy", "love", "perfect", "wonderful",
            "amazing", "fantastic", "awesome", "best", "nice"
        }
        self._negative_words = {
            "坏", "差", "糟糕", "讨厌", "难过", "悲伤", "失望", "烦", "错误",
            "bad", "terrible", "awful", "hate", "sad", "angry", "worst", "horrible",
            "disappointing", "wrong", "error", "fail"
        }
        self._intention_patterns = {
            "question": [r"什么|what|who|where|when|why|how|怎么|为什么|吗[?？]"],
            "request": [r"请|please|帮我|help|能否|could you|would you|帮我"],
            "gratitude": [r"谢谢|thank|感谢|appreciate"],
            "greeting": [r"你好|hello|hi|hey|morning|afternoon|evening"],
            "command": [r"必须|should|need to|do this|执行|运行"],
            "code_request": [r"代码|code|编程|program|写个|实现|function|class"]
        }
        logger.info("TextInputProcessor initialized")
    
    async def process(self, content: str, source: str = "user") -> ProcessedInput:
        """处理文本输入"""
        start_time = datetime.now()
        
        # 清洗文本
        cleaned_text = self._clean_text(content)
        
        # 分词
        tokens = self._tokenize(cleaned_text)
        
        # 实体提取
        entities = self._extract_entities(cleaned_text)
        
        # 语义分析
        semantic_features = self._analyze_semantics(cleaned_text)
        
        # 质量评估
        quality_report = self._assess_quality(cleaned_text, tokens, entities)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ProcessedInput(
            original_content=content,
            modality=InputModality.TEXT,
            normalized_text=cleaned_text,
            text_features=semantic_features,
            tokens=tokens,
            entities=entities,
            quality_score=quality_report.overall_score,
            quality_level=quality_report.quality_level,
            source=source,
            processing_time_ms=processing_time
        )
    
    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        # 移除多余空白
        text = " ".join(text.split())
        # 统一标点
        text = text.replace("，", ",").replace("。", ".").replace("？", "?").replace("！", "!")
        # 移除控制字符
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
        return text.strip()
    
    def _tokenize(self, text: str) -> List[TextToken]:
        """分词处理"""
        tokens = []
        # 简单分词：按空格和标点分割
        pattern = r'\w+|[^\w\s]'
        matches = list(re.finditer(pattern, text))
        
        for match in matches:
            word = match.group()
            token = TextToken(
                text=word,
                start=match.start(),
                end=match.end(),
                pos=self._guess_pos(word)
            )
            tokens.append(token)
        
        return tokens
    
    def _guess_pos(self, word: str) -> str:
        """猜测词性"""
        if word.isdigit():
            return "NUM"
        elif word.lower() in {"the", "a", "an", "这个", "那个"}:
            return "DET"
        elif word.lower() in {"is", "are", "was", "were", "是", "在"}:
            return "VERB"
        elif word[0].isupper() and len(word) > 1:
            return "PROPN"
        elif word.lower().endswith(("ing", "ed", "tion", "ly")):
            return "VERB" if word.endswith(("ing", "ed")) else "NOUN"
        return "NOUN"
    
    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """提取实体"""
        entities = []
        
        # 提取人名（大写字母开头）
        name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        for match in re.finditer(name_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type="PERSON",
                start=match.start(),
                end=match.end(),
                confidence=0.7
            ))
        
        # 提取URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for match in re.finditer(url_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type="URL",
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        # 提取邮箱
        email_pattern = r'[\w.-]+@[\w.-]+\.\w+'
        for match in re.finditer(email_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type="EMAIL",
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        # 提取代码相关
        code_pattern = r'`[^`]+`|```[\s\S]*?```'
        for match in re.finditer(code_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group()[:50],
                entity_type="CODE",
                start=match.start(),
                end=match.end(),
                confidence=0.9
            ))
        
        return entities
    
    def _analyze_semantics(self, text: str) -> SemanticFeatures:
        """分析语义特征"""
        text_lower = text.lower()
        words = set(re.findall(r'\w+', text_lower))
        
        # 情感分析
        positive_count = len(words & self._positive_words)
        negative_count = len(words & self._negative_words)
        total_sentiment = positive_count + negative_count
        
        if total_sentiment > 0:
            sentiment_score = (positive_count - negative_count) / total_sentiment
        else:
            sentiment_score = 0.0
        
        # 主观性（基于情感词密度）
        subjectivity = min(1.0, total_sentiment / max(len(words), 1) * 5)
        
        # 正式度
        formal_indicators = len(re.findall(r'[因此|然而|综上所述|accordingly|furthermore]', text))
        formality = min(1.0, 0.3 + formal_indicators * 0.1)
        
        # 复杂度
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        complexity = min(1.0, avg_word_len / 10)
        
        # 意图识别
        intent = self._detect_intent(text)
        
        # 关键词提取
        keywords = self._extract_keywords(text)
        
        # 主题检测
        topics = self._detect_topics(text)
        
        return SemanticFeatures(
            sentiment_score=sentiment_score,
            subjectivity=subjectivity,
            formality=formality,
            complexity=complexity,
            intent=intent,
            topics=topics,
            keywords=keywords
        )
    
    def _detect_intent(self, text: str) -> Optional[str]:
        """检测意图"""
        text_lower = text.lower()
        
        for intent, patterns in self._intention_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        
        return "statement"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = re.findall(r'\w+', text.lower())
        # 过滤停用词
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                     "的", "了", "在", "是", "我", "你", "他", "她", "它", "我们", "你们"}
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        
        # 统计词频
        from collections import Counter
        freq = Counter(filtered)
        return [word for word, count in freq.most_common(10)]
    
    def _detect_topics(self, text: str) -> List[str]:
        """检测主题"""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            "technology": ["code", "program", "software", "hardware", "ai", "algorithm", "数据", "代码", "编程"],
            "business": ["business", "market", "company", "profit", "投资", "市场", "公司"],
            "science": ["science", "research", "study", "experiment", "科学", "研究", "实验"],
            "health": ["health", "medical", "doctor", "disease", "健康", "医疗", "医生"],
            "education": ["education", "learn", "study", "school", "教育", "学习", "学校"],
            "entertainment": ["movie", "music", "game", "娱乐", "电影", "音乐", "游戏"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _assess_quality(self, text: str, tokens: List[TextToken], 
                        entities: List[ExtractedEntity]) -> InputQualityReport:
        """评估输入质量"""
        issues = []
        suggestions = []
        
        # 完整性检查
        completeness = 1.0
        if len(text.strip()) < 5:
            completeness = 0.3
            issues.append("输入过短")
            suggestions.append("请提供更详细的描述")
        elif len(text.strip()) < 20:
            completeness = 0.6
            suggestions.append("可以考虑提供更多细节")
        
        # 清晰度检查
        clarity = 1.0
        if text.count("?") > 3:
            clarity -= 0.2
            issues.append("问题过多，可能不够聚焦")
        if re.search(r'[^\w\s.,!?;:()\-\'\"@#$%&*]', text):
            clarity -= 0.1
            issues.append("包含特殊字符")
        
        # 相关性检查（基于实体密度）
        relevance = min(1.0, 0.5 + len(entities) * 0.1)
        
        # 综合评分
        overall = (completeness * 0.4 + clarity * 0.3 + relevance * 0.3)
        
        # 确定质量等级
        if overall >= 0.8:
            quality_level = InputQuality.EXCELLENT
        elif overall >= 0.6:
            quality_level = InputQuality.GOOD
        elif overall >= 0.4:
            quality_level = InputQuality.FAIR
        elif overall >= 0.2:
            quality_level = InputQuality.POOR
        else:
            quality_level = InputQuality.INVALID
        
        return InputQualityReport(
            overall_score=overall,
            quality_level=quality_level,
            completeness=completeness,
            clarity=clarity,
            relevance=relevance,
            issues=issues,
            suggestions=suggestions
        )


class ImageInputProcessor:
    """图像输入处理器"""
    
    def __init__(self):
        self.supported_formats = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
        logger.info("ImageInputProcessor initialized")
    
    async def process(self, content: Union[str, bytes], 
                      source: str = "user") -> ProcessedInput:
        """处理图像输入"""
        start_time = datetime.now()
        
        try:
            # 解析图像数据
            image_data = self._parse_image_data(content)
            
            # 提取特征（简化实现）
            features = ImageFeatures(
                description="[Image input received]",
                format=image_data.get("format", "unknown"),
                dimensions=image_data.get("dimensions"),
                size_bytes=image_data.get("size", 0),
                quality_score=self._assess_image_quality(image_data)
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessedInput(
                original_content=content,
                modality=InputModality.IMAGE,
                normalized_text=f"[Image: {features.format}, {features.dimensions}]",
                image_features=features,
                quality_score=features.quality_score,
                quality_level=InputQuality.GOOD if features.quality_score > 0.6 else InputQuality.FAIR,
                source=source,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return ProcessedInput(
                original_content=content,
                modality=InputModality.IMAGE,
                is_valid=False,
                error_message=str(e),
                source=source
            )
    
    def _parse_image_data(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """解析图像数据"""
        result = {"format": "unknown", "size": 0, "dimensions": None}
        
        if isinstance(content, str):
            # 检查是否是base64编码
            if content.startswith("data:image"):
                # 数据URI格式
                match = re.match(r'data:image/(\w+);base64,(.+)', content)
                if match:
                    result["format"] = match.group(1)
                    data = base64.b64decode(match.group(2))
                    result["size"] = len(data)
            elif content.startswith("http"):
                result["format"] = "url"
                result["size"] = len(content)
            else:
                # 文件路径
                ext = content.split(".")[-1].lower() if "." in content else ""
                if ext in self.supported_formats:
                    result["format"] = ext
        elif isinstance(content, bytes):
            result["size"] = len(content)
            # 检测格式
            if content[:8] == b'\x89PNG\r\n\x1a\n':
                result["format"] = "png"
            elif content[:2] == b'\xff\xd8':
                result["format"] = "jpeg"
            elif content[:6] in (b'GIF87a', b'GIF89a'):
                result["format"] = "gif"
        
        return result
    
    def _assess_image_quality(self, image_data: Dict[str, Any]) -> float:
        """评估图像质量"""
        score = 0.5
        
        # 基于文件大小
        size = image_data.get("size", 0)
        if size > 1024 * 1024:  # > 1MB
            score += 0.2
        elif size > 100 * 1024:  # > 100KB
            score += 0.1
        elif size < 10 * 1024:  # < 10KB
            score -= 0.2
        
        # 基于格式
        fmt = image_data.get("format", "")
        if fmt in {"png", "jpeg", "jpg"}:
            score += 0.1
        
        return max(0.0, min(1.0, score))


class AudioInputProcessor:
    """音频输入处理器"""
    
    def __init__(self):
        self.supported_formats = {"wav", "mp3", "ogg", "m4a", "flac"}
        logger.info("AudioInputProcessor initialized")
    
    async def process(self, content: Union[str, bytes], 
                      source: str = "user") -> ProcessedInput:
        """处理音频输入"""
        start_time = datetime.now()
        
        try:
            # 解析音频数据
            audio_data = self._parse_audio_data(content)
            
            # 模拟语音转文本和情感识别
            features = AudioFeatures(
                transcription="[Audio transcription placeholder]",
                language="zh-CN",
                duration_seconds=audio_data.get("duration", 0),
                sample_rate=audio_data.get("sample_rate", 44100),
                emotion_detected="neutral",
                emotion_confidence=0.5,
                confidence=0.7
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessedInput(
                original_content=content,
                modality=InputModality.AUDIO,
                normalized_text=features.transcription,
                audio_features=features,
                quality_score=features.confidence,
                quality_level=InputQuality.GOOD if features.confidence > 0.6 else InputQuality.FAIR,
                source=source,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return ProcessedInput(
                original_content=content,
                modality=InputModality.AUDIO,
                is_valid=False,
                error_message=str(e),
                source=source
            )
    
    def _parse_audio_data(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """解析音频数据"""
        result = {"format": "unknown", "duration": 0, "sample_rate": 44100}
        
        if isinstance(content, str):
            if content.startswith("http"):
                result["format"] = "url"
            else:
                ext = content.split(".")[-1].lower() if "." in content else ""
                if ext in self.supported_formats:
                    result["format"] = ext
        elif isinstance(content, bytes):
            result["size"] = len(content)
            # 简单检测格式
            if content[:4] == b'RIFF':
                result["format"] = "wav"
            elif content[:3] == b'ID3' or content[:2] == b'\xff\xfb':
                result["format"] = "mp3"
        
        return result


class MultimodalInputProcessor:
    """
    多模态输入处理器
    
    统一管理所有模态的输入处理，提供统一的处理接口。
    """
    
    def __init__(self):
        self.config = get_config().sensory
        self.text_processor = TextInputProcessor()
        self.image_processor = ImageInputProcessor()
        self.audio_processor = AudioInputProcessor()
        self._processing_history: List[ProcessedInput] = []
        logger.info("MultimodalInputProcessor initialized")
    
    async def process(self, content: Any, 
                      modality: Union[str, InputModality] = InputModality.TEXT,
                      source: str = "user",
                      metadata: Optional[Dict[str, Any]] = None) -> ProcessedInput:
        """
        处理输入数据
        
        Args:
            content: 输入内容
            modality: 输入模态
            source: 输入来源
            metadata: 附加元数据
            
        Returns:
            ProcessedInput: 处理后的输入
        """
        if isinstance(modality, str):
            modality = InputModality(modality.lower())
        
        logger.debug(f"Processing {modality.value} input from {source}")
        
        try:
            if modality == InputModality.TEXT or modality == InputModality.CODE:
                result = await self.text_processor.process(str(content), source)
                if modality == InputModality.CODE:
                    result.modality = InputModality.CODE
            elif modality == InputModality.IMAGE:
                result = await self.image_processor.process(content, source)
            elif modality == InputModality.AUDIO:
                result = await self.audio_processor.process(content, source)
            else:
                result = ProcessedInput(
                    original_content=content,
                    modality=modality,
                    is_valid=False,
                    error_message=f"Unsupported modality: {modality}",
                    source=source
                )
            
            if metadata:
                result.metadata.update(metadata)
            
            self._processing_history.append(result)
            
            # 限制历史记录大小
            if len(self._processing_history) > 1000:
                self._processing_history = self._processing_history[-500:]
            
            return result
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return ProcessedInput(
                original_content=content,
                modality=modality,
                is_valid=False,
                error_message=str(e),
                source=source
            )
    
    async def process_batch(self, 
                           inputs: List[Tuple[Any, Union[str, InputModality], str]]) -> List[ProcessedInput]:
        """
        批量处理输入
        
        Args:
            inputs: [(content, modality, source), ...]
            
        Returns:
            List[ProcessedInput]: 处理结果列表
        """
        tasks = [
            self.process(content, modality, source)
            for content, modality, source in inputs
        ]
        return await asyncio.gather(*tasks)
    
    def assess_quality(self, processed_input: ProcessedInput) -> InputQualityReport:
        """
        评估处理后的输入质量
        
        Args:
            processed_input: 处理后的输入
            
        Returns:
            InputQualityReport: 质量报告
        """
        if not processed_input.is_valid:
            return InputQualityReport(
                overall_score=0.0,
                quality_level=InputQuality.INVALID,
                issues=["输入无效"],
                suggestions=["请检查输入内容"]
            )
        
        # 基于已有的质量分数生成报告
        score = processed_input.quality_score
        
        if score >= 0.8:
            level = InputQuality.EXCELLENT
        elif score >= 0.6:
            level = InputQuality.GOOD
        elif score >= 0.4:
            level = InputQuality.FAIR
        else:
            level = InputQuality.POOR
        
        return InputQualityReport(
            overall_score=score,
            quality_level=level,
            completeness=score,
            clarity=score,
            relevance=score
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._processing_history)
        valid = sum(1 for p in self._processing_history if p.is_valid)
        
        modality_counts = {}
        for p in self._processing_history:
            modality_counts[p.modality.value] = modality_counts.get(p.modality.value, 0) + 1
        
        avg_quality = sum(p.quality_score for p in self._processing_history) / max(total, 1)
        
        return {
            "total_processed": total,
            "valid_count": valid,
            "invalid_count": total - valid,
            "valid_rate": valid / max(total, 1),
            "average_quality": avg_quality,
            "modality_distribution": modality_counts
        }
    
    def get_history(self, limit: int = 100) -> List[ProcessedInput]:
        """获取处理历史"""
        return self._processing_history[-limit:]
    
    def clear_history(self) -> None:
        """清空处理历史"""
        self._processing_history.clear()
        logger.info("Processing history cleared")
