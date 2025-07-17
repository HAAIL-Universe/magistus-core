# value_drift_monitor.py

import os
import json
import datetime
from typing import Dict, List

from context_types import ContextBundle
from user_profile import UserProfile
from ethical_compass import load_manifesto_text
from llm_wrapper import embed_texts  # Assumes we use the same embedding logic
from utils.file_utils import ensure_dir_exists  # Optional utility for directory checks
from debug_logger import log_debug  # Optional logger if present

# --- Paths ---
BASELINE_DIR = "data/value_drift_baseline"
LOG_PATH = "logs/value_drift_log.md"
MANIFESTO_BASELINE_PATH = os.path.join(BASELINE_DIR, "manifesto_embeddings.json")
USER_PROFILE_BASELINE_PATH = os.path.join(BASELINE_DIR, "user_profile_embeddings.json")


def store_reference_embeddings(current_manifesto_text: str, current_user_profile: UserProfile) -> None:
    """
    Saves the current Manifesto and UserProfile embeddings as a baseline snapshot.
    """
    ensure_dir_exists(BASELINE_DIR)

    # Embed Manifesto as a single chunk
    manifesto_embedding = embed_texts([current_manifesto_text])[0]
    with open(MANIFESTO_BASELINE_PATH, "w") as f:
        json.dump({"embedding": manifesto_embedding}, f)

    # Embed serialized UserProfile
    profile_json = json.dumps(current_user_profile.to_dict(), indent=2)
    profile_embedding = embed_texts([profile_json])[0]
    with open(USER_PROFILE_BASELINE_PATH, "w") as f:
        json.dump({"embedding": profile_embedding}, f)

    log_debug("Value drift: Stored baseline embeddings for manifesto and user profile.")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Computes cosine similarity between two embedding vectors.
    """
    from numpy import dot
    from numpy.linalg import norm
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))


def detect_value_drift(current_context: ContextBundle) -> Dict:
    """
    Compares the current Manifesto and UserProfile embeddings against the stored baseline.
    Returns drift status, similarity scores, and analysis notes.
    """
    notes = []
    drift_detected = False
    threshold = 0.85

    # Load stored baselines
    with open(MANIFESTO_BASELINE_PATH, "r") as f:
        baseline_manifesto = json.load(f)["embedding"]
    with open(USER_PROFILE_BASELINE_PATH, "r") as f:
        baseline_profile = json.load(f)["embedding"]

    # Re-embed current context
    current_manifesto = "\n".join(current_context.ethical_compass or [])
    current_manifesto_embedding = embed_texts([current_manifesto])[0]

    current_profile_json = json.dumps(current_context.user_profile.to_dict(), indent=2)
    current_profile_embedding = embed_texts([current_profile_json])[0]

    # Compare
    sim_manifesto = cosine_similarity(baseline_manifesto, current_manifesto_embedding)
    sim_profile = cosine_similarity(baseline_profile, current_profile_embedding)

    if sim_manifesto < threshold:
        drift_detected = True
        notes.append("Magistus Manifesto similarity below threshold — possible philosophical drift.")

    if sim_profile < threshold:
        drift_detected = True
        notes.append("User Profile similarity below threshold — possible evolution in values or preferences.")

    # Build report
    result = {
        "drift_detected": drift_detected,
        "similarity_score_manifesto": round(sim_manifesto, 4),
        "similarity_score_user_profile": round(sim_profile, 4),
        "notes": notes
    }

    log_drift_event(result)
    return result


def log_drift_event(result: Dict) -> None:
    """
    Appends drift detection results to the value_drift_log.md file with timestamp.
    """
    ensure_dir_exists("logs")
    timestamp = datetime.datetime.utcnow().isoformat()
    entry = f"\n### Drift Check: {timestamp}\n"
    entry += f"- Drift Detected: **{result['drift_detected']}**\n"
    entry += f"- Manifesto Similarity: `{result['similarity_score_manifesto']}`\n"
    entry += f"- Profile Similarity: `{result['similarity_score_user_profile']}`\n"
    for note in result["notes"]:
        entry += f"- Note: {note}\n"

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(entry)

    log_debug(f"Value drift audit recorded at {timestamp}")
