"""
Trajectory 采集器

- 暴露 `record(processing_result, ...)`，幂等写入 trajectories 表
- 成功 / 失败两种路径都记录；失败 reward 写 -1.0 哨兵
- 由 Brain.process 显式调用
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("trajectory_collector")


class TrajectoryCollector:
    def __init__(self, db):
        self.db = db

    def record(
        self,
        *,
        session_id: Optional[str],
        user_input: str,
        model_response: Optional[str],
        skills_invoked: Optional[list] = None,
        latency_ms: float = 0.0,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        写入一条轨迹，返回 trajectory_id。

        成功：reward=NULL，等 reward_scorer 后填
        失败：reward=-1.0 哨兵
        """
        traj_id = f"t_{uuid.uuid4().hex[:16]}"
        reward = None if success else -1.0
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    """
                    INSERT OR REPLACE INTO trajectories
                        (id, session_id, user_input, model_response,
                         skills_invoked, latency_ms, success, reward,
                         error, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """,
                    (
                        traj_id,
                        session_id,
                        (user_input or "")[:4000],
                        (model_response or "")[:4000] if model_response else None,
                        json.dumps(skills_invoked or [], ensure_ascii=False)[:2000],
                        float(latency_ms or 0.0),
                        1 if success else 0,
                        reward,
                        (error or "")[:1000],
                        json.dumps(metadata or {}, ensure_ascii=False)[:2000],
                    ),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"trajectory record failed: {e}")
            return ""
        return traj_id

    def list_pending(self, limit: int = 200) -> list:
        """列出 reward IS NULL 的轨迹。"""
        try:
            with self.db._get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, session_id, user_input, model_response, success, created_at
                    FROM trajectories
                    WHERE reward IS NULL
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (int(limit),),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"list_pending failed: {e}")
            return []

    def count(self) -> int:
        try:
            with self.db._get_connection() as conn:
                return int(conn.execute("SELECT COUNT(*) FROM trajectories").fetchone()[0] or 0)
        except Exception:  # noqa: BLE001
            return 0

    def avg_reward(self) -> Optional[float]:
        try:
            with self.db._get_connection() as conn:
                row = conn.execute(
                    "SELECT AVG(reward) FROM trajectories WHERE reward IS NOT NULL AND reward >= 0"
                ).fetchone()
            if not row or row[0] is None:
                return None
            return float(row[0])
        except Exception:  # noqa: BLE001
            return None
