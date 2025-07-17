import os
import json
import time
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from context_types import ContextBundle, AgentThought

try:
    from debug_logger import log_debug
except ImportError:
    def log_debug(msg): pass  # Silent fallback

try:
    from memory import search_memory
except ImportError:
    def search_memory(query): return []  # Stub fallback

try:
    from llm_wrapper import generate_response
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Constants
TASK_STORE_PATH = "data/scheduled_tasks.json"
MEMORY_LOG_PATH = "logs/memory_log.md"

# Ensure directories exist
os.makedirs(os.path.dirname(TASK_STORE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(MEMORY_LOG_PATH), exist_ok=True)

class ScheduledTask(BaseModel):
    task: str
    relevance: float = Field(..., ge=0.0, le=1.0)
    created_at: str
    last_updated: str

class TaskScheduler:
    """
    Manages memory-aware scheduling of cognitive tasks.
    Handles relevance tracking, decay, and resurfacing logic.
    """

    def __init__(self):
        self.tasks: List[ScheduledTask] = []
        self._load_tasks()

    def schedule_task(self, task: str, relevance_score: float):
        """
        Adds a task to the queue or boosts relevance if duplicate.
        """
        timestamp = datetime.utcnow().isoformat()
        for entry in self.tasks:
            if entry.task == task:
                entry.relevance = min(1.0, entry.relevance + relevance_score * 0.5)
                entry.last_updated = timestamp
                self._log_memory_event("🔁 Task Reinforced", task)
                log_debug(f"[TaskScheduler] Relevance boosted for task: {task}")
                self._save_tasks()
                return

        new_task = ScheduledTask(
            task=task,
            relevance=relevance_score,
            created_at=timestamp,
            last_updated=timestamp
        )
        self.tasks.append(new_task)
        self._log_memory_event("🆕 Task Scheduled", task)
        log_debug(f"[TaskScheduler] New task scheduled: {task}")
        self._save_tasks()

    def retrieve_due_tasks(self, threshold: float = 0.7) -> List[str]:
        due = [t.task for t in self.tasks if t.relevance >= threshold]
        if due:
            log_debug(f"[TaskScheduler] Retrieved due tasks above threshold {threshold}: {due}")
        return due

    def decay_relevance(self, decay_rate: float = 0.05):
        now = time.time()
        for task in self.tasks:
            last_update = datetime.fromisoformat(task.last_updated).timestamp()
            elapsed = now - last_update
            decay = decay_rate * (elapsed / 3600)  # decay per hour
            task.relevance = max(0.0, task.relevance - decay)
            task.last_updated = datetime.utcnow().isoformat()
        self._save_tasks()
        log_debug("[TaskScheduler] Relevance decay applied to all tasks.")

    def resurface_from_memory(self) -> List[str]:
        candidates = search_memory("unfinished task OR reminder OR to-do")
        matched = [c for c in candidates if "task" in c.lower()]
        log_debug(f"[TaskScheduler] Resurfaced {len(matched)} tasks from memory.")
        for m in matched:
            self.schedule_task(m, relevance_score=0.6)
        return matched

    def parse_natural_task(self, user_text: str) -> str:
        """
        Optional LLM-based method to extract task intent from natural language input.
        """
        if not LLM_AVAILABLE:
            log_debug("[TaskScheduler] LLM wrapper not available. Skipping parse.")
            return ""

        try:
            prompt = f"Extract the specific task or reminder from this input:\n\n{user_text}\n\nReturn only the task."
            result = generate_response(prompt)
            task = result.strip()
            log_debug(f"[TaskScheduler] Parsed natural task: {task}")
            return task
        except Exception as e:
            log_debug(f"[TaskScheduler] LLM task parse failed: {e}")
            return ""

    def _save_tasks(self):
        with open(TASK_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump([t.dict() for t in self.tasks], f, indent=2)

    def _load_tasks(self):
        if os.path.exists(TASK_STORE_PATH):
            with open(TASK_STORE_PATH, "r", encoding="utf-8") as f:
                task_dicts = json.load(f)
            self.tasks = [ScheduledTask(**t) for t in task_dicts]
            log_debug(f"[TaskScheduler] Loaded {len(self.tasks)} tasks from disk.")
        else:
            self.tasks = []

    def _log_memory_event(self, event_type: str, text: str):
        timestamp = datetime.utcnow().isoformat()
        entry = f"### {timestamp}\n{event_type}\n{text}\n\n"
        with open(MEMORY_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(entry)

    def __repr__(self):
        return f"<TaskScheduler: {len(self.tasks)} tasks tracked>"

# Agent entrypoint
def TaskSchedulerAgent(context: ContextBundle, _: List[AgentThought] = []) -> AgentThought:
    """
    Uses TaskScheduler to track cognitive reminders and surface important tasks.
    Returns top priorities as AgentThought content.
    """
    scheduler = TaskScheduler()
    summary_lines = []

    # Decay relevance first
    scheduler.decay_relevance()

    # Resurface tasks from memory
    memory_resurfaced = scheduler.resurface_from_memory()
    if memory_resurfaced:
        summary_lines.append(f"📂 Resurfaced {len(memory_resurfaced)} task(s) from memory.")

    # Extract task from user input
    user_input = getattr(context, "user_input", "") or getattr(context, "input_text", "")
    if user_input:
        task = scheduler.parse_natural_task(user_input)
        if task:
            scheduler.schedule_task(task, relevance_score=0.7)
            summary_lines.append(f"📝 New task parsed and added: '{task}'")

    # Retrieve currently due tasks
    due = scheduler.retrieve_due_tasks()
    if due:
        summary_lines.append("🔔 Tasks due now:")
        summary_lines.extend([f"• {t}" for t in due])
    else:
        summary_lines.append("✅ No tasks due at the moment.")

    return AgentThought(
        agent_name="task_scheduler",
        confidence=1.0,
        content="\n".join(summary_lines),
        reasons=["task management", "reminder prioritization"],
        requires_memory=True,
        flags={}
    )