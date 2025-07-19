from uuid import uuid4
from typing import Optional
from typing import List, Union
from context_types import ContextBundle, AgentThought
from config_loader import load_config
from memory import log_memory

try:
    from memory import MemoryRetriever, log_memory_recall
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    log_memory_recall = None  # graceful fallback

from llm_wrapper import generate_response, get_embedding

class PlanningAgent:
    """
    Translates high-level user goals into subtasks and sequences.
    Optionally uses memory for relevant prior examples.
    """

    def __init__(self):
        self.config = load_config()
        self.debug_mode = self.config.get("debug_mode", False)
        self.memory = MemoryRetriever(k=5) if MEMORY_AVAILABLE else None

    def _format_recall_payload(self, clues):
        """
        Normalize memory hits (strings OR dicts) into the format expected by log_memory_recall().
        """
        payload = []
        for c in clues:
            if isinstance(c, dict):
                payload.append({
                    "uuid": c.get("uuid", str(uuid4())),
                    "score": c.get("score", 0.0),
                    "summary": c.get("summary") or c.get("insight") or str(c)[:160]
                })
            else:
                payload.append({
                    "uuid": str(uuid4()),
                    "score": 0.0,
                    "summary": str(c)[:160]
                })
        return payload

    def generate_plan(self, goal: str) -> List[str]:
        plan: List[str] = []

        # Step 1 – Optionally recall memory
        memory_clues = []
        if self.memory:
            memory_clues = self.memory.search(goal)
            if self.debug_mode:
                print(f"[PlanningAgent] Memory matches: {len(memory_clues)}")

            # Log recall event (if logger available)
            if memory_clues and log_memory_recall:
                try:
                    recall_payload = self._format_recall_payload(memory_clues)
                    log_memory_recall(goal, recall_payload, triggering_agent="planning_agent")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[PlanningAgent] Failed to log memory recall: {e}")

        # Step 2 – Plan scaffold
        plan.append(f"🔍 Clarify goal: '{goal}' with user context.")
        plan.append("🧠 Identify any constraints, deadlines, or dependencies.")
        lower_goal = goal.lower()

        if "research" in lower_goal:
            plan.append("📚 Allocate time to collect relevant resources.")
            plan.append("📝 Summarize findings into bullet points.")
        elif "build" in lower_goal or "develop" in lower_goal:
            plan.append("📐 Break the system into modular components.")
            plan.append("🛠️ Design and test each component sequentially.")
        elif "learn" in lower_goal:
            plan.append("📘 Define specific learning objectives.")
            plan.append("📅 Schedule sessions or milestones.")
        else:
            plan.append("⚙️ Identify logical action steps using goal decomposition.")
            plan.append("📈 Prioritize tasks by impact and feasibility.")

        # Step 3 – Add relevant memories
        if memory_clues:
            plan.append("📂 Reflect on similar past efforts:")
            for clue in memory_clues[:2]:
                if isinstance(clue, dict):
                    snippet = clue.get("summary") or clue.get("insight") or "[no summary]"
                else:
                    snippet = str(clue)
                plan.append(f"➤ Related memory: {snippet[:100]}...")

        # Step 4 – Ask GPT to refine plan
        try:
            gpt_prompt = (
                f"You are a strategic planning assistant. Given this user goal and planning scaffold, refine it:\n"
                f"User Goal: {goal}\n"
                f"Initial Steps:\n" + "\n".join(plan)
            )
            gpt_output = generate_response(gpt_prompt).strip()
            if gpt_output:
                plan.append("🤖 GPT Refinement:")
                plan.extend([f"➤ {line.strip()}" for line in gpt_output.split("\n") if line.strip()])
        except Exception as e:
            if self.debug_mode:
                print(f"[PlanningAgent] GPT refinement failed: {e}")

        plan.append("✅ Mark each task complete as progress is made.")
        return plan

    def run(self, context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> AgentThought:
        """
        Entry point for agent orchestration.
        """
        goal_tracker = context.services.get("goal_tracker") if context.services else None
        active_goals = goal_tracker.get_active_goals() if goal_tracker else []

        # Enhanced goal selection logic
        selected_goal = None
        goal_id = None

        if active_goals:
            selected_goal = active_goals[0]
        elif goal_tracker:
            try:
                query_vector = get_embedding(context.user_input)
                results = goal_tracker.search_goals(query_vector)
                if results:
                    selected_goal = results[0]
            except Exception as e:
                if self.debug_mode:
                    print(f"[PlanningAgent] Goal embedding search failed: {e}")

        if not selected_goal:
            selected_goal = context.user_input
        else:
            goal_id = selected_goal.goal_id
            selected_goal = selected_goal.description

        steps = self.generate_plan(selected_goal)

        if MEMORY_AVAILABLE:
            try:
                markdown_text = f"""🧩 **Planning Sequence Generated**
- **Goal**: {selected_goal}
- **Used Goal ID**: `{goal_id}`""" if goal_id else f"""🧩 **Planning Sequence Generated**
- **Goal**: {selected_goal}
- *(No goal ID used — direct input)*"""

                markdown_text += "\n\n### 🗂️ Plan Steps:\n" + "\n".join([f"- {s}" for s in steps if not s.startswith("🤖")])
                if any("🤖" in step for step in steps):
                    markdown_text += "\n\n### 🤖 GPT Refinement:\n" + "\n".join([f"- {s[2:].strip()}" for s in steps if s.startswith("➤")])

                log_memory(
                    markdown_text=markdown_text,
                    timestamp=context.timestamp or context.utc_timestamp,
                    agent="planning_agent",
                    summary=f"Generated execution plan for goal: {selected_goal[:60]}",
                    adjustment="Planning scaffold created using heuristics and GPT refinement.",
                    tags=["plan", "goal", "strategy"]
                )
            except Exception as e:
                if self.debug_mode:
                    print(f"[PlanningAgent] Memory logging failed: {e}")


        return AgentThought(
            agent_name="planning_agent",
            confidence=0.92,
            content="\n".join(steps),
            reasons=["Generated based on structured goal decomposition and GPT refinement."],
            requires_memory=True,
            flags={"goal_id": goal_id} if goal_id else {}
        )
