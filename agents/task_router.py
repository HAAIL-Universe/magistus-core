# agents/task_router.py

from typing import List, Dict
import re

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg: object) -> None: pass  # Correct param name + type

class TaskRouter:
    """
    Symbolic task dispatcher for routing tasks to capable agents.
    Matches declared capabilities to inferred task requirements.
    """

    def __init__(self):
        # agent_name -> list of capabilities
        self.agent_registry: Dict[str, List[str]] = {}

        # Mapping of keywords → capability tags
        self.keyword_map: Dict[str, str] = {
            r"\b(plan|goal|roadmap|steps|strategy)\b": "planning",
            r"\b(memory|recall|retrieve|remember)\b": "memory",
            r"\b(think|reason|analyze|logic|deduce)\b": "logic",
            r"\b(emotion|feel|empathy|psychology)\b": "emotion",
            r"\b(creative|brainstorm|invent|imagine)\b": "creativity",
            r"\b(ethic|moral|should|fair)\b": "ethics",
        }

    def register_agent(self, agent_name: str, capabilities: List[str]):
        """
        Register an agent with its declared capability tags.
        """
        self.agent_registry[agent_name] = capabilities
        log_debug(f"[TaskRouter] Registered agent: {agent_name} with capabilities: {capabilities}")

    def route_task(self, task: str) -> List[str]:
        """
        Determine which agents are best suited to handle a given task.
        Basic implementation: keyword-to-capability mapping + agent lookup.
        """
        inferred_caps = self._infer_capabilities(task)
        matched_agents = []

        for agent_name, caps in self.agent_registry.items():
            if any(c in caps for c in inferred_caps):
                matched_agents.append(agent_name)

        log_debug(f"[TaskRouter] Task routed: '{task}' → {matched_agents} (via capabilities: {inferred_caps})")
        return matched_agents

    def _infer_capabilities(self, task: str) -> List[str]:
        """
        Match task string against known keyword-capability pairs.
        Returns a deduplicated list of inferred capability tags.
        """
        caps = set()
        for pattern, tag in self.keyword_map.items():
            if re.search(pattern, task, re.IGNORECASE):
                caps.add(tag)
        return list(caps)

    def __repr__(self):
        return f"<TaskRouter: {len(self.agent_registry)} agents registered>"
