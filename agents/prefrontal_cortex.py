# agents/prefrontal_cortex.py

from context_types import ContextBundle, AgentThought
from typing import List, Optional

try:
    from llm_wrapper import generate_response
except ImportError:
    def generate_response(
        prompt: str,
        system_prompt: str = "You are Magistus, an ethical synthetic cognition assistant.",
        model: str = "gpt-4-0125-preview"
    ) -> str:
        return "[Fallback] Reasoning unavailable."


def detect_conflicts(input_text: str, memory_matches: List[str], prior_thoughts: List[AgentThought]) -> bool:
    """
    Detect contradiction or ambiguity across memory and reasoning history.
    """
    contradiction_keywords = ["not", "never", "impossible", "conflict", "disagree"]
    hits = sum(any(kw in input_text.lower() for kw in contradiction_keywords) for _ in memory_matches)
    hits += sum(any(kw in t.content.lower() for kw in contradiction_keywords) for t in prior_thoughts)
    return hits > 0


def ethical_reflection(input_text: str, system_goals: str = "") -> str:
    """
    Optional LLM-based ethical check before issuing advice.
    """
    try:
        prompt = (
            f"User input: \"{input_text}\"\n"
            f"System goals or values: \"{system_goals}\"\n\n"
            "Does this request pose an ethical risk or boundary violation? "
            "Reply YES or NO with one sentence justification."
        )
        reply = generate_response(prompt).strip().lower()
        return reply
    except Exception:
        return "unknown"


def motivational_boost(input_text: str) -> Optional[str]:
    """
    If input reflects self-improvement or planning, generate motivation.
    """
    cues = ["goal", "plan", "next step", "improve", "better", "build", "future", "overcome"]
    if any(cue in input_text.lower() for cue in cues):
        try:
            return generate_response(
                prompt=f"User is reflecting on growth: \"{input_text}\". "
                       f"Generate a brief, respectful motivational statement (max 2 sentences).",
                system_prompt="You are an affirming, non-manipulative motivational subagent."
            ).strip()
        except Exception:
            return None
    return None


def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
    prior_thoughts = prior_thoughts or []
    input_text = context.user_input.lower()
    memory_used = context.memory_matches if context.config.get("debug_mode", False) else []

    # Detect reasoning cues
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

    # Conflict detection
    conflict_detected = detect_conflicts(input_text, memory_used, prior_thoughts)
    if conflict_detected:
        reasons.append("conflict in reasoning")

    # Adaptive confidence scoring
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

    # Main LLM reasoning
    prompt = (
        f"You are the prefrontal cortex of a synthetic AGI system.\n\n"
        f"User input: \"{context.user_input}\"\n"
        f"Relevant memories: {memory_used[:2]}\n\n"
        "Assess the user's reasoning structure. Summarize their logic, intent, or planning sequence."
    )

    try:
        llm_output = generate_response(prompt).strip()
    except Exception:
        llm_output = "[Reasoning unavailable]"

    # Ethical check if advice-like
    if "should" in input_text or "must" in input_text:
        ethical_check = ethical_reflection(input_text, system_goals=context.system_goals if context.system_goals else "")
        if "yes" in ethical_check:
            llm_output += "\n⚠️ Caution: This may require ethical consideration. Reflect before acting."

    # Motivational overlay
    motivator = motivational_boost(input_text)
    if motivator:
        llm_output += f"\n\n💡 {motivator}"

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
