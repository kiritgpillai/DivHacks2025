# LangGraph Multi-Agent Workflows - Market Mayhem

## Overview

**Multi-agent system** with **6 ReAct agents** orchestrated by LangGraph. Each agent has specialized tools for event generation, portfolio management, news analysis, price replay, Villain generation, and behavioral coaching.

**Agents**:
1. **Event Generator Agent** - Create market event scenarios (5 tools)
2. **Portfolio Agent** - Portfolio management (6 tools)
3. **News Agent** - Headlines + stance detection (4 tools)
4. **Price Agent** - Historical replay + price data (6 tools)
5. **Villain Agent** - Trash-talking hot takes (4 tools)
6. **Insight Agent** - Behavioral profiling + coaching (5 tools)

---

## 1. State Schema

```python
from typing import TypedDict, Dict, List, Any, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class GameState(TypedDict):
    # Game metadata
    game_id: str
    portfolio_id: str
    current_round: int
    task: str  # "round_start" | "decision_evaluation" | "final_report"
    
    # Agent communication
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Portfolio context
    portfolio: Dict[str, Any]  # From Portfolio Agent
    tickers: List[str]
    risk_profile: str
    
    # Round context
    selected_ticker: str
    event: Dict[str, Any]
    horizon: int
    
    # Data tab content
    headlines: List[Dict[str, Any]]  # From News Agent
    consensus: str
    contradiction_score: float
    fundamentals: Dict[str, Any]  # From Portfolio Agent
    price_data: Dict[str, Any]  # From Price Agent
    historical_outcomes: Dict[str, Any]  # From Price Agent
    neutral_tip: str  # From Insight Agent
    
    # Villain
    villain_take: Dict[str, Any]  # From Villain Agent
    
    # Player input
    player_decision: Dict[str, Any]
    
    # Outcome
    historical_case: Dict[str, Any]  # Sampled case
    pl_dollars: float
    pl_percent: float
    portfolio_value: float
    behavior_flags: Dict[str, Any]
    
    # Final report
    final_report: Dict[str, Any]
```

---

## 2. Agent Creation

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)

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
    prompt="""You generate realistic market event scenarios for Market Mayhem.
    
    Your job:
    1. Select a ticker from the player's portfolio (weight by position size)
    2. Choose an appropriate event type based on difficulty and market context
    3. Generate a compelling, educational event description
    4. Set the event horizon (3-5 trading days)
    5. Validate the event makes sense for the ticker
    
    Make scenarios realistic, engaging, and tied to actual market dynamics.
    """
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
    prompt="""You manage portfolios in Market Mayhem.
    
    Responsibilities:
    - Validate tickers before portfolio creation
    - Fetch current prices
    - Calculate position and portfolio values
    - Apply decisions (Sell All/Sell Half/Hold/Buy)
    - Provide fundamentals (P/E, beta, volatility)
    
    Be precise with calculations and validate all inputs.
    """
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
    prompt="""You fetch and analyze news for Market Mayhem.
    
    Responsibilities:
    - Fetch recent headlines for tickers (via Tavily)
    - Classify each headline as Bull/Bear/Neutral
    - Compute consensus (e.g., "Two-thirds Bull")
    - Calculate contradiction score vs Villain's stance
    
    Be objective in stance classification. The contradiction score helps players identify when the Villain is misleading.
    """
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
    prompt="""You handle price data and historical outcome replay in Market Mayhem.
    
    Responsibilities:
    - Provide current price snapshots
    - Generate sparklines for UI
    - Detect price patterns (3 down closes, gap up, volatility spikes)
    - Sample matched historical windows for outcome replay
    - Apply player decisions to price paths and calculate P/L
    - Calculate median historical outcomes for each action (Sell All/Sell Half/Hold)
    
    CRITICAL: Never use random outcomes. Always base outcomes on real historical price paths.
    Match by ticker > sector > event type for historical cases.
    """
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
    prompt="""You are the Villain in Market Mayhem - a trash-talking AI that misleads players.
    
    Responsibilities:
    - Generate bold, emotionally charged hot takes
    - Often be WRONG to mislead players (50-70% of the time)
    - Label cognitive biases you're exploiting (Fear/FOMO/Authority/Recency)
    - Maintain a consistent trash-talking persona
    
    Example hot take: "This earnings beat is a trap! Smart money is dumping into retail hype. I'm selling ALL my shares before it crashes tomorrow."
    
    Be confident, provocative, and educational through your mistakes.
    """
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
    prompt="""You provide neutral coaching and behavioral analysis in Market Mayhem.
    
    Responsibilities:
    - Write educational, non-coercive tips for the Data tab
    - Aggregate player decisions into behavioral metrics
    - Classify behavioral profiles (Rational/Emotional/Conservative)
    - Generate personalized coaching recommendations
    - Identify patterns (panic sells, FOMO chasing, Villain resistance)
    
    Be encouraging, never harsh. Focus on patterns and improvement.
    Use rule-based classification (transparent, explainable).
    """
)
```

---

## 3. Agent Node Implementations

### Portfolio Node

```python
from langchain_core.messages import HumanMessage

async def portfolio_node(state: GameState) -> GameState:
    """Handle portfolio operations"""
    
    task = state.get('task')
    
    if task == 'create_portfolio':
        # Portfolio creation (Round 0)
        result = await portfolio_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Validate and create portfolio:
                Tickers: {state['tickers']}
                Allocations: {state['allocations']}
                Risk profile: {state['risk_profile']}
                
                Return JSON: {{"valid": true/false, "portfolio": {{...}}, "total_value": number}}
                """)
            ]
        })
        
        portfolio_data = json.loads(result['messages'][-1].content)
        state['portfolio'] = portfolio_data['portfolio']
        state['portfolio_value'] = portfolio_data['total_value']
    
    elif task == 'get_fundamentals':
        # Get fundamentals for Data tab
        result = await portfolio_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Get fundamentals for {state['selected_ticker']}:
                - P/E ratio
                - YoY revenue growth
                - Beta
                - 30-day volatility
                
                Return JSON.
                """)
            ]
        })
        
        state['fundamentals'] = json.loads(result['messages'][-1].content)
    
    elif task == 'apply_decision':
        # Apply player decision to portfolio
        result = await portfolio_agent.ainvoke({
        'messages': [
                HumanMessage(content=f"""Apply decision to portfolio:
                Portfolio: {state['portfolio']}
                Ticker: {state['selected_ticker']}
                Decision: {state['player_decision']['action']}
                P/L: {state['pl_dollars']}
                
                Return updated portfolio JSON.
                """)
            ]
        })
        
        state['portfolio'] = json.loads(result['messages'][-1].content)
        state['portfolio_value'] += state['pl_dollars']
    
    return state
```

### News Node
    
```python
async def news_node(state: GameState) -> GameState:
    """Fetch and analyze news"""
    
    result = await news_agent.ainvoke({
        'messages': [
            HumanMessage(content=f"""Fetch and analyze news for {state['selected_ticker']}:
            1. Fetch 2-3 recent headlines (use fetch_ticker_news tool)
            2. Classify each headline stance (Bull/Bear/Neutral)
            3. Calculate consensus
            4. Compute contradiction score vs Villain stance: {state.get('villain_take', {}).get('stance', 'Unknown')}
            
            Return JSON: {{
                "headlines": [{{"title": "...", "stance": "Bull/Bear/Neutral", "source": "..."}}],
                "consensus": "Two-thirds Bull",
                "contradiction_score": 0.0-1.0
            }}
            """)
        ]
    })
    
    news_data = json.loads(result['messages'][-1].content)
    state['headlines'] = news_data['headlines']
    state['consensus'] = news_data['consensus']
    state['contradiction_score'] = news_data['contradiction_score']
    
    return state
```

### Price Node

```python
async def price_node(state: GameState) -> GameState:
    """Handle price data and historical replay"""
    
    task = state.get('task')
    
    if task == 'round_start':
        # Get price data for Data tab
        result = await price_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Get price data for {state['selected_ticker']}:
                1. Current price snapshot
                2. 5-day sparkline
                3. Detect price pattern (3 down closes, gap up, etc.)
                4. Calculate historical outcomes for similar events
                
                Event type: {state['event']['type']}
                Horizon: {state['horizon']} days
                
                Return JSON.
                """)
            ]
        })
        
        price_data = json.loads(result['messages'][-1].content)
        state['price_data'] = price_data['current']
        state['historical_outcomes'] = price_data['historical_outcomes']
    
    elif task == 'decision_evaluation':
        # Sample historical case and evaluate
        result = await price_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Evaluate decision using historical replay:
                Ticker: {state['selected_ticker']}
                Event type: {state['event']['type']}
                Horizon: {state['horizon']} days
                Player decision: {state['player_decision']['action']}
                
                Steps:
                1. Sample historical window (use sample_historical_window tool)
                2. Apply decision to price path (use apply_decision_to_path tool)
                3. Calculate P/L in dollars and percent
                
                Return JSON: {{
                    "historical_case": {{"date": "...", "day0_price": ..., "day_h_price": ...}},
                    "pl_dollars": number,
                    "pl_percent": number,
                    "explanation": "..."
                }}
                """)
            ]
        })
        
        outcome_data = json.loads(result['messages'][-1].content)
        state['historical_case'] = outcome_data['historical_case']
        state['pl_dollars'] = outcome_data['pl_dollars']
        state['pl_percent'] = outcome_data['pl_percent']
    
    return state
```

### Villain Node
    
```python
async def villain_node(state: GameState) -> GameState:
    """Generate Villain hot take"""
    
    result = await villain_agent.ainvoke({
        'messages': [
            HumanMessage(content=f"""Generate a Villain hot take for this event:
            Event: {state['event']['description']}
            Event type: {state['event']['type']}
            Ticker: {state['selected_ticker']}
            
            Steps:
            1. Determine your stance (often be contrarian/wrong)
            2. Choose a cognitive bias to exploit (Fear/FOMO/Authority/Recency)
            3. Generate a bold, trash-talking hot take (1-2 sentences)
            4. Label the bias
            
            Return JSON: {{
                "text": "Your hot take here",
                "stance": "Bullish/Bearish",
                "bias": "Fear Appeal/Overconfidence/Authority Lure/Recency Bias"
            }}
            """)
        ]
    })
    
    state['villain_take'] = json.loads(result['messages'][-1].content)
    
    return state
```

### Insight Node

```python
async def insight_node(state: GameState) -> GameState:
    """Provide coaching and analysis"""
    
    task = state.get('task')
    
    if task == 'round_start':
        # Generate neutral tip for Data tab
        result = await insight_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Write a neutral educational tip:
                Event type: {state['event']['type']}
                Price pattern: {state['price_data'].get('pattern', 'Unknown')}
                Volatility: {state['fundamentals'].get('volatility_30d', 'Unknown')}
                
                Make it educational, non-coercive, 1 sentence.
                Example: "Earnings gaps with high beta and rising vol often mean-revert within 3 days—consider trimming instead of exiting fully."
                """)
            ]
        })
        
        state['neutral_tip'] = result['messages'][-1].content
    
    elif task == 'identify_behavior':
        # Flag behavior patterns
        result = await insight_agent.ainvoke({
            'messages': [
                HumanMessage(content=f"""Identify behavior flags for this decision:
                Decision: {state['player_decision']}
                Price pattern: {state['price_data'].get('pattern', '')}
                Opened data tab: {state['player_decision'].get('opened_data_tab', False)}
                Consensus: {state['consensus']}
                Villain stance: {state['villain_take']['stance']}
                Contradiction score: {state['contradiction_score']}
                
                Check for:
                - Panic sell (after 3 down closes)
                - Chased spike (after 3 up closes with high vol)
                - Ignored data (didn't open tab)
                - Followed Villain under high contradiction
                - Aligned with consensus
                
                Return JSON: {{"panic_sell": bool, "chased_spike": bool, ...}}
                """)
            ]
        })
        
        state['behavior_flags'] = json.loads(result['messages'][-1].content)
    
    elif task == 'final_report':
        # Generate final behavioral report
        result = await insight_agent.ainvoke({
        'messages': [
                HumanMessage(content=f"""Generate final behavioral report:
                All decision logs: {state['all_decisions']}
                
                Steps:
                1. Aggregate behavior metrics (use aggregate_behavior tool)
                2. Classify profile (use classify_profile tool)
                3. Generate coaching (use generate_coaching tool)
                
                Return JSON: {{
                    "profile": "Rational/Emotional/Conservative",
                    "metrics": {{...}},
                    "coaching": ["tip 1", "tip 2", ...],
                    "best_trade": {{...}},
                    "worst_trade": {{...}}
                }}
            """)
        ]
    })
    
        state['final_report'] = json.loads(result['messages'][-1].content)
    
    return state
```

---

## 4. Multi-Agent Graph

```python
from langgraph.graph import StateGraph, END

def supervisor_node(state: GameState) -> GameState:
    """Decide next agent based on task"""
    
    task = state.get('task')
    
    if task == 'round_start':
        if not state.get('event'):
            state['next_agent'] = 'event_generator'
        elif not state.get('villain_take'):
            state['next_agent'] = 'villain'
        elif not state.get('headlines'):
            state['next_agent'] = 'news'
        elif not state.get('price_data'):
            state['next_agent'] = 'price'
        elif not state.get('fundamentals'):
            state['next_agent'] = 'portfolio_fundamentals'
        elif not state.get('neutral_tip'):
            state['next_agent'] = 'insight'
        else:
            state['next_agent'] = 'END'
    
    elif task == 'decision_evaluation':
        if not state.get('pl_dollars'):
            state['next_agent'] = 'price_evaluate'
        elif not state.get('behavior_flags'):
            state['next_agent'] = 'insight_behavior'
        elif not state.get('portfolio_updated'):
            state['next_agent'] = 'portfolio_apply'
        else:
            state['next_agent'] = 'END'
    
    elif task == 'final_report':
        if not state.get('final_report'):
            state['next_agent'] = 'insight_final'
        else:
            state['next_agent'] = 'END'
    
    return state

def create_market_mayhem_graph():
    """Build multi-agent workflow"""
    
    workflow = StateGraph(GameState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("event_generator", event_generator_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("news", news_node)
    workflow.add_node("price", price_node)
    workflow.add_node("villain", villain_node)
    workflow.add_node("insight", insight_node)
    
    # Entry point
    workflow.set_entry_point("supervisor")
    
    # Supervisor routes
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state['next_agent'],
        {
            "event_generator": "event_generator",
            "portfolio": "portfolio",
            "portfolio_fundamentals": "portfolio",
            "portfolio_apply": "portfolio",
            "news": "news",
            "price": "price",
            "price_evaluate": "price",
            "villain": "villain",
            "insight": "insight",
            "insight_behavior": "insight",
            "insight_final": "insight",
            "END": END
        }
    )
    
    # All agents return to supervisor
    workflow.add_edge("event_generator", "supervisor")
    workflow.add_edge("portfolio", "supervisor")
    workflow.add_edge("news", "supervisor")
    workflow.add_edge("price", "supervisor")
    workflow.add_edge("villain", "supervisor")
    workflow.add_edge("insight", "supervisor")
    
    return workflow.compile()

game_graph = create_market_mayhem_graph()
```

---

## 5. Usage Examples

### Example 1: Round Start

```python
async def start_round(game_id: str, round_number: int):
    """Generate round with event + Villain + data"""
    
    result = await game_graph.ainvoke({
        'game_id': game_id,
        'current_round': round_number,
        'task': 'round_start',
        'selected_ticker': 'TSLA',  # Selected from portfolio
        'event': {
            'type': 'EARNINGS_BEAT',
            'description': 'Tesla reports earnings beat of 15% vs expectations. Stock up 6% pre-market.'
        },
        'horizon': 3,
        'messages': []
    })
    
    return {
        'event': result['event'],
        'villain_take': result['villain_take'],
        'data_tab': {
            'headlines': result['headlines'],
            'consensus': result['consensus'],
            'contradiction_score': result['contradiction_score'],
            'fundamentals': result['fundamentals'],
            'price_data': result['price_data'],
            'historical_outcomes': result['historical_outcomes'],
            'neutral_tip': result['neutral_tip']
        }
    }
```

### Example 2: Evaluate Decision

```python
async def evaluate_decision(game_id: str, decision: dict):
    """Evaluate player decision using historical replay"""
    
    result = await game_graph.ainvoke({
        'game_id': game_id,
        'task': 'decision_evaluation',
        'selected_ticker': 'TSLA',
        'event': {...},
        'horizon': 3,
        'player_decision': decision,
        'messages': []
    })
    
    return {
        'outcome': {
            'pl_dollars': result['pl_dollars'],
            'pl_percent': result['pl_percent'],
            'historical_case': result['historical_case']
        },
        'portfolio_value': result['portfolio_value'],
        'behavior_flags': result['behavior_flags']
    }
```

### Example 3: Final Report

```python
async def generate_final_report(game_id: str, all_decisions: list):
    """Generate behavioral profile and coaching"""
    
    result = await game_graph.ainvoke({
        'game_id': game_id,
        'task': 'final_report',
        'all_decisions': all_decisions,
        'messages': []
    })
    
    return result['final_report']
```

---

## 6. Observability with Opik + LangSmith

### Enable LangSmith Visualization

```python
import os

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "market-mayhem"
```

### Add Opik Tracing

```python
from opik.integrations.langchain import OpikTracer

# Create tracers for each agent
portfolio_tracer = OpikTracer(tags=["portfolio", "agent"])
news_tracer = OpikTracer(tags=["news", "agent"])
price_tracer = OpikTracer(tags=["price", "agent"])
villain_tracer = OpikTracer(tags=["villain", "agent"])
insight_tracer = OpikTracer(tags=["insight", "agent"])

# Use in agent calls
async def portfolio_node_with_tracing(state: GameState) -> GameState:
    config = {"callbacks": [portfolio_tracer]}
    result = await portfolio_agent.ainvoke(state, config=config)
    # ...
```

---

## 7. Performance Metrics

| Operation | Agents | Tools | Latency | Parallel? |
|-----------|--------|-------|---------|-----------|
| Round start | 6 agents | 12-16 tools | 4-5s | Partial (Event Gen → then parallel) |
| Decision evaluation | 3 agents | 4-6 tools | 1-2s | Sequential |
| Final report | 1 agent | 3-4 tools | 2-3s | No |

---

## Summary

✅ **6 Specialized Agents** - Event Generator, Portfolio, News, Price, Villain, Insight
✅ **~30 Custom Tools** - Covering event generation, portfolio, news, price, Villain, and coaching
✅ **LangGraph Orchestration** - Supervisor pattern with conditional routing
✅ **Historical Replay** - Price Agent ensures realistic outcomes
✅ **Villain AI** - Generates biased takes with labeled cognitive biases
✅ **Behavioral Coaching** - Insight Agent provides transparent, rule-based profiling
✅ **Full Observability** - Opik tracing + LangSmith visualization

**Ready for implementation!** 🚀
