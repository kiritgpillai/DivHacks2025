"""Generate Final Report Use Case Handler"""

from typing import Dict, List
from infrastructure.agents.tools.insight_tools import (
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
    
    def __init__(self, supabase_client=None):
        # In production, inject repository dependencies
        self.game_repo = None  # TODO: inject SupabaseGameRepository
        self.decision_tracker_repo = None  # TODO: inject SupabaseDecisionTrackerRepository
        self.supabase = supabase_client
    
    async def execute(self, game_id: str) -> Dict:
        """
        Generate final report for completed game.
        
        Args:
            game_id: Game session ID
            
        Returns:
            Dict with profile, coaching, and summary stats
        """
        # Fetch all decision logs for this game from database
        decision_logs = await self._fetch_decision_logs(game_id)
        
        if not decision_logs:
            # If no real data, return empty report
            return {
                "game_id": game_id,
                "profile": "No Data",
                "coaching": ["No decision data available for analysis"],
                "summary": {
                    "total_rounds": 0,
                    "final_portfolio_value": 0,
                    "total_pl": 0,
                    "total_return_pct": 0,
                    "data_tab_usage": 0,
                    "consensus_alignment": 0
                },
                "metrics": {}
            }
        
        # Aggregate behavior
        metrics_result = await aggregate_behavior.ainvoke({"decision_logs": json.dumps(decision_logs)})
        metrics = json.loads(metrics_result)
        
        # Classify profile
        profile_result = await classify_profile.ainvoke({"metrics": json.dumps(metrics)})
        profile_data = json.loads(profile_result)
        profile = profile_data["profile"]
        
        # Generate coaching
        coaching_result = await generate_coaching.ainvoke({
            "decision_logs": json.dumps(decision_logs),
            "profile": profile
        })
        coaching_data = json.loads(coaching_result)
        coaching_tips = coaching_data["coaching"]
        
        # Get the final portfolio value from the most recent portfolio update
        final_portfolio_value = await self._get_final_portfolio_value(game_id)
        
        # Get the actual initial portfolio value (not hardcoded)
        initial_portfolio_value = await self._get_initial_portfolio_value(game_id)
        
        # Calculate total P/L as the difference between final and initial values
        total_pl = final_portfolio_value - initial_portfolio_value
        
        # Calculate return percentage based on actual initial investment
        total_return = (total_pl / initial_portfolio_value) * 100 if initial_portfolio_value > 0 else 0
        
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
    
    async def _fetch_decision_logs(self, game_id: str) -> List[Dict]:
        """
        Fetch decision logs from game_rounds table for the given game.
        
        Args:
            game_id: Game session ID
            
        Returns:
            List of decision log dictionaries
        """
        if not self.supabase:
            print("Warning: Supabase client not configured, cannot fetch decision logs")
            return []
        
        try:
            # Fetch all rounds for this game session
            response = self.supabase.table("game_rounds").select("*").eq("session_id", game_id).order("round_number").execute()
            
            if not response.data:
                print(f"No decision logs found for game {game_id}")
                return []
            
            # Convert database records to decision log format expected by insight tools
            decision_logs = []
            for record in response.data:
                # Determine consensus from event data (simplified logic)
                consensus = "Neutral"
                if record.get("villain_stance") == "Bullish":
                    consensus = "Bullish" if record.get("contradiction_score", 0.5) < 0.7 else "Bearish"
                elif record.get("villain_stance") == "Bearish":
                    consensus = "Bearish" if record.get("contradiction_score", 0.5) < 0.7 else "Bullish"
                
                # Determine behavior flags based on decision patterns
                behavior_flags = []
                if record.get("player_decision") == "SELL_ALL" and record.get("opened_data_tab", False) == False:
                    behavior_flags.append("panic_sell")
                if not record.get("opened_data_tab", False):
                    behavior_flags.append("ignored_data")
                if record.get("contradiction_score", 0) > 0.7:
                    if record.get("villain_stance") == "Bullish" and record.get("player_decision") in ["HOLD", "BUY"]:
                        behavior_flags.append("followed_villain_high_contradiction")
                    elif record.get("villain_stance") == "Bearish" and record.get("player_decision") in ["SELL_ALL", "SELL_HALF"]:
                        behavior_flags.append("followed_villain_high_contradiction")
                    else:
                        behavior_flags.append("resisted_villain")
                
                decision_log = {
                    "round_number": record.get("round_number", 0),
                    "player_decision": record.get("player_decision", ""),
                    "opened_data_tab": record.get("opened_data_tab", False),
                    "pl_dollars": float(record.get("pl_dollars", 0)),
                    "consensus": consensus,
                    "contradiction_score": float(record.get("villain_contradiction_score", 0.5)),  # Use a field if it exists
                    "behavior_flags": behavior_flags
                }
                
                decision_logs.append(decision_log)
            
            print(f"Fetched {len(decision_logs)} decision logs for game {game_id}")
            return decision_logs
            
        except Exception as e:
            print(f"Error fetching decision logs for game {game_id}: {e}")
            return []
    
    async def _get_final_portfolio_value(self, game_id: str) -> float:
        """
        Get the final portfolio value for the game.
        
        Args:
            game_id: Game session ID
            
        Returns:
            Final portfolio value
        """
        if not self.supabase:
            return 1_000_000  # Default fallback
        
        try:
            # Get the portfolio_id from the game session
            session_response = self.supabase.table("game_sessions").select("portfolio_id").eq("id", game_id).execute()
            
            if not session_response.data:
                return 1_000_000  # Default fallback
            
            portfolio_id = session_response.data[0]["portfolio_id"]
            
            # Get the current portfolio value
            portfolio_response = self.supabase.table("portfolios").select("total_value").eq("id", portfolio_id).execute()
            
            if not portfolio_response.data:
                return 1_000_000  # Default fallback
            
            return float(portfolio_response.data[0]["total_value"])
            
        except Exception as e:
            print(f"Error fetching final portfolio value for game {game_id}: {e}")
            return 1_000_000  # Default fallback
    
    async def _get_initial_portfolio_value(self, game_id: str) -> float:
        """
        Get the initial portfolio value for the game.
        
        Args:
            game_id: Game session ID
            
        Returns:
            Initial portfolio value
        """
        if not self.supabase:
            return 1_000_000  # Default fallback
        
        try:
            # Get the portfolio_id from the game session
            session_response = self.supabase.table("game_sessions").select("portfolio_id").eq("id", game_id).execute()
            
            if not session_response.data:
                return 1_000_000  # Default fallback
            
            portfolio_id = session_response.data[0]["portfolio_id"]
            
            # Calculate initial value as cash + sum of initial allocations (no initial_cash column in schema)
            portfolio_response = self.supabase.table("portfolios").select("cash").eq("id", portfolio_id).execute()
            positions_response = self.supabase.table("positions").select("allocation").eq("portfolio_id", portfolio_id).execute()
            
            if not portfolio_response.data:
                return 1_000_000  # Default fallback
            
            current_cash = float(portfolio_response.data[0].get("cash", 0) or 0)
            total_allocations = sum(float(pos["allocation"]) for pos in (positions_response.data or []))
            
            # If both are zero (unlikely), fall back to 1,000,000
            initial_value = current_cash + total_allocations
            return initial_value if initial_value > 0 else 1_000_000
            
        except Exception as e:
            print(f"Error fetching initial portfolio value for game {game_id}: {e}")
            return 1_000_000  # Default fallback

