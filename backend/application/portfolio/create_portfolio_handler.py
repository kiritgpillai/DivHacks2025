"""Create Portfolio Use Case Handler"""

from typing import List, Dict
import uuid
from backend.domain.portfolio.portfolio import Portfolio
from backend.domain.portfolio.risk_profile import RiskProfile
from backend.infrastructure.yfinance_adapter.price_fetcher import get_current_price


class CreatePortfolioHandler:
    """
    Handler for creating a new portfolio (Round 0).
    
    Validates tickers, fetches current prices, and creates portfolio aggregate.
    """
    
    def __init__(self):
        # In production, inject repository dependency
        self.portfolio_repo = None  # TODO: inject SupabasePortfolioRepository
    
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
        
        # Save to repository (TODO: implement persistence)
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

