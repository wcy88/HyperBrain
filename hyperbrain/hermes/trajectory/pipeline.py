"""
Trajectory 训练管道协调器

- 把 collector / reward_scorer / dataset_builder / trainer / model_registry / evaluator 串起来
- 由 Brain 持有，对外暴露一个 `score_pending()` 给 nudge 调用
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger
from hyperbrain.hermes.trajectory.trajectory_collector import TrajectoryCollector
from hyperbrain.hermes.trajectory.reward_scorer import RewardScorer
from hyperbrain.hermes.trajectory.dataset_builder import DatasetBuilder
from hyperbrain.hermes.trajectory.trainer import Trainer
from hyperbrain.hermes.trajectory.model_registry import ModelRegistry
from hyperbrain.hermes.trajectory.evaluator import Evaluator

logger = get_hermes_logger("trajectory_pipeline")


class TrajectoryPipeline:
    def __init__(self, *, db, model_manager, config, trainer_config=None):
        self.config = config
        self.db = db
        self.model_manager = model_manager
        self.collector = TrajectoryCollector(db)
        self.scorer = RewardScorer(db)
        self.builder = DatasetBuilder(db, output_dir=config.output_dir)
        self.registry = ModelRegistry(db)
        # trainer_config 兼容外部传入；缺省时用 config 自带的 trainer 字段
        from hyperbrain.core.config import HermesTrainerConfig
        self.trainer_cfg = trainer_config if trainer_config is not None else getattr(
            config, "trainer", HermesTrainerConfig()
        )
        self.trainer = Trainer(config=self.trainer_cfg, model_registry=self.registry)
        self.evaluator = Evaluator(
            db=db,
            model_manager=model_manager,
            model_registry=self.registry,
            reward_scorer=self.scorer,
            config=config,
        )

    # ---------- Nudge 用 ----------

    def score_pending(self, limit: int = 200) -> int:
        return self.scorer.score_pending(limit=limit)

    def build_dataset(self, threshold: Optional[float] = None,
                      schema: str = "sft") -> Optional[str]:
        return self.builder.build(
            threshold=threshold or self.config.reward_threshold,
            schema=schema,
        )

    async def maybe_train(self) -> Optional[Dict[str, Any]]:
        """训练门禁：>= min_new_samples 才触发。"""
        if not self.trainer_cfg.enabled:
            return None
        pending = self.builder.count_pending(self.config.reward_threshold)
        if pending < self.trainer_cfg.min_new_samples:
            return None
        dataset = self.build_dataset()
        if not dataset:
            return None
        run = await self.trainer.run(
            dataset_path=dataset, base_model=self.trainer_cfg.base_model
        )
        if run.status != "done":
            return {"version_id": run.version_id, "status": run.status, "error": run.error}
        eval_result = await self.evaluator.evaluate(run.version_id)
        return {"training": run, "evaluation": eval_result}

    # ---------- 统计 ----------

    def stats(self) -> Dict[str, Any]:
        return {
            "trajectories_total": self.collector.count(),
            "avg_reward": self.collector.avg_reward(),
            "current_model": (self.registry.get_current() or {}).get("version_id"),
        }
