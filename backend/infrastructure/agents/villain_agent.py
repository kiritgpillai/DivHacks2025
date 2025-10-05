"""Villain Agent - Generates biased hot takes"""

import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GEMINI_MODEL, TEMPERATURE_VILLAIN

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_VILLAIN)


async def villain_agent(state: dict) -> dict:
    """
    Generate biased hot take using direct execution (1 API call only).
    
    Determines stance and bias using logic, then generates hot take with LLM.
    """
    event_description = state.get("event_description", "")
    ticker = state.get("selected_ticker", "")
    
    # Step 1: Determine stance (no API call - pure logic)
    bearish_keywords = ["miss", "down", "fine", "investigation", "recall", "warning"]
    bullish_keywords = ["beat", "up", "approval", "breakthrough", "upgrade", "surge"]
    
    event_lower = event_description.lower()
    
    # Determine base stance from event
    if any(word in event_lower for word in bearish_keywords):
        base_stance = "Bearish"
    elif any(word in event_lower for word in bullish_keywords):
        base_stance = "Bullish"
    else:
        base_stance = random.choice(["Bullish", "Bearish"])
    
    # Be contrarian 70% of the time
    be_contrarian = random.random() < 0.7
    stance = "Bearish" if (base_stance == "Bullish" and be_contrarian) else ("Bullish" if (base_stance == "Bearish" and be_contrarian) else base_stance)
    
    # Step 2: Select cognitive bias (no API call - pure logic)
    biases = ["Fear Appeal", "Overconfidence/FOMO", "Authority Lure", "Recency Bias", "Anchoring Bias"]
    bias = random.choice(biases)
    
    # Step 3: Generate hot take (ONLY API CALL)
    prompt = f"""You are a trash-talking Villain AI in a trading game. Generate a bold, emotionally charged hot take.

Event: {event_description}
Your stance: {stance}
Cognitive bias to use: {bias}

Guidelines:
- Be confident and provocative (1-2 sentences)
- Use strong emotional language
- Be WRONG on purpose to mislead the player
- Exploit the {bias} bias explicitly
- Never hedge or show doubt

Generate your hot take now (return ONLY the hot take text, no JSON or formatting):"""
    
    try:
        response = await llm.ainvoke(prompt)
        hot_take = response.content.strip().strip('"\'')
    except Exception as e:
        # Fallback hot takes
        hot_take = f"This is the easiest trade of the year! {ticker} is going {'to the moon' if stance == 'Bullish' else 'to crash'}. Don't miss out!"
    
    # Update state
    return {
        **state,
        "villain_hot_take": hot_take,
        "villain_stance": stance,
        "villain_bias": bias
    }

