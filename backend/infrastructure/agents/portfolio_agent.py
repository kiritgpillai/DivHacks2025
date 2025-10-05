"""Portfolio Agent - Manages player portfolios"""

import os


async def portfolio_agent(state: dict) -> dict:
    """
    Portfolio agent (not used in round flow, only in portfolio creation).
    
    Returns state unchanged as portfolio management happens in handlers.
    """
    # Portfolio operations are handled by CreatePortfolioHandler
    # This agent is a placeholder for graph completeness
    return state

