# core/ethical_compass.py

from pydantic import BaseModel
from typing import List

class EthicalCompass(BaseModel):
    """
    Represents the active ethical boundaries and manifesto clauses guiding agent behavior.
    """
    manifesto_clauses: List[str] = [
        "Respect user agency",
        "Avoid manipulation or emotional simulation",
        "Preserve transparency at all times",
        "Seek clarification before prescriptive action",
        "Flag irreversible actions for explicit consent"
    ]

    def __len__(self):
        return len(self.manifesto_clauses)

    def __getitem__(self, index):
        return self.manifesto_clauses[index]

    def __iter__(self):
        return iter(self.manifesto_clauses)
