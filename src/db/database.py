"""
src/db/database.py
==================
MongoDB database layer with DNS pre-resolution for restricted networks.

Public API:
    get_collection() → pymongo Collection
    save_events(grouped) → (count, 0)
"""

import os
import pymongo
from pymongo import UpdateOne
from datetime import datetime, timezone
import dotenv

try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None

# Force Google DNS for SRV record resolution
# (bypasses restricted college/corporate DNS that blocks MongoDB Atlas)
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]
except ImportError:
    pass

# Load environment variables from project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv.load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# ---------------------------------------------------------------------------
# Cached MongoClient singleton
# ---------------------------------------------------------------------------

_cached_client = None


def _get_client() -> pymongo.MongoClient:
    """
    Return a cached MongoClient. The SRV DNS lookup happens only once
    at first call, then the client is reused for all subsequent calls.
    """
    global _cached_client

    if _cached_client is not None:
        return _cached_client

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set")

    conn_kwargs = {
        "serverSelectionTimeoutMS": 30000,
        "connectTimeoutMS": 30000,
        "socketTimeoutMS": 30000,
    }

    if CA_FILE:
        conn_kwargs["tlsCAFile"] = CA_FILE
    else:
        conn_kwargs["tlsAllowInvalidCertificates"] = True

    _cached_client = pymongo.MongoClient(mongo_uri, **conn_kwargs)
    return _cached_client


def get_collection():
    """
    Open a MongoDB connection.
    Returns the 'events' collection object from 'hackathons_db'.
    """
    client = _get_client()
    return client["hackathons_db"]["events"]


# ---------------------------------------------------------------------------
# Save events with clean schema
# ---------------------------------------------------------------------------

def save_events(grouped: dict[str, list[dict]]) -> tuple[int, int]:
    """
    Persist curated events to the MongoDB database.

    Collection : hackathons_db.events
    Unique key : { link: registrationLink }  ← upsert on this

    Fields to store per document:
      title       : event title
      type        : Hackathon / Bootcamp / Workshop / Contest
      platform    : Devpost / Unstop / Devfolio / HackerEarth / etc.
      location    : Online / Virtual/Online / Kerala city name
      link        : registrationLink (unique)
      days_left   : integer
      ig          : assigned IG name (one of the 30)
      score       : internal score (stored but not shown)
      updated_at  : datetime.now(UTC)
      created_at  : set only on first insert ($setOnInsert)
    """
    collection = get_collection()
    operations = []

    for ig, ev_list in grouped.items():
        for e in ev_list:
            link = e.get("registrationLink", "")
            if not link:
                continue

            days = e.get("_days_remaining", 0)

            doc = {
                "title": e.get("eventName", "Unknown"),
                "type": e.get("_event_type", "Hackathon"),
                "platform": e.get("platform", "Unknown"),
                "location": e.get("location", "Unknown"),
                "link": link,
                "days_left": int(days) if days is not None else 0,
                "ig": ig,
                "score": e.get("_score", 0),
                "updated_at": datetime.now(timezone.utc),
            }

            operations.append(
                UpdateOne(
                    {"link": link},
                    {
                        "$set": doc,
                        "$setOnInsert": {
                            "created_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
            )

    if operations:
        result = collection.bulk_write(operations)
        return (result.upserted_count + result.modified_count, 0)

    return 0, 0
