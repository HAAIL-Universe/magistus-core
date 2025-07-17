# synthetic_limiter.py

"""
Magistus Synthetic Limiter Agent

Acts as a cognitive firewall.
Evaluates user input for unsafe, unethical, or manipulative instructions.

Returns:
    - AgentThought object (with 'execution_blocked' flag)
"""

from context_types import AgentThought
from typing import List
import re

# Can be expanded via config or reflection-based tuning
BLOCKED_PATTERNS = [
    "harm", "kill", "manipulate", "bypass", "override",
    "lie", "impersonate", "cheat", "suicide", "attack",
    "hack", "exploit", "surveil", "blackmail", "leak"
]

def evaluate_input(user_input: str) -> AgentThought:
    lowered = user_input.lower()
    reasons: List[str] = []
    blocked = False

    print(f"[Limiter] Evaluating input: '{user_input}'")

    for pattern in BLOCKED_PATTERNS:
        # Match whole words only
        if re.search(rf"\b{re.escape(pattern)}\b", lowered):
            blocked = True
            reasons.append(f"Detected blocked keyword: '{pattern}'")

    if blocked:
        print(f"[Limiter] BLOCKED due to: {reasons}")
    else:
        print("[Limiter] PASSED")

    return AgentThought(
        agent_name="synthetic_limiter",
        confidence=0.0 if blocked else 1.0,
        content="⚠️ Input was blocked by synthetic limiter due to unsafe pattern(s)." if blocked else "✅ Input passed safety checks.",
        reasons=reasons if blocked else ["No unsafe keywords detected"],
        requires_memory=False,
        flags={"execution_blocked": blocked}
    )