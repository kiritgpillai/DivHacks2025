"""Villain Agent Tools - Trash-Talking AI"""

import os
from langchain.tools import tool
import json
import random
import google.generativeai as genai
from backend.config import GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))


@tool
async def determine_villain_stance(event_description: str, rational_action: str = "") -> str:
    """
    Determine Villain's stance (Bullish or Bearish).
    
    Often chooses contrarian stance to mislead player.
    
    Args:
        event_description: The market event
        rational_action: What rational analysis suggests (optional)
        
    Returns:
        JSON with stance and rationale
    """
    # Randomly choose to be contrarian (70% of the time) or aligned (30%)
    be_contrarian = random.random() < 0.7
    
    # Simple heuristic: look for keywords
    bearish_keywords = ["miss", "down", "fine", "investigation", "recall", "warning"]
    bullish_keywords = ["beat", "up", "approval", "breakthrough", "upgrade", "surge"]
    
    event_lower = event_description.lower()
    
    # Determine base stance from event
    if any(word in event_lower for word in bearish_keywords):
        base_stance = "Bearish"
    elif any(word in event_lower for word in bullish_keywords):
        base_stance = "Bullish"
    else:
        base_stance = random.choice(["Bullish", "Bearish"])
    
    # Apply contrarian logic
    if be_contrarian:
        stance = "Bearish" if base_stance == "Bullish" else "Bullish"
        rationale = "contrarian_misleading"
    else:
        stance = base_stance
        rationale = "aligned_with_event"
    
    return json.dumps({
        "stance": stance,
        "rationale": rationale,
        "is_contrarian": be_contrarian
    })


@tool
async def label_cognitive_bias(hot_take: str) -> str:
    """
    Label the cognitive bias being exploited in the hot take.
    
    Args:
        hot_take: The villain's statement
        
    Returns:
        Bias type (Fear Appeal, Overconfidence, Authority Lure, Recency Bias)
    """
    hot_take_lower = hot_take.lower()
    
    # Keyword-based classification
    if any(word in hot_take_lower for word in ["crash", "trap", "dump", "sell", "panic", "bag holder"]):
        bias = "Fear Appeal"
    elif any(word in hot_take_lower for word in ["guaranteed", "easy", "moon", "all in", "can't lose"]):
        bias = "Overconfidence"
    elif any(word in hot_take_lower for word in ["analyst", "expert", "wall street", "smart money", "insider"]):
        bias = "Authority Lure"
    elif any(word in hot_take_lower for word in ["momentum", "trend", "streak", "days in a row", "pattern"]):
        bias = "Recency Bias"
    else:
        # Default to random
        bias = random.choice(["Fear Appeal", "Overconfidence", "Authority Lure", "Recency Bias"])
    
    descriptions = {
        "Fear Appeal": "Creating panic and urgency to sell",
        "Overconfidence": "Promoting guaranteed gains and FOMO",
        "Authority Lure": "Appealing to expert opinion",
        "Recency Bias": "Overweighting recent price action"
    }
    
    return json.dumps({
        "bias": bias,
        "description": descriptions[bias]
    })


@tool
async def generate_hot_take(
    event_description: str,
    stance: str,
    bias_type: str
) -> str:
    """
    Generate Villain's biased hot take using Gemini.
    
    Args:
        event_description: The market event
        stance: Bullish or Bearish
        bias_type: Cognitive bias to exploit
        
    Returns:
        JSON with hot take text
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""You are a trash-talking Villain AI in a trading game. Generate a bold, emotionally charged hot take.

Event: {event_description}
Your stance: {stance}
Cognitive bias to use: {bias_type}

Guidelines:
- Be confident and provocative (1-2 sentences)
- Use strong emotional language
- Be WRONG on purpose to mislead the player
- Exploit the {bias_type} bias explicitly
- Never hedge or show doubt

Examples by bias type:

Fear Appeal: "This earnings beat is a trap! Smart money is dumping into retail hype. I'm selling ALL my shares before it crashes tomorrow."

Overconfidence: "This is the easiest trade of the year! Analyst upgrade means guaranteed 40% pop by next week. I'm leveraging up with calls."

Authority Lure: "My Goldman contacts are all bearish here. They're quietly exiting before the catalyst drops. When Wall Street's best are running, you should too."

Recency Bias: "Stock is up 3 straight days with massive volume. This thing is going parabolic. Momentum players are piling in. HOLD for the moon!"

Generate your hot take now:"""
        
        response = model.generate_content(prompt)
        hot_take = response.text.strip()
        
        # Remove quotes if Gemini adds them
        hot_take = hot_take.strip('"\'')
        
        return json.dumps({
            "text": hot_take,
            "stance": stance,
            "bias": bias_type,
            "success": True
        })
        
    except Exception as e:
        # Fallback hot takes
        fallbacks = {
            "Fear Appeal": f"This is a trap! Smart money is exiting. I'm selling everything before it crashes. Don't be left holding the bag!",
            "Overconfidence": f"This is guaranteed money! I'm all in with maximum leverage. Easy 50% gain by Friday!",
            "Authority Lure": f"Top analysts are all saying the same thing. Follow the smart money or get left behind!",
            "Recency Bias": f"The trend is clear from recent action. Momentum is everything. This is going way higher!"
        }
        
        return json.dumps({
            "text": fallbacks.get(bias_type, "This is a major move! Don't miss out!"),
            "stance": stance,
            "bias": bias_type,
            "success": False,
            "error": str(e)
        })


@tool
async def create_villain_persona() -> str:
    """
    Maintain consistent Villain persona characteristics.
    
    Returns:
        JSON with persona traits
    """
    return json.dumps({
        "personality": "confident_provocative",
        "communication_style": "bold_emotional",
        "accuracy_rate": 0.30,  # Wrong 70% of the time
        "favorite_phrases": [
            "Smart money is...",
            "This is a trap!",
            "Guaranteed gains!",
            "Follow the experts!",
            "The trend is clear!"
        ],
        "role": "educational_antagonist",
        "goal": "teach_cognitive_biases_through_mistakes"
    })

