# Observability Setup Guide

This module provides observability for Market Mayhem using:
- **Opik (Comet ML)**: LLM call tracing and agent performance metrics
- **LangSmith**: Multi-agent graph visualization and debugging

## Why Observability?

Observability helps you:
1. **Debug issues** - See exactly what each agent is doing
2. **Optimize performance** - Track latency and token usage
3. **Improve prompts** - Analyze agent outputs and iterate
4. **Monitor costs** - Track LLM API usage
5. **Visualize workflow** - See the multi-agent graph in action

## Setup Instructions

### 1. Opik (LLM Tracing)

#### Get API Key
1. Go to [comet.com](https://www.comet.com/)
2. Sign up / log in
3. Go to Settings → API Keys
4. Copy your Opik API key

#### Configure
```bash
# Add to .env
OPIK_API_KEY=your_opik_key_here
```

#### Enable in Backend
```python
# backend/main.py
from backend.infrastructure.observability import setup_opik

# At startup
@app.on_event("startup")
async def startup_event():
    setup_opik()
```

#### View Traces
- Dashboard: https://www.comet.com/opik
- Project: `market-mayhem`
- View all agent calls, LLM interactions, and performance metrics

### 2. LangSmith (Graph Visualization)

#### Get API Key
1. Go to [smith.langchain.com](https://smith.langchain.com/)
2. Sign up / log in
3. Go to Settings → API Keys
4. Copy your LangSmith API key

#### Configure
```bash
# Add to .env
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=market-mayhem  # Optional, defaults to "market-mayhem"
```

#### Enable in Backend
```python
# backend/main.py
from backend.infrastructure.observability import setup_langsmith

# At startup
@app.on_event("startup")
async def startup_event():
    setup_langsmith()
```

#### View Graphs
- Dashboard: https://smith.langchain.com
- Project: `market-mayhem`
- See the multi-agent graph, execution flow, and timing

## Usage

### Trace Agent Calls

Use the `@trace_agent_call` decorator:

```python
from backend.infrastructure.observability import trace_agent_call

@trace_agent_call("portfolio_agent")
async def portfolio_node(state):
    # Your agent code
    return result
```

### Log Custom Events

```python
from backend.infrastructure.observability.opik_tracer import log_game_event

# Log game events
log_game_event("round_start", {
    "round": 1,
    "ticker": "AAPL",
    "player_id": "player_123"
})

log_game_event("decision_submitted", {
    "decision": "HOLD",
    "decision_time": 15.5
})
```

### Log LLM Calls

```python
from backend.infrastructure.observability.opik_tracer import log_llm_call

log_llm_call(
    model="gemini-pro",
    prompt="Generate a realistic earnings event...",
    response="Apple reports Q4 earnings...",
    tokens=150,
    latency=1.2
)
```

## What Gets Tracked?

### Opik Tracks:
- ✅ All agent calls (6 agents)
- ✅ Tool usage by each agent
- ✅ LLM API calls (Gemini)
- ✅ Input/output for each agent
- ✅ Errors and exceptions
- ✅ Performance metrics (latency, tokens)
- ✅ Custom game events

### LangSmith Tracks:
- ✅ Multi-agent graph structure
- ✅ Agent execution flow
- ✅ State transitions
- ✅ Tool calls and responses
- ✅ LLM prompts and completions
- ✅ Timing and performance

## Example Integration

```python
# backend/infrastructure/agents/portfolio_agent.py
from backend.infrastructure.observability import trace_agent_call

@trace_agent_call("portfolio_agent")
async def portfolio_node(state):
    """Portfolio agent node with tracing"""
    result = await portfolio_agent.ainvoke(state)
    return result
```

## Dashboard Screenshots

### Opik Dashboard
- See all traces organized by project
- Filter by agent, time range, success/failure
- Analyze token usage and costs
- Export data for analysis

### LangSmith Dashboard
- Visualize the multi-agent graph
- See execution paths and timing
- Debug failures with full context
- Compare runs side-by-side

## Troubleshooting

### Opik Not Logging
- Check `OPIK_API_KEY` is set
- Verify internet connection
- Check opik is installed: `pip install opik`
- View logs for errors

### LangSmith Not Showing Graphs
- Check `LANGSMITH_API_KEY` is set
- Verify `LANGCHAIN_TRACING_V2=true`
- Check langsmith is installed: `pip install langsmith`
- Refresh dashboard after a few seconds

### High Latency
- Observability adds ~50-100ms overhead
- For production, consider sampling (trace 10% of requests)
- Use async logging to minimize impact

## Production Considerations

1. **Sampling**: Don't trace every request in production
   ```python
   import random
   should_trace = random.random() < 0.1  # 10% sampling
   ```

2. **PII Filtering**: Remove sensitive data from traces
   ```python
   # Don't log user IDs, emails, etc.
   trace.log_input({"user_id": "REDACTED", "action": action})
   ```

3. **Cost Management**: Track LLM token usage via Opik
   ```python
   # Set budget alerts in Opik dashboard
   ```

4. **Performance**: Use async logging to minimize latency
   ```python
   # Opik automatically uses async logging
   ```

## Next Steps

1. ✅ Enable observability in backend
2. ✅ Run a few test games
3. ✅ View traces in Opik dashboard
4. ✅ View graph in LangSmith
5. ✅ Analyze agent performance
6. ✅ Iterate on prompts based on data
7. ✅ Set up alerts for errors

## Resources

- [Opik Docs](https://www.comet.com/docs/opik/)
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [LangGraph Observability](https://python.langchain.com/docs/langgraph/how-tos/visualization)
