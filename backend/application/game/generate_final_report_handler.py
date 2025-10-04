"""Generate Final Report Use Case Handler"""

from typing import Dict, List
from backend.infrastructure.agents.tools.insight_tools import (
    aggregate_behavior,
    classify_profile,
    generate_coaching
)
import json


class GenerateFinalReportHandler:
    """
    Handler for generating final game report with behavioral profile.
    
    Uses Insight Agent tools to:
    1. Aggregate behavior metrics
    2. Classify behavioral profile
    3. Generate personalized coaching
    """
    
    def __init__(self):
        # In production, inject repository dependencies
        self.game_repo = None  # TODO: inject SupabaseGameRepository
        self.decision_tracker_repo = None  # TODO: inject SupabaseDecisionTrackerRepository
    
    async def execute(self, game_id: str) -> Dict:
        """
        Generate final report for completed game.
        
        Args:
            game_id: Game session ID
            
        Returns:
            Dict with profile, coaching, and summary stats
        """
        # Fetch all decision logs for this game
        # decision_logs = await self.decision_tracker_repo.get_by_game(game_id)
        
        # For MVP, use mock data
        decision_logs = [
            {
                "round_number": 1,
                "player_decision": "HOLD",
                "opened_data_tab": True,
                "pl_dollars": 12840,
                "consensus": "Bullish",
                "contradiction_score": 0.75,
                "behavior_flags": ["resisted_villain"]
            },
            {
                "round_number": 2,
                "player_decision": "SELL_ALL",
                "opened_data_tab": False,
                "pl_dollars": 0,
                "consensus": "Neutral",
                "contradiction_score": 0.5,
                "behavior_flags": ["panic_sell", "ignored_data"]
            },
            {
                "round_number": 3,
                "player_decision": "SELL_HALF",
                "opened_data_tab": True,
                "pl_dollars": 8500,
                "consensus": "Bearish",
                "contradiction_score": 0.2,
                "behavior_flags": []
            }
        ]
        
        # Aggregate behavior
        metrics_result = await aggregate_behavior(json.dumps(decision_logs))
        metrics = json.loads(metrics_result)
        
        # Classify profile
        profile_result = await classify_profile(json.dumps(metrics))
        profile_data = json.loads(profile_result)
        profile = profile_data["profile"]
        
        # Generate coaching
        coaching_result = await generate_coaching(
            json.dumps(decision_logs),
            profile
        )
        coaching_data = json.loads(coaching_result)
        coaching_tips = coaching_data["coaching"]
        
        # Calculate summary stats
        total_pl = sum(log["pl_dollars"] for log in decision_logs)
        final_portfolio_value = 1_000_000 + total_pl
        total_return = (total_pl / 1_000_000) * 100
        
        return {
            "game_id": game_id,
            "profile": profile,
            "coaching": coaching_tips,
            "summary": {
                "total_rounds": len(decision_logs),
                "final_portfolio_value": final_portfolio_value,
                "total_pl": total_pl,
                "total_return_pct": round(total_return, 2),
                "data_tab_usage": metrics.get("data_tab_usage", 0),
                "consensus_alignment": metrics.get("consensus_alignment", 0)
            },
            "metrics": metrics
        }

