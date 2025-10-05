# Software Architecture - Market Mayhem

## System Overview

**Market Mayhem** is an interactive portfolio-building game that turns market events into a behavioral training ground. Players build a $1M portfolio, navigate real-world-style events while a trash-talking Villain AI tries to mislead them, and learn through a Data tab that provides evidence-based decision support.

**Core Innovation**: Historical outcome replay using matched price windows (not random) + Villain AI with cognitive bias labeling + behavioral profiling.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│   Vercel (Next.js Frontend)                     │
│   - Portfolio builder (Round 0)                 │
│   - Event UI + Villain bubble                   │
│   - Data tab (headlines, fundamentals,          │
│                historical outcomes)              │
│   - Decision tracker + final report             │
└──────────────┬──────────────────────────────────┘
               │ WebSocket + HTTPS
               ▼
┌─────────────────────────────────────────────────┐
│   Render (FastAPI Backend)                      │
│   - LangGraph multi-agent engine                │
│   - 5 Agents: Portfolio/News/Price/Villain/     │
│               Insight                            │
│   - Gemini AI (stance, coaching, Villain takes) │
│   - Tavily (headline fetching)                  │
│   - yfinance (price data, historical windows)   │
└──────────────┬──────────────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌───────────┐    ┌─────────────┐
│ Supabase  │    │Upstash Redis│
│ Postgres  │    │   (Cache)   │
│- Portfolio│    │- Prices     │
│- Sessions │    │- Headlines  │
│- Rounds   │    │- Historical │
│- Tracker  │    └─────────────┘
└───────────┘
```

---

## Bounded Contexts

### 1. Portfolio Context
**Responsibility**: Manage player portfolio, positions, and valuation

**Entities**: 
- `Portfolio` - Player's holdings (tickers, allocations, risk profile)
- `Position` - Single stock holding (ticker, shares, entry price, current value)

**Value Objects**: 
- `RiskProfile` (Risk-On / Balanced / Risk-Off)
- `Allocation` (dollars per ticker)

**Key Operations**:
- Initialize portfolio with $1M
- Validate tickers (ensure they exist, can fetch prices)
- Calculate current portfolio value
- Apply decision (Sell All / Sell Half / Hold / Buy)

---

### 2. Event Context
**Responsibility**: Generate realistic market events tied to player's holdings

**Entities**: 
- `MarketEvent` - A scenario tied to one ticker (earnings, regulatory headline, analyst action, hype spike)
- `EventType` - Enumeration (EARNINGS_SURPRISE, REGULATORY_NEWS, ANALYST_UPGRADE, VOLATILITY_SPIKE, etc.)

**Value Objects**: 
- `Horizon` - Time window for outcome (e.g., 3 trading days)
- `EventStance` - Direction bias (Bullish / Bearish / Neutral / Mixed)

**Key Operations**:
- Select ticker from portfolio (weighted by position size)
- Generate event scenario relevant to ticker
- Return event description, type, and horizon

---

### 3. News Context
**Responsibility**: Fetch, classify, and aggregate headlines for the Data tab

**Entities**: 
- `Headline` - Single news article (title, source, URL, timestamp)
- `HeadlineStance` - Classification (Bull / Bear / Neutral)
- `Consensus` - Aggregated stance across headlines

**Value Objects**: 
- `ContradictionScore` - How much headlines disagree with Villain (0-1)
- `StanceTag` - Color-coded tag (🟢 Bull / 🔴 Bear / ⚪ Neutral)

**Key Operations**:
- Fetch 2-3 recent headlines per ticker (via Tavily)
- Assign stance to each headline (via Gemini)
- Compute consensus (e.g., "Two-thirds Bull")
- Calculate contradiction score vs Villain stance

---

### 4. Villain Context
**Responsibility**: Generate biased, emotionally charged hot takes to induce fear/FOMO

**Entities**: 
- `VillainTake` - A bold, biased statement about the event
- `CognitiveBias` - Labeled bias (Fear Appeal / Overconfidence / Authority Lure / Recency Bias)

**Value Objects**: 
- `VillainPersona` - Consistent character (trash-talking, confident, often wrong)
- `EmotionalTone` - Intensity of pressure (Aggressive / Moderate / Subtle)

**Key Operations**:
- Analyze event
- Generate hot take that contradicts rational analysis (often)
- Label dominant cognitive bias
- Return take + bias label

---

### 5. Historical Outcome Context
**Responsibility**: Replay realistic outcomes using matched historical price windows

**Entities**: 
- `HistoricalCase` - A past event instance (ticker, event type, date, price path)
- `PricePath` - Day 0 to Day H prices
- `Outcome` - Result of applying decision to price path

**Value Objects**: 
- `DecisionType` (Sell All / Sell Half / Hold / Buy)
- `PLImpact` - P/L in dollars and percentage

**Key Operations**:
- Sample historical case matching (ticker OR sector proxy, event type, horizon)
- Extract price path (day 0 → day H)
- Apply player decision to path:
  - **Sell All**: Exit at day 0, no further impact
  - **Sell Half**: Realize half at day 0, other half rides to day H
  - **Hold**: Full position rides to day H
  - **Buy**: Add to position (small increment, bounded by risk profile), rides to day H
- Calculate P/L, update portfolio value

---

### 6. Decision Tracking Context
**Responsibility**: Log every decision with full context for transparency and coaching

**Entities**: 
- `DecisionLog` - Complete record of a single round decision
- `BehaviorFlag` - Pattern detected (panic_sell, chased_spike, ignored_consensus)

**Value Objects**: 
- `DataTabUsage` - Whether player opened Data tab before deciding
- `TimingMetric` - Decision speed, deliberation time

**Key Operations**:
- Log round: ticker, event, Villain stance, headlines, consensus, contradiction score
- Record decision: action, data tab opened, time taken
- Match historical case used
- Calculate P/L impact
- Flag behaviors (panic on 3 down days, FOMO on up spike)

---

### 7. Behavioral Profiling Context
**Responsibility**: Aggregate decisions into behavioral profile and coaching

**Entities**: 
- `BehavioralProfile` - Classification (Rational / Emotional / Conservative)
- `CoachingTip` - Personalized recommendation based on patterns

**Value Objects**: 
- `ProfileMetrics` - Data tab usage %, alignment with consensus, Villain resistance
- `TradeQuality` - Best/worst trades, lessons learned

**Key Operations**:
- Aggregate all decision logs
- Calculate metrics (data tab usage, consensus alignment, panic/FOMO counts)
- Classify profile:
  - **Rational**: High data usage, high consensus alignment, beat Villain
  - **Emotional**: Low data usage, followed Villain under high contradiction, panic/FOMO
  - **Conservative**: Small sizes, frequent trimming, low drawdowns
- Generate 2-4 coaching tips (e.g., "Consider 'Sell Half' instead of 'Sell All' in downgrade scenarios")

---

## Layer Structure

```
/market-mayhem
  /frontend (Next.js - Vercel)
    /app
      /portfolio/page.tsx       # Round 0: Portfolio setup
      /game/[id]/page.tsx       # Rounds 1-7: Event + Data tab
      /game/[id]/summary/page.tsx  # Final report
    /components
      /portfolio
        /StockSelector.tsx      # Pick 3-6 tickers
        /AllocationControls.tsx # Allocate $1M
      /game
        /EventCard.tsx          # Event display
        /VillainBubble.tsx      # Villain hot take + bias label
        /DataTab.tsx            # Tabbed interface
          /HeadlinesPanel.tsx   # 2-3 headlines with stance
          /FundamentalsPanel.tsx  # P/E, beta, volatility
          /PricePanel.tsx       # Sparkline, recent behavior
          /HistoricalPanel.tsx  # Past outcomes (Sell All vs Hold)
        /DecisionButtons.tsx    # Sell All / Sell Half / Hold / Buy
      /summary
        /BehavioralProfile.tsx  # Rational/Emotional/Conservative
        /CoachingCards.tsx      # Personalized tips
        /DecisionTracker.tsx    # Expandable round-by-round log
  
  /backend (FastAPI - Render)
    /adapters
      /http                     # REST controllers
      /websocket                # Game events
    /application                # Use cases
      /portfolio
        - CreatePortfolioHandler
        - ValidateTickersHandler
        - CalculateValueHandler
      /game
        - StartGameHandler
        - AdvanceRoundHandler
        - SubmitDecisionHandler
      /data_tab
        - FetchDataTabContentHandler
      /summary
        - GenerateFinalReportHandler
    /domain                     # Pure business logic
      /portfolio
        - Portfolio
        - Position
        - RiskProfile
      /event
        - MarketEvent
        - EventType
      /news
        - Headline
        - HeadlineStance
        - Consensus
      /villain
        - VillainTake
        - CognitiveBias
      /decision
        - DecisionLog
        - BehaviorFlag
      /profile
        - BehavioralProfile
        - CoachingTip
    /infrastructure
      /agents                   # LangGraph agents
        - PortfolioAgent
        - NewsAgent
        - PriceAgent
        - VillainAgent
        - InsightAgent
      /tavily                   # News fetching
      /yfinance_adapter         # Price data + historical windows
      /db                       # Supabase
      /cache                    # Redis
```

---

## Dependency Rules

✅ **Allowed**:
- `adapters → application → domain`
- `infrastructure → domain` (via interfaces)
- `application → domain`

❌ **Forbidden**:
- `domain → infrastructure`
- `domain → application`
- `domain → external libraries`

---

## Data Flow

### 1. Portfolio Setup (Round 0)

```
Player visits /portfolio
  → Select 3-6 tickers (e.g., AAPL, TSLA, MSFT, NVDA)
  → Allocate $1M (e.g., $300k AAPL, $400k TSLA, $300k MSFT)
  → Choose risk profile (Risk-On / Balanced / Risk-Off)
  → POST /portfolio/create
    → CreatePortfolioHandler
      → Portfolio Agent: validate tickers, fetch current prices, create Portfolio entity
  → Save to Supabase
  → Return portfolio_id
  → Redirect to /game/{id}
```

### 2. Round Start (Event Generation)

```
Backend selects ticker from portfolio (weighted by position size)
  → StartRoundHandler
    → Event Agent: generate event tied to ticker (earnings, regulatory, etc.)
    → News Agent: fetch 2-3 recent headlines for ticker
    → Villain Agent: generate biased hot take + label cognitive bias
  → Push to client (WebSocket):
    {
      "type": "round_start",
      "round": 1,
      "ticker": "TSLA",
      "event": {
        "description": "Tesla reports earnings beat of 15% vs expectations. Stock up 6% pre-market.",
        "type": "EARNINGS_SURPRISE",
        "horizon": 3
      },
      "villain": {
        "take": "This is clearly a pump! Smart money is selling into the hype. I'm dumping ALL my shares.",
        "bias": "Fear Appeal"
      }
    }
  → Client renders EventCard + VillainBubble
```

### 3. Player Opens Data Tab

```
Player clicks "Data" tab
  → Client requests: GET /game/{id}/data?ticker=TSLA
    → FetchDataTabContentHandler
      → News Agent: return headlines + stance tags + consensus + contradiction score
      → Portfolio Agent: return fundamentals (P/E, beta, 30-day vol)
      → Price Agent: return sparkline, recent behavior (3 down closes, gap up, etc.)
      → Price Agent: return historical outcomes (Sell All vs Sell Half vs Hold median returns)
      → Insight Agent: generate one-line neutral tip
  → Response:
    {
      "headlines": [
        {"title": "Tesla beats Q4 earnings", "stance": "Bull", "source": "CNBC"},
        {"title": "Analysts raise TSLA targets", "stance": "Bull", "source": "Reuters"}
      ],
      "consensus": "Two-thirds Bull",
      "contradiction_score": 0.80,  // 80% of headlines disagree with Villain's bearish take
      "fundamentals": {
        "pe_ratio": 45.2,
        "yoy_revenue_growth": 0.18,
        "beta": 1.85,
        "volatility_30d": 0.42
      },
      "price_behavior": {
        "sparkline_5d": [240, 238, 236, 242, 251],
        "pattern": "gap_up_after_down_trend"
      },
      "historical_outcomes": {
        "similar_cases": 12,
        "sell_all": {"median_return": -0.03, "explanation": "Exited before typical 3-7% post-earnings rise"},
        "sell_half": {"median_return": 0.02, "explanation": "Captured partial upside, reduced risk"},
        "hold": {"median_return": 0.05, "explanation": "Full exposure to typical earnings beat rally"}
      },
      "neutral_tip": "Earnings gaps with high beta and rising vol often mean-revert within 3 days—consider trimming instead of exiting fully."
    }
  → Client renders DataTab with all panels
```

### 4. Player Makes Decision

```
Player clicks "SELL HALF" after 18.5 seconds
  → Client sends (WebSocket):
    {
      "type": "decision",
      "action": "SELL_HALF",
      "opened_data_tab": true,
      "decision_time": 18.5
    }
  → SubmitDecisionHandler
    → Price Agent: sample historical case matching (TSLA OR tech sector, EARNINGS_SURPRISE, horizon=3)
    → Price Agent: extract price path (e.g., day 0: 251, day 1: 253, day 2: 256, day 3: 258)
    → Price Agent: apply SELL_HALF decision:
      - Realize half at day 0 (251): +$0 P/L on exited half
      - Remaining half rides to day 3 (258): +2.79% P/L
      - Weighted P/L: +1.39% on original position
    → Calculate dollar P/L (e.g., +$5,560 on $400k position)
    → Update portfolio value: $1,000,000 → $1,005,560
    → Log decision to decision_tracker table
    → Flag behavior: none (rational, used data tab, aligned with consensus)
  → Push outcome (WebSocket):
    {
      "type": "outcome",
      "pl_dollars": 5560,
      "pl_percent": 1.39,
      "new_portfolio_value": 1005560,
      "explanation": "Mixed headlines; holding captured a median rebound common after non-actionable probes."
    }
  → Client renders P/L animation
```

### 5. Repeat for 3 Rounds

Each round:
- Select different ticker from portfolio
- Generate new event + Villain take
- Player uses Data tab + makes decision
- Log to decision_tracker
- Update portfolio value

### 6. Final Summary

```
After final round:
  → GenerateFinalReportHandler
    → Insight Agent: aggregate all decision logs
    → Calculate metrics:
      - Data tab usage: 2/3 rounds (67%)
      - Consensus alignment: 5/7 decisions (71%)
      - Villain resistance: Followed Villain 1/7 times under high contradiction (14%)
      - Panic sells: 0
      - Chased spikes: 1
    → Classify profile: **Rational** (high data usage, high consensus alignment, beat Villain)
    → Generate coaching:
      - "In downgrade scenarios, your 'Sell All' underperformed 'Sell Half' historically—consider partial de-risking."
      - "You chased one spike (NVDA after 3 up days with high vol)—wait for consolidation."
      - "Your 'Hold' on mixed signals captured mean-reversion—keep that discipline."
    → Identify best/worst trades:
      - Best: MSFT hold after upgrade (+8.2%)
      - Worst: AAPL sell all before rebound (-3.5% opportunity cost)
  → Return final report:
    {
      "final_value": 1087420,
      "absolute_return": 87420,
      "pct_return": 8.74,
      "villain_pnl": -23500,  // Villain's "opposite policy" lost money
      "profile": "Rational",
      "metrics": {...},
      "coaching": [...],
      "best_trade": {...},
      "worst_trade": {...},
      "decision_tracker_url": "/game/{id}/tracker"
    }
  → Client renders BehavioralProfile + CoachingCards + DecisionTracker
```

---

## Key Patterns

### Historical Outcome Replay (Core Innovation)

```python
# domain/historical_outcome/HistoricalSampler.py (interface)
class HistoricalSampler(ABC):
    @abstractmethod
    async def sample_case(
        self, 
        ticker: str,
        event_type: EventType,
        horizon: int
    ) -> HistoricalCase:
        pass

# infrastructure/yfinance_adapter/YFinanceHistoricalSampler.py
class YFinanceHistoricalSampler(HistoricalSampler):
    async def sample_case(
        self, 
        ticker: str,
        event_type: EventType,
        horizon: int
    ) -> HistoricalCase:
        # Find matching past events (from pre-built library OR dynamically)
        matching_cases = self._find_matching_cases(ticker, event_type)
        
        if not matching_cases:
            # Fallback to sector proxy
            sector = self._get_sector(ticker)
            matching_cases = self._find_matching_cases_by_sector(sector, event_type)
        
        # Sample one case
        case = random.choice(matching_cases)
        
        # Fetch price path from case date
        prices = yf.download(ticker, start=case.date, end=case.date + timedelta(days=horizon))
        
        return HistoricalCase(
            ticker=ticker,
            event_type=event_type,
            date=case.date,
            horizon=horizon,
            day0_price=prices.iloc[0]['Close'],
            day_h_price=prices.iloc[-1]['Close'],
            price_path=prices['Close'].tolist()
        )
```

### News Stance Detection

```python
# infrastructure/agents/tools/news_tools.py
@tool
async def assign_headline_stance(headline: str, event_context: str) -> str:
    """Classify headline as Bull/Bear/Neutral using Gemini"""
    
    prompt = f"""Classify this headline as Bull (positive for stock), Bear (negative), or Neutral.
    
    Headline: {headline}
    Event context: {event_context}
    
    Return only one word: Bull, Bear, or Neutral.
    """
    
    response = await gemini.generate_content_async(prompt)
    stance = response.text.strip()
    
    return stance  # Bull | Bear | Neutral

@tool
async def compute_contradiction_vs_villain(
    headlines: List[HeadlineStance],
    villain_stance: str
) -> float:
    """Calculate how much headlines disagree with Villain"""
    
    # Count opposing stances
    opposing_count = sum(
        1 for h in headlines
        if (villain_stance == "Bearish" and h.stance == "Bull") or
           (villain_stance == "Bullish" and h.stance == "Bear")
    )
    
    return opposing_count / len(headlines) if headlines else 0.0
```

### Villain AI with Bias Labeling

```python
# infrastructure/agents/villain_agent.py
@tool
async def generate_villain_take(
    event: MarketEvent,
    true_rational_action: str
) -> VillainTake:
    """Generate biased hot take that often contradicts rational analysis"""
    
    # Choose bias type based on event
    bias_options = ["Fear Appeal", "Overconfidence", "Authority Lure", "Recency Bias"]
    bias = random.choice(bias_options)
    
    # Generate take that uses this bias
    prompt = f"""You are a trash-talking Villain AI in a trading game.
    
    Event: {event.description}
    Rational action: {true_rational_action}
    
    Generate a bold, emotionally charged hot take using the "{bias}" cognitive bias.
    Your take should often be WRONG to mislead the player.
    Keep it under 2 sentences. Be confident and provocative.
    """
    
    response = await gemini.generate_content_async(prompt)
    
    return VillainTake(
        text=response.text.strip(),
        bias=bias,
        stance="Bearish" if "sell" in response.text.lower() else "Bullish"
    )
```

---

## WebSocket Events

```typescript
// Server → Client
{
  "type": "round_start",
  "round": 1,
  "ticker": "AAPL",
  "event": MarketEvent,
  "villain": VillainTake
}

{
  "type": "data_update",  // Response to Data tab request
  "headlines": Headline[],
  "consensus": string,
  "contradiction_score": number,
  "fundamentals": Fundamentals,
  "price_behavior": PriceBehavior,
  "historical_outcomes": HistoricalOutcomes,
  "neutral_tip": string
}

{
  "type": "outcome",
  "pl_dollars": number,
  "pl_percent": number,
  "new_portfolio_value": number,
  "explanation": string
}

{
  "type": "game_complete",
  "final_report": FinalReport
}

// Client → Server
{
  "type": "decision",
  "action": "SELL_ALL" | "SELL_HALF" | "HOLD" | "BUY",
  "opened_data_tab": boolean,
  "decision_time": number
}

{
  "type": "request_data_tab",
  "ticker": string
}
```

---

## Database Schema (Key Tables)

```sql
-- portfolios
id, player_id, risk_profile, tickers[], allocations (JSONB), initial_value, created_at

-- game_sessions
id, portfolio_id, current_round, portfolio_value, status, started_at, ended_at

-- game_rounds
id, session_id, round_number, ticker, event_type, event_description, 
villain_stance, villain_bias, player_decision, opened_data_tab, decision_time,
historical_case_date, entry_price, exit_price, pl_dollars, pl_percent

-- decision_tracker
id, round_id, headlines_shown (JSONB), consensus, contradiction_score,
fundamentals_shown (JSONB), historical_outcomes_shown (JSONB), behavior_flags (JSONB)

-- historical_cases (pre-seeded library)
id, ticker, event_type, date, horizon_days, day0_price, day_h_price, return_pct
```

---

## API Endpoints

```
# Portfolio
POST   /portfolio/create              # Round 0: Create portfolio
GET    /portfolio/{id}                 # Get portfolio state
POST   /portfolio/{id}/validate        # Validate tickers

# Game
POST   /game/start                     # Start game with portfolio
GET    /game/{id}                      # Get current game state
WS     /game/{id}/ws                   # WebSocket for real-time rounds

# Data Tab
GET    /game/{id}/data?ticker={ticker} # Get Data tab content (on-demand)

# Decision
POST   /game/{id}/decision             # Submit decision

# Summary
GET    /game/{id}/summary              # Final report
GET    /game/{id}/tracker              # Decision tracker (CSV/JSON export)

# Admin
POST   /admin/seed-historical          # Seed historical case library
```

---

## Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Portfolio creation | <2s | Validate tickers, fetch prices |
| Event + Villain generation | <3s | AI streaming |
| Data tab fetch | <1s | Parallel headlines + fundamentals + historical |
| Decision evaluation | <2s | Sample historical, calculate P/L |
| Final report | <3s | Aggregate, profile, coaching |

---

## Security (Hackathon Scope)

**Skip**: Full authentication (use simple session IDs)

**Include**: 
- Input validation (Pydantic)
- Rate limiting (prevent spam decisions)
- Environment secrets
- Ticker validation (prevent injection)

---

## Scalability

### Real-time Game Sessions
- **Challenge**: Multiple concurrent games
- **Solution**: Redis pub/sub + per-game WebSocket rooms
- **Limit**: ~100 concurrent players (hackathon scope)

### Historical Case Library
- **Option 1**: Pre-seed 100-200 cases covering top 10 tickers × common event types
- **Option 2**: Dynamically fetch from yfinance on demand (cache for 24hr)
- **Hybrid**: Pre-seed common cases, fallback to dynamic for rare cases

---

## Key Innovations

✅ **Historical Outcome Replay** - No random outcomes, all based on real price paths
✅ **Villain AI with Bias Labeling** - Teaches cognitive biases through gameplay
✅ **Data Tab** - Evidence-based decision support (headlines, fundamentals, historical)
✅ **Decision Tracker** - Full transparency, every decision logged
✅ **Behavioral Profiling** - Rule-based, explainable classification
✅ **Multi-Agent Orchestration** - 5 specialized agents coordinating via LangGraph

---

**Architecture optimized for: Portfolio simulation, historical replay, behavioral coaching, and real-time multi-agent AI—all on free tiers.** 🚀
