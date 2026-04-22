from pydantic import BaseModel, Field
from typing import Optional

class RawItem(BaseModel):
    """What the scraper gives us — unverified, unstructured."""
    title: str
    url: str
    text: str
    ig: str              # which Interest Group this came from
    source: str          # "rss", "search", or "site"
    status: Optional[str] = None

class CleanItem(BaseModel):
    """What we output — verified, structured, ready to deliver."""
    hash: str
    title: str
    url: str
    summary: str
    ig: str
    source: str          # "rss", "search", or "site"
    category: str
    deadline: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)
    status: str          # "ready" or "flagged"
    created_at: str      # ISO timestamp
