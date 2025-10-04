# Tavily Integration - Market Mayhem

## Why Tavily?

**Replaces**: Manual news scraping, NewsAPI ($449/mo)
**Free Tier**: 1000 requests/month
**Benefit**: Real-time headlines for news stance detection and contradiction scoring

---

## Setup

```python
from tavily import TavilyClient
import os

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
```

Get API key: https://tavily.com (free signup)

---

## Core Use Cases

### 1. Fetch Ticker News (News Agent)

```python
async def fetch_ticker_news(ticker: str, days: int = 3) -> List[Dict]:
    """Fetch recent headlines for a ticker"""
    
    query = f"{ticker} stock news"
    
    results = await tavily.search(
        query=query,
        topic="news",
        days=days,
        max_results=3  # 2-3 headlines per ticker
    )
    
    headlines = [
        {
            "title": r['title'],
            "source": r.get('domain', 'Unknown'),
            "url": r.get('url', ''),
            "snippet": r.get('content', '')[:200]
        }
        for r in results.get('results', [])
    ]
    
    return headlines
```

**Example Output**:
```json
[
  {
    "title": "Tesla beats Q4 earnings by 15%",
    "source": "cnbc.com",
    "url": "https://...",
    "snippet": "Tesla reported strong Q4 results..."
  },
  {
    "title": "Analysts raise Tesla price targets",
    "source": "reuters.com",
    "url": "https://...",
    "snippet": "Following the earnings beat..."
  }
]
```

---

### 2. Stance Detection (News Agent + Gemini)

```python
async def assign_headline_stance(
    headline: str,
    event_context: str
) -> str:
    """Classify headline as Bull/Bear/Neutral using Gemini"""
    
    prompt = f"""Classify this stock market headline as Bull (positive), Bear (negative), or Neutral.
    
    Headline: {headline}
    Event context: {event_context}
    
    Guidelines:
    - Bull: Positive news, price likely to rise
    - Bear: Negative news, price likely to fall
    - Neutral: Informational, no clear direction
    
    Return ONLY one word: Bull, Bear, or Neutral.
    """
    
    from google import generativeai as genai
    model = genai.GenerativeModel('gemini-pro')
    response = await model.generate_content_async(prompt)
    
    stance = response.text.strip()
    return stance  # Bull | Bear | Neutral
```

**Example**:
- "Tesla beats earnings" → **Bull**
- "Tesla recalls 1M vehicles" → **Bear**
- "Tesla reports Q4 revenue" → **Neutral**

---

### 3. Consensus Calculation (News Agent)

```python
def calculate_consensus(headlines_with_stances: List[Dict]) -> str:
    """Calculate consensus from headline stances"""
    
    bull_count = sum(1 for h in headlines_with_stances if h['stance'] == 'Bull')
    bear_count = sum(1 for h in headlines_with_stances if h['stance'] == 'Bear')
    total = len(headlines_with_stances)
    
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
```

**Example**:
- 2 Bull, 0 Bear → "Two-thirds Bull"
- 1 Bull, 2 Bear → "Two-thirds Bear"
- 1 Bull, 1 Bear, 1 Neutral → "Mixed"

---

### 4. Contradiction Score (News Agent)

```python
def compute_contradiction_vs_villain(
    headlines: List[Dict],
    villain_stance: str  # "Bullish" or "Bearish"
) -> float:
    """Calculate how much headlines disagree with Villain"""
    
    opposing_count = 0
    
    for headline in headlines:
        if villain_stance == "Bearish" and headline['stance'] == "Bull":
            opposing_count += 1
        elif villain_stance == "Bullish" and headline['stance'] == "Bear":
            opposing_count += 1
    
    contradiction_score = opposing_count / len(headlines) if headlines else 0.0
    
    return contradiction_score
```

**Example**:
- Villain: "Bearish" (says sell)
- Headlines: 2 Bull, 0 Bear
- **Contradiction: 1.0 (100% disagree with Villain)**

---

## Rate Limit Management

### Free Tier: 1000 requests/month

**Strategy**: Aggressive caching + smart usage

```python
import hashlib
import json

async def cached_tavily_search(
    query: str,
    cache_ttl: int = 3600,  # 1 hour
    **kwargs
):
    """Wrapper with Redis caching"""
    
    # Create cache key
    cache_key = f"tavily:{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache hit: {query}")
        return json.loads(cached)
    
    # Make request
    logger.info(f"Tavily API call: {query}")
    await track_tavily_usage()
    results = tavily.search(query, **kwargs)
    
    # Cache results
    await redis.setex(cache_key, cache_ttl, json.dumps(results))
    
    return results
```

### Usage Tracking

```python
async def track_tavily_usage():
    """Increment monthly counter"""
    
    today = datetime.now()
    month_key = f"tavily:usage:{today.year}:{today.month}"
    
    count = await redis.incr(month_key)
    
    # Set expiry (2 months)
    if count == 1:
        await redis.expire(month_key, 60 * 60 * 24 * 60)
    
    # Alert if approaching limit
    if count > 900:  # 90% of 1000
        logger.warning(f"Tavily usage at {count}/1000 for month")
    
    return count

async def get_remaining_tavily_calls() -> int:
    """Check remaining quota"""
    today = datetime.now()
    month_key = f"tavily:usage:{today.year}:{today.month}"
    
    used = await redis.get(month_key) or 0
    return 1000 - int(used)
```

---

## Complete News Pipeline

### Tool: fetch_and_analyze_news (News Agent)

```python
from langchain.tools import tool

@tool
async def fetch_and_analyze_news(ticker: str) -> str:
    """Complete news pipeline: fetch + stance + consensus + contradiction
    
    This is the main tool the News Agent uses.
    """
    
    # 1. Fetch headlines (1 Tavily call)
    headlines = await cached_tavily_search(
        query=f"{ticker} stock news",
        topic="news",
        days=3,
        max_results=3
    )
    
    # 2. Assign stance to each (3 Gemini calls)
    headlines_with_stance = []
    for headline in headlines.get('results', [])[:3]:
        stance = await assign_headline_stance(headline['title'], ticker)
        headlines_with_stance.append({
            "title": headline['title'],
            "source": headline.get('domain', 'Unknown'),
            "stance": stance
        })
    
    # 3. Calculate consensus
    consensus = calculate_consensus(headlines_with_stance)
    
    # Return as JSON for agent
    return json.dumps({
        "headlines": headlines_with_stance,
        "consensus": consensus
    })
```

---

## Budget Planning

### Monthly Budget: 1000 requests

| Use Case | Frequency | Monthly Total |
|----------|-----------|---------------|
| News per round | 1 call/round | ~3 calls/game × 100 games = 300 |
| Cache hits | 70% hit rate | 300 × 0.3 = 90 actual calls |
| **Total Estimate** | | **~90-100 calls/month** |

**With aggressive caching**: Support 100-150 games/month

### Per-Game Cost

```
Game with 7 rounds:
  - Round 1: Fetch AAPL news → 1 Tavily call (then cached 1hr)
  - Round 2: Fetch TSLA news → 1 Tavily call (then cached 1hr)
  - Round 3: Fetch MSFT news → 1 Tavily call (then cached 1hr)
  - Round 4: Fetch AAPL news → Cache hit (0 calls)
  - ...
  
Total: ~3 Tavily calls per game
```

**Capacity**: ~300 games/month with 1000 free requests

---

## Error Handling

### Graceful Degradation

```python
async def safe_tavily_search(query: str, max_retries: int = 2):
    """Search with retry and fallback"""
    
    for attempt in range(max_retries):
        try:
            results = await tavily.search(query)
            return results
        
        except Exception as e:
            logger.error(f"Tavily search failed (attempt {attempt + 1}): {e}")
            
            if attempt == max_retries - 1:
                # Return empty on final failure
                return {'results': []}
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

async def fetch_news_with_fallback(ticker: str):
    """Try Tavily, fallback to cached/generic"""
    
    # Check remaining quota
    remaining = await get_remaining_tavily_calls()
    if remaining < 10:
        logger.warning("Tavily quota low, using cached news")
        return await get_cached_generic_news(ticker)
    
    # Try Tavily
    results = await safe_tavily_search(f"{ticker} stock news")
    
    if not results or not results.get('results'):
        logger.warning("Tavily returned no results, using fallback")
        return await get_cached_generic_news(ticker)
    
    return results
```

---

## Testing Without Quota Impact

### Mock for Tests

```python
# tests/infrastructure/test_tavily.py
class MockTavilyClient:
    async def search(self, query: str, **kwargs):
        """Mock Tavily for testing"""
        
        # Return fake but realistic headlines
        if "AAPL" in query or "Apple" in query:
            return {
                'results': [
                    {
                        'title': 'Apple announces record iPhone sales',
                        'domain': 'cnbc.com',
                        'url': 'https://example.com/apple-sales',
                        'content': 'Apple reported strong Q4 iPhone sales...'
                    },
                    {
                        'title': 'Analysts bullish on Apple stock',
                        'domain': 'reuters.com',
                        'url': 'https://example.com/apple-analysts',
                        'content': 'Several analysts raised price targets...'
                    }
                ]
            }
        
        return {'results': []}

def test_fetch_and_analyze_news():
    """Test news pipeline without using Tavily quota"""
    mock_client = MockTavilyClient()
    
    # Inject mock
    tavily_client = mock_client
    
    headlines = await fetch_ticker_news("AAPL")
    
    assert len(headlines) > 0
    assert 'title' in headlines[0]
```

---

## Best Practices

1. **Always cache**: 1 hour TTL for headlines
2. **Batch when possible**: Fetch multiple tickers if available
3. **Track usage religiously**: Log every request
4. **Use fallbacks**: Have cached/generic news ready
5. **Monitor quota**: Alert at 90%, disable at 95%
6. **Test with mocks**: Never use quota for tests
7. **Respect rate limits**: Add exponential backoff

---

## ACL Pattern (Domain Isolation)

```python
# domain/news/NewsProvider.py (Interface)
from abc import ABC, abstractmethod

class NewsProvider(ABC):
    @abstractmethod
    async def get_ticker_news(self, ticker: str) -> List['Headline']:
        pass

# infrastructure/tavily/TavilyNewsProvider.py (Implementation)
class TavilyNewsProvider(NewsProvider):
    def __init__(self, tavily_client: TavilyClient, cache: RedisCache):
        self.tavily = tavily_client
        self.cache = cache
    
    async def get_ticker_news(self, ticker: str) -> List[Headline]:
        # Tavily-specific implementation
        results = await self.tavily.search(f"{ticker} stock news", days=3)
        
        # Return domain objects (NOT Tavily response)
        return [
            Headline(
                title=r['title'],
                source=r.get('domain', 'Unknown'),
                url=r.get('url', ''),
                snippet=r.get('content', '')[:200]
            )
            for r in results.get('results', [])[:3]
        ]
```

**Benefit**: Can swap Tavily for another provider without changing domain code.

---

## Summary

✅ **Free Tier**: 1000 requests/month (supports 100-150 games)
✅ **Aggressive Caching**: 1 hour TTL reduces calls by 70%
✅ **Stance Detection**: Gemini classifies Bull/Bear/Neutral
✅ **Consensus**: Aggregate stances for player decision support
✅ **Contradiction Score**: Measure Villain vs headlines disagreement
✅ **Graceful Degradation**: Fallback to cached news if quota exhausted
✅ **ACL Pattern**: Domain isolation for easy provider swapping

**Tavily provides the real-world news foundation for Market Mayhem's evidence-based decision making.** 🚀
