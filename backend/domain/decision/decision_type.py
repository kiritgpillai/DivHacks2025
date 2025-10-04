"""Decision Type enumeration"""

from enum import Enum


class DecisionType(str, Enum):
    """Player decision actions"""
    
    SELL_ALL = "SELL_ALL"
    SELL_HALF = "SELL_HALF"
    HOLD = "HOLD"
    BUY = "BUY"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Human-readable name"""
        return {
            "SELL_ALL": "Sell All",
            "SELL_HALF": "Sell Half",
            "HOLD": "Hold",
            "BUY": "Buy"
        }[self.value]

