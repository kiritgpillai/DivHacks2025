"""Submit Decision Use Case Handler"""

from typing import Dict
from backend.infrastructure.agents.game_graph import process_decision


class SubmitDecisionHandler:
    """
    Handler for submitting player decision.
    
    Invokes multi-agent graph to:
    1. Calculate outcome using historical replay (Price Agent)
    2. Track behavioral patterns (Insight Agent)
    """
    
    def __init__(self):
        # In production, inject repository dependencies
        self.game_repo = None  # TODO: inject SupabaseGameRepository
        self.decision_tracker_repo = None  # TODO: inject SupabaseDecisionTrackerRepository
    
    async def execute(
        self,
        game_id: str,
        round_number: int,
        player_decision: str,
        decision_time: float,
        opened_data_tab: bool
    ) -> Dict:
        """
        Process player decision and calculate outcome.
        
        Args:
            game_id: Game session ID
            round_number: Current round number
            player_decision: SELL_ALL, SELL_HALF, HOLD, or BUY
            decision_time: Time taken to decide (seconds)
            opened_data_tab: Whether player opened data tab
            
        Returns:
            Dict with outcome, P/L, and behavior tracking
        """
        # Fetch round data (historical case, position size, etc.)
        # round_data = await self.game_repo.get_round(game_id, round_number)
        
        # For MVP, use mock data
        historical_case = {
            "ticker": "AAPL",
            "event_type": "EARNINGS_BEAT",
            "date": "2023-05-15",
            "horizon": 3,
            "day0_price": 175.0,
            "day_h_price": 182.5,
            "price_path": [175.0, 178.2, 180.1, 182.5],
            "return_pct": 0.0428
        }
        position_size = 300000
        
        # Invoke multi-agent graph
        result = await process_decision(
            game_id=game_id,
            round_number=round_number,
            player_decision=player_decision,
            decision_time=decision_time,
            opened_data_tab=opened_data_tab,
            historical_case=historical_case,
            position_size=position_size
        )
        
        # Update game session portfolio value (TODO: implement)
        # new_portfolio_value = old_value + result['pl_dollars']
        # await self.game_repo.update_portfolio_value(game_id, new_portfolio_value)
        
        # Save decision log (TODO: implement persistence)
        decision_log = {
            "game_id": game_id,
            "round_number": round_number,
            "player_decision": player_decision,
            "decision_time": decision_time,
            "opened_data_tab": opened_data_tab,
            "pl_dollars": result["pl_dollars"],
            "pl_percent": result["pl_percent"],
            "behavior_flags": result.get("behavior_flags", [])
        }
        # await self.decision_tracker_repo.save(decision_log)
        
        return {
            "game_id": game_id,
            "round_number": round_number,
            "outcome": result["outcome"],
            "pl_dollars": result["pl_dollars"],
            "pl_percent": result["pl_percent"],
            "behavior_flags": result.get("behavior_flags", [])
        }

