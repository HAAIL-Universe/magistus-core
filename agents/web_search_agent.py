# agents/web_search_agent.py

import os
from typing import List
from dotenv import load_dotenv

from config_loader import load_config
from context_types import AgentThought, ContextBundle

# Attempt LangChain web search integration
try:
    from langchain.utilities import GoogleSearchAPIWrapper
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# LLM access
try:
    from llm_wrapper import generate_response
except ImportError:
    def generate_response(prompt: str) -> str:
        return ""  # fallback if no LLM

# Load secrets and config
load_dotenv()
config = load_config()
WEB_SEARCH_ENABLED = config.get("web_search_enabled", False)
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")


def run_web_search(query: str) -> AgentThought:
    """
    Executes a live web search using LangChain's GoogleSearchAPIWrapper.
    Optionally reflects on the results using the LLM wrapper.
    """

    if not WEB_SEARCH_ENABLED:
        return AgentThought(
            agent_name="web_search_agent",
            confidence=0.0,
            content="Web search is disabled by system configuration.",
            reasons=["web_search_enabled = false"],
            requires_memory=False,
            flags={
                "insight": False,
                "search_disabled": True
            }
        )

    if not LANGCHAIN_AVAILABLE or not SERPAPI_KEY:
        return AgentThought(
            agent_name="web_search_agent",
            confidence=0.0,
            content="Web search unavailable: missing LangChain or SERPAPI_API_KEY.",
            reasons=["Missing dependencies or API key"],
            requires_memory=False,
            flags={
                "insight": False,
                "search_failed": True
            }
        )

    try:
        search = GoogleSearchAPIWrapper()
        raw_output = search.run(query)
        snippets: List[str] = [s.strip() for s in raw_output.split("\n") if s.strip()]
        top_snippets = snippets[:5]
        summary = " ".join(top_snippets) or "No useful information returned from the web search."

        # Optional LLM reflection
        if config.get("use_llm_commentary", False):
            try:
                reflection = generate_response(
                    prompt=f"Reflect briefly on the usefulness of this search result for the query '{query}':\n\n{summary}"
                )
                if reflection:
                    summary += f"\n\n🧠 LLM Insight: {reflection.strip()}"
            except Exception as e:
                summary += f"\n\n(LLM commentary failed: {e})"

        return AgentThought(
            agent_name="web_search_agent",
            confidence=0.85,
            content=summary,
            reasons=["live web query"],
            requires_memory=False,
            flags={
                "insight": True
            }
        )

    except Exception as e:
        return AgentThought(
            agent_name="web_search_agent",
            confidence=0.0,
            content=f"Web search failed: {str(e)}",
            reasons=["Unhandled exception during search"],
            requires_memory=False,
            flags={
                "insight": False,
                "search_failed": True
            }
        )

def WebSearchAgent(context: ContextBundle, _: List[AgentThought] = []) -> AgentThought:
    """
    Adapter entrypoint for Magistus loop.
    Extracts the user query from context and runs the web search.
    """
    user_query = getattr(context, "user_input", "") or getattr(context, "input_text", "")
    if not user_query:
        return AgentThought(
            agent_name="web_search_agent",
            confidence=0.0,
            content="No user query provided for web search.",
            reasons=["No query found in context."],
            requires_memory=False,
            flags={"error": True}
        )

    return run_web_search(user_query)