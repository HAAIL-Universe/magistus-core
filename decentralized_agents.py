# decentralized_agents.py

import requests
import json
import os
from typing import Dict, Optional

from context_types import ContextBundle, AgentThought
from agents.agent_registry import agent_registry
from config_loader import load_config

# Load config
config = load_config()
DECENTRALIZED_MODE = config.get("decentralization_enabled", False)
ALLOW_FALLBACK = config.get("agent_fallback_enabled", True)

# Global registry for decentralized agents
_REMOTE_AGENT_REGISTRY: Dict[str, str] = {}

def register_remote_agent(agent_name: str, endpoint_url: str):
    """
    Registers a remote agent's endpoint.
    """
    _REMOTE_AGENT_REGISTRY[agent_name] = endpoint_url
    print(f"[Decentralized] Registered remote agent: {agent_name} → {endpoint_url}")


def get_registered_agents() -> Dict[str, str]:
    """
    Returns current remote agent registry.
    """
    return _REMOTE_AGENT_REGISTRY


def send_context_to_remote_agent(context: ContextBundle, agent_name: str) -> AgentThought:
    """
    Sends context to a remote agent over HTTP and returns its AgentThought.
    """
    if not DECENTRALIZED_MODE:
        raise RuntimeError("Decentralization is disabled in config.")

    endpoint = _REMOTE_AGENT_REGISTRY.get(agent_name)
    if not endpoint:
        raise ValueError(f"No remote endpoint registered for: {agent_name}")

    try:
        payload = json.dumps(
            context.dict(exclude_unset=True, exclude_none=True),
            indent=2,
            ensure_ascii=False
        )
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{endpoint}/think", data=payload, headers=headers, timeout=8)

        if response.status_code == 200:
            data = response.json()
            return AgentThought(**data)
        else:
            raise RuntimeError(
                f"[{agent_name}] Remote call failed: {response.status_code} {response.text}"
            )

    except Exception as e:
        print(f"[Decentralized] Remote call failed for {agent_name}: {e}")
        if ALLOW_FALLBACK:
            return fallback_to_local(agent_name, context)
        else:
            return AgentThought(
                agent_name=agent_name,
                content=f"Remote agent call failed and fallback disabled: {str(e)}",
                confidence=0.0,
                reasons=["network error"],
                requires_memory=False,
                flags={"error": True}
            )


def fallback_to_local(agent_name: str, context: ContextBundle) -> AgentThought:
    """
    Attempts to run local version of agent if remote fails.
    """
    local_agent = agent_registry.get(agent_name)
    if not local_agent:
        return AgentThought(
            agent_name=agent_name,
            content=f"No local fallback available for {agent_name}.",
            confidence=0.0,
            reasons=["missing fallback"],
            requires_memory=False,
            flags={"error": True}
        )

    print(f"[Fallback] Running `{agent_name}` locally.")
    return local_agent(context)
