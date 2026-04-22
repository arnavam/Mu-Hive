import psycopg2
from psycopg2.extras import RealDictCursor
from src.config.settings import DATABASE_URL

class DatabaseConnection:
    def __init__(self):
        self.url = DATABASE_URL
        self._conn = None

    def get_connection(self):
        """Returns a persistent database connection."""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.url)
                self._conn.autocommit = True
            except Exception as e:
                print(f"[!] Database Connection Error: {e}")
                raise e
        return self._conn

    def get_cursor(self, factory=None):
        """Returns a cursor from the current connection."""
        conn = self.get_connection()
        return conn.cursor(cursor_factory=factory)

# Shared connection instance
db_conn = DatabaseConnection()
