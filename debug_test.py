import sys
sys.path.insert(0, r'e:\超脑\超脑002')
import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE interaction_patterns (id INTEGER PRIMARY KEY AUTOINCREMENT, intent_key TEXT, user_input TEXT, response TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
for i in range(3):
    conn.execute('INSERT INTO interaction_patterns (intent_key, user_input, response) VALUES (?, ?, ?)', ('abc', f'q{i}', f'a{i}'))
conn.commit()
rows = conn.execute("SELECT COUNT(*) FROM interaction_patterns WHERE created_at >= datetime('now', '-3600 seconds')").fetchone()
print('filtered rows:', rows[0])
all_rows = conn.execute('SELECT COUNT(*) FROM interaction_patterns').fetchone()
print('all rows:', all_rows[0])
