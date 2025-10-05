"""Event Generator Agent - Creates market event scenarios"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from backend.config import GEMINI_MODEL, TEMPERATURE_EVENT_GENERATOR
from .tools.event_tools import (
    select_ticker_from_portfolio,
    determine_event_type,
    generate_event_description,
    set_event_horizon,
    validate_event_realism
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "event_generator_agent_prompt.md"), "r", encoding="utf-8") as f:
    EVENT_GENERATOR_PROMPT = f.read()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_EVENT_GENERATOR)

# Create Event Generator Agent
event_generator_agent = create_react_agent(
    llm,
    tools=[
        select_ticker_from_portfolio,
        determine_event_type,
        generate_event_description,
        set_event_horizon,
        validate_event_realism
    ],
    prompt=EVENT_GENERATOR_PROMPT,
    name="event_generator"
)