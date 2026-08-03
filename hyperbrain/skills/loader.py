"""
Skill 加载器 - 管理所有 Skill 的加载和执行

参考 OpenClaw 的 Gateway 设计
"""
import os
import sys
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import BaseSkill, SkillResult, SkillStatus
from hyperbrain.core.logger import get_logger

logger = get_logger("skill_loader")


class SkillLoader:
    """Skill 加载和管理器"""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path(__file__).parent / "builtin"
        self.skills: Dict[str, Type[BaseSkill]] = {}
        self.instances: Dict[str, BaseSkill] = {}
        self._loaded = False
        self.sensenova_loader = None
    
    def load_skills(self) -> int:
        """加载所有 Skills"""
        logger.info("开始加载 Skills")
        count = 0
        
        # 首先加载内置 Skills
        count += self._load_builtin_skills()
        
        # 加载 SenseNova Skills
        count += self._load_sensenova_skills()
        
        self._loaded = True
        logger.info(f"共加载 {count} 个 Skill")
        return count
    
    def _load_builtin_skills(self) -> int:
        """加载内置 Skills"""
        count = 0
        
        if not self.skills_dir.exists():
            logger.warning(f"Skills 目录不存在: {self.skills_dir}")
            return 0
        
        # 扫描目录
        for file in self.skills_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            try:
                module_name = f"hyperbrain.skills.builtin.{file.stem}"
                module = importlib.import_module(module_name)
                
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseSkill) and 
                        obj != BaseSkill):
                        skill_name = getattr(obj, "name", name.lower())
                        self.skills[skill_name] = obj
                        count += 1
                        logger.info(f"加载内置 Skill: {skill_name} ({obj.__name__})")
                        
            except Exception as e:
                logger.error(f"加载 Skill 文件失败 {file.name}: {e}")
        
        return count
    
    def _load_sensenova_skills(self) -> int:
        """加载 SenseNova Skills（官方）"""
        count = 0
        
        try:
            from .sensenova_integration import initialize_sensenova_skills
            
            # 初始化 SenseNova 加载器
            sn_count = initialize_sensenova_skills()
            
            if sn_count > 0:
                from .sensenova_integration import get_sensenova_loader
                self.sensenova_loader = get_sensenova_loader()
                
                if self.sensenova_loader:
                    # 将 SenseNova Skills 也注册到主列表中（为了兼容性）
                    for skill in self.sensenova_loader.skills.values():
                        # 注册一个包装类
                        skill_class = type(f"{skill.__class__.__name__}Wrapper", 
                                          (BaseSkill,), {})
                        
                        # 设置属性
                        skill_class.name = skill.name
                        skill_class.description = skill.description
                        skill_class.version = "1.0.0"
                        skill_class.category = skill.category
                        skill_class.tags = skill.tags
                        
                        # 绑定实例
                        self.instances[skill.name] = skill
                        self.skills[skill.name] = skill_class
                        count += 1
                        logger.info(f"加载官方 SenseNova Skill: {skill.name}")
                
        except ImportError as e:
            logger.warning(f"无法加载 SenseNova Skills: {e}")
        except Exception as e:
            logger.error(f"加载 SenseNova Skills 失败: {e}")
        
        return count
    
    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取 Skill 实例（懒加载）"""
        if name not in self.skills:
            logger.warning(f"Skill 不存在: {name}")
            return None
            
        if name not in self.instances:
            skill_class = self.skills[name]
            self.instances[name] = skill_class()
            await self.instances[name].initialize()
            
        return self.instances[name]
    
    async def execute_skill(self, name: str, **kwargs) -> SkillResult:
        """执行 Skill"""
        import time
        
        skill = await self.get_skill(name)
        if not skill:
            return SkillResult(
                success=False,
                status=SkillStatus.ERROR,
                error=f"Skill 不存在: {name}"
            )
        
        start_time = time.time()
        
        try:
            logger.info(f"执行 Skill: {name}")
            result = await skill.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Skill 执行完成: {name} - {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Skill 执行失败 {name}: {e}")
            return SkillResult(
                success=False,
                status=SkillStatus.ERROR,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def list_skills(self) -> List[Dict]:
        """列出所有 Skill"""
        return [
            {
                "name": name,
                "class": cls.__name__,
                "info": (
                    self.instances[name].get_info()
                    if name in self.instances
                    else {"name": name}
                )
            }
            for name, cls in self.skills.items()
        ]

    def reload(self, only_new: bool = True) -> List[str]:
        """
        热加载新生成的 Skill。

        Args:
            only_new: True 时只扫描 `auto_generated/` 子目录；False 时复用 _load_builtin_skills 全量重扫。

        Returns:
            新加入主注册表的 skill_name 列表。
        """
        new_names: List[str] = []

        if not only_new:
            # 全量：清空后重建
            self.skills.clear()
            self.instances.clear()
            self._loaded = False
            self.load_skills()
            new_names = list(self.skills.keys())
            return new_names

        # only_new：扫描 auto_generated/*.py
        auto_dir = self.skills_dir / "auto_generated"
        if not auto_dir.exists():
            return new_names

        for file in auto_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            # 已经加载过就跳过
            module_full = f"hyperbrain.skills.auto_generated.{file.stem}"
            if module_full in sys.modules and self._is_already_loaded(file.stem):
                continue
            try:
                spec = importlib.util.spec_from_file_location(module_full, file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_full] = module
                spec.loader.exec_module(module)  # type: ignore[union-attr]

                # 找出 BaseSkill 子类
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseSkill)
                        and obj is not BaseSkill
                    ):
                        skill_name = getattr(obj, "name", file.stem)
                        if not skill_name or skill_name in self.skills:
                            skill_name = f"auto_{file.stem}"
                        self.skills[skill_name] = obj
                        # 不立刻实例化（避免 init 副作用）
                        logger.info(f"hot-loaded auto skill: {skill_name} ({file.name})")
                        new_names.append(skill_name)
            except Exception as e:  # noqa: BLE001
                logger.error(f"hot-load failed for {file.name}: {e}")
        return new_names

    def _is_already_loaded(self, stem: str) -> bool:
        """判断某 auto_generated stem 是否已经在 self.skills 中。"""
        for name, cls in self.skills.items():
            if cls.__module__ == f"hyperbrain.skills.auto_generated.{stem}":
                return True
        return False
