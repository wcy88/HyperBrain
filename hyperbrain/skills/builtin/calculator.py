"""
计算器 Skill
"""
from hyperbrain.skills.base import BaseSkill, SkillResult, SkillStatus
import operator


class CalculatorSkill(BaseSkill):
    """计算器 Skill"""
    
    name = "calculator"
    description = "简单的数学计算器"
    version = "1.0.0"
    category = "tools"
    tags = ["math", "calculation", "arithmetic"]
    
    OPERATORS = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "**": operator.pow
    }
    
    async def execute(self, expression: str = "", **kwargs) -> SkillResult:
        """执行计算
        
        Args:
            expression: 数学表达式，如 "2 + 3" 或 "5 * 10"
        """
        if not expression:
            # 如果没有表达式，返回帮助
            return SkillResult(
                success=True,
                message="使用: expression='a + b', 支持 +, -, *, /, **"
            )
        
        try:
            # 安全计算
            result = eval(expression, {"__builtins__": {}}, self.OPERATORS)
            return SkillResult(
                success=True,
                message=f"{expression} = {result}",
                data={"result": result, "expression": expression}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                status=SkillStatus.ERROR,
                error=f"计算失败: {e}"
            )
