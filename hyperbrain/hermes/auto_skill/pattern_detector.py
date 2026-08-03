"""
模式检测器

职责：
- 监听 Brain.process 产生的新交互
- 把 (user_input, response) 映射到稳定的 intent_key
- 在滑动窗口内统计同 intent 出现频次
- 频次达到阈值时输出"待生成草稿"的 intent_key 集合

设计取舍：
- 不依赖外部 embedding 服务（项目无 ONNX/Torch 可用）
- 复用 HyperBrain 已有的 generate_text_embedding（md5 + n-gram）
- 即便 embedding 维度 / 矩阵缺失，也用 Jaccard / 关键词重叠做兜底
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from hyperbrain.hermes.common import (
    get_hermes_logger,
    intent_key_from_text,
)

logger = get_hermes_logger("pattern_detector")


class PatternDetector:
    """交互模式检测器"""

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.threshold = config.embedding_threshold
        self.window = config.window_seconds
        self.min_occ = config.min_occurrences
        self.cooldown = config.retry_cooldown_seconds

    # ---------- 公共 API ----------

    def record_interaction(
        self,
        *,
        user_input: str,
        response: str,
        session_id: Optional[str] = None,
        skills_invoked: Optional[List[str]] = None,
        success: bool = True,
    ) -> str:
        """
        写入一条交互模式记录，返回 intent_key。
        """
        intent_key = intent_key_from_text(user_input)
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    """
                    INSERT INTO interaction_patterns
                        (intent_key, user_input, response, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        intent_key,
                        user_input[:2000],
                        (response or "")[:2000],
                        session_id,
                        json.dumps(
                            {
                                "skills": skills_invoked or [],
                                "success": bool(success),
                                "ts": time.time(),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"record_interaction failed: {e}")
        return intent_key

    def scan(self) -> List[Dict[str, Any]]:
        """
        扫描滑动窗口内的所有 intent，返回频次达到阈值且"近期没失败过"的 intent 列表。

        Returns:
            list of dict: [{intent_key, count, samples: [user_input, ...], representative}]
        """
        # 用 SQLite 自己的 'now' 处理时区/字符串格式差异
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    """
                    SELECT intent_key, user_input, response
                    FROM interaction_patterns
                    WHERE created_at >= datetime('now', ?)
                    """,
                    (f"-{int(self.window)} seconds",),
                ).fetchall()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"scan query failed: {e}")
            return []

        if not rows:
            return []

        # 按 intent_key 分组
        grouped: Dict[str, List[Tuple[str, str]]] = {}
        for intent_key, ui, resp in rows:
            grouped.setdefault(intent_key, []).append((ui, resp))

        candidates: List[Dict[str, Any]] = []
        for intent_key, items in grouped.items():
            if len(items) < self.min_occ:
                continue
            unique_inputs = list({ui for ui, _ in items})
            # 24 小时冷却：最近是否已有失败记录
            if self._in_cooldown(conn=None, intent_key=intent_key):
                continue
            candidates.append(
                {
                    "intent_key": intent_key,
                    "count": len(items),
                    "unique_count": len(unique_inputs),
                    "samples": unique_inputs[:5],
                    "representative": unique_inputs[0],
                }
            )
        # 取出现频次最高的 max_drafts_per_run 个
        candidates.sort(key=lambda x: x["count"], reverse=True)
        return candidates[: self.config.max_drafts_per_run]

    def mark_failed(self, intent_key: str, error: str) -> None:
        """把一次失败写入 generated_skills（status=failed）以触发 24h 冷却。"""
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    """
                    INSERT OR REPLACE INTO generated_skills
                        (skill_name, file_path, intent_key, status, error_log, last_attempt_at)
                    VALUES (?, ?, ?, 'failed', ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        f"auto_{intent_key}",
                        f"hyperbrain/skills/auto_generated/{intent_key}.py",
                        intent_key,
                        error[:1000],
                    ),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"mark_failed: {e}")

    # ---------- 内部 ----------

    def _in_cooldown(self, conn, intent_key: str) -> bool:
        try:
            with self.db._get_connection() as conn:  # type: ignore[attr-defined]
                row = conn.execute(
                    """
                    SELECT last_attempt_at FROM generated_skills
                    WHERE intent_key = ? AND status = 'failed'
                    ORDER BY last_attempt_at DESC LIMIT 1
                    """,
                    (intent_key,),
                ).fetchone()
            if not row or not row[0]:
                return False
            # sqlite CURRENT_TIMESTAMP 形如 '2026-06-08 10:00:00'，与 time.time() 差较大；用 datetime 比较
            import datetime as _dt
            ts = _dt.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").timestamp()
            return (time.time() - ts) < self.cooldown
        except Exception as e:  # noqa: BLE001
            logger.debug(f"_in_cooldown check failed: {e}")
            return False
