"""Event Generator Agent Tools"""

import os
from langchain.tools import tool
import json
import random
import google.generativeai as genai
from backend.config import GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))


@tool
async def select_ticker_from_portfolio(portfolio: str) -> str:
    """
    Select ticker from portfolio (weighted by position size).
    
    Larger positions more likely to be selected.
    
    Args:
        portfolio: JSON string of portfolio positions {"AAPL": 300000, "TSLA": 400000}
        
    Returns:
        Selected ticker symbol
    """
    try:
        positions = json.loads(portfolio)
        tickers = list(positions.keys())
        weights = [positions[t] for t in tickers]
        
        # Normalize weights
        total = sum(weights)
        normalized_weights = [w/total for w in weights]
        
        # Weighted random selection
        selected = random.choices(tickers, weights=normalized_weights, k=1)[0]
        
        return json.dumps({
            "ticker": selected,
            "position_size": positions[selected],
            "rationale": f"Selected {selected} (${positions[selected]:,.0f} position)"
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def determine_event_type(ticker: str, difficulty: str = "INTERMEDIATE") -> str:
    """
    Determine event type based on difficulty level.
    
    Args:
        ticker: Stock ticker
        difficulty: BEGINNER, INTERMEDIATE, or ADVANCED
        
    Returns:
        Event type (EARNINGS_SURPRISE, REGULATORY_NEWS, etc.)
    """
    easy_events = ["ANALYST_ACTION", "PRODUCT_NEWS"]
    medium_events = ["EARNINGS_SURPRISE", "REGULATORY_NEWS"]
    hard_events = ["VOLATILITY_SPIKE", "MACRO_EVENT"]
    
    if difficulty == "BEGINNER":
        event_type = random.choice(easy_events)
    elif difficulty == "INTERMEDIATE":
        event_type = random.choice(medium_events)
    else:
        event_type = random.choice(hard_events)
    
    return json.dumps({
        "event_type": event_type,
        "difficulty": difficulty,
        "ticker": ticker
    })


@tool
async def generate_event_description(ticker: str, event_type: str) -> str:
    """
    Generate realistic event description using Gemini.
    
    Args:
        ticker: Stock ticker
        event_type: Type of event (EARNINGS_SURPRISE, etc.)
        
    Returns:
        Event description (2-3 sentences)
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        templates = {
            "EARNINGS_SURPRISE": f"Create a realistic earnings surprise event for {ticker}. Include specific numbers (EPS beat/miss %), pre-market reaction, and key details like revenue and guidance.",
            "REGULATORY_NEWS": f"Create a regulatory news event for {ticker}. Include government action, fine amounts, investigation details, or approval news.",
            "ANALYST_ACTION": f"Create an analyst upgrade or downgrade for {ticker}. Include the firm name, old/new rating, price target, and brief rationale.",
            "VOLATILITY_SPIKE": f"Create a sudden volatility event for {ticker}. Include breaking news, percentage move, volume surge.",
            "PRODUCT_NEWS": f"Create a product-related event for {ticker}. Include launch, recall, breakthrough, or partnership details.",
            "MACRO_EVENT": f"Create a macro event affecting {ticker}'s sector. Include Fed decision, economic data, or policy change."
        }
        
        prompt = f"""{templates.get(event_type, f'Create a market event for {ticker}')}.

Make it:
- Specific with numbers (percentages, dollar amounts, price targets)
- Include immediate market reaction (pre-market move, volume)
- Realistic and educational
- 2-3 sentences maximum

Example format: "Tesla reports Q4 earnings beat of 15% vs analyst expectations. EPS came in at $1.32 vs expected $1.15. Stock surges 6% in pre-market trading on strong vehicle delivery numbers."
"""
        
        response = model.generate_content(prompt)
        description = response.text.strip()
        
        return json.dumps({
            "ticker": ticker,
            "event_type": event_type,
            "description": description,
            "success": True
        })
        
    except Exception as e:
        return json.dumps({
            "ticker": ticker,
            "event_type": event_type,
            "error": str(e),
            "success": False,
            # Fallback description
            "description": f"{ticker} experiences {event_type.replace('_', ' ').lower()} event affecting stock price."
        })


@tool
async def set_event_horizon(event_type: str) -> str:
    """
    Set event horizon (time window for outcome) based on event type.
    
    Args:
        event_type: Type of event
        
    Returns:
        JSON with horizon in trading days
    """
    horizons = {
        "EARNINGS_SURPRISE": 3,
        "REGULATORY_NEWS": 5,
        "ANALYST_ACTION": 3,
        "VOLATILITY_SPIKE": 2,
        "PRODUCT_NEWS": 4,
        "MACRO_EVENT": 5
    }
    
    horizon = horizons.get(event_type, 3)
    
    return json.dumps({
        "event_type": event_type,
        "horizon": horizon,
        "explanation": f"{event_type} typically plays out over {horizon} trading days"
    })


@tool
async def validate_event_realism(ticker: str, event: str, context: str = "") -> str:
    """
    Validate if event makes sense for the ticker.
    
    Args:
        ticker: Stock ticker
        event: Event description
        context: Additional context (sector, company info)
        
    Returns:
        JSON with validation result and confidence
    """
    # Simple validation for MVP
    # In production, could use Gemini to validate
    
    valid = len(event) > 20  # Basic check
    confidence = 0.9 if valid else 0.3
    
    return json.dumps({
        "ticker": ticker,
        "valid": valid,
        "confidence": confidence,
        "message": "Event validated" if valid else "Event too short"
    })

