# 🎮 Market Mayhem

**Portfolio-building game with trash-talking AI and behavioral coaching**

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/Frontend-Next.js-000000)
![AI](https://img.shields.io/badge/AI-Multi--Agent-blueviolet)

---

## 🎯 What is Market Mayhem?

Market Mayhem is an **educational investing game** that uses a **multi-agent AI system** to teach behavioral finance through gameplay. Players face realistic market scenarios while a trash-talking Villain AI tries to induce fear and FOMO. At the end, they receive a personalized behavioral profile and coaching.

### **Key Innovation: Historical Outcome Replay**

Unlike typical trading simulations with random outcomes, Market Mayhem uses **real historical price paths**. Every outcome is based on actual market data, making it both educational and realistic.

---

## ✨ Features

- 🤖 **6 AI Agents** working together (LangGraph + Google Gemini)
- 📈 **Historical Replay** - Real price paths, not random outcomes
- 😈 **Villain AI** - Trash-talking hot takes with cognitive biases
- 🧠 **Behavioral Profiling** - Learn your investing psychology
- 📰 **Real-Time News** - Live headlines via Tavily API
- 📊 **Data Tab** - Consensus, contradiction score, historical outcomes
- 🎨 **Beautiful UI** - Next.js with Tailwind CSS and Framer Motion
- 🔌 **WebSocket** - Real-time game updates
- 📊 **Observability** - Full tracing with Opik + LangSmith

---

## 🏗️ Architecture

### Multi-Agent System (6 Agents)

1. **Event Generator** - Creates realistic market scenarios
2. **Portfolio Agent** - Manages player portfolios
3. **News Agent** - Fetches headlines and computes consensus
4. **Price Agent** - Historical outcome replay (core innovation!)
5. **Villain Agent** - Generates biased hot takes
6. **Insight Agent** - Behavioral profiling and coaching

### Tech Stack

**Backend:**
- FastAPI + WebSocket
- LangGraph (multi-agent orchestration)
- Google Gemini Pro (LLM)
- Tavily (news API)
- yfinance (historical data)
- PostgreSQL (Supabase)

**Frontend:**
- Next.js 14 + TypeScript
- Tailwind CSS
- Framer Motion
- WebSocket client

**Observability:**
- Opik (Comet ML)
- LangSmith

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- API Keys:
  - Google (Gemini Pro)
  - Tavily (news)
  - Supabase (optional)
  - Opik (optional)
  - LangSmith (optional)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/market-mayhem.git
cd market-mayhem
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../env.example .env
# Edit .env and add your API keys

# Run backend
python main.py
```

Backend will start at `http://localhost:8000`

### 3. Setup Frontend

```bash
cd frontend
npm install

# Configure environment  
cp .env.local.example .env.local
# Edit .env.local if needed

# Run frontend
npm run dev
```

Frontend will start at `http://localhost:3000`

### 4. Test

```bash
# Test backend (in project root)
pip install httpx rich
python test_backend.py
```

---

## 🎮 How to Play

1. **Build Your Portfolio**
   - Select 2+ stocks from the ticker universe
   - Allocate your $1,000,000 budget
   - Choose your risk profile (Risk-On, Balanced, Risk-Off)

2. **Play 3 Rounds**
   - Read the market event
   - Listen to the Villain's hot take (intentionally misleading!)
   - (Optional) Open the Data tab to see:
     - Recent headlines with stance (Bull/Bear/Neutral)
     - News consensus
     - Contradiction score (how much Villain contradicts news)
     - Price patterns
     - Historical outcomes for similar events
   - Make your decision: SELL ALL, SELL HALF, HOLD, or BUY
   - See the outcome based on real historical data

3. **Get Your Report**
   - Behavioral profile (Rational / Emotional / Conservative / Balanced)
   - Personalized coaching tips
   - Performance summary

---

## 📂 Project Structure

```
Divhacks2025/
├── backend/
│   ├── domain/              # Pure business logic (DDD)
│   ├── infrastructure/      # Agents, tools, adapters
│   ├── application/         # Use case handlers
│   ├── prompts/            # Agent prompts
│   └── main.py             # FastAPI app
│
├── frontend/
│   ├── app/                # Next.js pages
│   └── components/         # React components
│
├── database/
│   ├── schema.sql          # PostgreSQL schema
│   └── seed_historical_cases.py  # Data seeder
│
├── design/                 # Architecture docs
├── test_backend.py         # Automated tests
└── README.md              # This file
```

---

## 📚 Documentation

- **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Full project summary
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - How to deploy
- **[BACKEND_COMPLETE.md](BACKEND_COMPLETE.md)** - Backend details
- **[design/](design/)** - Architecture and design docs
- **[database/README.md](database/README.md)** - Database setup
- **[backend/infrastructure/observability/README.md](backend/infrastructure/observability/README.md)** - Observability

---

## 🚀 Deployment

### Quick Deploy

**Backend (Render):**
1. Push to GitHub
2. Create new Web Service on Render
3. Connect repo, set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

**Frontend (Vercel):**
```bash
cd frontend
vercel --prod
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## 🧪 Testing

```bash
# Backend unit tests
python test_backend.py

# Frontend tests
cd frontend
npm test

# End-to-end test
# 1. Start backend: python backend/main.py
# 2. Start frontend: cd frontend && npm run dev
# 3. Open http://localhost:3000
# 4. Play through a complete game
```

---

## 🎯 Core Innovation

### Historical Outcome Replay

Most trading games use random price movements. Market Mayhem is different:

1. **Real Historical Data** - Every outcome uses actual price paths from yfinance
2. **Matching Algorithm** - Finds similar historical cases by ticker, event type, and horizon
3. **Educational** - Players see what really happened in similar scenarios
4. **No RNG** - Outcomes are deterministic based on historical data

Example:
- Event: "Apple reports Q4 earnings beat of 15%"
- System finds: Actual Apple earnings beat from 2023-05-15
- Applies player decision to real price path from that date
- Shows actual 3-day outcome (+4.28% in this case)

---

## 🤖 Multi-Agent System

The game uses **6 specialized ReAct agents** orchestrated by LangGraph:

```
┌──────────────┐
│  Supervisor  │
└──────┬───────┘
       │
   ┌───┴────┐
   │ Agents │
   └────────┘
      ├─ Event Generator (creates scenarios)
      ├─ Portfolio Agent (manages positions)
      ├─ News Agent (fetches headlines)
      ├─ Price Agent (historical replay)
      ├─ Villain Agent (trash-talking)
      └─ Insight Agent (coaching)
```

Each agent has specialized tools and prompts. The supervisor coordinates them to create the complete game experience.

---

## 📊 Status

**Implementation: 100% Complete** ✅

- ✅ Backend (FastAPI + LangGraph)
- ✅ Frontend (Next.js + TypeScript)
- ✅ Database schema (PostgreSQL)
- ✅ All 6 AI agents
- ✅ Historical replay system
- ✅ WebSocket real-time updates
- ✅ Observability (Opik + LangSmith)
- ✅ Full documentation
- ✅ Deployment guides
- ✅ Testing scripts

---

## 🤝 Contributing

This project is complete and production-ready. Feel free to fork and adapt for your own use!

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🎓 Learning Resources

Built using concepts from:
- **Behavioral Finance** - Cognitive biases in investing
- **Domain-Driven Design** - Clean architecture
- **Multi-Agent Systems** - LangGraph orchestration
- **ReAct Agents** - Reasoning and acting with LLMs

---

## 🌟 Credits

**Developed for DivHacks 2025**

Built with:
- LangGraph & LangChain
- Google Gemini Pro
- FastAPI
- Next.js
- Tavily API
- yfinance
- Opik (Comet ML)
- LangSmith

---

## 📧 Contact

Questions or feedback? Open an issue or reach out!

---

**Ready to play? Deploy now and face the Villain AI!** 🎮🤖

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) to get started!