# reinforcement_loop.py

import os
import re
from datetime import datetime
from typing import List, Dict

from context_types import ContextBundle, AgentThought
from central_hub import run_agents  # Corrected import
from config_loader import load_config
from fine_tune_loader import collect_fine_tune_sample

# Load config
config = load_config()
ENABLE_FINE_TUNE = config.get("fine_tune_collection_enabled", True)

# Paths
EVOLUTION_LOG = "logs/thought_evolution_log.md"
REINFORCE_LOG = "logs/reinforcement_log.md"
os.makedirs("logs", exist_ok=True)


def retrieve_failed_decisions(n: int = 5) -> List[Dict]:
    """
    Parse past evolution logs and find low-confidence or misaligned decisions.
    """
    if not os.path.exists(EVOLUTION_LOG):
        return []

    with open(EVOLUTION_LOG, "r", encoding="utf-8") as f:
        entries = f.read().split("### 🧠 Thought Evolution Entry")

    failed = []
    for entry in reversed(entries):
        if len(failed) >= n:
            break
        if "Agent Thoughts:" not in entry:
            continue

        # Find any agent thought with low confidence or warning flags
        low_conf = re.findall(r"`(.*?)` \((\d{1,3})%\):", entry)
        flags = re.findall(r"ethical_warning", entry)

        if any(float(conf)/100 < 0.7 for _, conf in low_conf) or flags:
            user_input_match = re.search(r"\*\*User Input:\*\*.*?> (.+)", entry)
            fused_output_match = re.search(r"\*\*Final Fused Response:\*\*.*?> (.+)", entry)

            if user_input_match and fused_output_match:
                failed.append({
                    "user_input": user_input_match.group(1).strip(),
                    "fused_output": fused_output_match.group(1).strip()
                })

    return failed


def rerun_agents_on_context(context_bundle: ContextBundle) -> List[AgentThought]:
    """
    Rerun core agents using preserved context.
    """
    return run_agents(context_bundle)


def compare_responses(old: AgentThought, new: AgentThought) -> Dict:
    """
    Return comparison metrics and whether new output is an improvement.
    """
    delta_conf = round(new.confidence - old.confidence, 3)
    improvement = (
        delta_conf > 0.1 and
        new.flags.get("ethical_warning", False) is False and
        new.flags.get("contradiction", False) is False
    )
    return {
        "confidence_change": delta_conf,
        "old_flags": old.flags,
        "new_flags": new.flags,
        "improved": improvement
    }


def log_reinforcement_result(original_input: str, old_output: str, new_output: str, comparison: Dict):
    """
    Append the reinforcement outcome to logs/reinforcement_log.md.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(REINFORCE_LOG, "a", encoding="utf-8") as f:
        f.write(f"### 🔁 Reinforcement Pass — {timestamp}\n\n")
        f.write(f"**Original Input:**\n> {original_input}\n\n")
        f.write(f"**Old Output:**\n> {old_output}\n\n")
        f.write(f"**New Output:**\n> {new_output}\n\n")
        f.write(f"**Comparison:**\n")
        for k, v in comparison.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n---\n\n")


def run_reinforcement_loop(n: int = 5):
    """
    Main entrypoint for simulated reinforcement reprocessing.
    """
    failed_decisions = retrieve_failed_decisions(n)
    for failure in failed_decisions:
        input_text = failure["user_input"]
        old_output = failure["fused_output"]

        context = ContextBundle.from_input(
            user_input=input_text,
            memory_matches=[],
            config=config
        )
        new_thoughts = rerun_agents_on_context(context)

        # Find best new thought (assuming central hub returns list)
        best_new = max(new_thoughts, key=lambda t: t.confidence)

        # Create synthetic old thought for comparison
        synthetic_old = AgentThought(
            agent_name="fused_output",
            confidence=0.65,  # assume suboptimal
            content=old_output,
            reasons=[],
            requires_memory=False,
            flags={"contradiction": True}
        )

        comparison = compare_responses(synthetic_old, best_new)
        log_reinforcement_result(input_text, old_output, best_new.content, comparison)

        if comparison["improved"] and ENABLE_FINE_TUNE:
            collect_fine_tune_sample(context, new_thoughts, best_new.content)
