"""Decision Log entity"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class DecisionLog:
    """
    Complete record of a single round decision
    
    Captures everything: event, villain take, headlines, player decision,
    outcome, and behavioral flags for transparency and coaching.
    """
    
    round_number: int
    ticker: str
    event: Dict[str, Any]
    villain_take: Dict[str, Any]
    headlines: List[Dict[str, Any]]
    consensus: str
    contradiction_score: float
    player_decision: str
    opened_data_tab: bool
    decision_time: float
    historical_case: Dict[str, Any]
    pl_dollars: float
    pl_percent: float
    timestamp: datetime = field(default_factory=datetime.now)
    behavior_flags: List[str] = field(default_factory=list)
    
    def flag_panic_sell(self, price_pattern: str):
        """Flag if player panic-sold after down days"""
        if self.player_decision == "SELL_ALL" and "3_down_closes" in price_pattern:
            self.behavior_flags.append("panic_sell")
    
    def flag_chased_spike(self, price_pattern: str):
        """Flag if player chased after up moves"""
        if self.player_decision == "BUY" and "3_up_closes" in price_pattern:
            self.behavior_flags.append("chased_spike")
    
    def flag_ignored_data(self):
        """Flag if player didn't check data"""
        if not self.opened_data_tab:
            self.behavior_flags.append("ignored_data")
    
    def flag_followed_villain_high_contradiction(self):
        """Flag if player followed Villain when headlines strongly disagreed"""
        if self.contradiction_score > 0.7:
            villain_stance = self.villain_take.get("stance", "")
            if (villain_stance == "Bullish" and self.player_decision == "BUY") or \
               (villain_stance == "Bearish" and self.player_decision in ["SELL_ALL", "SELL_HALF"]):
                self.behavior_flags.append("followed_villain_high_contradiction")
    
    def flag_resisted_villain(self):
        """Flag if player resisted Villain under high contradiction"""
        if self.contradiction_score > 0.7:
            villain_stance = self.villain_take.get("stance", "")
            if (villain_stance == "Bearish" and self.player_decision in ["HOLD", "BUY"]) or \
               (villain_stance == "Bullish" and self.player_decision in ["SELL_ALL", "SELL_HALF"]):
                self.behavior_flags.append("resisted_villain")
    
    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "ticker": self.ticker,
            "event": self.event,
            "villain_take": self.villain_take,
            "headlines": self.headlines,
            "consensus": self.consensus,
            "contradiction_score": self.contradiction_score,
            "player_decision": self.player_decision,
            "opened_data_tab": self.opened_data_tab,
            "decision_time": self.decision_time,
            "historical_case": self.historical_case,
            "pl_dollars": self.pl_dollars,
            "pl_percent": self.pl_percent,
            "timestamp": self.timestamp.isoformat(),
            "behavior_flags": self.behavior_flags
        }

