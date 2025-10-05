"""Submit Decision Use Case Handler"""

from typing import Dict
from backend.application.portfolio.update_portfolio_handler import UpdatePortfolioHandler
from backend.infrastructure.observability.opik_tracer import log_game_event


class SubmitDecisionHandler:
    """
    Handler for submitting player decision.
    
    Process:
    1. Update portfolio in Supabase (UpdatePortfolioHandler)
    2. Calculate P/L based on actual price changes
    3. Store round outcome to Supabase (game_rounds table)
    4. Log to Opik for observability
    
    Note: No longer uses agent graph for decision processing.
    Portfolio updates are handled directly via Supabase.
    """
    
    def __init__(self, supabase_client=None):
        # Supabase client for database operations
        self.supabase = supabase_client
        self.update_portfolio_handler = UpdatePortfolioHandler(supabase_client)
        self.game_repo = None  # TODO: remove after full Supabase migration
        self.decision_tracker_repo = None  # TODO: remove after full Supabase migration
    
    async def execute(
        self,
        game_id: str,
        round_number: int,
        player_decision: str,
        decision_time: float,
        opened_data_tab: bool,
        portfolio_id: str = None,
        ticker: str = None,
        new_price: float = None,
        event_data: Dict = None,
        historical_case: Dict = None,
        historical_outcomes: Dict = None
    ) -> Dict:
        """
        Process player decision and calculate outcome.
        
        Args:
            game_id: Game session ID
            round_number: Current round number
            player_decision: SELL_HALF, HOLD, or BUY
            decision_time: Time taken to decide (seconds)
            opened_data_tab: Whether player opened data tab
            portfolio_id: Portfolio ID (required for portfolio updates)
            ticker: Stock ticker for the decision (required)
            new_price: Current price for the ticker (required)
            event_data: Event data from round start (for storing in game_rounds)
            
        Returns:
            Dict with outcome, P/L, updated portfolio, and behavior tracking
        """
        # Validate required parameters
        if not ticker or new_price is None:
            raise ValueError("ticker and new_price are required for portfolio updates")
        
        # Step 1: Update portfolio if portfolio_id provided
        portfolio_update = None
        if portfolio_id:
            try:
                portfolio_update = await self.update_portfolio_handler.execute(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    decision=player_decision,
                    new_price=new_price,
                    game_id=game_id,
                    round_number=round_number,
                    historical_case=historical_case
                )
            except Exception as e:
                print(f"Warning: Portfolio update failed: {e}")
                # Continue with mock P/L calculation
        
        # Step 2: Get P/L from portfolio update
        # We no longer need to invoke the agent graph for decision processing
        # Portfolio update handler already calculated P/L based on actual price changes
        if portfolio_update:
            pl_dollars = portfolio_update["pl_dollars"]
            pl_percent = portfolio_update["pl_percent"]
        else:
            # Fallback: If portfolio update failed, use mock calculation
            # This should rarely happen in production
            print("Warning: Using mock P/L calculation (portfolio update unavailable)")
            pl_dollars = 0.0
            pl_percent = 0.0
        
        # Step 3: Store round outcome to Supabase
        if self.supabase and event_data:
            try:
                await self._save_round_outcome(
                    game_id=game_id,
                    round_number=round_number,
                    ticker=ticker,
                    event_data=event_data,
                    player_decision=player_decision,
                    decision_time=decision_time,
                    opened_data_tab=opened_data_tab,
                    pl_dollars=pl_dollars,
                    pl_percent=pl_percent
                )
            except Exception as e:
                print(f"Warning: Failed to save round outcome: {e}")
        
        # Step 4: Log to Opik
        try:
            log_game_event("decision_submitted", {
                "game_id": game_id,
                "round_number": round_number,
                "portfolio_id": portfolio_id,
                "ticker": ticker,
                "decision": player_decision,
                "decision_time": decision_time,
                "opened_data_tab": opened_data_tab,
                "pl_dollars": pl_dollars,
                "pl_percent": pl_percent,
                "new_total_value": portfolio_update["new_total_value"] if portfolio_update else None
            })
        except Exception as e:
            print(f"Warning: Failed to log to Opik: {e}")
        
        # Generate outcome explanation based on decision and P/L
        explanation = self._generate_outcome_explanation(
            player_decision, pl_dollars, pl_percent, ticker, event_data
        )
        
        # Get historical case data if available
        historical_case_used = None
        if historical_case:
            historical_case_used = {
                "ticker": historical_case.get("ticker", ticker),
                "date": historical_case.get("date", "2023-01-01"),
                "day0_price": historical_case.get("day0_price", 100.0),
                "day_h_price": historical_case.get("day_h_price", 105.0)
            }
        
        return {
            "game_id": game_id,
            "round_number": round_number,
            "pl_dollars": pl_dollars,
            "pl_percent": pl_percent,
            "outcome": {
                "explanation": explanation,
                "historical_case_used": historical_case_used
            },
            "portfolio": portfolio_update,
            "behavior_flags": []  # TODO: Add behavioral analysis if needed
        }
    
    async def _save_round_outcome(
        self,
        game_id: str,
        round_number: int,
        ticker: str,
        event_data: Dict,
        player_decision: str,
        decision_time: float,
        opened_data_tab: bool,
        pl_dollars: float,
        pl_percent: float
    ) -> None:
        """
        Save round outcome to game_rounds table.
        
        Args:
            game_id: Game session ID
            round_number: Round number
            ticker: Stock ticker
            event_data: Event data from round start
            player_decision: Player's decision
            decision_time: Time taken to decide
            opened_data_tab: Whether player opened data tab
            pl_dollars: Profit/loss in dollars
            pl_percent: Profit/loss percentage
        """
        # Fetch session_id from game_sessions
        session_response = self.supabase.table("game_sessions").select("id").eq("id", game_id).execute()
        
        if not session_response.data or len(session_response.data) == 0:
            print(f"Warning: Game session {game_id} not found, skipping round outcome save")
            return
        
        # Insert round outcome
        self.supabase.table("game_rounds").insert({
            "session_id": game_id,
            "round_number": round_number,
            "ticker": ticker,
            "event_type": event_data.get("type", "UNKNOWN"),
            "event_description": event_data.get("description", ""),
            "event_horizon": event_data.get("horizon", 3),
            "villain_stance": event_data.get("villain_stance", "Bullish"),
            "villain_bias": event_data.get("villain_bias", "Unknown"),
            "villain_hot_take": event_data.get("villain_hot_take", ""),
            "player_decision": player_decision,
            "decision_time": decision_time,
            "opened_data_tab": opened_data_tab,
            "pl_dollars": pl_dollars,
            "pl_percent": pl_percent
        }).execute()
    
    def _generate_outcome_explanation(
        self,
        player_decision: str,
        pl_dollars: float,
        pl_percent: float,
        ticker: str,
        event_data: dict
    ) -> str:
        """
        Generate outcome explanation based on decision and P/L.
        
        Args:
            player_decision: Player's decision (BUY, HOLD, SELL_HALF)
            pl_dollars: Profit/loss in dollars
            pl_percent: Profit/loss percentage
            ticker: Stock ticker
            event_data: Event data from round start
            
        Returns:
            Explanation string for the outcome
        """
        is_profit = pl_dollars > 0
        event_type = event_data.get("type", "UNKNOWN").replace("_", " ").title()
        
        if is_profit:
            explanation = f"Great decision! Your {player_decision} decision on {ticker} during the {event_type} event resulted in a profit of ${pl_dollars:.2f} ({pl_percent:.1%}). "
        else:
            explanation = f"Your {player_decision} decision on {ticker} during the {event_type} event resulted in a loss of ${abs(pl_dollars):.2f} ({abs(pl_percent):.1%}). "
        
        # Add context based on decision type
        if player_decision == "BUY":
            explanation += f"You increased your position in {ticker} and captured the price movement."
        elif player_decision == "HOLD":
            explanation += f"You maintained your position in {ticker} and experienced the full price movement."
        elif player_decision == "SELL_HALF":
            explanation += f"You reduced your position in {ticker} by half, capturing partial gains while maintaining some exposure."
        
        return explanation

    