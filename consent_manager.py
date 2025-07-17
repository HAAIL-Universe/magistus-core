# consent_manager.py

from typing import Callable, Any

# Default action types that require explicit user approval
CRITICAL_ACTIONS = {
    "file_write",
    "memory_update",
    "plan_override",
    "goal_deletion",
    "external_api_call"
}

def requires_consent(action_type: str, details: str = "") -> bool:
    """
    Returns True if this action type is flagged for user approval.
    """
    return action_type in CRITICAL_ACTIONS

def request_user_consent(action_type: str, details: str = "") -> bool:
    """
    Simulated user approval request.
    In production, this should trigger a front-end dialog.
    """
    print(f"\n🔒 CONSENT REQUIRED for action: {action_type}")
    print(f"🔍 Details: {details}")
    print("⚠️  [Simulated] Auto-approving for now...\n")
    return True  # Replace with real UI callback in production

def execute_with_consent(action_fn: Callable[[], Any], action_type: str, details: str = "") -> Any:
    """
    Wraps any critical action and only executes it if user grants consent.
    """
    if requires_consent(action_type, details):
        approved = request_user_consent(action_type, details)
        if approved:
            return action_fn()
        else:
            print(f"[Consent Manager] Action '{action_type}' was denied by the user.")
            return None
    else:
        return action_fn()
