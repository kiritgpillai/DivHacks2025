"""Price Agent - Handles price data and historical outcome replay"""

import os
import asyncio
from backend.infrastructure.yfinance_adapter.price_fetcher import get_price_snapshot as fetch_price, detect_price_pattern
from backend.infrastructure.yfinance_adapter.historical_sampler import (
    sample_historical_window,
    calculate_historical_outcomes
)


async def price_agent(state: dict) -> dict:
    """
    Fetch price data and detect patterns using yfinance (0 API calls to Gemini).
    
    All data comes from Yahoo Finance, no LLM needed.
    """
    print(f"🔍 PRICE AGENT CALLED: task='{state.get('task', 'unknown')}', ticker='{state.get('selected_ticker', 'unknown')}'")
    ticker = state.get("selected_ticker", "")
    
    try:
        # Get price snapshot from yfinance
        snapshot = await fetch_price(ticker)
        
        # Detect price pattern
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        pattern = detect_price_pattern(hist)
        
        # Update state
        return {
            **state,
            "price_snapshot": snapshot,
            "price_pattern": pattern
        }
    except Exception as e:
        # Fallback data
        return {
            **state,
            "price_snapshot": {
                "ticker": ticker,
                "current": 100.0,
                "sparkline": [98, 99, 100, 101, 100],
                "high_5d": 102.0,
                "low_5d": 97.0,
                "volume_avg": 1000000
            },
            "price_pattern": "neutral"
        }


async def background_price_agent(
    ticker: str,
    event_type: str,
    event_horizon: int,
    game_id: str,
    round_number: int
) -> dict:
    """
    Background price agent that pre-calculates historical outcomes.
    
    This runs in the background during round generation to provide
    instant outcomes when the user makes a decision.
    
    Args:
        ticker: Stock ticker
        event_type: Type of event (EARNINGS_BEAT, etc.)
        event_horizon: Number of trading days
        game_id: Game session ID
        round_number: Round number
        
    Returns:
        Dict with pre-calculated historical outcomes
    """
    try:
        # Pre-calculate historical case for instant decision processing
        historical_case = await sample_historical_window(
            ticker=ticker,
            event_type=event_type,
            horizon=event_horizon
        )
        
        # Pre-calculate historical outcomes for data tab
        historical_outcomes = await calculate_historical_outcomes(
            event_type=event_type,
            ticker=ticker,
            num_samples=10
        )
        
        # Get current price for portfolio calculations
        from backend.infrastructure.yfinance_adapter.price_fetcher import get_current_price
        current_price = await get_current_price(ticker)
        
        return {
            "ticker": ticker,
            "event_type": event_type,
            "historical_case": historical_case,
            "historical_outcomes": historical_outcomes,
            "current_price": current_price,
            "game_id": game_id,
            "round_number": round_number,
            "status": "ready"
        }
        
    except Exception as e:
        print(f"Background price agent error for {ticker}: {e}")
        # Return fallback data
        return {
            "ticker": ticker,
            "event_type": event_type,
            "historical_case": {
                "ticker": ticker,
                "event_type": event_type,
                "date": "2023-01-01",
                "horizon": event_horizon,
                "day0_price": 100.0,
                "day_h_price": 105.0,
                "price_path": [100.0, 102.0, 103.0, 105.0],
                "return_pct": 0.05
            },
            "historical_outcomes": {
                "similar_cases": 5,
                "sell_half": {"median_return": 0.025, "explanation": "Captured partial upside"},
                "hold": {"median_return": 0.05, "explanation": "Full exposure to price movement"}
            },
            "current_price": 100.0,
            "game_id": game_id,
            "round_number": round_number,
            "status": "fallback"
        }

