# transparency_layer.py

from typing import List
from datetime import datetime
from context_types import AgentThought


def format_agent_thoughts(thoughts: List[AgentThought]) -> str:
    """
    Returns a markdown-formatted summary of all agent thoughts.
    """
    lines = []
    for thought in thoughts:
        agent = thought.agent_name
        confidence = int(thought.confidence * 100)
        summary = thought.content.strip()
        reasons = ", ".join(thought.reasons or [])
        flags = thought.flags or {}

        line = f"- `{agent}` ({confidence}%): \"{summary}\""
        if reasons:
            line += f"\n  - Reasons: {reasons}"
        if any(flags.values()):
            active_flags = ", ".join([k for k, v in flags.items() if v])
            line += f"\n  - Flags: {active_flags}"
        lines.append(line)

    return "\n".join(lines)


def generate_explanation(
    agent_thoughts: List[AgentThought],
    fused_output: str,
    verbosity: str = "normal"
) -> str:
    """
    Creates a user-facing transparency report based on system reasoning.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = [f"### 🧠 Transparency Report — {timestamp}\n"]

    report.append("**Final Response:**  \n> " + fused_output.strip())

    if verbosity == "brief":
        top_agents = sorted(agent_thoughts, key=lambda x: -x.confidence)[:2]
        brief_reasons = ", ".join(a.agent_name for a in top_agents)
        report.append(f"\n**Summary:** Decision influenced by {brief_reasons}.")
        return "\n".join(report)

    report.append("\n**Agent Insights:**")
    report.append(format_agent_thoughts(agent_thoughts))

    if verbosity in ["normal", "detailed"]:
        any_warnings = any(t.flags.get("ethical_warning", False) for t in agent_thoughts)
        contradictions = any(t.flags.get("contradiction", False) for t in agent_thoughts)
        avg_conf = sum(t.confidence for t in agent_thoughts) / len(agent_thoughts)

        report.append(f"\n**Ethical Check:** {'✅ Passed' if not any_warnings else '⚠️ Warning Raised'}")
        report.append(f"**Contradictions:** {'❌ None' if not contradictions else '⚠️ Contradiction Detected'}")
        report.append(f"**Confidence Score:** {round(avg_conf * 100, 1)} average")

    if verbosity == "detailed":
        report.append("\n---\n**Detailed Logs:**")
        for t in agent_thoughts:
            report.append(f"\n#### {t.agent_name} ({round(t.confidence * 100)}%)")
            report.append(f"- Content: {t.content.strip()}")
            if t.reasons:
                report.append(f"- Reasons: {', '.join(t.reasons)}")
            if t.flags:
                active_flags = ", ".join([f"{k}" for k, v in t.flags.items() if v])
                if active_flags:
                    report.append(f"- Flags: {active_flags}")

    return "\n".join(report)
