import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Resolve the absolute path to the data directory from the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "mu_hive.db"))

def get_connection():
    """Returns a new SQLite connection to the pipeline database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Creates the opportunities table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            ig_tags TEXT,
            quality_score INTEGER,
            is_processed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
