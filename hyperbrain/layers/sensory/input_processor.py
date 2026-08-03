"""
感知层输入处理器

负责接收和预处理各类输入信息，包括文本、语音、图像等
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("sensory.input_processor")


@dataclass
class SensoryInput:
    """感知输入数据对象"""
    raw_data: Any
    modality: str  # text, image, audio, video
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "user"
    priority: int = 1


@dataclass
class ProcessedInput:
    """预处理后的输入数据"""
    original: SensoryInput
    normalized_text: Optional[str] = None
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    sentiment_score: float = 0.0
    features: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True
    error_message: Optional[str] = None


class SensoryInputProcessor:
    """
    感知输入处理器
    
    功能：
    1. 接收多模态输入
    2. 输入验证和清洗
    3. 格式标准化
    4. 特征提取
    5. 优先级排序
    """
    
    def __init__(self):
        self.config = get_config().sensory
        self.input_buffer: List[SensoryInput] = []
        self.processed_count = 0
        logger.info("SensoryInputProcessor initialized")
    
    async def process(self, raw_input: Union[str, Dict, Any], 
                     modality: str = "text",
                     source: str = "user") -> ProcessedInput:
        """
        处理原始输入
        
        Args:
            raw_input: 原始输入数据
            modality: 输入模态类型
            source: 输入来源
            
        Returns:
            ProcessedInput: 处理后的输入对象
        """
        try:
            # 创建输入对象
            sensory_input = SensoryInput(
                raw_data=raw_input,
                modality=modality,
                source=source
            )
            
            # 验证输入
            if not self._validate_input(sensory_input):
                return ProcessedInput(
                    original=sensory_input,
                    is_valid=False,
                    error_message="Input validation failed"
                )
            
            # 根据模态类型处理
            if modality == "text":
                processed = await self._process_text(sensory_input)
            elif modality == "image":
                processed = await self._process_image(sensory_input)
            elif modality == "audio":
                processed = await self._process_audio(sensory_input)
            else:
                processed = ProcessedInput(
                    original=sensory_input,
                    is_valid=False,
                    error_message=f"Unsupported modality: {modality}"
                )
            
            self.processed_count += 1
            logger.debug(f"Processed {modality} input from {source}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return ProcessedInput(
                original=SensoryInput(raw_data=raw_input, modality=modality),
                is_valid=False,
                error_message=str(e)
            )
    
    def _validate_input(self, input_data: SensoryInput) -> bool:
        """验证输入数据"""
        if input_data.raw_data is None:
            return False
        
        if input_data.modality == "text":
            text = str(input_data.raw_data)
            if len(text) > self.config.text_max_length:
                logger.warning(f"Input text too long: {len(text)} chars")
                return False
        
        return True
    
    async def _process_text(self, input_data: SensoryInput) -> ProcessedInput:
        """处理文本输入"""
        text = str(input_data.raw_data).strip()
        
        # 基础清洗
        text = self._sanitize_text(text)
        
        # 实体提取（简化版）
        entities = self._extract_basic_entities(text)
        
        # 情感分析（简化版）
        sentiment = self._basic_sentiment(text)
        
        return ProcessedInput(
            original=input_data,
            normalized_text=text,
            extracted_entities=entities,
            sentiment_score=sentiment,
            features={"length": len(text), "word_count": len(text.split())}
        )
    
    async def _process_image(self, input_data: SensoryInput) -> ProcessedInput:
        """处理图像输入（占位实现）"""
        logger.info("Image processing not yet implemented")
        return ProcessedInput(
            original=input_data,
            normalized_text="[Image input]",
            features={"modality": "image"}
        )
    
    async def _process_audio(self, input_data: SensoryInput) -> ProcessedInput:
        """处理音频输入（占位实现）"""
        logger.info("Audio processing not yet implemented")
        return ProcessedInput(
            original=input_data,
            normalized_text="[Audio input]",
            features={"modality": "audio"}
        )
    
    def _sanitize_text(self, text: str) -> str:
        """文本清洗"""
        # 移除多余空白
        text = " ".join(text.split())
        return text
    
    def _extract_basic_entities(self, text: str) -> List[Dict[str, Any]]:
        """基础实体提取"""
        entities = []
        # 简单关键词提取（后续可接入NLP模型）
        words = text.split()
        for word in words:
            if word[0].isupper() and len(word) > 1:
                entities.append({"text": word, "type": "potential_entity"})
        return entities
    
    def _basic_sentiment(self, text: str) -> float:
        """基础情感分析"""
        positive_words = {"好", "棒", "优秀", "喜欢", "开心", "快乐"}
        negative_words = {"坏", "差", "糟糕", "讨厌", "难过", "悲伤"}
        
        score = 0.0
        for word in text:
            if word in positive_words:
                score += 0.1
            elif word in negative_words:
                score -= 0.1
        
        return max(-1.0, min(1.0, score))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "processed_count": self.processed_count,
            "buffer_size": len(self.input_buffer),
            "config": {
                "buffer_size": self.config.input_buffer_size,
                "max_concurrent": self.config.max_concurrent_inputs
            }
        }
