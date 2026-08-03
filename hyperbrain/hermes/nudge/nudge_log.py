"""
nudge_log：把每次 job 执行结果写入 nudge_log 表。
不持有任何缓存，每次写直接走 sqlite。
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("nudge_log")


class NudgeLog:
    def __init__(self, db):
        self.db = db

    def start(self, job_name: str) -> int:
        """写入一条 started_at=now 的日志，返回 row id。"""
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                cur = conn.execute(
                    """
                    INSERT INTO nudge_log (job_name, started_at, success)
                    VALUES (?, CURRENT_TIMESTAMP, 1)
                    """,
                    (job_name,),
                )
                return int(cur.lastrowid or 0)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"nudge_log.start failed: {e}")
            return 0

    def end(self, log_id: int, *, success: bool, error: Optional[str]) -> None:
        if not log_id:
            return
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                # 重新读 started_at 算 duration
                row = conn.execute(
                    "SELECT started_at FROM nudge_log WHERE id = ?", (log_id,)
                ).fetchone()
                duration_ms = None
                if row and row[0]:
                    import datetime as _dt
                    try:
                        ts = _dt.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").timestamp()
                        duration_ms = (time.time() - ts) * 1000.0
                    except Exception:
                        duration_ms = None
                conn.execute(
                    """
                    UPDATE nudge_log
                    SET ended_at = CURRENT_TIMESTAMP,
                        duration_ms = ?,
                        success = ?,
                        error = ?
                    WHERE id = ?
                    """,
                    (duration_ms, 1 if success else 0, (error or "")[:2000], log_id),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"nudge_log.end failed: {e}")

    def recent(self, job_name: str, limit: int = 20) -> list:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    """
                    SELECT id, job_name, started_at, ended_at, duration_ms, success, error
                    FROM nudge_log
                    WHERE job_name = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (job_name, int(limit)),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"nudge_log.recent failed: {e}")
            return []
