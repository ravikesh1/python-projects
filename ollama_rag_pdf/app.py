import streamlit as st
import requests

from config import settings
from pdf_processor import process_uploaded_file
from vector_store import (
    get_embedding_function,
    get_vector_store,
    add_documents,
    get_retriever,
)
from rag_chain import get_llm, create_rag_chain, query_with_sources


def check_ollama_connection(base_url: str) -> bool:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def fetch_ollama_models(base_url: str) -> list[str]:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except requests.ConnectionError:
        pass
    return []


def init_session_state():
    defaults = {
        "messages": [],
        "vector_store": None,
        "chain": None,
        "retriever": None,
        "ingested_files": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar():
    with st.sidebar:
        st.header("Configuration")

        base_url = st.text_input("Ollama URL", value=settings.ollama_base_url)
        connected = check_ollama_connection(base_url)
        if connected:
            st.success("Ollama connected")
        else:
            st.error("Cannot reach Ollama. Is it running?")
            return

        available_models = fetch_ollama_models(base_url)
        if not available_models:
            st.warning("No models found. Pull a model with `ollama pull <model>`.")
            return

        default_llm_idx = (
            available_models.index(settings.ollama_model)
            if settings.ollama_model in available_models
            else 0
        )
        llm_model = st.selectbox("LLM Model", options=available_models, index=default_llm_idx)

        default_embed_idx = (
            available_models.index(settings.ollama_embed_model)
            if settings.ollama_embed_model in available_models
            else 0
        )
        embed_model = st.selectbox(
            "Embedding Model", options=available_models, index=default_embed_idx
        )

        st.subheader("Text Splitting")
        chunk_size = st.slider("Chunk Size", 200, 2000, settings.chunk_size, step=100)
        chunk_overlap = st.slider("Chunk Overlap", 0, 500, settings.chunk_overlap, step=50)

        st.subheader("Upload PDFs")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
        )

        if uploaded_files and st.button("Ingest Documents"):
            with st.spinner("Processing and embedding documents..."):
                embed_fn = get_embedding_function(model=embed_model, base_url=base_url)
                vs = get_vector_store(embedding_function=embed_fn)

                all_chunks = []
                for f in uploaded_files:
                    if f.name not in st.session_state.ingested_files:
                        chunks = process_uploaded_file(f, chunk_size, chunk_overlap)
                        all_chunks.extend(chunks)
                        st.session_state.ingested_files.append(f.name)

                if all_chunks:
                    add_documents(vs, all_chunks)
                    st.session_state.vector_store = vs

                    retriever = get_retriever(vs)
                    llm = get_llm(model=llm_model, base_url=base_url)
                    chain = create_rag_chain(retriever, llm)

                    st.session_state.retriever = retriever
                    st.session_state.chain = chain

                    st.success(
                        f"Ingested {len(all_chunks)} chunks from "
                        f"{len(uploaded_files)} file(s)."
                    )
                else:
                    st.info("All files already ingested.")

        if st.session_state.ingested_files:
            st.subheader("Ingested Files")
            for fname in st.session_state.ingested_files:
                st.text(f"  {fname}")


def render_chat():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg:
                with st.expander("Source Documents"):
                    for i, src in enumerate(msg["sources"]):
                        st.markdown(
                            f"**Source {i + 1}** "
                            f"(Page {src.get('page', '?')}, {src.get('source', '?')})"
                        )
                        st.caption(src["content"])

    if question := st.chat_input("Ask a question about your documents"):
        if st.session_state.chain is None:
            st.warning("Please upload and ingest PDF documents first.")
            return

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = query_with_sources(
                    st.session_state.chain,
                    st.session_state.retriever,
                    question,
                )

            st.markdown(result["answer"])

            sources = []
            for doc in result["source_documents"]:
                sources.append({
                    "content": doc.page_content[:500],
                    "page": doc.metadata.get("page", "?"),
                    "source": doc.metadata.get("source", "?"),
                })

            if sources:
                with st.expander("Source Documents"):
                    for i, src in enumerate(sources):
                        st.markdown(
                            f"**Source {i + 1}** "
                            f"(Page {src['page']}, {src['source']})"
                        )
                        st.caption(src["content"])

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": sources,
        })


def main():
    st.set_page_config(page_title="PDF RAG Chat", page_icon="\U0001f4c4", layout="wide")
    st.title("PDF RAG Chat with Ollama")
    init_session_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
