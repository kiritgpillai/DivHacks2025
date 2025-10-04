"""News Stance enumeration"""

from enum import Enum


class NewsStance(str, Enum):
    """Stance classification for news headlines"""
    
    BULL = "Bull"
    BEAR = "Bear"
    NEUTRAL = "Neutral"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def emoji(self) -> str:
        """Visual emoji for UI"""
        return {
            "Bull": "🟢",
            "Bear": "🔴",
            "Neutral": "⚪"
        }[self.value]

