# utils/memory_summary.py

def summarize_prior_memories(context, max_entries=3):
    if not hasattr(context, "prior_memories") or not context.prior_memories:
        return "None available."

    # Pull summaries, insights, or fallback to raw content
    memories = []
    for mem in context.prior_memories[:max_entries]:
        summary = mem.get("reflective_summary") or mem.get("insight") or mem.get("content") or ""
        if summary:
            memories.append(f"- {summary.strip()}")

    return "\n".join(memories) if memories else "None available."
