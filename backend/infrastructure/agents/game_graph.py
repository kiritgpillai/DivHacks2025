"""Multi-Agent Game Graph - Orchestrates all 6 agents"""

from typing import TypedDict, Annotated, Literal, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GEMINI_MODEL, TEMPERATURE_SUPERVISOR

from .event_generator_agent import event_generator_agent
from .portfolio_agent import portfolio_agent
from .news_agent import news_agent
from .price_agent import price_agent
from .villain_agent import villain_agent
from .insight_agent import insight_agent


def _extract_last_tool_json(messages: list[BaseMessage], tool_name: str) -> Any | None:
    """Scan messages (from newest) and return JSON-decoded content of the last ToolMessage for `tool_name`."""
    for m in reversed(messages):
        if isinstance(m, ToolMessage):
            # Some providers include `name` on ToolMessage; fall back to content sniff if not present.
            if getattr(m, "name", None) == tool_name:
                try:
                    import json
                    return json.loads(m.content)
                except Exception:
                    return None
    return None


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
    current_step: int  # Track progress through the flow


def create_supervisor_node(llm: ChatGoogleGenerativeAI):
    """
    Create supervisor node that routes to appropriate agents.
    
    The supervisor orchestrates the game flow by routing to agents in sequence.
    Fixed to prevent recursion by using step tracking.
    """
    def supervisor_node(state: GameState) -> GameState:
        """
        Route to next agent based on task and current state.
        
        Game flow:
        1. round_start -> event_generator
        2. event_generator -> price -> news -> villain -> insight (sequential)
        3. All agents complete -> END (wait for player decision)
        4. decision_submitted -> price (calculate outcome)
        5. price complete -> insight (track behavior)
        6. insight complete -> END
        """
        task = state.get("task", "round_start")
        current_step = state.get("current_step", 0)
        
        # Round start: Generate event
        if task == "round_start":
            return {**state, "next_agent": "event_generator", "current_step": 1}
        
        # Event generated: Start data fetching sequence
        elif task == "event_generated":
            return {**state, "next_agent": "price", "task": "fetching_data", "current_step": 2}
        
        # Fetching data: Sequential flow with step tracking
        elif task == "fetching_data":
            if current_step == 2:  # After price
                return {**state, "next_agent": "news", "current_step": 3}
            elif current_step == 3:  # After news
                return {**state, "next_agent": "villain", "current_step": 4}
            elif current_step == 4:  # After villain
                return {**state, "next_agent": "insight", "current_step": 5}
            elif current_step == 5:  # After insight
                return {**state, "next_agent": "END", "task": "round_complete"}
            else:
                # Fallback: end the flow
                return {**state, "next_agent": "END", "task": "round_complete"}
        
        # Player made decision: Calculate outcome
        elif task == "decision_submitted":
            return {**state, "next_agent": "price", "task": "outcome_calculation"}
        
        # Outcome calculated: Track behavior
        elif task == "outcome_calculated":
            return {**state, "next_agent": "insight", "task": "behavior_tracking"}
        
        # Behavior tracking complete
        elif task == "behavior_tracking":
            return {**state, "next_agent": "END", "task": "round_complete"}
        
        # Round complete
        elif task == "round_complete":
            return {**state, "next_agent": "END"}
        
        # Game complete
        elif task == "game_complete":
            return {**state, "next_agent": "END"}
        
        # Default: end
        else:
            return {**state, "next_agent": "END", "task": "round_complete"}
    
    return supervisor_node


def event_generator_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    # Keep track of message boundary so we only read new messages
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent (it returns an updated state with more messages)
    out = event_generator_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) pick structured outputs from your tools (assuming they return JSON):
    sel = _extract_last_tool_json(new_msgs, "select_ticker_from_portfolio") or {}
    evt = _extract_last_tool_json(new_msgs, "determine_event_type") or {}
    desc = _extract_last_tool_json(new_msgs, "generate_event_description") or {}
    hor = _extract_last_tool_json(new_msgs, "set_event_horizon") or {}

    selected_ticker = sel.get("ticker") or state.get("selected_ticker")
    event_type = evt.get("event_type") or state.get("event_type")
    event_description = desc.get("description") or state.get("event_description")
    event_horizon = hor.get("horizon") or state.get("event_horizon")

    # 3) advance supervisor routing
    next_state = {
        **state,
        "messages": messages,
        "selected_ticker": selected_ticker,
        "event_type": event_type,
        "event_description": event_description,
        "event_horizon": event_horizon,
        "task": "event_generated",     # <- THIS UNBLOCKS THE LOOP
        "current_step": max(1, state.get("current_step", 0)),
    }
    return next_state


def price_agent_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent
    out = price_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) extract tool outputs
    price_snap = _extract_last_tool_json(new_msgs, "get_price_snapshot") or {}
    pattern = _extract_last_tool_json(new_msgs, "detect_price_pattern_tool") or {}
    historical = _extract_last_tool_json(new_msgs, "calculate_historical_outcomes") or {}

    price_snapshot = price_snap.get("snapshot") or state.get("price_snapshot")
    price_pattern = pattern.get("pattern") or state.get("price_pattern")
    historical_case = historical.get("outcomes") or state.get("historical_case")

    # 3) advance supervisor routing
    current_task = state.get("task", "fetching_data")
    if current_task == "outcome_calculation":
        new_task = "outcome_calculated"
        new_step = state.get("current_step", 0)
    else:
        new_task = "fetching_data"
        new_step = max(2, state.get("current_step", 0))

    next_state = {
        **state,
        "messages": messages,
        "price_snapshot": price_snapshot,
        "price_pattern": price_pattern,
        "historical_case": historical_case,
        "task": new_task,
        "current_step": new_step,
    }
    return next_state


def news_agent_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent
    out = news_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) extract tool outputs
    headlines_data = _extract_last_tool_json(new_msgs, "fetch_ticker_news") or {}
    consensus_data = _extract_last_tool_json(new_msgs, "compute_consensus") or {}
    contradiction_data = _extract_last_tool_json(new_msgs, "compute_contradiction_score") or {}

    headlines = headlines_data.get("headlines") or state.get("headlines")
    consensus = consensus_data.get("consensus") or state.get("consensus")
    contradiction_score = contradiction_data.get("contradiction_score") or state.get("contradiction_score")

    # 3) advance supervisor routing
    next_state = {
        **state,
        "messages": messages,
        "headlines": headlines,
        "consensus": consensus,
        "contradiction_score": contradiction_score,
        "task": "fetching_data",
        "current_step": max(3, state.get("current_step", 0)),
    }
    return next_state


def villain_agent_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent
    out = villain_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) extract tool outputs
    stance_data = _extract_last_tool_json(new_msgs, "determine_villain_stance") or {}
    bias_data = _extract_last_tool_json(new_msgs, "label_cognitive_bias") or {}
    hot_take_data = _extract_last_tool_json(new_msgs, "generate_hot_take") or {}

    villain_stance = stance_data.get("stance") or state.get("villain_stance")
    villain_bias = bias_data.get("bias") or state.get("villain_bias")
    villain_hot_take = hot_take_data.get("hot_take") or state.get("villain_hot_take")

    # 3) advance supervisor routing
    next_state = {
        **state,
        "messages": messages,
        "villain_stance": villain_stance,
        "villain_bias": villain_bias,
        "villain_hot_take": villain_hot_take,
        "task": "fetching_data",
        "current_step": max(4, state.get("current_step", 0)),
    }
    return next_state


def insight_agent_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent
    out = insight_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) extract tool outputs
    tip_data = _extract_last_tool_json(new_msgs, "write_neutral_tip") or {}
    behavior_data = _extract_last_tool_json(new_msgs, "aggregate_behavior") or {}

    neutral_tip = tip_data.get("tip") or state.get("neutral_tip")
    behavior_flags = behavior_data.get("flags") or state.get("behavior_flags", [])

    # 3) advance supervisor routing
    current_task = state.get("task", "fetching_data")
    if current_task == "behavior_tracking":
        new_task = "round_complete"
        new_step = state.get("current_step", 0)
    else:
        new_task = "fetching_data"
        new_step = max(5, state.get("current_step", 0))

    next_state = {
        **state,
        "messages": messages,
        "neutral_tip": neutral_tip,
        "behavior_flags": behavior_flags,
        "task": new_task,
        "current_step": new_step,
    }
    return next_state


def portfolio_agent_node(state: GameState) -> GameState:
    """Bridge ReAct agent -> GameState. Runs agent, reads tool outputs, updates state, advances task."""
    prev_n = len(state.get("messages", []))

    # 1) run the prebuilt agent
    out = portfolio_agent.invoke(state)
    messages = out.get("messages", state["messages"])
    new_msgs = messages[prev_n:]

    # 2) extract tool outputs (portfolio agent tools)
    price_data = _extract_last_tool_json(new_msgs, "get_current_price") or {}
    fundamentals_data = _extract_last_tool_json(new_msgs, "get_fundamentals") or {}
    allocation_data = _extract_last_tool_json(new_msgs, "check_allocation") or {}

    # 3) advance supervisor routing
    next_state = {
        **state,
        "messages": messages,
        "task": "fetching_data",
        "current_step": max(1, state.get("current_step", 0)),
    }
    return next_state


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
    workflow.add_node("event_generator", event_generator_node)
    workflow.add_node("portfolio", portfolio_agent_node)
    workflow.add_node("news", news_agent_node)
    workflow.add_node("price", price_agent_node)
    workflow.add_node("villain", villain_agent_node)
    workflow.add_node("insight", insight_agent_node)
    
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
        "current_step": 0,
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
        "current_step": 0,
        "next_agent": "supervisor"
    }
    
    result = await game_graph.ainvoke(initial_state)
    
    return {
        "outcome": result.get("outcome"),
        "pl_dollars": result.get("pl_dollars"),
        "pl_percent": result.get("pl_percent"),
        "behavior_flags": result.get("behavior_flags", [])
    }

