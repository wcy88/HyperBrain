import sys
sys.path.insert(0, r'e:\超脑\超脑002')
from hyperbrain.core.brain import get_brain
b = get_brain()
with b.db._get_connection() as conn:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
hermes_tables = [r[0] for r in rows if any(
    k in r[0] for k in ('interaction', 'generated_skill', 'nudge_log', 'trajector', 'model_vers', 'trajectory_f')
)]
print('Hermes tables:', hermes_tables)
