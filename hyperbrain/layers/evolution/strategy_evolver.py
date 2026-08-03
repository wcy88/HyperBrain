"""
策略进化器

进化系统的行为策略和决策规则
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from hyperbrain.core.logger import get_logger

logger = get_logger("evolution.strategy")


@dataclass
class Strategy:
    """策略对象"""
    name: str
    rules: Dict[str, Any]
    success_count: int = 0
    failure_count: int = 0
    priority: float = 1.0


class StrategyEvolver:
    """
    策略进化系统
    
    功能：
    1. 策略定义和管理
    2. 策略效果评估
    3. 策略选择和组合
    4. 新策略生成
    """
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.active_strategy: Optional[str] = None
        logger.info("StrategyEvolver initialized")
    
    def register_strategy(self, name: str, rules: Dict[str, Any]) -> Strategy:
        """
        注册策略
        
        Args:
            name: 策略名称
            rules: 策略规则
            
        Returns:
            Strategy: 策略对象
        """
        strategy = Strategy(name=name, rules=rules)
        self.strategies[name] = strategy
        logger.info(f"Registered strategy: {name}")
        return strategy
    
    def evaluate_strategy(self, name: str, success: bool) -> None:
        """
        评估策略效果
        
        Args:
            name: 策略名称
            success: 是否成功
        """
        if name not in self.strategies:
            return
        
        strategy = self.strategies[name]
        if success:
            strategy.success_count += 1
        else:
            strategy.failure_count += 1
        
        # 更新优先级
        total = strategy.success_count + strategy.failure_count
        if total > 0:
            strategy.priority = strategy.success_count / total
        
        logger.debug(f"Strategy {name} evaluated: success={success}, priority={strategy.priority:.2f}")
    
    def select_best_strategy(self, context: Optional[Dict[str, Any]] = None) -> Optional[Strategy]:
        """
        选择最佳策略
        
        Args:
            context: 上下文信息
            
        Returns:
            Optional[Strategy]: 最佳策略
        """
        if not self.strategies:
            return None
        
        # 按优先级排序
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.priority,
            reverse=True
        )
        
        return sorted_strategies[0] if sorted_strategies else None
    
    def combine_strategies(self, 
                          strategy_names: List[str],
                          new_name: str) -> Strategy:
        """
        组合多个策略
        
        Args:
            strategy_names: 策略名称列表
            new_name: 新策略名称
            
        Returns:
            Strategy: 组合后的策略
        """
        combined_rules = {}
        
        for name in strategy_names:
            if name in self.strategies:
                combined_rules.update(self.strategies[name].rules)
        
        return self.register_strategy(new_name, combined_rules)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_strategies": len(self.strategies),
            "avg_priority": sum(s.priority for s in self.strategies.values()) / max(len(self.strategies), 1),
            "best_strategy": max(self.strategies.values(), key=lambda s: s.priority).name if self.strategies else None
        }
