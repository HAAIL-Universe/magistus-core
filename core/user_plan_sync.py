# user_plan_sync.py

import uuid
from datetime import datetime
from typing import List, Dict, Optional

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg): pass  # silent fallback

MEMORY_LOG_PATH = "logs/memory_log.md"


class UserPlanSync:
    """
    Human-facing interface for managing long-term plans and syncing them with the internal task architecture.
    """

    def __init__(self):
        # In-memory plan store; can be persisted later
        self.plans: Dict[str, Dict] = {}

    def create_plan(self, title: str, goals: List[str], metadata: Optional[Dict] = None) -> str:
        """
        Creates a new long-term plan.
        """
        plan_id = str(uuid.uuid4())
        self.plans[plan_id] = {
            "plan_id": plan_id,
            "title": title,
            "goals": goals,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "history": []
        }
        self._log_memory_event("🧠 Plan Created", f"Plan: {title}\nGoals: {goals}")
        log_debug(f"[UserPlanSync] New plan created with ID {plan_id}: {title}")
        return plan_id

    def update_plan(self, plan_id: str, new_goals: List[str], reason: str) -> bool:
        """
        Updates the goals of an existing plan.
        """
        if plan_id not in self.plans:
            log_debug(f"[UserPlanSync] Attempted update on unknown plan_id: {plan_id}")
            return False

        plan = self.plans[plan_id]
        old_goals = plan["goals"]
        plan["goals"] = new_goals
        plan["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "update",
            "old_goals": old_goals,
            "new_goals": new_goals,
            "reason": reason
        })

        self._log_memory_event("✏️ Plan Updated", f"Title: {plan['title']}\nReason: {reason}\nNew Goals: {new_goals}")
        log_debug(f"[UserPlanSync] Updated plan {plan_id}. Reason: {reason}")
        return True

    def fork_plan(self, plan_id: str, edits: List[str]) -> Optional[str]:
        """
        Forks an existing plan with optional edits to goals.
        """
        if plan_id not in self.plans:
            log_debug(f"[UserPlanSync] Attempted fork on unknown plan_id: {plan_id}")
            return None

        original = self.plans[plan_id]
        new_goals = original["goals"] + edits
        forked_id = self.create_plan(
            title=f"{original['title']} [Forked]",
            goals=new_goals,
            metadata={"forked_from": plan_id}
        )
        self._log_memory_event("🌱 Plan Forked", f"Forked from {plan_id} with edits: {edits}")
        log_debug(f"[UserPlanSync] Forked plan {plan_id} into new ID {forked_id}")
        return forked_id

    def get_plan_summary(self, plan_id: str) -> Optional[str]:
        """
        Returns a readable summary of the plan's title, goals, and status.
        """
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]
        summary = f"🗂️ Plan: {plan['title']}\nGoals:\n" + "\n".join(f"- {g}" for g in plan["goals"])
        return summary

    def sync_with_scheduler(self, scheduler) -> None:
        """
        Pushes all active goals to the task scheduler for monitoring and prioritization.
        """
        for plan_id, plan in self.plans.items():
            for goal in plan["goals"]:
                scheduler.schedule_task(goal, relevance_score=0.8)
                log_debug(f"[UserPlanSync] Synced goal from plan {plan_id} to scheduler: {goal}")

        self._log_memory_event("🔁 Goals Synced", "All active goals pushed to TaskScheduler.")

    def _log_memory_event(self, event_type: str, text: str):
        timestamp = datetime.utcnow().isoformat()
        entry = f"### {timestamp}\n{event_type}\n{text}\n\n"
        try:
            with open(MEMORY_LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(entry)
        except Exception as e:
            log_debug(f"[UserPlanSync] Failed to write memory log: {e}")
