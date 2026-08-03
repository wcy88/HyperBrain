"""
进度监控模块 (Progress Monitor)

监控任务执行进度、资源使用和动态策略调整。

功能：
- 监控任务执行进度
- 进度报告生成
- 超时检测和处理
- 资源使用监控
- 动态策略调整
"""

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.monitor")


class MonitorStatus(str, Enum):
    """监控状态"""
    IDLE = "idle"
    MONITORING = "monitoring"
    ALERT = "alert"
    CRITICAL = "critical"
    STOPPED = "stopped"


class ResourceType(str, Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    TIME = "time"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ProgressSnapshot(BaseModel):
    """进度快照"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    task_id: str = ""
    task_name: str = ""
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    status: str = ""
    
    # 时间信息
    start_time: Optional[datetime] = None
    estimated_end_time: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    remaining_seconds: Optional[float] = None
    
    # 资源使用
    resource_usage: Dict[str, float] = Field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": self.remaining_seconds,
            "timestamp": self.timestamp.isoformat()
        }


class ResourceUsage(BaseModel):
    """资源使用情况"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    resource_type: ResourceType = ResourceType.CPU
    current_value: float = 0.0
    peak_value: float = 0.0
    average_value: float = 0.0
    limit_value: Optional[float] = None
    usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    
    def is_over_limit(self) -> bool:
        """是否超过限制"""
        if self.limit_value is not None:
            return self.current_value > self.limit_value
        return False
    
    def is_near_limit(self, threshold: float = 0.8) -> bool:
        """是否接近限制"""
        if self.limit_value is not None and self.limit_value > 0:
            return self.current_value / self.limit_value > threshold
        return False


class Alert(BaseModel):
    """告警"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: AlertLevel = AlertLevel.INFO
    message: str = ""
    resource_type: Optional[ResourceType] = None
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def resolve(self) -> None:
        """解决告警"""
        self.resolved = True
        self.resolved_at = datetime.now()


class ProgressReport(BaseModel):
    """进度报告"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    
    # 总体进度
    overall_progress: float = Field(default=0.0, ge=0.0, le=100.0)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    
    # 任务快照
    task_snapshots: List[ProgressSnapshot] = Field(default_factory=list)
    
    # 资源使用
    resource_usage: Dict[str, ResourceUsage] = Field(default_factory=dict)
    
    # 告警
    alerts: List[Alert] = Field(default_factory=list)
    
    # 时间
    report_time: datetime = Field(default_factory=datetime.now)
    elapsed_time_seconds: float = 0.0
    
    # 建议
    recommendations: List[str] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "overall_progress": self.overall_progress,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "elapsed_time_seconds": self.elapsed_time_seconds,
            "recommendations": self.recommendations
        }


class MonitoredTask:
    """被监控的任务"""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        total_steps: int = 100,
        timeout_seconds: Optional[float] = None,
        resource_limits: Optional[Dict[str, float]] = None
    ):
        self.task_id = task_id
        self.name = name
        self.total_steps = total_steps
        self.current_step = 0
        self.status = "pending"
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        self.timeout_seconds = timeout_seconds
        self.resource_limits = resource_limits or {}
        
        self._progress_callbacks: List[Callable[[ProgressSnapshot], None]] = []
        self._snapshots: List[ProgressSnapshot] = []
        self._resource_history: Dict[str, List[float]] = {}
        
        self._is_cancelled = False
    
    def start(self) -> None:
        """开始任务"""
        self.start_time = datetime.now()
        self.status = "running"
        logger.info(f"Task started: {self.name}")
    
    def update_progress(self, step: int, metadata: Optional[Dict[str, Any]] = None) -> ProgressSnapshot:
        """更新进度"""
        self.current_step = min(step, self.total_steps)
        progress_percent = (self.current_step / max(self.total_steps, 1)) * 100
        
        elapsed = 0.0
        remaining = None
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if progress_percent > 0:
                total_estimated = elapsed / (progress_percent / 100)
                remaining = total_estimated - elapsed
        
        snapshot = ProgressSnapshot(
            task_id=self.task_id,
            task_name=self.name,
            progress_percent=progress_percent,
            status=self.status,
            start_time=self.start_time,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
            metadata=metadata or {}
        )
        
        self._snapshots.append(snapshot)
        
        # 触发回调
        for callback in self._progress_callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
        
        return snapshot
    
    def update_resource_usage(self, resource_type: ResourceType, value: float) -> None:
        """更新资源使用"""
        key = resource_type.value
        if key not in self._resource_history:
            self._resource_history[key] = []
        self._resource_history[key].append(value)
    
    def complete(self, success: bool = True) -> None:
        """完成任务"""
        self.end_time = datetime.now()
        self.status = "completed" if success else "failed"
        self.current_step = self.total_steps
        
        self.update_progress(self.total_steps, {"completed": success})
        logger.info(f"Task {'completed' if success else 'failed'}: {self.name}")
    
    def cancel(self) -> None:
        """取消任务"""
        self._is_cancelled = True
        self.status = "cancelled"
        self.end_time = datetime.now()
        logger.info(f"Task cancelled: {self.name}")
    
    def is_timed_out(self) -> bool:
        """检查是否超时"""
        if not self.timeout_seconds or not self.start_time:
            return False
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed > self.timeout_seconds
    
    def add_progress_callback(self, callback: Callable[[ProgressSnapshot], None]) -> None:
        """添加进度回调"""
        self._progress_callbacks.append(callback)
    
    def get_latest_snapshot(self) -> Optional[ProgressSnapshot]:
        """获取最新快照"""
        if self._snapshots:
            return self._snapshots[-1]
        return None
    
    def get_average_resource_usage(self, resource_type: ResourceType) -> float:
        """获取平均资源使用"""
        key = resource_type.value
        values = self._resource_history.get(key, [])
        if values:
            return sum(values) / len(values)
        return 0.0


class ProgressMonitor:
    """
    进度监控器
    
    监控任务执行进度和资源使用，生成报告和告警。
    """
    
    def __init__(self, check_interval_seconds: float = 5.0):
        self.config = get_config()
        self.check_interval = check_interval_seconds
        
        self._monitored_tasks: Dict[str, MonitoredTask] = {}
        self._alerts: List[Alert] = []
        self._reports: List[ProgressReport] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._status = MonitorStatus.IDLE
        
        # 告警阈值
        self._alert_thresholds: Dict[str, float] = {
            "cpu": 80.0,
            "memory": 85.0,
            "disk": 90.0,
            "time_ratio": 1.5  # 实际时间/预估时间
        }
        
        logger.info("ProgressMonitor initialized")
    
    def register_task(
        self,
        task_id: str,
        name: str,
        total_steps: int = 100,
        timeout_seconds: Optional[float] = None,
        resource_limits: Optional[Dict[str, float]] = None
    ) -> MonitoredTask:
        """
        注册任务进行监控
        
        Args:
            task_id: 任务ID
            name: 任务名称
            total_steps: 总步骤数
            timeout_seconds: 超时时间
            resource_limits: 资源限制
            
        Returns:
            MonitoredTask: 被监控的任务
        """
        task = MonitoredTask(
            task_id=task_id,
            name=name,
            total_steps=total_steps,
            timeout_seconds=timeout_seconds,
            resource_limits=resource_limits
        )
        
        self._monitored_tasks[task_id] = task
        logger.debug(f"Registered task for monitoring: {name}")
        return task
    
    def unregister_task(self, task_id: str) -> bool:
        """注销任务"""
        if task_id in self._monitored_tasks:
            del self._monitored_tasks[task_id]
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[MonitoredTask]:
        """获取被监控的任务"""
        return self._monitored_tasks.get(task_id)
    
    async def start_monitoring(self) -> None:
        """开始监控循环"""
        if self._status == MonitorStatus.MONITORING:
            return
        
        self._status = MonitorStatus.MONITORING
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Progress monitoring started")
    
    async def stop_monitoring(self) -> None:
        """停止监控"""
        self._status = MonitorStatus.STOPPED
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        logger.info("Progress monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self._status == MonitorStatus.MONITORING:
            try:
                # 检查所有任务
                for task in list(self._monitored_tasks.values()):
                    await self._check_task(task)
                
                # 清理已完成的旧任务
                self._cleanup_completed_tasks()
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_task(self, task: MonitoredTask) -> None:
        """检查单个任务"""
        # 检查超时
        if task.is_timed_out():
            alert = Alert(
                level=AlertLevel.ERROR,
                message=f"Task timeout: {task.name}",
                task_id=task.task_id
            )
            self._alerts.append(alert)
            logger.warning(f"Task timeout detected: {task.name}")
        
        # 检查资源使用
        for resource_type in ResourceType:
            usage = task.get_average_resource_usage(resource_type)
            limit = task.resource_limits.get(resource_type.value)
            
            if limit and usage > limit:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    message=f"Resource limit exceeded: {resource_type.value} = {usage:.1f}",
                    resource_type=resource_type,
                    task_id=task.task_id
                )
                self._alerts.append(alert)
    
    def _cleanup_completed_tasks(self, max_age_seconds: float = 3600.0) -> None:
        """清理已完成的任务"""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self._monitored_tasks.items():
            if task.status in ("completed", "failed", "cancelled"):
                if task.end_time and (now - task.end_time).total_seconds() > max_age_seconds:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._monitored_tasks[task_id]
    
    def generate_report(self, title: str = "Progress Report") -> ProgressReport:
        """
        生成进度报告
        
        Args:
            title: 报告标题
            
        Returns:
            ProgressReport: 进度报告
        """
        report = ProgressReport(title=title)
        
        total_tasks = len(self._monitored_tasks)
        if total_tasks == 0:
            return report
        
        completed = 0
        failed = 0
        running = 0
        pending = 0
        total_progress = 0.0
        
        for task in self._monitored_tasks.values():
            snapshot = task.get_latest_snapshot()
            if snapshot:
                report.task_snapshots.append(snapshot)
                total_progress += snapshot.progress_percent
            
            if task.status == "completed":
                completed += 1
            elif task.status == "failed":
                failed += 1
            elif task.status == "running":
                running += 1
            else:
                pending += 1
        
        report.total_tasks = total_tasks
        report.completed_tasks = completed
        report.failed_tasks = failed
        report.running_tasks = running
        report.pending_tasks = pending
        report.overall_progress = total_progress / max(total_tasks, 1)
        
        # 添加未解决的告警
        report.alerts = [a for a in self._alerts if not a.resolved]
        
        # 生成建议
        report.recommendations = self._generate_recommendations(report)
        
        self._reports.append(report)
        return report
    
    def _generate_recommendations(self, report: ProgressReport) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if report.failed_tasks > 0:
            recommendations.append(f"有 {report.failed_tasks} 个任务失败，建议检查错误日志")
        
        if report.pending_tasks > report.running_tasks * 2:
            recommendations.append("待处理任务过多，建议增加并行度")
        
        # 检查告警
        critical_alerts = [a for a in report.alerts if a.level == AlertLevel.CRITICAL]
        if critical_alerts:
            recommendations.append(f"有 {len(critical_alerts)} 个严重告警需要处理")
        
        if report.overall_progress < 50 and report.elapsed_time_seconds > 300:
            recommendations.append("进度较慢，建议检查是否有性能瓶颈")
        
        return recommendations
    
    def create_alert(
        self,
        level: AlertLevel,
        message: str,
        resource_type: Optional[ResourceType] = None,
        task_id: Optional[str] = None
    ) -> Alert:
        """
        创建告警
        
        Args:
            level: 告警级别
            message: 消息
            resource_type: 资源类型
            task_id: 任务ID
            
        Returns:
            Alert: 告警
        """
        alert = Alert(
            level=level,
            message=message,
            resource_type=resource_type,
            task_id=task_id
        )
        self._alerts.append(alert)
        logger.warning(f"Alert created: [{level.value}] {message}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolve()
                return True
        return False
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        unresolved_only: bool = False
    ) -> List[Alert]:
        """获取告警"""
        alerts = self._alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return alerts
    
    def get_progress(self, task_id: str) -> Optional[float]:
        """获取任务进度"""
        task = self._monitored_tasks.get(task_id)
        if task:
            snapshot = task.get_latest_snapshot()
            if snapshot:
                return snapshot.progress_percent
        return None
    
    def get_overall_progress(self) -> float:
        """获取总体进度"""
        if not self._monitored_tasks:
            return 100.0
        
        total = sum(
            t.get_latest_snapshot().progress_percent 
            for t in self._monitored_tasks.values()
            if t.get_latest_snapshot()
        )
        return total / len(self._monitored_tasks)
    
    def set_alert_threshold(self, resource: str, threshold: float) -> None:
        """设置告警阈值"""
        self._alert_thresholds[resource] = threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "status": self._status.value,
            "monitored_tasks": len(self._monitored_tasks),
            "total_alerts": len(self._alerts),
            "unresolved_alerts": len([a for a in self._alerts if not a.resolved]),
            "total_reports": len(self._reports),
            "overall_progress": self.get_overall_progress()
        }
    
    def get_reports(self, limit: int = 10) -> List[ProgressReport]:
        """获取报告历史"""
        return self._reports[-limit:]
    
    def clear_history(self) -> None:
        """清空历史"""
        self._alerts.clear()
        self._reports.clear()
        logger.info("ProgressMonitor history cleared")
    
    def reset(self) -> None:
        """重置监控器"""
        self._monitored_tasks.clear()
        self._alerts.clear()
        self._reports.clear()
        self._status = MonitorStatus.IDLE
        logger.info("ProgressMonitor reset")
