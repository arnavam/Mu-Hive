from datetime import datetime, timezone
from pymongo import MongoClient
from src.config.settings import MONGO_URI, MONGO_DB_NAME

class Database:
    def __init__(self):
        self.uri = MONGO_URI
        self.db_name = MONGO_DB_NAME
        self._client = None
        self._db = None

    @property
    def client(self):
        if self._client is None:
            self._client = MongoClient(self.uri)
        return self._client

    @property
    def db(self):
        if self._db is None:
            self._db = self.client[self.db_name]
        return self._db

    def get_collection(self, name="scraped_data"):
        return self.db[name]

    def save_scrape_result(self, url, mode, data, summary=None):
        collection = self.get_collection()
        doc = {
            "url": url,
            "mode": mode,
            "data": data,
            "summary": summary,
            "created_at": datetime.now(timezone.utc)
        }
        return collection.insert_one(doc)

# Singleton instance
db = Database()
