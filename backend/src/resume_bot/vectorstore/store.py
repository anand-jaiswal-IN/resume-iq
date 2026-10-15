"""
ChromaDB vector store — persistent, developer-friendly, metadata-filterable.

Why ChromaDB for dev/testing?
  - Zero-config local SQLite persistence
  - Effortless metadata filtering (filter by section, candidate, etc.)
  - Python-native API
  - Easy to swap for FAISS/Pinecone in production (same LangChain interface)

ChromaDB → FAISS migration path (Phase 4):
  Replace Chroma(...) with FAISS.from_documents(...) and
  faiss_index.save_local() / FAISS.load_local() — zero chain changes needed.
"""

from __future__ import annotations
from typing import Any
from pathlib import Path
import chromadb

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from resume_bot.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    RETRIEVER_SEARCH_TYPE,
    RETRIEVER_K,
    RETRIEVER_FETCH_K,
    RETRIEVER_LAMBDA,
)
from resume_bot.vectorstore.embeddings import get_document_embeddings

_chroma_client: chromadb.api.ClientAPI | None = None


def get_chroma_client() -> chromadb.api.ClientAPI:
    """
    Return a singleton PersistentClient instance.
    Using a shared client prevents multi-client SQLite cache desync and
    stale collection UUID lookups.
    """
    global _chroma_client
    if _chroma_client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def get_vector_store(collection_name: str = CHROMA_COLLECTION_NAME) -> Chroma:
    """
    Return (or create) a persistent ChromaDB collection.
    Uses the shared persistent client to guarantee consistent collection IDs.
    """
    client = get_chroma_client()
    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_document_embeddings(),
    )


def index_documents(
    chunks: list[Document],
    collection_name: str = CHROMA_COLLECTION_NAME,
    reset: bool = False,
) -> Chroma:
    """
    Embed and store document chunks into ChromaDB.

    When reset=True, clears existing documents in-place rather than deleting the
    collection entity. This preserves the collection UUID and prevents
    NotFoundError in active retrievers and chains.

    Args:
        chunks:          Enriched chunks from the chunker.
        collection_name: ChromaDB collection to use.
        reset:           If True, clears existing documents from the collection.

    Returns:
        The populated Chroma vector store.
    """
    client = get_chroma_client()

    if reset:
        try:
            col = client.get_or_create_collection(name=collection_name)
            existing = col.get()
            if existing and existing.get("ids"):
                col.delete(ids=existing["ids"])
        except Exception:
            # Fallback if collection was in an inconsistent state
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass

    store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_document_embeddings(),
    )

    if chunks:
        store.add_documents(documents=chunks)

    return store


def get_retriever(store: Chroma | None = None, collection_name: str = CHROMA_COLLECTION_NAME):
    """
    Build an MMR retriever from the vector store.

    MMR (Maximal Marginal Relevance) configuration:
      - k=5 final chunks returned to LLM
      - fetch_k=10 candidate pool considered before diversity re-ranking
      - lambda_mult=0.6 balances relevance (1.0) vs diversity (0.0)

    Args:
        store: An existing Chroma store. If None, loads from disk.
        collection_name: Collection name to use if store is None.

    Returns:
        A LangChain VectorStoreRetriever ready for use in LCEL chains.
    """
    if store is None:
        store = get_vector_store(collection_name)

    return store.as_retriever(
        search_type=RETRIEVER_SEARCH_TYPE,
        search_kwargs={
            "k": RETRIEVER_K,
            "fetch_k": RETRIEVER_FETCH_K,
            "lambda_mult": RETRIEVER_LAMBDA,
        },
    )


def collection_is_populated(collection_name: str = CHROMA_COLLECTION_NAME) -> bool:
    """Check if the ChromaDB collection already has documents indexed."""
    try:
        client = get_chroma_client()
        col = client.get_or_create_collection(name=collection_name)
        return col.count() > 0
    except Exception:
        return False


def get_collection_stats(collection_name: str = CHROMA_COLLECTION_NAME) -> dict:
    """Return stats about the current collection for UI and CLI display."""
    try:
        client = get_chroma_client()
        col = client.get_or_create_collection(name=collection_name)
        count = col.count()
        return {"document_count": count, "collection": collection_name}
    except Exception:
        return {"document_count": 0, "collection": collection_name}


def delete_collection(collection_name: str) -> bool:
    """Delete a ChromaDB collection permanently."""
    try:
        client = get_chroma_client()
        client.delete_collection(name=collection_name)
        return True
    except Exception:
        return False


def get_active_collection_name() -> str:
    """Return the collection name for the active resume or default."""
    try:
        from resume_bot.rag.registry import get_active_resume
        active = get_active_resume()
        if active and active.collection_name:
            return active.collection_name
    except Exception:
        pass
    return CHROMA_COLLECTION_NAME
