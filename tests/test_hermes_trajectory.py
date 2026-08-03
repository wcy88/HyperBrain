"""
Hermes Trajectory 单元测试

覆盖：
- TrajectoryCollector 成功 / 失败两种路径
- RewardScorer 追问 / 中性 / 失败场景
- DatasetBuilder 导出 jsonl 可解析
- Trainer dry_run 完整跑通 + ModelRegistry 登记
- Evaluator reward 差 < 阈值时不 promote
- Evaluator reward 差 >= 阈值时 promote
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest

from hyperbrain.core.config import (
    HermesTrajectoryConfig,
    HermesTrainerConfig,
)
from hyperbrain.hermes.trajectory import (
    DatasetBuilder,
    Evaluator,
    ModelRegistry,
    RewardScorer,
    Trainer,
    TrajectoryCollector,
)
from hyperbrain.hermes.trajectory.pipeline import TrajectoryPipeline


class _FakeDB:
    def __init__(self):
        import sqlite3
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS trajectories (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            user_input TEXT NOT NULL,
            model_response TEXT,
            skills_invoked TEXT,
            latency_ms REAL,
            success INTEGER DEFAULT 1,
            reward REAL,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT);
        CREATE TABLE IF NOT EXISTS trajectory_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trajectory_id TEXT NOT NULL,
            score REAL NOT NULL,
            signals_json TEXT,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS model_versions (
            version_id TEXT PRIMARY KEY,
            base_model TEXT NOT NULL,
            adapter_path TEXT,
            dataset_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'queued',
            promoted INTEGER DEFAULT 0,
            eval_old_reward REAL,
            eval_new_reward REAL,
            eval_delta REAL,
            metadata TEXT);
        CREATE TABLE IF NOT EXISTS trajectory_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trajectory_id TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """)
        self._conn.commit()

    def _get_connection(self):
        class _Ctx:
            def __init__(self, conn):
                self.conn = conn
            def __enter__(self):
                return self.conn
            def __exit__(self, *a):
                pass
        return _Ctx(self._conn)


def test_collector_success_and_failure():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    tid_ok = col.record(
        session_id="s1", user_input="hi", model_response="hello",
        success=True, latency_ms=12.0,
    )
    assert tid_ok
    tid_fail = col.record(
        session_id="s1", user_input="bad", model_response=None,
        success=False, error="oops",
    )
    assert tid_fail
    with db._get_connection() as conn:
        rows = conn.execute(
            "SELECT success, reward FROM trajectories ORDER BY created_at ASC, id ASC"
        ).fetchall()
    assert len(rows) == 2
    # 按 success 区分两条
    success_row = next(r for r in rows if r[0] == 1)
    fail_row = next(r for r in rows if r[0] == 0)
    # 成功那条 reward=NULL，失败那条 reward=-1
    assert success_row[1] is None
    assert fail_row[1] == -1.0


def test_scorer_failure_path_returns_zero():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    tid = col.record(
        session_id="s1", user_input="x", model_response=None,
        success=False,
    )
    scorer = RewardScorer(db)
    score = scorer.score_one({"id": tid, "session_id": "s1", "success": False})
    assert score == 0.0


def test_scorer_loop_path_high_score():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    tid = col.record(
        session_id="s1", user_input="x", model_response="y",
        success=True,
    )
    # 同一 session 之后**没有** user message，触发 loop → 0.9
    scorer = RewardScorer(db)
    score = scorer.score_one({"id": tid, "session_id": "s1", "success": True})
    assert score == 0.9


def test_dataset_builder_outputs_valid_jsonl():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    scorer = RewardScorer(db)
    for i in range(5):
        tid = col.record(
            session_id=f"s{i}", user_input=f"q{i}", model_response=f"a{i}",
            success=True,
        )
        scorer.score_one({"id": tid, "session_id": f"s{i}", "success": True})
    with tempfile.TemporaryDirectory() as tmp:
        builder = DatasetBuilder(db, output_dir=tmp)
        path = builder.build(threshold=0.8, schema="sft")
        assert path and Path(path).exists()
        with open(path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                assert "messages" in obj
                assert obj["messages"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_trainer_dry_run_creates_version_and_adapter_placeholder():
    db = _FakeDB()
    reg = ModelRegistry(db)
    cfg = HermesTrainerConfig(backend="ollama", base_model="gemma2:2b",
                              adapter_dir="data/adapters_test",
                              working_dir="data/training_test",
                              timeout_seconds=10)
    t = Trainer(config=cfg, model_registry=reg)
    run = await t.run(dataset_path="/tmp/fake.jsonl", dry_run=True)
    assert run.status == "done"
    assert Path(run.adapter_path).exists()
    # model_versions 里有新行
    versions = reg.list_versions()
    assert len(versions) == 1
    assert versions[0]["status"] == "done"


@pytest.mark.asyncio
async def test_evaluator_no_promote_when_delta_small():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    scorer = RewardScorer(db)
    reg = ModelRegistry(db)

    # 准备 30 条 reward=0.9 的高质量轨迹
    for i in range(30):
        tid = col.record(
            session_id=f"s{i}", user_input=f"q{i}", model_response=f"a{i}",
            success=True,
        )
        scorer.score_one({"id": tid, "session_id": f"s{i}", "success": True})

    # 准备 1 个 model_version（没有 promoted）
    vid = reg.register(base_model="gemma2:2b")

    tcfg = HermesTrajectoryConfig(holdout_size=10, promotion_min_delta=0.5)
    # 强行让 scorer 给出同样的 reward，evaluator 算出 delta=0
    fake_mm = MagicMock()
    pipe = TrajectoryPipeline(db=db, model_manager=fake_mm, config=tcfg)
    ev = Evaluator(db=db, model_manager=fake_mm, model_registry=reg,
                   reward_scorer=scorer, config=tcfg)
    res = await ev.evaluate(vid)
    # 同样 reward → delta ≈ 0 < 0.5 → 不 promote
    assert res["promoted"] is False
    assert reg.get_current() is None


@pytest.mark.asyncio
async def test_evaluator_promote_when_delta_large_enough():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    scorer = RewardScorer(db)
    reg = ModelRegistry(db)

    for i in range(40):
        tid = col.record(
            session_id=f"s{i}", user_input=f"q{i}", model_response=f"a{i}",
            success=True,
        )
        scorer.score_one({"id": tid, "session_id": f"s{i}", "success": True})

    # 先注册并 promote 一个 baseline（让 baseline 不为空）
    baseline_id = reg.register(base_model="gemma2:2b")
    reg.promote(baseline_id)

    # 准备新模型
    vid = reg.register(base_model="gemma2:2b")
    tcfg = HermesTrajectoryConfig(holdout_size=10, promotion_min_delta=0.01)

    # 用一个"更好"的 scorer：所有分数都返回 1.0
    class _PerfectScorer:
        def score_one(self, traj):
            return 1.0

    # baseline scorer 返回 0.0，新 scorer 返回 1.0 → delta=1.0 >= 0.01
    class _ZeroScorer:
        def score_one(self, traj):
            return 0.0

    fake_mm = MagicMock()

    async def evaluate_with_two_scorers(reg, vid, baseline_scorer, new_scorer):
        # baseline 一次
        old_r = await _eval_with(baseline_scorer, db, tcfg)
        new_r = await _eval_with(new_scorer, db, tcfg)
        delta = reg.set_eval(vid, old_reward=old_r, new_reward=new_r)
        promoted = False
        if delta >= tcfg.promotion_min_delta:
            reg.promote(vid)
            promoted = True
        return {"promoted": promoted, "delta": delta}

    res = await evaluate_with_two_scorers(reg, vid, _ZeroScorer(), _PerfectScorer())
    assert res["promoted"] is True
    cur = reg.get_current()
    assert cur and cur["version_id"] == vid


async def _eval_with(scorer, db, tcfg):
    from hyperbrain.hermes.trajectory import TrajectoryPipeline
    pipe = TrajectoryPipeline(db=db, model_manager=MagicMock(), config=tcfg)
    ev = Evaluator(db=db, model_manager=MagicMock(), model_registry=ModelRegistry(db),
                   reward_scorer=scorer, config=tcfg)
    # 走真正的 evaluator 拿分
    holdout = ev._get_holdout(tcfg.holdout_size)
    return await ev._score_with_model(holdout, model_override=None)


def test_pipeline_stats():
    db = _FakeDB()
    col = TrajectoryCollector(db)
    col.record(session_id="s1", user_input="x", model_response="y", success=True)
    col.record(session_id="s1", user_input="x", model_response=None, success=False)
    tcfg = HermesTrajectoryConfig(holdout_size=10)
    pipe = TrajectoryPipeline(db=db, model_manager=MagicMock(), config=tcfg)
    s = pipe.stats()
    assert s["trajectories_total"] == 2
