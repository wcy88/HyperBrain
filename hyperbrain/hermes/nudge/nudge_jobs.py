"""
6 个默认 nudge 任务的实现。
每个函数都是 `async def ()`，被 NudgeScheduler 包成循环协程。

设计原则：
- 单个任务执行时长 < 30s，避免影响下一轮触发
- 失败不抛出到 scheduler，由 nudge_log 记录
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from hyperbrain.hermes.common import get_hermes_logger

if TYPE_CHECKING:
    from hyperbrain.core.brain import Brain

logger = get_hermes_logger("nudge_jobs")


def register_default_jobs(scheduler, brain: "Brain") -> None:
    cfg = brain.config.hermes.nudge
    if not cfg.enabled:
        return

    scheduler.register("pattern_mining", cfg.pattern_mining_interval,
                       lambda: _pattern_mining(brain))
    scheduler.register("memory_consolidation", cfg.memory_consolidation_interval,
                       lambda: _memory_consolidation(brain))
    scheduler.register("self_reflection", cfg.self_reflection_interval,
                       lambda: _self_reflection(brain))
    scheduler.register("trajectory_scoring", cfg.trajectory_scoring_interval,
                       lambda: _trajectory_scoring(brain))
    scheduler.register("skill_decay_check", cfg.skill_decay_check_interval,
                       lambda: _skill_decay_check(brain))
    scheduler.register("health_snapshot", cfg.health_snapshot_interval,
                       lambda: _health_snapshot(brain))


# ---------- 单个任务 ----------

async def _pattern_mining(brain: "Brain") -> None:
    gen = getattr(brain, "auto_skill_generator", None)
    if gen is None:
        return
    results = await gen.scan_once()
    if results:
        ok = sum(1 for r in results if r.get("success"))
        logger.info(f"pattern_mining: {ok}/{len(results)} created")


async def _memory_consolidation(brain: "Brain") -> None:
    try:
        n = brain.memory.consolidate()
        if n:
            logger.debug(f"memory_consolidation: {n} memories consolidated")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"memory_consolidation: {e}")
        raise


async def _self_reflection(brain: "Brain") -> None:
    try:
        # self_reflect 在现有 ConsciousManager 中是同步的；包成 to_thread
        import asyncio
        result = await asyncio.to_thread(brain.consciousness.self_reflect)
        if result:
            logger.debug(f"self_reflection: {result.get('cycle', '?')}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"self_reflection: {e}")
        raise


async def _trajectory_scoring(brain: "Brain") -> None:
    pipe = getattr(brain, "trajectory_pipeline", None)
    if pipe is None:
        return
    n = pipe.score_pending(limit=200)
    if n:
        logger.info(f"trajectory_scoring: scored {n} trajectories")


async def _skill_decay_check(brain: "Brain") -> None:
    """检查 30 天没被调用的 Skill（只针对 generated_skills）。"""
    try:
        with brain.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT skill_name, last_attempt_at FROM generated_skills
                WHERE status = 'active'
                """,
            ).fetchall()
        if not rows:
            return
        import datetime as _dt
        now = time.time()
        for name, last in rows:
            if not last:
                continue
            try:
                ts = _dt.datetime.strptime(last, "%Y-%m-%d %H:%M:%S").timestamp()
            except Exception:
                continue
            if now - ts > 30 * 86400:
                with brain.db.get_connection() as conn:
                    conn.execute(
                        "UPDATE generated_skills SET status = 'decayed' WHERE skill_name = ?",
                        (name,),
                    )
                logger.info(f"skill_decay_check: decayed {name}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"skill_decay_check: {e}")
        raise


async def _health_snapshot(brain: "Brain") -> None:
    """记录一次系统健康快照。"""
    try:
        stats = brain.get_stats()
        # 不另外写表，复用 nudge_log.metadata；这里只在 logger 留痕
        logger.debug(
            f"health_snapshot: state={stats.system_state} "
            f"errs={stats.error_count} avg={stats.average_processing_time_ms:.1f}ms"
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"health_snapshot: {e}")
        raise
