# zulip_writer.py
import zulip
from dataclasses import dataclass
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class CleanItem:
    title: str
    url: str
    score: float
    category: str
    deadline: str

class ZulipWriter:
    def __init__(self, zuliprc_path: str, stream: str):
        self.client = zulip.Client(config_file=zuliprc_path)
        self.stream = stream

    def send_item(self, item: CleanItem, topic: str) -> dict:
        content = f"**{item.title}**\n\n**URL:** [{item.url}]({item.url})\n**Category:** {item.category}"
        
        # Only add deadline if it's not TBA
        if item.deadline and item.deadline.lower() != "tba":
            content += f"\n**Deadline:** {item.deadline}"
            
        request = {
            "type": "stream",
            "to": self.stream,
            "topic": topic,
            "content": content
        }
        return self.client.send_message(request)

    def send_grouped(self, grouped: Dict[str, List[CleanItem]]) -> None:
        """Send top 3 items per IG to IG-specific topics."""
        for ig, items in grouped.items():
            if items:
                topic = f"{ig} Opportunities"
                for item in items[:3]:
                    result = self.send_item(item, topic)
                    logger.info(f"✅ Sent {item.title[:50]}... to {self.stream}/{topic}")
