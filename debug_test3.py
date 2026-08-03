import sys
sys.path.insert(0, r'e:\超脑\超脑002')
import sqlite3
from hyperbrain.core.config import HermesAutoSkillConfig
from hyperbrain.hermes.auto_skill.pattern_detector import PatternDetector

class _FakeDB:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
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

cfg = HermesAutoSkillConfig(window_seconds=3600, min_occurrences=3)
db = _FakeDB()
det = PatternDetector(db, cfg)
for s in ["查天气", "查天气", "查天气"]:
    det.record_interaction(user_input=s, response="ok")

# 直接模拟 scan 的查询
with db._get_connection() as conn:
    rows = conn.execute(
        """
        SELECT intent_key, user_input, response
        FROM interaction_patterns
        WHERE created_at >= datetime('now', ?)
        """,
        ("-3600 seconds",),
    ).fetchall()
    print('Filtered rows:', len(rows))
    for r in rows:
        print(dict(r))

# 试试 -3600 second
with db._get_connection() as conn:
    rows2 = conn.execute(
        """
        SELECT datetime('now', ?)
        """,
        ("-3600 seconds",),
    ).fetchall()
    print('now-3600:', rows2)

with db._get_connection() as conn:
    rows3 = conn.execute(
        """
        SELECT created_at, datetime('now', '-3600 seconds') FROM interaction_patterns
        """,
    ).fetchall()
    print('compare:', rows3[:1])
