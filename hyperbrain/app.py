"""
HyperBrain 应用启动器

支持 GUI 和 CLI 两种模式，提供系统初始化、信号处理和错误恢复。
"""

import argparse
import asyncio
import signal
import sys
import traceback
from typing import Optional

from hyperbrain.core.brain import Brain, get_brain, reset_brain
from hyperbrain.core.config import get_config
from hyperbrain.core.logger import get_logger, setup_logging

logger = get_logger("app")


class Application:
    """应用类
    
    管理整个应用的生命周期，包括：
    - 系统初始化
    - 信号处理
    - 模式切换
    - 优雅关闭
    """
    
    def __init__(self):
        self.brain: Optional[Brain] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
    
    async def initialize(
        self,
        config=None,
        log_level: str = "INFO",
        debug: bool = False
    ) -> bool:
        """初始化应用
        
        Args:
            config: 配置对象
            log_level: 日志级别
            debug: 调试模式
            
        Returns:
            bool: 是否成功
        """
        try:
            # 设置日志
            setup_logging(log_level=log_level)
            
            # 加载配置
            app_config = config or get_config()
            if debug:
                app_config.debug = True
            
            # 创建Brain实例
            self.brain = get_brain(
                config=app_config,
                enable_logging=True,
                log_level=log_level
            )
            
            # 初始化系统
            success = await self.brain.initialize()
            if not success:
                logger.error("Brain initialization failed")
                return False
            
            # 启动系统
            await self.brain.start()
            
            # 设置信号处理
            self._setup_signal_handlers()
            
            self._initialized = True
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def handle_signal(signum, frame):
            sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
            logger.info(f"Received signal {sig_name}")
            self._shutdown_event.set()
        
        try:
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
            
            # Windows 特定信号
            if sys.platform == "win32":
                try:
                    signal.signal(signal.SIGBREAK, handle_signal)
                except AttributeError:
                    pass
            
            logger.debug("Signal handlers registered")
        except (AttributeError, ValueError) as e:
            logger.warning(f"Could not set up signal handlers: {e}")
    
    async def wait_for_shutdown(self) -> None:
        """等待关闭信号"""
        await self._shutdown_event.wait()
    
    async def shutdown(self) -> None:
        """关闭应用"""
        if not self._initialized or not self.brain:
            return
        
        logger.info("Shutting down application...")
        
        try:
            await self.brain.shutdown()
            reset_brain()
            self._initialized = False
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run_cli(self) -> int:
        """运行CLI模式
        
        Returns:
            int: 退出码
        """
        from hyperbrain.main import CLIInterface
        
        cli = CLIInterface(self.brain)
        
        # 在后台运行CLI
        cli_task = asyncio.create_task(cli.run())
        
        # 等待关闭信号或CLI结束
        shutdown_task = asyncio.create_task(self.wait_for_shutdown())
        
        done, pending = await asyncio.wait(
            [cli_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 取消未完成的任务
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        return 0
    
    def run_gui(self) -> int:
        """运行GUI模式（同步版本，避免asyncio和Qt事件循环冲突）

        注意：此方法完全独立管理Brain生命周期，不依赖app.initialize()。
        在main()中，GUI模式会跳过app.initialize()直接调用此方法。

        Returns:
            int: 退出码
        """
        try:
            from PyQt6.QtWidgets import QApplication
            from hyperbrain.ui.main_window import MainWindow
            from hyperbrain.main import AsyncLoopThread

            app = QApplication(sys.argv)
            app.setApplicationName("HyperBrain")
            app.setApplicationVersion("0.2.0")

            # 创建后台持久事件循环用于Brain生命周期管理
            async_thread = AsyncLoopThread()

            try:
                # 在持久循环中初始化Brain（确保Queue在正确的循环中创建）
                async_thread.run_coroutine(self.brain.initialize())
                async_thread.run_coroutine(self.brain.start())

                window = MainWindow(brain=self.brain, async_thread=async_thread)
                window.show()

                logger.info("GUI mode started")

                # 运行Qt事件循环（阻塞，直到窗口关闭）
                exit_code = app.exec()

                return exit_code

            finally:
                # 清理：关闭Brain和事件循环
                try:
                    async_thread.run_coroutine(self.brain.shutdown())
                except Exception as e:
                    logger.error(f"Error during brain shutdown: {e}")
                finally:
                    async_thread.stop()

        except ImportError as e:
            logger.error(f"GUI dependencies not available: {e}")
            print("错误: GUI 模式不可用")
            print("请安装 PyQt6: pip install PyQt6")
            return 1
    
    async def process_single(self, user_input: str) -> int:
        """处理单条输入
        
        Args:
            user_input: 用户输入
            
        Returns:
            int: 退出码
        """
        try:
            result = await self.brain.process(user_input)
            
            if result.success:
                print(result.content)
                return 0
            else:
                print(f"错误: {result.error}", file=sys.stderr)
                return 1
                
        except Exception as e:
            logger.error(f"Process error: {e}")
            print(f"错误: {e}", file=sys.stderr)
            return 1


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="hyperbrain",
        description="HyperBrain - 拟人脑认知架构系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m hyperbrain.app                    # 启动CLI模式
  python -m hyperbrain.app --mode cli         # 启动CLI模式
  python -m hyperbrain.app --mode gui         # 启动GUI模式
  python -m hyperbrain.app --debug            # 调试模式
  python -m hyperbrain.app --process "你好"   # 单条处理
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["cli", "gui"],
        default="cli",
        help="运行模式 (默认: cli)"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--process", "-p",
        type=str,
        help="处理单条输入并退出"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.2.0"
    )
    
    return parser


async def main() -> int:
    """主函数
    
    Returns:
        int: 退出码
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = "DEBUG" if args.debug else args.log_level
    
    # 创建应用
    app = Application()
    
    try:
        # 根据模式运行
        if args.mode == "gui":
            # GUI模式：完全独立初始化，避免asyncio和Qt事件循环冲突
            # 不调用app.initialize()，由run_gui()在AsyncLoopThread中管理Brain生命周期
            setup_logging(log_level=log_level)
            app_config = get_config()
            if args.debug:
                app_config.debug = True
            app.brain = get_brain(
                config=app_config,
                enable_logging=True,
                log_level=log_level
            )
            exit_code = app.run_gui()
        else:
            # CLI/单条处理模式：使用标准asyncio初始化
            success = await app.initialize(
                log_level=log_level,
                debug=args.debug
            )

            if not success:
                print("应用初始化失败", file=sys.stderr)
                return 1

            if args.process:
                exit_code = await app.process_single(args.process)
            else:
                exit_code = await app.run_cli()

        return exit_code

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        print(f"致命错误: {e}", file=sys.stderr)
        return 1

    finally:
        if args.mode != "gui":
            await app.shutdown()


def run() -> None:
    """同步入口点"""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)


if __name__ == "__main__":
    run()
