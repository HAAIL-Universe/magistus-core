import os
import json
import uuid
import logging
import hashlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config_loader import load_config
from utils.json_memory_logger import log_json_memory
from meta_learning.memory_index_entry import load_memory_index

# ----------------------------
# ⚙️ Configuration
# ----------------------------

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR.parent / "data"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"

# Memory directories
STRUCTURED_MEMORY_DIR = BASE_DIR / "meta_learning" / "memory_store"
SHORT_TERM_MEMORY_DIR = BASE_DIR / "meta_learning" / "short_term_memory"
REFLECTIVE_SUMMARY_DIR = BASE_DIR / "meta_learning" / "reflective_summaries"

# Markdown and JSONL logs
LOG_PATH = LOGS_DIR / "memory_log.md"
MEMORY_RECALL_LOG_PATH = LOGS_DIR / "memory_recall_log.md"
MEMORY_RECALL_JSONL = LOGS_DIR / "memory_recall_log.jsonl"

# Vector index config
INDEX_DIR = FAISS_INDEX_DIR
INDEX_NAME = "index"

# ───── 🛠️ Directory + File Setup ─────

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STRUCTURED_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SHORT_TERM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
REFLECTIVE_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

if not MEMORY_RECALL_LOG_PATH.exists():
    MEMORY_RECALL_LOG_PATH.touch()

# ───── 🔐 Environment & Config ─────

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in .env file")

config = load_config()
DEBUG_MODE = config.get("debug_mode", False)

# ───── 📢 Logging Setup ─────

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ----------------------------
# 🔍 Embedding Index Setup
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
    logging.error(f"Failed to load FAISS index: {e}")

# ----------------------------
# 🧠 Memory Retriever
# ----------------------------

class MemoryRetriever:
    def __init__(self, k: int = 4, score_threshold: Optional[float] = None):
        self.k = k
        self.score_threshold = score_threshold
        self.embeddings = embedding_model
        self.vectorstore = vectorstore

    def search(self, query: str) -> List[dict]:
        if not self.vectorstore:
            logging.warning("Vectorstore not available.")
            return []

        try:
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=self.k)
        except Exception as e:
            logging.error(f"Vector search failed: {e}")
            return []

        formatted_results = []
        for doc, score in docs_and_scores:
            formatted_results.append({
                "uuid": str(uuid.uuid4()),
                "summary": doc.page_content,
                "score": score
            })

        return formatted_results

# ----------------------------
# 📓 Memory Recall Logging
# ----------------------------

def log_memory_recall(user_input: str, retrieved_memories: list, triggering_agent: str = "UnknownAgent"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # --- Write to Markdown Log ---
    with open(MEMORY_RECALL_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"## 🧠 Memory Recall — {timestamp}\n")
        f.write(f"- **Agent**: `{triggering_agent}`\n")
        f.write(f"- **User Input**: `{user_input}`\n\n")

        if not retrieved_memories:
            f.write("❌ **No relevant memories retrieved.**\n\n")
        else:
            f.write(f"**🔎 Top {len(retrieved_memories)} Retrieved Memories:**\n\n")
            for i, memory in enumerate(retrieved_memories, 1):
                summary = (
                    memory.get("summary")
                    or memory.get("insight")
                    or memory.get("final_response")
                    or "[no summary]"
                )
                score = memory.get("score")
                uuid = memory.get("uuid", "?")
                score_display = round(score, 3) if isinstance(score, (float, int)) else "?"
                f.write(f"{i}. **UUID**: `{uuid}` — **Score**: `{score_display}`\n")
                f.write(f"    ↳ _{summary}_\n\n")
        f.write("---\n\n")

    # --- Also Write to JSONL Recall Log ---
    recall_record = {
        "timestamp": timestamp,
        "agent": triggering_agent,
        "user_input": user_input,
        "matches": [
            {
                "uuid": memory.get("uuid", "?"),
                "score": memory.get("score", "?"),
                "summary": memory.get("summary")
                    or memory.get("insight")
                    or memory.get("final_response")
                    or "[no summary]"
            }
            for memory in retrieved_memories
        ]
    }

    try:
        with open(MEMORY_RECALL_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(recall_record) + "\n")
    except Exception as e:
        logging.error(f"❌ Failed to write structured memory recall log: {e}")

# ----------------------------
# 🔎 Memory Search (String Match)
# ----------------------------

def search_memory(query: str) -> dict:
    try:
        summary_files = sorted(SHORT_TERM_MEMORY_DIR.glob("*.json"), reverse=True)
    except Exception as e:
        logging.error(f"Failed to scan short-term memory: {e}")
        return {"error": "Short-term memory unavailable."}

    for file in summary_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                entry = json.load(f)
        except Exception as e:
            logging.warning(f"Skipped unreadable short-term memory file: {file.name}")
            continue

        combined_text = " ".join([
            entry.get("summary", ""),
            entry.get("context", ""),
            entry.get("adjustment", "")
        ]).lower()

        if query.lower() in combined_text:
            match_id = entry.get("id")
            timestamp = entry.get("timestamp", "").replace(":", "-")
            possible_matches = list(STRUCTURED_MEMORY_DIR.glob(f"{timestamp}_{match_id}.json"))

            if possible_matches:
                try:
                    with open(possible_matches[0], "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logging.error(f"Failed to load full memory: {e}")
                    return {"error": "Found summary but full memory failed to load."}
            else:
                return {"error": f"Summary matched but no full memory file found for {match_id}"}

    return {"message": "No matching memory found."}

# ----------------------------
# 📝 Log Memory Entry
# ----------------------------

def log_memory(markdown_text: str, **kwargs):
    try:
        # ✅ Ensure all required folders exist
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURED_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        SHORT_TERM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        REFLECTIVE_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

        # 🔁 Unified UUID + timestamp
        short_id = kwargs.get("id", str(uuid.uuid4()))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        iso_timestamp = datetime.now().isoformat()
        confidence = kwargs.get("confidence", "N/A")
        emotion = kwargs.get("emotion", "N/A")
        tags = kwargs.get("tags", ["memory"])
        if isinstance(tags, str):
            tags = [tags]

        insight = (kwargs.get("insight") or "").strip()
        summary = (kwargs.get("reflective_summary") or "").strip()

        # ✅ Markdown log
        log_entry = (
            f"### 🧠 Memory Entry\n"
            f"🕒 {timestamp} | 🆔 {short_id}\n"
            f"🧭 Confidence: {confidence} | 😐 Emotion: {emotion}\n"
            f"🏷️ Tags: {', '.join(tags)}\n\n"
            f"💡 Insight:\n{insight or '[No insight provided]'}\n\n"
            f"📌 Summary:\n{summary or '[No summary provided]'}\n\n---\n\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # ✅ JSON content for full + short memory
        content_hash = hashlib.md5(markdown_text.encode("utf-8")).hexdigest()
        full_memory_data = {
            "id": short_id,
            "timestamp": iso_timestamp,
            "type": kwargs.get("type", "narrative"),
            "content": markdown_text,
            "tags": tags,
            "context": kwargs.get("context", ""),
            "insight": insight,
            "behavioral_adjustment": kwargs.get("behavioral_adjustment", ""),
            "reflective_summary": summary,
            "relevance_score": kwargs.get("relevance_score", 0.5),
            "confidence": confidence,
            "emotion": emotion,
            "warnings": kwargs.get("warnings", []),
            "meta_reflection": kwargs.get("meta_reflection", {}),
            "content_hash": content_hash
        }

        # ✅ Skip duplicates
        for existing_file in STRUCTURED_MEMORY_DIR.glob("*.json"):
            try:
                with open(existing_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if existing.get("content_hash") == content_hash:
                        if DEBUG_MODE:
                            logging.debug(f"🔁 Duplicate memory skipped (hash: {content_hash})")
                        return
            except Exception:
                continue

        # ✅ Save long-term full entry
        full_filename = f"{iso_timestamp.replace(':', '-')}_{short_id}.json"
        with open(STRUCTURED_MEMORY_DIR / full_filename, "w", encoding="utf-8") as f:
            json.dump(full_memory_data, f, indent=2)

        if DEBUG_MODE:
            logging.debug(f"✅ Full memory written to: {STRUCTURED_MEMORY_DIR / full_filename}")

        # ✅ Save short-term summary
        short_memory_data = {
            "id": short_id,
            "timestamp": iso_timestamp,
            "agent": kwargs.get("agent", "unknown"),
            "context": kwargs.get("context", "[no context]"),
            "summary": summary,
            "adjustment": kwargs.get("behavioral_adjustment", ""),
            "tags": tags,
            "goals": kwargs.get("goals", []),
            "flags": kwargs.get("flags", {}),
            "persona_updates": kwargs.get("persona_updates", {})
        }
        short_filename = f"{iso_timestamp.replace(':', '-')}_{short_id}_summary.json"
        with open(SHORT_TERM_MEMORY_DIR / short_filename, "w", encoding="utf-8") as f:
            json.dump(short_memory_data, f, indent=2)

        if DEBUG_MODE:
            logging.debug(f"📝 Summary written to: {SHORT_TERM_MEMORY_DIR / short_filename}")

    except Exception as e:
        logging.error(f"❌ Failed to write memory: {e}")


# ----------------------------
# 🧠 Memory Loader
# ----------------------------

def load_memory_history(limit: int = 20, mode: str = "long") -> dict:
    structured = []
    summarized = []

    try:
        if mode in ("long", "both"):
            long_files = sorted(STRUCTURED_MEMORY_DIR.glob("*.json"), key=lambda f: f.name, reverse=True)
            for f in long_files[:limit]:
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        structured.append(json.load(file))
                except Exception as e:
                    logging.warning(f"⚠️ Failed to load long memory file {f.name}: {e}")
    except Exception as e:
        logging.error(f"Failed to load structured memory: {e}")

    try:
        if mode in ("short", "both"):
            short_files = sorted(SHORT_TERM_MEMORY_DIR.glob("*_summary.json"), key=lambda f: f.name, reverse=True)
            for f in short_files[:limit]:
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        summarized.append(json.load(file))
                except Exception as e:
                    logging.warning(f"⚠️ Failed to load short summary file {f.name}: {e}")
    except Exception as e:
        logging.error(f"Failed to load short-term memory: {e}")

    if mode == "long":
        return {"structured": structured}
    elif mode == "short":
        return {"summarized": summarized}
    else:
        return {"structured": structured, "summarized": summarized}
