"""
self_assessment.py

Performs scheduled and on-demand introspection on Magistus AGI behavior,
evaluating reasoning quality, ethical alignment, and decision effectiveness.

Logs structured summaries into self_assessment_log.jsonl and optionally updates
magistus_profile.json with compact reflections.
"""

import json
import os
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Optional, Any

SELF_ASSESSMENT_LOG = "meta_learning/memory_store/self_assessment_log.jsonl"
PROFILE_PATH = "magistus_profile.json"
USER_FEEDBACK_PATH = "meta_learning/memory_store/user_feedback.jsonl"

class EvaluateAgentPerformance:
    """
    Analyzes recent AgentThoughts for decision quality, ethical alignment, and reasoning clarity.
    """

    def __init__(self, agent_thoughts: List[Dict[str, Any]]):
        self.thoughts = agent_thoughts

    def evaluate_decisions(self) -> float:
        """Score the system’s decisions based on flags and consistency."""
        if not self.thoughts:
            return 0.0
        total = len(self.thoughts)
        clean = sum(1 for t in self.thoughts if not t.get("flags"))
        return round(clean / total, 3)

    def evaluate_ethical_alignment(self) -> float:
        """Score ethical alignment based on violations in flags."""
        if not self.thoughts:
            return 0.0
        ethical_flags = ["ethical_warning", "boundary_crossed"]
        concerns = sum(
            1 for t in self.thoughts if any(t.get("flags", {}).get(flag) for flag in ethical_flags)
        )
        return round(1.0 - (concerns / len(self.thoughts)), 3)

    def evaluate_reasoning_quality(self) -> float:
        """Analyze reasoning richness via reasoning text length and clarity."""
        if not self.thoughts:
            return 0.0
        avg_len = sum(len(t.get("reasons", [])) for t in self.thoughts) / len(self.thoughts)
        return round(min(avg_len / 5.0, 1.0), 3)  # cap at 1.0

class GenerateSelfReport:
    """
    Compiles introspection scores into a readable and storable self-assessment.
    """

    def __init__(
        self,
        decision_score: float,
        ethics_score: float,
        reasoning_score: float,
        feedback_insights: Optional[Dict[str, Any]] = None
    ):
        self.decision_score = decision_score
        self.ethics_score = ethics_score
        self.reasoning_score = reasoning_score
        self.feedback_insights = feedback_insights or {}

    def generate_summary(self) -> str:
        """Creates a short reflection summary suitable for profile update."""
        return (
            f"Performance review shows {round(self.decision_score*100)}% decision integrity, "
            f"{round(self.ethics_score*100)}% ethical alignment, and "
            f"{round(self.reasoning_score*100)}% reasoning depth. "
            f"Feedback trends: {self.feedback_insights.get('categories', {})}"
        )

    def generate_insights(self) -> Dict[str, Any]:
        """Creates a dictionary of internal notes."""
        return {
            "performance_score": round((self.decision_score + self.ethics_score + self.reasoning_score) / 3.0, 3),
            "key_metrics": {
                "decision_accuracy": self.decision_score,
                "ethical_alignment": self.ethics_score,
                "reasoning_depth": self.reasoning_score,
                "feedback": self.feedback_insights
            },
            "improvement_plan": self._build_plan()
        }

    def _build_plan(self) -> List[str]:
        plan = []
        if self.ethics_score < 0.9:
            plan.append("Review ethical clause tagging thresholds.")
        if self.reasoning_score < 0.75:
            plan.append("Enhance reasoning trace complexity.")
        if self.decision_score < 0.85:
            plan.append("Refine agent flag correlation tracking.")
        return plan or ["Maintain current calibration."]

class LogAssessment:
    """
    Handles saving self-assessment reports to disk.
    """

    @staticmethod
    def log_to_file(report: Dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "assessment_id": str(uuid4()),
            **report
        }
        try:
            os.makedirs(os.path.dirname(SELF_ASSESSMENT_LOG), exist_ok=True)
            with open(SELF_ASSESSMENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[LogAssessment] Logging failed: {e}")

    @staticmethod
    def update_magistus_profile(reflection: str) -> None:
        try:
            if not os.path.exists(PROFILE_PATH):
                with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                    json.dump({"reflections": [reflection]}, f, indent=2)
                return
            with open(PROFILE_PATH, "r+", encoding="utf-8") as f:
                data = json.load(f)
                reflections = data.get("reflections", [])
                reflections.append(reflection)
                f.seek(0)
                json.dump({"reflections": reflections}, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"[LogAssessment] Profile update failed: {e}")

def load_feedback_insights(limit: int = 50) -> Optional[Dict[str, Any]]:
    """Load and parse the most recent feedback data."""
    if not os.path.exists(USER_FEEDBACK_PATH):
        return None
    try:
        with open(USER_FEEDBACK_PATH, "r", encoding="utf-8") as f:
            lines = [json.loads(line.strip()) for line in f if line.strip()][-limit:]
        if not lines:
            return None
        avg_conf = sum(entry.get("confidence", 0.0) for entry in lines) / len(lines)
        cats = {}
        for entry in lines:
            cat = entry.get("feedback_category", "unspecified")
            cats[cat] = cats.get(cat, 0) + 1
        return {"average_confidence": round(avg_conf, 3), "categories": cats}
    except Exception as e:
        print(f"[load_feedback_insights] Failed: {e}")
        return None
