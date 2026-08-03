"""
Gateway 网关 - 路由和调度中心

参考 OpenClaw 的 Gateway 设计
"""
import asyncio
from typing import Dict, Any, Optional, List
from .context import ContextManager, ConversationTurn
from hyperbrain.skills import SkillLoader, BaseSkill, SkillResult
from hyperbrain.core.logger import get_logger

logger = get_logger("gateway")


class Gateway:
    """网关核心类"""
    
    def __init__(self):
        self.context = ContextManager()
        self.skill_loader = SkillLoader()
        self._initialized = False
        
    async def initialize(self) -> bool:
        """初始化网关"""
        logger.info("初始化 Gateway")
        count = self.skill_loader.load_skills()
        self._initialized = True
        logger.info(f"Gateway 初始化完成，加载 {count} 个 Skills")
        return True
    
    async def process_message(self, message: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """处理用户消息"""
        if not self._initialized:
            await self.initialize()
            
        logger.info(f"处理消息: {message[:100]}...")
        
        # 保存用户输入
        self.context.add_turn("user", message, metadata)
        
        # 解析意图并执行
        result = await self._parse_and_execute(message)
        
        # 保存系统输出
        if "message" in result:
            self.context.add_turn("assistant", result["message"], {"source": "gateway"})
            
        return result
    
    async def _parse_and_execute(self, message: str) -> Dict[str, Any]:
        """解析意图并执行"""
        message_lower = message.lower()
        
        # SenseNova Skills 意图识别
        skill_result = await self._parse_sensenova_intent(message, message_lower)
        if skill_result:
            return skill_result
        
        # 内置 Skills 意图识别
        skill_result = await self._parse_builtin_intent(message, message_lower)
        if skill_result:
            return skill_result
        
        # 默认响应
        skills = self.skill_loader.list_skills()
        skill_names = [s['name'] for s in skills]
        
        return {
            "success": True,
            "message": "您好！我是 HyperBrain。我有以下能力：\n" +
                     "📊 内置能力:\n" +
                     "  - 计算器：计算 2 + 3\n" +
                     "  - 系统信息：查看系统信息\n" +
                     "🧠 SenseNova 能力:\n" +
                     "  - 图像生成：生成一张图片\n" +
                     "  - PPT生成：制作一个PPT\n" +
                     "  - 数据分析：分析数据\n" +
                     "  - 深度研究：研究某个话题\n" +
                     "  - 网络搜索：搜索信息\n" +
                     "  - 信息图：制作信息图\n" +
                     f"\n📋 技能列表: {skill_names}",
            "data": {"skills": skills}
        }
    
    async def _parse_sensenova_intent(self, message: str, message_lower: str) -> Optional[Dict[str, Any]]:
        """解析 SenseNova Skills 意图"""
        # 图像生成
        if any(kw in message_lower for kw in ['生成图片', '生成图像', '画一张', '画图', '生成一张']):
            prompt = message.replace('生成', '').replace('图片', '').replace('图像', '').strip()
            skill_result = await self.skill_loader.execute_skill("sn_image_generate", prompt=prompt)
            return self._format_skill_result(skill_result)
        
        # PPT生成
        if any(kw in message_lower for kw in ['ppt', '演示', '幻灯片', '制作ppt']):
            import re
            # 提取页数
            match = re.search(r'(\d+)\s*页', message)
            slides = int(match.group(1)) if match else 10
            # 提取主题
            topic = re.sub(r'\d+\s*页', '', message).replace('PPT', '').replace('ppt', '').strip()
            skill_result = await self.skill_loader.execute_skill("sn_ppt_generate", topic=topic, slides=slides)
            return self._format_skill_result(skill_result)
        
        # 数据分析
        if any(kw in message_lower for kw in ['分析数据', '数据分析', '分析excel']):
            skill_result = await self.skill_loader.execute_skill("sn_data_analysis", file_path="未指定", analysis_type="summary")
            return self._format_skill_result(skill_result)
        
        # 深度研究
        if any(kw in message_lower for kw in ['研究', '调研', '深度研究']):
            topic = message.replace('研究', '').replace('调研', '').strip()
            skill_result = await self.skill_loader.execute_skill("sn_deep_research", topic=topic)
            return self._format_skill_result(skill_result)
        
        # 网络搜索
        if any(kw in message_lower for kw in ['搜索', '查找', '查询', '搜一下']):
            query = message.replace('搜索', '').replace('查找', '').replace('查询', '').strip()
            skill_result = await self.skill_loader.execute_skill("sn_web_search", query=query)
            return self._format_skill_result(skill_result)
        
        # 信息图
        if any(kw in message_lower for kw in ['信息图', '图表', '可视化']):
            content = message.replace('信息图', '').replace('图表', '').strip()
            skill_result = await self.skill_loader.execute_skill("sn_infographic", content=content)
            return self._format_skill_result(skill_result)
        
        return None
    
    async def _parse_builtin_intent(self, message: str, message_lower: str) -> Optional[Dict[str, Any]]:
        """解析内置 Skills 意图"""
        # 计算器
        if "计算" in message_lower or "calculator" in message_lower:
            expression = self._extract_expression(message)
            if expression:
                skill_result = await self.skill_loader.execute_skill("calculator", expression=expression)
                return self._format_skill_result(skill_result)
        
        # 系统信息
        elif "系统信息" in message_lower or "system" in message_lower:
            info_type = self._extract_info_type(message)
            skill_result = await self.skill_loader.execute_skill("system_info", info_type=info_type)
            return self._format_skill_result(skill_result)
        
        # 技能列表
        elif "技能列表" in message_lower or "skills" in message_lower:
            skills = self.skill_loader.list_skills()
            return {
                "success": True,
                "message": f"可用 Skills: {[s['name'] for s in skills]}",
                "data": {"skills": skills}
            }
        
        return None
    
    def _format_skill_result(self, skill_result: SkillResult) -> Dict[str, Any]:
        """格式化 Skill 结果"""
        return {
            "success": skill_result.success,
            "message": skill_result.message,
            "data": skill_result.data,
            "error": skill_result.error,
            "execution_time_ms": skill_result.execution_time_ms
        }
    
    def _extract_expression(self, message: str) -> Optional[str]:
        """从消息中提取数学表达式"""
        import re
        pattern = r'[\d+\-*/.()\s]+'
        matches = re.findall(pattern, message)
        for match in matches:
            match = match.strip()
            if match and any(op in match for op in "+-*/"):
                return match
        return None
    
    def _extract_info_type(self, message: str) -> str:
        """从消息中提取信息类型"""
        message_lower = message.lower()
        if "cpu" in message_lower:
            return "cpu"
        elif "memory" in message_lower or "内存" in message_lower:
            return "memory"
        elif "disk" in message_lower or "磁盘" in message_lower:
            return "disk"
        return "all"
    
    def list_skills(self) -> List[Dict]:
        """列出所有 Skills"""
        return self.skill_loader.list_skills()
