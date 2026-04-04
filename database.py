import datetime
try:
    from pymongo import MongoClient
except ImportError:
    print("pymongo is not installed. Please run `pip install pymongo`.")
    raise

class Database:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="mu_hive"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.events = self.db['events']
        
        # Create an index on link to ensure uniqueness and fast lookup
        self.events.create_index("link", unique=True)
        
    def link_exists(self, link):
        """Check if an event with the given link already exists in the database."""
        return self.events.find_one({"link": link}) is not None
        
    def insert_event(self, title, link, keyword_used, source_engine, status):
        """Insert a new event into the database."""
        event_doc = {
            "title": title,
            "link": link,
            "keyword_used": keyword_used,
            "source_engine": source_engine,
            "status": status,
            "timestamp": datetime.datetime.utcnow()
        }
        try:
            self.events.insert_one(event_doc)
            return True
        except Exception as e:
            # Catch DuplicateKeyError or other errors
            print(f"Error inserting into db: {e}")
            return False

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
