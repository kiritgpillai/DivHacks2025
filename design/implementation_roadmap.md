# Implementation Roadmap - Market Mayhem

## Overview

Complete **step-by-step implementation** for Market Mayhem: a portfolio-building, news-driven investing game with historical outcome replay, trash-talking Villain AI, and behavioral coaching.

**Estimated Timeline**: 3-4 days for hackathon MVP

---

## Phase 0: Setup & Environment (1 hour)

### Step 1: Project Structure

```bash
mkdir market-mayhem
cd market-mayhem

# Backend
mkdir -p backend/{domain,application,infrastructure,adapters}
mkdir -p backend/domain/{portfolio,event,news,villain,decision,profile}
mkdir -p backend/application/{portfolio,game,data_tab,summary}
mkdir -p backend/infrastructure/{agents,db,cache,yfinance_adapter,tavily}
mkdir -p backend/adapters/{http,websocket}

# Frontend
pnpm create next-app@latest frontend --typescript --tailwind --app
cd frontend && pnpm add framer-motion zustand recharts
```

### Step 2: Environment Variables

```bash
# backend/.env
GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
OPIK_API_KEY=your_opik_key
LANGSMITH_API_KEY=your_langsmith_key  # Optional
DATABASE_URL=your_supabase_url
REDIS_URL=your_upstash_url
TICKER_UNIVERSE=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,JPM,V,WMT
```

### Step 3: Dependencies

```bash
# backend/requirements.txt
fastapi==0.116.1
uvicorn==0.32.1
pydantic==2.10.6
langgraph==0.6.7
langchain-core==0.3.28
langchain-google-genai==2.0.10
langchain-community==0.3.18
tavily-python==0.5.0
opik==1.0.0
yfinance==0.2.40
asyncpg==0.29.0
redis==5.0.1
websockets==12.0
python-dotenv==1.0.0
google-generativeai==0.8.3
pandas==2.2.0

pip install -r requirements.txt
```

---

## Phase 1: Domain Layer (3 hours)

### Priority: Value Objects → Entities → Aggregates

### Step 1.1: Value Objects

**File**: `backend/domain/portfolio/RiskProfile.py`
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RiskProfile:
    value: str  # Risk-On | Balanced | Risk-Off
    
    @property
    def max_position_size_pct(self) -> float:
        return {
            "Risk-On": 0.50,
            "Balanced": 0.33,
            "Risk-Off": 0.25
        }[self.value]
```

**File**: `backend/domain/news/NewsStance.py`
```python
from enum import Enum

class NewsStance(Enum):
    BULL = "Bull"
    BEAR = "Bear"
    NEUTRAL = "Neutral"
```

**File**: `backend/domain/decision/DecisionType.py`
```python
from enum import Enum

class DecisionType(Enum):
    SELL_ALL = "SELL_ALL"
    SELL_HALF = "SELL_HALF"
    HOLD = "HOLD"
    BUY = "BUY"
```

### Step 1.2: Entities

**File**: `backend/domain/portfolio/Position.py`
```python
class Position:
    def __init__(self, ticker: str, allocation: float, entry_price: float):
        self.ticker = ticker
        self.allocation = allocation
        self.entry_price = entry_price
        self.shares = allocation / entry_price
        self.current_price = entry_price
    
    def calculate_value(self) -> float:
        return self.shares * self.current_price
    
    def calculate_pl(self) -> tuple[float, float]:
        current_value = self.calculate_value()
        pl_dollars = current_value - self.allocation
        pl_percent = pl_dollars / self.allocation
        return (pl_dollars, pl_percent)
```

### Step 1.3: Aggregates

**File**: `backend/domain/portfolio/Portfolio.py`
```python
from typing import List

class Portfolio:
    def __init__(self, id: str, player_id: str, risk_profile: RiskProfile):
        self.id = id
        self.player_id = player_id
        self.risk_profile = risk_profile
        self._positions: List[Position] = []
        self._cash = 1_000_000  # Initial $1M
    
    def add_position(self, ticker: str, allocation: float, entry_price: float):
        if allocation > self._cash:
            raise DomainError(f"Insufficient cash: {self._cash} < {allocation}")
        
        max_pct = self.risk_profile.max_position_size_pct
        if allocation / 1_000_000 > max_pct:
            raise DomainError(f"Position exceeds {max_pct*100}% limit")
        
        position = Position(ticker, allocation, entry_price)
        self._positions.append(position)
        self._cash -= allocation
    
    def calculate_total_value(self) -> float:
        positions_value = sum(p.calculate_value() for p in self._positions)
        return positions_value + self._cash
```

**✅ Checkpoint**: Domain layer complete, zero infrastructure dependencies

---

## Phase 2: Infrastructure - Tools & Adapters (4 hours)

### Step 2.1: yfinance Price Adapter

**File**: `backend/infrastructure/yfinance_adapter/price_fetcher.py`
```python
import yfinance as yf
import pandas as pd

async def get_current_price(ticker: str) -> float:
    """Fetch current price for a ticker"""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    return data['Close'].iloc[-1]

async def get_price_snapshot(ticker: str) -> dict:
    """Get current price + recent OHLC"""
    stock = yf.Ticker(ticker)
    data = stock.history(period="5d")
    
    return {
        "current": data['Close'].iloc[-1],
        "sparkline": data['Close'].tolist(),
        "high_5d": data['High'].max(),
        "low_5d": data['Low'].min()
    }
```

### Step 2.2: Historical Case Sampler

**File**: `backend/infrastructure/yfinance_adapter/historical_sampler.py`
```python
from datetime import datetime, timedelta
import random

async def sample_historical_window(
    ticker: str,
    event_type: str,
    horizon: int
) -> dict:
    """Sample matched historical case and return price path"""
    
    # Check pre-seeded library first
    case = await db.query("""
        SELECT * FROM historical_cases
        WHERE ticker = $1 AND event_type = $2
        ORDER BY RANDOM()
        LIMIT 1
    """, ticker, event_type)
    
    if not case:
        # Fallback: Generate from yfinance (simplified for demo)
        # In production, use pre-seeded library
        stock = yf.Ticker(ticker)
        
        # Get random date from past 2 years
        days_back = random.randint(horizon, 730)
        end_date = datetime.now() - timedelta(days=days_back)
        start_date = end_date - timedelta(days=horizon)
        
        data = stock.history(start=start_date, end=end_date)
        
        if len(data) < horizon:
            raise ValueError("Insufficient historical data")
        
        case = {
            "date": start_date.strftime("%Y-%m-%d"),
            "day0_price": data['Close'].iloc[0],
            "day_h_price": data['Close'].iloc[-1],
            "price_path": data['Close'].tolist()
        }
    
    return case
```

### Step 2.3: Agent Tools

**File**: `backend/infrastructure/agents/tools/news_tools.py`
```python
from langchain.tools import tool
from tavily import TavilyClient
import json

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
async def fetch_ticker_news(ticker: str, days: int = 3) -> str:
    """Fetch recent headlines for a ticker"""
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

@tool
async def assign_headline_stance(headline: str) -> str:
    """Classify headline as Bull/Bear/Neutral using Gemini"""
    from google import generativeai as genai
    
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"Classify this headline as Bull, Bear, or Neutral: {headline}\nReturn only one word."
    
    response = await model.generate_content_async(prompt)
    return response.text.strip()
```

**✅ Checkpoint**: All tools implemented and tested independently

---

## Phase 3: LangGraph Agents (5 hours)

### Step 3.1: Event Generator Agent (1 hour)

**File**: `backend/infrastructure/agents/event_generator_agent.py`
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
import random
import json

@tool
async def select_ticker_from_portfolio(portfolio: str) -> str:
    """Select ticker from portfolio (weighted by position size)"""
    positions = json.loads(portfolio)
    tickers = list(positions.keys())
    weights = [positions[t] for t in tickers]
    total = sum(weights)
    normalized_weights = [w/total for w in weights]
    return random.choices(tickers, weights=normalized_weights, k=1)[0]

@tool
async def determine_event_type(ticker: str, difficulty: str = "INTERMEDIATE") -> str:
    """Determine event type based on difficulty"""
    easy_events = ["ANALYST_ACTION", "PRODUCT_NEWS"]
    medium_events = ["EARNINGS_SURPRISE", "REGULATORY_NEWS"]
    hard_events = ["VOLATILITY_SPIKE", "MACRO_EVENT"]
    
    if difficulty == "BEGINNER":
        return random.choice(easy_events)
    elif difficulty == "INTERMEDIATE":
        return random.choice(medium_events)
    else:
        return random.choice(hard_events)

@tool
async def generate_event_description(ticker: str, event_type: str) -> str:
    """Generate event description using Gemini"""
    from google import generativeai as genai
    model = genai.GenerativeModel('gemini-pro')
    
    templates = {
        "EARNINGS_SURPRISE": f"Create a realistic earnings event for {ticker}",
        "REGULATORY_NEWS": f"Create regulatory news for {ticker}",
        "ANALYST_ACTION": f"Create analyst upgrade/downgrade for {ticker}",
    }
    
    prompt = f"""{templates.get(event_type, 'Create event')} for {ticker}.
    Include: What happened (numbers), market reaction, key details. 2-3 sentences."""
    
    response = await model.generate_content_async(prompt)
    return response.text.strip()

@tool
async def set_event_horizon(event_type: str) -> int:
    """Set event horizon in trading days"""
    horizons = {
        "EARNINGS_SURPRISE": 3,
        "REGULATORY_NEWS": 5,
        "ANALYST_ACTION": 3,
        "VOLATILITY_SPIKE": 2,
        "PRODUCT_NEWS": 4,
        "MACRO_EVENT": 5
    }
    return horizons.get(event_type, 3)

@tool
async def validate_event_realism(ticker: str, event: str) -> dict:
    """Validate event makes sense"""
    return {"valid": True, "confidence": 0.9}

# Create Event Generator Agent
llm = ChatGoogleGenerativeAI(model="gemini-pro")

event_generator_agent = create_react_agent(
    llm,
    tools=[
        select_ticker_from_portfolio,
        determine_event_type,
        generate_event_description,
        set_event_horizon,
        validate_event_realism
    ],
    prompt="""Generate realistic market event scenarios. Select ticker from portfolio, 
    choose event type, create description, set horizon, validate."""
)
```

**Test**:
```bash
python -c "from backend.infrastructure.agents.event_generator_agent import event_generator_agent; print('✓ Event Generator Agent created')"
```

---

### Step 3.2: Portfolio Agent (45 min)

**Old Step 3.1 is now Step 3.2**

**File**: `backend/infrastructure/agents/portfolio_agent.py`
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from .tools.portfolio_tools import (
    validate_ticker,
    get_current_price,
    get_fundamentals
)

llm = ChatGoogleGenerativeAI(model="gemini-pro")

portfolio_agent = create_react_agent(
    llm,
    tools=[validate_ticker, get_current_price, get_fundamentals],
    prompt="You manage portfolios. Validate tickers, fetch prices, provide fundamentals."
)
```

Repeat for: `news_agent`, `price_agent`, `villain_agent`, `insight_agent`

### Step 3.2: Build Multi-Agent Graph

**File**: `backend/infrastructure/agents/game_graph.py`
```python
from langgraph.graph import StateGraph, END

def create_game_graph():
    workflow = StateGraph(GameState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("news", news_node)
    workflow.add_node("price", price_node)
    workflow.add_node("villain", villain_node)
    workflow.add_node("insight", insight_node)
    
    # Supervisor routes
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state['next_agent'],
        {
            "portfolio": "portfolio",
            "news": "news",
            "price": "price",
            "villain": "villain",
            "insight": "insight",
            "END": END
        }
    )
    
    # All agents return to supervisor
    for agent in ["portfolio", "news", "price", "villain", "insight"]:
        workflow.add_edge(agent, "supervisor")
    
    workflow.set_entry_point("supervisor")
    
    return workflow.compile()

game_graph = create_game_graph()
```

**✅ Checkpoint**: Multi-agent graph working, can generate scenarios

---

## Phase 4: Application Layer (3 hours)

### Step 4.1: Use Case Handlers

**File**: `backend/application/portfolio/CreatePortfolioHandler.py`
```python
class CreatePortfolioHandler:
    def __init__(self, portfolio_repo, price_fetcher):
        self.portfolio_repo = portfolio_repo
        self.price_fetcher = price_fetcher
    
    async def execute(
        self,
        player_id: str,
        tickers: List[str],
        allocations: dict,
        risk_profile: str
    ):
        # Create portfolio
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            player_id=player_id,
            risk_profile=RiskProfile(risk_profile)
        )
        
        # Add positions
        for ticker in tickers:
            entry_price = await self.price_fetcher.get_current_price(ticker)
            portfolio.add_position(ticker, allocations[ticker], entry_price)
        
        # Save
        await self.portfolio_repo.save(portfolio)
        
        return {
            'portfolio_id': portfolio.id,
            'total_value': portfolio.calculate_total_value()
        }
```

**File**: `backend/application/game/StartRoundHandler.py`
```python
class StartRoundHandler:
    async def execute(self, game_id: str, round_number: int):
        # Invoke multi-agent graph
        result = await game_graph.ainvoke({
            'game_id': game_id,
            'task': 'round_start',
            # ...
        })
        
        return {
            'event': result['event'],
            'villain_take': result['villain_take'],
            'data_tab': {
                'headlines': result['headlines'],
                'consensus': result['consensus'],
                'contradiction_score': result['contradiction_score'],
                # ...
            }
        }
```

**✅ Checkpoint**: Business logic complete

---

## Phase 5: API Layer (3 hours)

### Step 5.1: FastAPI Setup

**File**: `backend/main.py`
```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
portfolio_repo = SupabasePortfolioRepository()
create_portfolio_handler = CreatePortfolioHandler(portfolio_repo, price_fetcher)

# Endpoints
@app.post("/portfolio/create")
async def create_portfolio(req: CreatePortfolioRequest):
    result = await create_portfolio_handler.execute(
        req.player_id,
        req.tickers,
        req.allocations,
        req.risk_profile
    )
    return result

@app.post("/game/start")
async def start_game(req: StartGameRequest):
    result = await start_game_handler.execute(req.portfolio_id)
    return result

@app.websocket("/game/{game_id}/ws")
async def game_websocket(websocket: WebSocket, game_id: str):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data['type'] == 'decision':
                result = await submit_decision_handler.execute(
                    game_id,
                    data['action'],
                    data['decision_time'],
                    data['opened_data_tab']
                )
                
                await websocket.send_json({
                    'type': 'outcome',
                    'data': result
                })
    except WebSocketDisconnect:
        pass
```

**✅ Checkpoint**: Backend API complete

---

## Phase 6: Frontend (5 hours)

### Step 6.1: Portfolio Builder

**File**: `frontend/app/portfolio/page.tsx`
```typescript
'use client'

import { useState } from 'react'
import { StockSelector } from '@/components/portfolio/StockSelector'
import { AllocationControls } from '@/components/portfolio/AllocationControls'

export default function PortfolioPage() {
  const [tickers, setTickers] = useState<string[]>([])
  const [allocations, setAllocations] = useState<Record<string, number>>({})
  const [riskProfile, setRiskProfile] = useState('Balanced')
  
  const handleCreate = async () => {
    const res = await fetch('/api/portfolio/create', {
      method: 'POST',
      body: JSON.stringify({ tickers, allocations, riskProfile })
    })
    
    const { portfolio_id } = await res.json()
    
    // Redirect to game
    window.location.href = `/game/${portfolio_id}`
  }
  
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-8">Build Your Portfolio</h1>
      
      <StockSelector
        universe={['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']}
        selected={tickers}
        onSelect={setTickers}
      />
      
      <AllocationControls
        tickers={tickers}
        allocations={allocations}
        onAllocate={setAllocations}
        budget={1_000_000}
      />
      
      <button onClick={handleCreate}>Start Game</button>
    </div>
  )
}
```

### Step 6.2: Game UI with Data Tab

**File**: `frontend/app/game/[id]/page.tsx`
```typescript
'use client'

import { useState } from 'react'
import { useGameWebSocket } from '@/lib/use-websocket'
import { EventCard } from '@/components/game/EventCard'
import { VillainBubble } from '@/components/game/VillainBubble'
import { DataTab } from '@/components/game/DataTab'
import { DecisionButtons } from '@/components/game/DecisionButtons'

export default function GamePage({ params }: { params: { id: string } }) {
  const [event, setEvent] = useState(null)
  const [villainTake, setVillainTake] = useState(null)
  const [dataTab, setDataTab] = useState(null)
  const [showDataTab, setShowDataTab] = useState(false)
  const [startTime] = useState(Date.now())
  
  const { sendDecision } = useGameWebSocket(params.id, (data) => {
    if (data.type === 'round_start') {
      setEvent(data.event)
      setVillainTake(data.villain)
      setDataTab(data.data_tab)
      setShowDataTab(false)
    } else if (data.type === 'outcome') {
      // Show outcome...
    }
  })
  
  const handleDecision = (action: string) => {
    const decisionTime = (Date.now() - startTime) / 1000
    sendDecision(action, decisionTime, showDataTab)
  }
  
  return (
    <div className="container mx-auto p-8">
      {event && <EventCard event={event} />}
      {villainTake && <VillainBubble take={villainTake} />}
      
      <button onClick={() => setShowDataTab(!showDataTab)}>
        {showDataTab ? 'Hide' : 'Show'} Data Tab
      </button>
      
      {showDataTab && dataTab && <DataTab data={dataTab} />}
      
      <DecisionButtons
        choices={['SELL_ALL', 'SELL_HALF', 'HOLD', 'BUY']}
        onDecision={handleDecision}
      />
    </div>
  )
}
```

**✅ Checkpoint**: Full-stack working

---

## Phase 7: Database & Historical Cases (2 hours)

### Step 7.1: Supabase Schema

```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    player_id UUID,
    risk_profile TEXT,
    tickers TEXT[],
    allocations JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE game_sessions (
    id UUID PRIMARY KEY,
    portfolio_id UUID REFERENCES portfolios(id),
    current_round INT DEFAULT 0,
    portfolio_value DECIMAL,
    started_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE game_rounds (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id),
    round_number INT,
    ticker TEXT,
    event_type TEXT,
    villain_stance TEXT,
    player_decision TEXT,
    opened_data_tab BOOLEAN,
    pl_dollars DECIMAL,
    pl_percent DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE decision_tracker (
    id UUID PRIMARY KEY,
    round_id UUID REFERENCES game_rounds(id),
    headlines_shown JSONB,
    consensus TEXT,
    contradiction_score DECIMAL,
    behavior_flags JSONB
);

CREATE TABLE historical_cases (
    id UUID PRIMARY KEY,
    ticker TEXT,
    event_type TEXT,
    date DATE,
    horizon_days INT,
    day0_price DECIMAL,
    day_h_price DECIMAL
);
```

### Step 7.2: Seed Historical Cases

```python
# backend/scripts/seed_historical_cases.py
import yfinance as yf
from datetime import datetime, timedelta

async def seed_historical_cases():
    """Pre-seed 100-200 historical cases"""
    
    tickers = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']
    event_types = ['EARNINGS_BEAT', 'EARNINGS_MISS', 'REGULATORY_NEWS', 'ANALYST_UPGRADE']
    
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        
        # Sample 20 random dates from past 2 years
        for _ in range(20):
            days_back = random.randint(7, 730)
            end_date = datetime.now() - timedelta(days=days_back)
            start_date = end_date - timedelta(days=3)
            
            data = stock.history(start=start_date, end=end_date)
            
            if len(data) >= 3:
                await db.execute("""
                    INSERT INTO historical_cases (ticker, event_type, date, horizon_days, day0_price, day_h_price)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, ticker, random.choice(event_types), start_date, 3, data['Close'].iloc[0], data['Close'].iloc[-1])

# Run once
asyncio.run(seed_historical_cases())
```

**✅ Checkpoint**: Persistence complete

---

## Phase 8: Observability (2 hours)

### Step 8.1: Enable Opik + LangSmith

```python
# backend/main.py
import opik
import os

# Opik
opik.configure(api_key=os.getenv("OPIK_API_KEY"))

# LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "market-mayhem"
```

### Step 8.2: Add Tracing to Agents

```python
from opik.integrations.langchain import OpikTracer

tracers = {
    "portfolio": OpikTracer(tags=["portfolio"]),
    "news": OpikTracer(tags=["news"]),
    # ...
}

async def news_node(state):
    config = {"callbacks": [tracers["news"]]}
    result = await news_agent.ainvoke(state, config=config)
    return result
```

**✅ Checkpoint**: Full observability + visualization

---

## Phase 9: Testing & Polish (3 hours)

### Step 9.1: End-to-End Test

```python
async def test_full_game():
    # Create portfolio
    portfolio = await create_portfolio_handler.execute(
        "player1",
        ["AAPL", "TSLA", "MSFT"],
        {"AAPL": 300000, "TSLA": 400000, "MSFT": 300000},
        "Balanced"
    )
    
    # Start game
    game = await start_game_handler.execute(portfolio['portfolio_id'])
    
    # Play 3 rounds
    for round_num in range(1, 4):
        round_data = await start_round_handler.execute(game['game_id'], round_num)
        
        # Make decision
        outcome = await submit_decision_handler.execute(
            game['game_id'],
            "SELL_HALF",
            15.5,
            opened_data_tab=True
        )
        
        print(f"Round {round_num}: P/L = {outcome['pl_dollars']}")
    
    # Final report
    report = await generate_final_report_handler.execute(game['game_id'])
    print(f"Profile: {report['profile']}")
```

---

## Development Timeline

### Day 1 (8 hours): Foundation
- **Morning (4h)**: Phase 0-1 (Setup + Domain)
- **Afternoon (4h)**: Phase 2 (Tools + Adapters)

### Day 2 (8 hours): Agents + Application
- **Morning (4h)**: Phase 3 (LangGraph Agents)
- **Afternoon (4h)**: Phase 4-5 (Application + API)

### Day 3 (8 hours): Frontend + Integration
- **Morning (4h)**: Phase 6 (Frontend)
- **Afternoon (4h)**: Phase 7-8 (Database + Observability)

### Day 4 (4 hours): Polish + Demo
- **Morning (2h)**: Phase 9 (Testing)
- **Afternoon (2h)**: Demo preparation

---

## Success Checklist

- [ ] Portfolio creation working (Round 0)
- [ ] Event generation with Villain + Data tab
- [ ] Historical outcome replay (not random)
- [ ] Decision tracking with full context
- [ ] Final report with behavioral profile
- [ ] Frontend connects to backend via WebSocket
- [ ] Opik tracing enabled
- [ ] LangSmith graph visualization
- [ ] Historical cases seeded
- [ ] End-to-end game flow complete

**Total Time**: ~28 hours
**Target**: Working MVP in 3-4 days

---

**Follow this roadmap step-by-step to build Market Mayhem systematically!** 🚀
