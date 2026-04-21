import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from src.config.settings import DATABASE_URL

class Database:
    def __init__(self):
        self.url = DATABASE_URL
        self._conn = None
        self._init_db()

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.url)
            self._conn.autocommit = True
        return self._conn

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    data JSONB,
                    summary TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def save_scrape_result(self, url, data, summary=None):
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Convert data to JSON string for the JSONB column
            json_data = json.dumps(data)
            cur.execute("""
                INSERT INTO scraped_data (url, data, summary, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (url, json_data, summary, datetime.now(timezone.utc)))
            return cur.fetchone()[0]

    def get_all_results(self):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scraped_data ORDER BY created_at DESC;")
            return cur.fetchall()

# Singleton instance
db = Database()
