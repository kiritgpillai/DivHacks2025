"""Consensus value object"""

from dataclasses import dataclass
from typing import List
from .headline import Headline
from .news_stance import NewsStance


@dataclass(frozen=True)
class Consensus:
    """Aggregated stance across multiple headlines"""
    
    value: str  # "Two-thirds Bull", "Majority Bear", "Mixed", etc.
    
    @staticmethod
    def calculate(headlines: List[Headline]) -> "Consensus":
        """Calculate consensus from headlines"""
        if not headlines:
            return Consensus("No Data")
        
        bull_count = sum(1 for h in headlines if h.stance == NewsStance.BULL)
        bear_count = sum(1 for h in headlines if h.stance == NewsStance.BEAR)
        total = len(headlines)
        
        bull_pct = bull_count / total
        bear_pct = bear_count / total
        
        if bull_pct >= 0.67:
            return Consensus("Two-thirds Bull")
        elif bear_pct >= 0.67:
            return Consensus("Two-thirds Bear")
        elif bull_pct > 0.5:
            return Consensus("Majority Bull")
        elif bear_pct > 0.5:
            return Consensus("Majority Bear")
        else:
            return Consensus("Mixed")
    
    def __str__(self) -> str:
        return self.value

