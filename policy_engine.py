from typing import List
from context_types import ContextBundle, AgentThought
from agents.reflective_self_monitor import run as reflective_self_monitor
from consent_manager import request_user_consent

# Define what qualifies as a critical action
CRITICAL_ACTION_TYPES = {
    "memory_purge",
    "goal_override",
    "profile_rewrite",
    "external_execution",
    "agent_modification"
}

def is_critical_action(action_type: str, allow_self_eval: bool = False) -> bool:
    """
    Determine whether a given action type qualifies as critical.
    Allow bypass if self-eval mode is enabled.
    """
    if allow_self_eval:
        # In self-eval mode, allow critical actions (don't treat as blocking)
        return False
    return action_type in CRITICAL_ACTION_TYPES

def check_reflective_alignment(context: ContextBundle, agent_thoughts: List[AgentThought]) -> bool:
    """
    Ask the ReflectiveSelfMonitor to evaluate ethical and reflective alignment.
    Returns True if no warnings are raised.
    """
    monitor_result = reflective_self_monitor(context, agent_thoughts)
    return not monitor_result.flags.get("ethical_warning", False)

def enforce_reflection_policy(
    action_type: str,
    context: ContextBundle,
    agent_thoughts: List[AgentThought],
    details: str = "",
    allow_self_eval: bool = False
) -> str:
    """
    Determines whether to proceed, pause, or require user intervention before critical action.
    Returns: "approved", "requires_user", or "blocked"
    """
    if allow_self_eval:
        # Auto-approve all critical actions in self-eval mode
        return "approved"

    if not is_critical_action(action_type):
        return "approved"  # Non-critical, pass through

    aligned = check_reflective_alignment(context, agent_thoughts)

    if aligned:
        user_approval = request_user_consent(
            action_type,
            f"This is a critical action and passed reflective alignment.\n\nDetails:\n{details}"
        )
        return "approved" if user_approval else "requires_user"
    else:
        return "blocked"

def should_block_execution(
    action_type: str,
    context: ContextBundle,
    agent_thoughts: List[AgentThought],
    allow_self_eval: bool = False
) -> bool:
    """
    Convenience wrapper: returns True if action should be blocked.
    """
    status = enforce_reflection_policy(action_type, context, agent_thoughts, allow_self_eval=allow_self_eval)
    return status == "blocked"
