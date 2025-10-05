"""Price Agent - Handles price data and historical outcome replay"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from backend.config import GEMINI_MODEL, TEMPERATURE_PRICE
from .tools.price_tools import (
    get_price_snapshot,
    get_sparkline,
    detect_price_pattern_tool,
    sample_historical_window,
    apply_decision_to_path,
    calculate_historical_outcomes
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "price_agent_prompt.md"), "r", encoding="utf-8") as f:
    PRICE_PROMPT = f.read()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_PRICE)

# Create Price Agent
price_agent = create_react_agent(
    llm,
    tools=[
        get_price_snapshot,
        get_sparkline,
        detect_price_pattern_tool,
        sample_historical_window,
        apply_decision_to_path,
        calculate_historical_outcomes
    ],
    prompt=PRICE_PROMPT,
    name="price"
)

