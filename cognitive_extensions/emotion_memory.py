"""
emotion_memory.py

This module implements emotional memory functions for the Magistus AGI system.
It handles the logging, retrieval, analysis, and tagging of emotional data,
providing a foundation for emotionally aware and ethically aligned AI behavior.

Data is written to:
- emotion_log.jsonl: logs of emotional responses with metadata
- tagged_memory_log.jsonl: emotional annotations tied to memory entries

All functions are designed to be safe, modular, and align with privacy and consent principles.
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import Counter

# Define file paths
EMOTION_LOG_PATH = "meta_learning/memory_store/emotion_log.jsonl"
TAGGED_MEMORY_PATH = "meta_learning/memory_store/tagged_memory_log.jsonl"

def _write_jsonl(filepath: str, data: Dict[str, Any]) -> None:
    """Appends a dictionary as a JSONL entry."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def _read_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Reads all JSONL lines from a file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def log_emotion(
    emotion_type: str,
    intensity: float,
    context_id: Optional[str] = None,
    source: str = "agent",
    model_version: str = "v1.0"
) -> None:
    """
    Logs a new emotion entry to emotion_log.jsonl.

    :param emotion_type: Type of emotion (e.g., 'joy', 'anger', 'confusion')
    :param intensity: Float from 0.0 to 1.0 indicating strength
    :param context_id: Optional context or session identifier
    :param source: Source of emotion signal (e.g., 'user_input', 'memory_analysis')
    :param model_version: Version of the emotional model used
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "emotion_type": emotion_type,
        "intensity": round(float(intensity), 2),
        "context_id": context_id,
        "source": source,
        "model_version": model_version
    }
    _write_jsonl(EMOTION_LOG_PATH, entry)

def analyze_mood_trend(limit: int = 20) -> Dict[str, Any]:
    """
    Analyzes recent emotions to identify mood trends.

    :param limit: Number of most recent entries to analyze
    :return: Dictionary with dominant emotion, average intensity, and breakdown
    """
    logs = _read_jsonl(EMOTION_LOG_PATH)[-limit:]
    if not logs:
        return {"trend": "neutral", "average_intensity": 0.0, "count": 0, "breakdown": {}}

    emotion_counter = Counter()
    intensity_total = 0.0

    for entry in logs:
        emotion_counter[entry["emotion_type"]] += 1
        intensity_total += entry["intensity"]

    dominant_emotion = emotion_counter.most_common(1)[0][0]
    average_intensity = round(intensity_total / len(logs), 2)

    return {
        "trend": dominant_emotion,
        "average_intensity": average_intensity,
        "count": len(logs),
        "breakdown": dict(emotion_counter)
    }

def tag_memory_with_emotion(
    memory_id: str,
    emotion_type: str,
    intensity: float
) -> None:
    """
    Tags a memory entry with an emotion.

    :param memory_id: Unique identifier for the memory
    :param emotion_type: Emotion to tag (e.g., 'hopeful', 'anxious')
    :param intensity: Strength of emotion (0.0 to 1.0)
    """
    entry = {
        "memory_id": memory_id,
        "emotion_type": emotion_type,
        "intensity": round(float(intensity), 2),
        "timestamp": datetime.utcnow().isoformat()
    }
    _write_jsonl(TAGGED_MEMORY_PATH, entry)

def retrieve_emotion_log(
    context_id: Optional[str] = None,
    emotion_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves emotion entries filtered by context or type.

    :param context_id: Context/session ID to match
    :param emotion_type: Specific emotion to filter by
    :return: Filtered list of emotion entries
    """
    logs = _read_jsonl(EMOTION_LOG_PATH)
    results = []

    for entry in logs:
        if context_id and entry.get("context_id") != context_id:
            continue
        if emotion_type and entry.get("emotion_type") != emotion_type:
            continue
        results.append(entry)

    return results

def update_emotion_log(
    timestamp: str,
    updated_fields: Dict[str, Any]
) -> bool:
    """
    Updates a previously logged emotion entry by timestamp.

    :param timestamp: Original ISO timestamp of the entry
    :param updated_fields: Fields to update (e.g., intensity, emotion_type)
    :return: True if update successful, False if not found
    """
    logs = _read_jsonl(EMOTION_LOG_PATH)
    updated = False

    for entry in logs:
        if entry["timestamp"] == timestamp:
            entry.update(updated_fields)
            updated = True
            break

    if updated:
        with open(EMOTION_LOG_PATH, "w", encoding="utf-8") as f:
            for entry in logs:
                f.write(json.dumps(entry) + "\n")

    return updated
