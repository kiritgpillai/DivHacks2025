"""Price fetcher using yfinance"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any


async def get_current_price(ticker: str) -> float:
    """
    Fetch current price for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Current closing price
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    
    if data.empty:
        raise ValueError(f"No price data available for {ticker}")
    
    return float(data['Close'].iloc[-1])


async def get_price_snapshot(ticker: str) -> Dict[str, Any]:
    """
    Get current price + recent OHLC data
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with current price, sparkline, high/low
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="5d")
    
    if data.empty:
        raise ValueError(f"No price data available for {ticker}")
    
    return {
        "ticker": ticker,
        "current": float(data['Close'].iloc[-1]),
        "sparkline": [float(p) for p in data['Close'].tolist()],
        "high_5d": float(data['High'].max()),
        "low_5d": float(data['Low'].min()),
        "volume_avg": float(data['Volume'].mean())
    }


def detect_price_pattern(price_data: pd.DataFrame) -> str:
    """
    Detect price patterns in historical data
    
    Args:
        price_data: DataFrame with OHLC data
        
    Returns:
        Pattern name (e.g., "3_down_closes", "gap_up", "volatility_spike")
    """
    closes = price_data['Close']
    
    # Check for 3 consecutive down days
    if len(closes) >= 4:
        last_4 = closes[-4:].tolist()
        if all(last_4[i] > last_4[i+1] for i in range(3)):
            return "3_down_closes"
    
    # Check for 3 consecutive up days
    if len(closes) >= 4:
        last_4 = closes[-4:].tolist()
        if all(last_4[i] < last_4[i+1] for i in range(3)):
            return "3_up_closes"
    
    # Check for gap up (today's open > yesterday's close by >2%)
    if len(price_data) >= 2:
        today_open = price_data['Open'].iloc[-1]
        yesterday_close = price_data['Close'].iloc[-2]
        if (today_open - yesterday_close) / yesterday_close > 0.02:
            return "gap_up"
    
    # Check for gap down
    if len(price_data) >= 2:
        today_open = price_data['Open'].iloc[-1]
        yesterday_close = price_data['Close'].iloc[-2]
        if (yesterday_close - today_open) / yesterday_close > 0.02:
            return "gap_down"
    
    # Check for volatility spike (>5% daily moves)
    if len(closes) >= 2:
        pct_changes = closes.pct_change().abs()
        if (pct_changes > 0.05).any():
            return "volatility_spike"
    
    # Check for consolidation (tight range <2% over 5 days)
    if len(closes) >= 5:
        recent_5 = closes[-5:]
        range_pct = (recent_5.max() - recent_5.min()) / recent_5.min()
        if range_pct < 0.02:
            return "consolidation"
    
    return "normal"

