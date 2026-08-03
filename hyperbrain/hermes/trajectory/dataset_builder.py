"""
训练数据集构造器

- 选 score >= threshold 的轨迹
- 去重 key = (user_input[:200], response[:200])
- 输出 jsonl（每行 {messages: [...], source, score}，SFT/DPO 通用）
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("dataset_builder")


class DatasetBuilder:
    def __init__(self, db, output_dir: str = "data/training"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        *,
        threshold: float = 0.8,
        schema: str = "sft",
        limit: int = 5000,
    ) -> Optional[str]:
        """
        Returns:
            输出文件路径；没有样本则返回 None。
        """
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    """
                    SELECT id, user_input, model_response, reward
                    FROM trajectories
                    WHERE reward IS NOT NULL AND reward >= ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (float(threshold), int(limit)),
                ).fetchall()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"dataset query failed: {e}")
            return None

        if not rows:
            return None

        seen = set()
        out: List[Dict[str, Any]] = []
        for r in rows:
            key = hashlib.md5(
                ((r[1] or "")[:200] + "||" + (r[2] or "")[:200]).encode("utf-8")
            ).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            if schema == "dpo":
                out.append(
                    {
                        "prompt": r[1] or "",
                        "chosen": r[2] or "",
                        "rejected": "",
                        "source": "trajectory",
                        "score": float(r[3] or 0.0),
                    }
                )
            else:
                out.append(
                    {
                        "messages": [
                            {"role": "user", "content": r[1] or ""},
                            {"role": "assistant", "content": r[2] or ""},
                        ],
                        "source": "trajectory",
                        "score": float(r[3] or 0.0),
                    }
                )

        if not out:
            return None

        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = self.output_dir / f"traj_{schema}_{ts}.jsonl"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                for item in out:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            logger.error(f"dataset write failed: {e}")
            return None
        logger.info(f"dataset built: {out_path} ({len(out)} samples)")
        return str(out_path)

    def count_pending(self, threshold: float = 0.8) -> int:
        """返回 score >= threshold 且尚未导出（或已导出但你想重新看）的轨迹数。"""
        try:
            with self.db._get_connection() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM trajectories WHERE reward IS NOT NULL AND reward >= ?",
                    (float(threshold),),
                ).fetchone()
            return int(row[0] or 0)
        except Exception:  # noqa: BLE001
            return 0
