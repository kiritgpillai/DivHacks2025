"""Risk Profile value object"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RiskProfile:
    """Risk profile determines maximum position size limits"""
    
    value: Literal["Risk-On", "Balanced", "Risk-Off"]
    
    @property
    def max_position_size_pct(self) -> float:
        """Maximum percentage of portfolio per position"""
        return {
            "Risk-On": 0.50,      # 50% max
            "Balanced": 0.33,     # 33% max
            "Risk-Off": 0.25      # 25% max
        }[self.value]
    
    @property
    def display_name(self) -> str:
        """Human-readable name"""
        return self.value
    
    def __str__(self) -> str:
        return self.value

