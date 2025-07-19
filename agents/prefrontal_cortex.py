# agents/prefrontal_cortex.py

from context_types import ContextBundle, AgentThought
from typing import List, Optional
from ethical.ethical_compass import EthicalCompass
import json
import os

try:
    from llm_wrapper import generate_response
except ImportError:
    def generate_response(
        prompt: str,
        system_prompt: str = "You are Magistus, an ethical synthetic cognition assistant.",
        model: str = "gpt-4-0125-preview"
    ) -> str:
        return "[Fallback] Reasoning unavailable."


# NEW: Import memory summarizer
try:
    from utils.memory_summary import summarize_prior_memories
except ImportError:
    def summarize_prior_memories(context, max_entries=3):
        if not hasattr(context, "prior_memories") or not context.prior_memories:
            return "None available."
        memories = []
        for mem in context.prior_memories[:max_entries]:
            summary = mem.get("reflective_summary") or mem.get("insight") or mem.get("content") or ""
            if summary:
                memories.append(f"- {summary.strip()}")
        return "\n".join(memories) if memories else "None available."


def detect_conflicts(input_text: str, memory_matches: List[str], prior_thoughts: List[AgentThought]) -> bool:
    contradiction_keywords = ["not", "never", "impossible", "conflict", "disagree"]
    hits = sum(any(kw in input_text.lower() for kw in contradiction_keywords) for _ in memory_matches)
    hits += sum(any(kw in t.content.lower() for kw in contradiction_keywords) for t in prior_thoughts)
    return hits > 0


def motivational_boost(input_text: str) -> Optional[str]:
    cues = ["goal", "plan", "next step", "improve", "better", "build", "future", "overcome"]
    if any(cue in input_text.lower() for cue in cues):
        try:
            return generate_response(
                prompt=(
                    f"The user appears to be reflecting on a challenge or aspiration:\n\n"
                    f"\"{input_text}\"\n\n"
                    "Offer a short motivational boost (1–2 sentences). Avoid clichés, avoid pressure. "
                    "Be gentle, affirming, and always respectful of the user's autonomy."
                ),
                system_prompt=(
                    "You are Magistus' motivational subagent. "
                    "Speak with emotional intelligence. Never exaggerate or manipulate. "
                    "Your tone is calm, supportive, and real."
                )
            ).strip()
        except Exception:
            return None
    return None


def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:

    prior_thoughts = prior_thoughts or []
    input_text = context.user_input.lower()
    memory_used = context.memory_matches if context.config.get("debug_mode", False) else []

    # NEW: summarize prior memory (safe fallback logic included)
    memory_context = summarize_prior_memories(context)

    has_conditional = any(w in input_text for w in ["if", "then", "therefore", "because"])
    has_planning = any(w in input_text for w in ["plan", "should", "need to", "must", "goal", "strategy", "next step"])
    has_ethics = any(w in input_text for w in ["should i", "right thing", "is it ethical", "ought to"])

    reasons = []
    if has_conditional:
        reasons.append("logical construct")
    if has_planning:
        reasons.append("planning detected")
    if has_ethics:
        reasons.append("moral reasoning")
    if not reasons:
        reasons.append("general reasoning")

    conflict_detected = detect_conflicts(input_text, memory_used, prior_thoughts)
    if conflict_detected:
        reasons.append("conflict in reasoning")

    confidence = 0.75
    if has_conditional:
        confidence += 0.05
    if has_planning:
        confidence += 0.05
    if has_ethics:
        confidence += 0.02
    if conflict_detected:
        confidence -= 0.1
    confidence = round(max(min(confidence, 0.95), 0.5), 2)

    # ✅ SYSTEM PROMPT DEFINING AGENT ROLE
    system_prompt = (
        "You are the Prefrontal Cortex of a synthetic AGI named Magistus.\n"
        "Your cognitive role is strategic reasoning, planning assessment, and ethical foresight.\n"
        "Be objective, concise, and ethical. Avoid repetition or filler."
    )

    # ✅ Use dynamic prompt if provided
    dynamic_prompt = (
        context.dynamic_prompt_state.get("prefrontal_cortex")
        if hasattr(context, "dynamic_prompt_state") and isinstance(context.dynamic_prompt_state, dict)
        else None
    )

    if dynamic_prompt:
        prompt = dynamic_prompt
    else:
        prompt = (
            f"USER INPUT:\n\"{context.user_input}\"\n\n"
            f"RELEVANT MEMORY SNAPSHOTS:\n{memory_context}\n\n"
            "TASK:\n"
            "- Analyze the user's reasoning pattern, emotional state, or decision framing.\n"
            "- Identify intent, logic flow, potential contradictions, or ethical tension.\n"
            "- Summarize clearly in plain language with high cognitive clarity.\n"
        )

    try:
        llm_output = generate_response(prompt=prompt, system_prompt=system_prompt).strip()
    except Exception:
        llm_output = "[Reasoning unavailable]"

    # ✅ ETHICS CHECK (via ethical_compass)
    try:
        compass = EthicalCompass()
        ethics_result = compass.evaluate_input(context.user_input)
        ethics_json = json.loads(ethics_result)
        if ethics_json.get("violation") == "yes":
            llm_output += f"\n⚠️ Ethical Flag: {ethics_json.get('justification', '')}"
    except Exception:
        llm_output += "\n⚠️ Ethical check failed to parse."

    # ✅ MOTIVATION BOOST (optional)
    motivator = motivational_boost(input_text)
    if motivator:
        llm_output += f"\n\n💡 {motivator}"

    try:
        from datetime import datetime
        os.makedirs("logs", exist_ok=True)

        if context.config.get("log_prompts", False):
            log_entry = {
                "agent": "prefrontal_cortex",
                "timestamp": datetime.utcnow().isoformat(),
                "system_prompt": system_prompt,
                "prompt": prompt,
                "llm_output": llm_output,
                "user_input": context.user_input
            }

            with open("logs/prompt_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        print(f"[LOGGING ERROR - Prefrontal Cortex] Failed to save prompt log: {e}")

    return AgentThought(
        agent_name="prefrontal_cortex",
        confidence=confidence,
        content=llm_output,
        reasons=reasons + memory_used[:1],
        requires_memory=True,
        flags={
            "contradiction": conflict_detected,
            "insight": True
        }
    )
