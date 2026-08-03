"""
Hermes Agent 三件套入口

- auto_skill : Skill 自动创建
- nudge      : 周期性 nudge 调度
- trajectory : Trajectory 训练管道闭环

所有子模块只读 Brain.db / Brain.model_manager，不直接 import 8 层，
避免与现有架构形成循环依赖。
"""
from .common import (
    get_hermes_logger,
    safe_chat,
    intent_key_from_text,
)

__all__ = [
    "get_hermes_logger",
    "safe_chat",
    "intent_key_from_text",
]
