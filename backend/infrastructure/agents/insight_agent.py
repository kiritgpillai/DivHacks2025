"""Insight Agent - Provides neutral tips and behavioral coaching"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from backend.config import GEMINI_MODEL, TEMPERATURE_INSIGHT
from .tools.insight_tools import (
    write_neutral_tip,
    classify_profile,
    generate_coaching,
    aggregate_behavior,
    identify_patterns
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "insight_agent_prompt.md"), "r", encoding="utf-8") as f:
    INSIGHT_PROMPT = f.read()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_INSIGHT)

# Create Insight Agent
insight_agent = create_react_agent(
    llm,
    tools=[
        write_neutral_tip,
        classify_profile,
        generate_coaching,
        aggregate_behavior,
        identify_patterns
    ],
    prompt=INSIGHT_PROMPT,
    name="insight"
)

