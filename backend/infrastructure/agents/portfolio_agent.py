"""Portfolio Agent - Manages player portfolios"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from .tools.portfolio_tools import (
    validate_ticker,
    get_current_price,
    get_fundamentals,
    check_allocation
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "portfolio_agent_prompt.md"), "r", encoding="utf-8") as f:
    PORTFOLIO_PROMPT = f.read()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

# Create Portfolio Agent
portfolio_agent = create_react_agent(
    llm,
    tools=[
        validate_ticker,
        get_current_price,
        get_fundamentals,
        check_allocation
    ],
    prompt=PORTFOLIO_PROMPT,
    name="portfolio"
)

