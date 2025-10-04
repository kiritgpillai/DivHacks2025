"""
LangSmith Integration for Agent Graph Visualization

Enables visualization of the multi-agent workflow in LangSmith.
"""

import os


def setup_langsmith():
    """
    Setup LangSmith for agent graph visualization.
    
    Call this at application startup to enable tracing.
    """
    api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not api_key:
        print("WARNING: LANGSMITH_API_KEY not set. Graph visualization disabled.")
        return False
    
    try:
        # Enable LangSmith tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "market-mayhem")
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        
        print("SUCCESS: LangSmith graph visualization enabled")
        print(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
        print(f"   Dashboard: https://smith.langchain.com")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to setup LangSmith: {str(e)}")
        return False


def get_langsmith_url(run_id: str) -> str:
    """
    Get the LangSmith URL for a specific run.
    
    Args:
        run_id: The LangChain run ID
        
    Returns:
        URL to view the run in LangSmith
    """
    project = os.getenv("LANGCHAIN_PROJECT", "market-mayhem")
    return f"https://smith.langchain.com/public/{project}/r/{run_id}"


def log_to_langsmith(message: str, metadata: dict = None):
    """
    Log custom messages to LangSmith.
    
    Usage:
        log_to_langsmith("Round started", {"round": 1})
    """
    try:
        from langsmith import Client
        
        client = Client()
        client.create_feedback(
            run_id=metadata.get("run_id") if metadata else None,
            key="custom_log",
            score=1.0,
            value=message,
            comment=str(metadata) if metadata else None
        )
    except Exception as e:
        print(f"Failed to log to LangSmith: {str(e)}")
