"""
Token 管理器

提供 Token 使用统计、成本控制、预算管理、使用限制和告警机制。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from hyperbrain.core.logger import get_logger
from .base import ModelProvider, ModelUsage

logger = get_logger("models.token_manager")


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """告警类型"""
    BUDGET_THRESHOLD = "budget_threshold"
    RATE_LIMIT = "rate_limit"
    COST_SPIKE = "cost_spike"
    TOKEN_QUOTA = "token_quota"
    DAILY_LIMIT = "daily_limit"


@dataclass
class BudgetAlert:
    """预算告警
    
    Attributes:
        type: 告警类型
        level: 告警级别
        message: 告警消息
        timestamp: 告警时间
        metadata: 额外元数据
    """
    type: AlertType
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConfig:
    """预算配置
    
    Attributes:
        daily_budget: 每日预算（美元）
        monthly_budget: 每月预算（美元）
        warning_threshold: 警告阈值（0-1）
        critical_threshold: 严重阈值（0-1）
        daily_token_limit: 每日 Token 上限
        rate_limit_per_minute: 每分钟请求限制
    """
    daily_budget: float = 10.0
    monthly_budget: float = 100.0
    warning_threshold: float = 0.7
    critical_threshold: float = 0.9
    daily_token_limit: int = 1000000
    rate_limit_per_minute: int = 60


@dataclass
class UsageRecord:
    """使用记录
    
    Attributes:
        provider: 提供商
        model: 模型名称
        usage: Token 使用统计
        cost: 成本估算
        timestamp: 时间戳
        latency_ms: 延迟
        task_type: 任务类型
    """
    provider: str
    model: str
    usage: ModelUsage
    cost: float
    timestamp: datetime
    latency_ms: float
    task_type: str = "unknown"


class TokenManager:
    """Token 管理器
    
    管理所有模型的 Token 使用、成本和预算。
    
    功能：
    - Token 使用统计
    - 成本控制
    - 预算管理
    - 使用限制
    - 告警机制
    
    Attributes:
        budget_config: 预算配置
        usage_history: 使用历史记录
        alert_handlers: 告警处理器列表
    """
    
    def __init__(self, budget_config: Optional[BudgetConfig] = None):
        self.budget_config = budget_config or BudgetConfig()
        self.usage_history: List[UsageRecord] = []
        self.alert_handlers: List[Callable[[BudgetAlert], None]] = []
        self._rate_limit_timestamps: List[datetime] = []
        self._lock = asyncio.Lock()
        self._alerts_sent: Set[str] = set()
    
    def add_alert_handler(self, handler: Callable[[BudgetAlert], None]) -> None:
        """添加告警处理器
        
        Args:
            handler: 告警处理函数
        """
        self.alert_handlers.append(handler)
    
    def _send_alert(self, alert: BudgetAlert) -> None:
        """发送告警
        
        Args:
            alert: 告警对象
        """
        alert_key = f"{alert.type.value}_{alert.level.value}_{alert.timestamp.strftime('%Y-%m-%d-%H')}"
        
        # 避免重复发送相同告警
        if alert_key in self._alerts_sent:
            return
        
        self._alerts_sent.add(alert_key)
        
        logger.log(
            "WARNING" if alert.level == AlertLevel.WARNING else "ERROR" if alert.level == AlertLevel.CRITICAL else "INFO",
            f"[TokenManager Alert] {alert.level.value.upper()}: {alert.message}"
        )
        
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    async def record_usage(
        self,
        provider: str,
        model: str,
        usage: ModelUsage,
        cost: float,
        latency_ms: float,
        task_type: str = "unknown"
    ) -> None:
        """记录使用
        
        Args:
            provider: 提供商
            model: 模型名称
            usage: Token 使用统计
            cost: 成本
            latency_ms: 延迟
            task_type: 任务类型
        """
        async with self._lock:
            record = UsageRecord(
                provider=provider,
                model=model,
                usage=usage,
                cost=cost,
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                task_type=task_type
            )
            
            self.usage_history.append(record)
            
            # 限制历史记录大小
            if len(self.usage_history) > 100000:
                self.usage_history = self.usage_history[-50000:]
            
            # 检查预算和限制
            await self._check_budget_alerts()
            await self._check_rate_limit()
            await self._check_token_quota()
    
    async def _check_budget_alerts(self) -> None:
        """检查预算告警"""
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        # 检查每日预算
        daily_ratio = daily_cost / self.budget_config.daily_budget if self.budget_config.daily_budget > 0 else 0
        
        if daily_ratio >= self.budget_config.critical_threshold:
            self._send_alert(BudgetAlert(
                type=AlertType.BUDGET_THRESHOLD,
                level=AlertLevel.CRITICAL,
                message=f"Daily budget critical: ${daily_cost:.4f} / ${self.budget_config.daily_budget:.2f} ({daily_ratio*100:.1f}%)",
                metadata={"daily_cost": daily_cost, "budget": self.budget_config.daily_budget}
            ))
        elif daily_ratio >= self.budget_config.warning_threshold:
            self._send_alert(BudgetAlert(
                type=AlertType.BUDGET_THRESHOLD,
                level=AlertLevel.WARNING,
                message=f"Daily budget warning: ${daily_cost:.4f} / ${self.budget_config.daily_budget:.2f} ({daily_ratio*100:.1f}%)",
                metadata={"daily_cost": daily_cost, "budget": self.budget_config.daily_budget}
            ))
        
        # 检查每月预算
        monthly_ratio = monthly_cost / self.budget_config.monthly_budget if self.budget_config.monthly_budget > 0 else 0
        
        if monthly_ratio >= self.budget_config.critical_threshold:
            self._send_alert(BudgetAlert(
                type=AlertType.BUDGET_THRESHOLD,
                level=AlertLevel.CRITICAL,
                message=f"Monthly budget critical: ${monthly_cost:.4f} / ${self.budget_config.monthly_budget:.2f} ({monthly_ratio*100:.1f}%)",
                metadata={"monthly_cost": monthly_cost, "budget": self.budget_config.monthly_budget}
            ))
    
    async def _check_rate_limit(self) -> None:
        """检查速率限制"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # 清理过期记录
        self._rate_limit_timestamps = [
            ts for ts in self._rate_limit_timestamps if ts > one_minute_ago
        ]
        
        request_count = len(self._rate_limit_timestamps)
        
        if request_count >= self.budget_config.rate_limit_per_minute:
            self._send_alert(BudgetAlert(
                type=AlertType.RATE_LIMIT,
                level=AlertLevel.WARNING,
                message=f"Rate limit reached: {request_count} requests/min (limit: {self.budget_config.rate_limit_per_minute})",
                metadata={"request_count": request_count, "limit": self.budget_config.rate_limit_per_minute}
            ))
        
        self._rate_limit_timestamps.append(now)
    
    async def _check_token_quota(self) -> None:
        """检查 Token 配额"""
        daily_tokens = self.get_daily_tokens()
        
        if daily_tokens >= self.budget_config.daily_token_limit:
            self._send_alert(BudgetAlert(
                type=AlertType.TOKEN_QUOTA,
                level=AlertLevel.CRITICAL,
                message=f"Daily token quota exceeded: {daily_tokens} / {self.budget_config.daily_token_limit}",
                metadata={"daily_tokens": daily_tokens, "limit": self.budget_config.daily_token_limit}
            ))
    
    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """获取指定日期的成本
        
        Args:
            date: 日期，默认今天
            
        Returns:
            float: 当日成本
        """
        target_date = date or datetime.now()
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        return sum(
            r.cost for r in self.usage_history
            if start <= r.timestamp < end
        )
    
    def get_monthly_cost(self, month: Optional[datetime] = None) -> float:
        """获取指定月份的成本
        
        Args:
            month: 月份，默认本月
            
        Returns:
            float: 当月成本
        """
        target = month or datetime.now()
        start = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if target.month == 12:
            end = target.replace(year=target.year + 1, month=1, day=1)
        else:
            end = target.replace(month=target.month + 1, day=1)
        
        return sum(
            r.cost for r in self.usage_history
            if start <= r.timestamp < end
        )
    
    def get_daily_tokens(self, date: Optional[datetime] = None) -> int:
        """获取指定日期的 Token 使用量
        
        Args:
            date: 日期，默认今天
            
        Returns:
            int: 当日 Token 使用量
        """
        target_date = date or datetime.now()
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        return sum(
            r.usage.total_tokens for r in self.usage_history
            if start <= r.timestamp < end
        )
    
    def get_usage_stats(
        self,
        since: Optional[datetime] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取使用统计
        
        Args:
            since: 起始时间
            provider: 过滤提供商
            model: 过滤模型
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        records = self.usage_history
        
        if since:
            records = [r for r in records if r.timestamp >= since]
        if provider:
            records = [r for r in records if r.provider == provider]
        if model:
            records = [r for r in records if r.model == model]
        
        if not records:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_latency_ms": 0.0,
                "by_provider": {},
                "by_model": {},
            }
        
        total_requests = len(records)
        total_tokens = sum(r.usage.total_tokens for r in records)
        total_cost = sum(r.cost for r in records)
        avg_latency = sum(r.latency_ms for r in records) / total_requests
        
        # 按提供商统计
        by_provider: Dict[str, Dict[str, Any]] = {}
        for r in records:
            if r.provider not in by_provider:
                by_provider[r.provider] = {"requests": 0, "tokens": 0, "cost": 0.0}
            by_provider[r.provider]["requests"] += 1
            by_provider[r.provider]["tokens"] += r.usage.total_tokens
            by_provider[r.provider]["cost"] += r.cost
        
        # 按模型统计
        by_model: Dict[str, Dict[str, Any]] = {}
        for r in records:
            if r.model not in by_model:
                by_model[r.model] = {"requests": 0, "tokens": 0, "cost": 0.0}
            by_model[r.model]["requests"] += 1
            by_model[r.model]["tokens"] += r.usage.total_tokens
            by_model[r.model]["cost"] += r.cost
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_latency_ms": avg_latency,
            "by_provider": by_provider,
            "by_model": by_model,
        }
    
    def is_budget_exceeded(self) -> bool:
        """检查预算是否已超出
        
        Returns:
            bool: 是否超出预算
        """
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        daily_tokens = self.get_daily_tokens()
        
        if daily_cost >= self.budget_config.daily_budget:
            return True
        if monthly_cost >= self.budget_config.monthly_budget:
            return True
        if daily_tokens >= self.budget_config.daily_token_limit:
            return True
        
        return False
    
    def can_make_request(self, estimated_cost: float = 0.0) -> bool:
        """检查是否可以发起请求
        
        Args:
            estimated_cost: 预估成本
            
        Returns:
            bool: 是否可以发起请求
        """
        if self.is_budget_exceeded():
            return False
        
        daily_cost = self.get_daily_cost()
        if daily_cost + estimated_cost >= self.budget_config.daily_budget:
            return False
        
        return True
    
    def get_budget_status(self) -> Dict[str, Any]:
        """获取预算状态
        
        Returns:
            Dict[str, Any]: 预算状态
        """
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        daily_tokens = self.get_daily_tokens()
        
        return {
            "daily": {
                "budget": self.budget_config.daily_budget,
                "used": daily_cost,
                "remaining": max(0, self.budget_config.daily_budget - daily_cost),
                "percentage": (daily_cost / self.budget_config.daily_budget * 100) if self.budget_config.daily_budget > 0 else 0,
            },
            "monthly": {
                "budget": self.budget_config.monthly_budget,
                "used": monthly_cost,
                "remaining": max(0, self.budget_config.monthly_budget - monthly_cost),
                "percentage": (monthly_cost / self.budget_config.monthly_budget * 100) if self.budget_config.monthly_budget > 0 else 0,
            },
            "tokens": {
                "daily_limit": self.budget_config.daily_token_limit,
                "used": daily_tokens,
                "remaining": max(0, self.budget_config.daily_token_limit - daily_tokens),
                "percentage": (daily_tokens / self.budget_config.daily_token_limit * 100) if self.budget_config.daily_token_limit > 0 else 0,
            },
            "rate_limit": {
                "limit_per_minute": self.budget_config.rate_limit_per_minute,
                "current_usage": len(self._rate_limit_timestamps),
            },
            "can_request": self.can_make_request(),
        }
    
    def reset_daily_stats(self) -> None:
        """重置每日统计（通常在午夜调用）"""
        self._alerts_sent.clear()
        self._rate_limit_timestamps.clear()
        logger.info("Daily stats reset")
    
    def get_cost_projection(self, days: int = 30) -> Dict[str, float]:
        """获取成本预测
        
        基于最近的使用情况预测未来成本。
        
        Args:
            days: 预测天数
            
        Returns:
            Dict[str, float]: 预测结果
        """
        # 获取最近7天的平均日成本
        recent_costs = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            recent_costs.append(self.get_daily_cost(date))
        
        avg_daily = sum(recent_costs) / len(recent_costs) if recent_costs else 0
        
        return {
            "avg_daily_cost": avg_daily,
            "projected_monthly": avg_daily * 30,
            "projected_period": avg_daily * days,
            "current_monthly": self.get_monthly_cost(),
        }


# 全局 Token 管理器实例
_global_token_manager: Optional[TokenManager] = None


def get_token_manager(budget_config: Optional[BudgetConfig] = None) -> TokenManager:
    """获取全局 Token 管理器
    
    Args:
        budget_config: 预算配置（首次创建时有效）
        
    Returns:
        TokenManager: Token 管理器实例
    """
    global _global_token_manager
    if _global_token_manager is None:
        _global_token_manager = TokenManager(budget_config)
    return _global_token_manager
