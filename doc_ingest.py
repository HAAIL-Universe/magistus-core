# doc_ingest.py

import os
import logging
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PDFPlumberLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from config_loader import load_config


# ----------------------------
# 📁 Path Configuration
# ----------------------------
SOURCE_DIR = Path("data/source_docs")
INDEX_DIR = Path("data/faiss_index")
INDEX_NAME = "index"

SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf"]

# ----------------------------
# 🧠 Initialize
# ----------------------------
config = load_config()
DEBUG_MODE = config.get("debug_mode", False)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ----------------------------
# 🔍 File Loader Router
# ----------------------------

def load_document(filepath: Path):
    ext = filepath.suffix.lower()
    
    if ext == ".txt":
        return TextLoader(str(filepath), encoding="utf-8").load()
    elif ext == ".md":
        return UnstructuredMarkdownLoader(str(filepath)).load()
    elif ext == ".pdf":
        return PDFPlumberLoader(str(filepath)).load()
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# ----------------------------
# 🧩 Ingestion Pipeline
# ----------------------------

def ingest_documents():
    logging.info("Starting document ingestion...")

    if not SOURCE_DIR.exists():
        logging.warning(f"Source directory '{SOURCE_DIR}' does not exist. Nothing to ingest.")
        return

    all_docs = []

    for file in SOURCE_DIR.iterdir():
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            docs = load_document(file)
            all_docs.extend(docs)
            logging.info(f"Loaded: {file.name} ({len(docs)} chunks)")
        except Exception as e:
            logging.error(f"Failed to load {file.name}: {e}")

    if not all_docs:
        logging.warning("No valid documents found.")
        return

    # Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=750,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )

    split_docs = splitter.split_documents(all_docs)
    logging.info(f"Total chunks after splitting: {len(split_docs)}")

    # Vectorize
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    # Ensure index directory
    os.makedirs(INDEX_DIR, exist_ok=True)

    # Save FAISS index
    vectorstore.save_local(str(INDEX_DIR), index_name=INDEX_NAME)
    logging.info(f"FAISS index saved to '{INDEX_DIR}/{INDEX_NAME}'")

    logging.info("Ingestion complete.")


# ----------------------------
# 🔧 CLI Entry Point
# ----------------------------

if __name__ == "__main__":
    ingest_documents()
