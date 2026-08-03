"""
HyperBrain Skill 系统

提供可插拔的能力模块，参考 OpenClaw 的 Skill 架构
"""
from .base import BaseSkill, SkillResult
from .loader import SkillLoader

__all__ = ['BaseSkill', 'SkillResult', 'SkillLoader']
