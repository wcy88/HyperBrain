"""
SenseNova Skills 官方集成器

能够解析和加载来自 https://github.com/opensensenova/sensenova-skills 的官方Skills
"""
import os
import sys
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base import BaseSkill, SkillResult, SkillStatus
from hyperbrain.core.logger import get_logger

logger = get_logger("sensenova_integration")


class SenseNovaSkillManifest:
    """SenseNova SKILL.md 清单解析器"""

    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self.skill_md = skill_dir / "SKILL.md"
        self.manifest: Dict[str, Any] = {}
        self.name: str = ""
        self.description: str = ""
        self.triggers: List[str] = []
        self.metadata: Dict[str, Any] = {}

        if self.skill_md.exists():
            self._parse_skill_md()

    def _parse_skill_md(self):
        """解析 SKILL.md 中的 YAML front matter"""
        try:
            content = self.skill_md.read_text(encoding="utf-8")

            # 提取 YAML front matter
            if content.startswith("---"):
                yaml_parts = content.split("---", 2)
                if len(yaml_parts) >= 3:
                    yaml_content = yaml_parts[1]
                    self.manifest = yaml.safe_load(yaml_content)

                    self.name = self.manifest.get("name", self.skill_dir.name)
                    self.description = self.manifest.get("description", "")
                    self.triggers = self.manifest.get("triggers", [])
                    self.metadata = self.manifest.get("metadata", {})

        except Exception as e:
            logger.warning(f"解析 {self.skill_md} 失败: {e}")


class SenseNovaSkill(BaseSkill):
    """SenseNova 官方 Skill 包装器"""

    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self.manifest = SenseNovaSkillManifest(skill_dir)

        # 设置属性
        self.name = self.manifest.name
        self.description = self.manifest.description
        self.version = "1.0.0"
        self.category = self.manifest.metadata.get("category", "sensenova")
        self.tags = []

        # 使用官方 SKILL.md 中的触发器作为标签
        self.tags.extend(self.manifest.triggers)

    async def initialize(self) -> bool:
        """初始化"""
        logger.info(f"初始化 SenseNova Skill: {self.name}")
        return True

    async def execute(self, **kwargs) -> SkillResult:
        """执行 Skill（占位）"""
        return SkillResult(
            success=True,
            status=SkillStatus.SUCCESS,
            message=f"SenseNova Skill '{self.name}' 已准备就绪（完整实现需要配合 OpenClaw 或 hermes-agent）",
            data={
                "skill_name": self.name,
                "skill_dir": str(self.skill_dir),
                "triggers": self.manifest.triggers,
                "metadata": self.manifest.metadata,
            },
        )


class SenseNovaSkillLoader:
    """SenseNova 官方 Skills 加载器"""

    def __init__(self, official_skills_dir: Path):
        self.official_skills_dir = official_skills_dir
        self.skills: Dict[str, SenseNovaSkill] = {}

    def load_all_skills(self) -> int:
        """加载所有官方 Skills"""
        logger.info(f"从 {self.official_skills_dir} 加载 SenseNova Skills")

        if not self.official_skills_dir.exists():
            logger.warning(f"目录不存在: {self.official_skills_dir}")
            return 0

        count = 0
        for item in sorted(self.official_skills_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                # 检查是否有 SKILL.md
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    try:
                        skill = SenseNovaSkill(item)
                        self.skills[skill.name] = skill
                        count += 1
                        logger.info(f"加载 SenseNova Skill: {skill.name}")
                    except Exception as e:
                        logger.warning(f"加载 Skill {item.name} 失败: {e}")

        logger.info(f"共加载 {count} 个 SenseNova Skills")
        return count

    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有 Skills"""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "triggers": skill.manifest.triggers,
                "metadata": skill.manifest.metadata,
                "dir": str(skill.skill_dir),
            }
            for skill in self.skills.values()
        ]


# 全局单例
_SENSENOVA_LOADER: Optional[SenseNovaSkillLoader] = None


def get_sensenova_loader() -> Optional[SenseNovaSkillLoader]:
    """获取 SenseNova 加载器（单例）"""
    return _SENSENOVA_LOADER


def initialize_sensenova_skills() -> int:
    """初始化 SenseNova Skills"""
    global _SENSENOVA_LOADER

    base_dir = Path(__file__).parent.parent
    official_skills_dir = base_dir / "sensenova_skills" / "official_skills"

    if not official_skills_dir.exists():
        logger.warning("SenseNova Skills 未安装")
        return 0

    _SENSENOVA_LOADER = SenseNovaSkillLoader(official_skills_dir)
    count = _SENSENOVA_LOADER.load_all_skills()

    return count
