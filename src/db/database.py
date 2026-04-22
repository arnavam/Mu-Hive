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
    def save_scrape_result(self, url, data):
        return self.scrapes.save(url, data)

    def get_scrape_result(self, record_id):
        return self.scrapes.get_by_id(record_id)

    def get_all_results(self):
        return self.scrapes.get_all()

    def upsert_event(self, event_data):
        return self.events.upsert(event_data)

# Singleton instance for the application
db = DatabaseFacade()
