from src.db.schema import initialize_schema
from src.db.repositories.scrape_repository import ScrapeRepository
from src.db.repositories.event_repository import EventRepository

class DatabaseFacade:
    """
    A unified interface for the database system.
    This class coordinates schema initialization and delegates work to specific repositories.
    """
    def __init__(self):
        # Automatically initialize schema on startup
        initialize_schema()
        self.scrapes = ScrapeRepository()
        self.events = EventRepository()

    # Backward compatibility methods for existing code
    def save_scrape_result(self, title, url, ig, status, data, scraped_at=None):
        return self.scrapes.save(title, url, ig, status, data, scraped_at)

    def get_scrape_result(self, record_id):
        return self.scrapes.get_by_id(record_id)

    def get_all_results(self):
        return self.scrapes.get_all()

    def upsert_event(self, event_data):
        return self.events.upsert(event_data)

    # ----------------------------------------------------
    # MongoDB Backwards Compatibility Wrappers
    # ----------------------------------------------------
    def link_exists(self, link, keyword):
        return self.scrapes.link_exists(link, keyword)
        
    def insert_event(self, title, link, keyword_used, source_engine, status):
        return self.scrapes.insert_queue(title, link, keyword_used, source_engine, status)
        
    def find_pending_scrape(self, limit=50):
        rows = self.scrapes.find_pending(limit=limit)
        # Adapt keys for the scraper scripts expecting MongoDB dicts
        for row in rows:
            row['_id'] = row['id']
            row['link'] = row['url']
        return rows
        
    def update_event_scrape(self, doc_id, status, scraped_page_title=None, scraped_meta_description=None, scraped_full_text=None, scrape_layer=None, scrape_error=None):
        scrape_data = {}
        if scraped_page_title: scrape_data['scraped_page_title'] = scraped_page_title
        if scraped_meta_description: scrape_data['scraped_meta_description'] = scraped_meta_description
        if scraped_full_text: scrape_data['scraped_full_text'] = scraped_full_text
        if scrape_error: scrape_data['scrape_error'] = scrape_error
        
        return self.scrapes.update_scrape(doc_id, status, scrape_layer, scrape_data)
        
    def close(self):
        # Postgres connection is persistent, ignore.
        pass

# MongoDB drop-in replacement naming
Database = DatabaseFacade

def save_events(grouped: dict):
    db_obj = DatabaseFacade()
    inserted, modified = 0, 0
    for ig, events_list in grouped.items():
        for event in events_list:
            if hasattr(event, 'model_dump'): event = event.model_dump()
            elif hasattr(event, 'dict'): event = event.dict()
            elif not isinstance(event, dict): event = vars(event)
            
            title = event.get('eventName', 'Unknown')
            link = event.get('registrationLink', '')
            if not link: continue
            
            if not db_obj.link_exists(link, ig):
                doc_id = db_obj.insert_event(title, link, ig, "eventslink_parser", "not processed")
                if doc_id: inserted += 1
            else:
                modified += 1
    return inserted, modified

# Singleton instance for the application
db = DatabaseFacade()
