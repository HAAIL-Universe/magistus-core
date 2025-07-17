from context_types import ContextBundle, AgentThought
from typing import List, Optional
from llm_wrapper import generate_response

def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
    memory_matches = context.memory_matches or []
    debug_mode = context.config.get("debug_mode", False)
    memory_used = memory_matches if debug_mode else []
    input_text = context.user_input.lower()

    conflict_keywords = ["but", "however", "although", "confused", "uncertain", "conflict", "mixed feelings"]
    motivational_keywords = ["should", "need", "want", "try", "goal", "effort", "must", "i will", "no matter what"]
    hesitation_keywords = ["maybe", "not sure", "i guess", "possibly", "i think"]

    detected_conflict = any(kw in input_text for kw in conflict_keywords)
    motivational_tone = any(kw in input_text for kw in motivational_keywords)
    strong_conviction = any(kw in input_text for kw in ["i must", "i will", "no matter what"])
    hesitation_detected = any(kw in input_text for kw in hesitation_keywords)

    optimistic_refs = ["hope", "i can", "getting better", "progress", "excited", "ready"]
    pessimistic_refs = ["stuck", "can't", "overwhelmed", "confused", "regret", "lost"]

    optimistic_count = sum(1 for m in memory_matches if any(o in m.lower() for o in optimistic_refs))
    pessimistic_count = sum(1 for m in memory_matches if any(p in m.lower() for p in pessimistic_refs))
    mood_delta = optimistic_count - pessimistic_count

    if mood_delta > 2:
        mood_trend = "improving"
    elif mood_delta < -2:
        mood_trend = "declining"
    else:
        mood_trend = "stable"

    confidence = 0.55
    if strong_conviction:
        confidence += 0.2
    elif motivational_tone:
        confidence += 0.1

    if detected_conflict:
        confidence -= 0.1
    if hesitation_detected:
        confidence -= 0.05
    if mood_trend == "improving":
        confidence += 0.05
    elif mood_trend == "declining":
        confidence -= 0.05

    confidence = round(min(max(confidence, 0.0), 0.95), 2)

    if confidence > 0.8:
        ethical_tag = "encouragement"
    elif confidence < 0.4 or detected_conflict:
        ethical_tag = "caution"
    else:
        ethical_tag = "neutral"

    reasoning_note = (
        "Conflict and uncertainty present despite motivational effort."
        if detected_conflict and motivational_tone else
        "Clear conviction observed with mild emotional resistance."
        if strong_conviction and detected_conflict else
        "Moderate motivational tone with emotional stability."
        if motivational_tone else
        "No motivational force or cognitive conflict detected."
    )

    prompt = (
        f"You are simulating the anterior cingulate cortex — the internal emotional evaluator.\n\n"
        f"User input: \"{context.user_input}\"\n"
        f"Recent memory fragments: {memory_used[:2]}\n"
        f"Mood trend: {mood_trend}\n\n"
        f"Analyze:\n"
        f"- Motivational intensity vs hesitation\n"
        f"- Emotional trajectory over time\n"
        f"- Conflict signals vs alignment cues\n\n"
        f"Respond in 1–2 sentences as a cognitive-emotional insight."
    )

    try:
        llm_output = generate_response(prompt).strip()
    except Exception:
        llm_output = "User displays emotional fluctuation with moderate decision readiness."

    return AgentThought(
        agent_name="anterior_cingulate",
        confidence=confidence,
        content=llm_output,
        reasons=[
            reasoning_note,
            f"mood trend: {mood_trend}",
            "motivational intent detected" if motivational_tone else "low motivation",
            "hesitation markers present" if hesitation_detected else "confident tone",
            "conflict present" if detected_conflict else "no contradiction",
            *memory_used[:1]
        ],
        requires_memory=True,
        flags={
            "contradiction": detected_conflict or hesitation_detected,
            "insight": motivational_tone,
            "is_encouraging": ethical_tag == "encouragement",
            "is_cautious": ethical_tag == "caution",
            "is_neutral": ethical_tag == "neutral",
            "self_assessment_ready": True
        }
    )
