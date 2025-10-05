"""Villain Agent - Generates biased hot takes"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from backend.config import GEMINI_MODEL, TEMPERATURE_VILLAIN
from .tools.villain_tools import (
    determine_villain_stance,
    label_cognitive_bias,
    generate_hot_take,
    create_villain_persona
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "villain_agent_prompt.md"), "r", encoding="utf-8") as f:
    VILLAIN_PROMPT = f.read()

# Initialize LLM (higher temperature for creativity)
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE_VILLAIN)

# Create Villain Agent
villain_agent = create_react_agent(
    llm,
    tools=[
        determine_villain_stance,
        label_cognitive_bias,
        generate_hot_take,
        create_villain_persona
    ],
    prompt=VILLAIN_PROMPT,
    name="villain"
)

