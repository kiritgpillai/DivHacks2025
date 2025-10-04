# Tech Stack - Market Mayhem

## Project Overview

**Market Mayhem** is a portfolio-building, news-driven investing game where players compete against a trash-talking Villain AI. Players start with $1,000,000, build a portfolio of 3-6 stocks, and navigate 5-7 rounds of real market events while using a Data tab to make informed decisions.

---

## Frontend (Vercel - FREE)

### Next.js 14+ App Router
- **Framework**: Next.js 14/15 with TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui (for portfolio UI, data tab, decision tracker)
- **Charts**: Recharts or Chart.js (for price sparklines, performance graphs)
- **Animations**: Framer Motion (P/L animations, round transitions)
- **State**: Zustand (portfolio state, game state) + WebSocket (real-time events)
- **Data Fetching**: Server Actions + TanStack Query
- **Real-time**: WebSocket connection for game events

**Key Features**:
- **Portfolio Builder**: Stock selection interface with allocation controls
- **Data Tab**: Tabbed interface showing headlines, fundamentals, price charts, historical outcomes
- **Decision Tracker**: Expandable rows showing every decision with full context
- **Villain Chat**: Speech bubble interface for Villain takes
- **Behavioral Report**: Final summary with profile and coaching

**Key Files**:
```
/app
  /portfolio/page.tsx          # Portfolio setup (Round 0)
  /game/[id]/page.tsx           # Main game interface
  /game/[id]/summary/page.tsx   # Final report
  /actions.ts                   # Server Actions
/components
  /portfolio
    /StockSelector.tsx          # Pick 3-6 stocks
    /AllocationControls.tsx     # Allocate $1M
  /game
    /EventCard.tsx              # Event scenario display
    /VillainBubble.tsx          # Villain's hot take
    /DataTab.tsx                # Headlines + Fundamentals + Historical
      /HeadlinesPanel.tsx       # News with stance tags
      /FundamentalsPanel.tsx    # P/E, beta, volatility
      /PricePanel.tsx           # Sparklines, recent behavior
      /HistoricalPanel.tsx      # Past outcomes for similar events
    /DecisionButtons.tsx        # Sell All / Sell Half / Hold / Buy
  /summary
    /BehavioralProfile.tsx      # Rational/Emotional/Conservative
    /CoachingCards.tsx          # Personalized tips
    /DecisionTracker.tsx        # Full round-by-round log
```

---

## Backend (Render.com - FREE)

### FastAPI (Python 3.11)
- **Framework**: FastAPI
- **ASGI**: Uvicorn
- **Validation**: Pydantic v2
- **Async**: asyncio, httpx
- **WebSocket**: FastAPI WebSocket support

**Key Libraries**:
```python
fastapi==0.116.1
uvicorn==0.32.1
pydantic==2.10.6
python-dotenv==1.0.0
websockets==12.0
pandas==2.2.0  # For price history processing
```

---

## AI/Agent Stack

### Multi-Agent System with LangGraph
- **Orchestration**: LangGraph 0.6.7
- **Agent Type**: ReAct agents with tool-calling
- **LLM**: Gemini Pro (Google AI) - FREE tier
- **Search**: Tavily API (1000 req/month free)
- **Observability**: Opik 1.0.0 (Comet ML) - FREE tier
- **Visualization**: LangSmith (for agent graph visualization)

**6 Specialized ReAct Agents**:

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **Event Generator Agent** | Create realistic market event scenarios tied to portfolio holdings | `select_ticker_from_portfolio`, `determine_event_type`, `generate_event_description`, `set_event_horizon`, `validate_event_realism` |
| **Portfolio Agent** | Initialize portfolio, validate holdings, calculate P/L | `validate_ticker`, `get_current_price`, `calculate_position_value`, `check_allocation` |
| **News Agent** | Fetch headlines, assign stance (Bull/Bear/Neutral), compute consensus & contradiction score | `fetch_ticker_news`, `assign_headline_stance`, `calculate_consensus`, `compute_contradiction_vs_villain` |
| **Price Agent** | Provide price snapshots, run historical backtest sampler, return matched price paths | `get_price_snapshot`, `sample_historical_window`, `apply_decision_to_path`, `calculate_pl` |
| **Villain Agent** | Generate biased hot takes, label cognitive biases (Fear/FOMO/Authority), create emotional pressure | `generate_hot_take`, `label_cognitive_bias`, `create_villain_persona` |
| **Insight Agent** | Write neutral tips during rounds, aggregate decisions into behavioral profile, generate coaching | `write_neutral_tip`, `aggregate_behavior`, `generate_coaching`, `identify_patterns` |

**Total Tools**: ~25 custom tools across 6 agents

**What Makes This Impressive**:
✅ **Dynamic event generation** tied to player's portfolio holdings
✅ **Portfolio management** with real stock universe
✅ **News stance detection** (Bull/Bear/Neutral tags)
✅ **Historical outcome replay** (matched price windows, not random)
✅ **Villain AI with cognitive bias labeling**
✅ **Behavioral profiling** (Rational/Emotional/Conservative)
✅ **Full observability** with Opik + LangSmith visualization

```python
langgraph==0.6.7
langchain-core==0.3.28
langchain-google-genai==2.0.10
langchain-community==0.3.18
google-generativeai==0.8.3
tavily-python==0.5.0
opik==1.0.0
```

---

## Database & Cache

### Supabase (FREE: 500MB)
- **Database**: PostgreSQL
- **Real-time**: WebSocket subscriptions (for live updates)
- **Client**: asyncpg
- **Tables**: 
  - `players` (id, username, games_played)
  - `portfolios` (id, player_id, tickers, allocations, risk_profile)
  - `game_sessions` (id, portfolio_id, status, final_value)
  - `game_rounds` (id, session_id, ticker, event_type, villain_stance, player_decision, outcome, pl)
  - `decision_tracker` (id, round_id, opened_data_tab, headlines_shown, consensus, contradiction_score, behavior_flags)
  - `historical_cases` (id, ticker, event_type, date, day0_price, day_h_price)

```python
asyncpg==0.29.0
sqlalchemy==2.0.27
```

### Upstash Redis (FREE: 10K commands/day)
- **Cache**: Ticker prices, news headlines, historical case library
- **Session**: Active game sessions, portfolio state
- **TTL**: 5min for prices, 1hr for news, 24hr for historical cases

```python
redis==5.0.1
```

---

## Data Sources

### Price Data
- **Source**: yfinance (free, historical data) OR Alpha Vantage API (free tier)
- **Usage**: Fetch current prices, historical OHLC data for backtest sampler
- **Cache Strategy**: Cache prices for 5 minutes, historical data for 24 hours

```python
yfinance==0.2.40  # Recommended for hackathon (easy, free, no API key)
# OR
# alpha-vantage==2.3.1  # If you prefer API-based approach
```

### News Data
- **Source**: Tavily API (1000 requests/month free)
- **Usage**: Fetch recent headlines per ticker, extract titles + snippets
- **Stance Detection**: Use Gemini to classify Bull/Bear/Neutral
- **Cache Strategy**: Cache headlines for 1 hour

### Historical Event Library
- **Source**: Pre-seeded JSON file OR dynamically built from yfinance
- **Structure**: 
  ```json
  {
    "ticker": "TSLA",
    "event_type": "earnings_beat",
    "date": "2023-10-18",
    "horizon_days": 3,
    "day0_price": 242.50,
    "day_h_price": 251.30,
    "return_pct": 3.63
  }
  ```
- **Usage**: Price Agent samples matching cases for outcome replay

---

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://market-mayhem-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://market-mayhem-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
```

### Backend (.env)
```bash
# AI
GOOGLE_API_KEY=AIzaSy-xxx
TAVILY_API_KEY=tvly-xxx

# Database
DATABASE_URL=postgresql://xxx  # From Supabase
REDIS_URL=redis://xxx           # From Upstash

# Observability
OPIK_API_KEY=xxx  # From comet.com
LANGSMITH_API_KEY=xxx  # Optional, for visualization
LANGSMITH_PROJECT=market-mayhem

# Data
ALPHA_VANTAGE_API_KEY=xxx  # Optional, if using Alpha Vantage

# Config
ALLOWED_ORIGINS=https://market-mayhem.vercel.app
TICKER_UNIVERSE=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,JPM,V,WMT  # Top 10 for demo
```

---

## Free Tier Limits

| Service | Limit | Usage Strategy | Est. Capacity |
|---------|-------|----------------|---------------|
| **Vercel** | Unlimited | Frontend hosting | ∞ users |
| **Render** | 750h/mo | Backend (auto-sleep OK) | ~300 games/mo |
| **Supabase** | 500MB | ~20MB for demo | ~5000 games |
| **Upstash Redis** | 10K/day | Cache everything | ~100 concurrent |
| **Tavily** | 1000/mo | Cache 1hr, ~6-10 req/game | ~100-150 games/mo |
| **Google AI (Gemini)** | Free tier | 15 req/min, 1M tokens/day | ~500 games/day |
| **yfinance** | Unlimited | Free, rate-limited | ~1000 req/day safe |

**Total Cost**: $0 (assuming free tiers)

**Bottleneck**: Tavily (1000/mo) limits to ~100-150 games with news fetching

---

## LangSmith Integration (Optional but Recommended)

### Visualization Setup
```python
# backend/infrastructure/agents/__init__.py
import os

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "market-mayhem"
```

**Benefits**:
- 🔍 **Visualize agent graph** - See Portfolio → News → Villain → Player Decision → Price → Insight flow
- 📊 **Trace execution** - See which agents are called when
- 🐛 **Debug agent reasoning** - Inspect why Villain generated specific takes
- ⚡ **Monitor performance** - Identify slow agents or tools

---

## Development Setup

```bash
# Install pnpm (if not already installed)
npm install -g pnpm

# Frontend
cd frontend
pnpm install
pnpm dev  # http://localhost:3000

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000  # http://localhost:8000
```

---

## WebSocket Architecture

### Connection Flow
```
Player starts game → Connect WebSocket
  → Server sends: {"type": "round_start", "round": 1, "event": {...}, "villain_take": {...}}
  → Player opens Data Tab → Request data
  → Server sends: {"type": "data_update", "headlines": [...], "fundamentals": {...}, "historical": [...]}
  → Player makes decision → Send: {"type": "decision", "action": "SELL_HALF", "opened_data_tab": true}
  → Server sends: {"type": "outcome", "pl": {...}, "new_portfolio_value": 1050000}
  → Repeat for 5-7 rounds
  → Server sends: {"type": "game_complete", "final_report": {...}}
```

---

## Database Schema

```sql
-- portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    player_id UUID REFERENCES players(id),
    risk_profile TEXT NOT NULL,  -- Risk-On / Balanced / Risk-Off
    tickers TEXT[] NOT NULL,     -- ['AAPL', 'TSLA', 'MSFT']
    allocations JSONB NOT NULL,  -- {"AAPL": 300000, "TSLA": 400000, ...}
    initial_value DECIMAL NOT NULL DEFAULT 1000000,
    created_at TIMESTAMP DEFAULT NOW()
);

-- game_sessions
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY,
    portfolio_id UUID REFERENCES portfolios(id),
    current_round INT DEFAULT 0,
    portfolio_value DECIMAL NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

-- game_rounds
CREATE TABLE game_rounds (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id),
    round_number INT NOT NULL,
    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    villain_stance TEXT NOT NULL,
    villain_bias TEXT NOT NULL,  -- Fear / FOMO / Authority
    player_decision TEXT NOT NULL,
    opened_data_tab BOOLEAN NOT NULL,
    decision_time FLOAT NOT NULL,
    historical_case_date DATE,
    entry_price DECIMAL,
    exit_price DECIMAL,
    pl_dollars DECIMAL,
    pl_percent DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- decision_tracker (detailed logs)
CREATE TABLE decision_tracker (
    id UUID PRIMARY KEY,
    round_id UUID REFERENCES game_rounds(id),
    headlines_shown JSONB NOT NULL,  -- [{"title": "...", "stance": "Bull"}]
    consensus TEXT NOT NULL,         -- "Two-thirds Bull"
    contradiction_score DECIMAL NOT NULL,  -- 0.67 (67% disagree with Villain)
    fundamentals_shown JSONB,
    historical_outcomes_shown JSONB,
    behavior_flags JSONB,  -- {"panic_sell": false, "chased_spike": false}
    created_at TIMESTAMP DEFAULT NOW()
);

-- historical_cases (pre-seeded library)
CREATE TABLE historical_cases (
    id UUID PRIMARY KEY,
    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    date DATE NOT NULL,
    horizon_days INT NOT NULL,
    day0_price DECIMAL NOT NULL,
    day_h_price DECIMAL NOT NULL,
    return_pct DECIMAL NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

```
# Portfolio
POST   /portfolio/create        # Create portfolio (Round 0)
GET    /portfolio/{id}           # Get portfolio state
POST   /portfolio/{id}/validate  # Validate tickers

# Game
POST   /game/start               # Start game with portfolio
GET    /game/{id}                # Get game state
WS     /game/{id}/ws             # WebSocket for rounds

# Round
POST   /game/{id}/decision       # Submit decision
GET    /game/{id}/data           # Get Data tab content
GET    /game/{id}/villain        # Get Villain take

# Summary
GET    /game/{id}/summary        # Final report
GET    /game/{id}/tracker        # Decision tracker

# Admin
POST   /admin/seed-historical    # Seed historical case library
```

---

## Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Portfolio creation | <2s | Validate tickers, fetch prices |
| Generate event + Villain | <3s | AI streaming + cached news |
| Fetch Data tab content | <1s | Parallel headlines + fundamentals + historical |
| Decision evaluation | <2s | Sample historical case, calculate P/L |
| Final report generation | <3s | Aggregate decisions, profile + coaching |

---

## Why These Choices?

| Choice | Alternative | Reason |
|--------|------------|--------|
| Gemini | GPT-4 | Free tier, good quality for stance + coaching |
| Tavily | NewsAPI + scraping | Unified API, free tier, fast |
| yfinance | Alpha Vantage | No API key, easier for hackathon |
| Supabase | Vercel Postgres | Real-time subscriptions, larger free tier |
| LangSmith | Custom viz | Official LangGraph visualization |

---

## Cold Start Mitigation (Render)

For hackathon: **Accept cold starts**, show friendly loading screen:
- "Waking up the Villain AI..."
- "Loading your portfolio..."
- "Fetching market data..."

---

## Monitoring (Opik + LangSmith)

```python
# Log key metrics
logger.info(f"Portfolio created: {portfolio_id}, tickers: {tickers}")
logger.info(f"Villain generated: {villain_take}, bias: {bias_type}")
logger.info(f"Decision made: {decision}, data_tab_opened: {opened}, P/L: {pl}")

# Opik tracking
opik.log_metric("contradiction_score", contradiction_score)
opik.log_metric("behavioral_profile", profile)

# LangSmith tracing (automatic if env vars set)
# View agent graph at: https://smith.langchain.com
```

---

**Stack optimized for: Multi-agent AI, portfolio simulation, historical replay, and behavioral coaching—all on free tiers.** 🚀
