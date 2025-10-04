"""Behavioral Profile enumeration"""

from enum import Enum


class BehavioralProfile(str, Enum):
    """Player behavioral profile classification"""
    
    RATIONAL = "Rational"
    EMOTIONAL = "Emotional"
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def description(self) -> str:
        """Profile description"""
        return {
            "Rational": "Data-driven decision maker who resists emotional pressure",
            "Emotional": "Influenced by fear and FOMO, needs more data discipline",
            "Conservative": "Risk-averse with careful position management",
            "Balanced": "Balanced approach between emotion and analysis"
        }[self.value]
    
    @property
    def emoji(self) -> str:
        """Visual emoji"""
        return {
            "Rational": "🧠",
            "Emotional": "😰",
            "Conservative": "🛡️",
            "Balanced": "⚖️"
        }[self.value]

