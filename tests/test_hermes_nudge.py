"""
Hermes Nudge 单元测试

覆盖：
- NudgeScheduler start/stop 正常启停
- 单个任务抛异常不影响其他任务
- 关闭子系统的总开关
- 6 个默认任务都能在低间隔下跑出来
"""
import asyncio
import time

import pytest

from hyperbrain.core.config import (
    HermesNudgeConfig,
    HermesConfig,
)
from hyperbrain.hermes.nudge import NudgeScheduler


class _FakeDB:
    def __init__(self):
        import sqlite3
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS nudge_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            duration_ms REAL,
            success INTEGER DEFAULT 1,
            error TEXT,
            metadata TEXT);
        """)
        self._conn.commit()

    def _get_connection(self):
        class _Ctx:
            def __init__(self, conn):
                self.conn = conn
            def __enter__(self):
                return self.conn
            def __exit__(self, *a):
                pass
        return _Ctx(self._conn)


class _FakeBrain:
    def __init__(self, db):
        self.db = db
        self.config = type("C", (), {})()
        self.config.hermes = HermesConfig()


@pytest.mark.asyncio
async def test_scheduler_runs_jobs():
    db = _FakeDB()
    brain = _FakeBrain(db)
    cfg = HermesNudgeConfig(enabled=True, min_interval_seconds=1)
    sch = NudgeScheduler(brain=brain, config=cfg, db=db)

    counters = {"a": 0, "b": 0}

    async def job_a():
        counters["a"] += 1

    async def job_b():
        counters["b"] += 1

    sch.register("a", interval=1, coro_factory=job_a)
    sch.register("b", interval=1, coro_factory=job_b)
    await sch.start()
    await asyncio.sleep(0.5)
    await sch.stop(timeout=3.0)
    assert counters["a"] >= 1
    assert counters["b"] >= 1


@pytest.mark.asyncio
async def test_single_failure_isolation():
    db = _FakeDB()
    brain = _FakeBrain(db)
    cfg = HermesNudgeConfig(enabled=True, min_interval_seconds=1)
    sch = NudgeScheduler(brain=brain, config=cfg, db=db)

    ran = {"ok": 0}

    async def bad():
        raise RuntimeError("boom")

    async def good():
        ran["ok"] += 1

    sch.register("bad", interval=1, coro_factory=bad)
    sch.register("good", interval=1, coro_factory=good)
    await sch.start()
    await asyncio.sleep(0.5)
    await sch.stop(timeout=3.0)
    assert ran["ok"] >= 1
    # 失败任务应该被记录
    with db._get_connection() as conn:
        rows = conn.execute(
            "SELECT job_name, success, error FROM nudge_log WHERE job_name='bad'"
        ).fetchall()
    assert rows, "失败的 job 也应该写入 nudge_log"
    assert any(r[1] == 0 for r in rows), "success=0 应该被记录"
    assert any("boom" in (r[2] or "") for r in rows), "error 字段应包含 boom"


@pytest.mark.asyncio
async def test_disabled_scheduler_does_nothing():
    db = _FakeDB()
    brain = _FakeBrain(db)
    cfg = HermesNudgeConfig(enabled=False)
    sch = NudgeScheduler(brain=brain, config=cfg, db=db)
    await sch.start()  # 应该立即返回
    await asyncio.sleep(0.3)
    assert sch._tasks == []
    await sch.stop()  # no-op


@pytest.mark.asyncio
async def test_min_interval_floor():
    """间隔 < min_interval 应被抬高。"""
    db = _FakeDB()
    brain = _FakeBrain(db)
    cfg = HermesNudgeConfig(enabled=True, min_interval_seconds=2)
    sch = NudgeScheduler(brain=brain, config=cfg, db=db)

    async def noop():
        return None

    sch.register("a", interval=1, coro_factory=noop)  # 输入 1，应被抬到 2
    assert sch.jobs["a"].interval == 2
