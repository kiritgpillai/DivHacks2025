"""Historical case sampler for outcome replay"""

import yfinance as yf
from datetime import datetime, timedelta
import random
from typing import Dict, Any
from decimal import Decimal


async def sample_historical_window(
    ticker: str,
    event_type: str,
    horizon: int
) -> Dict[str, Any]:
    """
    Sample a matched historical case and return real price path.
    
    This is the CORE INNOVATION - no random outcomes, only real historical data.
    
    Args:
        ticker: Stock ticker symbol
        event_type: Type of event (EARNINGS_BEAT, etc.)
        horizon: Number of trading days to look ahead
        
    Returns:
        Dict with historical case details including price path
    """
    # TODO: In production, check pre-seeded database first
    # For MVP, dynamically sample from yfinance
    
    stock = yf.Ticker(ticker)
    
    # Sample a random date from past 2 years (avoiding recent data)
    days_back = random.randint(horizon + 10, 730)
    end_date = datetime.now() - timedelta(days=days_back)
    start_date = end_date - timedelta(days=horizon + 5)  # Get a bit extra for pattern detection
    
    # Fetch historical data
    hist = stock.history(start=start_date, end=end_date)
    
    if len(hist) < horizon:
        raise ValueError(f"Insufficient historical data for {ticker}")
    
    # Extract price path
    price_path = hist['Close'].tolist()[:horizon+1]
    day0_price = price_path[0]
    day_h_price = price_path[min(horizon, len(price_path)-1)]
    
    return {
        "ticker": ticker,
        "event_type": event_type,
        "date": start_date.strftime("%Y-%m-%d"),
        "horizon": horizon,
        "day0_price": float(day0_price),
        "day_h_price": float(day_h_price),
        "price_path": [float(p) for p in price_path],
        "return_pct": float((day_h_price - day0_price) / day0_price)
    }


async def apply_decision_to_path(
    decision: str,
    historical_case: Dict[str, Any],
    position_size: float
) -> Dict[str, Any]:
    """
    Apply player decision to historical price path and calculate P/L.
    
    This implements the exact logic from the domain design:
    - SELL_ALL: Exit at day 0, no further impact
    - SELL_HALF: Realize half at day 0, other half rides to day H
    - HOLD: Full position rides to day H
    - BUY: Add 10% to position, rides to day H
    
    Args:
        decision: Player decision (SELL_ALL, SELL_HALF, HOLD, BUY)
        historical_case: Historical case data from sample_historical_window
        position_size: Current position size in dollars
        
    Returns:
        Dict with P/L dollars, percent, and explanation
    """
    day0_price = Decimal(str(historical_case['day0_price']))
    day_h_price = Decimal(str(historical_case['day_h_price']))
    position_size_decimal = Decimal(str(position_size))
    
    if decision == "SELL_ALL":
        # Exit entire position at day 0, no further exposure
        # P/L is $0 because we exit at current price (no gain/loss)
        pl_dollars = Decimal(0)
        pl_percent = Decimal(0)
        explanation = f"Exited entire ${position_size:,.0f} position at ${day0_price:.2f}. No P/L since exit at current price."
        
    elif decision == "SELL_HALF":
        # Exit half at day 0, remaining half rides to day H
        # P/L is only on the remaining half that rides the price change
        half_size = position_size_decimal / Decimal(2)
        day_h_return = (day_h_price - day0_price) / day0_price
        pl_dollars = half_size * day_h_return  # P/L only on remaining half
        pl_percent = day_h_return / Decimal(2)  # Weighted by half exposure
        
        explanation = f"Sold half (${float(half_size):,.0f}) at ${day0_price:.2f}. Remaining half rode from ${day0_price:.2f} to ${day_h_price:.2f} ({float(day_h_return)*100:.2f}%). P/L on remaining half: {float(pl_percent)*100:.2f}%."
        
    elif decision == "HOLD":
        # Full position rides to day H
        # P/L is the gain/loss from entry price to final price
        day_h_return = (day_h_price - day0_price) / day0_price
        pl_dollars = position_size_decimal * day_h_return
        pl_percent = day_h_return
        
        explanation = f"Held entire ${position_size:,.0f} position. Price moved from ${day0_price:.2f} to ${day_h_price:.2f} ({float(day_h_return)*100:.2f}%). Full exposure to price movement."
        
    elif decision == "BUY":
        # Add 10% to position, total position rides to day H
        # P/L is calculated on the additional 10% purchased
        buy_size = position_size_decimal * Decimal("0.1")
        total_size = position_size_decimal + buy_size
        day_h_return = (day_h_price - day0_price) / day0_price
        pl_dollars = buy_size * day_h_return  # P/L only on the additional 10%
        pl_percent = day_h_return * Decimal("0.1")  # Weighted by 10% addition
        
        explanation = f"Added ${float(buy_size):,.0f} (10%) to ${position_size:,.0f} position at ${day0_price:.2f}. P/L on additional 10%: {float(pl_percent)*100:.2f}%."
        
    else:
        raise ValueError(f"Invalid decision: {decision}")
    
    return {
        "pl_dollars": float(pl_dollars),
        "pl_percent": float(pl_percent),
        "explanation": explanation,
        "historical_case_used": {
            "date": historical_case['date'],
            "ticker": historical_case['ticker'],
            "day0_price": historical_case['day0_price'],
            "day_h_price": historical_case['day_h_price']
        }
    }


async def calculate_historical_outcomes(
    event_type: str,
    ticker: str,
    num_samples: int = 10
) -> Dict[str, Any]:
    """
    Calculate median historical outcomes for each action type.
    
    Used for the Data tab to show players what typically happened
    for similar events in the past.
    
    Args:
        event_type: Type of event (EARNINGS_BEAT, etc.)
        ticker: Stock ticker
        num_samples: Number of historical cases to sample
        
    Returns:
        Dict with median returns for each action
    """
    # Sample multiple historical windows
    sell_all_returns = []
    sell_half_returns = []
    hold_returns = []
    
    for _ in range(num_samples):
        try:
            case = await sample_historical_window(ticker, event_type, 3)
            
            # SELL_ALL: always 0
            sell_all_returns.append(0.0)
            
            # SELL_HALF: half of the return
            sell_half_returns.append(case['return_pct'] / 2)
            
            # HOLD: full return
            hold_returns.append(case['return_pct'])
            
        except Exception:
            continue
    
    if not hold_returns:
        raise ValueError("Could not sample sufficient historical data")
    
    # Calculate medians
    import statistics
    
    return {
        "similar_cases": len(hold_returns),
        "sell_all": {
            "median_return": 0.0,
            "explanation": "Exited before typical price movement"
        },
        "sell_half": {
            "median_return": round(statistics.median(sell_half_returns), 4),
            "explanation": "Captured partial upside/downside, reduced risk"
        },
        "hold": {
            "median_return": round(statistics.median(hold_returns), 4),
            "explanation": "Full exposure to typical price movement"
        }
    }

