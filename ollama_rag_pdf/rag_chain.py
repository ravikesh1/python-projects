from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from config import settings

SYSTEM_TEMPLATE = """You are a helpful assistant that answers questions based on the provided context from PDF documents.

Use ONLY the following context to answer the question. If the context does not contain enough information to answer, say so clearly -- do not make up information.

Context:
{context}"""


def get_llm(model: str | None = None, base_url: str | None = None) -> ChatOllama:
    return ChatOllama(
        model=model or settings.ollama_model,
        base_url=base_url or settings.ollama_base_url,
    )


def format_documents(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain(retriever, llm: ChatOllama | None = None):
    llm = llm or get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("human", "{question}"),
    ])

    chain = (
        {
            "context": retriever | format_documents,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def query_with_sources(chain, retriever, question: str) -> dict:
    source_docs = retriever.invoke(question)
    answer = chain.invoke(question)

    return {
        "answer": answer,
        "source_documents": source_docs,
    }
