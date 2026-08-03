"""
HyperBrain 主入口

拟人脑认知架构系统 - 命令行版本
支持完整的CLI交互、参数解析和系统管理
"""

import argparse
import asyncio
import json
import sys
import threading
import traceback
from typing import Optional

from hyperbrain.core.brain import Brain, SystemState, get_brain, reset_brain
from hyperbrain.core.config import get_config
from hyperbrain.core.logger import get_logger, setup_logging

logger = get_logger("main")


class AsyncLoopThread:
    """后台持久事件循环线程，供 GUI 模式使用"""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._started = threading.Event()
        self._thread.start()
        self._started.wait()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._started.set()
        self._loop.run_forever()

    def run_coroutine(self, coro):
        """在线程的事件循环中提交并等待协程执行，返回结果"""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def submit_coroutine(self, coro, callback=None):
        """提交协程，可选回调接收结果"""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        if callback:
            future.add_done_callback(lambda f: callback(f))
        return future

    def stop(self):
        """停止事件循环"""
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    @property
    def loop(self):
        return self._loop


_global_async_thread: Optional[AsyncLoopThread] = None


def get_async_thread() -> AsyncLoopThread:
    global _global_async_thread
    if _global_async_thread is None:
        _global_async_thread = AsyncLoopThread()
    return _global_async_thread


class CLIInterface:
    """命令行交互界面"""
    
    def __init__(self, brain: Brain):
        self.brain = brain
        self._running = False
        self._command_history: list = []
        
    async def run(self) -> None:
        """运行CLI交互循环"""
        self._running = True
        
        print("=" * 60)
        print(" HyperBrain - 拟人脑认知架构系统")
        print(" 版本: 0.2.0")
        print("=" * 60)
        print()
        print("命令:")
        print("  /exit, /quit    - 退出系统")
        print("  /stats          - 显示系统统计")
        print("  /report         - 生成系统报告")
        print("  /memory         - 显示记忆状态")
        print("  /emotion        - 显示情感状态")
        print("  /reflect        - 触发自我反思")
        print("  /evolve         - 触发进化周期")
        print("  /learn <内容>   - 学习新内容")
        print("  /think <问题>   - 认知思考")
        print("  /clear          - 清屏")
        print("  /help           - 显示帮助")
        print("=" * 60)
        print()
        
        # 初始化系统
        success = await self.brain.initialize()
        if not success:
            print("系统初始化失败，请检查日志")
            return
        
        await self.brain.start()
        
        while self._running:
            try:
                user_input = input("\n你: ").strip()
                
                if not user_input:
                    continue
                
                self._command_history.append(user_input)
                
                # 处理命令
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                else:
                    # 处理普通输入
                    await self._process_input(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n收到中断信号，正在关闭...")
                break
            except EOFError:
                print("\n输入结束")
                break
            except Exception as e:
                logger.error(f"CLI error: {e}")
                print(f"\n发生错误: {e}")
        
        await self.brain.shutdown()
        print("\n系统已关闭。再见！")
    
    async def _handle_command(self, command: str) -> None:
        """处理内部命令"""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ["/exit", "/quit"]:
            self._running = False
            
        elif cmd == "/stats":
            await self._show_stats()
            
        elif cmd == "/report":
            await self._show_report()
            
        elif cmd == "/memory":
            await self._show_memory()
            
        elif cmd == "/emotion":
            await self._show_emotion()
            
        elif cmd == "/reflect":
            await self._do_reflect()
            
        elif cmd == "/evolve":
            await self._do_evolve()
            
        elif cmd == "/learn":
            if args:
                content = " ".join(args)
                result = await self.brain.learn(content)
                print(f"\n[学习完成] 模式: {result.mode_used.value}")
            else:
                print("\n用法: /learn <学习内容>")
                
        elif cmd == "/think":
            if args:
                problem = " ".join(args)
                result = await self.brain.think(problem)
                print(f"\n[思考结果]")
                print(f"问题: {result.get('problem', 'N/A')}")
                stages = result.get('stages', {})
                for stage_name, stage_data in stages.items():
                    print(f"  {stage_name}: {stage_data}")
            else:
                print("\n用法: /think <问题>")
                
        elif cmd == "/clear":
            print("\n" * 50)
            
        elif cmd == "/help":
            self._show_help()
            
        else:
            print(f"\n未知命令: {cmd}，输入 /help 查看帮助")
    
    async def _process_input(self, user_input: str) -> None:
        """处理用户输入"""
        print("\nHyperBrain: ", end="", flush=True)
        
        try:
            result = await self.brain.process(user_input)
            
            if result.success:
                print(result.content)
                
                # 显示处理信息（调试用）
                if self.brain.config.debug:
                    print(f"\n[处理时间: {result.processing_time_ms:.0f}ms | "
                          f"层: {', '.join(result.layers_involved)}]")
            else:
                print(f"[处理失败] {result.error}")
                
        except Exception as e:
            logger.error(f"Process error: {e}")
            print(f"[错误] {str(e)}")
    
    async def _show_stats(self) -> None:
        """显示系统统计"""
        stats = self.brain.get_stats()
        
        print("\n" + "=" * 50)
        print("系统统计")
        print("=" * 50)
        print(f"状态: {stats.system_state}")
        print(f"运行时间: {stats.uptime_seconds:.1f} 秒")
        print(f"处理输入: {stats.total_inputs_processed}")
        print(f"生成输出: {stats.total_outputs_generated}")
        print(f"平均处理时间: {stats.average_processing_time_ms:.1f} ms")
        print(f"错误数: {stats.error_count}")
        print("-" * 50)
        print("记忆状态:")
        for key, value in stats.memory_usage.items():
            print(f"  {key}: {value}")
        print("=" * 50)
    
    async def _show_report(self) -> None:
        """显示系统报告"""
        try:
            report = await self.brain.get_system_report()
            
            print("\n" + "=" * 50)
            print("系统报告")
            print("=" * 50)
            print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
            print("=" * 50)
            
        except Exception as e:
            print(f"\n生成报告失败: {e}")
    
    async def _show_memory(self) -> None:
        """显示记忆状态"""
        summary = self.brain.get_memory_summary()
        
        print("\n" + "=" * 50)
        print("记忆状态")
        print("=" * 50)
        print("记忆流:")
        for key, value in summary.get("flow", {}).items():
            print(f"  {key}: {value}")
        print("=" * 50)
    
    async def _show_emotion(self) -> None:
        """显示情感状态"""
        emotion = self.brain.get_emotional_state()
        
        print("\n" + "=" * 50)
        print("情感状态")
        print("=" * 50)
        if emotion:
            print(json.dumps(emotion, indent=2, ensure_ascii=False, default=str))
        else:
            print("无活跃情感")
        print("=" * 50)
    
    async def _do_reflect(self) -> None:
        """执行自我反思"""
        print("\n[正在反思...]")
        try:
            result = await self.brain.reflect()
            print("\n反思结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            print(f"反思失败: {e}")
    
    async def _do_evolve(self) -> None:
        """执行进化"""
        print("\n[正在执行进化周期...]")
        try:
            result = await self.brain.evolve()
            if result:
                print(f"\n进化完成: {result.cycle_id}")
                print(f"完成阶段: {len(result.phases_completed)}")
                print(f"状态: {result.status}")
            else:
                print("进化未执行")
        except Exception as e:
            print(f"进化失败: {e}")
    
    def _show_help(self) -> None:
        """显示帮助信息"""
        print("\n" + "=" * 50)
        print("HyperBrain CLI 帮助")
        print("=" * 50)
        print("\n普通输入:")
        print("  直接输入文本与系统对话")
        print("\n命令:")
        print("  /exit, /quit    - 退出系统")
        print("  /stats          - 显示系统统计")
        print("  /report         - 生成完整系统报告")
        print("  /memory         - 显示记忆状态")
        print("  /emotion        - 显示情感状态")
        print("  /reflect        - 触发自我反思")
        print("  /evolve         - 触发进化周期")
        print("  /learn <内容>   - 学习新内容")
        print("  /think <问题>   - 认知思考")
        print("  /clear          - 清屏")
        print("  /help           - 显示此帮助")
        print("=" * 50)


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="hyperbrain",
        description="HyperBrain - 拟人脑认知架构系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m hyperbrain.main                    # 启动CLI模式
  python -m hyperbrain.main --mode cli         # 启动CLI模式
  python -m hyperbrain.main --mode gui         # 启动GUI模式
  python -m hyperbrain.main --debug            # 调试模式
  python -m hyperbrain.main --process "你好"   # 单条处理
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


async def run_single_process(brain: Brain, user_input: str) -> None:
    """处理单条输入"""
    try:
        await brain.initialize()
        await brain.start()
        
        result = await brain.process(user_input)
        
        if result.success:
            print(result.content)
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)
            
    finally:
        await brain.shutdown()


def main():
    """主函数 - 同步版本，避免异步冲突
    
    Returns:
        int: 退出码
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志
    log_level = "DEBUG" if args.debug else args.log_level
    setup_logging(log_level=log_level)
    
    # 加载配置
    config = get_config()
    if args.debug:
        config.debug = True
    
    logger.info(f"Starting HyperBrain in {args.mode} mode")
    
    try:
        # 创建Brain实例
        brain = get_brain(config=config, log_level=log_level)
        
        # 单条处理模式
        if args.process:
            asyncio.run(run_single_process(brain, args.process))
            return 0
        
        # CLI模式
        if args.mode == "cli":
            asyncio.run(run_cli(brain))
            return 0
        
        # GUI模式
        elif args.mode == "gui":
            try:
                from PyQt6.QtWidgets import QApplication
                from hyperbrain.ui.main_window import MainWindow
                
                # 创建后台持久事件循环
                async_thread = get_async_thread()
                
                # 在持久循环中初始化 Brain
                async_thread.run_coroutine(brain.initialize())
                async_thread.run_coroutine(brain.start())
                
                app = QApplication(sys.argv)
                app.setApplicationName("HyperBrain")
                app.setApplicationVersion("0.2.0")
                
                window = MainWindow(brain=brain, async_thread=async_thread)
                window.show()
                
                logger.info("GUI mode started")
                exit_code = app.exec()
                
                # 清理
                async_thread.run_coroutine(brain.shutdown())
                async_thread.stop()
                
                return exit_code
                
            except ImportError as e:
                logger.error(f"GUI dependencies not available: {e}")
                print("GUI 模式不可用，请安装 PyQt6")
                print("运行: pip install PyQt6")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        print(f"致命错误: {e}", file=sys.stderr)
        return 1
    finally:
        reset_brain()


async def run_cli(brain: Brain):
    """运行CLI模式"""
    cli = CLIInterface(brain)
    await cli.run()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
