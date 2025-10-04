"""Start Game Use Case Handler"""

import uuid
from typing import Dict


class StartGameHandler:
    """
    Handler for starting a new game session.
    
    Creates game session record and initializes round counter.
    """
    
    def __init__(self):
        # In production, inject repository dependency
        self.game_repo = None  # TODO: inject SupabaseGameRepository
        self.portfolio_repo = None  # TODO: inject SupabasePortfolioRepository
    
    async def execute(self, portfolio_id: str) -> Dict:
        """
        Start a new game session.
        
        Args:
            portfolio_id: Portfolio ID to play with
            
        Returns:
            Dict with game_id and initial state
        """
        # Fetch portfolio (TODO: implement)
        # portfolio = await self.portfolio_repo.get(portfolio_id)
        
        # Create game session
        game_id = str(uuid.uuid4())
        
        # Initialize game session record (TODO: persist to DB)
        game_session = {
            "id": game_id,
            "portfolio_id": portfolio_id,
            "current_round": 0,
            "portfolio_value": 1_000_000,  # TODO: calculate from portfolio
            "started_at": None  # TODO: add timestamp
        }
        
        # Save game session (TODO: implement persistence)
        if self.game_repo:
            await self.game_repo.save(game_session)
        
        return {
            "game_id": game_id,
            "portfolio_id": portfolio_id,
            "current_round": 0,
            "message": "Game started! Ready for Round 1."
        }

