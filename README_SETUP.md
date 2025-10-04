# Market Mayhem - Setup Guide

## 🎯 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm (recommended) or npm

### 1. Clone and Install

```bash
# Install all dependencies
npm run install:all

# Or manually:
npm install
cd frontend && pnpm install
cd ../backend && pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy example env file
cp .env.example .env

# Update with your API keys:
# - GOOGLE_API_KEY (https://makersuite.google.com/app/apikey)
# - TAVILY_API_KEY (https://tavily.com)
# - DATABASE_URL (https://supabase.com)
# - REDIS_URL (https://upstash.com)
# - OPIK_API_KEY (https://www.comet.com/signup)
```

### 3. Database Setup

```bash
# Create Supabase tables
cd backend
python scripts/init_db.py

# Seed historical cases (optional but recommended)
python scripts/seed_historical_cases.py
```

### 4. Run Development Servers

```bash
# From project root:
npm run dev

# This runs both:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🏗️ Project Structure

```
market-mayhem/
├── frontend/                 # Next.js 14+ frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   └── lib/                 # Utilities
├── backend/                 # FastAPI backend
│   ├── domain/              # Pure business logic
│   ├── application/         # Use case handlers
│   ├── infrastructure/      # Agents, tools, external services
│   ├── adapters/            # HTTP/WebSocket controllers
│   └── prompts/             # All agent prompts
├── design/                  # Design documents
├── package.json             # Root package.json
└── .env.example             # Environment template
```

## 🤖 Multi-Agent System

This project uses **6 specialized ReAct agents**:

1. **Event Generator Agent** - Creates market scenarios
2. **Portfolio Agent** - Manages portfolios and positions
3. **News Agent** - Fetches headlines and detects stance
4. **Price Agent** - Historical outcome replay
5. **Villain Agent** - Generates biased hot takes
6. **Insight Agent** - Behavioral profiling and coaching

## 📚 Documentation

- [Software Architecture](design/software_architecture.md)
- [Agent Architecture](design/agent_architecture_and_flow.md)
- [Implementation Roadmap](design/implementation_roadmap.md)
- [Development Guide](design/DEVELOPMENT_GUIDE.md)

## 🎮 Game Flow

1. **Round 0**: Build portfolio ($1M, 3-6 stocks)
2. **Rounds 1-7**: Event → Villain Take → Data Tab → Decision
3. **Final Report**: Behavioral profile + coaching

## 🔧 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Verify all env vars are set in `.env`
- Check port 8000 is not in use

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Clear Next.js cache: `rm -rf frontend/.next`
- Reinstall dependencies: `cd frontend && pnpm install`

### Database connection fails
- Verify Supabase credentials
- Check DATABASE_URL format
- Run migrations: `python backend/scripts/init_db.py`

## 📦 Free Tier Services

All services have generous free tiers:
- **Vercel**: Unlimited frontend hosting
- **Render**: 750h/month backend
- **Supabase**: 500MB database
- **Upstash Redis**: 10K commands/day
- **Tavily**: 1000 requests/month
- **Google Gemini**: Free tier with rate limits
- **Opik**: Free LLM observability

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel deploy
```

### Backend (Render)
- Connect GitHub repo
- Set environment variables
- Deploy from `backend/` directory

## 📊 Observability

- **Opik Dashboard**: https://www.comet.com/site/products/opik/
- **LangSmith**: https://smith.langchain.com (optional)

## 🤝 Contributing

This is a hackathon project for DivHacks 2025. Built with LangGraph multi-agent system!

