"""
HyperBrain 核心大脑类

整合所有8个核心认知层，实现层间通信、数据流管理和系统生命周期管理。

架构：
- 感知层 (Sensory): 信息输入与预处理
- 记忆层 (Memory): 信息存储与检索
- 认知层 (Cognitive): 思维与推理
- 学习层 (Learning): 知识获取与更新
- 进化层 (Evolution): 自我优化与适应
- 情感层 (Emotional): 情感计算与表达
- 执行层 (Execution): 行动执行与反馈
- 意识层 (Consciousness): 自我意识与元认知

数据流：
输入 -> 感知层 -> 记忆层 -> 认知层 -> 意识层 -> 执行层 -> 输出
                ^         ^          ^
                |         |          |
              情感层    学习层     进化层
"""

import asyncio
import signal
import sys
import threading
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from hyperbrain.core.config import Config, get_config
from hyperbrain.core.logger import get_logger, setup_logging

from hyperbrain.layers.sensory.sensory_manager import SensoryManager
from hyperbrain.layers.memory.memory_manager import MemoryManager
from hyperbrain.layers.cognitive.cognitive_manager import CognitiveManager
from hyperbrain.layers.learning.learning_manager import LearningManager
from hyperbrain.layers.evolution.evolution_manager import EvolutionManager
from hyperbrain.layers.emotional.emotion_manager import EmotionManager
from hyperbrain.layers.execution.execution_manager import ExecutionManager
from hyperbrain.layers.consciousness.consciousness_manager import ConsciousnessManager

from hyperbrain.models.model_manager import ModelManager, get_model_manager
from hyperbrain.database.sqlite_manager import SQLiteManager
from hyperbrain.database.vector_store import VectorStore

logger = get_logger("brain")


class SystemState(Enum):
    """系统状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool = True
    content: Any = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0
    layers_involved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainStats:
    """大脑统计信息"""
    system_state: str = "unknown"
    uptime_seconds: float = 0.0
    total_inputs_processed: int = 0
    total_outputs_generated: int = 0
    average_processing_time_ms: float = 0.0
    error_count: int = 0
    layer_stats: Dict[str, Any] = field(default_factory=dict)
    memory_usage: Dict[str, int] = field(default_factory=dict)


class LayerCommunicator:
    """层间通信器
    
    实现发布-订阅模式，支持层间异步通信。
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._message_queue: Optional[asyncio.Queue] = None
        self._lock = threading.RLock()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅"""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    cb for cb in self._subscribers[event_type]
                    if cb != callback
                ]
    
    async def publish(self, event_type: str, data: Any, source: str = "") -> None:
        """发布事件"""
        if self._message_queue is None:
            logger.warning(f"LayerCommunicator not started, dropping event: {event_type}")
            return
        await self._message_queue.put({
            "type": event_type,
            "data": data,
            "source": source,
            "timestamp": time.time()
        })
    
    async def start(self) -> None:
        """启动消息分发"""
        if self._running:
            logger.warning("LayerCommunicator already started")
            return
        self._message_queue = asyncio.Queue()
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())
        logger.info("LayerCommunicator started")
    
    async def stop(self) -> None:
        """停止消息分发"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._message_queue = None
        logger.info("LayerCommunicator stopped")
    
    def _safe_create_task(self, coro, name: str = "") -> asyncio.Task:
        """创建 asyncio task 并添加异常日志回调（spec comprehensive-debug-v2）"""
        task = asyncio.create_task(coro)
        def _on_done(t: asyncio.Task):
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.error(f"Task {name or coro} failed: {exc}", exc_info=exc)
        task.add_done_callback(_on_done)
        return task
    
    async def _dispatch_loop(self) -> None:
        """消息分发循环"""
        while self._running:
            try:
                if self._message_queue is None:
                    await asyncio.sleep(0.1)
                    continue
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )
                event_type = message["type"]
                
                with self._lock:
                    callbacks = self._subscribers.get(event_type, []).copy()
                
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            self._safe_create_task(
                                callback(message),
                                name=f"layer_callback:{event_type}",
                            )
                        else:
                            callback(message)
                    except Exception as e:
                        logger.error(f"Callback error for {event_type}: {e}")
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Dispatch loop error: {e}")


class Brain:
    """
    HyperBrain 核心大脑类
    
    整合所有8个核心认知层，提供统一的系统接口。
    
    功能：
    1. 层间通信管理
    2. 数据流管理
    3. 系统生命周期管理
    4. 配置加载和初始化
    5. 错误处理和恢复
    
    Attributes:
        config: 系统配置
        state: 系统状态
        sensory: 感知层管理器
        memory: 记忆层管理器
        cognitive: 认知层管理器
        learning: 学习层管理器
        evolution: 进化层管理器
        emotional: 情感层管理器
        execution: 执行层管理器
        consciousness: 意识层管理器
        model_manager: 模型管理器
        db: SQLite数据库
        vector_store: 向量存储
        communicator: 层间通信器
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        enable_logging: bool = True,
        log_level: str = "INFO"
    ):
        self.config = config or get_config()
        self.state = SystemState.INITIALIZING
        self._start_time = time.time()
        self._session_id = str(uuid.uuid4())
        
        # 统计
        self._total_inputs = 0
        self._total_outputs = 0
        self._processing_times: List[float] = []
        self._error_count = 0
        self._lock = threading.RLock()
        
        # 设置日志
        if enable_logging:
            setup_logging(log_level=log_level)
        
        # 层间通信器
        self.communicator = LayerCommunicator()
        
        # 初始化各层（按依赖顺序）
        logger.info("Initializing Brain layers...")
        
        # 1. 数据库层（最底层依赖）
        self.db = SQLiteManager()
        self.vector_store = VectorStore()
        
        # 2. 记忆层
        self.memory = MemoryManager(
            db_path=self.config.memory.db_path,
            vector_dim=self.config.memory.vector_dim
        )
        
        # 3. 感知层
        self.sensory = SensoryManager(memory_manager=self.memory)
        
        # 4. 情感层
        self.emotional = EmotionManager(memory_manager=self.memory)
        
        # 5. 认知层
        self.cognitive = CognitiveManager(memory_manager=self.memory)
        
        # 6. 学习层
        self.learning = LearningManager()
        
        # 7. 执行层
        self.execution = ExecutionManager()
        
        # 8. 意识层
        self.consciousness = ConsciousnessManager(
            emotional_manager=self.emotional,
            cognitive_manager=self.cognitive,
            memory_manager=self.memory
        )
        
        # 9. 进化层
        self.evolution = EvolutionManager()
        
        # 10. 模型管理器
        self.model_manager = get_model_manager()

        # 11. SkillLoader（Hermes 自动创建技能需要）
        from hyperbrain.skills.loader import SkillLoader
        self.skill_loader = SkillLoader()
        try:
            self.skill_loader.load_skills()
        except Exception as e:
            logger.warning(f"skill loader init failed: {e}")

        # 12. Hermes 三件套（hermes.* 子包）
        self._init_hermes()

        # 连接各层
        self._connect_layers()
        
        # 注册层间通信事件
        self._register_communication_events()
        
        # 信号处理
        self._setup_signal_handlers()
        
        logger.info(f"Brain initialized with session_id={self._session_id}")

    # ========== Hermes 子系统 ==========

    def _init_hermes(self) -> None:
        """按需初始化 Hermes 三件套（auto_skill / nudge / trajectory）。"""
        self.auto_skill_generator = None
        self.nudge_scheduler = None
        self.trajectory_pipeline = None

        cfg = self.config.hermes
        if not (cfg.auto_skill.enabled or cfg.nudge.enabled or cfg.trajectory.enabled):
            logger.info("Hermes all subsystems disabled by config")
            return

        try:
            if cfg.auto_skill.enabled:
                from hyperbrain.hermes.auto_skill import AutoSkillGenerator
                self.auto_skill_generator = AutoSkillGenerator(
                    db=self.db,
                    model_manager=self.model_manager,
                    skill_loader=self.skill_loader,
                    config=cfg.auto_skill,
                )
        except Exception as e:
            logger.warning(f"AutoSkillGenerator init failed: {e}")

        try:
            if cfg.trajectory.enabled:
                from hyperbrain.hermes.trajectory import TrajectoryPipeline
                self.trajectory_pipeline = TrajectoryPipeline(
                    db=self.db,
                    model_manager=self.model_manager,
                    config=cfg.trajectory,
                    trainer_config=cfg.trainer,
                )
        except Exception as e:
            logger.warning(f"TrajectoryPipeline init failed: {e}")

        try:
            if cfg.nudge.enabled:
                from hyperbrain.hermes.nudge import NudgeScheduler, register_default_jobs
                self.nudge_scheduler = NudgeScheduler(
                    brain=self,
                    config=cfg.nudge,
                    db=self.db,
                )
                register_default_jobs(self.nudge_scheduler, self)
        except Exception as e:
            logger.warning(f"NudgeScheduler init failed: {e}")

    def _hermes_post_process(
        self,
        *,
        user_input: str,
        response: Optional[str],
        success: bool,
        latency_ms: float,
        skills_invoked: Optional[list] = None,
        error: Optional[str] = None,
    ) -> None:
        """Brain.process 末尾调一次；trajectory 写入 + pattern 记录。"""
        # 1) Trajectory
        if self.trajectory_pipeline is not None:
            try:
                self.trajectory_pipeline.collector.record(
                    session_id=self._session_id,
                    user_input=user_input or "",
                    model_response=response,
                    skills_invoked=skills_invoked or [],
                    latency_ms=float(latency_ms or 0.0),
                    success=bool(success),
                    error=error,
                )
            except Exception as e:  # noqa: BLE001
                logger.debug(f"hermes trajectory record failed: {e}")

        # 2) Pattern（供后续 auto_skill_generator 复用）
        if self.auto_skill_generator is not None:
            try:
                self.auto_skill_generator.record(
                    user_input=user_input or "",
                    response=response or "",
                    session_id=self._session_id,
                    skills_invoked=skills_invoked or [],
                    success=bool(success),
                )
            except Exception as e:  # noqa: BLE001
                logger.debug(f"hermes pattern record failed: {e}")

    def _connect_layers(self) -> None:
        """连接各层之间的引用"""
        # 认知层 -> 记忆层
        self.cognitive.set_memory_manager(self.memory)

        # 感知层 -> 记忆层
        self.sensory.set_memory_manager(self.memory)

        # 进化层连接
        self.evolution.connect_memory_system(self.memory)
        self.evolution.connect_cognitive_system(self.cognitive)
        self.evolution.connect_learning_system(self.learning)

        # 情感层连接
        self.emotional.memory_manager = self.memory
        self.emotional.cognitive_manager = self.cognitive
        
        # 意识层连接
        self.consciousness.memory_manager = self.memory
        
        logger.info("Layers connected")
    
    def _register_communication_events(self) -> None:
        """注册层间通信事件"""
        # 感知事件 -> 记忆存储
        async def on_perception(message):
            data = message["data"]
            if isinstance(data, dict) and "perception" in data:
                self.memory.process_input(
                    content=data["perception"],
                    modality="sensory",
                    source="sensory_layer"
                )
        
        # 情感事件 -> 意识层
        async def on_emotion(message):
            data = message["data"]
            if isinstance(data, dict) and "emotional_state" in data:
                self.consciousness.integrate_emotional_input(
                    data["emotional_state"]
                )
        
        # 认知事件 -> 学习层
        async def on_cognition(message):
            data = message["data"]
            if isinstance(data, dict) and "cognitive_result" in data:
                self.learning.learn(
                    content=data["cognitive_result"],
                    context=None
                )
        
        # 错误事件 -> 进化层
        async def on_error(message):
            data = message["data"]
            if isinstance(data, dict) and "error" in data:
                from hyperbrain.layers.evolution.error_analysis import ErrorSeverity
                self.evolution.record_error(
                    description=data["error"],
                    severity=ErrorSeverity.MEDIUM,
                    context=data.get("context", {})
                )
        
        self.communicator.subscribe("perception", on_perception)
        self.communicator.subscribe("emotion", on_emotion)
        self.communicator.subscribe("cognition", on_cognition)
        self.communicator.subscribe("error", on_error)
        
        logger.info("Communication events registered")
    
    def _safe_create_task(self, coro, name: str = "") -> asyncio.Task:
        """创建 asyncio task 并添加异常日志回调（spec comprehensive-debug-v2）"""
        task = asyncio.create_task(coro)
        def _on_done(t: asyncio.Task):
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.error(f"Task {name or coro} failed: {exc}", exc_info=exc)
        task.add_done_callback(_on_done)
        return task
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self._safe_create_task(self.shutdown(), name="brain_shutdown")
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (AttributeError, ValueError):
            pass
    
    # ========== 生命周期管理 ==========
    
    async def initialize(self) -> bool:
        """初始化系统
        
        Returns:
            bool: 是否成功
        """
        try:
            self.state = SystemState.INITIALIZING
            logger.info("Initializing system...")
            
            # 启动层间通信
            await self.communicator.start()
            
            # 初始化感知层
            await self.sensory.initialize()
            
            # 初始化执行层
            await self.execution.initialize()
            
            # 初始化模型
            await self.model_manager.initialize_all()
            
            # 自动发现本地模型
            await self.model_manager.discover_local_models()
            
            # 加载向量数据
            self.vector_store.load()
            
            self.state = SystemState.READY
            logger.info("System initialization complete")
            
            # 记录启动事件
            self.db.log_event(
                "system_start",
                f"System initialized with session {self._session_id}",
                {"session_id": self._session_id}
            )
            
            return True
            
        except Exception as e:
            self.state = SystemState.ERROR
            logger.error(f"Initialization failed: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    async def start(self) -> bool:
        """启动系统运行

        Returns:
            bool: 是否成功
        """
        if self.state not in [SystemState.READY, SystemState.PAUSED]:
            logger.error(f"Cannot start from state: {self.state}")
            return False

        self.state = SystemState.RUNNING
        logger.info("System started")

        # 启动后台任务
        self._background_tasks = [
            asyncio.create_task(self._auto_consolidation_loop()),
            asyncio.create_task(self._auto_evolution_loop()),
            asyncio.create_task(self._consciousness_cycle_loop()),
        ]

        # 启动 Hermes NudgeScheduler（如已启用）
        if self.nudge_scheduler is not None:
            try:
                await self.nudge_scheduler.start()
            except Exception as e:
                logger.warning(f"nudge scheduler start failed: {e}")

        return True
    
    async def pause(self) -> None:
        """暂停系统"""
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            logger.info("System paused")
    
    async def resume(self) -> None:
        """恢复系统"""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            logger.info("System resumed")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表板所需的统一数据快照

        供 UI 组件（记忆面板、认知面板、监控面板）调用。
        返回的字典包含四部分：
        - ``memory``: 记忆系统统计
        - ``abilities``: 认知能力水平（0-100）
        - ``emotion``: 情感状态
        - ``tasks``: 任务列表
        - ``cognition_chain``: 最近的思维链步骤

        Returns:
            Dict[str, Any]: 仪表板数据
        """
        import time

        try:
            memory_stats = self.memory.get_stats() if hasattr(self.memory, 'get_stats') else {}
        except Exception as e:
            logger.debug(f"get_dashboard_data: memory stats failed: {e}")
            memory_stats = {}

        try:
            cognitive_stats = self.cognitive.get_stats() if hasattr(self.cognitive, 'get_stats') else {}
        except Exception as e:
            logger.debug(f"get_dashboard_data: cognitive stats failed: {e}")
            cognitive_stats = {}

        try:
            learning_stats = self.learning.get_stats() if hasattr(self.learning, 'get_stats') else {}
        except Exception as e:
            logger.debug(f"get_dashboard_data: learning stats failed: {e}")
            learning_stats = {}

        try:
            emotional_stats = self.emotional.get_stats() if hasattr(self.emotional, 'get_stats') else {}
        except Exception as e:
            logger.debug(f"get_dashboard_data: emotional stats failed: {e}")
            emotional_stats = {}

        try:
            execution_stats = self.execution.get_stats() if hasattr(self.execution, 'get_stats') else {}
        except Exception as e:
            logger.debug(f"get_dashboard_data: execution stats failed: {e}")
            execution_stats = {}

        # 推导认知能力水平（0-100）
        abilities = self._derive_abilities(cognitive_stats, learning_stats)

        # 当前情感
        try:
            current_emotion = self.emotional.get_current_emotion()
            if hasattr(current_emotion, 'to_dict'):
                emotion_data = current_emotion.to_dict()
            elif isinstance(current_emotion, dict):
                emotion_data = current_emotion
            else:
                emotion_data = {
                    "name": "平静",
                    "intensity": 0.0,
                    "valence": 0.0,
                    "pleasure": 0.5,
                    "arousal": 0.0,
                    "dominance": 0.0,
                }
        except Exception:
            emotion_data = {
                "name": "平静",
                "intensity": 0.0,
                "valence": "中性",
                "pleasure": 0.5,
                "arousal": 0.0,
                "dominance": 0.0,
            }

        # 情感历史
        try:
            emotion_history = []
            if hasattr(self.emotional, 'get_emotion_history'):
                emotion_history = self.emotional.get_emotion_history(limit=20)
            elif hasattr(self.emotional, 'emotion_memory'):
                emotion_history = self.emotional.emotion_memory.get_recent(20)
        except Exception:
            emotion_history = []

        # 任务列表
        try:
            tasks = []
            if hasattr(self.execution, 'get_active_tasks'):
                tasks = self.execution.get_active_tasks()
            elif hasattr(self.execution, 'task_executor') and hasattr(self.execution.task_executor, 'get_all_tasks'):
                tasks = self.execution.task_executor.get_all_tasks()
        except Exception:
            tasks = []

        # 思维链（最近推理）
        try:
            cognition_chain = []
            if hasattr(self.cognitive, 'reasoning_engine') and hasattr(self.cognitive.reasoning_engine, 'get_recent_chains'):
                cognition_chain = self.cognitive.reasoning_engine.get_recent_chains(limit=10)
            elif hasattr(self, '_recent_cognition_steps'):
                cognition_chain = self._recent_cognition_steps[-10:]
        except Exception:
            cognition_chain = []

        return {
            "timestamp": time.time(),
            "memory": memory_stats,
            "abilities": abilities,
            "emotion": emotion_data,
            "emotion_history": emotion_history,
            "tasks": tasks,
            "cognition_chain": cognition_chain,
            "learning": learning_stats,
            "cognitive": cognitive_stats,
            "execution": execution_stats,
            "session_id": getattr(self, '_session_id', None),
        }

    def _derive_abilities(
        self,
        cognitive_stats: Dict[str, Any],
        learning_stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        从认知/学习统计中推导能力水平（0-100）

        能力包括：
        - 推理能力（reasoning）
        - 学习能力（learning）
        - 记忆能力（memory）
        - 注意力（attention）
        - 规划能力（planning）
        - 问题解决（problem_solving）
        - 创造力（creativity）
        - 同理心（empathy）
        - 沟通能力（communication）
        """
        # 基础值（系统启动即有）
        abilities = {
            "reasoning": 50.0,
            "learning": 50.0,
            "memory": 50.0,
            "attention": 50.0,
            "planning": 50.0,
            "problem_solving": 50.0,
            "creativity": 50.0,
            "empathy": 50.0,
            "communication": 50.0,
        }

        # 从认知统计中增加推理/问题解决/规划
        try:
            reasoning_stats = cognitive_stats.get("reasoning", {}) or {}
            total_reasoning = reasoning_stats.get("total_reasoning_count", 0) or 0
            abilities["reasoning"] = min(100, 50 + min(total_reasoning, 50))

            ps_stats = cognitive_stats.get("problem_solving", {}) or {}
            total_problems = ps_stats.get("total_problems", 0) or 0
            abilities["problem_solving"] = min(100, 50 + min(total_problems, 50))

            planning_stats = cognitive_stats.get("planning", {}) or {}
            total_plans = planning_stats.get("total_plans", 0) or 0
            abilities["planning"] = min(100, 50 + min(total_plans, 50))
        except Exception:
            pass

        # 从学习统计中增加学习能力
        try:
            total_learned = learning_stats.get("total_learned", 0) or learning_stats.get("items_learned", 0) or 0
            abilities["learning"] = min(100, 50 + min(total_learned, 50))
        except Exception:
            pass

        # 记忆能力：从记忆系统统计
        try:
            memory_stats = self.memory.get_stats() if hasattr(self, 'memory') else {}
            ltm = memory_stats.get("long_term_memory", {}) or {}
            total_memories = ltm.get("total_memories", 0) or 0
            # 记忆能力与记忆数对数相关
            import math
            abilities["memory"] = min(100, 50 + min(int(math.log10(max(total_memories, 1)) * 20), 50))
        except Exception:
            pass

        # 注意力/创造力/同理心/沟通能力：基于交互次数的合理估值
        try:
            # 注意力 = 1 - 误差率
            error_count = 0
            if hasattr(self, 'evolution') and hasattr(self.evolution, 'error_count'):
                error_count = self.evolution.error_count
            abilities["attention"] = max(30, 100 - min(error_count, 70))

            # 沟通能力：基于已处理的对话数
            abilities["communication"] = min(100, 50 + min(int(getattr(self, '_interaction_count', 0) / 2), 50))

            # 同理心/创造力：基础值
            abilities["empathy"] = min(100, 50 + min(int(getattr(self, '_interaction_count', 0) / 4), 50))
            abilities["creativity"] = min(100, 50 + min(int(getattr(self, '_interaction_count', 0) / 5), 50))
        except Exception:
            pass

        return abilities

    def record_interaction(self) -> None:
        """记录一次交互（用于能力统计）"""
        self._interaction_count = getattr(self, '_interaction_count', 0) + 1

    async def shutdown(self) -> None:
        """关闭系统"""
        if self.state == SystemState.SHUTTING_DOWN:
            return

        self.state = SystemState.SHUTTING_DOWN
        logger.info("Shutting down system...")

        # 取消后台任务
        if hasattr(self, '_background_tasks'):
            for task in self._background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # 停止 Hermes NudgeScheduler（graceful）
        if self.nudge_scheduler is not None:
            try:
                await self.nudge_scheduler.stop(timeout=10.0)
            except Exception as e:
                logger.warning(f"nudge scheduler stop failed: {e}")

        # 停止层间通信
        await self.communicator.stop()

        # 关闭执行层
        await self.execution.shutdown()

        # 记忆巩固
        self.memory.consolidate(force=True)
        self.memory.shutdown()

        # 保存向量数据
        self.vector_store.save()
        
        # 关闭模型
        await self.model_manager.close_all()
        
        # 记录关闭事件
        self.db.log_event(
            "system_shutdown",
            f"System shutdown after {self.get_uptime():.1f} seconds",
            {"uptime": self.get_uptime(), "session_id": self._session_id}
        )
        
        logger.info("System shutdown complete")
    
    @asynccontextmanager
    async def session(self):
        """上下文管理器，自动管理生命周期"""
        try:
            await self.initialize()
            await self.start()
            yield self
        finally:
            await self.shutdown()
    
    # ========== 核心处理流程 ==========
    
    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        处理用户输入（完整流程）
        
        数据流：
        1. 感知层处理输入
        2. 情感层更新状态
        3. 记忆层检索相关记忆
        4. 认知层进行推理
        5. 意识层进行决策
        6. 执行层生成输出
        7. 记忆层存储新信息
        8. 学习层从交互中学习
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            ProcessingResult: 处理结果
        """
        start_time = time.time()
        layers_involved = []
        
        try:
            with self._lock:
                self._total_inputs += 1
            
            # 1. 感知层处理
            perception = await self.sensory.perceive(
                content=user_input,
                modality="text",
                source="user",
                metadata=context
            )
            layers_involved.append("sensory")
            
            if not perception.processed_input.is_valid:
                return ProcessingResult(
                    success=False,
                    error=perception.processed_input.error_message,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    layers_involved=layers_involved
                )
            
            # 2. 情感层处理
            sentiment_score = 0.0
            if perception.processed_input.text_features:
                sentiment_score = perception.processed_input.text_features.sentiment_score
            
            emotional_result = self.emotional.process_input({
                "sentiment_score": sentiment_score,
                "event_type": "user_input",
                "context": {"input": user_input[:100]}
            })
            layers_involved.append("emotional")
            
            # 3. 记忆层检索
            relevant_memories = self.memory.retrieve(
                query=user_input,
                top_k=5
            )
            memory_context = "\n".join([
                str(m.memory.content)[:200] for m in relevant_memories
                if m.memory.content
            ])
            layers_involved.append("memory")
            
            # 4. 认知层推理
            cognitive_result = self.cognitive.think(
                problem=user_input,
                context={
                    "memories": memory_context,
                    "emotional_state": emotional_result
                }
            )
            layers_involved.append("cognitive")
            
            # 5. 意识层决策
            consciousness_result = self.consciousness.make_decision(
                options=["respond", "ask_clarification", "decline"],
                context={
                    "input": user_input,
                    "cognitive_result": cognitive_result
                }
            )
            layers_involved.append("consciousness")
            
            # 6. 构建系统提示
            system_prompt = self._build_system_prompt(
                memory_context=memory_context,
                emotional_state=emotional_result,
                cognitive_result=cognitive_result
            )
            
            # 7. 调用大模型生成响应
            from hyperbrain.models.base import ChatMessage
            messages = [ChatMessage(role="system", content=system_prompt)]

            # 添加历史对话上下文（最近10轮）
            try:
                history = self.db.get_conversation_history(self._session_id, limit=20)
                # 历史是按时间倒序的，需要反转
                for msg in reversed(history):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content and role in ("user", "assistant"):
                        messages.append(ChatMessage(role=role, content=content))
            except Exception as e:
                logger.debug(f"Failed to load conversation history: {e}")

            # 添加当前用户输入
            messages.append(ChatMessage(role="user", content=user_input))

            # spec fix-ollama-thinking-timeout: 优先走降级链（fallback_models 非空时）
            fallback_models = []
            try:
                fb = getattr(self.config.model, 'fallback_models', None)
                if isinstance(fb, (list, tuple)):
                    fallback_models = list(fb)
            except Exception:
                fallback_models = []

            if fallback_models:
                try:
                    model_response = await self.model_manager.chat_with_fallback(
                        messages=messages,
                        primary_model="ollama_default",
                        fallback_models=fallback_models,
                    )
                except Exception as fb_err:
                    logger.warning(f"chat_with_fallback failed: {fb_err}; falling back to plain chat")
                    model_response = await self.model_manager.chat(messages)
            else:
                model_response = await self.model_manager.chat(messages)
            # spec show-thinking-process: 提取 thinking 字段（用于 metadata 透传，不写入长期记忆）
            thinking_content = getattr(model_response, 'thinking', '') or ''
            response_content = model_response.content
            layers_involved.append("model")
            
            # 8. 执行层处理输出
            from hyperbrain.layers.execution.execution_manager import ExecutionRequest
            output_request = await self.execution.execute(
                ExecutionRequest(
                    request_type="output",
                    content=response_content,
                    parameters={"output_type": "text", "content": response_content}
                )
            )
            layers_involved.append("execution")
            
            # 9. 存储到记忆
            # 9.1 写入工作记忆（短期记忆 / 工作记忆）
            try:
                if hasattr(self.memory, 'working_memory') and self.memory.working_memory is not None:
                    self.memory.working_memory.add(
                        content=f"用户: {user_input[:200]}",
                        chunk_type="user_input",
                        priority=0.7,
                        size=1,
                        source="conversation"
                    )
                    self.memory.working_memory.add(
                        content=f"AI: {response_content[:200]}",
                        chunk_type="ai_response",
                        priority=0.6,
                        size=1,
                        source="conversation"
                    )
            except Exception as e:
                logger.debug(f"working_memory add failed: {e}")
            # 9.2 写入长期记忆
            self.memory.store(
                content={
                    "input": user_input,
                    "output": response_content,
                    "emotional_state": emotional_result,
                    "cognitive_result": cognitive_result
                },
                importance=0.6,
                context_tags=["conversation", "user_interaction"],
                metadata={
                    "session_id": self._session_id,
                    "processing_time": (time.time() - start_time) * 1000
                }
            )
            
            # 10. 学习层学习
            self.learning.learn(
                content={
                    "input": user_input,
                    "output": response_content,
                    "feedback": "auto"
                },
                context=None
            )
            layers_involved.append("learning")

            # 10.5 记录交互次数 + 思维链
            self.record_interaction()
            try:
                if not hasattr(self, '_recent_cognition_steps'):
                    self._recent_cognition_steps = []
                self._recent_cognition_steps.append({
                    "step": "response",
                    "input": user_input[:100],
                    "output": response_content[:100],
                    "time": time.time(),
                })
                if len(self._recent_cognition_steps) > 50:
                    self._recent_cognition_steps = self._recent_cognition_steps[-50:]
            except Exception:
                pass
            
            # 11. 记录对话
            import uuid as uuid_mod
            conv_id = str(uuid_mod.uuid4())
            self.db.insert_conversation(
                conversation_id=conv_id,
                session_id=self._session_id,
                role="user",
                content=user_input
            )
            self.db.insert_conversation(
                conversation_id=str(uuid_mod.uuid4()),
                session_id=self._session_id,
                role="assistant",
                content=response_content
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            with self._lock:
                self._total_outputs += 1
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 100:
                    self._processing_times = self._processing_times[-100:]
            
            # 发布处理完成事件
            await self.communicator.publish(
                "processing_complete",
                {
                    "input": user_input[:100],
                    "output": response_content[:100],
                    "processing_time": processing_time
                },
                source="brain"
            )

            # Hermes 钩子：trajectory 采集 + pattern 记录
            self._hermes_post_process(
                user_input=user_input,
                response=response_content,
                success=True,
                latency_ms=processing_time,
                skills_invoked=layers_involved,
                error=None,
            )

            return ProcessingResult(
                success=True,
                content=response_content,
                processing_time_ms=processing_time,
                layers_involved=layers_involved,
                metadata={
                    "emotional_state": emotional_result,
                    "consciousness_decision": consciousness_result,
                    "model_used": model_response.model,
                    "thinking": thinking_content,  # spec show-thinking-process: 透传思维链
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            with self._lock:
                self._error_count += 1

            logger.error(f"Processing error: {error_msg}")
            logger.debug(traceback.format_exc())

            # Hermes 钩子：失败也记录轨迹
            try:
                self._hermes_post_process(
                    user_input=user_input,
                    response=None,
                    success=False,
                    latency_ms=processing_time,
                    skills_invoked=layers_involved,
                    error=error_msg,
                )
            except Exception:
                pass

            # 发布错误事件
            await self.communicator.publish(
                "error",
                {"error": error_msg, "input": user_input[:100]},
                source="brain"
            )
            
            return ProcessingResult(
                success=False,
                error=error_msg,
                processing_time_ms=processing_time,
                layers_involved=layers_involved
            )
    
    async def process_stream(self, user_input: str, context: Optional[Dict[str, Any]] = None):
        """
        流式处理用户输入

        spec show-thinking-process: 兼容 stream_chat() 新的 (type, text) 元组格式
        - type="thinking" / type="content" → yield 对应文本片段
        - StreamChunk(is_finished=True) → 结束信号

        Yields:
            str: 响应片段（thinking + content 拼接后逐片段 yield；目前 task 5 才接 GUI）
        """
        try:
            # 快速路径：直接调用模型流式接口
            from hyperbrain.models.base import ChatMessage

            # 构建简化提示
            system_prompt = self._build_system_prompt()
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_input)
            ]

            full_response = ""
            full_thinking = ""  # spec show-thinking-process
            async for item in self.model_manager.stream_chat(messages):
                # 兼容新元组格式和旧 StreamChunk 格式
                if isinstance(item, tuple) and len(item) == 2:
                    chunk_type, chunk_text = item
                    if chunk_type == "thinking":
                        full_thinking += chunk_text
                        continue  # thinking 不直接 yield（task 6 才在 UI 显示）
                    elif chunk_type == "content":
                        full_response += chunk_text
                        yield chunk_text
                    else:
                        # 未知 type：当作 content 处理
                        full_response += str(chunk_text)
                        yield str(chunk_text)
                else:
                    # 旧 StreamChunk 格式
                    content = getattr(item, "content", "")
                    full_response += content
                    if content:
                        yield content
                    if getattr(item, "is_finished", False):
                        break

            # 后台存储（不阻塞响应）
            self._safe_create_task(
                self._store_interaction(user_input, full_response),
                name="store_interaction",
            )

        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            yield f"[Error: {str(e)}]"
    
    async def _store_interaction(self, user_input: str, response: str) -> None:
        """后台存储交互记录"""
        try:
            # 1) 写入工作记忆（短期记忆）
            try:
                if hasattr(self.memory, 'working_memory') and self.memory.working_memory is not None:
                    self.memory.working_memory.add(
                        content=f"用户: {user_input[:200]}",
                        chunk_type="user_input",
                        priority=0.7,
                        size=1,
                        source="conversation"
                    )
                    self.memory.working_memory.add(
                        content=f"AI: {response[:200]}",
                        chunk_type="ai_response",
                        priority=0.6,
                        size=1,
                        source="conversation"
                    )
            except Exception as wm_err:
                logger.debug(f"working_memory add failed: {wm_err}")
            # 2) 写入长期记忆
            self.memory.store(
                content={"input": user_input, "output": response},
                importance=0.5,
                context_tags=["conversation"]
            )
            self.db.insert_conversation(
                conversation_id=f"conv_{self._total_inputs}",
                session_id=self._session_id,
                role="user",
                content=user_input
            )
            self.db.insert_conversation(
                conversation_id=f"conv_{self._total_inputs}_resp",
                session_id=self._session_id,
                role="assistant",
                content=response
            )
        except Exception as e:
            logger.warning(f"Background store error: {e}")
    
    def _build_system_prompt(
        self,
        memory_context: str = "",
        emotional_state: Optional[Dict] = None,
        cognitive_result: Optional[Dict] = None
    ) -> str:
        """构建系统提示"""
        emotional_info = ""
        if emotional_state:
            current = self.emotional.get_current_emotion()
            if current:
                dom, intensity = current.get("dominant", ("neutral", 0.0))
                emotional_info = f"\n当前情感: {dom} (强度: {intensity:.2f})"
        
        prompt = f"""你是 HyperBrain，一个拟人脑认知架构系统。

当前状态：
- 认知深度: {self.config.cognitive.reasoning_depth}
- 学习模式: {self.learning.get_current_mode().value}
{emotional_info}

相关记忆：
{memory_context if memory_context else "无"}

请以智能、有同理心的方式回应用户。保持对话的连贯性和上下文理解。"""
        
        return prompt
    
    # ========== 后台任务 ==========
    
    async def _auto_consolidation_loop(self) -> None:
        """自动记忆巩固循环"""
        while self.state == SystemState.RUNNING:
            try:
                await asyncio.sleep(300)  # 5分钟
                if self.state == SystemState.RUNNING:
                    consolidated = self.memory.consolidate()
                    if consolidated > 0:
                        logger.info(f"Auto-consolidated {consolidated} memories")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consolidation loop error: {e}")
    
    async def _auto_evolution_loop(self) -> None:
        """自动进化循环"""
        while self.state == SystemState.RUNNING:
            try:
                await asyncio.sleep(3600)  # 1小时
                if self.state == SystemState.RUNNING:
                    cycle = self.evolution.auto_evolve()
                    if cycle:
                        logger.info(f"Evolution cycle completed: {cycle.cycle_id}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
    
    async def _consciousness_cycle_loop(self) -> None:
        """意识周期循环"""
        while self.state == SystemState.RUNNING:
            try:
                await asyncio.sleep(60)  # 1分钟
                if self.state == SystemState.RUNNING:
                    result = self.consciousness.process_cycle()
                    logger.debug(f"Consciousness cycle: {result['cycle']}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consciousness loop error: {e}")
    
    # ========== 查询接口 ==========
    
    def get_stats(self) -> BrainStats:
        """获取系统统计信息"""
        with self._lock:
            avg_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )

            layer_stats = {
                "sensory": self.sensory.get_stats(),
                "memory": self.memory.get_stats(),
                "cognitive": self.cognitive.get_stats(),
                "learning": self.learning.get_stats(),
                "evolution": self.evolution.get_stats(),
                "emotional": self.emotional.get_stats(),
                "execution": self.execution.get_stats(),
                "consciousness": self.consciousness.get_consciousness_state(),
            }

            # Hermes 统计
            hermes_stats: Dict[str, Any] = {"enabled": False}
            try:
                if self.trajectory_pipeline is not None:
                    hermes_stats = {
                        "enabled": True,
                        **self.trajectory_pipeline.stats(),
                    }
                if self.auto_skill_generator is not None and self.skill_loader is not None:
                    try:
                        n = sum(
                            1 for n in self.skill_loader.skills  # type: ignore[attr-defined]
                            if str(n).startswith("auto_")
                        )
                    except Exception:
                        n = 0
                    hermes_stats["auto_skills_total"] = n
            except Exception as e:
                logger.debug(f"hermes stats failed: {e}")
            layer_stats["hermes"] = hermes_stats

            return BrainStats(
                system_state=self.state.value,
                uptime_seconds=self.get_uptime(),
                total_inputs_processed=self._total_inputs,
                total_outputs_generated=self._total_outputs,
                average_processing_time_ms=avg_time,
                error_count=self._error_count,
                layer_stats=layer_stats,
                memory_usage=self.memory.get_memory_flow()
            )
    
    def get_uptime(self) -> float:
        """获取运行时间"""
        return time.time() - self._start_time
    
    def get_session_id(self) -> str:
        """获取会话ID"""
        return self._session_id
    
    async def get_system_report(self) -> Dict[str, Any]:
        """获取完整系统报告"""
        stats = self.get_stats()
        
        return {
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "system_state": stats.system_state,
            "uptime_seconds": stats.uptime_seconds,
            "processing_stats": {
                "total_inputs": stats.total_inputs_processed,
                "total_outputs": stats.total_outputs_generated,
                "average_processing_time_ms": stats.average_processing_time_ms,
                "error_count": stats.error_count,
                "error_rate": (
                    stats.error_count / max(stats.total_inputs_processed, 1)
                )
            },
            "layer_stats": stats.layer_stats,
            "memory_flow": stats.memory_usage,
            "model_stats": self.model_manager.get_stats(),
            "database_stats": self.db.get_stats(),
            "consciousness_report": self.consciousness.get_integrated_report(),
            "evolution_report": self.evolution.get_comprehensive_report(),
            "learning_report": self.learning.get_learning_report(),
        }
    
    # ========== 快捷操作 ==========
    
    async def think(self, problem: str) -> Dict[str, Any]:
        """认知思考"""
        return self.cognitive.think(problem)
    
    async def learn(self, content: Any, **kwargs) -> Any:
        """学习新内容"""
        return self.learning.learn(content, **kwargs)
    
    async def reflect(self) -> Dict[str, Any]:
        """自我反思"""
        return self.consciousness.self_reflect()
    
    async def evolve(self) -> Any:
        """触发进化"""
        return self.evolution.run_evolution_cycle()
    
    def get_emotional_state(self) -> Optional[Dict[str, Any]]:
        """获取情感状态"""
        return self.emotional.get_current_emotion()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        return {
            "flow": self.memory.get_memory_flow(),
            "stats": self.memory.get_stats()
        }


# 全局Brain实例
_global_brain: Optional[Brain] = None


def get_brain(
    config: Optional[Config] = None,
    enable_logging: bool = True,
    log_level: str = "INFO"
) -> Brain:
    """获取全局Brain实例（单例模式）
    
    Args:
        config: 配置
        enable_logging: 是否启用日志
        log_level: 日志级别
        
    Returns:
        Brain: Brain实例
    """
    global _global_brain
    if _global_brain is None:
        _global_brain = Brain(config, enable_logging, log_level)
    return _global_brain


def reset_brain() -> None:
    """重置全局Brain实例"""
    global _global_brain
    _global_brain = None
