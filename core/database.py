import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "vnlist.db")
COVERS_PATH = os.path.join("data", "covers")

def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs(COVERS_PATH, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            score INTEGER NOT NULL,
            comment TEXT,
            vndb_url TEXT,
            cover_image_path TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_game(title, score, comment, vndb_url, cover_image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO games (title, score, comment, vndb_url, cover_image_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, score, comment, vndb_url, cover_image_path, now, now))
    conn.commit()
    conn.close()

def update_game(game_id, title, score, comment, vndb_url, cover_image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE games 
        SET title = ?, score = ?, comment = ?, vndb_url = ?, cover_image_path = ?, updated_at = ?
        WHERE id = ?
    ''', (title, score, comment, vndb_url, cover_image_path, now, game_id))
    conn.commit()
    conn.close()

def delete_game(game_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()

def get_all_games():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games ORDER BY score DESC, created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
