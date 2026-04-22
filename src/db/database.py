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
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    type TEXT,
                    platform TEXT,
                    location TEXT,
                    link TEXT UNIQUE,
                    days_left INTEGER,
                    ig TEXT,
                    score INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def save_scrape_result(self, url, data):
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Convert data to JSON string for the JSONB column
            json_data = json.dumps(data)
            cur.execute("""
                INSERT INTO scraped_data (url, data, created_at)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (url, json_data, datetime.now(timezone.utc)))
            return cur.fetchone()[0]

    def get_scrape_result(self, record_id):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scraped_data WHERE id = %s;", (record_id,))
            return cur.fetchone()


    def upsert_event(self, event_data):
        """
        Upserts an event based on the link.
        Updates all fields and updated_at on conflict.
        """
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (
                    title, type, platform, location, link, days_left, ig, score, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO UPDATE SET
                    title = EXCLUDED.title,
                    type = EXCLUDED.type,
                    platform = EXCLUDED.platform,
                    location = EXCLUDED.location,
                    days_left = EXCLUDED.days_left,
                    ig = EXCLUDED.ig,
                    score = EXCLUDED.score,
                    updated_at = EXCLUDED.updated_at
                RETURNING id;
            """, (
                event_data.get('title'),
                event_data.get('type'),
                event_data.get('platform'),
                event_data.get('location'),
                event_data.get('link'),
                event_data.get('days_left'),
                event_data.get('ig'),
                event_data.get('score'),
                datetime.now(timezone.utc)
            ))
            return cur.fetchone()[0]

    def get_all_results(self):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scraped_data ORDER BY created_at DESC;")
            return cur.fetchall()

# Singleton instance
db = Database()
