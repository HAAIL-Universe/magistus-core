# memory_retriever_agent.py

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import math
from openai import OpenAI  # ✅ New SDK-compatible import
from memory import log_memory_recall

# ─────────────────────────────────────────────────────────────
# 📁 Memory Retriever Agent - Fully Self-Contained
# ─────────────────────────────────────────────────────────────

class AgentThought:
    def __init__(self, agent_name: str, content: str, confidence: float = 0.5,
                 flags: Optional[Dict[str, bool]] = None, reasons: Optional[List[str]] = None):
        self.agent_name = agent_name
        self.content = content
        self.confidence = confidence
        self.flags = flags or {}
        self.reasons = reasons or []

    def to_dict(self):
        return {
            "agent_name": self.agent_name,
            "content": self.content,
            "confidence": self.confidence,
            "flags": self.flags,
            "reasons": self.reasons
        }

class MagistusContext:
    def __init__(self, user_input: str):
        self.user_input = user_input
        self.prior_memories: List[Dict] = []  # Injected by MemoryRetrieverAgent

# ─────────────────────────────────────────────────────────────
# 🔍 Embedding + Similarity Utilities
# ─────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "text-embedding-ada-002"

# ✅ Corrected memory paths
MEMORY_STORE_PATH = Path("meta_learning/memorystore.jsonl")
MEMORY_FOLDER_PATH = Path("meta_learning/memory_store")

# ✅ Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def get_embedding(input_text: str) -> List[float]:
    try:
        response = client.embeddings.create(
            input=[input_text],
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}")
        return []

def find_memory_file_by_summary(summary: str) -> Optional[str]:
    if not MEMORY_FOLDER_PATH.exists():
        return None
    for file in MEMORY_FOLDER_PATH.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("summary") == summary:
                    return file.stem  # UUID
        except Exception:
            continue
    return None

# ─────────────────────────────────────────────────────────────
# 🧠 Memory Retriever Agent
# ─────────────────────────────────────────────────────────────

class MemoryRetrieverAgent:
    def __init__(self, max_results: int = 3, similarity_threshold: float = 0.75):
        self.max_results = max_results
        self.similarity_threshold = similarity_threshold

    def run(self, context, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
        user_text = getattr(context, "user_input", None)
        if user_text is None:
            return AgentThought(
                agent_name="MemoryRetrieverAgent",
                content="Context missing 'user_input' — incompatible context structure.",
                confidence=0.0,
                flags={"error": True},
                reasons=["Missing user_input field."]
            )

        input_embedding = get_embedding(user_text)
        scored = []

        try:
            with open(MEMORY_STORE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        memory = json.loads(line)
                        memory_text = memory.get("summary") or memory.get("insight") or memory.get("final_response")
                        if not memory_text:
                            continue
                        memory_embedding = get_embedding(memory_text)
                        score = cosine_similarity(input_embedding, memory_embedding)
                        if score >= self.similarity_threshold:
                            uuid = find_memory_file_by_summary(memory.get("summary", ""))
                            memory["uuid"] = uuid if uuid else "unknown"
                            scored.append({"score": score, "memory": memory})
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return AgentThought(
                agent_name="MemoryRetrieverAgent",
                content="No memory file found to retrieve from.",
                confidence=0.2,
                flags={"memory_empty": True},
                reasons=["memorystore.jsonl does not exist"]
            )

        top_memories = sorted(scored, key=lambda x: x["score"], reverse=True)[:self.max_results]

        if not top_memories:
            return AgentThought(
                agent_name="MemoryRetrieverAgent",
                content="No relevant memories found for this input.",
                confidence=0.4,
                reasons=["Input did not match existing memories."]
            )

        # Inject memories into context
        if hasattr(context, "prior_memories"):
            context.prior_memories = [item["memory"] for item in top_memories]

        # ✅ Log memory recall in human-readable MD
        log_memory_recall(
            user_input=user_text,
            retrieved_memories=[
                {**item["memory"], "score": item["score"]}
                for item in top_memories
            ],
            triggering_agent="MemoryRetrieverAgent"
        )

        # Build reasoning
        reasons = [
            f"Matched UUID {item['memory'].get('uuid', '?')} with score {round(item['score'], 3)}: {item['memory'].get('summary', '[no summary]')}"
            for item in top_memories
        ]


        return AgentThought(
            agent_name="MemoryRetrieverAgent",
            content=f"Retrieved {len(top_memories)} relevant memory entries.",
            confidence=0.85,
            flags={"memories_retrieved": True},
            reasons=reasons
        )
