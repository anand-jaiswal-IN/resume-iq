"""
LCEL RAG chain and Enhanced RAG Pipeline.

Features:
  - Base LCEL RAG chain for grounded factual Q&A
  - Conversational multi-turn chain with RunnableWithMessageHistory
  - Enhanced RAG dispatcher (Intent routing, JD matching, query rewriting, candidate summary)
"""

from typing import Iterator

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from resume_bot.config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_OUTPUT_TOKENS,
)
from resume_bot.rag.prompts import resume_qa_prompt, resume_chat_prompt
from resume_bot.vectorstore.store import get_retriever


# ── LLM initialisation ────────────────────────────────────────────────────────

def get_llm(temperature: float = LLM_TEMPERATURE) -> ChatGoogleGenerativeAI:
    """Return the Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
        max_output_tokens=LLM_MAX_OUTPUT_TOKENS,
    )


# ── Context formatting ────────────────────────────────────────────────────────

def format_docs(docs: list[Document]) -> str:
    """
    Join retrieved document chunks into a single context string.
    Prefixes each chunk with its section label for traceability.
    """
    parts: list[str] = []
    for doc in docs:
        section = doc.metadata.get("section", "general").upper()
        page = doc.metadata.get("page", "?")
        parts.append(f"[{section} | Page {page}]\n{doc.page_content}")
    return "\n\n".join(parts)


# ── Self-healing retriever invocation ─────────────────────────────────────────

def safe_invoke_retriever(
    retriever: VectorStoreRetriever | None, query: str
) -> list[Document]:
    """
    Invoke retriever with self-healing recovery against stale collection UUIDs
    or deleted Chroma collections.
    """
    from resume_bot.vectorstore.store import get_active_collection_name

    if retriever is None:
        retriever = get_retriever(collection_name=get_active_collection_name())

    try:
        return retriever.invoke(query)
    except Exception as e:
        err_str = str(e).lower()
        if "does not exist" in err_str or "notfounderror" in type(e).__name__.lower():
            # Recreate a fresh retriever connected to the current collection
            fresh_retriever = get_retriever(collection_name=get_active_collection_name())
            return fresh_retriever.invoke(query)
        raise


# ── Simple one-shot RAG chain ─────────────────────────────────────────────────

def build_rag_chain(retriever: VectorStoreRetriever | None = None):
    """
    Build a single-turn LCEL RAG chain.
    """
    if retriever is None:
        from resume_bot.vectorstore.store import get_active_collection_name
        retriever = get_retriever(collection_name=get_active_collection_name())

    llm = get_llm()

    chain = (
        {
            "context": RunnableLambda(lambda q: format_docs(safe_invoke_retriever(retriever, q))),
            "question": RunnablePassthrough(),
        }
        | resume_qa_prompt
        | llm
        | StrOutputParser()
    )

    return chain


# ── Conversational multi-turn RAG chain ───────────────────────────────────────

_session_store: dict[str, ChatMessageHistory] = {}
_shared_conversational_chain = None


def _get_session_history(session_id: str) -> ChatMessageHistory:
    """Return or create a ChatMessageHistory for a given session."""
    if session_id not in _session_store:
        _session_store[session_id] = ChatMessageHistory()
    return _session_store[session_id]


def build_conversational_chain(retriever: VectorStoreRetriever | None = None):
    """
    Build a multi-turn conversational LCEL RAG chain with session memory.
    """
    if retriever is None:
        from resume_bot.vectorstore.store import get_active_collection_name
        retriever = get_retriever(collection_name=get_active_collection_name())

    llm = get_llm()

    core_chain = (
        {
            "context": RunnableLambda(
                lambda x: format_docs(safe_invoke_retriever(retriever, x["question"]))
            ),
            "question": RunnableLambda(lambda x: x["question"]),
            "chat_history": RunnableLambda(lambda x: x.get("chat_history", [])),
        }
        | resume_chat_prompt
        | llm
        | StrOutputParser()
    )

    chain_with_history = RunnableWithMessageHistory(
        core_chain,
        _get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    return chain_with_history


def get_shared_conversational_chain(force_refresh: bool = False, collection_name: str | None = None):
    """
    Get or build the shared conversational chain instance.
    """
    global _shared_conversational_chain
    if _shared_conversational_chain is None or force_refresh:
        from resume_bot.vectorstore.store import get_active_collection_name
        col = collection_name or get_active_collection_name()
        retriever = get_retriever(collection_name=col)
        _shared_conversational_chain = build_conversational_chain(retriever)
    return _shared_conversational_chain


def reset_conversational_chain() -> None:
    """
    Reset the shared conversational chain instance (e.g. after new resume upload).
    """
    global _shared_conversational_chain
    _shared_conversational_chain = None


def stream_conversational_answer(
    chain, question: str, session_id: str = "default"
) -> Iterator[str]:
    """
    Stream from the conversational chain with a specific session.
    """
    for chunk in chain.stream(
        {"question": question},
        config={"configurable": {"session_id": session_id}},
    ):
        # Extract text from chunk (handles TextAccessor or plain str)
        if hasattr(chunk, "text"):
            yield chunk.text
        elif isinstance(chunk, str):
            yield chunk
        else:
            yield str(chunk)


def clear_session(session_id: str = "default") -> None:
    """Clear the chat history for a given session."""
    if session_id in _session_store:
        _session_store[session_id].clear()


def get_session_history_messages(session_id: str = "default") -> list:
    """Return the chat history messages for a session."""
    return _get_session_history(session_id).messages
