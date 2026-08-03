"""
AutoSkillGenerator：把 detector + generator + validator + publisher 串成一条管道。
由 NudgeScheduler 的 `pattern_mining` 任务周期性调用。
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger
from hyperbrain.hermes.auto_skill import (
    PatternDetector,
    SkillGenerator,
    SkillValidator,
    SkillPublisher,
)

logger = get_hermes_logger("auto_skill_generator")


class AutoSkillGenerator:
    """把四个子组件串起来的协调器。"""

    def __init__(
        self,
        *,
        db,
        model_manager,
        skill_loader,
        config,
    ):
        self.db = db
        self.model_manager = model_manager
        self.config = config
        self.detector = PatternDetector(db, config)
        self.generator = SkillGenerator(model_manager)
        self.validator = SkillValidator(import_whitelist=config.import_whitelist)
        self.publisher = SkillPublisher(db, skill_loader)

    def record(self, *, user_input, response, session_id=None,
               skills_invoked=None, success=True) -> str:
        """Brain.process 后调用：把一次交互写入 interaction_patterns。"""
        return self.detector.record_interaction(
            user_input=user_input,
            response=response,
            session_id=session_id,
            skills_invoked=skills_invoked,
            success=success,
        )

    async def scan_once(self) -> List[Dict[str, Any]]:
        """
        完整跑一遍：扫描 → 生成 → 验证 → 发布。
        返回本轮每个 intent 的处理结果。
        """
        if not self.config.enabled:
            logger.info("auto_skill disabled by config, skip")
            return []

        candidates = self.detector.scan()
        if not candidates:
            logger.debug("no pattern candidates")
            return []

        results: List[Dict[str, Any]] = []
        for c in candidates:
            intent_key = c["intent_key"]
            try:
                meta = await self.generator.generate(
                    intent_key=intent_key,
                    samples=c["samples"],
                )
                if not meta:
                    err = "LLM returned no valid JSON"
                    self.detector.mark_failed(intent_key, err)
                    results.append({"intent_key": intent_key, "success": False, "error": err})
                    continue

                v = self.validator.validate(meta["source_code"])
                if not v.success:
                    self.detector.mark_failed(intent_key, v.error)
                    self.publisher.rollback(
                        intent_key=intent_key,
                        skill_name=meta.get("skill_name", f"auto_{intent_key[:8]}"),
                        file_path=f"hyperbrain/skills/auto_generated/{meta.get('skill_name', intent_key)}.py",
                        error=v.error,
                    )
                    results.append({"intent_key": intent_key, "success": False, "error": v.error})
                    continue

                pub = self.publisher.publish(intent_key=intent_key, skill_meta=meta)
                if not pub.get("success"):
                    self.detector.mark_failed(intent_key, pub.get("error", "publish failed"))
                    results.append({"intent_key": intent_key, "success": False, "error": pub.get("error")})
                    continue

                results.append({
                    "intent_key": intent_key,
                    "success": True,
                    "skill_name": pub["skill_name"],
                    "file_path": pub["file_path"],
                })
                logger.info(f"auto skill created: {pub['skill_name']}")
            except Exception as e:  # noqa: BLE001
                logger.exception(f"scan_once item failed: {e}")
                self.detector.mark_failed(intent_key, str(e))
                results.append({"intent_key": intent_key, "success": False, "error": str(e)})
        return results
