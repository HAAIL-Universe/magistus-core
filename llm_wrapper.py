import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from typing import Generator, Union
from pydantic import SecretStr

# === Load environment variables ===
load_dotenv()
api_key_str = os.getenv("OPENAI_API_KEY")
if not api_key_str:
    raise ValueError("OPENAI_API_KEY not found in .env file")

OPENAI_API_KEY = SecretStr(api_key_str)  # ✅ still use SecretStr

# === Default config ===
DEFAULT_MODEL = "gpt-4-0125-preview"
DEFAULT_SYSTEM_PROMPT = "You are Magistus, an ethical synthetic cognition assistant."

# === Embedding model ===
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY  # ✅ this is allowed because constructor accepts SecretStr
)

def get_embedding(text: str) -> list[float]:
    """
    Returns a vector embedding for the given text using OpenAI.
    """
    try:
        return embedding_model.embed_query(text)
    except Exception:
        return []

def generate_response(
    prompt: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Generate a non-streaming response from the LLM.
    """
    try:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,  # ✅ passes SecretStr
            model=model,
            temperature=0.4,
            streaming=False
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        result: Union[BaseMessage, str] = llm.invoke(messages)
        return getattr(result, "content", str(result))
    except Exception:
        return "[Fallback] Reasoning unavailable."

def stream_response(
    prompt: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL
) -> Generator[str, None, None]:
    """
    Stream the response from the LLM chunk-by-chunk.
    """
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,  # ✅ again, SecretStr accepted
        model=model,
        temperature=0.4,
        streaming=True
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    for chunk in llm.stream(messages):
        content = getattr(chunk, "content", None)
        if content:
            yield content
