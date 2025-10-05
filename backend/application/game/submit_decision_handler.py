"""Submit Decision Use Case Handler"""

from typing import Dict
from decimal import Decimal
from backend.infrastructure.yfinance_adapter.historical_sampler import sample_historical_window
from application.portfolio.update_portfolio_handler import UpdatePortfolioHandler
from infrastructure.observability.opik_tracer import log_game_event


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
        event_data: Dict = None
    ) -> Dict:
        """
        Process player decision and calculate outcome.
        
        Args:
            game_id: Game session ID
            round_number: Current round number
            player_decision: SELL_ALL, SELL_HALF, HOLD, or BUY
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
        
        # Step 1: Sample historical window for this round to drive per-asset movement
        round_horizon = (event_data or {}).get("horizon", 3)
        event_type = (event_data or {}).get("type", "UNKNOWN")
        try:
            hist_case = await sample_historical_window(ticker=ticker, event_type=event_type, horizon=round_horizon)
            day0_price = Decimal(str(hist_case["day0_price"]))
            day_h_price = Decimal(str(hist_case["day_h_price"]))
        except Exception as e:
            print(f"Warning: Failed to sample historical window: {e}")
            # Fall back to provided new_price for a minimal flow
            day0_price = Decimal(str(new_price))
            day_h_price = Decimal(str(new_price))

        # Decide which price to use to update state (end-of-round settlement)
        # - SELL_ALL settles at day0 (exit now)
        # - Others settle at day H (end of round)
        state_settle_price = float(day0_price if player_decision == "SELL_ALL" else day_h_price)

        # Step 2: Update portfolio state at the appropriate settlement price
        portfolio_update = None
        if portfolio_id:
            try:
                portfolio_update = await self.update_portfolio_handler.execute(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    decision=player_decision,
                    new_price=state_settle_price,
                    game_id=game_id,
                    round_number=round_number
                )
            except Exception as e:
                print(f"Warning: Portfolio update failed: {e}")

        # Step 3: Compute per-asset P/L for this round using historical prices
        # Use pre-update details to derive entry price
        if portfolio_update:
            allocation_before = Decimal(str(portfolio_update.get("allocation_before", 0)))
            shares_before = Decimal(str(portfolio_update.get("shares_before", 0)))
        else:
            allocation_before = Decimal("0")
            shares_before = Decimal("0")

        entry_price = (allocation_before / shares_before) if shares_before > 0 else Decimal("0")
        round_pl_dollars = Decimal("0")
        round_pl_percent = Decimal("0")

        try:
            if player_decision == "HOLD":
                asset_return = (day_h_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")
                round_pl_dollars = allocation_before * asset_return
                round_pl_percent = asset_return
            elif player_decision == "SELL_ALL":
                asset_return = (day0_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")
                round_pl_dollars = allocation_before * asset_return
                round_pl_percent = asset_return
            elif player_decision == "SELL_HALF":
                half_alloc = allocation_before / Decimal("2")
                ret_day0 = (day0_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")
                ret_dayh = (day_h_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")
                realized = half_alloc * ret_day0
                unrealized = half_alloc * ret_dayh
                round_pl_dollars = realized + unrealized
                round_pl_percent = (round_pl_dollars / allocation_before) if allocation_before > 0 else Decimal("0")
            elif player_decision == "BUY":
                buy_size = allocation_before * Decimal("0.1")
                buy_return = (day_h_price - day0_price) / day0_price if day0_price > 0 else Decimal("0")
                round_pl_dollars = buy_size * buy_return
                round_pl_percent = buy_return * Decimal("0.1")
            else:
                round_pl_dollars = Decimal("0")
                round_pl_percent = Decimal("0")
        except Exception as e:
            print(f"Warning: Failed P/L computation: {e}")

        # Prefer our per-asset P/L; store percent as percentage units (e.g., 5.25 for 5.25%)
        pl_dollars = float(round_pl_dollars)
        pl_percent = float(round(round_pl_percent * Decimal("100"), 4))
        # Clean near-zero noise
        if abs(pl_dollars) < 1e-9:
            pl_dollars = 0.0
        if abs(pl_percent) < 1e-9:
            pl_percent = 0.0
        
        # Step 4: Store round outcome to Supabase
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
        
        # Step 5: Log to Opik
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
        
        return {
            "game_id": game_id,
            "round_number": round_number,
            "outcome": "success",  # Simple outcome status
            "pl_dollars": pl_dollars,
            "pl_percent": pl_percent,
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

