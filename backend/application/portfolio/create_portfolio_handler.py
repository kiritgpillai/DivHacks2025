"""Create Portfolio Use Case Handler"""

from typing import List, Dict
import uuid
from domain.portfolio.portfolio import Portfolio
from domain.portfolio.risk_profile import RiskProfile
from infrastructure.yfinance_adapter.price_fetcher import get_current_price


class CreatePortfolioHandler:
    """
    Handler for creating a new portfolio (Round 0).
    
    Validates tickers, fetches current prices, and creates portfolio aggregate.
    """
    
    def __init__(self, supabase_client=None):
        # Supabase client for database operations
        self.supabase = supabase_client
        self.portfolio_repo = None  # TODO: remove after full Supabase migration
    
    async def execute(
        self,
        player_id: str,
        tickers: List[str],
        allocations: Dict[str, float],
        risk_profile: str
    ) -> Dict:
        """
        Create a new portfolio.
        
        Args:
            player_id: Player ID
            tickers: List of ticker symbols
            allocations: Dict of {ticker: allocation_dollars}
            risk_profile: "Risk-On", "Balanced", or "Risk-Off"
            
        Returns:
            Dict with portfolio_id and total_value
        """
        # Validate total allocation = $1M
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1_000_000) > 1:
            raise ValueError(f"Total allocation must be $1,000,000, got ${total_allocation:,.0f}")
        
        # Create portfolio aggregate
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            player_id=player_id,
            risk_profile=RiskProfile(risk_profile)
        )
        
        # Add positions (fetch current prices)
        for ticker in tickers:
            try:
                entry_price = await get_current_price(ticker)
                portfolio.add_position(ticker, allocations[ticker], entry_price)
            except Exception as e:
                raise ValueError(f"Failed to add position for {ticker}: {str(e)}")
        
        # Calculate total value
        total_value = portfolio.calculate_total_value()
        
        # Save to Supabase
        if self.supabase:
            await self._save_to_supabase(portfolio)
        
        # Save to repository (legacy, TODO: remove)
        if self.portfolio_repo:
            await self.portfolio_repo.save(portfolio)
        
        return {
            "portfolio_id": portfolio.id,
            "player_id": player_id,
            "risk_profile": risk_profile,
            "positions": [
                {
                    "ticker": p.ticker,
                    "shares": p.shares,
                    "entry_price": p.entry_price,
                    "allocation": p.allocation
                }
                for p in portfolio.positions
            ],
            "cash": portfolio.cash,
            "total_value": total_value
        }
    
    async def _save_to_supabase(self, portfolio: Portfolio) -> None:
        """
        Save portfolio and positions to Supabase.
        
        Args:
            portfolio: Portfolio aggregate to save
        """
        # Insert portfolio record
        self.supabase.table("portfolios").insert({
            "id": portfolio.id,
            "player_id": portfolio.player_id,
            "risk_profile": str(portfolio.risk_profile.value),
            "tickers": [p.ticker for p in portfolio.positions],
            "allocations": {p.ticker: float(p.allocation) for p in portfolio.positions},
            "cash": float(portfolio.cash),
            "total_value": float(portfolio.calculate_total_value())
        }).execute()
        
        # Insert positions
        for position in portfolio.positions:
            self.supabase.table("positions").insert({
                "portfolio_id": portfolio.id,
                "ticker": position.ticker,
                "shares": float(position.shares),
                "entry_price": float(position.entry_price),
                "current_price": float(position.current_price),
                "allocation": float(position.allocation)
            }).execute()

