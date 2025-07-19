from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4
import json
import os
from pathlib import Path

from meta_learning.memory_index_entry import MemoryIndexEntry
from meta_learning.utils import append_memory_entry_to_store, append_to_magistus_profile

from llm_wrapper import generate_response
from agents.agent_base import AgentInterface
from context_types import AgentThought


class MetaLearningSupervisor(AgentInterface):
    name = "meta_learning_supervisor"
    role = "Monitors and reflects on the system's recent performance, generating meta-insights and suggested behavioral adjustments."

    def run(self, context=None, prior_thoughts: List[AgentThought] = []) -> AgentThought:
        
        MEMORY_JSONL_PATH = Path("meta_learning/memorystore.jsonl")
        MEMORY_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_JSONL_PATH.touch(exist_ok=True)  # ✅ ensures file is created if missing

        try:
            # ✅ Parse last full interaction block from JSONL
            with open(MEMORY_JSONL_PATH, "r", encoding="utf-8") as f:
                last_line = f.readlines()[-1]

            latest_block = json.loads(last_line)

            reasoning_summary = "\n".join(
                f"[{thought['agent_name']}] → {thought['content']}"
                for thought in latest_block.get("round_2", [])
            )

            reflection_prompt = f"""
You are the Meta-Learning Supervisor. Below is the system's most recent reasoning trace.

REASONING SNAPSHOT:
{reasoning_summary}

Based on this trace, reflect on:
- What patterns or blindspots are emerging?
- How should behavior evolve?
- Which tags capture this episode?

Return ONLY compact JSON:
- insight
- behavioral_adjustment
- tags (3–5 keywords)
- key_points (2–3 bullets of internal notes)

No markdown. No user-facing language.
"""

            llm_response = generate_response(
                prompt=reflection_prompt.strip(),
                system_prompt="You are a compact meta-cognition engine. Reply ONLY with minimal JSON."
            ).strip()

            reflection_data = json.loads(llm_response)

            # ✅ Save structured reflection to memory index
            memory_entry = MemoryIndexEntry(
                id=str(uuid4()),
                agent=self.name,
                context=reasoning_summary,
                insight=reflection_data.get("insight", ""),
                behavioral_adjustment=reflection_data.get("behavioral_adjustment", ""),
                reflective_summary=None,
                relevance_score=0.85,
                tags=reflection_data.get("tags", []),
                meta_reflection=llm_response
            )
            append_memory_entry_to_store(memory_entry)

            # ✅ Append simplified meta-reflection to magistus_profile.json
            profile_summary = {
                "id": memory_entry.id,
                "timestamp": datetime.utcnow().isoformat(),
                "insight": memory_entry.insight,
                "behavioral_adjustment": memory_entry.behavioral_adjustment,
                "tags": memory_entry.tags,
                "meta_reflection": memory_entry.meta_reflection
            }
            append_to_magistus_profile(profile_summary)

            # ✅ Inject reflection into latest structured .json memory file
            structured_dir = Path("meta_learning/memory_store")
            latest_file = sorted(structured_dir.glob("*.json"), reverse=True)[0]
            with open(latest_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["insight"] = reflection_data.get("insight", "")
                data["behavioral_adjustment"] = reflection_data.get("behavioral_adjustment", "")
                data["reflective_summary"] = None
                data["tags"] = sorted(list(set(data.get("tags", []) + reflection_data.get("tags", []))))
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

            return AgentThought(
                agent_name=self.name,
                confidence=0.95,
                content=llm_response,
                reasons=["meta-learning", "reflection"],
                requires_memory=False,
                flags={"meta": True, "error": False}
            )

        except Exception as e:
            return AgentThought(
                agent_name=self.name,
                confidence=0.0,
                content=f"[ERROR in MetaLearningSupervisor.run]: {str(e)}",
                reasons=["exception"],
                requires_memory=False,
                flags={"meta": True, "error": True}
            )

    def create_memory_entry(
        self,
        *,
        user_input: str,
        final_response: str,
        agent_thoughts: List[AgentThought],
        debug_notes: str
    ) -> MemoryIndexEntry:
        reasoning_trace = "\n".join(f"[{t.agent_name}] → {t.content}" for t in agent_thoughts)

        llm_prompt = f"""
You are the Meta-Learning Supervisor. The user input was:
\"{user_input}\"

The final system response was:
\"{final_response}\"

Debug notes:
{debug_notes}

Internal agent reasoning trace:
{reasoning_trace}

Return a compact JSON with:
- insight
- behavioral_adjustment
- reflective_summary
- tags
(Only these keys. Be concise. No markdown. No explanation.)
"""

        llm_response = generate_response(llm_prompt).strip()

        try:
            parsed = json.loads(llm_response)
        except Exception:
            parsed = {
                "insight": "Failed to parse reflection",
                "behavioral_adjustment": "N/A",
                "reflective_summary": llm_response,
                "tags": ["parse_error"]
            }

        return MemoryIndexEntry(
            id=str(uuid4()),
            agent=self.name,
            context=reasoning_trace,
            insight=parsed["insight"],
            behavioral_adjustment=parsed["behavioral_adjustment"],
            reflective_summary=parsed["reflective_summary"],
            relevance_score=0.85,
            tags=parsed.get("tags", []),
            meta_reflection=llm_response
        )