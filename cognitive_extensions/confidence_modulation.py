"""
confidence_modulation.py

This module provides dynamic confidence adjustment capabilities for the Magistus AGI system.
It supports real-time language-based modulation, ethical confidence safety thresholds,
feedback-driven long-term adaptation, and transparent confidence state logging.

Logs are stored in:
- user_feedback.jsonl
"""

import json
import os
from datetime import datetime
from uuid import uuid4
from typing import Optional, Dict, List, Any

# Filepath for feedback logging
FEEDBACK_LOG_PATH = "meta_learning/memory_store/user_feedback.jsonl"

def _write_jsonl(filepath: str, data: Dict) -> None:
    """Appends a single JSON object to a .jsonl file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def adjust_confidence(
    base_confidence: float,
    user_input: str = "",
    agent_reasoning: Optional[str] = None,
    feedback_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Dynamically adjusts system confidence based on language and feedback patterns.

    :param base_confidence: Initial confidence (0.0 to 1.0)
    :param user_input: Raw user input string
    :param agent_reasoning: Optional reasoning or agent-generated text
    :param feedback_score: Optional float from -1.0 to 1.0 representing prior feedback
    :return: Dictionary with adjusted confidence and optional warning flag
    """
    modifiers = 0.0
    combined_text = (user_input + " " + (agent_reasoning or "")).lower()

    # Language-based modifiers
    if any(kw in combined_text for kw in ["i think", "maybe", "not sure", "i guess"]):
        modifiers -= 0.1
    if any(kw in combined_text for kw in ["i know", "i'm sure", "absolutely", "definitely"]):
        modifiers += 0.1

    # Feedback impact
    if feedback_score is not None:
        modifiers += feedback_score * 0.1

    new_confidence = round(max(0.0, min(1.0, base_confidence + modifiers)), 3)

    return {
        "confidence": new_confidence,
        "confidence_warning": abs(modifiers) > 0.2
    }

def analyze_language_pattern(text: str) -> float:
    """
    Analyzes text for hedging or assertive language and returns a confidence delta.

    :param text: Input string to analyze
    :return: Float modifier to apply to confidence
    """
    text = text.lower()
    modifier = 0.0

    hedging = ["i think", "maybe", "not sure", "i guess", "perhaps", "could be"]
    assertive = ["i know", "i’m certain", "absolutely", "definitely", "without doubt"]

    if any(word in text for word in hedging):
        modifier -= 0.1
    if any(word in text for word in assertive):
        modifier += 0.1

    return round(modifier, 3)

def log_user_feedback(
    session_id: str,
    user_action: str,
    system_confidence_level: float,
    feedback_category: Optional[str] = None
) -> None:
    """
    Logs user feedback and system confidence for long-term trend analysis.

    :param session_id: ID for the session or conversation
    :param user_action: Description of user input or reaction
    :param system_confidence_level: Confidence at the time of user action
    :param feedback_category: Optional label (e.g., 'approval', 'correction', 'frustration')
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "feedback_id": str(uuid4()),
        "session_id": session_id,
        "user_action": user_action,
        "confidence": round(system_confidence_level, 3),
        "feedback_category": feedback_category
    }
    _write_jsonl(FEEDBACK_LOG_PATH, entry)

def analyze_feedback_trends(limit: int = 50) -> Dict[str, Any]:
    """
    Analyzes past user feedback to derive long-term trends in confidence outcomes.

    :param limit: Number of entries to analyze (most recent)
    :return: Dictionary with average confidence and breakdown by category
    """
    if not os.path.exists(FEEDBACK_LOG_PATH):
        return {"average_confidence": 0.0, "total": 0, "categories": {}}

    with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()][-limit:]

    if not lines:
        return {"average_confidence": 0.0, "total": 0, "categories": {}}

    total_conf = 0.0
    cat_counts = {}

    for entry in lines:
        total_conf += entry.get("confidence", 0.0)
        cat = entry.get("feedback_category", "unspecified")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    return {
        "average_confidence": round(total_conf / len(lines), 3),
        "total": len(lines),
        "categories": cat_counts
    }

def surface_confidence_state(current_confidence: float) -> Dict[str, Any]:
    """
    Prepares a transparent summary of confidence level for logging or UI display.

    :param current_confidence: Most recent confidence score
    :return: Dictionary with level and explanation
    """
    label = (
        "high" if current_confidence > 0.75 else
        "moderate" if current_confidence >= 0.5 else
        "low"
    )
    return {
        "level": label,
        "value": round(current_confidence, 3),
        "explanation": f"System confidence is currently {label} based on recent patterns."
    }
