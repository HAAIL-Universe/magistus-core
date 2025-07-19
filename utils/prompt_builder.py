def build_dynamic_prompt(agent_name: str, memory_snippets: list, user_goals: list, recent_tags: list) -> str:
    base_intro = f"You are the {agent_name.replace('_', ' ')} agent within the Magistus cognition system.\n"
    guidance = ""

    if agent_name == "prefrontal_cortex":
        guidance += "- Your role is to assess reasoning structure and planning logic.\n"
        guidance += "- Highlight intent, contradictions, and value-alignment.\n"

    if "confusion" in recent_tags:
        guidance += "- The user appears uncertain. Be extra clear in your logic explanation.\n"

    if "ethics" in recent_tags:
        guidance += "- Ethical reasoning may be required. Review boundaries.\n"

    if user_goals:
        goals_list = "\n".join(f"- {g}" for g in user_goals)
        guidance += f"- Current user goals:\n{goals_list}\n"

    memory_blob = "\n".join(f"- {m}" for m in memory_snippets[:3]) or "- None"

    prompt = (
        f"{base_intro}"
        f"{guidance}\n"
        f"Relevant recent memory:\n{memory_blob}\n\n"
        "Now, respond with insight based on the above."
    )

    return prompt.strip()
