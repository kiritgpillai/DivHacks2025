"""Villain Take entity"""

from dataclasses import dataclass
from .cognitive_bias import CognitiveBias


@dataclass
class VillainTake:
    """Villain's biased hot take on an event"""
    
    text: str
    stance: str  # "Bullish" or "Bearish"
    bias: CognitiveBias
    
    def __post_init__(self):
        if len(self.text) < 20:
            raise ValueError("Villain take must be at least 20 characters")
        
        if self.stance not in ["Bullish", "Bearish"]:
            raise ValueError("Stance must be 'Bullish' or 'Bearish'")
    
    def is_contrarian_to_consensus(self, consensus_value: str) -> bool:
        """Check if Villain contradicts news consensus"""
        if "Bull" in consensus_value and self.stance == "Bearish":
            return True
        if "Bear" in consensus_value and self.stance == "Bullish":
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "stance": self.stance,
            "bias": str(self.bias),
            "bias_emoji": self.bias.emoji,
            "bias_description": self.bias.description
        }

