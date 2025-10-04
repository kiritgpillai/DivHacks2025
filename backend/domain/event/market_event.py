"""Market Event entity"""

from dataclasses import dataclass
from .event_type import EventType


@dataclass
class MarketEvent:
    """A market event scenario tied to a specific ticker"""
    
    ticker: str
    event_type: EventType
    description: str
    horizon: int  # Time window for outcome (trading days)
    
    def __post_init__(self):
        if not self.description or len(self.description) < 20:
            raise ValueError("Event description must be at least 20 characters")
        
        if self.horizon < 1 or self.horizon > 10:
            raise ValueError("Horizon must be between 1 and 10 trading days")
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "event_type": str(self.event_type),
            "description": self.description,
            "horizon": self.horizon
        }

