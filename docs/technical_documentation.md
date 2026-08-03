# HyperBrain 技术文档

## 目录

1. [API 接口文档](#1-api-接口文档)
2. [模块说明](#2-模块说明)
3. [数据模型](#3-数据模型)
4. [二次开发指南](#4-二次开发指南)
5. [扩展接口说明](#5-扩展接口说明)

---

## 1. API 接口文档

### 1.1 Brain 核心类

#### 初始化与生命周期

```python
from hyperbrain.core.brain import Brain, get_brain, reset_brain
from hyperbrain.core.config import get_config

# 获取配置
config = get_config()

# 创建 Brain 实例
brain = get_brain(config=config)

# 初始化
success = await brain.initialize()

# 启动
await brain.start()

# 处理输入
result = await brain.process("你好")

# 关闭
await brain.shutdown()

# 重置
reset_brain()
```

#### 主要方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `initialize` | `async def initialize() -> bool` | 初始化系统 |
| `start` | `async def start() -> None` | 启动系统 |
| `shutdown` | `async def shutdown() -> None` | 关闭系统 |
| `process` | `async def process(input_data: str) -> ProcessingResult` | 处理输入 |
| `learn` | `async def learn(content: str) -> LearningResult` | 学习新内容 |
| `think` | `async def think(problem: str) -> Dict` | 认知思考 |
| `reflect` | `async def reflect() -> Dict` | 自我反思 |
| `evolve` | `async def evolve() -> EvolutionResult` | 触发进化 |
| `get_stats` | `def get_stats() -> BrainStats` | 获取统计 |
| `get_memory_summary` | `def get_memory_summary() -> Dict` | 记忆摘要 |
| `get_emotional_state` | `def get_emotional_state() -> Dict` | 情感状态 |
| `get_system_report` | `async def get_system_report() -> Dict` | 系统报告 |

### 1.2 配置系统

```python
from hyperbrain.core.config import get_config, Config

# 获取默认配置
config = get_config()

# 从文件加载
config = get_config("config.yaml")

# 修改配置
config.model.default_model = "openai"
config.model.temperature = 0.8
config.memory.max_short_term_items = 200

# 验证配置
config.validate()

# 保存配置
from hyperbrain.core.config import save_config
save_config(config, "config.yaml")
```

### 1.3 模型管理

```python
from hyperbrain.models.model_manager import get_model_manager

# 获取模型管理器
model_manager = get_model_manager()

# 发送聊天消息
from hyperbrain.models.base import ChatMessage

messages = [
    ChatMessage(role="system", content="你是一个助手"),
    ChatMessage(role="user", content="你好")
]

response = await model_manager.chat(messages)
print(response.content)

# 获取嵌入向量
embedding = await model_manager.embed("文本内容")
print(embedding.vector)

# 流式输出
async for chunk in model_manager.chat_stream(messages):
    print(chunk.content, end="")
```

### 1.4 记忆系统

```python
from hyperbrain.layers.memory.memory_manager import MemoryManager

# 创建记忆管理器
memory = MemoryManager()

# 存储记忆
memory_id = await memory.store(
    content="重要信息",
    category="general",
    importance=0.8
)

# 检索记忆
results = await memory.retrieve(
    query="搜索内容",
    top_k=5
)

# 获取记忆流
flow = memory.get_memory_flow()
```

### 1.5 情感系统

```python
from hyperbrain.layers.emotional.emotion_manager import EmotionManager

# 创建情感管理器
emotion = EmotionManager()

# 处理输入并生成情感
emotion_state = await emotion.process_input("令人高兴的消息")

# 获取当前情感
current = emotion.get_current_emotion()

# 表达情感
expression = emotion.express()
```

---

## 2. 模块说明

### 2.1 核心模块 (hyperbrain.core)

#### brain.py
- **Brain**: 大脑核心类，整合所有认知层
- **LayerCommunicator**: 层间通信器，发布-订阅模式
- **ProcessingResult**: 处理结果数据类
- **BrainStats**: 大脑统计数据类
- **SystemState**: 系统状态枚举

#### config.py
- **Config**: 主配置类
- **ConfigManager**: 配置管理器
- **ModelConfig**: 模型配置
- **MemoryConfig**: 记忆配置
- **CognitiveConfig**: 认知配置

#### logger.py
- **setup_logging**: 初始化日志
- **get_logger**: 获取日志记录器

### 2.2 感知层 (hyperbrain.layers.sensory)

| 模块 | 类 | 功能 |
|------|-----|------|
| sensory_manager.py | SensoryManager | 感知管理器 |
| input_processor.py | InputProcessor | 输入预处理 |
| attention.py | AttentionMechanism | 注意力机制 |
| context_awareness.py | ContextAwareness | 情境感知 |
| multimodal_handler.py | MultimodalHandler | 多模态处理 |
| text_parser.py | TextParser | 文本解析 |

### 2.3 记忆层 (hyperbrain.layers.memory)

| 模块 | 类 | 功能 |
|------|-----|------|
| memory_manager.py | MemoryManager | 记忆管理器 |
| memory_models.py | MemoryItem, MemoryType | 记忆模型 |
| sensory_memory.py | SensoryMemory | 瞬时记忆 |
| short_term_memory.py | ShortTermMemory | 短期记忆 |
| working_memory.py | WorkingMemory | 工作记忆 |
| long_term_memory.py | LongTermMemory | 长期记忆 |
| consolidation.py | ConsolidationEngine | 记忆巩固 |
| retrieval.py | RetrievalEngine | 记忆检索 |
| enhancement.py | EnhancementEngine | 记忆增强 |
| forgetting.py | ForgettingEngine | 遗忘机制 |

### 2.4 认知层 (hyperbrain.layers.cognitive)

| 模块 | 类 | 功能 |
|------|-----|------|
| cognitive_manager.py | CognitiveManager | 认知管理器 |
| reasoning.py | ReasoningEngine | 逻辑推理 |
| decision_making.py | DecisionEngine | 决策引擎 |
| planning.py | PlanningEngine | 规划引擎 |
| problem_solving.py | ProblemSolver | 问题求解 |
| abstraction.py | AbstractionEngine | 抽象思维 |
| metacognition.py | MetacognitionEngine | 元认知 |

### 2.5 学习层 (hyperbrain.layers.learning)

| 模块 | 类 | 功能 |
|------|-----|------|
| learning_manager.py | LearningManager | 学习管理器 |
| infant_learning.py | InfantLearning | 婴儿学习 |
| child_learning.py | ChildLearning | 儿童学习 |
| adult_learning.py | AdultLearning | 成人学习 |
| lifelong_learning.py | LifelongLearning | 终身学习 |
| knowledge_integration.py | KnowledgeIntegration | 知识整合 |
| transfer_learning.py | TransferLearning | 迁移学习 |

### 2.6 进化层 (hyperbrain.layers.evolution)

| 模块 | 类 | 功能 |
|------|-----|------|
| evolution_manager.py | EvolutionManager | 进化管理器 |
| self_reflection.py | SelfReflection | 自我反思 |
| error_analysis.py | ErrorAnalysis | 错误分析 |
| capability_assessment.py | CapabilityAssessment | 能力评估 |
| self_optimization.py | SelfOptimization | 自我优化 |
| goal_evolution.py | GoalEvolution | 目标进化 |

### 2.7 情感层 (hyperbrain.layers.emotional)

| 模块 | 类 | 功能 |
|------|-----|------|
| emotion_manager.py | EmotionManager | 情感管理器 |
| emotion_model.py | EmotionModel | 情感模型 |
| emotion_engine.py | EmotionEngine | 情感引擎 |
| emotion_generation.py | EmotionGeneration | 情感生成 |
| emotion_expression.py | EmotionExpression | 情感表达 |
| emotion_regulation.py | EmotionRegulation | 情感调节 |
| empathy.py | EmpathyModule | 共情模块 |

### 2.8 执行层 (hyperbrain.layers.execution)

| 模块 | 类 | 功能 |
|------|-----|------|
| execution_manager.py | ExecutionManager | 执行管理器 |
| task_execution.py | TaskExecutor | 任务执行 |
| task_scheduler.py | TaskScheduler | 任务调度 |
| output_generation.py | OutputGenerator | 输出生成 |
| tool_invocation.py | ToolInvoker | 工具调用 |

### 2.9 意识层 (hyperbrain.layers.consciousness)

| 模块 | 类 | 功能 |
|------|-----|------|
| consciousness_manager.py | ConsciousnessManager | 意识管理器 |
| self_awareness.py | SelfAwareness | 自我意识 |
| self_knowledge.py | SelfKnowledge | 自我认知 |
| will.py | WillModule | 意志模块 |
| value_system.py | ValueSystem | 价值体系 |
| goal_system.py | GoalSystem | 目标体系 |

---

## 3. 数据模型

### 3.1 核心数据类

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class MemoryType(Enum):
    DECLARATIVE = "declarative"      # 陈述性记忆
    PROCEDURAL = "procedural"        # 程序性记忆
    EPISODIC = "episodic"            # 情景记忆
    EMOTIONAL = "emotional"          # 情感记忆

class EmotionType(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"

@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    memory_type: MemoryType
    importance: float = 0.5
    emotional_tags: List[EmotionType] = field(default_factory=list)
    created_at: float = 0.0
    last_accessed: float = 0.0
    access_count: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmotionState:
    """情感状态"""
    primary_emotion: EmotionType
    intensity: float = 0.5
    valence: float = 0.0          # 愉悦度
    arousal: float = 0.0          # 唤醒度
    dominance: float = 0.0        # 支配度
    timestamp: float = 0.0

@dataclass
class CognitiveProcess:
    """认知过程"""
    process_id: str
    process_type: str
    input_data: Any
    output_data: Any
    reasoning_chain: List[str] = field(default_factory=list)
    confidence: float = 0.0
    duration_ms: float = 0.0

@dataclass
class LearningResult:
    """学习结果"""
    success: bool
    knowledge_id: Optional[str] = None
    mode_used: str = ""
    integration_score: float = 0.0
    related_memories: List[str] = field(default_factory=list)
```

### 3.2 配置数据类

```python
@dataclass
class ModelConfig:
    """模型配置"""
    default_model: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_attempts: int = 3
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-sonnet"
    google_api_key: str = ""
    google_model: str = "gemini-pro"
    ollama_model: str = "llama2"
    ollama_base_url: str = "http://localhost:11434"

@dataclass
class MemoryConfig:
    """记忆配置"""
    db_path: str = "memory.db"
    vector_dim: int = 1536
    max_short_term_items: int = 100
    consolidation_interval: int = 300
    importance_threshold: float = 0.5
```

---

## 4. 二次开发指南

### 4.1 开发环境搭建

```bash
# 1. 克隆仓库
git clone <repository-url>
cd hyperbrain

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-qt

# 4. 运行测试
pytest
```

### 4.2 添加新的认知层模块

```python
# hyperbrain/layers/custom/custom_module.py
from hyperbrain.core.logger import get_logger

logger = get_logger("layers.custom")

class CustomModule:
    """自定义模块
    
    实现自定义的认知功能。
    """
    
    def __init__(self, config=None):
        self.config = config
        self._initialized = False
        
    async def initialize(self) -> bool:
        """初始化模块"""
        try:
            # 初始化逻辑
            self._initialized = True
            logger.info("CustomModule initialized")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def process(self, data: Any) -> Any:
        """处理数据"""
        if not self._initialized:
            raise RuntimeError("Module not initialized")
        
        # 处理逻辑
        result = await self._do_processing(data)
        return result
    
    async def _do_processing(self, data: Any) -> Any:
        """实际处理逻辑"""
        pass
    
    async def shutdown(self) -> None:
        """关闭模块"""
        self._initialized = False
        logger.info("CustomModule shutdown")
```

### 4.3 添加新的大模型支持

```python
# hyperbrain/models/custom_model.py
from typing import AsyncGenerator, List
from hyperbrain.models.base import (
    BaseModel, ChatMessage, ModelResponse, 
    StreamChunk, EmbeddingResponse
)

class CustomModel(BaseModel):
    """自定义模型实现"""
    
    PROVIDER = "custom"
    
    def __init__(self, config):
        super().__init__(config)
        self.client = None
    
    async def initialize(self) -> bool:
        """初始化模型客户端"""
        # 初始化 API 客户端
        return True
    
    async def chat(self, messages: List[ChatMessage]) -> ModelResponse:
        """发送聊天请求"""
        # 实现聊天逻辑
        return ModelResponse(
            content="响应内容",
            model=self.config.model_name,
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
    
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """流式聊天"""
        # 实现流式输出
        yield StreamChunk(content="流式", is_done=False)
        yield StreamChunk(content="", is_done=True)
    
    async def embed(self, text: str) -> EmbeddingResponse:
        """获取嵌入向量"""
        # 实现嵌入逻辑
        return EmbeddingResponse(vector=[0.1, 0.2, 0.3])
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True
```

### 4.4 注册新模型

```python
# hyperbrain/models/model_manager.py
from .custom_model import CustomModel

# 在 _MODEL_CLASS_MAP 中添加
_MODEL_CLASS_MAP[ModelProvider.CUSTOM] = CustomModel
```

### 4.5 添加 UI 组件

```python
# hyperbrain/ui/custom_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class CustomWidget(QWidget):
    """自定义 UI 组件"""
    
    def __init__(self, brain, parent=None):
        super().__init__(parent)
        self.brain = brain
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        
        self.label = QLabel("自定义组件")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
    
    def update_data(self, data):
        """更新数据"""
        self.label.setText(str(data))
```

---

## 5. 扩展接口说明

### 5.1 插件系统接口

```python
# 插件基类
class HyperBrainPlugin:
    """HyperBrain 插件基类"""
    
    name: str = ""
    version: str = ""
    description: str = ""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    async def on_input(self, input_data: str) -> Optional[str]:
        """处理输入前钩子"""
        return None
    
    async def on_output(self, output_data: str) -> Optional[str]:
        """处理输出后钩子"""
        return None
    
    async def on_event(self, event_type: str, data: Any) -> None:
        """事件处理"""
        pass
    
    async def shutdown(self) -> None:
        """关闭插件"""
        pass
```

### 5.2 工具调用接口

```python
# 自定义工具
class CustomTool:
    """自定义工具"""
    
    name: str = "custom_tool"
    description: str = "工具描述"
    parameters: Dict[str, Any] = {}
    
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        # 实现工具逻辑
        return {"result": "success"}
```

### 5.3 记忆存储接口

```python
# 自定义记忆存储
class CustomMemoryStore:
    """自定义记忆存储后端"""
    
    async def store(self, item: MemoryItem) -> str:
        """存储记忆"""
        pass
    
    async def retrieve(self, query: str, top_k: int = 10) -> List[MemoryItem]:
        """检索记忆"""
        pass
    
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
    
    async def update(self, memory_id: str, updates: Dict) -> bool:
        """更新记忆"""
        pass
```

### 5.4 事件系统

```python
# 订阅事件
from hyperbrain.core.brain import get_brain

brain = get_brain()

async def on_memory_stored(event_data):
    print(f"记忆已存储: {event_data}")

brain.communicator.subscribe("memory.stored", on_memory_stored)

# 发布事件
await brain.communicator.publish(
    event_type="custom.event",
    data={"key": "value"},
    source="custom_module"
)
```

### 5.5 配置扩展

```python
# 自定义配置
from hyperbrain.core.config import Config
from dataclasses import dataclass, field

@dataclass
class CustomConfig:
    """自定义配置"""
    custom_param: str = "default"
    custom_flag: bool = True

# 注册到主配置
class Config:
    # ... 现有配置 ...
    custom: CustomConfig = field(default_factory=CustomConfig)
```

---

## 附录

### A. 事件类型列表

| 事件类型 | 说明 | 数据 |
|----------|------|------|
| `system.initialized` | 系统初始化完成 | - |
| `system.started` | 系统启动 | - |
| `system.shutdown` | 系统关闭 | - |
| `input.received` | 收到输入 | `{input: str}` |
| `output.generated` | 生成输出 | `{output: str}` |
| `memory.stored` | 记忆存储 | `{memory_id: str}` |
| `memory.retrieved` | 记忆检索 | `{query: str, results: list}` |
| `emotion.changed` | 情感变化 | `{emotion: EmotionState}` |
| `learning.completed` | 学习完成 | `{result: LearningResult}` |
| `evolution.completed` | 进化完成 | `{cycle_id: str}` |

### B. 错误代码

| 代码 | 说明 | 处理建议 |
|------|------|----------|
| `E001` | 配置错误 | 检查配置文件 |
| `E002` | 模型调用失败 | 检查 API Key 和网络 |
| `E003` | 数据库错误 | 检查数据库文件 |
| `E004` | 内存不足 | 清理记忆或增加内存 |
| `E005` | 初始化失败 | 查看日志排查 |

### C. 版本兼容性

| 版本 | Python | PyQt6 | 说明 |
|------|--------|-------|------|
| 0.2.0 | 3.11+ | 6.6+ | 当前版本 |
| 0.3.0 | 3.12+ | 6.7+ | 计划版本 |
