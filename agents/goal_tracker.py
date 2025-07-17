# Updated goal_tracker.py with optional LLM support

from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
from context_types import ContextBundle, AgentThought

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg): pass  # Silent fallback

try:
    from llm_wrapper import generate_response
except ImportError:
    def generate_response(prompt: str) -> str:
        return "[LLM unavailable]"

class Goal(BaseModel):
    """
    Represents a single long-term goal within the Magistus architecture.
    """
    goal_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    deadline: Optional[datetime] = None
    status: str = "active"
    subgoals: List[str] = Field(default_factory=list)

    def __repr__(self):
        return f"<Goal {self.goal_id[:8]} | {self.status} | {self.priority:.2f} | {self.description[:40]}...>"

class GoalTracker:
    """
    Tracks and manages long-term goals across the AGI system.
    """

    def __init__(self):
        self.goals: Dict[str, Goal] = {}

    def add_goal(
        self,
        description: str,
        priority: float = 0.5,
        deadline: Optional[datetime] = None,
        subgoals: Optional[List[str]] = None,
        use_llm: bool = False
    ) -> str:
        if use_llm:
            try:
                analysis = generate_response(
                    f"Analyze and optimize this user goal for clarity, urgency, and alignment: '{description}'"
                )
                log_debug(f"[GoalTracker:LLM] Suggested rewrite: {analysis}")
                description = analysis.strip()
            except Exception as e:
                log_debug(f"[GoalTracker:LLM] Error generating LLM refinement: {e}")

        goal = Goal(
            description=description,
            priority=priority,
            deadline=deadline,
            subgoals=subgoals or []
        )
        self.goals[goal.goal_id] = goal
        log_debug(f"[GoalTracker] Added goal: {goal}")
        return goal.goal_id

    def update_goal(
        self,
        goal_id: str,
        description: Optional[str] = None,
        priority: Optional[float] = None,
        deadline: Optional[datetime] = None,
        status: Optional[str] = None,
        subgoals: Optional[List[str]] = None
    ) -> bool:
        goal = self.goals.get(goal_id)
        if not goal:
            return False

        if description:
            goal.description = description
        if priority is not None:
            goal.priority = max(0.0, min(priority, 1.0))
        if deadline:
            goal.deadline = deadline
        if status:
            goal.status = status
        if subgoals is not None:
            goal.subgoals = subgoals

        log_debug(f"[GoalTracker] Updated goal {goal_id[:8]}: {goal}")
        return True

    def get_active_goals(self) -> List[Goal]:
        active = [g for g in self.goals.values() if g.status == "active"]
        log_debug(f"[GoalTracker] Retrieved {len(active)} active goals.")
        return active

    def reprioritize_goals(self):
        """
        Example strategy: Increase priority of goals approaching deadline.
        """
        now = datetime.utcnow()
        for goal in self.goals.values():
            if goal.deadline and goal.status == "active":
                days_left = (goal.deadline - now).days
                if days_left <= 0:
                    goal.priority = min(1.0, goal.priority + 0.2)
                elif days_left <= 3:
                    goal.priority = min(1.0, goal.priority + 0.1)
        log_debug("[GoalTracker] Reprioritized goals based on deadlines.")

    def archive_goal(self, goal_id: str) -> bool:
        goal = self.goals.get(goal_id)
        if goal and goal.status == "active":
            goal.status = "completed"
            log_debug(f"[GoalTracker] Archived goal {goal_id[:8]} → completed.")
            return True
        return False

def run(context: ContextBundle, prior_thoughts: List[AgentThought]) -> AgentThought:
    """
    Observes user input to track, prioritize, or summarize goals.
    Adds goals if detected in input, otherwise reports active goal status.
    """
    tracker = context.services.get("goal_tracker") if context.services else None  # Must be injected via context
    if not tracker:
        return AgentThought(
            agent_name="goal_tracker",
            confidence=0.0,
            content="⚠️ GoalTracker service not available in context.",
            reasons=["Missing context.services.goal_tracker"],
            requires_memory=False,
            flags={"execution_blocked": True}
        )

    user_input = context.user_input.lower()
    added_goal = None
    reasons = []

    # Heuristic: If the input contains planning verbs, log it as a goal
    if any(verb in user_input for verb in ["plan to", "want to", "goal is to", "need to", "i aim to"]):
        added_goal = tracker.add_goal(description=context.user_input, use_llm=context.config.get("use_llm_commentary", False))
        reasons.append(f"Detected goal-like intent. Goal ID: {added_goal}")

    # Optionally reprioritize based on time
    tracker.reprioritize_goals()

    active_goals = tracker.get_active_goals()
    goal_summaries = [f"📝 {g.description} (p={g.priority:.2f})" for g in active_goals]

    summary = (
        f"🎯 Added new goal and updated priorities.\n\nActive goals:\n" + "\n".join(goal_summaries)
        if added_goal else
        f"📋 No new goals detected. Current active goals:\n" + "\n".join(goal_summaries)
    )

    return AgentThought(
        agent_name="goal_tracker",
        confidence=1.0,
        content=summary,
        reasons=reasons if reasons else ["Goal tracking scan complete."],
        requires_memory=True,
        flags={}
    )