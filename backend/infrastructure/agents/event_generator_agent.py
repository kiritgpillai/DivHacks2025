"""Event Generator Agent - Creates market event scenarios"""

import os
import json
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_MODEL, TEMPERATURE_EVENT_GENERATOR

# Initialize LLM (only used for event description generation)
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_EVENT_GENERATOR)


async def event_generator_agent(state: dict) -> dict:
    """
    Generate market event using direct execution (1 API call only).
    
    Combines all event generation logic into single LLM call.
    """
    portfolio = state.get("portfolio", {})
    
    # Step 1: Select ticker (no API call - pure logic)
    tickers = list(portfolio.keys())
    weights = [portfolio[t] for t in tickers]
    total = sum(weights)
    normalized_weights = [w/total for w in weights]
    selected_ticker = random.choices(tickers, weights=normalized_weights, k=1)[0]
    
    # Step 2: Determine event type (no API call - pure logic)
    event_types = ["EARNINGS_SURPRISE", "REGULATORY_NEWS", "ANALYST_ACTION", 
                   "VOLATILITY_SPIKE", "PRODUCT_NEWS", "MACRO_EVENT"]
    event_type = random.choice(event_types)
    
    # Step 3: Set horizon (no API call - pure logic)
    horizons = {
        "EARNINGS_SURPRISE": 3,
        "REGULATORY_NEWS": 5,
        "ANALYST_ACTION": 3,
        "VOLATILITY_SPIKE": 2,
        "PRODUCT_NEWS": 4,
        "MACRO_EVENT": 5
    }
    horizon = horizons.get(event_type, 3)
    
    # Step 4: Generate description (ONLY API CALL)
    templates = {
        "EARNINGS_SURPRISE": f"Create a realistic earnings surprise event for {selected_ticker}. Include specific numbers (EPS beat/miss %), pre-market reaction, and key details like revenue and guidance.",
        "REGULATORY_NEWS": f"Create a regulatory news event for {selected_ticker}. Include government action, fine amounts, investigation details, or approval news.",
        "ANALYST_ACTION": f"Create an analyst upgrade or downgrade for {selected_ticker}. Include the firm name, old/new rating, price target, and brief rationale.",
        "VOLATILITY_SPIKE": f"Create a sudden volatility event for {selected_ticker}. Include breaking news, percentage move, volume surge.",
        "PRODUCT_NEWS": f"Create a product-related event for {selected_ticker}. Include launch, recall, breakthrough, or partnership details.",
        "MACRO_EVENT": f"Create a macro event affecting {selected_ticker}'s sector. Include Fed decision, economic data, or policy change."
    }
    
    prompt = f"""{templates.get(event_type, f'Create a market event for {selected_ticker}')}.

Make it:
- Specific with numbers (percentages, dollar amounts, price targets)
- Include immediate market reaction (pre-market move, volume)
- Realistic and educational
- 2-3 sentences maximum

Return ONLY the event description, no JSON or formatting."""
    
    try:
        response = await llm.ainvoke(prompt)
        description = response.content.strip()
    except Exception as e:
        description = f"{selected_ticker} experiences {event_type.replace('_', ' ').lower()} event affecting stock price."
    
    # Update state
    return {
        **state,
        "selected_ticker": selected_ticker,
        "event_type": event_type,
        "event_description": description,
        "event_horizon": horizon,
        "task": "event_generated"
    }

