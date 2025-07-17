# thought_evolution.py

import os
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from context_types import ContextBundle, AgentThought
from config_loader import load_config

# Config
config = load_config()
EVOLUTION_LOGGING_ENABLED = config.get("thought_evolution_logging", True)

# Log paths
LOG_DIR = "logs"
LOG_PATH_MD = os.path.join(LOG_DIR, "thought_evolution_log.md")
LOG_PATH_JSONL = os.path.join(LOG_DIR, "thought_evolution.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)


def log_thought_evolution(
    user_input: str,
    agent_thoughts: List[AgentThought],
    fused_output: str,
    context: Optional[ContextBundle] = None
) -> None:
    """
    Logs a full reasoning cycle in both markdown and JSONL format.
    Includes user input, agent thoughts, and final output.
    """
    if not EVOLUTION_LOGGING_ENABLED:
        print("[Thought Evolution Logging Disabled]")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # === MARKDOWN LOG (for dev) ===
    lines = [f"### 🧠 Thought Evolution Entry — {timestamp}\n"]
    lines.append(f"**User Input:**  \n> {user_input.strip()}\n")
    lines.append("**Agent Thoughts:**")

    for thought in agent_thoughts:
        confidence_pct = int(thought.confidence * 100)
        reason_str = ", ".join(thought.reasons) if thought.reasons else "No reasons provided"
        flags_str = ", ".join(f"{k}={v}" for k, v in thought.flags.items()) if thought.flags else "No flags"
        lines.append(f"- `{thought.agent_name}` ({confidence_pct}%): \"{thought.content.strip()}\"")
        lines.append(f"  - Reasons: {reason_str}")
        lines.append(f"  - Flags: {flags_str}")

    lines.append("\n**Final Fused Response:**  \n> " + fused_output.strip())
    lines.append("\n---\n")

    with open(LOG_PATH_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # === JSONL STRUCTURED LOG ===
    json_entry = {
        "timestamp": timestamp,
        "user_input": user_input.strip(),
        "fused_output": fused_output.strip(),
        "agent_thoughts": [t.dict() for t in agent_thoughts]
    }

    if context:
        def safe_dict(x):
            return x.dict() if isinstance(x, BaseModel) else None

        json_entry["context"] = {
            "config": context.config,
            "memory_matches": context.memory_matches,
            "timestamp": context.timestamp,
            "user_profile": safe_dict(context.user_profile),
            "persona_core": safe_dict(context.persona_core),
            "ethical_compass": safe_dict(context.ethical_compass),
        }

    with open(LOG_PATH_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")


def summarize_evolution_history(n: int = 5) -> List[str]:
    """
    Returns a summary list of the last n markdown entries.
    """
    if not os.path.exists(LOG_PATH_MD):
        return []

    with open(LOG_PATH_MD, "r", encoding="utf-8") as f:
        content = f.read().strip()

    entries = content.split("### 🧠 Thought Evolution Entry — ")
    summaries = []

    for entry in reversed(entries[1:]):
        lines = entry.strip().splitlines()
        timestamp = lines[0].strip()
        user_input = ""
        fused_response = ""

        for i, line in enumerate(lines):
            if line.startswith("**User Input:**"):
                user_input = lines[i + 1].replace("> ", "").strip()
            if line.startswith("**Final Fused Response:**"):
                fused_response = lines[i + 1].replace("> ", "").strip()
                break

        summaries.append(f"- [{timestamp}] \"{user_input}\" → {fused_response}")
        if len(summaries) >= n:
            break

    return summaries
