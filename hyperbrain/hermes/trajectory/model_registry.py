"""
模型版本注册表

- model_versions 表的封装
- register / promote / get_current
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("model_registry")


class ModelRegistry:
    def __init__(self, db):
        self.db = db

    def register(
        self,
        *,
        base_model: str,
        adapter_path: Optional[str] = None,
        dataset_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        version_id = f"v_{uuid.uuid4().hex[:12]}"
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    """
                    INSERT INTO model_versions
                        (version_id, base_model, adapter_path, dataset_path, status, metadata)
                    VALUES (?, ?, ?, ?, 'queued', ?)
                    """,
                    (
                        version_id,
                        base_model,
                        adapter_path,
                        dataset_path,
                        json.dumps(metadata or {}, ensure_ascii=False)[:2000],
                    ),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"register model failed: {e}")
        return version_id

    def update_status(self, version_id: str, status: str) -> None:
        if status not in {"queued", "running", "done", "failed"}:
            return
        try:
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE model_versions SET status = ? WHERE version_id = ?",
                    (status, version_id),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"update_status failed: {e}")

    def set_eval(
        self,
        version_id: str,
        *,
        old_reward: float,
        new_reward: float,
    ) -> float:
        delta = new_reward - old_reward
        try:
            with self.db._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE model_versions
                    SET eval_old_reward = ?, eval_new_reward = ?, eval_delta = ?
                    WHERE version_id = ?
                    """,
                    (old_reward, new_reward, delta, version_id),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"set_eval failed: {e}")
        return delta

    def promote(self, version_id: str) -> None:
        """把指定版本设为生产；其他版本 demote。"""
        try:
            with self.db._get_connection() as conn:
                conn.execute("UPDATE model_versions SET promoted = 0")
                conn.execute(
                    "UPDATE model_versions SET promoted = 1 WHERE version_id = ?",
                    (version_id,),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"promote failed: {e}")

    def get_current(self) -> Optional[Dict[str, Any]]:
        try:
            with self.db._get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT * FROM model_versions
                    WHERE promoted = 1
                    ORDER BY created_at DESC LIMIT 1
                    """,
                ).fetchone()
            return dict(row) if row else None
        except Exception:  # noqa: BLE001
            return None

    def list_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            with self.db._get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT version_id, base_model, adapter_path, status,
                           promoted, eval_old_reward, eval_new_reward, eval_delta,
                           created_at
                    FROM model_versions ORDER BY created_at DESC LIMIT ?
                    """,
                    (int(limit),),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:  # noqa: BLE001
            return []
