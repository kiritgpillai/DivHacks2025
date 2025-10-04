# Opik + LangSmith Integration - Market Mayhem

## Overview

**Opik** (by Comet ML) provides LLM observability for Market Mayhem's 6 agents. **LangSmith** visualizes the agent graph and execution flow.

**Key Benefits**:
- 🔍 **Track agent reasoning** - See why Event Generator picks specific tickers and events
- 📊 **Monitor performance** - Identify slow agents or tools
- 🐛 **Debug decisions** - Trace event generation and historical case sampling
- 📈 **Track metrics** - Event quality, contradiction scores, behavioral profiles
- 🎨 **Visualize graph** - LangSmith shows agent coordination

---

## Installation & Setup

### Step 1: Install Opik + LangSmith

```bash
# backend/requirements.txt
opik==1.0.0
langsmith==0.1.0  # Optional for visualization

pip install opik langsmith
```

### Step 2: Configure Environment

```bash
# backend/.env
OPIK_API_KEY=your_opik_api_key
OPIK_PROJECT_NAME=market-mayhem
OPIK_WORKSPACE=your_workspace

# Optional: LangSmith visualization
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=market-mayhem

# Get keys from:
# Opik: https://www.comet.com/signup
# LangSmith: https://smith.langchain.com
```

### Step 3: Initialize in Application

```python
# backend/main.py
import opik
import os

# Initialize Opik
opik.configure(
    api_key=os.getenv("OPIK_API_KEY"),
    project_name=os.getenv("OPIK_PROJECT_NAME", "market-mayhem")
)

# LangSmith tracing (automatic if env vars set)
print("✅ Opik + LangSmith initialized - All agents will be traced")
```

---

## Agent Instrumentation

### Pattern: Add OpikTracer to Agents

```python
# backend/infrastructure/agents/__init__.py
from opik.integrations.langchain import OpikTracer

# Create tracers for each agent
tracers = {
    "event_generator": OpikTracer(
        tags=["event-generator", "agent"],
        metadata={"agent": "EventGeneratorAgent", "tool_count": 5}
    ),
    "portfolio": OpikTracer(
        tags=["portfolio", "agent"],
        metadata={"agent": "PortfolioAgent", "tool_count": 6}
    ),
    "news": OpikTracer(
        tags=["news", "agent"],
        metadata={"agent": "NewsAgent", "tool_count": 4}
    ),
    "price": OpikTracer(
        tags=["price", "agent"],
        metadata={"agent": "PriceAgent", "tool_count": 6}
    ),
    "villain": OpikTracer(
        tags=["villain", "agent"],
        metadata={"agent": "VillainAgent", "tool_count": 4}
    ),
    "insight": OpikTracer(
        tags=["insight", "agent"],
        metadata={"agent": "InsightAgent", "tool_count": 5}
    )
}

def get_agent_config(agent_name: str) -> dict:
    """Get config with OpikTracer"""
    return {"callbacks": [tracers[agent_name]]}
```

### Use in Agent Nodes

```python
# backend/infrastructure/agents/game_graph.py
async def news_node_with_tracing(state: GameState) -> GameState:
    """News agent with Opik tracing"""
    
    config = get_agent_config("news")
    
    result = await news_agent.ainvoke(state, config=config)
    
    # State updates...
    return state
```

---

## Tool Tracing

### Add @track Decorator to Tools

```python
# backend/infrastructure/agents/tools/news_tools.py
from opik import track

@tool
@track(name="fetch_ticker_news", tags=["tool", "tavily"])
async def fetch_ticker_news(ticker: str, days: int = 3) -> str:
    """Fetch recent headlines for a ticker.
    
    Opik automatically captures:
    - Input: ticker, days
    - Output: JSON headlines
    - Execution time
    - Any errors
    """
    query = f"{ticker} stock news"
    
    results = await tavily.search(
        query=query,
        topic="news",
        days=days,
        max_results=3
    )
    
    # Opik logs this automatically
    opik.log_metric("tavily_results_count", len(results.get('results', [])))
    
    return json.dumps(results)

@tool
@track(name="assign_headline_stance", tags=["tool", "gemini"])
async def assign_headline_stance(headline: str) -> str:
    """Classify headline stance using Gemini (traced)"""
    # Tool logic...
    pass
```

---

## Game Flow Tracing

### Track Round Execution

```python
# backend/application/game/StartRoundHandler.py
from opik import track, log_metric

class StartRoundHandler:
    @track(
        name="start_round",
        tags=["game", "round"],
        capture_input=True,
        capture_output=True
    )
    async def execute(self, game_id: str, round_number: int):
        """Start round with full tracing"""
        
        start_time = time.time()
        
        # Invoke multi-agent graph (agents auto-traced)
        result = await game_graph.ainvoke(
            {
                'game_id': game_id,
                'current_round': round_number,
                'task': 'round_start',
                # ...
            },
            config=get_agent_config("supervisor")
        )
        
        # Log custom metrics
        round_time = time.time() - start_time
        log_metric("round_generation_time", round_time, tags=["performance"])
        log_metric("contradiction_score", result['contradiction_score'], tags=["villain"])
        log_metric("consensus", result['consensus'], tags=["news"])
        
        return result
```

### Track Decision Evaluation

```python
# backend/application/game/SubmitDecisionHandler.py
class SubmitDecisionHandler:
    @track(
        name="evaluate_decision",
        tags=["game", "decision"],
        capture_input=True,
        capture_output=True
    )
    async def execute(self, game_id: str, decision: dict):
        """Evaluate decision with tracing"""
        
        result = await game_graph.ainvoke(
            {
                'game_id': game_id,
                'task': 'decision_evaluation',
                'player_decision': decision,
                # ...
            },
            config=get_agent_config("supervisor")
        )
        
        # Log decision metrics
        log_metric("pl_dollars", result['pl_dollars'], tags=["outcome"])
        log_metric("pl_percent", result['pl_percent'], tags=["outcome"])
        log_metric("opened_data_tab", decision['opened_data_tab'], tags=["behavior"])
        log_metric("decision_time", decision['decision_time'], tags=["behavior"])
        
        # Track behavior flags
        for flag, value in result['behavior_flags'].items():
            if value:
                log_metric(f"behavior_{flag}", 1.0, tags=["behavior"])
        
        return result
```

---

## Custom Metrics for Market Mayhem

### Contradiction Score Tracking

```python
# Track how often Villain misleads
opik.log_metric("contradiction_score", contradiction_score, tags=["villain", "news"])

# Track if player resisted Villain
if contradiction_score > 0.7 and not followed_villain:
    opik.log_metric("resisted_villain_high_contradiction", 1.0, tags=["behavior", "success"])
```

### Behavioral Profile Tracking

```python
# Track final profile classification
opik.log_metric("behavioral_profile", profile_name, tags=["final_report"])

# Track profile metrics
opik.log_metric("data_tab_usage_pct", data_tab_usage, tags=["behavior"])
opik.log_metric("consensus_alignment_pct", consensus_alignment, tags=["behavior"])
opik.log_metric("panic_sells_count", panic_sells, tags=["behavior"])
opik.log_metric("chased_spikes_count", chased_spikes, tags=["behavior"])
```

### Historical Case Selection

```python
# Track which historical cases are used
opik.log_metric("historical_case_date", case_date, tags=["price_agent"])
opik.log_metric("historical_case_ticker", case_ticker, tags=["price_agent"])
opik.log_metric("historical_case_event_type", event_type, tags=["price_agent"])
```

---

## LangSmith Visualization

### Enable Graph Visualization

LangSmith automatically visualizes your LangGraph workflow when `LANGCHAIN_TRACING_V2=true`.

**What you see**:
1. **Agent Graph**: Visual representation of your 5 agents and their connections
2. **Execution Flow**: See which agents are called in what order
3. **Tool Calls**: Drill down into individual tool invocations
4. **Latency**: Identify bottlenecks

**Access**: https://smith.langchain.com → Select "market-mayhem" project

### Trace a Complete Game Round

```
Round Start Trace:
├── Supervisor Node (decides: round_start)
├── Event Generator Agent
│   ├── select_ticker_from_portfolio tool
│   ├── determine_event_type tool
│   ├── generate_event_description tool (Gemini LLM call)
│   └── set_event_horizon tool
├── Villain Agent
│   ├── determine_villain_stance tool
│   ├── generate_hot_take tool (Gemini LLM call)
│   └── label_cognitive_bias tool
├── News Agent
│   ├── fetch_ticker_news tool (Tavily API)
│   ├── assign_headline_stance tool (Gemini LLM call)
│   ├── calculate_consensus tool
│   └── compute_contradiction_vs_villain tool
├── Price Agent
│   ├── get_sparkline tool (yfinance)
│   ├── detect_price_pattern tool
│   └── calculate_historical_outcomes tool
├── Portfolio Agent
│   └── get_fundamentals tool (yfinance)
└── Insight Agent
    └── write_neutral_tip tool (Gemini LLM call)

Total Time: 4.5s
Total Tool Calls: 15
Total LLM Calls: 4
```

---

## Dashboard Configuration

### Opik Dashboard Views

#### 1. **Agent Performance**
Track individual agent metrics:
- Event Generator Agent: Event generation time, ticker selection distribution, event type variety
- Portfolio Agent: Validation time, price fetch latency
- News Agent: Stance accuracy, contradiction score distribution
- Price Agent: Historical case sampling time, P/L calculation accuracy
- Villain Agent: Hot take generation time, bias distribution
- Insight Agent: Profile classification accuracy, coaching quality

#### 2. **Game Flow**
Visualize complete game sessions:
- Round 0 (Portfolio setup) → Rounds 1-7 → Final report
- Which agents are invoked per round
- Tool call dependencies
- Latency bottlenecks

#### 3. **Player Analytics**
Monitor learning progression:
- Data tab usage trends
- Decision quality improvements
- Behavioral profile distribution (Rational/Emotional/Conservative)
- Villain resistance patterns

#### 4. **System Health**
Track system performance:
- API response times (Tavily, yfinance, Gemini)
- Agent execution latency
- Error rates
- Cache hit rates

---

## Example: Complete Round Trace

```
Trace: Game Round #3 (Player: user123, Ticker: TSLA, Event: EARNINGS_BEAT)

├── [Supervisor] Route to round_start (0.1s)
├── [Event Generator Agent] Create event scenario (1.3s)
│   ├── [Tool] select_ticker_from_portfolio → "TSLA" (0.1s)
│   ├── [Tool] determine_event_type → "EARNINGS_SURPRISE" (0.2s)
│   ├── [LLM] generate_event_description → "Tesla reports Q4..." (0.9s)
│   └── [Tool] set_event_horizon → 3 days (0.1s)
├── [Villain Agent] Generate hot take (1.2s)
│   ├── [Tool] determine_villain_stance → "Bearish" (0.3s)
│   ├── [LLM] generate_hot_take → "Earnings trap! Sell now!" (0.8s)
│   └── [Tool] label_cognitive_bias → "Fear Appeal" (0.1s)
├── [News Agent] Fetch and analyze (1.5s)
│   ├── [Tool] fetch_ticker_news → 3 headlines (0.8s)
│   ├── [LLM] assign_headline_stance (3 calls) → Bull, Bull, Neutral (0.6s)
│   └── [Tool] compute_contradiction_vs_villain → 0.67 (0.1s)
├── [Price Agent] Get price data (0.9s)
│   ├── [Tool] get_sparkline → [240, 238, 236, 242, 251] (0.4s)
│   ├── [Tool] detect_price_pattern → "gap_up_after_down_trend" (0.2s)
│   └── [Tool] calculate_historical_outcomes → {sell_all: -0.03, ...} (0.3s)
├── [Portfolio Agent] Get fundamentals (0.5s)
│   └── [Tool] get_fundamentals → {pe: 45.2, beta: 1.85, ...} (0.5s)
└── [Insight Agent] Write tip (0.8s)
    └── [LLM] write_neutral_tip → "Earnings gaps with high beta..." (0.8s)

Metrics:
├── Total time: 4.3s
├── Agent calls: 6
├── Tool calls: 14
├── LLM calls: 6
├── Event: EARNINGS_SURPRISE on TSLA
├── Contradiction score: 0.67 (67% disagree with Villain)
└── Data tab populated: ✓

Player Decision: SELL_HALF after 18.5s (opened data tab)
```

---

## Quick Start Checklist

- [ ] Install: `pip install opik langsmith`
- [ ] Get API keys: comet.com/signup, smith.langchain.com
- [ ] Add keys to `.env`
- [ ] Initialize Opik in `main.py`
- [ ] Create OpikTracer for each agent
- [ ] Add `@track` decorators to tools
- [ ] Add `@track` decorators to handlers
- [ ] Test one round, view traces
- [ ] Configure custom metrics
- [ ] View LangSmith graph visualization

---

## Benefits Summary

✅ **Visibility** - See every agent decision, tool call, and LLM interaction
✅ **Performance** - Identify and fix latency bottlenecks
✅ **Quality** - Monitor Villain misleading rate, stance accuracy
✅ **Learning** - Track player progression and behavioral patterns
✅ **Debugging** - Trace errors to specific agents or tools
✅ **Optimization** - Data-driven improvements to prompts and logic
✅ **Visualization** - LangSmith shows agent graph and flow

**Implementation Time**: ~2 hours
**Ongoing Overhead**: Minimal (<5% latency)
**Value**: Essential for development, demo, and production monitoring

---

**Opik + LangSmith provide complete observability and visualization for Market Mayhem's multi-agent system.** 🚀
