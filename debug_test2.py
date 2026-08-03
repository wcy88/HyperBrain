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

# 直接看 db
with db._get_connection() as conn:
    rows = conn.execute("SELECT * FROM interaction_patterns").fetchall()
    print('Direct count:', len(rows))
    for r in rows:
        print('row:', dict(r))

# 看 intent_key
from hyperbrain.hermes.common import intent_key_from_text
print('intent_key_for "查天气":', intent_key_from_text("查天气"))

# scan
cands = det.scan()
print('cands:', cands)
