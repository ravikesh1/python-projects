import argparse
import os
import shutil
import sys

from config import settings
from pdf_processor import load_pdf, split_documents
from vector_store import (
    get_embedding_function,
    get_vector_store,
    add_documents,
    get_retriever,
)
from rag_chain import get_llm, create_rag_chain, query_with_sources


def cmd_ingest(args):
    embed_fn = get_embedding_function(model=args.embed_model)
    vs = get_vector_store(embedding_function=embed_fn)

    total_chunks = 0
    for pdf_path in args.files:
        if not os.path.isfile(pdf_path):
            print(f"Skipping {pdf_path}: file not found")
            continue

        print(f"Processing {pdf_path}...")
        pages = load_pdf(pdf_path)
        chunks = split_documents(pages, args.chunk_size, args.chunk_overlap)
        add_documents(vs, chunks)
        total_chunks += len(chunks)
        print(f"  {len(pages)} pages -> {len(chunks)} chunks")

    print(f"\nDone. Ingested {total_chunks} total chunks into ChromaDB.")


def cmd_query(args):
    embed_fn = get_embedding_function(model=args.embed_model)
    vs = get_vector_store(embedding_function=embed_fn)

    collection = vs._collection
    if collection.count() == 0:
        print("No documents ingested yet. Run: python cli.py ingest <pdf files>")
        return

    retriever = get_retriever(vs, k=args.top_k)
    llm = get_llm(model=args.model)
    chain = create_rag_chain(retriever, llm)

    print(f"RAG ready (model: {args.model or settings.ollama_model}, "
          f"embeddings: {args.embed_model or settings.ollama_embed_model}, "
          f"top-k: {args.top_k})")
    print("Type your question (or 'quit' to exit):\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            break

        result = query_with_sources(chain, retriever, question)
        print(f"\nAssistant: {result['answer']}\n")

        if result["source_documents"]:
            print("Sources:")
            for i, doc in enumerate(result["source_documents"], 1):
                source = doc.metadata.get("source", "?")
                page = doc.metadata.get("page", "?")
                preview = doc.page_content[:150].replace("\n", " ")
                print(f"  [{i}] {source} (page {page}): {preview}...")
            print()


def cmd_clear(args):
    persist_dir = settings.chroma_persist_dir
    if not os.path.exists(persist_dir):
        print("Nothing to clear — no vector store found.")
        return

    if not args.yes:
        answer = input(f"Delete vector store at '{persist_dir}'? [y/N] ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return

    shutil.rmtree(persist_dir)
    print(f"Cleared vector store at '{persist_dir}'.")


def main():
    parser = argparse.ArgumentParser(
        description="Ollama PDF RAG — ingest PDFs and query them via CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest PDF files into the vector store")
    p_ingest.add_argument("files", nargs="+", help="PDF file paths to ingest")
    p_ingest.add_argument("--embed-model", default=None, help="Ollama embedding model")
    p_ingest.add_argument("--chunk-size", type=int, default=None, help="Text chunk size")
    p_ingest.add_argument("--chunk-overlap", type=int, default=None, help="Text chunk overlap")
    p_ingest.set_defaults(func=cmd_ingest)

    # query
    p_query = subparsers.add_parser("query", help="Interactive Q&A against ingested documents")
    p_query.add_argument("--model", default=None, help="Ollama LLM model")
    p_query.add_argument("--embed-model", default=None, help="Ollama embedding model")
    p_query.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve")
    p_query.set_defaults(func=cmd_query)

    # clear
    p_clear = subparsers.add_parser("clear", help="Delete the vector store")
    p_clear.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
