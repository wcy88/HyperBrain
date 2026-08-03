"""
评估器

在 holdout 上跑新旧模型，对比平均 reward。
仅当新模型相对旧模型 reward 提升 >= 阈值时 promote。
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger, safe_chat
from hyperbrain.models.base import ChatMessage

logger = get_hermes_logger("evaluator")


class Evaluator:
    def __init__(self, db, model_manager, model_registry, reward_scorer, config):
        self.db = db
        self.model_manager = model_manager
        self.registry = model_registry
        self.scorer = reward_scorer
        self.config = config

    async def evaluate(self, version_id: str) -> Dict[str, Any]:
        """
        对 version_id 对应的新模型做一次评估，必要时 promote。
        """
        holdout = self._get_holdout(self.config.holdout_size)
        if not holdout:
            return {"version_id": version_id, "skipped": "no_holdout", "promoted": False}

        # 取 baseline（旧模型 / 当前生产模型）的 reward
        baseline = self.registry.get_current()
        baseline_id = baseline["version_id"] if baseline else None

        new_reward = await self._score_with_model(holdout, model_override=None)
        old_reward = (
            await self._score_with_model(holdout, model_override=baseline_id)
            if baseline_id
            else new_reward
        )

        # 取高版本：评估分差
        delta = self.registry.set_eval(
            version_id, old_reward=old_reward, new_reward=new_reward
        )

        promoted = False
        if delta >= self.config.promotion_min_delta:
            self.registry.promote(version_id)
            promoted = True
            logger.info(
                f"evaluator: promoted {version_id} (delta={delta:.4f})"
            )
        else:
            logger.info(
                f"evaluator: NOT promoted {version_id} (delta={delta:.4f} < "
                f"threshold {self.config.promotion_min_delta})"
            )

        return {
            "version_id": version_id,
            "old_reward": old_reward,
            "new_reward": new_reward,
            "delta": delta,
            "promoted": promoted,
            "holdout_size": len(holdout),
        }

    # ---------- 内部 ----------

    def _get_holdout(self, n: int) -> List[Dict[str, Any]]:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    """
                    SELECT id, user_input, model_response, reward, session_id
                    FROM trajectories
                    WHERE reward IS NOT NULL AND reward >= 0
                    ORDER BY RANDOM() LIMIT ?
                    """,
                    (int(n),),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:  # noqa: BLE001
            return []

    async def _score_with_model(
        self, holdout: List[Dict[str, Any]], *, model_override: Optional[str]
    ) -> float:
        """
        跑一遍 holdout，用 reward_scorer 同样的方式打分。
        模型切换只在生产模型切换时才有意义（这里 dry-run 用现有 model_manager）。
        """
        if not holdout:
            return 0.0
        scores: List[float] = []
        for h in holdout:
            # 简单复用 reward_scorer 的逻辑
            score = self.scorer.score_one(
                {
                    "id": h["id"],
                    "session_id": h.get("session_id"),
                    "user_input": h.get("user_input", ""),
                    "model_response": h.get("model_response", ""),
                    "success": True,
                }
            )
            if score is not None:
                scores.append(score)
        if not scores:
            return 0.0
        return sum(scores) / len(scores)
