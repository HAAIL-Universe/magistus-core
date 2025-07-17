# cognitive_extensions/post_agent_thought_hooks.py

from context_types import AgentThought, ContextBundle
from typing import List, Dict
from datetime import datetime

from cognitive_extensions.confidence_modulation import adjust_confidence
from cognitive_extensions.emotion_memory import log_emotion
from cognitive_extensions.self_assessment import (
    EvaluateAgentPerformance,
    GenerateSelfReport,
    LogAssessment,
    load_feedback_insights
)

from memory import log_json_memory  # ✅ Correct import

def post_process_agent_thoughts(context: ContextBundle, thoughts: List[AgentThought]) -> List[AgentThought]:
    """
    Applies centralized post-processing to AgentThoughts after core reasoning.
    Integrates emotion logging, confidence modulation, and self-assessment scheduling.
    """
    updated_thoughts = []

    for thought in thoughts:
        # 🧠 Confidence adjustment
        confidence_result = adjust_confidence(
            user_input=context.user_input,
            agent_reasoning=" ".join(thought.reasons) if isinstance(thought.reasons, list) else thought.reasons,
            base_confidence=thought.confidence
        )
        confidence_value = confidence_result.get("adjusted", 0.5)
        print(f"[🧠 CONFIDENCE] Adjusted confidence for {thought.agent_name}: {thought.confidence:.2f} → {confidence_value:.2f}")
        thought.confidence = round(max(min(confidence_value, 0.99), 0.01), 2)

        # ❤️ Emotion logging
        # ❤️ Emotion logging
        if thought.flags.get("emotional_relevance") or "emotionally charged" in " ".join(thought.reasons).lower():
            emotion = str(thought.flags.get("emotion_type") or "neutral")
            emotion_intensity = thought.flags.get("emotion_intensity", 0.5)
            print(f"[❤️ EMOTION] Logging emotion for {thought.agent_name}: {emotion} @ intensity {emotion_intensity}")
            log_emotion(
                emotion_type=emotion,
                intensity=emotion_intensity,
                context_id=getattr(context, "session_id", None),
                source="agent_thought"
            )
            thought.flags["emotion_logged"] = True

        # ⚖️ Ethical warnings
        if thought.flags.get("ethics_warning") or thought.flags.get("contradiction"):
            print(f"[⚖️ ETHICS] Ethics flag triggered for {thought.agent_name}")
            thought.flags["requires_review"] = True

        # 🧾 Log structured JSON memory
        try:
            log_json_memory(
                user_input=context.user_input,
                timestamp=datetime.utcnow().isoformat(),
                agent=thought.agent_name,
                round1=None,
                round2=None,
                final_response=None,
                debug_metadata=None,
                goals=[],
                flags=thought.flags,
                summary=thought.content[:200],
                adjustment=f"confidence: {thought.confidence:.2f}",
                tags=list(thought.flags.keys()),
                summary_tags=[],
                persona_updates={}
            )
        except Exception as e:
            print(f"[❌ MEMORY ERROR] Failed to log JSON memory: {e}")

        updated_thoughts.append(thought)

    # 🪞 Trigger reflection if needed
    if should_run_self_assessment(context, updated_thoughts):
        print("[🪞 SELF-ASSESSMENT] Trigger conditions met — running self-assessment")
        run_self_assessment(updated_thoughts)

    return updated_thoughts


def should_run_self_assessment(context: ContextBundle, thoughts: List[AgentThought]) -> bool:
    turns = getattr(context, "session_stats", {}).get("interaction_count", 0)
    if turns > 0 and turns % 100 == 0:
        return True
    return any(t.flags.get("requires_review") or t.flags.get("emotion_intensity", 0.0) >= 0.85 for t in thoughts)


def run_self_assessment(thoughts: List[AgentThought]) -> None:
    raw_thoughts = [t.__dict__ for t in thoughts]
    evaluator = EvaluateAgentPerformance(agent_thoughts=raw_thoughts)
    decision_score = evaluator.evaluate_decisions()
    ethics_score = evaluator.evaluate_ethical_alignment()
    reasoning_score = evaluator.evaluate_reasoning_quality()

    print(f"[📊 SELF-REVIEW] Scores — Decision: {decision_score:.2f}, Ethics: {ethics_score:.2f}, Reasoning: {reasoning_score:.2f}")

    feedback = load_feedback_insights()
    reporter = GenerateSelfReport(
        decision_score=decision_score,
        ethics_score=ethics_score,
        reasoning_score=reasoning_score,
        feedback_insights=feedback
    )
    report = reporter.generate_insights()
    summary = reporter.generate_summary()
    print(f"[📝 SELF-REPORT] Summary: {summary}")
    LogAssessment.log_to_file(report)
    LogAssessment.update_magistus_profile(summary)
