"""
Opik Integration for LLM Observability

Tracks all agent calls, tool usage, and LLM interactions.
"""

import os
from typing import Any, Dict, Optional
import opik
from functools import wraps
import asyncio


def setup_opik():
    """
    Setup Opik observability.
    
    Call this at application startup to enable tracing.
    """
    api_key = os.getenv("OPIK_API_KEY")
    
    if not api_key:
        print("WARNING: OPIK_API_KEY not set. Observability disabled.")
        return False
    
    try:
        opik.configure(api_key=api_key)
        print("SUCCESS: Opik observability enabled")
        return True
    except Exception as e:
        print(f"ERROR: Failed to setup Opik: {str(e)}")
        return False


def trace_agent_call(agent_name: str):
    """
    Decorator to trace agent calls with Opik.
    
    Usage:
        @trace_agent_call("portfolio_agent")
        async def portfolio_node(state):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Start Opik trace
                with opik.track(
                    name=f"{agent_name}_call",
                    project_name="market-mayhem",
                    tags=[agent_name, "agent_call"]
                ) as trace:
                    # Extract state for logging
                    state = args[0] if args else kwargs.get('state', {})
                    
                    # Log input
                    trace.log_input({
                        "agent": agent_name,
                        "state_keys": list(state.keys()) if isinstance(state, dict) else [],
                        "round": state.get("round_number", 0) if isinstance(state, dict) else 0
                    })
                    
                    # Execute agent
                    result = await func(*args, **kwargs)
                    
                    # Log output
                    trace.log_output({
                        "agent": agent_name,
                        "success": True,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else []
                    })
                    
                    return result
                    
            except Exception as e:
                # Log error
                print(f"Error in {agent_name}: {str(e)}")
                
                try:
                    with opik.track(
                        name=f"{agent_name}_error",
                        project_name="market-mayhem",
                        tags=[agent_name, "error"]
                    ) as error_trace:
                        error_trace.log_output({
                            "agent": agent_name,
                            "error": str(e),
                            "success": False
                        })
                except:
                    pass
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                with opik.track(
                    name=f"{agent_name}_call",
                    project_name="market-mayhem",
                    tags=[agent_name, "agent_call"]
                ) as trace:
                    state = args[0] if args else kwargs.get('state', {})
                    
                    trace.log_input({
                        "agent": agent_name,
                        "state_keys": list(state.keys()) if isinstance(state, dict) else []
                    })
                    
                    result = func(*args, **kwargs)
                    
                    trace.log_output({
                        "agent": agent_name,
                        "success": True
                    })
                    
                    return result
                    
            except Exception as e:
                print(f"Error in {agent_name}: {str(e)}")
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_game_event(event_type: str, data: Dict[str, Any]):
    """
    Log custom game events to Opik.
    
    Usage:
        log_game_event("round_start", {"round": 1, "ticker": "AAPL"})
        log_game_event("decision_submitted", {"decision": "HOLD"})
    """
    try:
        with opik.track(
            name=f"game_{event_type}",
            project_name="market-mayhem",
            tags=["game_event", event_type]
        ) as trace:
            trace.log_input(data)
            trace.log_output({"event": event_type, "logged": True})
    except Exception as e:
        print(f"Failed to log event: {str(e)}")


def log_llm_call(
    model: str,
    prompt: str,
    response: str,
    tokens: Optional[int] = None,
    latency: Optional[float] = None
):
    """
    Log LLM API calls to Opik.
    
    Usage:
        log_llm_call(
            model="gemini-pro",
            prompt="Generate event...",
            response="...",
            tokens=150,
            latency=1.2
        )
    """
    try:
        with opik.track(
            name="llm_call",
            project_name="market-mayhem",
            tags=["llm", model]
        ) as trace:
            trace.log_input({
                "model": model,
                "prompt": prompt[:500],  # Truncate long prompts
                "prompt_length": len(prompt)
            })
            
            trace.log_output({
                "response": response[:500],
                "response_length": len(response),
                "tokens": tokens,
                "latency_seconds": latency
            })
    except Exception as e:
        print(f"Failed to log LLM call: {str(e)}")
