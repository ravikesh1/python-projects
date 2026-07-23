"""ChromaDB vector store for semantic document search."""

import chromadb
from pathlib import Path

CHROMA_PATH = str(Path(__file__).parent / "chroma_data")


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=CHROMA_PATH)


def setup(documents: list[dict]) -> None:
    """Create a collection and add documents with auto-generated embeddings."""
    client = get_client()

    # Delete if exists, then recreate
    try:
        client.delete_collection("medical_docs")
    except Exception:
        pass

    collection = client.create_collection(
        name="medical_docs",
        metadata={"description": "Healthcare knowledge base"},
    )

    collection.add(
        ids=[d["id"] for d in documents],
        documents=[d["text"] for d in documents],
        metadatas=[d["metadata"] for d in documents],
    )


def query_semantic(question: str, n_results: int = 3) -> dict:
    """Ask a plain English question — returns the most relevant documents by meaning."""
    client = get_client()
    collection = client.get_collection("medical_docs")
    return collection.query(query_texts=[question], n_results=n_results)


def query_with_filter(question: str, category: str, n_results: int = 3) -> dict:
    """Semantic search + metadata filter combined."""
    client = get_client()
    collection = client.get_collection("medical_docs")
    return collection.query(
        query_texts=[question],
        n_results=n_results,
        where={"category": category},
    )
