# reasoning_logger.py

import os
import json
from datetime import datetime
from typing import List, Optional, Dict

# Attempt to import debug logger
try:
    from debug_logger import log_error
except ImportError:
    def log_error(msg): pass  # fallback noop

# Paths
LOG_DIR = "logs"
MARKDOWN_PATH = os.path.join(LOG_DIR, "reasoning_chains.md")
JSON_PATH = os.path.join(LOG_DIR, "chain_trace.json")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)


def log_reasoning_chain(
    agent_name: str,
    decision_type: str,
    triggering_input: str,
    reasoning_steps: List[str],
    retrieved_memory: Optional[List[str]],
    outcome: str
):
    """
    Append a transparent reasoning log to both markdown and structured JSON.
    """

    timestamp = datetime.utcnow().isoformat()

    # MARKDOWN FORMAT
    try:
        with open(MARKDOWN_PATH, "a", encoding="utf-8") as md_file:
            md_file.write(f"\n---\n\n")
            md_file.write(f"### 🧠 Reasoning Chain — {timestamp} UTC\n")
            md_file.write(f"- **Agent**: `{agent_name}`\n")
            md_file.write(f"- **Decision Type**: `{decision_type}`\n")
            md_file.write(f"- **Triggering Input**: `{triggering_input}`\n\n")

            if retrieved_memory:
                md_file.write("#### 📚 Retrieved Memory:\n")
                for mem in retrieved_memory:
                    md_file.write(f"- {mem}\n")
                md_file.write("\n")

            md_file.write("#### 🔍 Reasoning Steps:\n")
            for i, step in enumerate(reasoning_steps, 1):
                md_file.write(f"{i}. {step}\n")

            md_file.write("\n#### ✅ Final Outcome:\n")
            md_file.write(f"{outcome}\n")
    except Exception as e:
        log_error(f"Failed to write reasoning chain markdown: {e}")


    # JSON FORMAT
    try:
        log_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "decision_type": decision_type,
            "input": triggering_input,
            "memory": retrieved_memory or [],
            "steps": reasoning_steps,
            "outcome": outcome,
        }

        # Append entry to JSON list
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, "r+", encoding="utf-8") as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = []
                data.append(log_entry)
                json_file.seek(0)
                json.dump(data, json_file, indent=2)
        else:
            with open(JSON_PATH, "w", encoding="utf-8") as json_file:
                json.dump([log_entry], json_file, indent=2)

    except Exception as e:
        log_error(f"Failed to write reasoning chain JSON: {e}")
