"""
Reward 评分器

三种信号合成 0-1 分：
1. 追问检测：同一 session 后续是否有 user message（追问 → 0.3，闭环 → 0.9）
2. 错误关联：轨迹失败 / 触发 evolution.record_error（截断到 0）
3. 显式反馈：trajectory_feedback 表（无则用 0.5）
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("reward_scorer")


class RewardScorer:
    def __init__(self, db):
        self.db = db

    def score_one(self, traj: Dict[str, Any]) -> Optional[float]:
        """
        单条评分；返回 [0, 1] 或 None（数据不足）。
        """
        traj_id = traj.get("id")
        if not traj_id:
            return None

        signals: Dict[str, Any] = {}

        # 1. 追问检测（如果 traj 缺 created_at，从 DB 补一次）
        if not traj.get("created_at"):
            traj = dict(traj)
            traj["created_at"] = self._fetch_created_at(traj_id)
        follow = self._detect_followup(traj)
        signals["followup"] = follow

        # 2. 错误关联
        if not traj.get("success", 1):
            signals["error_flag"] = True
            return 0.0  # 失败 → 0 分，不再叠加其他信号

        # 3. 显式反馈
        feedback = self._read_feedback(traj_id)
        signals["feedback"] = feedback

        # 合成：follow=0.9, followup=0.3, neutral=0.5
        if follow == "loop":
            base = 0.9
        elif follow == "followup":
            base = 0.3
        else:
            base = 0.5  # 中性

        # 显式反馈覆盖：up → +0.1，down → -0.2
        if feedback == "up":
            base = min(1.0, base + 0.1)
        elif feedback == "down":
            base = max(0.0, base - 0.2)

        score = round(base, 4)
        self._write(traj_id, score, signals)
        return score

    def _fetch_created_at(self, traj_id: str) -> Optional[str]:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                row = conn.execute(
                    "SELECT created_at FROM trajectories WHERE id = ?", (traj_id,)
                ).fetchone()
            return row[0] if row else None
        except Exception:  # noqa: BLE001
            return None

    def score_pending(self, limit: int = 200) -> int:
        """批量评分，返回成功条数。"""
        from .trajectory_collector import TrajectoryCollector
        col = TrajectoryCollector(self.db)
        pending = col.list_pending(limit=limit)
        n = 0
        for t in pending:
            try:
                if self.score_one(t) is not None:
                    n += 1
            except Exception as e:  # noqa: BLE001
                logger.warning(f"score_one failed for {t.get('id')}: {e}")
        return n

    # ---------- 内部 ----------

    def _detect_followup(self, traj: Dict[str, Any]) -> str:
        """
        看同一 session 在这条 trajectory 之后是否还有 user message。
        - "loop"     : 没有追问，视为闭环
        - "followup" : 有追问但 5 分钟内没有 assistant 回答
        - "neutral"  : 数据不足
        """
        session_id = traj.get("session_id")
        created_at = traj.get("created_at")
        if not session_id or not created_at:
            return "neutral"
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                # 后续有没有 user role 的对话
                rows = conn.execute(
                    """
                    SELECT 1 FROM conversations
                    WHERE session_id = ? AND role = 'user' AND timestamp > ?
                    LIMIT 1
                    """,
                    (session_id, created_at),
                ).fetchall()
            return "loop" if not rows else "followup"
        except Exception:  # noqa: BLE001
            return "neutral"

    def _read_feedback(self, traj_id: str) -> Optional[str]:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                row = conn.execute(
                    """
                    SELECT feedback_type FROM trajectory_feedback
                    WHERE trajectory_id = ? ORDER BY id DESC LIMIT 1
                    """,
                    (traj_id,),
                ).fetchone()
            return row[0] if row else None
        except Exception:  # noqa: BLE001
            return None

    def _write(self, traj_id: str, score: float, signals: Dict[str, Any]) -> None:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                # 写 trajectory_rewards
                conn.execute(
                    """
                    INSERT INTO trajectory_rewards (trajectory_id, score, signals_json)
                    VALUES (?, ?, ?)
                    """,
                    (traj_id, float(score), json.dumps(signals, ensure_ascii=False)[:2000]),
                )
                # 反写 trajectories.reward
                conn.execute(
                    "UPDATE trajectories SET reward = ? WHERE id = ?",
                    (float(score), traj_id),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"reward write failed: {e}")
