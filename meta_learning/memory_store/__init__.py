import os
import json
from pathlib import Path
from meta_learning.memory_index_entry import MemoryIndexEntry

def get_latest_memory_entry() -> MemoryIndexEntry | None:
    # Ensure it always looks in meta_learning/memory_store
    folder = Path(__file__).resolve().parent / "memory_store"
    if not folder.exists():
        return None

    entries = sorted(
        [f for f in folder.iterdir() if f.suffix == ".json"],
        reverse=True
    )

    if not entries:
        return None

    latest_path = entries[0]

    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MemoryIndexEntry(**data)
    except Exception as e:
        print(f"Failed to load memory entry: {e}")
        return None
