"""Start Round Use Case Handler"""

from typing import Dict
from backend.infrastructure.agents.game_graph import start_round


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
    
    async def execute(self, game_id: str, round_number: int) -> Dict:
        """
        Start a new round.
        
        Args:
            game_id: Game session ID
            round_number: Round number (1-5)
            
        Returns:
            Dict with event, villain take, and data tab
        """
        # Fetch game session and portfolio (TODO: implement)
        # game_session = await self.game_repo.get(game_id)
        # portfolio = await self.portfolio_repo.get(game_session['portfolio_id'])
        
        # For MVP, use mock data
        portfolio_data = {
            "AAPL": 300000,
            "TSLA": 400000,
            "MSFT": 300000
        }
        portfolio_value = 1_000_000
        
        # Invoke multi-agent graph
        result = await start_round(
            game_id=game_id,
            portfolio_id="mock_portfolio_id",
            round_number=round_number,
            portfolio=portfolio_data,
            portfolio_value=portfolio_value
        )
        
        # Save round data (TODO: implement persistence)
        # await self.game_repo.save_round(game_id, round_number, result)
        
        return {
            "game_id": game_id,
            "round_number": round_number,
            "event": result["event"],
            "villain_take": result["villain_take"],
            "data_tab": result["data_tab"]
        }

