# agents/temporal_lobe.py

from context_types import ContextBundle, AgentThought
from typing import List, Optional
from datetime import datetime
import re

try:
    from llm_wrapper import generate_response
except ImportError:
    def generate_response(prompt: str) -> str:
        return "[Fallback] Temporal processing unavailable."

# Helper: crude emotional valence estimator (can be replaced later with NLP sentiment classifier)
def detect_emotional_valence(text: str) -> str:
    emotion_keywords = {
        "joy": ["happy", "excited", "joy", "love", "great"],
        "anger": ["angry", "hate", "furious", "irritated"],
        "sadness": ["sad", "lonely", "depressed", "miss"],
        "confusion": ["confused", "unclear", "lost", "don't understand"],
        "neutral": []
    }
    text = text.lower()
    for emotion, keywords in emotion_keywords.items():
        if any(kw in text for kw in keywords):
            return emotion
    return "neutral"

# Helper: identify pattern triggers
def extract_temporal_patterns(memories: List[str], input_text: str) -> List[str]:
    pattern_clues = []
    for mem in memories:
        if any(kw in mem.lower() for kw in ["again", "last", "repeat", "every time"]):
            pattern_clues.append("repeat_detected")
        if any(word in input_text.lower() for word in mem.lower().split()):
            pattern_clues.append("input_repeats_memory_term")
    return list(set(pattern_clues))


def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
    """
    The Temporal Lobe agent retrieves relevant past memory fragments,
    scores them by relevance and emotional context, and interprets
    time-linked patterns to forecast possible continuity.
    """

    debug_mode = context.config.get("debug_mode", False)
    memory_matches = context.memory_matches or []
    user_input = context.user_input.lower()
    emotional_valence = detect_emotional_valence(user_input)

    # Score and sort memory matches by emotional valence + recency + keyword triggers
    keyword_triggers = ["remember", "again", "last time", "once more", "previously"]
    triggered = any(kw in user_input for kw in keyword_triggers)

    weighted_memories = []
    for i, mem in enumerate(memory_matches):
        valence = detect_emotional_valence(mem)
        score = 1.0
        if valence != "neutral":
            score += 0.2
        if any(kw in mem.lower() for kw in keyword_triggers):
            score += 0.2
        score -= i * 0.1  # decay over time
        weighted_memories.append((score, mem))

    weighted_memories.sort(reverse=True)
    top_memories = [m[1] for m in weighted_memories[:2]]

    # Pattern recognition
    pattern_signals = extract_temporal_patterns(top_memories, user_input)

    # Build prompt for interpretation
    prompt = (
        f"You are the temporal lobe of a synthetic brain.\n"
        f"User emotional tone: {emotional_valence}\n"
        f"Detected temporal keywords: {', '.join([kw for kw in keyword_triggers if kw in user_input])}\n\n"
        f"Relevant memories:\n{top_memories}\n\n"
        f"Pattern signals: {pattern_signals}\n\n"
        f"Interpret how the current input connects to prior experiences over time. "
        f"Highlight any emotional continuity, repeat cycles, or broken temporal links. "
        f"Maintain ethical tone and never assume memory is certain — state confidence carefully."
    )

    try:
        llm_content = generate_response(prompt).strip()
    except Exception:
        llm_content = "[Fallback] No temporal interpretation available."

    # Confidence scoring
    confidence = 0.55
    if memory_matches:
        confidence += 0.1
    if triggered:
        confidence += 0.1
    if pattern_signals:
        confidence += 0.1
    confidence = round(min(confidence, 0.95), 2)

    # Reasoning tags
    reasons = []
    if triggered:
        reasons.append("temporal language")
    if memory_matches:
        reasons.append("memory match")
    if pattern_signals:
        reasons.extend(pattern_signals)
    if emotional_valence != "neutral":
        reasons.append(f"emotion:{emotional_valence}")

    return AgentThought(
        agent_name="temporal_lobe",
        confidence=confidence,
        content=llm_content,
        reasons=reasons,
        requires_memory=True,
        flags={
            "insight": True,
            "ethical_check": False,
            "pattern_detected": bool(pattern_signals)
        }
    )
