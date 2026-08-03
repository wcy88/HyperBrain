"""
HyperBrain 日志系统

基于loguru的高级日志管理，支持：
- 控制台彩色输出
- 文件轮转记录
- 结构化日志
- 异常追踪
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


class InterceptHandler:
    """拦截标准logging的处理器"""
    
    def write(self, message: str) -> None:
        if message.strip():
            logger.info(message.strip())
    
    def flush(self) -> None:
        pass


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    rotation: str = "10 MB",
    retention: str = "30 days"
) -> None:
    """
    配置日志系统
    
    Args:
        log_dir: 日志目录，默认从配置读取
        log_level: 日志级别
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件记录
        rotation: 日志文件轮转大小
        retention: 日志保留时间
    """
    # 延迟导入避免循环导入
    try:
        from .config import get_config
        config = get_config()
        default_log_dir = getattr(config, 'log_dir', 'logs')
    except (ImportError, Exception):
        default_log_dir = 'logs'
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    if enable_console:
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            enqueue=True
        )
    
    # 文件输出
    if enable_file:
        log_path = Path(log_dir or default_log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 主日志文件
        logger.add(
            log_path / "hyperbrain.log",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # 错误日志单独记录
        logger.add(
            log_path / "error.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )


def get_logger(name: Optional[str] = None):
    """
    获取配置好的logger实例
    
    Args:
        name: 模块名称，用于标识日志来源
        
    Returns:
        loguru.logger: 配置好的logger
    """
    if name:
        return logger.bind(module=name)
    return logger


# 初始化默认日志配置
setup_logging()
