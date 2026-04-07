import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'stats.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    ''')
    for key in ['messages_safe', 'messages_ban', 'bans_confirmed', 'false_positives', 'false_negatives']:
        cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0)', (key,))
    conn.commit()
    conn.close()

def get_stat(key: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM stats WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_stat(key: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE stats SET value = value + 1 WHERE key = ?', (key,))
    cursor.execute('SELECT value FROM stats WHERE key = ?', (key,))
    new_value = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_value