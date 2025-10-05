"""Start Game Use Case Handler"""

import uuid
from typing import Dict, Optional


class StartGameHandler:
    """
    Handler for starting a new game session.
    
    Creates game session record and initializes round counter.
    Integrates with Supabase for persistence and Opik for observability.
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize handler with optional Supabase client.
        
        Args:
            supabase_client: Optional Supabase client for persistence
        """
        self.supabase = supabase_client
    
    async def execute(self, portfolio_id: str) -> Dict:
        """
        Start a new game session.
        
        Args:
            portfolio_id: Portfolio ID to play with
            
        Returns:
            Dict with game_id and initial state
        """
        # Fetch portfolio value from Supabase if available
        # Always start with $1,000,000 base value
        portfolio_value = 1_000_000.0
        
        if self.supabase:
            try:
                # Verify portfolio exists and get its current value
                portfolio_response = self.supabase.table("portfolios").select("total_value").eq("id", portfolio_id).execute()
                
                if portfolio_response.data and len(portfolio_response.data) > 0:
                    # Use the portfolio's total value (should be $1M for new portfolios)
                    portfolio_value = float(portfolio_response.data[0]["total_value"])
            except Exception as e:
                print(f"Warning: Failed to fetch portfolio from Supabase: {e}")
                # Continue with default $1M value
        
        # Create game session
        game_id = str(uuid.uuid4())
        
        # Save game session to Supabase if available
        if self.supabase:
            try:
                self.supabase.table("game_sessions").insert({
                    "id": game_id,
                    "portfolio_id": portfolio_id,
                    "current_round": 0,
                    "portfolio_value": portfolio_value
                }).execute()
            except Exception as e:
                print(f"Warning: Failed to save game session to Supabase: {e}")
                # Continue anyway - will use in-memory storage
        
        # Log to Opik
        try:
            from backend.infrastructure.observability.opik_tracer import log_game_event
            log_game_event("game_started", {
                "game_id": game_id,
                "portfolio_id": portfolio_id,
                "portfolio_value": portfolio_value,
                "supabase_enabled": self.supabase is not None
            })
        except Exception as e:
            # Don't fail if Opik logging fails
            print(f"Warning: Failed to log to Opik: {e}")
        
        return {
            "game_id": game_id,
            "portfolio_id": portfolio_id,
            "current_round": 0,
            "portfolio_value": portfolio_value,
            "message": "Game started! Ready for Round 1."
        }

