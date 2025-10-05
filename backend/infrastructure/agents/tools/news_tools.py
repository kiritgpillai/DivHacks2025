"""News Agent Tools"""

import os
from langchain.tools import tool
import json
from typing import List
try:
    from tavily import TavilyClient
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
    TAVILY_AVAILABLE = bool(os.getenv("TAVILY_API_KEY"))
except ImportError:
    TAVILY_AVAILABLE = False
    tavily = None

import google.generativeai as genai
from config import GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))


@tool
async def fetch_ticker_news(ticker: str, days: int = 3) -> str:
    """
    Fetch recent headlines for a ticker using Tavily.
    
    Args:
        ticker: Stock ticker symbol
        days: Days back to search (default 3)
        
    Returns:
        JSON array of headlines
    """
    if not TAVILY_AVAILABLE or not tavily:
        # Fallback to mock data if Tavily not available
        return json.dumps([
            {
                "title": f"{ticker} stock shows strong performance",
                "source": "Financial News",
                "url": "https://example.com",
                "snippet": "Recent market activity..."
            },
            {
                "title": f"Analysts update {ticker} outlook",
                "source": "Market Watch",
                "url": "https://example.com",
                "snippet": "Market sentiment..."
            }
        ])
    
    try:
        query = f"{ticker} stock news"
        results = tavily.search(
            query=query,
            topic="news",
            days=days,
            max_results=3
        )
        
        headlines = [
            {
                "title": r.get('title', ''),
                "source": r.get('domain', 'Unknown'),
                "url": r.get('url', ''),
                "snippet": r.get('content', '')[:200]
            }
            for r in results.get('results', [])[:3]
        ]
        
        return json.dumps(headlines)
        
    except Exception as e:
        return json.dumps([{
            "error": str(e),
            "ticker": ticker
        }])


@tool
async def assign_headline_stance(headline: str, event_context: str = "") -> str:
    """
    Classify headline as Bull/Bear/Neutral using Gemini.
    
    Args:
        headline: Headline text
        event_context: Optional context about the event
        
    Returns:
        Stance classification: "Bull", "Bear", or "Neutral"
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""Classify this stock market headline as Bull (positive), Bear (negative), or Neutral.

Headline: {headline}
{f"Context: {event_context}" if event_context else ""}

Guidelines:
- Bull: Positive news, price likely to rise
- Bear: Negative news, price likely to fall
- Neutral: Informational, no clear direction

Return ONLY one word: Bull, Bear, or Neutral."""
        
        response = model.generate_content(prompt)
        stance = response.text.strip()
        
        # Validate response
        if stance not in ["Bull", "Bear", "Neutral"]:
            stance = "Neutral"
        
        return stance
        
    except Exception as e:
        return "Neutral"


@tool
async def compute_consensus(headlines_json: str) -> str:
    """
    Calculate consensus from headlines with stances.
    
    Args:
        headlines_json: JSON array of headlines with stance field
        
    Returns:
        Consensus string (e.g., "Two-thirds Bull")
    """
    try:
        headlines = json.loads(headlines_json)
        
        bull_count = sum(1 for h in headlines if h.get('stance') == 'Bull')
        bear_count = sum(1 for h in headlines if h.get('stance') == 'Bear')
        total = len(headlines)
        
        if total == 0:
            return "No Data"
        
        bull_pct = bull_count / total
        bear_pct = bear_count / total
        
        if bull_pct >= 0.67:
            return "Two-thirds Bull"
        elif bear_pct >= 0.67:
            return "Two-thirds Bear"
        elif bull_pct > 0.5:
            return "Majority Bull"
        elif bear_pct > 0.5:
            return "Majority Bear"
        else:
            return "Mixed"
            
    except Exception as e:
        return "Mixed"


@tool
async def compute_contradiction_score(headlines_json: str, villain_stance: str) -> str:
    """
    Calculate how much headlines disagree with Villain.
    
    Args:
        headlines_json: JSON array of headlines with stance field
        villain_stance: "Bullish" or "Bearish"
        
    Returns:
        JSON with contradiction score (0-1)
    """
    try:
        headlines = json.loads(headlines_json)
        
        opposing_count = 0
        for headline in headlines:
            h_stance = headline.get('stance', '')
            if villain_stance == "Bearish" and h_stance == "Bull":
                opposing_count += 1
            elif villain_stance == "Bullish" and h_stance == "Bear":
                opposing_count += 1
        
        total = len(headlines)
        score = opposing_count / total if total > 0 else 0.0
        
        return json.dumps({
            "contradiction_score": round(score, 2),
            "opposing_headlines": opposing_count,
            "total_headlines": total
        })
        
    except Exception as e:
        return json.dumps({
            "contradiction_score": 0.0,
            "error": str(e)
        })

