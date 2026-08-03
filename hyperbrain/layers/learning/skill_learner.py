"""
技能学习器

学习并掌握新技能，支持技能分解和组合
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from hyperbrain.core.logger import get_logger

logger = get_logger("learning.skill")


@dataclass
class Skill:
    """技能对象"""
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    proficiency: float = 0.0  # 熟练度 0-1
    success_count: int = 0
    failure_count: int = 0


class SkillLearner:
    """
    技能学习系统
    
    功能：
    1. 技能定义和分解
    2. 技能练习和改进
    3. 技能组合
    4. 熟练度追踪
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.skill_graph: Dict[str, List[str]] = {}  # 技能依赖图
        logger.info("SkillLearner initialized")
    
    def define_skill(self, name: str, description: str,
                    steps: List[str],
                    prerequisites: Optional[List[str]] = None) -> Skill:
        """
        定义新技能
        
        Args:
            name: 技能名称
            description: 技能描述
            steps: 执行步骤
            prerequisites: 前置技能
            
        Returns:
            Skill: 技能对象
        """
        skill = Skill(
            name=name,
            description=description,
            steps=steps,
            prerequisites=prerequisites or []
        )
        
        self.skills[name] = skill
        self.skill_graph[name] = prerequisites or []
        
        logger.info(f"Defined skill: {name}")
        return skill
    
    def practice_skill(self, name: str, success: bool = True) -> Skill:
        """
        练习技能
        
        Args:
            name: 技能名称
            success: 是否成功
            
        Returns:
            Skill: 更新后的技能
        """
        if name not in self.skills:
            raise ValueError(f"Skill not found: {name}")
        
        skill = self.skills[name]
        
        if success:
            skill.success_count += 1
        else:
            skill.failure_count += 1
        
        # 更新熟练度
        total = skill.success_count + skill.failure_count
        if total > 0:
            skill.proficiency = skill.success_count / total
        
        logger.debug(f"Practiced skill {name}: success={success}, proficiency={skill.proficiency:.2f}")
        return skill
    
    def get_skill_proficiency(self, name: str) -> float:
        """获取技能熟练度"""
        if name not in self.skills:
            return 0.0
        return self.skills[name].proficiency
    
    def can_perform(self, name: str) -> bool:
        """检查是否可以执行技能（前置技能满足）"""
        if name not in self.skills:
            return False
        
        skill = self.skills[name]
        for prereq in skill.prerequisites:
            if prereq not in self.skills:
                return False
            if self.skills[prereq].proficiency < 0.5:
                return False
        
        return True
    
    def get_learning_path(self, target_skill: str) -> List[str]:
        """获取学习路径"""
        if target_skill not in self.skills:
            return []
        
        # BFS查找依赖路径
        path = []
        visited = set()
        queue = [target_skill]
        
        while queue:
            skill_name = queue.pop(0)
            if skill_name in visited:
                continue
            visited.add(skill_name)
            path.append(skill_name)
            
            if skill_name in self.skill_graph:
                for prereq in self.skill_graph[skill_name]:
                    if prereq not in visited:
                        queue.append(prereq)
        
        return list(reversed(path))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_skills": len(self.skills),
            "avg_proficiency": sum(s.proficiency for s in self.skills.values()) / max(len(self.skills), 1),
            "mastered_skills": sum(1 for s in self.skills.values() if s.proficiency >= 0.8)
        }
