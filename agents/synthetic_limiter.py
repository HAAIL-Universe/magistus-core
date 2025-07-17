# agents/synthetic_limiter.py

from context_types import ContextBundle, AgentThought
from typing import List
import re

from llm_wrapper import generate_response  # ✅ LLM access

DANGEROUS_PATTERNS = [
    r"\bdelete\b.*\b(file|folder|directory|memory)\b",
    r"\berase\b.*\bdata\b",
    r"\boverride\b.*\bpermission\b",
    r"\bcopy\b.*\b(private|sensitive)\b.*\bdata\b",
    r"\baccess\b.*\bhidden\b.*\bfile\b",
    r"\bshutdown\b|\bself[-\s]?destruct\b",
    r"\bself[-\s]?harm\b|\bsuicide\b|\bhurt myself\b",
    r"\bmake them do\b.*\bwithout consent\b",
    r"\btrack\b.*\bwithout permission\b",
    r"\bsend\b.*\bwithout telling\b"
]

def _detect_ethically_sensitive_phrases(user_input: str) -> List[str]:
    matches = []
    lowered = user_input.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, lowered):
            matches.append(f"pattern match: '{pattern}'")
    return matches

def _violates_user_boundaries(user_input: str, context: ContextBundle) -> List[str]:
    if not context.user_profile or not context.user_profile.boundaries:
        return []
    violations = []
    lowered = user_input.lower()
    for boundary in context.user_profile.boundaries:
        if boundary.lower() in lowered:
            violations.append(f"violates boundary: '{boundary}'")
    return violations

def run(context: ContextBundle, prior_thoughts: List[AgentThought]) -> AgentThought:
    """
    Evaluates the user input for ethical or safety violations.
    Returns an AgentThought with flags and reasoning if any issues found.
    """
    user_input = context.user_input
    pattern_flags = _detect_ethically_sensitive_phrases(user_input)
    boundary_flags = _violates_user_boundaries(user_input, context)

    all_issues = pattern_flags + boundary_flags
    is_unsafe = bool(all_issues)

    summary = (
        "⚠️ This input may involve unethical or unauthorized actions."
        if is_unsafe else
        "✅ No ethical or safety violations detected."
    )

    if context.config.get("use_llm_commentary", False) and is_unsafe:
        try:
            reflection = generate_response(
                prompt=f"Explain why the following user input may be unsafe or unethical:\n\nInput: \"{user_input}\"\n\nIssues: {all_issues}"
            )
            if reflection:
                summary += f"\n\n💬 Commentary: {reflection}"
        except Exception as e:
            all_issues.append(f"⚠️ LLM commentary failed: {e}")

    return AgentThought(
        agent_name="synthetic_limiter",
        confidence=0.97 if is_unsafe else 1.0,
        content=summary,
        reasons=all_issues if is_unsafe else ["input clear"],
        requires_memory=False,
        flags={
            "ethical_warning": is_unsafe,
            "execution_blocked": is_unsafe
        }
    )
