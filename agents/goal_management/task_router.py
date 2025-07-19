from typing import List, Dict, Optional
import re
from datetime import datetime
from context_types import AgentThought, ContextBundle

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg: object) -> None: pass

try:
    from memory import log_memory
except ImportError:
    log_memory = None

class TaskRouter:
    """
    Symbolic task dispatcher for routing tasks to capable agents.
    Now enhanced with optional goal context to improve routing decisions.
    """

    def __init__(self):
        self.agent_registry: Dict[str, List[str]] = {}
        self.name = "task_router"
        self.description = (
            "Routes user input to relevant agents based on symbolic keyword-to-capability matching. "
            "Also optionally references stored goals for improved contextual alignment."
        )

        self.keyword_map: Dict[str, str] = {
            r"\b(plan|goal|roadmap|steps|strategy)\b": "planning",
            r"\b(memory|recall|retrieve|remember)\b": "memory",
            r"\b(think|reason|analyze|logic|deduce)\b": "logic",
            r"\b(emotion|feel|empathy|psychology)\b": "emotion",
            r"\b(creative|brainstorm|invent|imagine)\b": "creativity",
            r"\b(ethic|moral|should|fair)\b": "ethics",
        }

    def register_agent(self, agent_name: str, capabilities: List[str]):
        self.agent_registry[agent_name] = capabilities
        log_debug(f"[TaskRouter] Registered agent: {agent_name} with capabilities: {capabilities}")

    def _infer_capabilities(self, task: str) -> List[str]:
        caps = set()
        for pattern, tag in self.keyword_map.items():
            if re.search(pattern, task, re.IGNORECASE):
                caps.add(tag)
        return list(caps)

    def _cross_reference_goals(self, task: str, goal_tracker) -> Optional[List[str]]:
        """Return additional inferred capabilities based on matching task text with known goal descriptions."""
        additional_caps = set()
        user_words = set(re.findall(r'\w+', task.lower()))

        try:
            for goal in goal_tracker.get_active_goals():
                goal_words = set(re.findall(r'\w+', goal.description.lower()))
                overlap = user_words.intersection(goal_words)
                if overlap:
                    log_debug(f"[TaskRouter] Matched keywords with goal '{goal.description[:50]}...' → {overlap}")
                    additional_caps.add("planning")
        except Exception as e:
            log_debug(f"[TaskRouter] Goal reference failed: {e}")

        return list(additional_caps) if additional_caps else None

    def route_task(self, task: str, goal_tracker=None) -> List[str]:
        inferred_caps = set(self._infer_capabilities(task))

        if goal_tracker:
            goal_based_caps = self._cross_reference_goals(task, goal_tracker)
            if goal_based_caps:
                inferred_caps.update(goal_based_caps)

        matched_agents = [
            name for name, caps in self.agent_registry.items()
            if any(cap in caps for cap in inferred_caps)
        ]

        log_debug(f"[TaskRouter] Task routed: '{task}' → {matched_agents} (via capabilities: {list(inferred_caps)})")
        return matched_agents

    def run(self, context: ContextBundle, prior_thoughts=None) -> AgentThought:
        user_input = context.user_input
        goal_tracker = context.services.get("goal_tracker") if context.services else None

        inferred_caps = self._infer_capabilities(user_input)
        if goal_tracker:
            goal_caps = self._cross_reference_goals(user_input, goal_tracker)
            if goal_caps:
                inferred_caps.extend(goal_caps)

        inferred_agents = self.route_task(user_input, goal_tracker)

        response = (
            f"📥 Input: '{user_input}'\n"
            f"🔍 Inferred capabilities: {inferred_caps}\n"
            f"✅ Suggested agents: {inferred_agents}"
        )

        # ✅ Trinity-compatible transparency logging
        if log_memory:
            try:
                log_memory(
                    context=context,
                    agent_name="task_router",
                    insight=f"Capabilities inferred: {inferred_caps}",
                    behavioral_adjustment="Agent selection aligned to symbolic and goal-based routing.",
                    reflective_summary=response,
                    relevance_score=0.85,
                    warnings=None,
                    tags=["task_routing", "transparency"],
                    markdown_text=response  # ✅ Add this
                )
            except Exception as e:
                log_debug(f"[TaskRouter] Memory log failed: {e}")

        return AgentThought(
            agent_name="task_router",
            content=response,
            confidence=1.0,
            reasons=["inferred from keyword-capability map and goal context"],
            requires_memory=False,
            flags={}
        )

    def __repr__(self):
        return f"<TaskRouter: {len(self.agent_registry)} agents registered>"
