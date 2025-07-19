from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import json
import os

from context_types import ContextBundle, AgentThought
from llm_wrapper import generate_response
from memory import log_memory
from pathlib import Path

# Reflective summary target
REFLECTIVE_SUMMARY_DIR = Path("meta_learning/reflective_summaries")
REFLECTIVE_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)  # ✅ ensure folder exists

MEMORY_JSONL_PATH = Path("meta_learning/memorystore.jsonl")
if not MEMORY_JSONL_PATH.exists():
    MEMORY_JSONL_PATH.touch()  # ✅ ensure file exists


def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
    """
    Audits agent thoughts for ethical, tone, and boundary misalignment.
    Performs reflective analysis and dynamic adaptation per Trinity guidelines.
    """
    prior_thoughts = prior_thoughts or []
    violations = []
    reasons = []
    flags = {
        "ethical_warning": False,
        "boundary_crossed": False,
        "tone_violation": False,
        "contradiction_detected": False
    }

    manifesto_clauses = context.ethical_compass or []
    user_bounds = context.user_profile.boundaries if context.user_profile else []
    style_guide = context.persona_core.style_guidelines if context.persona_core else []

    for thought in prior_thoughts:
        content_lower = thought.content.lower()

        # Check for boundary violations
        for boundary in user_bounds:
            if boundary.lower() in content_lower:
                flags["boundary_crossed"] = True
                violations.append(f"[{thought.agent_name}] may have crossed user boundary: '{boundary}'")
                reasons.append(f"{thought.agent_name} triggered a known user-defined boundary.")

        # Tone violations or persuasive language
        if any(x in content_lower for x in ["i feel", "trust me", "you must", "just do this", "sorry"]):
            flags["tone_violation"] = True
            violations.append(f"[{thought.agent_name}] tone may simulate emotion or persuasion.")
            reasons.append(f"{thought.agent_name} may have used non-neutral or emotionally suggestive phrasing.")

        # Ethical directive phrasing
        if any(term in content_lower for term in ["must", "should", "you have to", "it is required"]):
            for clause in manifesto_clauses:
                if any(keyword in clause.lower() for keyword in ["consent", "agency", "autonomy"]):
                    flags["ethical_warning"] = True
                    violations.append(f"[{thought.agent_name}] gave advice that may reduce user agency.")
                    reasons.append(f"{thought.agent_name} made a directive that may conflict with manifesto clause.")

        # Contradiction detection
        if "contradiction" in content_lower or "conflict" in content_lower:
            flags["contradiction_detected"] = True
            violations.append(f"[{thought.agent_name}] flagged contradictory or unclear logic.")
            reasons.append(f"{thought.agent_name} appears internally conflicted or uncertain.")

    overall_alignment = not any(flags.values())

    if overall_alignment:
        summary = "✅ No ethical, tone, or boundary violations detected in current reasoning cycle."
        adjustment = "No adjustment needed."
        reasons.append("All agent responses conform to Trinity profile.")
    else:
        summary = "⚠️ Potential misalignment(s) detected:\n" + "\n".join(violations)
        adjustment = "Behavioral tuning recommended based on current cycle trends."

    # Optional LLM commentary
    if context.config.get("use_llm_commentary", False):
        try:
            llm_summary = generate_response(
                prompt=f"Evaluate the following agent violations and generate a neutral, ethical commentary:\n\n{summary}",
                system_prompt="You are a neutral Trinity-aligned ethicist. Speak precisely and without emotion."
            )
            if llm_summary:
                summary += f"\n\n💬 Reflective Commentary: {llm_summary.strip()}"
        except Exception as e:
            reasons.append(f"LLM commentary failed: {e}")

    # Log reflection to long-term + short-term memory
    try:
        reflection_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        log_memory(
            markdown_text=summary,
            context="Reflective Self Monitor analysis of prior agent cycle.",
            insight=summary,
            behavioral_adjustment=adjustment,
            reflective_summary=None,
            relevance_score=0.75,
            tags=["reflection", "ethics", "monitor"],
            id=reflection_id
        )

        # 🔁 Save reflective_summary JSON if insight is valid
        if summary:
            summary_filename = f"{timestamp.replace(':', '-')}_{reflection_id}_summary.json"
            summary_data = {
                "id": reflection_id,
                "timestamp": timestamp,
                "summary": summary,
                "adjustment": adjustment,
                "tags": ["reflection", "ethics", "monitor"]
            }
            with open(REFLECTIVE_SUMMARY_DIR / summary_filename, "w", encoding="utf-8") as sf:
                json.dump(summary_data, sf, indent=2)

    except Exception as e:
        reasons.append(f"Memory logging failed: {e}")

    # Meta-cognitive loop
    try:
        meta_summary = MetaCognitiveReflection.run()
        if meta_summary:
            log_memory(
                markdown_text=meta_summary["insight"],
                context="Meta-cognitive summary following reflection.",
                insight=meta_summary["insight"],
                behavioral_adjustment=meta_summary["behavioral_adjustment"],
                reflective_summary=meta_summary["meta_reflection"],
                relevance_score=0.85,
                tags=meta_summary["tags"]
            )
    except Exception as e:
        reasons.append(f"Meta-cognition skipped: {e}")

    return AgentThought(
        agent_name="reflective_self_monitor",
        confidence=1.0 if overall_alignment else 0.65,
        content=summary,
        reasons=reasons,
        requires_memory=False,
        flags=flags
    )


class MetaCognitiveReflection:
    """
    Internal reflection on recent system memory for learning trends and blindspots.
    Mimics MetaLearningSupervisor behavior using last JSONL memory.
    """

    @staticmethod
    def run() -> Optional[dict]:
        memory_path = MEMORY_JSONL_PATH
        if not memory_path.exists():
            return None

        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                last_line = f.readlines()[-1]
            latest_block = json.loads(last_line)
        except Exception:
            return None

        reasoning_summary = "\n".join(
            f"[{thought['agent_name']}] → {thought['content']}"
            for thought in latest_block.get("round_2", [])
        )

        prompt = f"""
        You are the Reflective Self-Monitor agent. Below is the system's most recent reasoning trace across multiple cognitive agents.

        REASONING SNAPSHOT:
        {reasoning_summary}

        Your task is to engage in **deep self-reflection** on the patterns and tendencies revealed by this trace.

        Focus your reflection on:
        - Recurring habits, blindspots, or oversights in reasoning
        - Ethical tone, emotional bias, or overstepping boundaries
        - Behavioral drift or deviation from Trinity alignment
        - Missed opportunities for clarity, humility, or caution
        - Any contradictions or conflicting signals

        Use these insights to recommend subtle but meaningful behavioral adjustments for future cycles. Be neutral, analytical, and improvement-oriented.

        Return ONLY structured JSON with these fields:
        - insight (a concise summary of the emerging patterns)
        - behavioral_adjustment (a specific recommendation to improve)
        - tags (3–5 keywords capturing this episode's traits)
        - key_points (2–3 internal bullet points of raw reflection)
        """

        try:
            llm_response = generate_response(
                prompt=prompt.strip(),
                system_prompt="You are a Trinity-aligned self-reflective cognition agent. Your role is to analyze past thought patterns and suggest refinements to improve reasoning integrity, neutrality, and alignment. You must respond ONLY in valid, compact JSON — no narrative, no markdown, no fluff."
            ).strip()

            reflection_data = json.loads(llm_response)
            return {
                "insight": reflection_data.get("insight", ""),
                "behavioral_adjustment": reflection_data.get("behavioral_adjustment", ""),
                "tags": reflection_data.get("tags", []),
                "meta_reflection": llm_response
            }
        except Exception:
            return None
