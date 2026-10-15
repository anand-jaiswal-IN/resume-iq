"""
Unit tests for Qdrant Vector Store integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings
from qdrant_client import QdrantClient

from resume_bot.vectorstore.store import (
    get_qdrant_client,
    ensure_collection_exists,
    get_vector_store,
    index_documents,
    get_retriever,
    collection_is_populated,
    get_collection_stats,
    delete_collection,
)


@pytest.fixture
def test_client(tmp_path):
    """Provide an isolated local QdrantClient instance for testing."""
    client = QdrantClient(path=str(tmp_path / "qdrant_test_db"))
    return client


def test_qdrant_collection_lifecycle(test_client):
    col_name = "test_resume_col"
    fake_embeddings = FakeEmbeddings(size=768)

    # 1. Initially does not exist / not populated
    assert test_client.collection_exists(col_name) is False

    # 2. Ensure collection created
    ensure_collection_exists(test_client, col_name, vector_size=768)
    assert test_client.collection_exists(col_name) is True

    # 3. Patch get_qdrant_client and embedding to use isolated test objects
    with patch("resume_bot.vectorstore.store.get_qdrant_client", return_value=test_client), \
         patch("resume_bot.vectorstore.store.get_document_embeddings", return_value=fake_embeddings):

        assert collection_is_populated(col_name) is False
        stats = get_collection_stats(col_name)
        assert stats["document_count"] == 0

        # 4. Index documents
        docs = [
            Document(page_content="Senior Full Stack Python Engineer", metadata={"section": "experience"}),
            Document(page_content="Expert in React, TypeScript, FastAPI, Qdrant", metadata={"section": "skills"}),
        ]
        store = index_documents(docs, collection_name=col_name, reset=False)
        assert store is not None

        # 5. Check populated & stats
        assert collection_is_populated(col_name) is True
        stats = get_collection_stats(col_name)
        assert stats["document_count"] == 2

        # 6. Retrieve using MMR
        retriever = get_retriever(store=store, collection_name=col_name)
        results = retriever.invoke("FastAPI")
        assert len(results) > 0

        # 7. Delete collection
        success = delete_collection(col_name)
        assert success is True
        assert collection_is_populated(col_name) is False
