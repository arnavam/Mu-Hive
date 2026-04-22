from pydantic import BaseModel
from typing import Optional

class Event(BaseModel):
    eventName: str
    registrationLink: str
    startDate: str
    location: Optional[str] = None
    platform: Optional[str] = None
    days_remaining: Optional[int] = None
