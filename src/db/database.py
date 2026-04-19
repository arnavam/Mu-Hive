import datetime
import os
import logging
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv

try:
    from pymongo import MongoClient
except ImportError:
    print("pymongo is not installed. Please run `pip install pymongo`.")
    raise

logger = logging.getLogger(__name__)
load_dotenv()

class Database:
    def __init__(self, uri=None, db_name="mu_hive"):
        if not uri:
            uri = os.getenv("MONGO_URI", "")
        
        # If separate credentials are provided, build the URI from parts
        mongo_user = os.getenv("MONGO_USER", "")
        mongo_pass = os.getenv("MONGO_PASS", "")
        mongo_host = os.getenv("MONGO_HOST", "")
        
        if mongo_user and mongo_pass and mongo_host:
            # Build URI from individual components (handles special chars in password)
            uri = f"mongodb+srv://{quote_plus(mongo_user)}:{quote_plus(mongo_pass)}@{mongo_host}"
            logger.info("Built MongoDB URI from MONGO_USER/MONGO_PASS/MONGO_HOST")
        elif uri:
            # Try to encode credentials in the provided URI
            # Handle passwords containing @ by splitting from the right
            match = re.match(r'^(mongodb(?:\+srv)?://)(.+)@([^@]+)$', uri)
            if match:
                scheme, userinfo, hostinfo = match.groups()
                if ':' in userinfo:
                    user, password = userinfo.split(':', 1)
                    uri = f"{scheme}{quote_plus(user)}:{quote_plus(password)}@{hostinfo}"
        else:
            uri = "mongodb://localhost:27017/"
        
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.opportunities = self.db['opportunities']
        
        # Create an index on link to ensure uniqueness and fast lookup
        self.opportunities.create_index([("link", 1)], unique=True)
        
    def link_exists(self, link):
        return self.opportunities.find_one({"link": link}) is not None
        
    def insert_opportunity(self, title, link, summary="", source_engine="RSS", ig_tags=None, is_processed=False):
        """Insert a new opportunity event into the database."""
        event_doc = {
            "title": title,
            "link": link,
            "summary": summary,
            "source_engine": source_engine,
            "status": "not processed" if not is_processed else "processed",
            "is_processed": is_processed,
            "ig_tags": ig_tags if ig_tags else [],
            "quality_score": None,
            "created_at": datetime.datetime.now(datetime.UTC),
            "scraped_full_text": None,
            "scrape_layer": None
        }
        try:
            self.opportunities.insert_one(event_doc)
            return True
        except Exception as e:
            # Catch DuplicateKeyError
            return False

    def find_pending_scrape(self, limit=50):
        """Opportunities inserted that haven't been scraped for full HTML text."""
        return list(
            self.opportunities.find({
                "status": "not processed", 
                "scraped_full_text": None,
                "scrape_error": {"$exists": False}
            }).limit(limit)
        )

    def update_event_scrape(self, doc_id, status, scraped_page_title=None, scraped_meta_description=None, scraped_full_text=None, scrape_layer=None, scrape_error=None):
        """Attach scrape results to the document identified by _id."""
        fields = {
            "status": status,
            "scraped_at": datetime.datetime.now(datetime.UTC),
        }
        if scraped_page_title:
            fields["title"] = scraped_page_title # override title
        if scraped_meta_description:
            fields["summary"] = scraped_meta_description
        if scraped_full_text:
            fields["scraped_full_text"] = scraped_full_text
        if scrape_layer:
            fields["scrape_layer"] = scrape_layer
        if scrape_error:
            fields["scrape_error"] = scrape_error

        result = self.opportunities.update_one({"_id": doc_id}, {"$set": fields})
        return result.modified_count > 0

    def get_unprocessed_for_intelligence(self, limit=15):
        """Get documents that have been scraped (or failed) but not evaluated by Intelligence."""
        return list(self.opportunities.find({
            "is_processed": False,
            "quality_score": None,
            "status": {"$ne": "not processed"}
        }).limit(limit))

    def update_intelligence(self, doc_id, final_score, ig_tags):
        result = self.opportunities.update_one(
            {"_id": doc_id},
            {"$set": {
                "quality_score": final_score,
                "ig_tags": ig_tags,
                "is_processed": True
            }}
        )
        return result.modified_count > 0

    def get_top_opportunities_by_ig(self, ig, limit=5):
        return list(self.opportunities.find(
            {
                "ig_tags": ig,
                "quality_score": {"$gte": 5}
            }
        ).sort("quality_score", -1).limit(limit))

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = Database()
    logger.info("MongoDB connection verified. Existing collections: " + str(db.db.list_collection_names()))
    db.close()
