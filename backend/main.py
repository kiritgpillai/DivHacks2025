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

# Initialize Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_AVAILABLE = True
        print("✅ Supabase client initialized")
    else:
        supabase = None
        SUPABASE_AVAILABLE = False
        print("⚠️  SUPABASE_URL or SUPABASE_KEY not set. Using in-memory storage.")
except ImportError:
    supabase = None
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase package not installed. Run: pip install supabase")

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

# In-memory storage for MVP (replace with database in production)
# Key: game_id, Value: {"portfolio_id": str, "portfolio": dict, "portfolio_value": float}
game_sessions_store = {}
# Key: portfolio_id, Value: {"positions": dict, "total_value": float, "risk_profile": str}
portfolios_store = {}

# Initialize handlers with Supabase client
create_portfolio_handler = CreatePortfolioHandler(supabase_client=supabase if SUPABASE_AVAILABLE else None)
start_game_handler = StartGameHandler(supabase_client=supabase if SUPABASE_AVAILABLE else None)
start_round_handler = StartRoundHandler()
submit_decision_handler = SubmitDecisionHandler(supabase_client=supabase if SUPABASE_AVAILABLE else None)
generate_final_report_handler = GenerateFinalReportHandler(supabase_client=supabase if SUPABASE_AVAILABLE else None)


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
        
        # Store portfolio in memory for MVP
        portfolio_id = result["portfolio_id"]
        portfolios_store[portfolio_id] = {
            "positions": request.allocations,  # {ticker: allocation_dollars}
            "total_value": result["total_value"],
            "risk_profile": request.risk_profile,
            "player_id": request.player_id
        }
        
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
    Integrates with Supabase for persistence and Opik for observability.
    """
    try:
        # Validate portfolio exists (check Supabase first, then in-memory)
        if SUPABASE_AVAILABLE:
            # Validate in Supabase
            portfolio_check = supabase.table("portfolios").select("id").eq("id", request.portfolio_id).execute()
            if not portfolio_check.data or len(portfolio_check.data) == 0:
                raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        else:
            # Validate in memory
            if request.portfolio_id not in portfolios_store:
                raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        
        # Start game (handler saves to Supabase if available)
        result = await start_game_handler.execute(
            portfolio_id=request.portfolio_id
        )
        
        game_id = result["game_id"]
        
        # Cache game session in memory for fast access
        # This ensures dynamic portfolio data flows through the entire game
        if SUPABASE_AVAILABLE:
            # Fetch dynamic portfolio data from Supabase
            portfolio_data = supabase.table("portfolios").select("*").eq("id", request.portfolio_id).execute()
            positions_data = supabase.table("positions").select("*").eq("portfolio_id", request.portfolio_id).execute()
            
            if not portfolio_data.data or len(portfolio_data.data) == 0:
                raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found in database")
            
            # Build dynamic portfolio dict from user's actual positions
            portfolio_dict = {}
            for pos in positions_data.data:
                portfolio_dict[pos["ticker"]] = float(pos["allocation"])
            
            game_sessions_store[game_id] = {
                "portfolio_id": request.portfolio_id,
                "portfolio": portfolio_dict,  # DYNAMIC: User's actual tickers and allocations
                "portfolio_value": float(portfolio_data.data[0]["total_value"]),
                "risk_profile": portfolio_data.data[0]["risk_profile"],
                "current_round": 0
            }
        else:
            # Use in-memory data (fallback)
            portfolio = portfolios_store[request.portfolio_id]
            game_sessions_store[game_id] = {
                "portfolio_id": request.portfolio_id,
                "portfolio": portfolio["positions"],  # DYNAMIC: User's actual tickers
                "portfolio_value": portfolio["total_value"],
                "risk_profile": portfolio["risk_profile"],
                "current_round": 0
            }
        
        return {
            "success": True,
            "game": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/game/{game_id}/round/{round_number}/start")
async def start_round(game_id: str, round_number: int):
    """
    Start a new game round
    
    Invokes multi-agent graph to generate:
    - Event (Event Generator Agent) - uses DYNAMIC portfolio tickers
    - News headlines + consensus (News Agent)
    - Price data + pattern (Price Agent)
    - Villain hot take (Villain Agent)
    - Neutral tip (Insight Agent)
    
    All agents receive the user's actual portfolio (NO hardcoded tickers).
    """
    try:
        # Validate game session exists
        if game_id not in game_sessions_store:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
        # Fetch DYNAMIC game session data (user's actual portfolio)
        game_session = game_sessions_store[game_id]
        
        # Log round start to Opik
        try:
            from backend.infrastructure.observability.opik_tracer import log_game_event
            log_game_event("round_start", {
                "game_id": game_id,
                "round_number": round_number,
                "portfolio": game_session["portfolio"],  # DYNAMIC: User's actual tickers
                "portfolio_value": game_session["portfolio_value"],
                "supabase_enabled": SUPABASE_AVAILABLE
            })
        except Exception as e:
            print(f"Warning: Failed to log round start to Opik: {e}")
        
        # Execute round with DYNAMIC portfolio (user's actual tickers)
        result = await start_round_handler.execute(
            game_id=game_id,
            round_number=round_number,
            portfolio=game_session["portfolio"],        # DYNAMIC: User's tickers
            portfolio_value=game_session["portfolio_value"]
        )
        
        # Store round data for decision submission
        # This ensures the decision endpoint knows which ticker was selected
        event = result["event"]
        villain_take = result.get("villain_take", {})
        
        game_session[f"round_{round_number}_data"] = {
            "ticker": event["ticker"],  # DYNAMIC: Ticker selected from user's portfolio
            "event_data": {
                "type": event["type"],
                "description": event["description"],
                "horizon": event["horizon"],
                "villain_stance": villain_take.get("stance", "Bullish"),
                "villain_bias": villain_take.get("bias", "Unknown"),
                "villain_hot_take": villain_take.get("text", "")
            }
        }
        
        # Log round completion to Opik
        try:
            log_game_event("round_completed", {
                "game_id": game_id,
                "round_number": round_number,
                "event_ticker": event["ticker"],  # DYNAMIC: User's ticker
                "event_type": event["type"],
                "supabase_enabled": SUPABASE_AVAILABLE
            })
        except Exception as e:
            print(f"Warning: Failed to log round completion to Opik: {e}")
        
        return {
            "success": True,
            "round": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/decision")
async def submit_decision(request: SubmitDecisionRequest):
    """
    Submit player decision
    
    Invokes multi-agent graph to:
    1. Update portfolio in Supabase (UpdatePortfolioHandler)
    2. Calculate outcome using historical replay (Price Agent)
    3. Store round outcome to Supabase (game_rounds table)
    4. Track behavioral patterns (Insight Agent)
    
    Uses DYNAMIC ticker from the round event (user's actual portfolio).
    """
    try:
        # Validate game session exists
        if request.game_id not in game_sessions_store:
            raise HTTPException(status_code=404, detail=f"Game {request.game_id} not found")
        
        game_session = game_sessions_store[request.game_id]
        
        # Get DYNAMIC round data (ticker selected from user's portfolio)
        round_data = game_session.get(f"round_{request.round_number}_data", {})
        ticker = round_data.get("ticker")
        event_data = round_data.get("event_data")
        
        if not ticker:
            raise HTTPException(
                status_code=400, 
                detail=f"Round {request.round_number} data not found. Start the round first."
            )
        
        # Get current price for the DYNAMIC ticker
        from backend.infrastructure.yfinance_adapter.price_fetcher import get_current_price
        try:
            current_price = await get_current_price(ticker)
        except Exception as e:
            print(f"Warning: Failed to fetch price for {ticker}: {e}")
            # Use a fallback price (should rarely happen)
            current_price = 100.0
        
        # Submit decision with DYNAMIC ticker and all required data
        result = await submit_decision_handler.execute(
            game_id=request.game_id,
            round_number=request.round_number,
            player_decision=request.player_decision,
            decision_time=request.decision_time,
            opened_data_tab=request.opened_data_tab,
            portfolio_id=game_session["portfolio_id"],  # For Supabase updates
            ticker=ticker,                              # DYNAMIC: User's ticker
            new_price=current_price,                    # Current market price
            event_data=event_data                       # Event context for storage
        )
        
        # Update game session cache with new portfolio values
        if result.get("portfolio"):
            game_session["portfolio_value"] = result["portfolio"]["new_total_value"]
            
            # Update DYNAMIC portfolio allocations
            game_session["portfolio"] = {
                pos["ticker"]: pos["allocation"] 
                for pos in result["portfolio"]["positions"]
            }
        
        return {
            "success": True,
            "outcome": result
        }
        
    except HTTPException:
        raise
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
                
                # Fetch game session data
                if game_id not in game_sessions_store:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Game {game_id} not found"
                    })
                    continue
                
                game_session = game_sessions_store[game_id]
                
                # Log round start to Opik
                try:
                    from backend.infrastructure.observability.opik_tracer import log_game_event
                    log_game_event("round_start", {
                        "game_id": game_id,
                        "round_number": round_number,
                        "portfolio": game_session["portfolio"],
                        "portfolio_value": game_session["portfolio_value"],
                        "supabase_enabled": SUPABASE_AVAILABLE,
                        "via": "websocket"
                    })
                except Exception as e:
                    print(f"Warning: Failed to log round start to Opik: {e}")
                
                # Execute round with DYNAMIC portfolio
                round_result = await start_round_handler.execute(
                    game_id=game_id,
                    round_number=round_number,
                    portfolio=game_session["portfolio"],
                    portfolio_value=game_session["portfolio_value"]
                )
                
                # Store round data for decision submission
                event = round_result["event"]
                villain_take = round_result.get("villain_take", {})
                
                game_session[f"round_{round_number}_data"] = {
                    "ticker": event["ticker"],  # DYNAMIC: Ticker from user's portfolio
                    "event_data": {
                        "type": event["type"],
                        "description": event["description"],
                        "horizon": event["horizon"],
                        "villain_stance": villain_take.get("stance", "Bullish"),
                        "villain_bias": villain_take.get("bias", "Unknown"),
                        "villain_hot_take": villain_take.get("text", "")
                    }
                }
                
                # Log round completion to Opik
                try:
                    log_game_event("round_completed", {
                        "game_id": game_id,
                        "round_number": round_number,
                        "event_ticker": event["ticker"],
                        "event_type": event["type"],
                        "supabase_enabled": SUPABASE_AVAILABLE,
                        "via": "websocket"
                    })
                except Exception as e:
                    print(f"Warning: Failed to log round completion to Opik: {e}")
                
                await websocket.send_json({
                    "type": "round_started",
                    "data": round_result
                })
            
            elif message_type == "submit_decision":
                # Submit decision and get outcome
                # Fetch game session and round data
                if game_id not in game_sessions_store:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Game {game_id} not found"
                    })
                    continue
                
                game_session = game_sessions_store[game_id]
                round_number = data.get("round_number", 1)
                
                # Get DYNAMIC round data (ticker from user's portfolio)
                round_data = game_session.get(f"round_{round_number}_data", {})
                ticker = round_data.get("ticker")
                event_data = round_data.get("event_data")
                
                if not ticker:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Round {round_number} data not found. Start the round first."
                    })
                    continue
                
                # Get current price for the DYNAMIC ticker
                from backend.infrastructure.yfinance_adapter.price_fetcher import get_current_price
                try:
                    current_price = await get_current_price(ticker)
                except Exception as e:
                    print(f"Warning: Failed to fetch price for {ticker}: {e}")
                    current_price = 100.0
                
                # Submit decision with all required parameters
                decision_result = await submit_decision_handler.execute(
                    game_id=game_id,
                    round_number=round_number,
                    player_decision=data.get("decision"),
                    decision_time=data.get("decision_time", 0),
                    opened_data_tab=data.get("opened_data_tab", False),
                    portfolio_id=game_session["portfolio_id"],  # For Supabase updates
                    ticker=ticker,                              # DYNAMIC: User's ticker
                    new_price=current_price,                    # Current market price
                    event_data=event_data                       # Event context for storage
                )
                
                # Update game session cache with new portfolio values
                if decision_result.get("portfolio"):
                    game_session["portfolio_value"] = decision_result["portfolio"]["new_total_value"]
                    
                    # Update DYNAMIC portfolio allocations
                    game_session["portfolio"] = {
                        pos["ticker"]: pos["allocation"] 
                        for pos in decision_result["portfolio"]["positions"]
                    }
                
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
        # Truncate error message to fit in WebSocket control frame (max 125 bytes)
        error_msg = str(e)[:100]
        await websocket.close(code=1011, reason=error_msg)


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

