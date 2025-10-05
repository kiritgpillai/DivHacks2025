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
        
        NOTE: Decision processing is handled directly by SubmitDecisionHandler,
        NOT through the agent graph. If decision tasks reach here, it's a bug.
        """
        print(f"🚨 SUPERVISOR CALLED: task='{state.get('task', 'round_start')}', next_agent='{state.get('next_agent', 'END')}'")
        task = state.get("task", "round_start")
        
        # GUARD: Prevent decision processing through agent graph
        if task in ["decision_submitted", "outcome_calculated"]:
            print(f"⚠️ CRITICAL: Agent graph invoked with task='{task}' - this is a bug!")
            print("⚠️ Decision processing should use SubmitDecisionHandler directly")
            print(f"⚠️ State: {state}")
            print(f"⚠️ Returning END to stop recursion")
            return {**state, "next_agent": "END"}
        
        print(f"🔍 Supervisor called with task='{task}', next_agent='{state.get('next_agent', 'END')}'")
        
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
        
        # Decision processing is DISABLED - handled directly by SubmitDecisionHandler
        # If this code is reached, it means there's a bug where the agent graph
        # is being invoked for decision processing when it shouldn't be
        elif task == "decision_submitted":
            print("⚠️ WARNING: Agent graph invoked for decision_submitted - this should not happen!")
            print("⚠️ Decision processing should use SubmitDecisionHandler directly")
            return {**state, "next_agent": "END"}
        
        # Outcome calculated: Track behavior (DISABLED)
        elif task == "outcome_calculated":
            print("⚠️ WARNING: Agent graph invoked for outcome_calculated - this should not happen!")
            return {**state, "next_agent": "END"}
        
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


# NOTE: Decision processing is now handled directly by SubmitDecisionHandler
# This function has been removed to prevent GraphRecursionError
# The WebSocket handler uses submit_decision_handler.execute() directly

