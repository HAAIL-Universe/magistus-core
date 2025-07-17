# fine_tune_loader.py

import os
import json
from datetime import datetime
from typing import List
from context_types import ContextBundle, AgentThought
from config_loader import load_config

# Paths and config
FT_DIR = "data/fine_tune_samples"
FT_FILE = os.path.join(FT_DIR, "fine_tune_data.jsonl")
os.makedirs(FT_DIR, exist_ok=True)

config = load_config()
TUNING_ENABLED = config.get("fine_tune_collection_enabled", True)

def collect_fine_tune_sample(context: ContextBundle, agent_thoughts: List[AgentThought], fused_output: str) -> None:
    """
    Save a fine-tune sample if:
    - All agents are high confidence (>= 0.85)
    - No ethical warnings from reflective_self_monitor
    """
    if not TUNING_ENABLED:
        print("[Fine-Tune Collection Disabled]")
        return

    # Reject if any agent is low-confidence
    if any(thought.confidence < 0.85 for thought in agent_thoughts):
        print("[Fine-Tune Skipped] Confidence threshold not met.")
        return

    # Reject if reflective monitor flags ethical warning
    reflective = next((t for t in agent_thoughts if t.agent_name == "reflective_self_monitor"), None)
    if reflective and reflective.flags.get("ethical_warning", False):
        print("[Fine-Tune Skipped] Ethical warning detected.")
        return

    # Construct OpenAI-style format
    sample = {
        "messages": [
            {
                "role": "system",
                "content": "You are Magistus, a modular cognitive assistant powered by transparent neuro-symbolic reasoning."
            },
            {
                "role": "user",
                "content": context.user_input.strip()
            },
            {
                "role": "assistant",
                "content": fused_output.strip()
            }
        ],
        "metadata": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_confidences": {
                t.agent_name: round(t.confidence, 3) for t in agent_thoughts
            },
            "manifesto_aligned": True
        }
    }

    # Write to file
    with open(FT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")
