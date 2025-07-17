import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

JSON_LOG_FILE = Path("memorystore.jsonl")

def log_json_memory(
    user_input: str,
    timestamp: str,
    agent: str,
    round1: Optional[str],
    round2: Optional[str],
    final_response: Optional[str],
    debug_metadata: Optional[str],
    goals: List[str],
    flags: Dict[str, bool],
    summary: str,
    adjustment: str,
    tags: List[str],
    summary_tags: List[str],
    persona_updates: Dict[str, Any]
) -> None:
    """
    Appends a structured memory entry to memorystore.jsonl for long-term reflection and recall.
    """
    entry = {
        "user_input": user_input,
        "timestamp": timestamp,
        "agent": agent,
        "round1": round1,
        "round2": round2,
        "final_response": final_response,
        "debug_metadata": debug_metadata,
        "goals": goals,
        "flags": flags,
        "summary": summary,
        "adjustment": adjustment,
        "tags": tags,
        "summary_tags": summary_tags,
        "persona_updates": persona_updates
    }

    try:
        with open(JSON_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"❌ Failed to log structured memory entry: {e}")
