"""Multi-Agent Game Graph - Orchestrates all 6 agents"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GEMINI_MODEL, TEMPERATURE_SUPERVISOR

from .event_generator_agent import event_generator_agent
from .portfolio_agent import portfolio_agent
from .news_agent import news_agent
from .price_agent import price_agent
from .villain_agent import villain_agent
from .insight_agent import insight_agent

# Note: All agents are now direct async functions (not ReAct agents)
# Each agent makes at most 1 Gemini API call
# Total: ~4 API calls per round (Event, Villain, Insight, + 0 supervisor overhead)


# Define Game State
class GameState(TypedDict):
    """State shared across all agents in the game"""
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Game context
    game_id: str
    portfolio_id: str
    round_number: int
    
    # Portfolio data
    portfolio: dict  # {ticker: position_size}
    portfolio_value: float
    
    # Event data
    selected_ticker: str
    event_type: str
    event_description: str
    event_horizon: int
    
    # News data
    headlines: list[dict]
    consensus: str
    contradiction_score: float
    
    # Price data
    price_snapshot: dict
    price_pattern: str
    historical_case: dict
    
    # Villain data
    villain_stance: str
    villain_bias: str
    villain_hot_take: str
    
    # Insight data
    neutral_tip: str
    
    # Decision tracking
    player_decision: str
    decision_time: float
    opened_data_tab: bool
    
    # Outcome
    outcome: dict
    pl_dollars: float
    pl_percent: float
    
    # Control flow
    next_agent: str
    task: str  # round_start, decision_submitted, round_end, game_end


def create_supervisor_node(llm: ChatGoogleGenerativeAI):
    """
    Create supervisor node that routes to appropriate agents.
    
    The supervisor orchestrates the game flow by routing to agents in sequence.
    """
    def supervisor_node(state: GameState) -> GameState:
        """
        Route to next agent based on task and current state.
        
        Game flow:
        1. round_start -> event_generator
        2. event_generator -> portfolio, news, price, villain, insight (parallel)
        3. All agents complete -> END (wait for player decision)
        4. decision_submitted -> price (calculate outcome)
        5. price complete -> insight (track behavior)
        6. insight complete -> END
        """
        task = state.get("task", "round_start")
        
        # Round start: Generate event
        if task == "round_start":
            return {**state, "next_agent": "event_generator"}
        
        # Event generated: Fetch all round data
        elif task == "event_generated":
            # In a real implementation, we'd run these in parallel
            # For MVP, we'll run sequentially: portfolio -> news -> price -> villain -> insight
            if not state.get("price_snapshot"):
                return {**state, "next_agent": "price", "task": "fetching_data"}
            elif not state.get("headlines"):
                return {**state, "next_agent": "news", "task": "fetching_data"}
            elif not state.get("villain_hot_take"):
                return {**state, "next_agent": "villain", "task": "fetching_data"}
            elif not state.get("neutral_tip"):
                return {**state, "next_agent": "insight", "task": "fetching_data"}
            else:
                return {**state, "next_agent": "END", "task": "round_complete"}
        
        # Fetching data: Continue with next agent
        elif task == "fetching_data":
            # Continue with the same logic as event_generated
            if not state.get("price_snapshot"):
                return {**state, "next_agent": "price", "task": "fetching_data"}
            elif not state.get("headlines"):
                return {**state, "next_agent": "news", "task": "fetching_data"}
            elif not state.get("villain_hot_take"):
                return {**state, "next_agent": "villain", "task": "fetching_data"}
            elif not state.get("neutral_tip"):
                return {**state, "next_agent": "insight", "task": "fetching_data"}
            else:
                return {**state, "next_agent": "END", "task": "round_complete"}
        
        # Player made decision: Calculate outcome
        elif task == "decision_submitted":
            return {**state, "next_agent": "price"}
        
        # Outcome calculated: Track behavior
        elif task == "outcome_calculated":
            return {**state, "next_agent": "insight"}
        
        # Round complete
        elif task == "round_complete":
            return {**state, "next_agent": "END"}
        
        # Game complete
        elif task == "game_complete":
            return {**state, "next_agent": "END"}
        
        # Default: end
        else:
            return {**state, "next_agent": "END"}
    
    return supervisor_node


# Create supervisor LLM
supervisor_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_SUPERVISOR)

# Create supervisor node
supervisor = create_supervisor_node(supervisor_llm)


def create_game_graph():
    """
    Create and compile the multi-agent game graph.
    
    Returns:
        Compiled LangGraph
    """
    workflow = StateGraph(GameState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("event_generator", event_generator_agent)
    workflow.add_node("portfolio", portfolio_agent)
    workflow.add_node("news", news_agent)
    workflow.add_node("price", price_agent)
    workflow.add_node("villain", villain_agent)
    workflow.add_node("insight", insight_agent)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Supervisor conditional routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_agent", "END"),
        {
            "event_generator": "event_generator",
            "portfolio": "portfolio",
            "news": "news",
            "price": "price",
            "villain": "villain",
            "insight": "insight",
            "END": END
        }
    )
    
    # All agents return to supervisor
    for agent_name in ["event_generator", "portfolio", "news", "price", "villain", "insight"]:
        workflow.add_edge(agent_name, "supervisor")
    
    return workflow.compile()


# Create the game graph instance
game_graph = create_game_graph()


# Helper function to invoke graph for round start
async def start_round(
    game_id: str,
    portfolio_id: str,
    round_number: int,
    portfolio: dict,
    portfolio_value: float
) -> dict:
    """
    Start a new game round.
    
    Args:
        game_id: Game session ID
        portfolio_id: Portfolio ID
        round_number: Current round number
        portfolio: Portfolio positions {ticker: size}
        portfolio_value: Total portfolio value
        
    Returns:
        Round data with event, villain take, news, data tab
    """
    initial_state = {
        "messages": [
            HumanMessage(content=f"Start round {round_number}. Portfolio: {portfolio}. Portfolio value: ${portfolio_value:,.2f}. Generate a new market event scenario.")
        ],
        "game_id": game_id,
        "portfolio_id": portfolio_id,
        "round_number": round_number,
        "portfolio": portfolio,
        "portfolio_value": portfolio_value,
        "task": "round_start",
        "next_agent": "supervisor"
    }
    
    result = await game_graph.ainvoke(initial_state)
    
    return {
        "event": {
            "ticker": result.get("selected_ticker"),
            "type": result.get("event_type"),
            "description": result.get("event_description"),
            "horizon": result.get("event_horizon")
        },
        "villain_take": {
            "text": result.get("villain_hot_take"),
            "stance": result.get("villain_stance"),
            "bias": result.get("villain_bias")
        },
        "data_tab": {
            "headlines": result.get("headlines", []),
            "consensus": result.get("consensus"),
            "contradiction_score": result.get("contradiction_score"),
            "price_pattern": result.get("price_pattern"),
            "neutral_tip": result.get("neutral_tip"),
            "historical_outcomes": result.get("historical_outcomes", {})
        }
    }


# Helper function to process player decision
async def process_decision(
    game_id: str,
    round_number: int,
    player_decision: str,
    decision_time: float,
    opened_data_tab: bool,
    historical_case: dict,
    position_size: float
) -> dict:
    """
    Process player decision and calculate outcome.
    
    Args:
        game_id: Game session ID
        round_number: Current round number
        player_decision: SELL_ALL, SELL_HALF, HOLD, or BUY
        decision_time: Time taken to decide (seconds)
        opened_data_tab: Whether player opened data tab
        historical_case: Historical case to apply decision to
        position_size: Current position size
        
    Returns:
        Outcome data with P/L and behavior tracking
    """
    initial_state = {
        "messages": [
            HumanMessage(content=f"Player decision: {player_decision}. Decision time: {decision_time:.2f}s. Opened data tab: {opened_data_tab}. Calculate outcome based on historical case.")
        ],
        "game_id": game_id,
        "round_number": round_number,
        "player_decision": player_decision,
        "decision_time": decision_time,
        "opened_data_tab": opened_data_tab,
        "historical_case": historical_case,
        "task": "decision_submitted",
        "next_agent": "supervisor"
    }
    
    result = await game_graph.ainvoke(initial_state)
    
    return {
        "outcome": result.get("outcome"),
        "pl_dollars": result.get("pl_dollars"),
        "pl_percent": result.get("pl_percent"),
        "behavior_flags": result.get("behavior_flags", [])
    }

