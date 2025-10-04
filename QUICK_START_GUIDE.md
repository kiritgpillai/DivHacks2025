# Market Mayhem - Quick Start Guide

## 🎯 What's Been Built So Far

### ✅ Complete (30% of project)
1. **Project Structure** - Root package.json, env.example, gitignore
2. **Agent Prompts** - All 6 agent prompts in `backend/prompts/`
3. **Domain Layer** - Complete business logic (Portfolio, Event, News, Villain, Decision, Profile)
4. **Infrastructure Tools** - Started with Portfolio and News tools

### 🚧 What's Next

You now have a solid foundation. Here's how to continue building:

## 📋 Recommended Build Order

### Phase 1: Complete Core Tools (Priority: HIGH)
**Estimated Time**: 3-4 hours

Create remaining critical tools:

```bash
cd backend/infrastructure/agents/tools

# 1. Create price_tools.py (Historical replay - KEY FEATURE)
# Tools needed:
# - get_price_snapshot
# - sample_historical_window
# - apply_decision_to_path

# 2. Create event_tools.py (Event generation)
# Tools needed:
# - select_ticker_from_portfolio
# - generate_event_description (uses Gemini)
# - determine_event_type

# 3. Create villain_tools.py (Trash-talking AI)
# Tools needed:
# - generate_hot_take (uses Gemini)
# - determine_villain_stance
# - label_cognitive_bias

# 4. Create insight_tools.py (Behavioral coaching)
# Tools needed:
# - write_neutral_tip (uses Gemini)
# - classify_profile
# - generate_coaching (uses Gemini)
```

**Use the prompts in `backend/prompts/` as your implementation guide!**

### Phase 2: Create Simplified Agents (Priority: HIGH)
**Estimated Time**: 2-3 hours

```bash
cd backend/infrastructure/agents

# Create simplified_agents.py with:
# 1. Basic agent setup using langgraph
# 2. Simple tool integration
# 3. State management

# Start with just 2-3 agents working:
# - Portfolio Agent (validate, get prices)
# - News Agent (fetch headlines, classify stance)
# - Price Agent (historical replay)
```

**Example pattern** (from design docs):
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

llm = ChatGoogleGenerativeAI(model="gemini-pro")

portfolio_agent = create_react_agent(
    llm,
    tools=[validate_ticker, get_current_price, get_fundamentals],
    prompt=open('backend/prompts/portfolio_agent_prompt.md').read()
)
```

### Phase 3: Minimal FastAPI Backend (Priority: HIGH)
**Estimated Time**: 2 hours

```bash
cd backend

# Create main.py with:
# 1. FastAPI app setup
# 2. Basic endpoints:
#    - POST /portfolio/create
#    - POST /game/start
#    - GET /game/{id}/data
# 3. Simple in-memory state (no database yet)
```

**Example**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/portfolio/create")
async def create_portfolio(tickers: list, allocations: dict):
    # Use domain/portfolio/Portfolio class
    # Call portfolio_agent tools
    pass
```

### Phase 4: Database Setup (Priority: MEDIUM)
**Estimated Time**: 1-2 hours

```bash
cd backend/scripts

# Create init_db.py with Supabase schema from design/implementation_roadmap.md
# Create seed_historical_cases.py to populate price data
```

### Phase 5: Basic Frontend (Priority: MEDIUM)
**Estimated Time**: 4-5 hours

```bash
cd frontend

# Use Next.js 14+ App Router
pnpm create next-app@latest . --typescript --tailwind --app

# Build pages:
# 1. app/portfolio/page.tsx - Portfolio builder
# 2. app/game/[id]/page.tsx - Game UI
# 3. components/game/EventCard.tsx
# 4. components/game/VillainBubble.tsx
# 5. components/game/DataTab.tsx
```

## 🔧 Development Workflow

### Step 1: Setup Environment

```bash
# 1. Copy env.example to .env
cp env.example .env

# 2. Get API keys:
# - Google Gemini: https://makersuite.google.com/app/apikey
# - Tavily: https://tavily.com (1000 free/month)
# - Supabase: https://supabase.com (500MB free)

# 3. Update .env with your keys

# 4. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install
```

### Step 2: Test Tools Individually

```bash
cd backend

# Create test script
python -c "
from infrastructure.agents.tools.portfolio_tools import validate_ticker
import asyncio

async def test():
    result = await validate_ticker.ainvoke('AAPL')
    print(result)

asyncio.run(test())
"
```

### Step 3: Test Agents

```bash
# Once you have agents created:
python -c "
from infrastructure.agents.simplified_agents import portfolio_agent

# Test agent
result = portfolio_agent.invoke({
    'messages': ['Validate ticker AAPL and get its current price']
})
print(result)
"
```

### Step 4: Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000

# Test at http://localhost:8000/docs
```

### Step 5: Run Frontend

```bash
cd frontend
pnpm dev

# Visit http://localhost:3000
```

## 📚 Key Resources

### Design Documents (Your Blueprint)
- `design/implementation_roadmap.md` - **START HERE** for step-by-step instructions
- `design/agent_architecture_and_flow.md` - How agents work together
- `design/langgraph_workflow.md` - Agent implementation details
- `design/tech_stack.md` - All dependencies and versions

### Your Created Files
- `backend/prompts/` - **USE THESE** as agent system prompts
- `backend/domain/` - Business logic ready to use
- `backend/infrastructure/agents/tools/` - Tool implementations (partial)

### MCP Servers (For Help)
- `context7` - Get documentation for libraries (LangChain, LangGraph, etc.)
- `sequentialthinking` - Break down complex problems
- `ref` - Search documentation and examples

## 🎯 Minimal Viable Product (MVP) Checklist

Get this working first, then expand:

- [ ] Portfolio Agent can validate tickers and get prices
- [ ] News Agent can fetch headlines (mock if Tavily not setup)
- [ ] Price Agent can sample historical data (simplified)
- [ ] FastAPI endpoint creates portfolio
- [ ] FastAPI endpoint starts a game round
- [ ] Basic frontend shows portfolio builder
- [ ] Basic frontend displays event + villain take

**Don't worry about**:
- Perfect UI styling
- All 30 tools
- Database persistence
- WebSocket real-time
- Observability

Get the core loop working first!

## 🚀 Next Command to Run

```bash
# Continue from where we left off:
cd backend/infrastructure/agents/tools

# Create price_tools.py (most important for the game)
# Reference: design/agent_architecture_and_flow.md lines 108-158
# Use: backend/prompts/price_agent_prompt.md for guidance

# Then test it:
python -c "
from tools.price_tools import sample_historical_window
import asyncio

async def test():
    result = await sample_historical_window.ainvoke({
        'ticker': 'AAPL',
        'event_type': 'EARNINGS_BEAT',
        'horizon': 3
    })
    print(result)

asyncio.run(test())
"
```

## ❓ Common Questions

**Q: How do I implement a tool?**
A: Use the `@tool` decorator from LangChain. See `portfolio_tools.py` for examples.

**Q: How do I create an agent?**
A: Use `create_react_agent` from LangGraph. See `design/langgraph_workflow.md` for full example.

**Q: Can I test without Tavily/Gemini keys?**
A: Yes! Tools have fallbacks for mock data. Get keys when ready for real functionality.

**Q: How do I know what to build next?**
A: Follow `design/implementation_roadmap.md` Phase 2-3. It has detailed code examples.

## 💡 Tips

1. **Use the prompts** - They're your agent system prompts, already written
2. **Start simple** - Get 1-2 agents working before building all 6
3. **Test incrementally** - Test each tool before building agents
4. **Reference designs** - All answers are in the design/ folder
5. **Ask for help** - Use MCP servers to look up documentation

---

**You have 30% done. The foundation is solid. Keep building! 🚀**

