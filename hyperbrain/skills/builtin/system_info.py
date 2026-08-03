"""
系统信息 Skill
"""
from hyperbrain.skills.base import BaseSkill, SkillResult, SkillStatus
import platform
import sys
import psutil


class SystemInfoSkill(BaseSkill):
    """系统信息查询 Skill"""
    
    name = "system_info"
    description = "查询系统信息"
    version = "1.0.0"
    category = "system"
    tags = ["system", "hardware", "status"]
    
    async def execute(self, info_type: str = "all", **kwargs) -> SkillResult:
        """获取系统信息
        
        Args:
            info_type: 信息类型 (all, basic, memory, cpu, disk)
        """
        info = {}
        
        if info_type in ["all", "basic"]:
            info["python"] = {
                "version": platform.python_version(),
                "implementation": platform.python_implementation()
            }
            info["os"] = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine()
            }
        
        if info_type in ["all", "cpu"]:
            info["cpu"] = {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1)
            }
        
        if info_type in ["all", "memory"]:
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent
            }
        
        if info_type in ["all", "disk"]:
            disk = psutil.disk_usage("/")
            info["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        
        return SkillResult(
            success=True,
            message=f"获取 {info_type} 信息完成",
            data=info
        )
