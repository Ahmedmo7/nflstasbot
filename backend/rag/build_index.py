import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import DOCS_DIR, VECTORSTORE_DIR, EMBEDDING_MODEL

load_dotenv()  # load environment variables from .env file


def load_docs() -> list[Document]:
    """
    Load all markdown docs from the docs/ folder into LangChain Documents.

    - Recursively walks docs/ (not just top-level).
    - Infers category from the first subfolder under docs/:
        docs/schema/qb_season_stats.md      -> category="schema"
        docs/metrics/epa_and_success.md     -> category="metrics"
        docs/examples/sample_queries.md     -> category="examples"
        docs/other/whatever.md              -> category="other"
    - Stores filename + full path in metadata.
    """
    docs: list[Document] = []

    if not DOCS_DIR.exists():
        raise RuntimeError(f"DOCS_DIR does not exist: {DOCS_DIR}")

    for path in DOCS_DIR.rglob("*.md"):
        # Figure out category from relative path
        rel = path.relative_to(DOCS_DIR)
        parts = rel.parts

        if len(parts) > 1:
            category = parts[0]  # e.g. "schema", "metrics", "examples"
        else:
            category = "general"

        text = path.read_text(encoding="utf-8")
        metadata = {
            "source": str(path),
            "category": category,
            "filename": path.name,
            "rel_path": str(rel),
        }
        docs.append(Document(page_content=text, metadata=metadata))

    print(f"Loaded {len(docs)} raw docs from {DOCS_DIR}")
    return docs


def build_vectorstore():
    load_dotenv()  # ensure OPENAI_API_KEY etc.

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Load raw docs
    raw_docs = load_docs()
    if not raw_docs:
        raise RuntimeError("No docs found in docs/ directory.")

    # Split docs into smaller chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    split_docs = splitter.split_documents(raw_docs)

    # Optional: add a simple chunk index in metadata for debugging
    for i, d in enumerate(split_docs):
        d.metadata.setdefault("chunk_index", i)

    # Make sure vectorstore dir exists
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    # Create / overwrite Chroma index
    Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
    )

    # Persist to disk
    
    print(f"Built vector store at {VECTORSTORE_DIR} with {len(split_docs)} chunks.")


if __name__ == "__main__":
    build_vectorstore()
