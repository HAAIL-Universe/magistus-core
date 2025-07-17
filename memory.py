import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config_loader import load_config
from utils.json_memory_logger import log_json_memory

# ----------------------------
# ⚙️ Configuration
# ----------------------------

INDEX_DIR = Path("data/faiss_index")
INDEX_NAME = "index"
LOG_PATH = Path("logs/memory_log.md")
STRUCTURED_MEMORY_DIR = Path("meta_learning/memory_store")

# Ensure necessary directories exist
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(LOG_PATH.parent, exist_ok=True)
os.makedirs(STRUCTURED_MEMORY_DIR, exist_ok=True)

# Load config and API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found. Make sure it's set in your .env file.")

config = load_config()
DEBUG_MODE = config.get("debug_mode", False)

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ----------------------------
# 🔍 Embedding + Index Setup
# ----------------------------

embedding_model = OpenAIEmbeddings()

try:
    if (INDEX_DIR / f"{INDEX_NAME}.faiss").exists():
        vectorstore = FAISS.load_local(
            str(INDEX_DIR),
            embeddings=embedding_model,
            index_name=INDEX_NAME,
            allow_dangerous_deserialization=True
        )
        logging.info(f"Memory index loaded from '{INDEX_DIR}/{INDEX_NAME}'")
    else:
        vectorstore = FAISS.from_texts(["The Magistus memory index has been initialized."], embedding_model)
        vectorstore.save_local(str(INDEX_DIR), index_name=INDEX_NAME)
        logging.info(f"New memory index initialized at '{INDEX_DIR}/{INDEX_NAME}'")
except Exception as e:
    vectorstore = None
    logging.error(f"Failed to initialize or load FAISS index: {e}")

# ----------------------------
# 🧠 Core Memory Class
# ----------------------------

class MemoryRetriever:
    def __init__(self, k: int = 4, score_threshold: Optional[float] = None):
        self.k = k
        self.score_threshold = score_threshold
        self.index_path = INDEX_DIR
        self.embeddings = embedding_model
        self.vectorstore = vectorstore

    def search(self, query: str) -> List[str]:
        if not self.vectorstore:
            logging.warning("Memory index not available. Returning empty result.")
            return []

        try:
            docs_and_scores: List[tuple[Document, float]] = self.vectorstore.similarity_search_with_score(query, k=self.k)
        except Exception as e:
            logging.error(f"Memory search failed: {e}")
            return []

        filtered = []
        for doc, score in docs_and_scores:
            if self.score_threshold is None or score >= self.score_threshold:
                filtered.append(doc.page_content)
                if DEBUG_MODE:
                    logging.debug(f"[MATCH @ {score:.4f}] {doc.page_content[:100]}...")

        return filtered

    def __str__(self):
        return f"<MemoryRetriever: k={self.k}, threshold={self.score_threshold}>"

    def __repr__(self):
        return self.__str__()

# ----------------------------
# 🧩 Public Utility Functions
# ----------------------------

def add_memory(text: str):
    if not vectorstore:
        logging.error("Cannot add memory — vectorstore not initialized.")
        return

    try:
        vectorstore.add_texts([text])
        vectorstore.save_local(str(INDEX_DIR), index_name=INDEX_NAME)
        log_memory(markdown_text=text, raw_text=text)
        logging.info("New memory added and indexed.")
    except Exception as e:
        logging.error(f"Failed to add memory: {e}")

def search_memory(query: str) -> List[str]:
    if not vectorstore:
        logging.warning("Vectorstore not available for search.")
        return []

    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        docs = retriever.get_relevant_documents(query)
        return [doc.page_content for doc in docs]
    except Exception as e:
        logging.error(f"Quick memory search failed: {e}")
        return []

def log_memory(markdown_text: str, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"### {timestamp}\n{markdown_text}\n\n"

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
        if DEBUG_MODE:
            logging.debug(f"📝 Logged memory entry at {timestamp}")
    except Exception as e:
        logging.error(f"❌ Failed to log memory: {e}")

    try:
        entry_type = kwargs.get("type", "narrative")
        tags = kwargs.get("tags", ["memory", "log"])
        if isinstance(tags, str):
            tags = [tags]

        log_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "content": markdown_text,
            "tags": tags,
            "context": kwargs.get("context", ""),
            "insight": kwargs.get("insight", ""),
            "behavioral_adjustment": kwargs.get("behavioral_adjustment", ""),
            "reflective_summary": kwargs.get("reflective_summary", ""),
            "relevance_score": kwargs.get("relevance_score", 0.5)
        }

        filename = f"{log_data['timestamp'].replace(':', '-')}_{log_data['id']}.json"
        memory_path = STRUCTURED_MEMORY_DIR / filename
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

        if DEBUG_MODE:
            logging.debug(f"🧠 Structured memory written to: {memory_path}")
    except Exception as e:
        logging.error(f"❌ Failed to write structured memory file: {e}")

    try:
        log_json_memory(**kwargs)
    except Exception as e:
        logging.error(f"❌ Failed to log JSON memory: {e}")

def load_memory_history(limit: int = 20, source: str = "both") -> dict:
    history = {
        "narrative": [],
        "structured": []
    }

    if source in ("markdown", "both"):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                entries = []
                entry = []
                for line in reversed(lines):
                    if line.startswith("### "):
                        if entry:
                            entries.append("".join(reversed(entry)))
                            entry = []
                    entry.append(line)
                if entry:
                    entries.append("".join(reversed(entry)))
                history["narrative"] = entries[:limit]
        except FileNotFoundError:
            logging.warning("Markdown memory log not found.")
        except Exception as e:
            logging.error(f"Failed to load markdown memory: {e}")

    if source in ("json", "both"):
        try:
            files = sorted(
                STRUCTURED_MEMORY_DIR.glob("*.json"),
                key=lambda f: f.name,
                reverse=True
            )
            structured_entries = []
            for fpath in files[:limit]:
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        structured_entries.append(json.load(f))
                except Exception as e:
                    logging.warning(f"Could not load {fpath.name}: {e}")
            history["structured"] = structured_entries
        except FileNotFoundError:
            logging.warning("Structured memory folder not found.")
        except Exception as e:
            logging.error(f"Failed to load structured memory: {e}")

    if source == "markdown":
        return {"narrative": history["narrative"]}
    elif source == "json":
        return {"structured": history["structured"]}
    return history
