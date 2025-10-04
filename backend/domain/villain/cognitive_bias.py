"""Cognitive Bias enumeration"""

from enum import Enum


class CognitiveBias(str, Enum):
    """Types of cognitive biases the Villain exploits"""
    
    FEAR_APPEAL = "Fear Appeal"
    OVERCONFIDENCE = "Overconfidence"
    AUTHORITY_LURE = "Authority Lure"
    RECENCY_BIAS = "Recency Bias"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def description(self) -> str:
        """Description of the bias"""
        return {
            "Fear Appeal": "Creating panic and urgency to sell",
            "Overconfidence": "Promoting guaranteed gains and FOMO",
            "Authority Lure": "Appealing to expert opinion",
            "Recency Bias": "Overweighting recent price action"
        }[self.value]
    
    @property
    def emoji(self) -> str:
        """Visual emoji"""
        return {
            "Fear Appeal": "😱",
            "Overconfidence": "🚀",
            "Authority Lure": "🎓",
            "Recency Bias": "📈"
        }[self.value]

