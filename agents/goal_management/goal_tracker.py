from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4
import os
import json
from pydantic import BaseModel, Field
from context_types import ContextBundle, AgentThought

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg): pass

try:
    from llm_wrapper import generate_response, get_embedding
except ImportError:
    def generate_response(prompt: str) -> str:
        return "[LLM unavailable]"
    def get_embedding(text: str) -> List[float]:
        return []

try:
    from memory import log_memory
    MEMORY_LOGGING_AVAILABLE = True
except ImportError:
    MEMORY_LOGGING_AVAILABLE = False

GOAL_STORE_PATH = "agents/goal_management/goal_store/goals.json"

class Goal(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    deadline: Optional[datetime] = None
    status: str = "active"
    subgoals: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None

    def __repr__(self):
        return f"<Goal {self.goal_id[:8]} | {self.status} | {self.priority:.2f} | {self.description[:40]}...>"

class GoalTracker:
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.load_goals_from_disk()

    def add_goal(
        self,
        description: str,
        priority: float = 0.5,
        deadline: Optional[datetime] = None,
        subgoals: Optional[List[str]] = None,
        use_llm: bool = False
    ) -> str:
        original_description = description

        if use_llm:
            try:
                analysis = generate_response(
                    f"Analyze and optimize this user goal for clarity, urgency, and alignment: '{description}'"
                )
                log_debug(f"[GoalTracker:LLM] Suggested rewrite: {analysis}")
                description = analysis.strip()
            except Exception as e:
                log_debug(f"[GoalTracker:LLM] Error generating LLM refinement: {e}")

        embedding = None
        try:
            embedding = get_embedding(description)
        except Exception as e:
            log_debug(f"[GoalTracker] Embedding failed: {e}")

        goal = Goal(
            description=description,
            priority=priority,
            deadline=deadline,
            subgoals=subgoals or [],
            embedding=embedding
        )
        self.goals[goal.goal_id] = goal
        log_debug(f"[GoalTracker] Added goal: {goal}")

        if MEMORY_LOGGING_AVAILABLE:
            try:
                subgoal_lines = "\n".join([f"  - {s}" for s in goal.subgoals]) if goal.subgoals else "  - None"
                markdown_text = f"""🎯 **New Goal Added**
- **ID**: `{goal.goal_id}`
- **Description**: {description}
- **Priority**: `{priority:.2f}`
- **Deadline**: `{deadline if deadline else "None"}`
- **Subgoals**:\n{subgoal_lines}
"""

                log_memory(
                    markdown_text=markdown_text,
                    timestamp=datetime.utcnow().isoformat(),
                    agent="goal_tracker",
                    summary=f"Added goal: {description}",
                    adjustment="Tracked new user intent and registered structured goal.",
                    tags=["goal", "planning", "user_input"]
                )
            except Exception as e:
                log_debug(f"[GoalTracker] Memory logging failed: {e}")

        self.save_goals_to_disk()
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
        self.save_goals_to_disk()
        return True

    def get_active_goals(self) -> List[Goal]:
        active = [g for g in self.goals.values() if g.status == "active"]
        log_debug(f"[GoalTracker] Retrieved {len(active)} active goals.")
        return active

    def reprioritize_goals(self):
        now = datetime.utcnow()
        for goal in self.goals.values():
            if goal.deadline and goal.status == "active":
                days_left = (goal.deadline - now).days
                if days_left <= 0:
                    goal.priority = min(1.0, goal.priority + 0.2)
                elif days_left <= 3:
                    goal.priority = min(1.0, goal.priority + 0.1)
        log_debug("[GoalTracker] Reprioritized goals based on deadlines.")
        self.save_goals_to_disk()

    def archive_goal(self, goal_id: str) -> bool:
        goal = self.goals.get(goal_id)
        if goal and goal.status == "active":
            goal.status = "completed"
            log_debug(f"[GoalTracker] Archived goal {goal_id[:8]} → completed.")
            self.save_goals_to_disk()
            return True
        return False

    def save_goals_to_disk(self):
        try:
            os.makedirs(os.path.dirname(GOAL_STORE_PATH), exist_ok=True)
            with open(GOAL_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump({gid: goal.dict() for gid, goal in self.goals.items()}, f, indent=2, default=str)
            log_debug("[GoalTracker] Saved goals to disk.")
        except Exception as e:
            log_debug(f"[GoalTracker] Failed to save goals: {e}")

    def load_goals_from_disk(self):
        try:
            if os.path.exists(GOAL_STORE_PATH):
                with open(GOAL_STORE_PATH, "r", encoding="utf-8") as f:
                    raw_goals = json.load(f)
                for gid, goal_data in raw_goals.items():
                    self.goals[gid] = Goal(**goal_data)
                log_debug(f"[GoalTracker] Loaded {len(self.goals)} goals from disk.")
        except Exception as e:
            log_debug(f"[GoalTracker] Failed to load goals: {e}")

def run(context: ContextBundle, prior_thoughts: List[AgentThought]) -> AgentThought:
    tracker = context.services.get("goal_tracker") if context.services else None
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

    if any(verb in user_input for verb in ["plan to", "want to", "goal is to", "need to", "i aim to"]):
        added_goal = tracker.add_goal(
            description=context.user_input,
            use_llm=context.config.get("use_llm_commentary", False)
        )
        reasons.append(f"Detected goal-like intent. Goal ID: {added_goal}")

    tracker.reprioritize_goals()
    active_goals = tracker.get_active_goals()
    goal_summaries = [f"📝 {g.description} (p={g.priority:.2f})" for g in active_goals]

    summary = (
        f"🌟 Added new goal and updated priorities.\n\nActive goals:\n" + "\n".join(goal_summaries)
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