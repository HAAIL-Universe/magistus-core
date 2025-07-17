# device_sync.py

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from context_types import ContextBundle
from user_profile import UserProfile
from persona_core import PersonaCore

# Define the directory for sync snapshots
SYNC_DIR = "data/device_sync/"
os.makedirs(SYNC_DIR, exist_ok=True)


def export_context_bundle(context: ContextBundle) -> Dict[str, Any]:
    """
    Converts a ContextBundle into a JSON-serializable dictionary for cross-device sync.
    """
    return {
        "user_input": context.user_input,
        "memory_matches": context.memory_matches,
        "timestamp": context.timestamp,
        "config": context.config,
        "user_profile": context.user_profile.to_dict() if context.user_profile else {},
        "persona_core": {
            "tone_description": context.persona_core.tone_description,
            "self_narrative": context.persona_core.self_narrative,
            "style_guidelines": context.persona_core.style_guidelines
        } if context.persona_core else {},
        "ethical_compass": context.ethical_compass if context.ethical_compass else "",
        "manifesto_embeddings": context.manifesto_embeddings if context.manifesto_embeddings else [],
        "device_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sync_timestamp": datetime.now().isoformat()
    }


def import_context_bundle(data: Dict[str, Any]) -> ContextBundle:
    """
    Reconstructs a ContextBundle object from a dictionary.
    Handles missing or partial data gracefully.
    """
    user_profile = UserProfile.from_dict(data.get("user_profile", {}))
    persona_core = PersonaCore(
        tone_description=data.get("persona_core", {}).get("tone_description", ""),
        self_narrative=data.get("persona_core", {}).get("self_narrative", ""),
        style_guidelines=data.get("persona_core", {}).get("style_guidelines", [])
    )

    return ContextBundle(
        user_input=data.get("user_input", ""),
        memory_matches=data.get("memory_matches", []),
        timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        config=data.get("config", {}),
        user_profile=user_profile,
        persona_core=persona_core,
        ethical_compass=data.get("ethical_compass", ""),
        manifesto_embeddings=data.get("manifesto_embeddings", [])
    )


def save_context_snapshot(context: ContextBundle, filename: str) -> None:
    """
    Saves the exported context bundle to a JSON file in the sync directory.
    """
    bundle = export_context_bundle(context)
    path = os.path.join(SYNC_DIR, filename if filename.endswith(".json") else f"{filename}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)


def load_context_snapshot(filename: str) -> ContextBundle:
    """
    Loads a context snapshot from disk and returns a reconstructed ContextBundle.
    """
    path = os.path.join(SYNC_DIR, filename if filename.endswith(".json") else f"{filename}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_context_bundle(data)
