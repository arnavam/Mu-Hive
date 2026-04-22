import json
from datetime import datetime, timezone
from psycopg2.extras import RealDictCursor
from src.db.connection import db_conn

class ScrapeRepository:
    """Handles all database operations related to raw scraped data."""

    @staticmethod
    def save(url, data):
        """Saves raw scraped data to the database."""
        with db_conn.get_cursor() as cur:
            json_data = json.dumps(data)
            cur.execute("""
                INSERT INTO scraped_data (url, data, created_at)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (url, json_data, datetime.now(timezone.utc)))
            return cur.fetchone()[0]

    @staticmethod
    def get_by_id(record_id):
        """Fetches a single scraped record by its ID."""
        with db_conn.get_cursor(factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scraped_data WHERE id = %s;", (record_id,))
            return cur.fetchone()

    @staticmethod
    def get_all():
        """Fetches all scraped data records ordered by date."""
        with db_conn.get_cursor(factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scraped_data ORDER BY created_at DESC;")
            return cur.fetchall()
