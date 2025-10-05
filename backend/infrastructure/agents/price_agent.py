"""Price Agent - Handles price data and historical outcome replay"""

import os
from infrastructure.yfinance_adapter.price_fetcher import get_price_snapshot as fetch_price, detect_price_pattern


async def price_agent(state: dict) -> dict:
    """
    Fetch price data and detect patterns using yfinance (0 API calls to Gemini).
    
    All data comes from Yahoo Finance, no LLM needed.
    """
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
        # No fallback data - raise error to ensure proper error handling
        print(f"Error fetching price data for {ticker}: {e}")
        raise ValueError(f"Failed to fetch price data for {ticker}: {str(e)}")

