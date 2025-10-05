"""Insight Agent - Provides neutral tips and behavioral coaching"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GEMINI_MODEL, TEMPERATURE_INSIGHT

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_INSIGHT)


async def insight_agent(state: dict) -> dict:
    """
    Generate neutral educational tip using direct execution (1 API call only).
    
    Creates tip based on event type and price pattern.
    """
    event_type = state.get("event_type", "")
    price_pattern = state.get("price_pattern", "neutral")
    
    # Determine volatility from price data
    price_snapshot = state.get("price_snapshot", {})
    high = price_snapshot.get("high_5d", 100)
    low = price_snapshot.get("low_5d", 100)
    current = price_snapshot.get("current", 100)
    
    if current > 0:
        volatility_pct = ((high - low) / current) * 100
        if volatility_pct > 5:
            volatility = "high"
        elif volatility_pct > 2:
            volatility = "medium"
        else:
            volatility = "low"
    else:
        volatility = "medium"
    
    # Generate tip (ONLY API CALL)
    prompt = f"""Write a neutral, educational tip for a trading game Data tab.

Context:
- Event type: {event_type}
- Price pattern: {price_pattern}
- Volatility: {volatility}

Requirements:
- 1 sentence maximum
- Educational (teach market concepts)
- Non-coercive (don't tell player what to do)
- Evidence-based (reference data patterns)
- Actionable framework

Examples:
- "Earnings gaps with high beta and rising vol often mean-revert within 3 days—consider trimming instead of exiting fully."
- "High volatility (>40% 30-day) suggests uncertainty—historical outcomes show 'Sell Half' captured 70% of 'Hold' upside with 50% of risk."

Generate tip (return ONLY the tip text, no JSON or formatting):"""
    
    try:
        response = await llm.ainvoke(prompt)
        tip = response.content.strip()
    except Exception as e:
        # Fallback tips by event type
        fallbacks = {
            "EARNINGS_SURPRISE": "Earnings gaps with high beta often mean-revert within 3 days—position sizing matters more than direction.",
            "REGULATORY_NEWS": "Regulatory events show wide outcome variance—diversification and timing matter more than prediction.",
            "ANALYST_ACTION": "Analyst upgrades/downgrades have diminishing impact over time—focus on fundamentals, not ratings.",
            "VOLATILITY_SPIKE": "High volatility suggests uncertainty—partial exits can capture upside while limiting downside.",
            "PRODUCT_NEWS": "Product announcements often see initial overreaction—wait for market to digest before acting.",
            "MACRO_EVENT": "Macro events affect sectors differently—sector rotation may be more important than individual stocks."
        }
        tip = fallbacks.get(event_type, "Market events show wide outcome variance—position sizing and timing matter more than direction alone.")
    
    # Update state
    return {
        **state,
        "neutral_tip": tip
    }

