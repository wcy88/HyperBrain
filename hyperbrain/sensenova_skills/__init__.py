"""
SenseNova Skills 官方集成
本目录包含来自OpenSenseNova/SenseNova-Skills的官方Skills
"""
import os
import sys
from pathlib import Path

SENSENOVA_DIR = Path(__file__).parent
OFFICIAL_SKILLS_DIR = SENSENOVA_DIR / "official_skills"

def get_official_skills_list():
    """获取官方Skill列表"""
    if not OFFICIAL_SKILLS_DIR.exists():
        return []
    
    skills = []
    for skill_dir in OFFICIAL_SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            skills.append(skill_dir.name)
    
    return sorted(skills)

# 信息
__version__ = "0.1.0"
__author__ = "OpenSenseNova"
