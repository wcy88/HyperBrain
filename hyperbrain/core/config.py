"""
HyperBrain 配置系统

支持：
- 配置文件加载
- 环境变量覆盖
- 配置验证
- 热更新
"""

import os
import json
import yaml
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from hyperbrain.core.logger import get_logger

logger = get_logger("config")


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


@dataclass
class ModelConfig:
    """模型配置"""
    default_provider: str = "ollama"
    default_model: str = "gemma2:2b"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: float = 90.0
    retry_attempts: int = 3

    # === 新增：thinking 模型 + 降级链 + 流式 + worker 超时（spec fix-ollama-thinking-timeout）===
    think: bool = True  # spec show-thinking-process: 默认为 true，允许 thinking 模型生成思维链
    fallback_models: List[str] = field(default_factory=list)
    stream: bool = True
    worker_timeout: float = 180.0  # 180 秒；thinking 模型常需 100s+，原 90s 会误报超时

    # API Keys
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: str = ""

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-sonnet"

    google_api_key: str = ""
    google_model: str = "gemini-pro"

    ollama_model: str = "gemma2:2b"
    ollama_base_url: str = "http://localhost:11434"

    def __post_init__(self):
        """确保字符串字段不为 None（spec fix-openai-base-url-null）"""
        # yaml 中 null 加载后变为 None，需转回空字符串以匹配 str 类型注解
        if self.openai_base_url is None:
            self.openai_base_url = ""
        if self.openai_api_key is None:
            self.openai_api_key = ""
        if self.anthropic_api_key is None:
            self.anthropic_api_key = ""
        if self.google_api_key is None:
            self.google_api_key = ""

    def validate(self) -> None:
        """验证配置"""
        if not 0 <= self.temperature <= 2:
            raise ConfigValidationError("temperature 必须在 0-2 之间")
        if self.max_tokens < 1 or self.max_tokens > 262144:
            raise ConfigValidationError("max_tokens 必须在 1-262144 之间")
        if self.timeout < 1 or self.timeout > 300:
            raise ConfigValidationError("timeout 必须在 1-300 之间")
        if self.worker_timeout < 30 or self.worker_timeout > 600:
            raise ConfigValidationError("worker_timeout 必须在 30-600 之间")


@dataclass
class MemoryConfig:
    """记忆配置"""
    db_path: str = "memory.db"
    vector_dim: int = 1536
    max_short_term_items: int = 100
    consolidation_interval: int = 300
    importance_threshold: float = 0.5
    similarity_threshold: float = 0.7
    memory_decay_rate: float = 0.05
    long_term_index_type: str = "Flat"
    
    def validate(self) -> None:
        """验证配置"""
        if self.vector_dim < 1:
            raise ConfigValidationError("vector_dim 必须大于 0")
        if self.max_short_term_items < 1:
            raise ConfigValidationError("max_short_term_items 必须大于 0")
        if not 0 <= self.importance_threshold <= 1:
            raise ConfigValidationError("importance_threshold 必须在 0-1 之间")


@dataclass
class CognitiveConfig:
    """认知配置"""
    reasoning_depth: int = 3
    max_thinking_time: int = 30
    enable_meta_cognition: bool = True
    max_chain_length: int = 5
    confidence_threshold: float = 0.7
    enable_reflection: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if self.reasoning_depth < 1 or self.reasoning_depth > 10:
            raise ConfigValidationError("reasoning_depth 必须在 1-10 之间")
        if self.max_chain_length < 1 or self.max_chain_length > 20:
            raise ConfigValidationError("max_chain_length 必须在 1-20 之间")
        if not 0 <= self.confidence_threshold <= 1:
            raise ConfigValidationError("confidence_threshold 必须在 0-1 之间")


@dataclass
class EvolutionConfig:
    """进化配置"""
    auto_evolve: bool = True
    evolution_interval: int = 3600
    mutation_rate: float = 0.1
    
    def validate(self) -> None:
        """验证配置"""
        if not 0 <= self.mutation_rate <= 1:
            raise ConfigValidationError("mutation_rate 必须在 0-1 之间")


@dataclass
class EmotionalConfig:
    """情感配置"""
    emotion_decay_rate: float = 0.95
    emotion_threshold: float = 0.3
    enable_emotional_memory: bool = True
    enable_empathy: bool = True
    enable_emotion_regulation: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if not 0 <= self.emotion_decay_rate <= 1:
            raise ConfigValidationError("emotion_decay_rate 必须在 0-1 之间")


@dataclass
class SensoryConfig:
    """感知配置"""
    max_input_length: int = 10000
    enable_multimodal: bool = True
    default_modality: str = "text"
    
    def validate(self) -> None:
        """验证配置"""
        if self.max_input_length < 1:
            raise ConfigValidationError("max_input_length 必须大于 0")


@dataclass
class ExecutionConfig:
    """执行配置"""
    max_workers: int = 4
    task_timeout: int = 30
    enable_parallel_execution: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if self.max_workers < 1:
            raise ConfigValidationError("max_workers 必须大于 0")
        if self.task_timeout < 1:
            raise ConfigValidationError("task_timeout 必须大于 0")


@dataclass
class UIConfig:
    """UI配置"""
    window_width: int = 1200
    window_height: int = 800
    theme: str = "dark"
    font_size: int = 14
    sidebar_width: int = 300
    enable_animations: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if self.window_width < 400:
            raise ConfigValidationError("window_width 必须大于 400")
        if self.window_height < 300:
            raise ConfigValidationError("window_height 必须大于 300")


@dataclass
class SystemConfig:
    """系统配置"""
    log_level: str = "INFO"
    max_workers: int = 4
    enable_gui: bool = True

    def validate(self) -> None:
        """验证配置"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ConfigValidationError(f"log_level 必须是 {valid_levels} 之一")


@dataclass
class ConsciousnessConfig:
    """意识配置"""
    awareness_threshold: float = 0.5
    reflection_interval: int = 60
    enable_self_model: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if not 0 <= self.awareness_threshold <= 1:
            raise ConfigValidationError("awareness_threshold 必须在 0-1 之间")


@dataclass
class LearningConfig:
    """学习配置"""
    learning_rate: float = 0.001
    enable_online_learning: bool = True
    
    def validate(self) -> None:
        """验证配置"""
        if self.learning_rate <= 0:
            raise ConfigValidationError("learning_rate 必须大于 0")


@dataclass
class HermesAutoSkillConfig:
    """Hermes Skill 自动创建配置"""
    enabled: bool = True
    window_seconds: int = 3600          # 滑动窗口
    min_occurrences: int = 3            # 触发自动创建的最少重复次数
    embedding_threshold: float = 0.78   # 意图聚类相似度阈值
    retry_cooldown_seconds: int = 86400 # 同一意图 24 小时内不重试
    max_drafts_per_run: int = 3         # 单次扫描最多生成草稿数
    import_whitelist: List[str] = field(
        default_factory=lambda: [
            "asyncio", "json", "re", "math", "datetime", "pathlib",
            "typing", "dataclasses", "enum", "collections", "itertools",
            "functools", "statistics", "random", "string", "textwrap",
        ]
    )

    def validate(self) -> None:
        if self.min_occurrences < 1:
            raise ConfigValidationError("min_occurrences 必须 >= 1")
        if not 0 < self.embedding_threshold <= 1:
            raise ConfigValidationError("embedding_threshold 必须在 (0, 1]")
        if self.window_seconds < 60:
            raise ConfigValidationError("window_seconds 必须 >= 60")


@dataclass
class HermesNudgeConfig:
    """Hermes 周期性 Nudge 配置"""
    enabled: bool = True
    min_interval_seconds: int = 10

    # 每个 nudge 任务的开关 + 周期（秒）
    pattern_mining_interval: int = 900          # 15 min
    memory_consolidation_interval: int = 300    # 5 min
    self_reflection_interval: int = 3600        # 60 min
    trajectory_scoring_interval: int = 1800     # 30 min
    skill_decay_check_interval: int = 86400     # 24 h
    health_snapshot_interval: int = 60          # 1 min

    def validate(self) -> None:
        if self.min_interval_seconds < 1:
            raise ConfigValidationError("min_interval_seconds 必须 >= 1")


@dataclass
class HermesTrajectoryConfig:
    """Hermes Trajectory 管道配置"""
    enabled: bool = True
    reward_threshold: float = 0.8         # 入选训练集的下限
    holdout_size: int = 30                # 评估 holdout 数量
    promotion_min_delta: float = 0.05     # 新模型相对旧模型 reward 提升阈值
    min_new_samples: int = 50             # 触发微调所需最少新样本
    output_dir: str = "data/training"     # 数据集导出目录

    def validate(self) -> None:
        if not 0 <= self.reward_threshold <= 1:
            raise ConfigValidationError("reward_threshold 必须在 [0, 1]")
        if self.holdout_size < 1:
            raise ConfigValidationError("holdout_size 必须 >= 1")
        if not 0 < self.promotion_min_delta <= 1:
            raise ConfigValidationError("promotion_min_delta 必须在 (0, 1]")


@dataclass
class HermesTrainerConfig:
    """Hermes 微调配置（可后端三种：ollama / llamafactory / unsloth）"""
    enabled: bool = False                  # 默认关闭，避免误触发
    backend: str = "ollama"                # ollama | llamafactory | unsloth
    base_model: str = "gemma2:2b"
    adapter_dir: str = "data/adapters"
    working_dir: str = "data/training"
    timeout_seconds: int = 7200            # 2h
    holdout_ratio: float = 0.1

    def validate(self) -> None:
        if self.backend not in {"ollama", "llamafactory", "unsloth"}:
            raise ConfigValidationError("backend 必须是 ollama/llamafactory/unsloth")
        if not 0 < self.holdout_ratio < 1:
            raise ConfigValidationError("holdout_ratio 必须在 (0, 1)")


@dataclass
class HermesConfig:
    """Hermes 三件套总配置"""
    auto_skill: HermesAutoSkillConfig = field(default_factory=HermesAutoSkillConfig)
    nudge: HermesNudgeConfig = field(default_factory=HermesNudgeConfig)
    trajectory: HermesTrajectoryConfig = field(default_factory=HermesTrajectoryConfig)
    trainer: HermesTrainerConfig = field(default_factory=HermesTrainerConfig)

    def validate(self) -> None:
        self.auto_skill.validate()
        self.nudge.validate()
        self.trajectory.validate()
        self.trainer.validate()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesConfig":
        cfg = cls()
        if "auto_skill" in data and isinstance(data["auto_skill"], dict):
            cfg.auto_skill = HermesAutoSkillConfig(**data["auto_skill"])
        if "nudge" in data and isinstance(data["nudge"], dict):
            cfg.nudge = HermesNudgeConfig(**data["nudge"])
        if "trajectory" in data and isinstance(data["trajectory"], dict):
            cfg.trajectory = HermesTrajectoryConfig(**data["trajectory"])
        if "trainer" in data and isinstance(data["trainer"], dict):
            cfg.trainer = HermesTrainerConfig(**data["trainer"])
        return cfg


@dataclass
class Config:
    """主配置类"""
    model: ModelConfig = field(default_factory=ModelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    cognitive: CognitiveConfig = field(default_factory=CognitiveConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    emotional: EmotionalConfig = field(default_factory=EmotionalConfig)
    sensory: SensoryConfig = field(default_factory=SensoryConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    consciousness: ConsciousnessConfig = field(default_factory=ConsciousnessConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)
    # spec fix-test-model-revert: 添加缺失的 hermes 字段（之前 to_dict 引用了 self.hermes 但未声明）
    hermes: HermesConfig = field(default_factory=HermesConfig)
    
    # 运行时配置
    debug: bool = False
    config_path: Optional[str] = None
    
    # 热更新
    _watchers: List[Callable] = field(default_factory=list, repr=False)
    _last_modified: float = field(default=0.0, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    
    def validate(self) -> None:
        """验证所有配置"""
        self.model.validate()
        self.memory.validate()
        self.cognitive.validate()
        self.evolution.validate()
        self.emotional.validate()
        self.sensory.validate()
        self.execution.validate()
        self.consciousness.validate()
        self.system.validate()
        self.ui.validate()
        self.learning.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model": asdict(self.model),
            "memory": asdict(self.memory),
            "cognitive": asdict(self.cognitive),
            "evolution": asdict(self.evolution),
            "emotional": asdict(self.emotional),
            "sensory": asdict(self.sensory),
            "execution": asdict(self.execution),
            "consciousness": asdict(self.consciousness),
            "system": asdict(self.system),
            "ui": asdict(self.ui),
            "learning": asdict(self.learning),
            "hermes": asdict(self.hermes),
            "debug": self.debug
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        config = cls()
        
        if "model" in data:
            config.model = ModelConfig(**data["model"])
        if "memory" in data:
            config.memory = MemoryConfig(**data["memory"])
        if "cognitive" in data:
            config.cognitive = CognitiveConfig(**data["cognitive"])
        if "evolution" in data:
            config.evolution = EvolutionConfig(**data["evolution"])
        if "emotional" in data:
            config.emotional = EmotionalConfig(**data["emotional"])
        if "sensory" in data:
            config.sensory = SensoryConfig(**data["sensory"])
        if "execution" in data:
            config.execution = ExecutionConfig(**data["execution"])
        if "consciousness" in data:
            config.consciousness = ConsciousnessConfig(**data["consciousness"])
        if "system" in data:
            config.system = SystemConfig(**data["system"])
        if "ui" in data:
            config.ui = UIConfig(**data["ui"])
        if "learning" in data:
            config.learning = LearningConfig(**data["learning"])
        if "hermes" in data:
            try:
                config.hermes = HermesConfig.from_dict(data["hermes"])
            except Exception as e:
                logger.warning(f"Failed to parse hermes config: {e}, using defaults")
        if "debug" in data:
            config.debug = data["debug"]

        return config
    
    def add_watcher(self, callback: Callable) -> None:
        """添加配置变更监听器"""
        with self._lock:
            self._watchers.append(callback)
    
    def remove_watcher(self, callback: Callable) -> None:
        """移除配置变更监听器"""
        with self._lock:
            if callback in self._watchers:
                self._watchers.remove(callback)
    
    def _notify_watchers(self, old_config: "Config") -> None:
        """通知监听器配置变更"""
        with self._lock:
            for watcher in self._watchers:
                try:
                    watcher(self, old_config)
                except Exception as e:
                    logger.error(f"Config watcher error: {e}")


class ConfigManager:
    """配置管理器
    
    管理配置的加载、保存和热更新
    """
    
    def __init__(self):
        self._config: Optional[Config] = None
        self._config_path: Optional[str] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_watching = threading.Event()
    
    def load_config(
        self,
        config_path: Optional[str] = None,
        use_env: bool = True
    ) -> Config:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            use_env: 是否使用环境变量覆盖
            
        Returns:
            Config: 配置对象
        """
        # 自动检测项目根目录的 config.yaml
        if config_path is None:
            auto_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
            if auto_path.exists():
                config_path = str(auto_path)
                logger.info(f"Auto-detected config file: {config_path}")
        
        config = Config()
        
        # 从文件加载
        if config_path and os.path.exists(config_path):
            config = self._load_from_file(config_path)
            config.config_path = config_path
            self._config_path = config_path
        
        # 从环境变量加载
        if use_env:
            config = self._load_from_env(config)
        
        # 验证配置
        try:
            config.validate()
        except ConfigValidationError as e:
            logger.error(f"Config validation failed: {e}")
            raise
        
        self._config = config
        logger.info("Configuration loaded successfully")
        
        return config
    
    def _load_from_file(self, path: str) -> Config:
        """从文件加载配置"""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return Config.from_dict(data)
    
    def _load_from_env(self, config: Config) -> Config:
        """从环境变量加载配置"""
        env_mappings = {
            # 模型配置
            "HYPERBRAIN_MODEL_DEFAULT": ("model", "default_model", str),
            "HYPERBRAIN_MODEL_TEMPERATURE": ("model", "temperature", float),
            "HYPERBRAIN_MODEL_MAX_TOKENS": ("model", "max_tokens", int),
            "HYPERBRAIN_MODEL_TIMEOUT": ("model", "timeout", int),
            
            # 记忆配置
            "HYPERBRAIN_MEMORY_DB_PATH": ("memory", "db_path", str),
            "HYPERBRAIN_MEMORY_VECTOR_DIM": ("memory", "vector_dim", int),
            "HYPERBRAIN_MEMORY_MAX_SHORT_TERM": ("memory", "max_short_term_items", int),
            
            # 认知配置
            "HYPERBRAIN_COGNITIVE_REASONING_DEPTH": ("cognitive", "reasoning_depth", int),
            
            # 系统配置
            "HYPERBRAIN_SYSTEM_LOG_LEVEL": ("system", "log_level", str),
            "HYPERBRAIN_SYSTEM_MAX_WORKERS": ("system", "max_workers", int),
            
            # 调试
            "HYPERBRAIN_DEBUG": ("debug", None, lambda x: x.lower() in ['true', '1', 'yes']),
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted = type_func(value)
                    
                    if section == "debug":
                        config.debug = converted
                    else:
                        section_obj = getattr(config, section)
                        if key:
                            setattr(section_obj, key, converted)
                    
                    logger.debug(f"Loaded from env: {env_var}={value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse env var {env_var}: {e}")
        
        return config
    
    def save_config(self, config: Config, path: Optional[str] = None) -> None:
        """保存配置到文件

        Args:
            config: 配置对象
            path: 保存路径
        """
        save_path = path or self._config_path or "config.yaml"
        path_obj = Path(save_path)

        data = config.to_dict()

        with open(path_obj, 'w', encoding='utf-8') as f:
            if path_obj.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif path_obj.suffix == '.json':
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        # spec fix-test-model-revert: 写后回读校验关键字段
        self._verify_saved_config(path_obj, config)

        logger.info(f"Configuration saved to {save_path}")

    def _verify_saved_config(self, path_obj: Path, config: Config) -> None:
        """写后回读校验：确保 yaml 中的关键字段与内存一致（spec fix-test-model-revert）

        Args:
            path_obj: 写入的配置文件路径
            config: 内存中的 Config 对象

        Raises:
            IOError: 当关键字段写后回读不一致时
        """
        try:
            with open(path_obj, 'r', encoding='utf-8') as f:
                if path_obj.suffix in ['.yaml', '.yml']:
                    readback = yaml.safe_load(f) or {}
                elif path_obj.suffix == '.json':
                    readback = json.load(f) or {}
                else:
                    readback = yaml.safe_load(f) or {}

            saved_ollama_model = readback.get('model', {}).get('ollama_model')
            expected_ollama_model = config.model.ollama_model
            if saved_ollama_model != expected_ollama_model:
                logger.error(
                    f"Config save mismatch! saved={saved_ollama_model!r} "
                    f"expected={expected_ollama_model!r}"
                )
                raise IOError(
                    f"Config save verification failed for ollama_model: "
                    f"saved={saved_ollama_model!r}, expected={expected_ollama_model!r}"
                )
            logger.info(
                f"Configuration saved and verified: ollama_model={expected_ollama_model}"
            )
        except IOError:
            raise
        except Exception as e:
            # 其他异常（如 FileNotFoundError, yaml.YAMLError 等）不视为硬错误，仅警告
            logger.warning(f"Config verification skipped due to: {e}")
    
    def start_hot_reload(self, interval: int = 5) -> None:
        """启动热重载
        
        Args:
            interval: 检查间隔（秒）
        """
        if self._watch_thread and self._watch_thread.is_alive():
            logger.warning("Hot reload already running")
            return
        
        self._stop_watching.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_config_file,
            args=(interval,),
            daemon=True
        )
        self._watch_thread.start()
        logger.info(f"Hot reload started with interval={interval}s")
    
    def stop_hot_reload(self) -> None:
        """停止热重载"""
        self._stop_watching.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)
        logger.info("Hot reload stopped")
    
    def _watch_config_file(self, interval: int) -> None:
        """监视配置文件变化"""
        if not self._config_path or not os.path.exists(self._config_path):
            return
        
        last_modified = os.path.getmtime(self._config_path)
        
        while not self._stop_watching.wait(interval):
            try:
                current_modified = os.path.getmtime(self._config_path)
                
                if current_modified > last_modified:
                    logger.info("Config file changed, reloading...")
                    
                    old_config = self._config
                    new_config = self.load_config(self._config_path)
                    
                    if old_config:
                        new_config._notify_watchers(old_config)
                    
                    last_modified = current_modified
                    
            except Exception as e:
                logger.error(f"Hot reload error: {e}")
    
    def get_config(self) -> Config:
        """获取当前配置"""
        if self._config is None:
            self._config = self.load_config()
        return self._config


# 全局配置管理器
_config_manager = ConfigManager()


def get_config(config_path: Optional[str] = None) -> Config:
    """获取配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config: 配置对象
    """
    return _config_manager.load_config(config_path)


def save_config(config: Config, path: Optional[str] = None) -> None:
    """保存配置"""
    _config_manager.save_config(config, path)


def start_hot_reload(interval: int = 5) -> None:
    """启动配置热重载"""
    _config_manager.start_hot_reload(interval)


def stop_hot_reload() -> None:
    """停止配置热重载"""
    _config_manager.stop_hot_reload()


def create_default_config(path: str = "config.yaml") -> None:
    """创建默认配置文件"""
    config = Config()
    _config_manager.save_config(config, path)
    print(f"Default configuration created at {path}")
