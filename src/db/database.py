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
        self.events.create_index([("link", 1), ("keyword_used", 1)],unique=True)
        
    def link_exists(self, link, keyword):
        return self.events.find_one({
            "link": link,
            "keyword_used": keyword
        }) is not None
        
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

    def find_pending_scrape(self, limit=50):
        """Events inserted by the search agent with status 'not processed'."""
        return list(
            self.events.find({"status": "not processed"}).limit(limit)
        )

    def update_event_scrape(
        self,
        doc_id,
        status,
        scraped_page_title=None,
        scraped_meta_description=None,
        scraped_full_text=None,
        scrape_layer=None,
        scrape_error=None,
    ):
        """Attach scrape results to the event document identified by _id."""
        fields = {
            "status": status,
            "scraped_at": datetime.datetime.utcnow(),
        }
        if scraped_page_title is not None:
            fields["scraped_page_title"] = scraped_page_title
        if scraped_meta_description is not None:
            fields["scraped_meta_description"] = scraped_meta_description
        if scraped_full_text is not None:
            fields["scraped_full_text"] = scraped_full_text
        if scrape_layer is not None:
            fields["scrape_layer"] = scrape_layer
        if scrape_error is not None:
            fields["scrape_error"] = scrape_error
        else:
            fields["scrape_error"] = None

        result = self.events.update_one({"_id": doc_id}, {"$set": fields})
        return result.modified_count > 0

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
