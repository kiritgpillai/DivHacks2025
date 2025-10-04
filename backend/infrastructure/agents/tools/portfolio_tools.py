"""Portfolio Agent Tools"""

import os
from langchain.tools import tool
import yfinance as yf
from typing import Dict, Any
import json


@tool
async def validate_ticker(ticker: str) -> str:
    """
    Validate if ticker exists and can fetch prices.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        JSON with validation result and current price
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Try to get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price:
            return json.dumps({
                "valid": True,
                "ticker": ticker,
                "current_price": float(current_price),
                "name": info.get('longName', ticker)
            })
        else:
            return json.dumps({
                "valid": False,
                "ticker": ticker,
                "error": "Unable to fetch price"
            })
            
    except Exception as e:
        return json.dumps({
            "valid": False,
            "ticker": ticker,
            "error": str(e)
        })


@tool
async def get_current_price(ticker: str) -> str:
    """
    Fetch current price for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        JSON with current price
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            return json.dumps({
                "ticker": ticker,
                "price": current_price,
                "success": True
            })
        else:
            return json.dumps({
                "ticker": ticker,
                "error": "No price data available",
                "success": False
            })
            
    except Exception as e:
        return json.dumps({
            "ticker": ticker,
            "error": str(e),
            "success": False
        })


@tool
async def get_fundamentals(ticker: str) -> str:
    """
    Get fundamental data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        JSON with P/E ratio, beta, volatility, growth
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for volatility calculation
        hist = stock.history(period="1mo")
        volatility_30d = float(hist['Close'].pct_change().std() * (252 ** 0.5)) if not hist.empty else 0.0
        
        return json.dumps({
            "ticker": ticker,
            "pe_ratio": info.get('trailingPE'),
            "beta": info.get('beta'),
            "volatility_30d": round(volatility_30d, 4),
            "yoy_revenue_growth": info.get('revenueGrowth'),
            "market_cap": info.get('marketCap'),
            "success": True
        })
        
    except Exception as e:
        return json.dumps({
            "ticker": ticker,
            "error": str(e),
            "success": False
        })


@tool
async def check_allocation(allocations: str, budget: float) -> str:
    """
    Validate allocations don't exceed budget.
    
    Args:
        allocations: JSON string of allocations {"AAPL": 300000, "TSLA": 400000}
        budget: Total budget available
        
    Returns:
        JSON with validation result
    """
    try:
        alloc_dict = json.loads(allocations)
        total = sum(alloc_dict.values())
        
        return json.dumps({
            "valid": total <= budget,
            "total_allocated": total,
            "budget": budget,
            "remaining": budget - total,
            "over_budget": max(0, total - budget)
        })
        
    except Exception as e:
        return json.dumps({
            "valid": False,
            "error": str(e)
        })

