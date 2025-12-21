import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import VECTORSTORE_DIR, EMBEDDING_MODEL

# We’ll keep a singleton-like cache of the vectorstore
_vectorstore = None

def get_vectorstore():
    """Load (or reuse) the persistent Chroma vector store."""
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    load_dotenv()
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    _vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
    )
    return _vectorstore

def get_relevant_docs(query: str, k: int = 4):
    """Return top-k relevant documents for the given natural language query."""
    vs = get_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": k})

    return retriever._get_relevant_documents(query, run_manager=None)

if __name__ == "__main__":
    # Quick manual tests
    examples = [
        "What is EPA per play and how is it stored in the DB?",
        "Which table holds season-level QB stats?",
        "How do I find the top 3 QBs by EPA per play in 2022?",
    ]

    for q in examples:
        print(f"\n=== Query: {q}")
        docs = get_relevant_docs(q, k=3)
        for i, d in enumerate(docs, start=1):
            print(f"\n--- Doc {i} (source={d.metadata.get('filename')}):")
            # Print only first 400 chars for brevity
            print(d.page_content[:400], "...")
