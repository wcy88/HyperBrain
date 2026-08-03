"""
Hermes auto_skill 单元测试

覆盖：
- pattern_detector 同意图聚类
- skill_validator AST / 白名单 / 沙箱
- skill_publisher 写盘 + DB 登记
- 全链路 scan_once（mock LLM 返"恶意"或"正常"两种情况）
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from hyperbrain.hermes.auto_skill import (
    AutoSkillGenerator,
    PatternDetector,
    SkillGenerator,
    SkillPublisher,
    SkillValidator,
)
from hyperbrain.hermes.auto_skill._embedding_fallback import jaccard
from hyperbrain.core.config import HermesAutoSkillConfig


class _FakeDB:
    """最小 SQLite 替身，模拟 _get_connection 上下文管理器。"""

    def __init__(self):
        import sqlite3
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        # 复制真实 schema
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS interaction_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_key TEXT NOT NULL,
            user_input TEXT NOT NULL,
            response TEXT NOT NULL,
            session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT);
        CREATE TABLE IF NOT EXISTS generated_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            file_path TEXT NOT NULL,
            intent_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            error_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_attempt_at TIMESTAMP,
            metadata TEXT);
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


def test_intent_key_stable():
    from hyperbrain.hermes.common import intent_key_from_text
    a = intent_key_from_text("今天天气怎么样？")
    b = intent_key_from_text("今天天气怎么样")
    assert a == b, "stopword/punct 应不影响"
    assert isinstance(a, str) and len(a) == 10


def test_jaccard_basic():
    assert jaccard("hello world", "hello world") == 1.0
    assert 0.0 <= jaccard("apple", "orange") < 0.5


def test_pattern_detector_cluster():
    cfg = HermesAutoSkillConfig(window_seconds=3600, min_occurrences=3)
    det = PatternDetector(_FakeDB(), cfg)
    for s in ["查天气", "查天气", "查天气"]:
        det.record_interaction(user_input=s, response="ok")
    cands = det.scan()
    assert cands, "应至少 1 个候选"
    assert cands[0]["count"] >= 3
    # 关键：3 条都被压成同一个 intent_key
    keys = {c["intent_key"] for c in cands}
    assert len(keys) == 1


def test_skill_validator_rejects_malicious():
    v = SkillValidator(import_whitelist=["asyncio", "json", "re"])
    bad = "import os\nclass EvilSkill:\n    pass"
    res = v.validate(bad)
    assert res.success is False
    assert "import" in res.error.lower()


def test_skill_validator_passes_minimal_skill():
    from hyperbrain.skills.base import BaseSkill
    v = SkillValidator(import_whitelist=["asyncio", "json"])
    good = (
        "from hyperbrain.skills.base import BaseSkill, SkillResult\n"
        "class HelloSkill(BaseSkill):\n"
        "    name = 'hello_skill'\n"
        "    description = 'say hi'\n"
        "    async def execute(self, dry_run: bool = True, **kwargs):\n"
        "        return SkillResult(success=True, message='hi')\n"
    )
    res = v.validate(good)
    assert res.success, f"expected pass, got: {res.error}"


def test_skill_publisher_writes_file_and_db():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        (root / "auto_generated").mkdir(parents=True)
        db = _FakeDB()
        # 不实际接 loader（只在 publish 末尾 reload，而 reload 不传 loader 时不会崩）
        gen = SkillPublisher(db=db, skill_loader=None, skills_root=root)
        meta = {
            "skill_name": "test_skill_a",
            "class_name": "TestSkillA",
            "description": "demo",
            "category": "tools",
            "tags": ["auto"],
            "source_code": "x = 1",
        }
        out = gen.publish(intent_key="abc1234567", skill_meta=meta)
        assert out["success"]
        # 文件已写
        assert (root / "auto_generated" / "test_skill_a.py").exists()
        # DB 登记
        with db._get_connection() as conn:
            row = conn.execute(
                "SELECT status FROM generated_skills WHERE skill_name=?",
                ("test_skill_a",),
            ).fetchone()
        assert row and row[0] == "active"


def test_skill_publisher_rollback():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        (root / "auto_generated").mkdir(parents=True)
        db = _FakeDB()
        gen = SkillPublisher(db=db, skill_loader=None, skills_root=root)
        gen.rollback(
            intent_key="x",
            skill_name="nope",
            file_path=str(root / "auto_generated" / "nope.py"),
            error="syntax error",
        )
        with db._get_connection() as conn:
            row = conn.execute(
                "SELECT status, error_log FROM generated_skills WHERE skill_name=?",
                ("nope",),
            ).fetchone()
        assert row[0] == "failed"
        assert "syntax" in (row[1] or "")


def test_auto_skill_scan_marks_failed_on_bad_output(monkeypatch):
    """LLM 返 'import os' 的草稿 → validator 拒绝 → generated_skills status=failed。"""
    cfg = HermesAutoSkillConfig(min_occurrences=2, max_drafts_per_run=2)
    db = _FakeDB()
    det = PatternDetector(db, cfg)
    for s in ["计算 1+2", "计算 1+2"]:
        det.record_interaction(user_input=s, response="3")

    # mock LLM：返回带 import os 的恶意代码
    fake_mm = MagicMock()
    fake_mm.chat = AsyncMock(return_value=MagicMock(content=json.dumps({
        "skill_name": "bad_skill",
        "class_name": "BadSkill",
        "description": "x",
        "source_code": "import os\nx = 1",
    })))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        (root / "auto_generated").mkdir(parents=True)
        gen = AutoSkillGenerator(
            db=db,
            model_manager=fake_mm,
            skill_loader=None,
            config=cfg,
        )
        gen.publisher = SkillPublisher(db=db, skill_loader=None, skills_root=root)
        results = asyncio.run(gen.scan_once())
    assert results, "应返回 1 个结果"
    assert results[0]["success"] is False
    with db._get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM generated_skills WHERE intent_key=?",
            (results[0]["intent_key"],),
        ).fetchone()
    assert row and row[0] == "failed"
