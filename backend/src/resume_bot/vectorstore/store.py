"""
Qdrant vector store — high-performance, container-ready, metadata-filterable.

Configured to run in either:
  1. Distributed/server mode via QDRANT_URL (e.g., http://qdrant:6333 in Docker Compose or Cloud)
  2. Embedded local disk mode via QDRANT_PATH (when QDRANT_URL is not set)
"""

from __future__ import annotations
from typing import Any
from pathlib import Path
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

from resume_bot.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_PATH,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_DIMENSIONS,
    RETRIEVER_SEARCH_TYPE,
    RETRIEVER_K,
    RETRIEVER_FETCH_K,
    RETRIEVER_LAMBDA,
)
from resume_bot.vectorstore.embeddings import get_document_embeddings

_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """
    Return a singleton QdrantClient instance.
    Connects to remote/Docker Qdrant if QDRANT_URL is configured,
    otherwise uses local persistent storage at QDRANT_PATH.
    """
    global _qdrant_client
    if _qdrant_client is None:
        if QDRANT_URL:
            _qdrant_client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )
        else:
            QDRANT_PATH.mkdir(parents=True, exist_ok=True)
            _qdrant_client = QdrantClient(path=str(QDRANT_PATH))
    return _qdrant_client


# Backward-compatible alias
get_chroma_client = get_qdrant_client


def ensure_collection_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = EMBEDDING_DIMENSIONS,
) -> None:
    """Ensure the target collection exists in Qdrant with proper vector configuration."""
    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )


def get_vector_store(collection_name: str = QDRANT_COLLECTION_NAME) -> QdrantVectorStore:
    """
    Return (or create) a persistent Qdrant vector store collection.
    """
    client = get_qdrant_client()
    ensure_collection_exists(client, collection_name=collection_name)
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_document_embeddings(),
    )


def index_documents(
    chunks: list[Document],
    collection_name: str = QDRANT_COLLECTION_NAME,
    reset: bool = False,
) -> QdrantVectorStore:
    """
    Embed and store document chunks into Qdrant.

    When reset=True, recreates the collection to wipe existing points.

    Args:
        chunks:          Enriched chunks from the chunker.
        collection_name: Qdrant collection to use.
        reset:           If True, clears existing documents from the collection.

    Returns:
        The populated QdrantVectorStore.
    """
    client = get_qdrant_client()

    if reset and client.collection_exists(collection_name=collection_name):
        try:
            client.delete_collection(collection_name=collection_name)
        except Exception:
            pass

    ensure_collection_exists(client, collection_name=collection_name)

    store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_document_embeddings(),
    )

    if chunks:
        store.add_documents(documents=chunks)

    return store


def get_retriever(store: QdrantVectorStore | None = None, collection_name: str = QDRANT_COLLECTION_NAME):
    """
    Build an MMR retriever from the Qdrant vector store.

    MMR (Maximal Marginal Relevance) configuration:
      - k=5 final chunks returned to LLM
      - fetch_k=10 candidate pool considered before diversity re-ranking
      - lambda_mult=0.6 balances relevance (1.0) vs diversity (0.0)

    Args:
        store: An existing Qdrant store. If None, initializes from client.
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


def collection_is_populated(collection_name: str = QDRANT_COLLECTION_NAME) -> bool:
    """Check if the Qdrant collection exists and has points indexed."""
    try:
        client = get_qdrant_client()
        if not client.collection_exists(collection_name=collection_name):
            return False
        info = client.get_collection(collection_name=collection_name)
        return (info.points_count or 0) > 0
    except Exception:
        return False


def get_collection_stats(collection_name: str = QDRANT_COLLECTION_NAME) -> dict:
    """Return stats about the current collection for UI and CLI display."""
    try:
        client = get_qdrant_client()
        if not client.collection_exists(collection_name=collection_name):
            return {"document_count": 0, "collection": collection_name}
        info = client.get_collection(collection_name=collection_name)
        count = info.points_count or 0
        return {"document_count": count, "collection": collection_name}
    except Exception:
        return {"document_count": 0, "collection": collection_name}


def delete_collection(collection_name: str) -> bool:
    """Delete a Qdrant collection permanently."""
    try:
        client = get_qdrant_client()
        if client.collection_exists(collection_name=collection_name):
            client.delete_collection(collection_name=collection_name)
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
    return QDRANT_COLLECTION_NAME
