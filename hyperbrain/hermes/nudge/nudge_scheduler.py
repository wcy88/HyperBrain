"""
Nudge 调度器

设计：
- 纯 asyncio 实现，不引入 APScheduler 减少依赖
- 每个 nudge job = 一个 `asyncio.create_task` 协程，内部 `while self._running: sleep(interval)`
- 异常隔离：每个 job 单独的 try/except 包裹，写入 nudge_log 表
- start() / stop() 接口，stop() 会 cancel 所有 job 并等待 graceful shutdown
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger
from hyperbrain.hermes.nudge.nudge_log import NudgeLog

logger = get_hermes_logger("scheduler")


@dataclass
class NudgeJob:
    name: str
    interval: int            # 秒
    coro_factory: Callable[[], Awaitable[None]]
    last_run_ts: float = 0.0
    run_count: int = 0
    err_count: int = 0


class NudgeScheduler:
    """
    异步 Nudge 调度器。

    Usage:
        sch = NudgeScheduler(brain)
        sch.register(NudgeJob("pattern_mining", 15, _pattern_mining))
        await sch.start()
        ...
        await sch.stop()
    """

    def __init__(self, brain, config, db):
        self.brain = brain
        self.config = config
        self.db = db
        self.jobs: Dict[str, NudgeJob] = {}
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self._log = NudgeLog(db)

    # ---------- 注册 ----------

    def register(self, name: str, interval: int, coro_factory: Callable[[], Awaitable[None]]) -> None:
        """注册一个 nudge job；同 name 会覆盖。"""
        # 强制 interval 不低于 min_interval
        interval = max(int(interval or 0), int(self.config.min_interval_seconds))
        self.jobs[name] = NudgeJob(
            name=name,
            interval=interval,
            coro_factory=coro_factory,
        )

    def unregister(self, name: str) -> None:
        self.jobs.pop(name, None)

    def list_jobs(self) -> List[Dict]:
        return [
            {
                "name": j.name,
                "interval": j.interval,
                "last_run_ts": j.last_run_ts,
                "run_count": j.run_count,
                "err_count": j.err_count,
            }
            for j in self.jobs.values()
        ]

    # ---------- 生命周期 ----------

    async def start(self) -> None:
        if not self.config.enabled:
            logger.info("nudge disabled by config")
            return
        if self._running:
            return
        self._running = True
        self._tasks = [
            asyncio.create_task(self._loop(j), name=f"nudge.{j.name}")
            for j in self.jobs.values()
        ]
        logger.info(f"nudge scheduler started with {len(self._tasks)} jobs")

    async def stop(self, timeout: float = 10.0) -> None:
        if not self._running:
            return
        self._running = False
        for t in self._tasks:
            t.cancel()
        # 等所有 task 收尾
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("nudge stop timeout, some tasks may not finish cleanly")
        self._tasks = []
        logger.info("nudge scheduler stopped")

    # ---------- 内部循环 ----------

    async def _loop(self, job: NudgeJob) -> None:
        # 启动时先小睡 0.1s，避免与主流程抢资源
        await asyncio.sleep(0.1)
        while self._running:
            started = time.time()
            log_id = self._log.start(job.name)
            try:
                await job.coro_factory()
                job.run_count += 1
                job.last_run_ts = time.time()
                self._log.end(log_id, success=True, error=None)
            except asyncio.CancelledError:
                # stop() 触发的 cancel；不再记录成功的 log，直接退出
                break
            except Exception as e:  # noqa: BLE001
                job.err_count += 1
                err = f"{type(e).__name__}: {e}"[:1000]
                self._log.end(log_id, success=False, error=err)
                logger.error(f"nudge {job.name} failed: {e}")
            # 距离本轮开始睡了多久，补足到 interval
            elapsed = time.time() - started
            sleep_for = max(0.5, job.interval - elapsed)
            # 分段 sleep 以便快速响应 stop
            slept = 0.0
            while self._running and slept < sleep_for:
                chunk = min(1.0, sleep_for - slept)
                await asyncio.sleep(chunk)
                slept += chunk
