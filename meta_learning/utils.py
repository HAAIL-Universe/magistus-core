# utils.py

import os
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from meta_learning.memory_index_entry import MemoryIndexEntry

# ----------------------------
# 📁 Constants and Paths
# ----------------------------

MEMORY_DIR = Path(__file__).resolve().parent / "memory_store"
PROFILE_PATH = Path("magistus_profile.json")
MEMORY_JSONL_PATH = Path("memorystore.jsonl")


# ----------------------------
# 🧠 Core Utilities
# ----------------------------

def ensure_memory_dir_exists():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def append_memory_entry_to_store(entry: MemoryIndexEntry):
    """
    Appends a MemoryIndexEntry as a single line in the long-term memory JSONL store.
    Trinity-compliant for Phase 12 long-term memory.
    """
    try:
        with open(MEMORY_JSONL_PATH, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write memory entry to store: {e}")


def append_to_magistus_profile(reflection: dict):
    """
    Append a compact reflective insight to Magistus's evolving persona model.
    Each entry tagged with timestamp and stored under 'reflections' key.
    """
    if not PROFILE_PATH.exists():
        PROFILE_PATH.write_text(json.dumps({"reflections": []}, indent=2), encoding="utf-8")

    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"reflections": []}

    if "reflections" not in data:
        data["reflections"] = []

    reflection["timestamp"] = datetime.utcnow().isoformat()
    data["reflections"].append(reflection)

    with PROFILE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
