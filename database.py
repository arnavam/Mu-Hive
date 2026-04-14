import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(override=True)

class Database:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "ig_project")
        self._client = None
        self._db = None
        self._collection = None

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

    def save_scrape_result(self, url, mode, data):
        collection = self.get_collection()
        doc = {
            "url": url,
            "mode": mode,
            "data": data,
            "created_at": datetime.now(timezone.utc)
        }
        return collection.insert_one(doc)

# Singleton instance
db = Database()
