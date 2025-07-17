# stability_tests.py

import os
import datetime
from typing import List, Dict
from central_hub import run_magistus
from agents.synthetic_limiter import evaluate_input
from agents.reflective_self_monitor import check_alignment
from policy_engine import is_critical_action
from config_loader import load_config
from context_types import AgentThought

# Config
config = load_config()
FAILURE_LOG_PATH = "logs/stability_failures.md"
os.makedirs("logs", exist_ok=True)

def run_test_case(prompt: str) -> dict:
    """
    Simulates a full Magistus pipeline call.
    Returns structured result including agent flags and outcome status.
    """
    context_bundle, agent_thoughts, fused_output = run_magistus(prompt)

    limiter_thought = evaluate_input(prompt, context_bundle)
    reflective_thought = check_alignment(agent_thoughts, fused_output)

    # Determine pass/fail based on flags
    flags = []
    if limiter_thought.flags.get("execution_blocked"):
        flags.append("execution_blocked")
    if limiter_thought.flags.get("ethical_warning"):
        flags.append("ethical_warning")
    if reflective_thought.flags.get("contradiction_detected"):
        flags.append("contradiction_detected")
    if reflective_thought.flags.get("ethical_violation"):
        flags.append("ethical_violation")

    status = "passed"
    if "execution_blocked" in flags:
        status = "failed"
    elif flags:
        status = "warning"

    return {
        "prompt": prompt,
        "status": status,
        "flags": flags,
        "agents": [t.agent_name for t in agent_thoughts],
        "fused_output": fused_output,
        "limiter": limiter_thought.content,
        "reflective": reflective_thought.content,
        "agent_thoughts": [t.dict() for t in agent_thoughts]
    }

def run_batch_tests(prompt_list: List[str], verbose: bool = False) -> List[dict]:
    """
    Runs a batch of test prompts through the full system.
    Logs failures and warnings.
    """
    results = []
    failures = []

    for prompt in prompt_list:
        result = run_test_case(prompt)
        results.append(result)

        if result["status"] != "passed":
            failures.append(result)
            _log_failure(result)

        if verbose:
            print(f"[{result['status'].upper()}] {prompt}")

    return results

def generate_test_summary(results: List[dict]) -> str:
    """
    Analyzes test results and creates a Markdown summary.
    """
    total = len(results)
    passed = len([r for r in results if r["status"] == "passed"])
    warnings = len([r for r in results if r["status"] == "warning"])
    failed = len([r for r in results if r["status"] == "failed"])

    failure_agents = {}
    for r in results:
        if r["status"] != "passed":
            for a in r["agents"]:
                failure_agents[a] = failure_agents.get(a, 0) + 1

    summary_lines = [
        f"## 🧪 Magistus Stability Test Summary",
        f"**Total Tests:** {total}",
        f"**Passed:** {passed} ({round(100 * passed/total, 1)}%)",
        f"**Warnings:** {warnings}",
        f"**Failed:** {failed}",
        "",
        "### ⚠️ Most Frequently Involved Agents in Failures:",
    ]

    sorted_agents = sorted(failure_agents.items(), key=lambda x: x[1], reverse=True)
    for agent, count in sorted_agents[:5]:
        summary_lines.append(f"- `{agent}`: {count} failures")

    return "\n".join(summary_lines)

def _log_failure(result: dict):
    """
    Appends a failure/warning entry to logs/stability_failures.md
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(FAILURE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n### ❌ Test {result['status'].capitalize()} — {timestamp}\n\n")
        f.write(f"**Prompt:** \"{result['prompt']}\"\n\n")

        if result['status'] == 'failed':
            if "execution_blocked" in result['flags']:
                f.write("**Limiter Agent:** Blocked execution\n\n")
            if "ethical_violation" in result['flags']:
                f.write("**Reflective Monitor:** Flagged ethical violation\n\n")
        elif result['status'] == 'warning':
            if "contradiction_detected" in result['flags']:
                f.write("**Reflective Monitor:** Detected internal contradiction\n\n")
            if "ethical_warning" in result['flags']:
                f.write("**Limiter Agent:** Raised ethical warning\n\n")

        f.write(f"**Fused Response:**\n> {result['fused_output']}\n\n")
        f.write(f"---\n")
