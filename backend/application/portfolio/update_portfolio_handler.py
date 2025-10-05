"""Update Portfolio Use Case Handler"""

from typing import Dict, Optional
from decimal import Decimal
from domain.portfolio.portfolio import Portfolio
from domain.portfolio.position import Position
from domain.portfolio.risk_profile import RiskProfile
from infrastructure.observability.opik_tracer import log_game_event


class UpdatePortfolioHandler:
    """
    Handler for updating portfolio based on player decisions.
    
    Applies BUY, SELL_ALL, SELL_HALF, or HOLD decisions to portfolio
    and persists changes to Supabase.
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize handler with Supabase client.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
    
    async def execute(
        self,
        portfolio_id: str,
        ticker: str,
        decision: str,
        new_price: float,
        game_id: str = None,
        round_number: int = None
    ) -> Dict:
        """
        Update portfolio based on player decision.
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker
            decision: SELL_ALL, SELL_HALF, HOLD, or BUY
            new_price: Current/new price for the ticker
            game_id: Game session ID (for logging)
            round_number: Round number (for logging)
            
        Returns:
            Dict with updated portfolio state and P/L
        """
        # Step 1: Fetch portfolio from Supabase
        portfolio = await self._fetch_portfolio(portfolio_id)
        
        # Step 2: Get position before update
        position_before = portfolio.get_position(ticker)
        if not position_before:
            raise ValueError(f"Position not found for ticker: {ticker}")
        
        value_before = position_before.calculate_value()
        shares_before = position_before.shares
        allocation_before = position_before.allocation
        
        # Step 3: Apply decision to portfolio and calculate P/L correctly
        pl_dollars = Decimal(0)
        pl_percent = Decimal(0)
        shares_after = Decimal(0)
        allocation_after = Decimal(0)
        
        if decision == "SELL_ALL":
            # SELL_ALL: Exit at current price, no P/L (exit before any price movement)
            # Ensure we settle at the provided new_price for realized value
            position_now = portfolio.get_position(ticker)
            if position_now:
                position_now.update_price(new_price)
            portfolio.apply_sell_all(ticker)
            pl_dollars = Decimal(0)
            pl_percent = Decimal(0)
            shares_after = Decimal(0)
            allocation_after = Decimal(0)
            
        elif decision == "SELL_HALF":
            # SELL_HALF: Realize half at current price, remaining half rides price change
            portfolio.apply_sell_half(ticker)
            position_after = portfolio.get_position(ticker)
            if position_after:
                # Ensure remaining half reflects the latest market price
                position_after.update_price(new_price)
                shares_after = position_after.shares
                allocation_after = position_after.allocation
                # P/L is the gain/loss on the remaining half that rides the price change
                # Since we just sold half at current price, P/L is 0 on the sold half
                # The remaining half will have P/L based on price change from entry
                pl_dollars = position_after.calculate_value() - position_after.allocation
                pl_percent = pl_dollars / position_after.allocation if position_after.allocation > 0 else Decimal(0)
            
        elif decision == "HOLD":
            # HOLD: Full position rides price change from entry to current price
            portfolio.apply_hold(ticker, new_price)
            position_after = portfolio.get_position(ticker)
            shares_after = position_after.shares
            allocation_after = position_after.allocation
            # P/L is the gain/loss from entry price to current price
            pl_dollars = position_after.calculate_value() - position_after.allocation
            pl_percent = pl_dollars / position_after.allocation if position_after.allocation > 0 else Decimal(0)
            
        elif decision == "BUY":
            # BUY: Add 10% to position, calculate P/L on the additional 10%
            amount_spent = portfolio.apply_buy(ticker, new_price)
            position_after = portfolio.get_position(ticker)
            shares_after = position_after.shares
            allocation_after = position_after.allocation
            
            # P/L is the gain/loss on the additional 10% purchased
            # Since we just bought at current price, P/L is 0 (no gain/loss yet)
            # The actual P/L will be realized when the price changes in future rounds
            pl_dollars = Decimal(0)
            pl_percent = Decimal(0)
            
        else:
            raise ValueError(f"Invalid decision: {decision}")
        
        # Step 4: Calculate new portfolio value
        new_total_value = portfolio.calculate_total_value()
        
        # Step 5: Persist to Supabase
        await self._save_portfolio(portfolio)
        
        # Step 6: Log to Opik
        try:
            log_game_event("portfolio_updated", {
                "game_id": game_id,
                "round_number": round_number,
                "portfolio_id": portfolio_id,
                "ticker": ticker,
                "decision": decision,
                "shares_before": float(shares_before),
                "shares_after": float(shares_after),
                "allocation_before": float(allocation_before),
                "allocation_after": float(allocation_after),
                "pl_dollars": float(pl_dollars),
                "new_total_value": float(new_total_value),
                "new_price": new_price,
                "cash": float(portfolio.cash)
            })
        except Exception as e:
            print(f"Warning: Failed to log to Opik: {e}")
        
        # Step 7: Return result
        # Normalize tiny negative zeros for cleaner UI
        def _clean_number(value: Decimal | float) -> float:
            v = float(value)
            if abs(v) < 1e-9:
                return 0.0
            return v

        result = {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "decision": decision,
            "pl_dollars": _clean_number(pl_dollars),
            "pl_percent": _clean_number(pl_percent),
            "shares_before": float(shares_before),
            "shares_after": float(shares_after),
            "allocation_before": float(allocation_before),
            "allocation_after": float(allocation_after),
            "new_total_value": _clean_number(new_total_value),
            "cash": float(portfolio.cash),
            "positions": [
                {
                    "ticker": p.ticker,
                    "shares": float(p.shares),
                    "current_price": float(p.current_price),
                    "allocation": float(p.allocation),
                    "value": float(p.calculate_value())
                }
                for p in portfolio.positions
            ]
        }

        # Also return a minimal mirror for in-memory cache updates
        result["portfolio_min"] = {
            "portfolio_value": result["new_total_value"],
            "allocations": {pos["ticker"]: pos["allocation"] for pos in result["positions"]}
        }

        return result
    
    async def _fetch_portfolio(self, portfolio_id: str) -> Portfolio:
        """
        Fetch portfolio from Supabase.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio aggregate
        """
        if not self.supabase:
            raise ValueError("Supabase client not configured")
        
        # Fetch portfolio record
        portfolio_response = self.supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise ValueError(f"Portfolio not found: {portfolio_id}")
        
        portfolio_data = portfolio_response.data[0]
        
        # Fetch positions
        positions_response = self.supabase.table("positions").select("*").eq("portfolio_id", portfolio_id).execute()
        
        # Reconstruct Portfolio aggregate
        # Get actual initial cash from portfolio data or calculate from positions
        initial_cash = portfolio_data.get("initial_cash", 1_000_000)
        if not initial_cash or initial_cash <= 0:
            # Calculate initial cash from current positions + cash
            total_allocations = sum(float(pos["allocation"]) for pos in positions_response.data) if positions_response.data else 0
            current_cash = float(portfolio_data.get("cash", 0))
            initial_cash = total_allocations + current_cash
        
        portfolio = Portfolio(
            id=portfolio_data["id"],
            player_id=portfolio_data["player_id"],
            risk_profile=RiskProfile(portfolio_data["risk_profile"]),
            initial_cash=float(initial_cash)
        )
        
        # Reconstruct positions
        for pos_data in positions_response.data:
            position = Position(
                ticker=pos_data["ticker"],
                allocation=float(pos_data["allocation"]),
                entry_price=float(pos_data["entry_price"])
            )
            position.shares = Decimal(str(pos_data["shares"]))
            position.current_price = Decimal(str(pos_data["current_price"]))
            portfolio._positions.append(position)
        
        # Set cash
        portfolio._cash = Decimal(str(portfolio_data["cash"]))
        
        return portfolio
    
    async def _save_portfolio(self, portfolio: Portfolio) -> None:
        """
        Save portfolio to Supabase.
        
        Args:
            portfolio: Portfolio aggregate to save
        """
        if not self.supabase:
            raise ValueError("Supabase client not configured")
        
        # Update portfolio record
        self.supabase.table("portfolios").update({
            "cash": float(portfolio.cash),
            "total_value": float(portfolio.calculate_total_value())
        }).eq("id", portfolio.id).execute()
        
        # Update or insert positions
        for position in portfolio.positions:
            # Try to update first
            result = self.supabase.table("positions").update({
                "shares": float(position.shares),
                "current_price": float(position.current_price),
                "allocation": float(position.allocation)
            }).eq("portfolio_id", portfolio.id).eq("ticker", position.ticker).execute()
            
            # If no rows updated, insert new position
            if not result.data or len(result.data) == 0:
                self.supabase.table("positions").insert({
                    "portfolio_id": portfolio.id,
                    "ticker": position.ticker,
                    "shares": float(position.shares),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price),
                    "allocation": float(position.allocation)
                }).execute()
        
        # Delete positions that were sold completely
        # Fetch all positions for this portfolio
        all_positions = self.supabase.table("positions").select("ticker").eq("portfolio_id", portfolio.id).execute()
        
        if all_positions.data:
            existing_tickers = [p.ticker for p in portfolio.positions]
            # Delete each position that's not in the current portfolio
            for pos in all_positions.data:
                if pos["ticker"] not in existing_tickers:
                    self.supabase.table("positions").delete().eq("portfolio_id", portfolio.id).eq("ticker", pos["ticker"]).execute()
