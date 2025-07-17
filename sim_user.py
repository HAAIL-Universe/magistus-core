# sim_user.py

from central_hub import run_agents
from voice_output import speak_text
from context_types import AgentThought


def display_thought(thought: AgentThought):
    """
    Nicely formats an agent's thought for display.
    """
    print(f"\n[{thought.agent_name.upper()}]")
    print(f"Confidence: {thought.confidence:.2f}")
    print(f"Content: {thought.content}")
    print(f"Reasons: {', '.join(thought.reasons)}")
    print(f"Flags: {thought.flags}")


def main():
    print("🧠 Magistus CLI (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        try:
            thoughts = run_agents(user_input)

            print("\n--- Agent Thoughts ---")
            for thought in thoughts:
                display_thought(thought)

            # Simple fused output (placeholder for now)
            best = max(thoughts, key=lambda t: t.confidence)
            print("\n🧠 Magistus:", best.content)
            speak_text(best.content)

        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
