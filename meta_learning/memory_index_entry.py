from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path
import logging

# ----------------------------
# 📦 Memory Entry Model
# ----------------------------

class MemoryIndexEntry(BaseModel):
    """
    A structured memory log entry used by Magistus to reflect,
    evaluate, and later retrieve cognitive milestones or philosophical insights.
    """
    id: str = Field(..., description="Unique identifier for the memory entry (e.g., timestamp or UUID).")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time when the memory was created.")
    tags: List[str] = Field(default_factory=list, description="Relevant themes or categories.")
    context: str = Field(..., description="The conversational or cognitive context in which this memory arose.")
    insight: Optional[str] = Field(None, description="The distilled reflection or takeaway.")
    behavioral_adjustment: Optional[str] = Field(None, description="How Magistus should adapt based on this reflection.")
    reflective_summary: Optional[str] = Field(None, description="Optional summary given to the user.")
    relevance_score: float = Field(1.0, ge=0.0, le=1.0, description="Score for how crucial this memory is (default: 1.0).")
    meta_reflection: Optional[str] = Field(None, description="Post-hoc introspective commentary on the entry.")
    agent: Optional[str] = Field(None, description="Agent or module that created this memory.")
    goals: Optional[List[str]] = Field(default_factory=list, description="User or system goals related to the memory.")
    flags: Optional[dict] = Field(default_factory=dict, description="Any ethical/safety/etc. flags.")
    persona_updates: Optional[dict] = Field(default_factory=dict, description="Updates to persona model if any.")

# ----------------------------
# 📁 Paths & Globals
# ----------------------------

SHORT_TERM_MEMORY_DIR = Path("short_term_memory")

def load_memory_index(limit: int = 100) -> List[dict]:
    """
    Dynamically loads the latest `limit` short-term memory summaries
    from the short_term_memory folder, sorted by timestamp.
    """
    entries = []

    if not SHORT_TERM_MEMORY_DIR.exists():
        logging.warning(f"Short-term memory folder not found: {SHORT_TERM_MEMORY_DIR}")
        return []

    files = sorted(SHORT_TERM_MEMORY_DIR.glob("*.json"), reverse=True)

    for fpath in files:
        if len(entries) >= limit:
            break

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = json.load(f)
                entry = MemoryIndexEntry(**raw)
                entries.append(entry.dict())
        except Exception as e:
            logging.warning(f"⛔ Failed to parse short-term memory file '{fpath.name}': {e}")
            continue

    return entries
