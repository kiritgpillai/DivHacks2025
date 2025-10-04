"""Event Type enumeration"""

from enum import Enum


class EventType(str, Enum):
    """Types of market events that can occur"""
    
    EARNINGS_SURPRISE = "EARNINGS_SURPRISE"
    REGULATORY_NEWS = "REGULATORY_NEWS"
    ANALYST_ACTION = "ANALYST_ACTION"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"
    PRODUCT_NEWS = "PRODUCT_NEWS"
    MACRO_EVENT = "MACRO_EVENT"
    
    @property
    def default_horizon(self) -> int:
        """Default time horizon for this event type (trading days)"""
        return {
            "EARNINGS_SURPRISE": 3,
            "REGULATORY_NEWS": 5,
            "ANALYST_ACTION": 3,
            "VOLATILITY_SPIKE": 2,
            "PRODUCT_NEWS": 4,
            "MACRO_EVENT": 5
        }[self.value]
    
    def __str__(self) -> str:
        return self.value

