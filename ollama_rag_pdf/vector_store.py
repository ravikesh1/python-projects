from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import settings


def get_embedding_function(
    model: str | None = None,
    base_url: str | None = None,
) -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=model or settings.ollama_embed_model,
        base_url=base_url or settings.ollama_base_url,
    )


def get_vector_store(
    collection_name: str | None = None,
    persist_directory: str | None = None,
    embedding_function: OllamaEmbeddings | None = None,
) -> Chroma:
    return Chroma(
        collection_name=collection_name or settings.chroma_collection,
        persist_directory=persist_directory or settings.chroma_persist_dir,
        embedding_function=embedding_function or get_embedding_function(),
    )


def add_documents(vector_store: Chroma, documents: list[Document]) -> list[str]:
    return vector_store.add_documents(documents)


def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
