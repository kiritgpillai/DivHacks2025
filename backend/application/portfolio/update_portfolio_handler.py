"""Update Portfolio Use Case Handler"""

from typing import Dict, Optional
from decimal import Decimal
from backend.domain.portfolio.portfolio import Portfolio
from backend.domain.portfolio.position import Position
from backend.domain.portfolio.risk_profile import RiskProfile
from backend.infrastructure.observability.opik_tracer import log_game_event


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
        
        # Step 3: Apply decision to portfolio
        pl_dollars = Decimal(0)
        shares_after = Decimal(0)
        allocation_after = Decimal(0)
        
        if decision == "SELL_ALL":
            pl_dollars = portfolio.apply_sell_all(ticker)
            shares_after = Decimal(0)
            allocation_after = Decimal(0)
            
        elif decision == "SELL_HALF":
            pl_dollars = portfolio.apply_sell_half(ticker)
            position_after = portfolio.get_position(ticker)
            if position_after:
                shares_after = position_after.shares
                allocation_after = position_after.allocation
            
        elif decision == "HOLD":
            portfolio.apply_hold(ticker, new_price)
            position_after = portfolio.get_position(ticker)
            shares_after = position_after.shares
            allocation_after = position_after.allocation
            value_after = position_after.calculate_value()
            pl_dollars = value_after - value_before
            
        elif decision == "BUY":
            amount_spent = portfolio.apply_buy(ticker, new_price)
            pl_dollars = -amount_spent  # Negative (spent cash)
            position_after = portfolio.get_position(ticker)
            shares_after = position_after.shares
            allocation_after = position_after.allocation
            
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
        return {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "decision": decision,
            "pl_dollars": float(pl_dollars),
            "pl_percent": float((pl_dollars / value_before) * 100) if value_before > 0 else 0,
            "shares_before": float(shares_before),
            "shares_after": float(shares_after),
            "allocation_before": float(allocation_before),
            "allocation_after": float(allocation_after),
            "new_total_value": float(new_total_value),
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
        portfolio = Portfolio(
            id=portfolio_data["id"],
            player_id=portfolio_data["player_id"],
            risk_profile=RiskProfile(portfolio_data["risk_profile"]),
            initial_cash=float(portfolio_data.get("cash", 0))  # Use remaining cash as initial
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
