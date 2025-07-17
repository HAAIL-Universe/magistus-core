# agents/agent_base.py

from typing import List, Dict, Any
from pydantic import BaseModel

class AgentThought(BaseModel):
    agent_name: str
    content: str
    reasoning: str
    confidence: float = 1.0
    flags: Dict[str, Any] = {}
    reasons: List[str] = []

class AgentInterface:
    name: str
    role: str

    def run(self, context, prior_thoughts: List[AgentThought]) -> AgentThought:
        raise NotImplementedError("Each agent must implement the run() method.")
