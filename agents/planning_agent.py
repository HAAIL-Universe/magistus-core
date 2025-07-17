from typing import List
from context_types import ContextBundle, AgentThought
from config_loader import load_config

try:
    from memory import MemoryRetriever
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# ✅ LLM wrapper added here
from llm_wrapper import generate_response

class PlanningAgent:
    """
    Translates high-level user goals into subtasks and sequences.
    Optionally uses memory for relevant prior examples.
    """

    def __init__(self):
        self.config = load_config()
        self.debug_mode = self.config.get("debug_mode", False)
        self.memory = MemoryRetriever(k=5) if MEMORY_AVAILABLE else None

    def generate_plan(self, goal: str) -> List[str]:
        """
        Decomposes a high-level goal into logical subtasks.

        :param goal: Abstract user intent or objective
        :return: List of subtasks or action items
        """
        plan: List[str] = []

        # Step 1 – Optionally recall memory
        memory_clues = []
        if self.memory:
            memory_clues = self.memory.search(goal)
            if self.debug_mode:
                print(f"[PlanningAgent] Memory matches: {len(memory_clues)}")

        # Step 2 – Build plan scaffolding
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

        # Step 3 – Reflect on relevant past memory
        if memory_clues:
            plan.append("📂 Reflect on similar past efforts:")
            for clue in memory_clues[:2]:
                plan.append(f"➤ Related memory: {clue.strip()[:100]}...")

        # Step 4 – Ask GPT to refine and improve
        try:
            gpt_prompt = (
                f"You are a strategic planning assistant. Given this user goal and planning scaffold, refine it:\n"
                f"User Goal: {goal}\n"
                f"Initial Steps:\n" + "\n".join(plan)
            )
            gpt_output = generate_response(gpt_prompt).strip()
            if gpt_output:
                plan.append(""")
🤖 GPT Refinement:
""".strip())
                plan.extend([f"➤ {line.strip()}" for line in gpt_output.split("\n") if line.strip()])
        except Exception as e:
            if self.debug_mode:
                print(f"[PlanningAgent] GPT refinement failed: {e}")

        plan.append("✅ Mark each task complete as progress is made.")
        return plan

def planning_agent(context: ContextBundle, _: List[AgentThought]) -> AgentThought:
    """
    Wrapper for PlanningAgent to interface with core loop.
    """
    agent = PlanningAgent()
    goal_tracker = getattr(context.services, "get", lambda key: None)("goal_tracker") if context.services else None
    active_goals = goal_tracker.get_active_goals() if goal_tracker else []
    goal_text = active_goals[0].description if active_goals else context.user_input

    plan_steps = agent.generate_plan(goal_text)

    return AgentThought(
        agent_name="planning_agent",
        confidence=0.92,
        content="\n".join(plan_steps),
        reasons=["Plan generated based on goal analysis and GPT refinement."],
        requires_memory=True,
        flags={}
    )
