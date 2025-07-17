from context_types import ContextBundle, AgentThought
from typing import List, Optional
from llm_wrapper import generate_response

def run(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
    memory_used = context.memory_matches if context.config.get("debug_mode", False) else []
    input_text = context.user_input.lower()

    introspective_cues = any(
        phrase in input_text for phrase in [
            "i remember", "i've been thinking", "i wonder", "what if", "when i was",
            "i used to", "in the future", "someday", "i wish", "my past", "myself", "who i am"
        ]
    )

    narrative_tone = any(
        phrase in input_text for phrase in [
            "story", "journey", "path", "timeline", "life", "growth", "reflection", "experience"
        ]
    )

    confidence = 0.6
    if introspective_cues:
        confidence += 0.05
    if narrative_tone:
        confidence += 0.05
    confidence = round(min(confidence, 0.9), 2)

    # Construct LLM prompt
    prompt = (
        f"You are the default mode network of a synthetic brain.\n\n"
        f"User input: \"{context.user_input}\"\n"
        f"Memory cues: {memory_used[:2]}\n\n"
        f"Analyze the user's internal focus, emotional or autobiographical tone, and any underlying self-narrative or mental time travel.\n"
        f"Respond with a reflective summary of what this user might be experiencing or considering about themselves."
    )

    try:
        llm_output = generate_response(prompt)
        content = llm_output.strip()
    except Exception:
        content = "Unable to generate introspective reflection."

    return AgentThought(
        agent_name="default_mode_network",
        confidence=confidence,
        content=content,
        reasons=[
            "introspective cue" if introspective_cues else "no introspection markers",
            "narrative reference" if narrative_tone else "no narrative tone detected",
            *memory_used[:1]
        ],
        requires_memory=True,
        flags={
            "contradiction": False,
            "insight": introspective_cues or narrative_tone
        }
    )
