import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import re
import uuid

# Path where user profile is stored (can be relocated via config)
USER_PROFILE_PATH = "data/user_profile.json"
INSTANCE_ID_PATH = "data/instance_id.txt"

class UserProfile:
    """
    Represents the user's long-term preferences, boundaries, and evolving intent.
    Used across Magistus agents for ethical alignment and personalization.
    """
    def __init__(
        self,
        intent_summary: str = "No intent specified.",
        preferences: Optional[Dict[str, Any]] = None,
        boundaries: Optional[List[str]] = None,
        last_updated: Optional[datetime] = None
    ):
        self.intent_summary = intent_summary
        self.preferences = preferences if preferences is not None else {}
        self.boundaries = boundaries if boundaries is not None else []
        self.last_updated = last_updated or datetime.utcnow()

    def update_from_input(self, user_input: str) -> None:
        """
        Parses natural language user input and attempts to extract updates
        to intent, preferences, or boundaries.
        """
        lowered = user_input.lower()

        # Detect new boundaries
        if any(phrase in lowered for phrase in ["i don't want", "please avoid", "never mention"]):
            matches = re.findall(r"(?:i don't want to talk about|please avoid|never mention)\s+(.*?)(?:\.|,|$)", lowered)
            for match in matches:
                cleaned = match.strip()
                if cleaned and cleaned not in self.boundaries:
                    self.boundaries.append(cleaned)

        # Detect preferences (simple pattern-based tagging)
        if "i prefer" in lowered or "i like" in lowered:
            matches = re.findall(r"(?:i prefer|i like)\s+(.*?)(?:\.|,|$)", lowered)
            for match in matches:
                cleaned = match.strip()
                if cleaned:
                    self.preferences.setdefault("likes", []).append(cleaned)

        # Detect intent (basic fallback)
        if "my goal is" in lowered or "i want to" in lowered:
            match = re.search(r"(?:my goal is|i want to)\s+(.*?)(?:\.|,|$)", lowered)
            if match:
                self.intent_summary = match.group(1).strip()

        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_summary": self.intent_summary,
            "preferences": self.preferences,
            "boundaries": self.boundaries,
            "last_updated": self.last_updated.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        raw_timestamp = data.get("last_updated")
        try:
            parsed_timestamp = datetime.fromisoformat(raw_timestamp) if isinstance(raw_timestamp, str) else datetime.utcnow()
        except Exception:
            parsed_timestamp = datetime.utcnow()

        return cls(
            intent_summary=data.get("intent_summary", ""),
            preferences=data.get("preferences", {}),
            boundaries=data.get("boundaries", []),
            last_updated=parsed_timestamp
        )


    def detect_intent_shift(self, new_input: str) -> Optional[str]:
        """
        Detects whether a new input significantly differs from the prior intent.
        If so, returns a suggested updated intent.
        """
        lowered = new_input.lower()
        if "i want to" in lowered or "my goal is" in lowered:
            match = re.search(r"(?:i want to|my goal is)\s+(.*?)(?:\.|,|$)", lowered)
            if match:
                new_intent = match.group(1).strip()
                if new_intent and new_intent != self.intent_summary:
                    return new_intent
        return None


def load_user_profile() -> UserProfile:
    """
    Loads the user profile from disk, or returns a default profile if missing.
    """
    if os.path.exists(USER_PROFILE_PATH):
        try:
            with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return UserProfile.from_dict(data)
        except Exception as e:
            print(f"[WARNING] Failed to load user profile: {e}")
    return UserProfile()


def save_user_profile(profile: UserProfile) -> None:
    """
    Saves the current user profile to disk as JSON.
    """
    os.makedirs(os.path.dirname(USER_PROFILE_PATH), exist_ok=True)
    try:
        with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save user profile: {e}")


def get_instance_id() -> str:
    """
    Returns a persistent instance ID for the Magistus system.
    If none exists, it creates and saves one to disk.
    """
    os.makedirs(os.path.dirname(INSTANCE_ID_PATH), exist_ok=True)
    if os.path.exists(INSTANCE_ID_PATH):
        try:
            with open(INSTANCE_ID_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"[WARNING] Failed to read instance ID: {e}")

    new_id = f"magistus_{uuid.uuid4().hex[:8]}"
    try:
        with open(INSTANCE_ID_PATH, "w", encoding="utf-8") as f:
            f.write(new_id)
    except Exception as e:
        print(f"[ERROR] Failed to save instance ID: {e}")
    return new_id
