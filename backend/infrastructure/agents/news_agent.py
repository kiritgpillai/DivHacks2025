"""News Agent - Fetches and analyzes news headlines"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from .tools.news_tools import (
    fetch_ticker_news,
    assign_headline_stance,
    compute_consensus,
    compute_contradiction_score
)

# Load prompt from file
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
with open(os.path.join(PROMPTS_DIR, "news_agent_prompt.md"), "r", encoding="utf-8") as f:
    NEWS_PROMPT = f.read()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2)

# Create News Agent
news_agent = create_react_agent(
    llm,
    tools=[
        fetch_ticker_news,
        assign_headline_stance,
        compute_consensus,
        compute_contradiction_score
    ],
    prompt=NEWS_PROMPT,
    name="news"
)

