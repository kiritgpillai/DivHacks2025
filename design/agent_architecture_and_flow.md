# Agent Architecture and Flow - Market Mayhem

## Agent System Overview

Market Mayhem uses **6 specialized ReAct agents** orchestrated by LangGraph to create a portfolio-building game with dynamic event generation, historical outcome replay, trash-talking Villain AI, and behavioral coaching. Each agent has specific responsibilities and tools.

**Key Innovation**: Agents collaborate to generate realistic events tied to player holdings, provide evidence-based data, mislead with Villain takes, replay historical outcomes, and coach players on behavior—all without random outcomes.

---

## Agent Types & Responsibilities

### 1. **Event Generator Agent** (ReAct Agent with Tools)
**Role**: Create realistic market event scenarios tied to player's portfolio holdings

**Tools Available**:
- `select_ticker_from_portfolio` - Choose which stock to focus on (weighted by position size)
- `determine_event_type` - Choose event type based on difficulty and market context
- `generate_event_description` - Create compelling event narrative using Gemini
- `set_event_horizon` - Determine time window for outcome (3-5 trading days)
- `validate_event_realism` - Check if event makes sense for the ticker/sector

**Example Tool Call**:
```python
# Create event for TSLA in player's portfolio
→ Calls: select_ticker_from_portfolio(portfolio={"AAPL": 300k, "TSLA": 400k, "MSFT": 300k})
→ Returns: "TSLA" (higher weight due to larger position)
→ Calls: determine_event_type(ticker="TSLA", difficulty="INTERMEDIATE", market_context="tech_sector_up")
→ Returns: "EARNINGS_SURPRISE"
→ Calls: generate_event_description(ticker="TSLA", event_type="EARNINGS_SURPRISE")
→ Uses Gemini with prompt:
    "Create a realistic earnings surprise event for Tesla. Include:
     - What happened (beat/miss by what %)
     - Pre-market reaction
     - Key details (revenue, EPS, guidance)
     Make it compelling and educational. 2-3 sentences."
→ Returns: "Tesla reports Q4 earnings beat of 15% vs analyst expectations. EPS came in at $1.32 vs expected $1.15. Stock surges 6% in pre-market trading on strong vehicle delivery numbers."
→ Calls: set_event_horizon(event_type="EARNINGS_SURPRISE")
→ Returns: 3 trading days
→ Calls: validate_event_realism(ticker="TSLA", event="earnings beat", context="growth stock")
→ Returns: {"valid": true, "confidence": 0.92}
```

**Event Types Generated**:
- **EARNINGS_SURPRISE** - Earnings beat/miss
- **REGULATORY_NEWS** - Government action, investigation, approval
- **ANALYST_ACTION** - Upgrade/downgrade, price target change
- **VOLATILITY_SPIKE** - Sudden price movement, breaking news
- **PRODUCT_NEWS** - Launch, recall, breakthrough
- **MACRO_EVENT** - Fed decision, economic data affecting sector

---

### 2. **Portfolio Agent** (ReAct Agent with Tools)
**Role**: Manage player portfolio, validate holdings, calculate valuations

**Tools Available**:
- `validate_ticker` - Check if ticker exists and can fetch prices
- `get_current_price` - Fetch latest price for a ticker
- `calculate_position_value` - Calculate current value of a position
- `check_allocation` - Validate allocation doesn't exceed budget
- `get_fundamentals` - Fetch P/E ratio, beta, YoY growth, volatility
- `apply_decision` - Apply Sell All/Sell Half/Hold/Buy to portfolio

**Example Tool Call**:
```python
# Player creates portfolio with AAPL, TSLA, MSFT
→ Calls: validate_ticker("AAPL")
→ Returns: {"valid": true, "current_price": 195.50}
→ Calls: check_allocation({"AAPL": 300000, "TSLA": 400000, "MSFT": 300000}, budget=1000000)
→ Returns: {"valid": true, "remaining": 0}
→ Creates Portfolio entity with validated holdings
```

---

### 3. **News Agent** (ReAct Agent with Tools)
**Role**: Fetch recent headlines, classify stance, compute consensus and contradiction score

**Tools Available**:
- `fetch_ticker_news` - Get 2-3 recent headlines for ticker (via Tavily)
- `assign_headline_stance` - Classify headline as Bull/Bear/Neutral (via Gemini)
- `calculate_consensus` - Aggregate stances (e.g., "Two-thirds Bull")
- `compute_contradiction_vs_villain` - Calculate how much headlines disagree with Villain

**Example Tool Call**:
```python
# For TSLA event, fetch news and analyze
→ Calls: fetch_ticker_news(ticker="TSLA", days=3)
→ Returns: [
    {"title": "Tesla beats Q4 earnings", "source": "CNBC"},
    {"title": "Analysts raise TSLA targets", "source": "Reuters"}
  ]
→ Calls: assign_headline_stance("Tesla beats Q4 earnings", "earnings_beat")
→ Returns: "Bull"
→ Calls: assign_headline_stance("Analysts raise TSLA targets", "analyst_upgrade")
→ Returns: "Bull"
→ Calls: calculate_consensus([{"stance": "Bull"}, {"stance": "Bull"}])
→ Returns: "Two-thirds Bull" (100% Bull, but phrased conservatively)
→ Villain says: "This is a pump, I'm selling everything!"
→ Calls: compute_contradiction_vs_villain(headlines, villain_stance="Bearish")
→ Returns: 1.0  # 100% of headlines contradict Villain
```

---

### 4. **Price Agent** (ReAct Agent with Tools)
**Role**: Provide price data, sample historical windows, replay outcomes

**Tools Available**:
- `get_price_snapshot` - Current price + recent OHLC
- `get_sparkline` - 5-day price sparkline for UI
- `detect_price_pattern` - Identify "3 down closes", "gap up", "volatility spike"
- `sample_historical_window` - Find matching past event, return price path
- `apply_decision_to_path` - Apply Sell All/Sell Half/Hold to price path, calculate P/L
- `calculate_historical_outcomes` - For Data tab: median returns for each action

**Example Tool Call**:
```python
# Player decides "SELL_HALF" on TSLA earnings beat
→ Calls: sample_historical_window(ticker="TSLA", event_type="EARNINGS_BEAT", horizon=3)
→ Searches historical_cases table or dynamically fetches from yfinance
→ Finds: TSLA earnings beat on 2023-10-18, 3-day window
→ Returns: HistoricalCase(
    date="2023-10-18",
    day0_price=242.50,
    day_h_price=251.30,
    price_path=[242.50, 245.20, 248.90, 251.30]
  )
→ Calls: apply_decision_to_path(decision="SELL_HALF", case)
→ Calculates:
    - Sell half at day 0: 242.50, no P/L yet
    - Remaining half rides to day 3: 251.30
    - Return on remaining half: +3.63%
    - Weighted return: +1.81% (half the position)
→ Returns: Outcome(pl_dollars=7240, pl_percent=1.81, explanation="...")
```

**Historical Outcomes for Data Tab**:
```python
→ Calls: calculate_historical_outcomes(event_type="EARNINGS_BEAT", ticker="TSLA")
→ Finds 12 similar cases
→ Returns: {
    "sell_all": {
      "median_return": -0.03,
      "explanation": "Exited before typical 3-7% post-earnings rise"
    },
    "sell_half": {
      "median_return": 0.02,
      "explanation": "Captured partial upside, reduced risk"
    },
    "hold": {
      "median_return": 0.05,
      "explanation": "Full exposure to typical earnings beat rally"
    }
  }
```

---

### 5. **Villain Agent** (ReAct Agent with Tools)
**Role**: Generate biased, trash-talking hot takes to induce fear/FOMO

**Tools Available**:
- `generate_hot_take` - Create bold, emotionally charged statement
- `label_cognitive_bias` - Identify and label the bias (Fear/FOMO/Authority/Recency)
- `determine_villain_stance` - Choose stance (often contrarian to rational analysis)
- `create_villain_persona` - Maintain consistent character

**Example Tool Call**:
```python
# TSLA earnings beat event, rational action is BUY or HOLD
→ Calls: determine_villain_stance(event="TSLA earnings beat", rational="HOLD")
→ Decides: Contrarian "Bearish" stance (to mislead)
→ Calls: generate_hot_take(
    event="TSLA earnings beat",
    stance="Bearish",
    bias_type="Fear Appeal"
  )
→ Uses Gemini with prompt:
    "Generate a trash-talking hot take using Fear Appeal.
     Be wrong on purpose to mislead the player. 1-2 sentences."
→ Returns: "This earnings beat is a trap! Smart money is dumping into retail hype. I'm selling ALL my TSLA before it crashes tomorrow. Don't be the bag holder!"
→ Calls: label_cognitive_bias(hot_take)
→ Returns: "Fear Appeal"
→ Final VillainTake: {
    text: "This earnings beat is a trap! Smart money is...",
    bias: "Fear Appeal",
    stance: "Bearish"
  }
```

**Bias Types**:
- **Fear Appeal**: "It's going to crash! Sell now!"
- **Overconfidence**: "This is a guaranteed 50% gain, I'm all in!"
- **Authority Lure**: "Top analysts are saying X, follow the experts!"
- **Recency Bias**: "It's up 3 days in a row, momentum is king!"

---

### 6. **Insight Agent** (ReAct Agent with Tools)
**Role**: Provide neutral tips during rounds, aggregate decisions, generate behavioral profile and coaching

**Tools Available**:
- `write_neutral_tip` - Generate one-line educational tip for Data tab
- `aggregate_behavior` - Analyze all decision logs, compute metrics
- `classify_profile` - Determine Rational/Emotional/Conservative
- `generate_coaching` - Create 2-4 personalized recommendations
- `identify_patterns` - Detect panic sells, FOMO chasing, Villain resistance

**Example Tool Call (During Round)**:
```python
# For Data tab neutral tip
→ Calls: write_neutral_tip(
    event_type="EARNINGS_BEAT",
    price_pattern="gap_up",
    volatility="high"
  )
→ Uses Gemini to generate educational, non-coercive tip
→ Returns: "Earnings gaps with high beta and rising vol often mean-revert within 3 days—consider trimming instead of exiting fully."
```

**Example Tool Call (Final Report)**:
```python
# After 7 rounds complete
→ Calls: aggregate_behavior(decision_logs)
→ Calculates:
    - Data tab usage: 6/7 rounds (85%)
    - Consensus alignment: 5/7 decisions (71%)
    - Villain followed under high contradiction: 1/7 (14%)
    - Panic sells: 0
    - Chased spikes: 1
→ Calls: classify_profile(metrics)
→ Rule-based logic:
    IF data_tab_usage > 70% AND consensus_alignment > 60% AND beat_villain:
      RETURN "Rational"
    ELIF followed_villain_high_contradiction > 40% OR panic_sells > 2:
      RETURN "Emotional"
    ELIF small_sizes AND frequent_trimming AND low_drawdowns:
      RETURN "Conservative"
→ Returns: "Rational"
→ Calls: generate_coaching(decision_logs, profile="Rational")
→ Returns: [
    "In downgrade scenarios, your 'Sell All' underperformed 'Sell Half' historically—consider partial de-risking.",
    "You chased one spike (NVDA after 3 up days with high vol)—wait for consolidation.",
    "Your 'Hold' on mixed signals captured mean-reversion—keep that discipline."
  ]
```

---

## LangGraph Multi-Agent Architecture

### Agent Graph Structure

```python
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-pro")

# Event Generator Agent
event_generator_agent = create_react_agent(
    llm,
    tools=[
        select_ticker_from_portfolio,
        determine_event_type,
        generate_event_description,
        set_event_horizon,
        validate_event_realism
    ],
    prompt="You generate realistic market event scenarios tied to the player's portfolio. Select a ticker from their holdings (weight by position size), choose an appropriate event type, and create a compelling, educational scenario description."
)

# Portfolio Agent
portfolio_agent = create_react_agent(
    llm,
    tools=[
        validate_ticker,
        get_current_price,
        calculate_position_value,
        check_allocation,
        get_fundamentals,
        apply_decision
    ],
    prompt="You manage player portfolios. Validate tickers, fetch prices, calculate valuations, and apply decisions."
)

# News Agent
news_agent = create_react_agent(
    llm,
    tools=[
        fetch_ticker_news,
        assign_headline_stance,
        calculate_consensus,
        compute_contradiction_vs_villain
    ],
    prompt="You fetch and analyze news. Classify headline stances (Bull/Bear/Neutral), compute consensus, and calculate contradiction scores vs the Villain."
)

# Price Agent
price_agent = create_react_agent(
    llm,
    tools=[
        get_price_snapshot,
        get_sparkline,
        detect_price_pattern,
        sample_historical_window,
        apply_decision_to_path,
        calculate_historical_outcomes
    ],
    prompt="You handle price data and historical outcome replay. Sample matched historical windows, apply decisions to price paths, and calculate P/L. Never use random outcomes."
)

# Villain Agent
villain_agent = create_react_agent(
    llm,
    tools=[
        generate_hot_take,
        label_cognitive_bias,
        determine_villain_stance,
        create_villain_persona
    ],
    prompt="You are a trash-talking Villain. Generate biased hot takes to mislead players. Use cognitive biases (Fear/FOMO/Authority/Recency) and be confidently wrong often."
)

# Insight Agent
insight_agent = create_react_agent(
    llm,
    tools=[
        write_neutral_tip,
        aggregate_behavior,
        classify_profile,
        generate_coaching,
        identify_patterns
    ],
    prompt="You provide neutral coaching. Write educational tips, analyze player behavior, classify profiles (Rational/Emotional/Conservative), and generate personalized coaching."
)
```

---

## Multi-Agent Workflows

### Flow 1: Portfolio Setup (Round 0)

```
Player selects 3-6 tickers and allocates $1M
    ↓
┌──────────────────────────────────────────┐
│  Portfolio Agent                         │
├──────────────────────────────────────────┤
│  ReAct Loop:                             │
│    Thought: "Need to validate tickers"   │
│    Action: validate_ticker("AAPL")       │
│    Observation: {"valid": true, "price": 195.50} │
│    Action: validate_ticker("TSLA")       │
│    Observation: {"valid": true, "price": 251.30} │
│    Action: validate_ticker("MSFT")       │
│    Observation: {"valid": true, "price": 415.20} │
│    Thought: "Check allocation"           │
│    Action: check_allocation({...}, budget=1000000) │
│    Observation: {"valid": true}          │
│    Final Answer: Portfolio created       │
└──────────────────────────────────────────┘
    ↓
Portfolio entity saved, game ready to start
```

---

### Flow 2: Round Start (Event Generation + Data Collection)

```
Backend selects round, invokes Event Generator
    ↓
┌──────────────────────────────────────────┐
│  Event Generator Agent                   │
├──────────────────────────────────────────┤
│  ReAct Loop:                             │
│    Thought: "Select ticker from portfolio"│
│    Action: select_ticker_from_portfolio(│
│            portfolio={"AAPL": 300k,      │
│                       "TSLA": 400k,      │
│                       "MSFT": 300k})     │
│    Observation: "TSLA" (weighted random) │
│    Thought: "Choose event type"          │
│    Action: determine_event_type(         │
│            ticker="TSLA",                │
│            difficulty="INTERMEDIATE")    │
│    Observation: "EARNINGS_SURPRISE"      │
│    Thought: "Create compelling scenario" │
│    Action: generate_event_description(   │
│            ticker="TSLA",                │
│            event_type="EARNINGS_SURPRISE")│
│    Observation: "Tesla reports Q4..."    │
│    Action: set_event_horizon("EARNINGS")│
│    Observation: 3 days                   │
│    Final Answer: Event scenario created  │
└──────────────────────────────────────────┘
    ↓
Event passed to other agents...
```

### Flow 3: Complete Round Start (All Agents)
    ↓
┌──────────────────────────────────────────┐
│  Portfolio Agent                         │
├──────────────────────────────────────────┤
│  ReAct Loop:                             │
│    Thought: "Need to validate tickers"   │
│    Action: validate_ticker("AAPL")       │
│    Observation: {"valid": true, "price": 195.50} │
│    Action: validate_ticker("TSLA")       │
│    Observation: {"valid": true, "price": 251.30} │
│    Action: validate_ticker("MSFT")       │
│    Observation: {"valid": true, "price": 415.20} │
│    Thought: "Check allocation"           │
│    Action: check_allocation({...}, budget=1000000) │
│    Observation: {"valid": true}          │
│    Final Answer: Portfolio created       │
└──────────────────────────────────────────┘
    ↓
Portfolio entity saved, game ready to start
```

```
Backend initiates round start
    ↓
┌──────────────────────────────────────────┐
│  News Agent: Fetch headlines             │
├──────────────────────────────────────────┤
│  Action: fetch_ticker_news("TSLA", days=3) │
│  Returns: 2 headlines                    │
│  Action: assign_headline_stance(...)     │
│  Returns: "Bull", "Bull"                 │
│  Action: calculate_consensus([...])      │
│  Returns: "Two-thirds Bull"              │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Villain Agent: Generate hot take        │
├──────────────────────────────────────────┤
│  Action: determine_villain_stance(...)   │
│  Returns: "Bearish" (contrarian)         │
│  Action: generate_hot_take(stance="Bearish", bias="Fear") │
│  Returns: "Earnings trap! Sell now!"     │
│  Action: label_cognitive_bias(...)       │
│  Returns: "Fear Appeal"                  │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  News Agent: Compute contradiction       │
├──────────────────────────────────────────┤
│  Action: compute_contradiction_vs_villain([Bull, Bull], "Bearish") │
│  Returns: 1.0 (100% disagree)            │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Price Agent: Get price data             │
├──────────────────────────────────────────┤
│  Action: get_sparkline("TSLA", days=5)   │
│  Returns: [240, 238, 236, 242, 251]      │
│  Action: detect_price_pattern(...)       │
│  Returns: "gap_up_after_down_trend"      │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Price Agent: Historical outcomes        │
├──────────────────────────────────────────┤
│  Action: calculate_historical_outcomes("EARNINGS_BEAT", "TSLA") │
│  Returns: {sell_all: -0.03, sell_half: 0.02, hold: 0.05} │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Insight Agent: Neutral tip              │
├──────────────────────────────────────────┤
│  Action: write_neutral_tip(event="EARNINGS_BEAT", pattern="gap_up", vol="high") │
│  Returns: "Earnings gaps with high beta and rising vol often mean-revert..." │
└──────────────────────────────────────────┘
    ↓
Push to client:
- Event description
- Villain take + bias label
- Data tab content (headlines, fundamentals, sparkline, historical, tip)
```

**Total Time**: 4-5 seconds (Event Generator sequential, then parallel for others)

---

### Flow 4: Player Decision → Outcome Replay

```
Player clicks "SELL HALF" after 18.5 seconds
    ↓
┌──────────────────────────────────────────┐
│  Price Agent: Sample historical window   │
├──────────────────────────────────────────┤
│  Action: sample_historical_window(ticker="TSLA", event="EARNINGS_BEAT", horizon=3) │
│  Returns: HistoricalCase(date="2023-10-18", day0_price=242.50, day_h_price=251.30) │
│  Action: apply_decision_to_path(decision="SELL_HALF", case) │
│  Calculates:                             │
│    - Sell half at 242.50: realized       │
│    - Remaining half rides to 251.30: +3.63% │
│    - Weighted P/L: +1.81%                │
│  Returns: Outcome(pl_dollars=7240, pl_percent=1.81) │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Portfolio Agent: Update portfolio       │
├──────────────────────────────────────────┤
│  Action: apply_decision(portfolio, "SELL_HALF", ticker="TSLA", pl=7240) │
│  Updates: Portfolio value: $1,000,000 → $1,007,240 │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Insight Agent: Flag behavior            │
├──────────────────────────────────────────┤
│  Action: identify_patterns(decision_log) │
│  Checks:                                 │
│    - Panic sell? No (no 3 down closes)   │
│    - Chased spike? No (not after 3 up)   │
│    - Used data tab? Yes                  │
│    - Aligned with consensus? Yes         │
│    - Resisted Villain? Yes (high contradiction) │
│  Returns: {"rational": true}             │
└──────────────────────────────────────────┘
    ↓
Log to decision_tracker table, push outcome to client
```

**Total Time**: 1-2 seconds

---

### Flow 5: Final Report Generation

```
After round 7 completes
    ↓
┌──────────────────────────────────────────┐
│  Insight Agent: Aggregate behavior       │
├──────────────────────────────────────────┤
│  Action: aggregate_behavior(all_decision_logs) │
│  Calculates:                             │
│    - Data tab usage: 6/7 (85%)           │
│    - Consensus alignment: 5/7 (71%)      │
│    - Villain resistance: High            │
│    - Panic sells: 0                      │
│    - Chased spikes: 1                    │
│  Returns: BehaviorMetrics {...}          │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Insight Agent: Classify profile         │
├──────────────────────────────────────────┤
│  Action: classify_profile(metrics)       │
│  Rule-based logic:                       │
│    data_tab_usage > 70% → +1 Rational    │
│    consensus_alignment > 60% → +1 Rational │
│    beat_villain → +1 Rational            │
│    → Total: Rational                     │
│  Returns: "Rational"                     │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Insight Agent: Generate coaching        │
├──────────────────────────────────────────┤
│  Action: generate_coaching(logs, profile="Rational") │
│  Uses Gemini to analyze patterns and create tips: │
│  Returns: [                              │
│    "In downgrade scenarios, 'Sell Half' outperformed 'Sell All'...", │
│    "You chased NVDA spike—wait for consolidation", │
│    "Hold on mixed signals captured mean-reversion" │
│  ]                                       │
└──────────────────────────────────────────┘
    ↓
Return final report: profile + coaching + metrics + decision tracker
```

**Total Time**: 2-3 seconds

---

## Tool Implementations (Key Examples)

### Tool 1: generate_event_description (Event Generator Agent)

```python
from langchain.tools import tool
from google import generativeai as genai

@tool
async def generate_event_description(
    ticker: str,
    event_type: str
) -> str:
    """Generate realistic event scenario using Gemini.
    
    Args:
        ticker: Stock ticker symbol
        event_type: Type of event (EARNINGS_SURPRISE, REGULATORY_NEWS, etc.)
    
    Returns:
        Compelling event description (2-3 sentences)
    """
    
    event_templates = {
        "EARNINGS_SURPRISE": "Create a realistic earnings surprise event",
        "REGULATORY_NEWS": "Create a regulatory news event",
        "ANALYST_ACTION": "Create an analyst upgrade/downgrade event",
        "VOLATILITY_SPIKE": "Create a sudden volatility event",
        "PRODUCT_NEWS": "Create a product launch or recall event"
    }
    
    prompt = f"""{event_templates.get(event_type, 'Create a market event')} for {ticker}.
    
    Include:
    - What happened (be specific with numbers if applicable)
    - Immediate market reaction (pre-market movement, volume)
    - Key details that make this event compelling
    
    Make it realistic and educational. 2-3 sentences max.
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = await model.generate_content_async(prompt)
    
    return response.text.strip()
```

---

### Tool 2: select_ticker_from_portfolio (Event Generator Agent)

```python
import random

@tool
async def select_ticker_from_portfolio(portfolio: str) -> str:
    """Select ticker from portfolio (weighted by position size).
    
    Args:
        portfolio: JSON string of portfolio positions
    
    Returns:
        Selected ticker symbol
    """
    import json
    positions = json.loads(portfolio)
    
    # Weight by allocation size
    tickers = list(positions.keys())
    weights = [positions[t] for t in tickers]
    total = sum(weights)
    normalized_weights = [w/total for w in weights]
    
    # Weighted random selection
    selected = random.choices(tickers, weights=normalized_weights, k=1)[0]
    
    return selected
```

---

### Tool 3: fetch_ticker_news (News Agent)

```python
from langchain.tools import tool
from tavily import TavilyClient

@tool
async def fetch_ticker_news(ticker: str, days: int = 3) -> str:
    """Fetch recent headlines for a ticker using Tavily.
    
    Args:
        ticker: Stock ticker symbol
        days: Days back to search
    
    Returns:
        JSON string with headlines
    """
    query = f"{ticker} stock news"
    
    results = await tavily.search(
        query=query,
        topic="news",
        days=days,
        max_results=3
    )
    
    headlines = [
        {"title": r['title'], "source": r.get('domain', 'Unknown')}
        for r in results.get('results', [])
    ]
    
    return json.dumps(headlines)
```

---

### Tool 4: sample_historical_window (Price Agent)

```python
@tool
async def sample_historical_window(
    ticker: str,
    event_type: str,
    horizon: int
) -> str:
    """Sample a matching historical case and return price path.
    
    Args:
        ticker: Stock ticker
        event_type: Type of event (EARNINGS_BEAT, etc.)
        horizon: Number of days to look ahead
    
    Returns:
        JSON with historical case details
    """
    # Check pre-seeded library first
    case = await db.query("""
        SELECT * FROM historical_cases
        WHERE ticker = $1 AND event_type = $2
        ORDER BY RANDOM()
        LIMIT 1
    """, ticker, event_type)
    
    if not case:
        # Fallback: Use sector proxy
        sector = get_sector(ticker)
        case = await db.query("""
            SELECT * FROM historical_cases
            WHERE ticker IN (SELECT ticker FROM tickers WHERE sector = $1)
            AND event_type = $2
            ORDER BY RANDOM()
            LIMIT 1
        """, sector, event_type)
    
    if not case:
        # Fallback: Generic same event type
        case = await db.query("""
            SELECT * FROM historical_cases
            WHERE event_type = $1
            ORDER BY RANDOM()
            LIMIT 1
        """, event_type)
    
    return json.dumps({
        "date": case['date'],
        "day0_price": case['day0_price'],
        "day_h_price": case['day_h_price'],
        "return_pct": case['return_pct']
    })
```

---

### Tool 5: generate_hot_take (Villain Agent)

```python
@tool
async def generate_hot_take(
    event_description: str,
    stance: str,
    bias_type: str
) -> str:
    """Generate Villain's biased hot take.
    
    Args:
        event_description: The market event
        stance: Desired stance (Bullish / Bearish)
        bias_type: Cognitive bias to use
    
    Returns:
        Hot take text
    """
    prompt = f"""You are a trash-talking Villain in a trading game.
    
    Event: {event_description}
    Your stance: {stance}
    Cognitive bias to use: {bias_type}
    
    Generate a bold, emotionally charged hot take (1-2 sentences).
    Be confident and provocative. Often be WRONG to mislead the player.
    Use the {bias_type} bias explicitly.
    """
    
    response = await gemini.generate_content_async(prompt)
    return response.text.strip()
```

---

### Tool 6: classify_profile (Insight Agent)

```python
@tool
async def classify_profile(metrics: str) -> str:
    """Classify player's behavioral profile.
    
    Args:
        metrics: JSON string with behavior metrics
    
    Returns:
        Profile classification
    """
    m = json.loads(metrics)
    
    # Rule-based classification (transparent, explainable)
    rational_score = 0
    emotional_score = 0
    conservative_score = 0
    
    if m['data_tab_usage'] > 0.7:
        rational_score += 1
    if m['consensus_alignment'] > 0.6:
        rational_score += 1
    if m['beat_villain']:
        rational_score += 1
    
    if m['followed_villain_high_contradiction'] > 0.4:
        emotional_score += 2
    if m['panic_sells'] > 2:
        emotional_score += 2
    if m['chased_spikes'] > 2:
        emotional_score += 1
    
    if m['small_sizes'] and m['frequent_trimming']:
        conservative_score += 2
    if m['low_drawdowns']:
        conservative_score += 1
    
    # Determine profile
    if rational_score >= 2 and emotional_score == 0:
        return "Rational"
    elif emotional_score >= 2:
        return "Emotional"
    elif conservative_score >= 2:
        return "Conservative"
    else:
        return "Balanced"
```

---

## State Management

### Shared State Across Agents

```python
from typing import TypedDict, List
from langchain_core.messages import BaseMessage

class GameState(TypedDict):
    # Game context
    game_id: str
    portfolio_id: str
    current_round: int
    
    # Multi-agent communication
    messages: List[BaseMessage]
    
    # Generated content
    portfolio: dict           # From Portfolio Agent
    event: dict               # From Event Generator Agent
    selected_ticker: str      # From Event Generator Agent
    headlines: List[dict]     # From News Agent
    consensus: str            # From News Agent
    contradiction_score: float  # From News Agent
    villain_take: dict        # From Villain Agent
    fundamentals: dict        # From Portfolio Agent
    price_data: dict          # From Price Agent
    historical_outcomes: dict  # From Price Agent
    neutral_tip: str          # From Insight Agent
    
    # Player input
    player_decision: dict     # Action, time, data_tab_opened
    
    # Outcome
    outcome: dict             # P/L, explanation
    behavior_flags: dict      # From Insight Agent
    
    # Final report
    final_report: dict        # From Insight Agent
```

---

## Supervisor Pattern (Orchestrator)

```python
from langgraph.graph import StateGraph, END

def create_game_graph():
    """Build multi-agent workflow"""
    
    workflow = StateGraph(GameState)
    
    # Add agent nodes
    workflow.add_node("event_generator", event_generator_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("news", news_node)
    workflow.add_node("price", price_node)
    workflow.add_node("villain", villain_node)
    workflow.add_node("insight", insight_node)
    workflow.add_node("supervisor", supervisor_node)
    
    # Supervisor routes based on task
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state['task'],
        {
            "round_start": "event_generator",
            "decision_evaluation": "price",
            "final_report": "insight",
            "end": END
        }
    )
    
    # Round start flow
    workflow.add_edge("event_generator", "villain")
    workflow.add_edge("villain", "news")
    workflow.add_edge("news", "price")
    workflow.add_edge("price", "portfolio")
    workflow.add_edge("portfolio", "insight")
    workflow.add_edge("insight", "supervisor")
    
    # Decision evaluation flow
    workflow.add_edge("price", "portfolio")
    workflow.add_edge("portfolio", "insight")
    workflow.add_edge("insight", "supervisor")
    
    workflow.set_entry_point("supervisor")
    
    return workflow.compile()

game_graph = create_game_graph()
```

---

## Performance Metrics

| Operation | Agents Involved | Tool Calls | Latency |
|-----------|----------------|------------|---------|
| Portfolio creation | Portfolio | 3-6 tools | 1-2s |
| Round start (event + Villain + data) | Event Generator + Villain + News + Price + Portfolio + Insight | 12-16 tools | 4-5s |
| Decision evaluation | Price + Portfolio + Insight | 4-6 tools | 1-2s |
| Final report | Insight | 3-4 tools | 2-3s |

---

## Why This Multi-Agent Design?

✅ **Separation of Concerns**: Each agent has a clear, single responsibility
✅ **Dynamic Event Generation**: Event Generator creates scenarios tied to player's holdings
✅ **Portfolio Management**: Portfolio Agent handles all position logic
✅ **Evidence-Based Data**: News + Price Agents provide factual data
✅ **Behavioral Pressure**: Villain Agent creates emotional decisions vs rational ones
✅ **Historical Realism**: Price Agent ensures outcomes are based on real price paths
✅ **Transparent Coaching**: Insight Agent provides explainable behavioral profiling
✅ **Scalability**: Easy to add new agents or tools
✅ **Demo-Friendly**: Can visualize agent flow with LangSmith
