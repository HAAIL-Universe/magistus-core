# profile/persona_core.py

from typing import List

class PersonaCore:
    """
    Represents the system's active personality style and tone constraints.
    Used to shape how Magistus speaks and evaluates its own expression.
    """
    def __init__(self, style_guidelines: List[str] = None):
        self.style_guidelines = style_guidelines or [
            "avoid emotional simulation",
            "be precise, not verbose",
            "maintain clarity over cleverness",
            "never impersonate the user",
            "avoid coercive language",
        ]
