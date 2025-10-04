"""Price Agent Tools - Historical Replay Core"""

import os
from langchain.tools import tool
import json
from ...yfinance_adapter.price_fetcher import (
    get_current_price as fetch_price,
    get_price_snapshot as fetch_snapshot,
    detect_price_pattern
)
from ...yfinance_adapter.historical_sampler import (
    sample_historical_window as sample_window,
    apply_decision_to_path as apply_decision,
    calculate_historical_outcomes as calc_outcomes
)
import yfinance as yf


@tool
async def get_price_snapshot(ticker: str) -> str:
    """
    Get current price + 5-day OHLC data.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        JSON with current price, sparkline, high/low
    """
    try:
        snapshot = await fetch_snapshot(ticker)
        return json.dumps(snapshot)
    except Exception as e:
        return json.dumps({"error": str(e), "ticker": ticker})


@tool
async def get_sparkline(ticker: str, days: int = 5) -> str:
    """
    Get price sparkline for UI charting.
    
    Args:
        ticker: Stock ticker
        days: Number of days (default 5)
        
    Returns:
        JSON with price array
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days}d")
        
        return json.dumps({
            "ticker": ticker,
            "prices": [float(p) for p in hist['Close'].tolist()],
            "dates": [d.strftime("%Y-%m-%d") for d in hist.index]
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def detect_price_pattern_tool(ticker: str) -> str:
    """
    Detect price patterns in recent data.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Pattern name (e.g., "3_down_closes", "gap_up", "volatility_spike")
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="10d")
        
        pattern = detect_price_pattern(hist)
        
        return json.dumps({
            "ticker": ticker,
            "pattern": pattern,
            "description": _get_pattern_description(pattern)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def sample_historical_window(ticker: str, event_type: str, horizon: int) -> str:
    """
    Sample a matched historical case and return real price path.
    
    THIS IS THE CORE GAME MECHANIC - no random outcomes!
    
    Args:
        ticker: Stock ticker
        event_type: Event type (EARNINGS_BEAT, REGULATORY_NEWS, etc.)
        horizon: Number of trading days
        
    Returns:
        JSON with historical case and price path
    """
    try:
        case = await sample_window(ticker, event_type, horizon)
        return json.dumps(case)
    except Exception as e:
        return json.dumps({"error": str(e), "ticker": ticker})


@tool
async def apply_decision_to_path(
    decision: str,
    historical_case_json: str,
    position_size: float
) -> str:
    """
    Apply player decision to historical price path and calculate P/L.
    
    Args:
        decision: SELL_ALL, SELL_HALF, HOLD, or BUY
        historical_case_json: JSON string from sample_historical_window
        position_size: Current position size in dollars
        
    Returns:
        JSON with P/L dollars, percent, and explanation
    """
    try:
        historical_case = json.loads(historical_case_json)
        outcome = await apply_decision(decision, historical_case, position_size)
        return json.dumps(outcome)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def calculate_historical_outcomes(event_type: str, ticker: str) -> str:
    """
    Calculate median historical outcomes for each action type.
    
    Used for Data tab to show what typically happened.
    
    Args:
        event_type: Event type
        ticker: Stock ticker
        
    Returns:
        JSON with median returns per action
    """
    try:
        outcomes = await calc_outcomes(event_type, ticker, num_samples=10)
        return json.dumps(outcomes)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _get_pattern_description(pattern: str) -> str:
    """Get human-readable pattern description"""
    descriptions = {
        "3_down_closes": "Three consecutive down days",
        "3_up_closes": "Three consecutive up days",
        "gap_up": "Gapped up >2% from previous close",
        "gap_down": "Gapped down >2% from previous close",
        "volatility_spike": "High volatility (>5% daily moves)",
        "consolidation": "Tight range consolidation (<2%)",
        "normal": "Normal price action"
    }
    return descriptions.get(pattern, pattern)

