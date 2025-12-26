import sqlite3
import os
import json

DB_PATH = "backend/library.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Enable JSON support if needed, but text is fine for simple lists
    
    # 1. Books Table
    # Stores the high-level "Book" concept (deduplicated)
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT,
        author TEXT COLLATE NOCASE,
        cover_image_path TEXT,
        description TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2. Book Files Table
    # Stores the actual physical files associated with a book (EPUB, PDF, etc)
    c.execute('''CREATE TABLE IF NOT EXISTS book_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id TEXT,
        file_path TEXT,
        format TEXT,
        file_size INTEGER,
        FOREIGN KEY(book_id) REFERENCES books(id)
    )''')

    # 3. Reading Progress Table
    c.execute('''CREATE TABLE IF NOT EXISTS reading_progress (
        book_id TEXT PRIMARY KEY,
        current_position REAL, -- 0.0 to 1.0 (Percentage) or Line Number
        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
        view_mode TEXT DEFAULT 'scroll', -- 'scroll' or 'flip'
        FOREIGN KEY(book_id) REFERENCES books(id)
    )''')

    conn.commit()
    conn.close()
    print(f"Library Database initialized at {DB_PATH}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    # Ensure backend dir exists
    os.makedirs("backend", exist_ok=True)
    init_db()
