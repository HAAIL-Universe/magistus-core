# agents/agent_registry.py

from agents.temporal_lobe import run as temporal_lobe
from agents.reflective_self_monitor import run as reflective_self_monitor
from agents.web_search_agent import run as web_search_agent

# If you have more agents, import them here

agent_registry = {
    "temporal_lobe": temporal_lobe,
    "reflective_self_monitor": reflective_self_monitor,
    "web_search_agent": web_search_agent,
    # Add other agents here
}
