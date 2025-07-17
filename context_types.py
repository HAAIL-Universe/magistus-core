from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime

from user_profile import UserProfile
from ethical.ethical_compass import EthicalCompass
from persona_core import PersonaCore


class ContextBundle(BaseModel):
    """
    This class represents a unified packet of contextual data shared with all agents.
    """
    user_input: str
    memory_matches: List[str]
    timestamp: str
    config: Dict[str, Any]

    ethical_compass: Optional[EthicalCompass] = EthicalCompass()
    user_profile: Optional[UserProfile] = None
    persona_core: Optional[PersonaCore] = None
    services: Optional[dict] = None
    system_goals: Optional[str] = ""

    # ✅ This line tells Pydantic to allow non-BaseModel types
    model_config = {
        "arbitrary_types_allowed": True
    }

    @classmethod
    def from_input(
        cls,
        user_input: str,
        memory_matches: List[str],
        config: Dict[str, Any],
        ethical_compass: Optional[EthicalCompass] = None,
        user_profile: Optional[UserProfile] = None,
        persona_core: Optional[PersonaCore] = None
    ):
        return cls(
            user_input=user_input,
            memory_matches=memory_matches,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            config=config,
            ethical_compass=ethical_compass or EthicalCompass(),
            user_profile=user_profile,
            persona_core=persona_core
        )


class AgentThought(BaseModel):
    """
    Represents an agent's structured output in response to a ContextBundle.
    """
    agent_name: str
    confidence: float  # 0.0 → 1.0
    content: str       # Natural language output
    reasons: List[str]  # Short rationale phrases or memory matches
    requires_memory: bool
    flags: Dict[str, bool]  # e.g., {"contradiction": False, "insight": True}

    @validator("confidence")
    def confidence_must_be_in_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

    def summary(self) -> str:
        """
        Returns a readable summary string for debugging or display.
        """
        return f"[{self.agent_name}] ({self.confidence:.2f}) → {self.content}"


class UserInput(BaseModel):
    """
    Represents raw user input before processing.
    Used by API endpoints like /think or /chat.
    """
    input: str
