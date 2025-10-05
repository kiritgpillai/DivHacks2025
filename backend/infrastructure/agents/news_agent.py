"""News Agent - Fetches and analyzes news headlines"""

import os
import json


async def news_agent(state: dict) -> dict:
    """
    Fetch and analyze news headlines using rule-based classification (0 API calls).
    
    Uses keyword matching instead of LLM for stance classification.
    """
    ticker = state.get("selected_ticker", "")
    
    # Fetch headlines (Tavily or mock data - no Gemini)
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
        if os.getenv("TAVILY_API_KEY"):
            query = f"{ticker} stock news"
            results = tavily.search(query, max_results=3, days=3)
            headlines = [
                {
                    "title": r.get("title", ""),
                    "source": r.get("url", "").split("/")[2] if r.get("url") else "Unknown",
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:200]
                }
                for r in results.get("results", [])
            ]
        else:
            raise Exception("No Tavily key")
    except:
        # Fallback mock data
        headlines = [
            {"title": f"{ticker} stock shows strong performance", "source": "Financial News", "url": "https://example.com", "snippet": "Recent market activity..."},
            {"title": f"Analysts update {ticker} outlook", "source": "Market Watch", "url": "https://example.com", "snippet": "Market sentiment..."},
            {"title": f"{ticker} trading volume increases", "source": "Bloomberg", "url": "https://example.com", "snippet": "Trading patterns..."}
        ]
    
    # Classify headlines using keyword matching (NO GEMINI CALLS)
    bearish_keywords = ["miss", "down", "fall", "decline", "warning", "fine", "investigation", "recall", "lawsuit", "loss", "weak", "disappoints"]
    bullish_keywords = ["beat", "up", "rise", "surge", "approval", "upgrade", "breakthrough", "record", "strong", "exceeds", "growth", "positive"]
    
    for headline in headlines:
        text = (headline["title"] + " " + headline.get("snippet", "")).lower()
        
        # Count keyword matches
        bear_score = sum(1 for word in bearish_keywords if word in text)
        bull_score = sum(1 for word in bullish_keywords if word in text)
        
        if bear_score > bull_score:
            headline["stance"] = "Bear"
        elif bull_score > bear_score:
            headline["stance"] = "Bull"
        else:
            headline["stance"] = "Neutral"
    
    # Compute consensus
    stances = [h["stance"] for h in headlines]
    bull_count = stances.count("Bull")
    bear_count = stances.count("Bear")
    neutral_count = stances.count("Neutral")
    total = len(stances)
    
    if bull_count > bear_count and bull_count > neutral_count:
        consensus = f"{bull_count}/{total} Bull"
    elif bear_count > bull_count and bear_count > neutral_count:
        consensus = f"{bear_count}/{total} Bear"
    else:
        consensus = "Mixed"
    
    # Compute contradiction score vs villain
    villain_stance = state.get("villain_stance", "Bullish")
    if "Bull" in villain_stance:
        disagreement = bear_count / total if total > 0 else 0
    elif "Bear" in villain_stance:
        disagreement = bull_count / total if total > 0 else 0
    else:
        disagreement = 0.5
    
    # Update state
    return {
        **state,
        "headlines": headlines,
        "consensus": consensus,
        "contradiction_score": round(disagreement, 2)
    }

