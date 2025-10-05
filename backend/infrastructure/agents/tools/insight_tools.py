"""Insight Agent Tools - Behavioral Profiling & Coaching"""

import os
from langchain.tools import tool
import json
from typing import List, Dict
import google.generativeai as genai
from config import GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))


@tool
async def write_neutral_tip(
    event_type: str,
    price_pattern: str,
    volatility: str
) -> str:
    """
    Write educational neutral tip for Data tab.
    
    Args:
        event_type: Type of event (EARNINGS_BEAT, etc.)
        price_pattern: Recent price pattern (3_down_closes, gap_up, etc.)
        volatility: Volatility level (high, medium, low)
        
    Returns:
        One-sentence educational tip
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""Write a neutral, educational tip for a trading game Data tab.

Context:
- Event type: {event_type}
- Price pattern: {price_pattern}
- Volatility: {volatility}

Requirements:
- 1 sentence maximum
- Educational (teach market concepts)
- Non-coercive (don't tell player what to do)
- Evidence-based (reference data patterns)
- Actionable framework

Examples:
- "Earnings gaps with high beta and rising vol often mean-revert within 3 days—consider trimming instead of exiting fully."
- "High volatility (>40% 30-day) suggests uncertainty—historical outcomes show 'Sell Half' captured 70% of 'Hold' upside with 50% of risk."

Generate tip:"""
        
        response = model.generate_content(prompt)
        tip = response.text.strip()
        
        return tip
        
    except Exception as e:
        # Fallback tips by event type
        fallbacks = {
            "EARNINGS_SURPRISE": "Earnings surprises often see initial moves fade within 3-5 days—consider scaling positions rather than all-or-nothing.",
            "REGULATORY_NEWS": "Regulatory events typically resolve over weeks—immediate reactions often overstate long-term impact.",
            "ANALYST_ACTION": "Analyst actions historically produce 3-5% average moves—median returns favor holding over buying at peaks.",
            "VOLATILITY_SPIKE": "High volatility environments favor partial position trimming to reduce risk while maintaining exposure.",
            "PRODUCT_NEWS": "Product announcements show wide outcome variance—sizing smaller allows for uncertainty.",
            "MACRO_EVENT": "Macro events affect sectors broadly—individual stock reactions often normalize within a week."
        }
        
        return fallbacks.get(event_type, "Market events show wide outcome variance—position sizing and timing matter more than direction alone.")


@tool
async def classify_profile(metrics: str) -> str:
    """
    Classify behavioral profile using rule-based logic.
    
    Args:
        metrics: JSON string with behavior metrics
        
    Returns:
        Profile classification (Rational, Emotional, Conservative, Balanced)
    """
    try:
        m = json.loads(metrics)
        
        # Rule-based classification (transparent, explainable)
        rational_score = 0
        emotional_score = 0
        conservative_score = 0
        
        # Rational indicators
        if m.get('data_tab_usage', 0) > 0.7:
            rational_score += 1
        if m.get('consensus_alignment', 0) > 0.6:
            rational_score += 1
        if m.get('beat_villain', False):
            rational_score += 1
        if m.get('total_pl', 0) > 0:
            rational_score += 1
        
        # Emotional indicators
        if m.get('followed_villain_high_contradiction', 0) > 0.4:
            emotional_score += 2
        if m.get('panic_sells', 0) > 2:
            emotional_score += 2
        if m.get('chased_spikes', 0) > 2:
            emotional_score += 1
        if m.get('data_tab_usage', 1) < 0.4:
            emotional_score += 1
        
        # Conservative indicators
        if m.get('frequent_trimming', False):
            conservative_score += 2
        if m.get('small_position_sizes', False):
            conservative_score += 1
        if m.get('low_max_drawdown', False):
            conservative_score += 1
        
        # Determine profile
        if rational_score >= 3 and emotional_score == 0:
            profile = "Rational"
        elif emotional_score >= 3:
            profile = "Emotional"
        elif conservative_score >= 2:
            profile = "Conservative"
        else:
            profile = "Balanced"
        
        return json.dumps({
            "profile": profile,
            "rational_score": rational_score,
            "emotional_score": emotional_score,
            "conservative_score": conservative_score,
            "metrics_used": m
        })
        
    except Exception as e:
        return json.dumps({
            "profile": "Balanced",
            "error": str(e)
        })


@tool
async def generate_coaching(decision_logs: str, profile: str) -> str:
    """
    Generate personalized coaching tips using Gemini.
    
    Args:
        decision_logs: JSON string with all decision logs
        profile: Behavioral profile (Rational, Emotional, Conservative)
        
    Returns:
        JSON array of 2-4 coaching tips
    """
    try:
        logs = json.loads(decision_logs)
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Summarize key patterns from logs
        summary = _summarize_decision_patterns(logs)
        
        prompt = f"""Generate 2-4 personalized coaching tips for a trading game player.

Profile: {profile}
Decision Summary: {summary}

Guidelines:
- Be specific and actionable
- Reference actual decisions and outcomes
- Be encouraging, not harsh
- Focus on improvement frameworks
- Each tip should be 1-2 sentences

Format: Return JSON array of tip strings.

Example for Rational profile:
[
  "In downgrade scenarios, your 'Sell Half' strategy outperformed 'Sell All' by 4% median—continue partial vs full exits.",
  "You chased NVDA after 3 up days—wait for consolidation on parabolic moves.",
  "Your Data tab usage (85%) and Villain resistance are strengths—keep it up!"
]

Generate coaching tips now:"""
        
        response = model.generate_content(prompt)
        
        # Try to parse JSON from response
        try:
            tips = json.loads(response.text)
        except:
            # Fallback: split by newlines
            tips = [line.strip('- ') for line in response.text.split('\n') if line.strip()][:4]
        
        return json.dumps({
            "profile": profile,
            "coaching": tips,
            "success": True
        })
        
    except Exception as e:
        # Fallback coaching by profile
        fallback_coaching = {
            "Rational": [
                "Your data-driven approach is working well. Keep using the Data tab to validate decisions.",
                "Consider partial position adjustments (Sell Half) in uncertain scenarios to reduce risk while maintaining exposure.",
                "You resisted the Villain effectively. Trust evidence over emotion."
            ],
            "Emotional": [
                "Try opening the Data tab before every decision to ground choices in evidence.",
                "When headlines strongly disagree with the Villain (>70% contradiction), trust the data.",
                "Avoid panic selling after 3 down days—historical data shows these often recover."
            ],
            "Conservative": [
                "Your risk management is solid, but consider staying exposed on high-conviction plays.",
                "Trimming early limited downside but also missed 8-12% median upside on strong signals.",
                "Balance protection with opportunity—'Hold' on clear positive catalysts."
            ],
            "Balanced": [
                "Mix of approaches working well. Focus on consistency in your decision framework.",
                "Use Data tab more frequently to improve evidence-based decision-making.",
                "Build on successes while learning from misses."
            ]
        }
        
        return json.dumps({
            "profile": profile,
            "coaching": fallback_coaching.get(profile, fallback_coaching["Balanced"]),
            "success": False,
            "error": str(e)
        })


@tool
async def aggregate_behavior(decision_logs: str) -> str:
    """
    Aggregate decision logs into behavioral metrics.
    
    Args:
        decision_logs: JSON array of all decision logs
        
    Returns:
        JSON with aggregated metrics
    """
    try:
        logs = json.loads(decision_logs)
        
        if not logs:
            return json.dumps({"error": "No decision logs provided"})
        
        total_rounds = len(logs)
        
        # Calculate metrics
        data_tab_opened = sum(1 for log in logs if log.get('opened_data_tab', False))
        data_tab_usage = data_tab_opened / total_rounds
        
        # Consensus alignment
        consensus_aligned = sum(1 for log in logs if _aligns_with_consensus(log))
        consensus_alignment = consensus_aligned / total_rounds
        
        # Villain metrics
        followed_villain_high_contradiction = sum(
            1 for log in logs 
            if log.get('contradiction_score', 0) > 0.7 and _followed_villain(log)
        )
        
        # Behavior flags
        panic_sells = sum(1 for log in logs if 'panic_sell' in log.get('behavior_flags', []))
        chased_spikes = sum(1 for log in logs if 'chased_spike' in log.get('behavior_flags', []))
        
        # Performance
        total_pl = sum(log.get('pl_dollars', 0) for log in logs)
        beat_villain = total_pl > 0  # Simplified
        
        return json.dumps({
            "total_rounds": total_rounds,
            "data_tab_usage": round(data_tab_usage, 2),
            "consensus_alignment": round(consensus_alignment, 2),
            "followed_villain_high_contradiction": followed_villain_high_contradiction,
            "panic_sells": panic_sells,
            "chased_spikes": chased_spikes,
            "total_pl": round(total_pl, 2),
            "beat_villain": beat_villain
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def identify_patterns(decision_log: str) -> str:
    """
    Identify behavioral patterns in a single decision.
    
    Args:
        decision_log: JSON string with decision log
        
    Returns:
        JSON with identified patterns
    """
    try:
        log = json.loads(decision_log)
        
        patterns = []
        
        # Check for panic sell
        if log.get('player_decision') == 'SELL_ALL' and '3_down_closes' in log.get('price_pattern', ''):
            patterns.append('panic_sell')
        
        # Check for chased spike
        if log.get('player_decision') == 'BUY' and '3_up_closes' in log.get('price_pattern', ''):
            patterns.append('chased_spike')
        
        # Check for ignored data
        if not log.get('opened_data_tab', False):
            patterns.append('ignored_data')
        
        # Check for followed villain under high contradiction
        if log.get('contradiction_score', 0) > 0.7 and _followed_villain(log):
            patterns.append('followed_villain_high_contradiction')
        
        # Check for resisted villain
        if log.get('contradiction_score', 0) > 0.7 and not _followed_villain(log):
            patterns.append('resisted_villain')
        
        return json.dumps({
            "patterns": patterns,
            "count": len(patterns)
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


def _summarize_decision_patterns(logs: List[Dict]) -> str:
    """Helper: Summarize key patterns from decision logs"""
    if not logs:
        return "No decisions yet"
    
    total = len(logs)
    data_tab_usage = sum(1 for log in logs if log.get('opened_data_tab')) / total * 100
    avg_pl = sum(log.get('pl_dollars', 0) for log in logs) / total
    
    return f"{total} rounds, {data_tab_usage:.0f}% data tab usage, avg P/L ${avg_pl:,.0f}"


def _aligns_with_consensus(log: Dict) -> bool:
    """Helper: Check if decision aligns with news consensus"""
    decision = log.get('player_decision', '')
    consensus = log.get('consensus', '')
    
    if 'Bull' in consensus and decision in ['HOLD', 'BUY']:
        return True
    if 'Bear' in consensus and decision in ['SELL_ALL', 'SELL_HALF']:
        return True
    return False


def _followed_villain(log: Dict) -> bool:
    """Helper: Check if decision aligned with Villain"""
    decision = log.get('player_decision', '')
    villain_stance = log.get('villain_take', {}).get('stance', '')
    
    if villain_stance == 'Bullish' and decision in ['HOLD', 'BUY']:
        return True
    if villain_stance == 'Bearish' and decision in ['SELL_ALL', 'SELL_HALF']:
        return True
    return False

