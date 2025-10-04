# Fix Python path to allow imports from project root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables FIRST (before any imports that need API keys)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json

# Import application handlers (these import agents which need API keys)
from backend.application.portfolio.create_portfolio_handler import CreatePortfolioHandler
from backend.application.game.start_game_handler import StartGameHandler
from backend.application.game.start_round_handler import StartRoundHandler
from backend.application.game.submit_decision_handler import SubmitDecisionHandler
from backend.application.game.generate_final_report_handler import GenerateFinalReportHandler

# Import observability
try:
    from backend.infrastructure.observability import setup_opik, setup_langsmith
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    print("⚠️  Observability modules not available. Install opik and langsmith for full observability.")

# Create FastAPI app
app = FastAPI(
    title="Market Mayhem API",
    description="Portfolio-building game with multi-agent AI system",
    version="1.0.0"
)

# Setup observability on startup
@app.on_event("startup")
async def startup_event():
    """Initialize observability on application startup"""
    print("\n" + "="*60)
    print("Market Mayhem API Starting...")
    print("="*60 + "\n")
    
    if OBSERVABILITY_AVAILABLE:
        print("Setting up observability...")
        opik_enabled = setup_opik()
        langsmith_enabled = setup_langsmith()
        
        if opik_enabled or langsmith_enabled:
            print("\nObservability configured successfully!")
        else:
            print("\nObservability not enabled (API keys not set)")
    
    print("\n" + "="*60)
    print("API Ready at http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    print("="*60 + "\n")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dependency Injection ===

# Initialize handlers
create_portfolio_handler = CreatePortfolioHandler()
start_game_handler = StartGameHandler()
start_round_handler = StartRoundHandler()
submit_decision_handler = SubmitDecisionHandler()
generate_final_report_handler = GenerateFinalReportHandler()


# === Request/Response Models ===

class CreatePortfolioRequest(BaseModel):
    player_id: str
    tickers: List[str]
    allocations: Dict[str, float]
    risk_profile: str = "Balanced"


class StartGameRequest(BaseModel):
    portfolio_id: str


class SubmitDecisionRequest(BaseModel):
    game_id: str
    round_number: int
    player_decision: str  # SELL_ALL, SELL_HALF, HOLD, BUY
    decision_time: float
    opened_data_tab: bool


# === Endpoints ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Market Mayhem API",
        "version": "1.0.0",
        "agents": ["Event Generator", "Portfolio", "News", "Price", "Villain", "Insight"]
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY")),
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "redis_configured": bool(os.getenv("REDIS_URL"))
    }


@app.get("/tickers")
async def get_ticker_universe():
    """Get available tickers for portfolio building"""
    tickers = os.getenv("TICKER_UNIVERSE", "AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,JPM,V,WMT").split(",")
    return {
        "tickers": tickers,
        "count": len(tickers)
    }


# === Portfolio Endpoints ===

@app.post("/portfolio/create")
async def create_portfolio(request: CreatePortfolioRequest):
    """
    Create a new portfolio (Round 0)
    
    This endpoint:
    1. Validates tickers
    2. Fetches current prices
    3. Creates Portfolio aggregate
    4. Returns portfolio ID for game start
    """
    try:
        result = await create_portfolio_handler.execute(
            player_id=request.player_id,
            tickers=request.tickers,
            allocations=request.allocations,
            risk_profile=request.risk_profile
        )
        
        return {
            "success": True,
            "portfolio": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get portfolio details"""
    # TODO: Implement repository fetch
    return {
        "portfolio_id": portfolio_id,
        "message": "Portfolio retrieval not yet implemented"
    }


# === Game Endpoints ===

@app.post("/game/start")
async def start_game(request: StartGameRequest):
    """
    Start a new game session
    
    Creates game session record and initializes round counter.
    """
    try:
        result = await start_game_handler.execute(
            portfolio_id=request.portfolio_id
        )
        
        return {
            "success": True,
            "game": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/game/{game_id}/round/{round_number}/start")
async def start_round(game_id: str, round_number: int):
    """
    Start a new game round
    
    Invokes multi-agent graph to generate:
    - Event (Event Generator Agent)
    - News headlines + consensus (News Agent)
    - Price data + pattern (Price Agent)
    - Villain hot take (Villain Agent)
    - Neutral tip (Insight Agent)
    """
    try:
        result = await start_round_handler.execute(
            game_id=game_id,
            round_number=round_number
        )
        
        return {
            "success": True,
            "round": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/decision")
async def submit_decision(request: SubmitDecisionRequest):
    """
    Submit player decision
    
    Invokes multi-agent graph to:
    1. Calculate outcome using historical replay (Price Agent)
    2. Track behavioral patterns (Insight Agent)
    """
    try:
        result = await submit_decision_handler.execute(
            game_id=request.game_id,
            round_number=request.round_number,
            player_decision=request.player_decision,
            decision_time=request.decision_time,
            opened_data_tab=request.opened_data_tab
        )
        
        return {
            "success": True,
            "outcome": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{game_id}/report")
async def get_final_report(game_id: str):
    """
    Generate final game report
    
    Returns:
    - Behavioral profile
    - Personalized coaching
    - Summary stats
    """
    try:
        result = await generate_final_report_handler.execute(game_id=game_id)
        
        return {
            "success": True,
            "report": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === WebSocket for Real-time Game Communication ===

@app.websocket("/game/{game_id}/ws")
async def game_websocket(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for real-time game communication
    
    Client sends:
    {
        "type": "start_round",
        "round_number": 1
    }
    
    {
        "type": "submit_decision",
        "decision": "HOLD",
        "decision_time": 15.5,
        "opened_data_tab": true
    }
    
    Server sends:
    {
        "type": "round_started",
        "data": {...}
    }
    
    {
        "type": "outcome",
        "data": {...}
    }
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "start_round":
                # Start new round
                round_number = data.get("round_number", 1)
                
                round_result = await start_round_handler.execute(
                    game_id=game_id,
                    round_number=round_number
                )
                
                await websocket.send_json({
                    "type": "round_started",
                    "data": round_result
                })
            
            elif message_type == "submit_decision":
                # Submit decision and get outcome
                decision_result = await submit_decision_handler.execute(
                    game_id=game_id,
                    round_number=data.get("round_number", 1),
                    player_decision=data.get("decision"),
                    decision_time=data.get("decision_time", 0),
                    opened_data_tab=data.get("opened_data_tab", False)
                )
                
                await websocket.send_json({
                    "type": "outcome",
                    "data": decision_result
                })
            
            elif message_type == "get_report":
                # Generate final report
                report_result = await generate_final_report_handler.execute(game_id=game_id)
                
                await websocket.send_json({
                    "type": "final_report",
                    "data": report_result
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        print(f"Client disconnected from game {game_id}")
    except Exception as e:
        print(f"WebSocket error for game {game_id}: {str(e)}")
        await websocket.close(code=1011, reason=str(e))


# === Development Info Endpoints ===

@app.get("/agents")
async def list_agents():
    """List all agents and their responsibilities"""
    return {
        "agents": [
            {
                "name": "Event Generator Agent",
                "role": "Create realistic market event scenarios",
                "tools": 5,
                "prompt": "backend/prompts/event_generator_agent_prompt.md"
            },
            {
                "name": "Portfolio Agent",
                "role": "Manage portfolios and positions",
                "tools": 4,
                "prompt": "backend/prompts/portfolio_agent_prompt.md"
            },
            {
                "name": "News Agent",
                "role": "Fetch and analyze headlines",
                "tools": 4,
                "prompt": "backend/prompts/news_agent_prompt.md"
            },
            {
                "name": "Price Agent",
                "role": "Historical outcome replay",
                "tools": 6,
                "prompt": "backend/prompts/price_agent_prompt.md"
            },
            {
                "name": "Villain Agent",
                "role": "Generate biased hot takes",
                "tools": 4,
                "prompt": "backend/prompts/villain_agent_prompt.md"
            },
            {
                "name": "Insight Agent",
                "role": "Behavioral profiling and coaching",
                "tools": 5,
                "prompt": "backend/prompts/insight_agent_prompt.md"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

