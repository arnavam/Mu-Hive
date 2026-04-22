from datetime import datetime, timezone
from src.db.connection import db_conn

class EventRepository:
    """Handles all database operations related to structured events."""

    @staticmethod
    def upsert(event_data):
        """
        Upserts an event based on the link.
        Updates all fields and updated_at on conflict.
        """
        with db_conn.get_cursor() as cur:
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
