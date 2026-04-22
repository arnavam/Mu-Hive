import logging
logger = logging.getLogger(__name__)

import datetime
from bson.objectid import ObjectId
try:
    from pymongo import MongoClient
except ImportError:
    logger.info("pymongo is not installed. Please run `pip install pymongo`.")
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
            result = self.events.insert_one(event_doc)
            return result.inserted_id
        except Exception as e:
            # Catch DuplicateKeyError or other errors
            logger.info(f"Error inserting into db: {e}")
            return None

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

def get_collection():
    """Retrieve the main 'events' collection directly."""
    return Database().events

def save_events(grouped: dict):
    """
    Parses the grouped events from eventslink_parser and stores them
    as 'not processed' so that the scraper_agent can pick them up.
    """
    db_obj = Database()
    inserted = 0
    modified = 0
    for ig, events_list in grouped.items():
        for event in events_list:
            title = event.get('eventName', 'Unknown')
            link = event.get('registrationLink', '')
            if not link:
                continue
                
            if not db_obj.link_exists(link, ig):
                doc_id = db_obj.insert_event(title, link, ig, "eventslink_parser", "not processed")
                if doc_id:
                    inserted += 1
                
                event_extras = {k: v for k, v in event.items() if k not in ["eventName", "registrationLink"]}
                if event_extras and doc_id:
                    db_obj.events.update_one({"_id": doc_id}, {"$set": {"parser_metadata": event_extras}})
            else:
                modified += 1
                
    db_obj.close()
    return inserted, modified

