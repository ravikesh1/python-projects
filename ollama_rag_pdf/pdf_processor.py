import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


def load_pdf(file_path: str) -> list[Document]:
    loader = PyPDFLoader(file_path)
    return loader.load()


def split_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def process_uploaded_file(
    uploaded_file,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        pages = load_pdf(tmp_path)
        for page in pages:
            page.metadata["source"] = uploaded_file.name
        chunks = split_documents(pages, chunk_size, chunk_overlap)
    finally:
        os.unlink(tmp_path)

    return chunks
