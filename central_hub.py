import importlib
from typing import List, Tuple, Optional, Dict, Any

from config_loader import load_config
from context_types import ContextBundle, AgentThought
from memory import MemoryRetriever, log_memory
from utils.json_memory_logger import log_json_memory
from llm_wrapper import generate_response
from agents.goal_management.goal_tracker import GoalTracker
from ethical.ethical_compass import EthicalCompass
from user_profile import UserProfile
from persona_core import PersonaCore
from meta_learning.meta_learning_supervisor import MetaLearningSupervisor
from meta_learning.utils import append_memory_entry_to_store
from uuid import uuid4
from meta_learning.memory_index_entry import MemoryIndexEntry
from agents.statistical_reasoning_agent import StatisticalReasoningAgent
from agents.predictive_memory_manager import PredictiveMemoryManager
from agents.memory_retriever_agent import MemoryRetrieverAgent
from utils.prompt_builder import build_dynamic_prompt

def run_agents(context: ContextBundle, prior_thoughts: Optional[List[AgentThought]] = None) -> List[AgentThought]:
    config = context.config
    enabled_agents = config.get("agents_enabled", [])
    debug_mode = config.get("debug_mode", False)

    thoughts: List[AgentThought] = []

    for agent_name in enabled_agents:
        try:
            agent_module = importlib.import_module(f"agents.{agent_name}")
            thought: AgentThought = agent_module.run(context, prior_thoughts)
            thoughts.append(thought)

            if debug_mode:
                print(f"[DEBUG] {agent_name} round {'2' if prior_thoughts else '1'} → {thought.confidence:.2f}")
        except Exception as e:
            print(f"[ERROR] Agent '{agent_name}' failed: {e}")

    return thoughts

def detect_contradictions(thoughts: List[AgentThought]) -> List[str]:
    contradictions = []
    for i, a in enumerate(thoughts):
        for b in thoughts[i + 1:]:
            if a.content.strip() != b.content.strip() and abs(a.confidence - b.confidence) < 0.2:
                contradictions.append(f"⚠️ {a.agent_name} vs {b.agent_name} — conflicting views")
    return contradictions

def fuse_agent_thoughts(round1: List[AgentThought], round2: List[AgentThought]) -> Tuple[str, str, List[AgentThought]]:
    best = max(round2, key=lambda t: t.confidence)

    changed = [
        agent.agent_name for agent in round2
        if agent.content != next((a.content for a in round1 if a.agent_name == agent.agent_name), "")
    ]

    contradictions = detect_contradictions(round2)

    debug_notes = ""
    if changed:
        debug_notes += f"\n🌀 Revised by: {', '.join(changed)}"
    if contradictions:
        debug_notes += "\n" + "\n".join(contradictions)

    return best.content.strip(), debug_notes.strip(), round2

def run_magistus(
    user_input: str,
    allow_self_eval: bool = False
) -> Tuple[ContextBundle, List[AgentThought], str, str, Optional[MemoryIndexEntry]]:

    config = load_config()
    compass = EthicalCompass()
    profile = UserProfile()
    persona = PersonaCore()

    greetings = ["hi", "hello", "hey", "hiya", "greetings", "good morning", "good evening"]
    if user_input.strip().lower() in greetings:
        context = ContextBundle.from_input(user_input=user_input, memory_matches=[], config=config)
        response = generate_response(f'The user said: "{user_input}". Respond casually and kindly.')
        return context, [], response.strip(), "🔁 Direct LLM response — agents skipped", None

    retriever = MemoryRetriever(k=5)
    memory_matches = retriever.search(user_input)

    from memory import log_memory_recall
    if memory_matches:
        formatted_matches = []
        for match in memory_matches:
            formatted_matches.append({
                "uuid": match.get("id", str(uuid4())),
                "score": match.get("relevance_score", 0.5),
                "summary": match.get("summary")
                    or match.get("insight")
                    or match.get("content", "[no summary]")
            })
        log_memory_recall(user_input, formatted_matches, triggering_agent="central_hub")

    goal_tracker = GoalTracker()
    summaries_only = [m.get("summary", "[no summary]") for m in memory_matches]

    context = ContextBundle.from_input(
        user_input=user_input,
        memory_matches=summaries_only,
        config=config,
        ethical_compass=compass,
        user_profile=profile,
        persona_core=persona
    )
    context.services = {
        "goal_tracker": goal_tracker
    }

    # Inject dynamic_prompt_state
    if "prefrontal_cortex" in config.get("agents_enabled", []):
        dynamic_prompt = build_dynamic_prompt(
            agent_name="prefrontal_cortex",
            memory_snippets=summaries_only,
            user_goals=[g.description for g in goal_tracker.get_active_goals()] if hasattr(goal_tracker, "get_active_goals") else [],
            recent_tags=config.get("recent_tags", [])
        )
        context.dynamic_prompt_state["prefrontal_cortex"] = dynamic_prompt

    stat_agent = StatisticalReasoningAgent(historical_data=[1, 2, 3, 4, 5])
    memory_manager = PredictiveMemoryManager()

    memory_retriever = MemoryRetrieverAgent()
    memory_thought = memory_retriever.run(context)
    print(f"[MemoryRetriever] → {memory_thought.content}")

    round1_thoughts = run_agents(context)
    round2_thoughts = run_agents(context, prior_thoughts=round1_thoughts)

    fused_summary, debug_metadata, final_thoughts = fuse_agent_thoughts(round1_thoughts, round2_thoughts)

    summarised_thoughts = "\n".join(f"[{t.agent_name}] {t.content}" for t in round2_thoughts)
    llm_final_prompt = (
        f'The user said: "{user_input}"\n\n'
        f'Here is a summary of internal system reasoning:\n{summarised_thoughts}\n\n'
        "Based on the above, respond helpfully and conversationally as Magistus would — "
        "not by repeating the analysis, but by responding naturally and insightfully to the user."
    )
    final_response = generate_response(llm_final_prompt).strip()

    log_memory(
        f"# 🧠 Magistus Reasoning Cycle\n"
        f"**User Input:** {user_input}\n\n"
        f"## Round 1:\n" +
        "\n".join(f"[{t.agent_name}] ({t.confidence:.2f}) {t.content}" for t in round1_thoughts) +
        "\n\n## Round 2:\n" +
        "\n".join(f"[{t.agent_name}] ({t.confidence:.2f}) {t.content}" for t in round2_thoughts) +
        f"\n\n## 🧠 Final Response:\n{final_response}\n"
        f"\n\n## 🧩 Debug Notes:\n{debug_metadata}\n"
    )

    memory_entry = None
    try:
        meta_agent = MetaLearningSupervisor()
        memory_entry = meta_agent.create_memory_entry(
            user_input=user_input,
            final_response=fused_summary,
            agent_thoughts=round2_thoughts,
            debug_notes=debug_metadata
        )
        append_memory_entry_to_store(memory_entry)
    except Exception as e:
        print(f"[MetaLearning] Failed to save structured memory entry: {e}")

    log_memory(
        markdown_text=(
            f"# 🧠 Magistus Reasoning Cycle\n"
            f"**User Input:** {user_input}\n\n"
            f"## Round 1:\n" +
            "\n".join(f"[{t.agent_name}] ({t.confidence:.2f}) {t.content}" for t in round1_thoughts) +
            "\n\n## Round 2:\n" +
            "\n".join(f"[{t.agent_name}] ({t.confidence:.2f}) {t.content}" for t in round2_thoughts) +
            f"\n\n## 🧠 Final Response:\n{final_response}\n"
            f"\n\n## 🧩 Debug Notes:\n{debug_metadata}\n"
        ),
        user_input=user_input,
        round1=round1_thoughts,
        round2=round2_thoughts,
        final_response=final_response,
        debug_metadata=debug_metadata,
        goals=[],
        flags={},
        summary_tags=[],
        persona_updates={}
    )

    return context, round2_thoughts, final_response, debug_metadata, memory_entry

if __name__ == "__main__":
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        context, thoughts, final_response, debug_metadata, meta_entry = run_magistus(user_input)
        print(f"\n🧠 Magistus: {final_response}\n")
        print(f"\n🧩 Debug:\n{debug_metadata}\n")
