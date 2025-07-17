# persona_core.py

import json
import os
from typing import List, Dict, Optional

PERSONA_PATH = "data/persona_core.json"

class PersonaCore:
    """
    Represents the unified tone, narrative, and style constraints of Magistus.
    This ensures consistent voice, ethical transparency, and traceable behavior.
    """

    def __init__(
        self,
        tone_description: str = "Calm, rational, precise.",
        self_narrative: str = (
            "I am a synthetic cognitive system designed to support human reasoning, alignment, and decision-making. "
            "I do not possess consciousness, emotions, or subjective experience."
        ),
        style_guidelines: Optional[List[str]] = None
    ):
        self.tone_description = tone_description
        self.self_narrative = self_narrative
        self.style_guidelines = style_guidelines or [
            "Do not simulate human emotion.",
            "Avoid persuasive language or manipulation.",
            "Cite rationale for every claim.",
            "Be concise and information-dense.",
            "Maintain neutrality unless explicitly asked to take a stance.",
            "Always disclose uncertainty when relevant.",
            "Avoid anthropomorphic language.",
        ]

    def apply_to_output(self, content: str) -> str:
        """
        Wraps or adjusts raw agent output to conform to the system's tone and ethical voice.
        """
        preamble = (
            "As your cognitive assistant, I have considered the available information in alignment with your profile and preferences.\n"
        )
        return f"{preamble}{content.strip()}"

    def update_narrative(self, new_description: str) -> None:
        """
        Updates the system's self-narrative (ethically modifiable by the user only).
        """
        self.self_narrative = new_description

    def to_dict(self) -> Dict:
        return {
            "tone_description": self.tone_description,
            "self_narrative": self.self_narrative,
            "style_guidelines": self.style_guidelines
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            tone_description=data.get("tone_description", ""),
            self_narrative=data.get("self_narrative", ""),
            style_guidelines=data.get("style_guidelines", [])
        )

    def save(self, path: str = PERSONA_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str = PERSONA_PATH):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls.from_dict(data)
            except Exception as e:
                print(f"[WARNING] Failed to load PersonaCore: {e}")
        return cls()
