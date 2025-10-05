"""Start Round Use Case Handler"""

from typing import Dict, Optional
import asyncio
from backend.infrastructure.agents.game_graph import start_round
from backend.infrastructure.agents.price_agent import background_price_agent


class StartRoundHandler:
    """
    Handler for starting a new game round.
    
    Invokes multi-agent graph to:
    1. Generate event (Event Generator Agent)
    2. Fetch news (News Agent)
    3. Get price data (Price Agent)
    4. Generate Villain hot take (Villain Agent)
    5. Provide neutral tip (Insight Agent)
    """
    
    def __init__(self):
        # In production, inject repository dependencies
        self.game_repo = None  # TODO: inject SupabaseGameRepository
        self.portfolio_repo = None  # TODO: inject SupabasePortfolioRepository
    
    async def execute(
        self, 
        game_id: str, 
        round_number: int,
        portfolio: Dict[str, float] = None,
        portfolio_value: float = None
    ) -> Dict:
        """
        Start a new round.
        
        Args:
            game_id: Game session ID
            round_number: Round number (1-3)
            portfolio: Portfolio positions {ticker: allocation_dollars} - REQUIRED, must be user's actual portfolio
            portfolio_value: Total portfolio value - REQUIRED, must be user's actual value
            
        Returns:
            Dict with event, villain take, and data tab
            
        Raises:
            ValueError: If portfolio or portfolio_value not provided
        """
        # IMPORTANT: Portfolio MUST be provided - no hardcoded fallback
        # This ensures events are always generated for the user's actual tickers
        if not portfolio or portfolio_value is None:
            raise ValueError(
                "Portfolio data is required. Cannot start round without user's portfolio. "
                "This is a critical error - portfolio should be passed from game session."
            )
        
        # Validate portfolio is not empty
        if not portfolio or len(portfolio) == 0:
            raise ValueError("Portfolio cannot be empty. User must have at least one position.")
        
        # Use DYNAMIC portfolio data (user's actual tickers and allocations)
        portfolio_data = portfolio
        
        # Invoke multi-agent graph with DYNAMIC portfolio
        # Event Generator will select a ticker from this portfolio
        result = await start_round(
            game_id=game_id,
            portfolio_id="mock_portfolio_id",  # TODO: pass actual portfolio_id
            round_number=round_number,
            portfolio=portfolio_data,  # DYNAMIC: User's actual tickers
            portfolio_value=portfolio_value
        )
        
        return {
            "game_id": game_id,
            "round_number": round_number,
            "event": result["event"],
            "villain_take": result["villain_take"],
            "data_tab": result["data_tab"]
        }

