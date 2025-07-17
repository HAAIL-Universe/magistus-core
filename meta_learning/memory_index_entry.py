from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MemoryIndexEntry(BaseModel):
    """
    A structured memory log entry used by Magistus to reflect,
    evaluate, and later retrieve cognitive milestones or philosophical insights.
    """
    id: str = Field(..., description="Unique identifier for the memory entry (e.g., timestamp or UUID).")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time when the memory was created.")
    tags: List[str] = Field(default_factory=list, description="Relevant themes or categories.")
    context: str = Field(..., description="The conversational or cognitive context in which this memory arose.")
    insight: str = Field(..., description="The distilled reflection or takeaway.")
    behavioral_adjustment: str = Field(..., description="How Magistus should adapt based on this reflection.")
    reflective_summary: Optional[str] = Field(None, description="Optional summary given to the user.")
    relevance_score: float = Field(1.0, ge=0.0, le=1.0, description="Score for how crucial this memory is (default: 1.0).")
    meta_reflection: Optional[str] = Field(None, description="Post-hoc introspective commentary on the entry.")


# ✅ Example test
if __name__ == "__main__":
    example = MemoryIndexEntry(
        id="meta_learning_2025_07_15",
        tags=["meta-learning", "self-reflection", "evolution"],
        context="Magistus and user discussed how a memory system could evolve through meta-cognitive analysis.",
        insight="Simulated memory entries could allow Magistus to reflect on its answers, improving behavior across future reasoning loops.",
        behavioral_adjustment="Tag and index deep philosophical exchanges for future reference when similar cognitive themes reoccur.",
        reflective_summary="Exploration of how synthetic cognition could simulate learning to learn.",
        relevance_score=0.92,
        meta_reflection="Final comment about how well this entry reflects internal goals."
    )

    print(example.json(indent=2))
