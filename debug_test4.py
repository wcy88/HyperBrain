import sys
sys.path.insert(0, r'e:\超脑\超脑002')
import sqlite3
from hyperbrain.hermes.trajectory.trajectory_collector import TrajectoryCollector

class _FakeDB:
    def __init__(self):
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

db = _FakeDB()
col = TrajectoryCollector(db)
tid_ok = col.record(session_id="s1", user_input="hi", model_response="hello", success=True)
print('tid_ok:', tid_ok)
tid_fail = col.record(session_id="s1", user_input="bad", model_response=None, success=False, error="oops")
print('tid_fail:', tid_fail)
