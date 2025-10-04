"""Headline entity"""

from dataclasses import dataclass
from .news_stance import NewsStance


@dataclass
class Headline:
    """Single news headline with stance classification"""
    
    title: str
    source: str
    stance: NewsStance
    url: str = ""
    snippet: str = ""
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "stance": str(self.stance),
            "stance_emoji": self.stance.emoji,
            "url": self.url,
            "snippet": self.snippet
        }

