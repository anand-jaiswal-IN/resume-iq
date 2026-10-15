"""
Unit and integration tests for Phase 3: FastAPI REST and WebSocket endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from resume_bot.api.app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["websocket"] == "/ws/chat"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AI Resume Bot" in data["message"]


def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "collection_name" in data
    assert "document_count" in data


def test_resume_status_endpoint():
    response = client.get("/api/resume/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_loaded" in data
    assert "total_chunks" in data


def test_resume_links_endpoint():
    response = client.get("/api/resume/links")
    assert response.status_code == 200
    data = response.json()
    assert "total_links" in data
    assert isinstance(data["links"], list)


def test_resume_profile_endpoint():
    response = client.get("/api/resume/profile")
    # If a profile was extracted during Phase 2 tests, it will return 200
    if response.status_code == 200:
        data = response.json()
        assert "full_name" in data
        assert "skills" in data
        assert "languages" in data["skills"]
    else:
        assert response.status_code == 404


def test_chat_history_clear():
    session_id = "test-session"
    response = client.delete(f"/api/chat/history?session_id={session_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    hist_response = client.get(f"/api/chat/history?session_id={session_id}")
    assert hist_response.status_code == 200
    assert len(hist_response.json()["messages"]) == 0


def test_websocket_chat_connection():
    with client.websocket_connect("/ws/chat") as websocket:
        # Send a simple general greeting
        websocket.send_json({"message": "Hello!", "session_id": "ws-test"})

        # First message should be intent detection
        first_resp = websocket.receive_json()
        assert first_resp["type"] == "intent"
        assert first_resp["content"] in (
            "GENERAL_CONVERSATION",
            "FACTUAL_QA",
            "JD_EVALUATION",
            "RESUME_SUMMARY",
        )

        # Collect subsequent messages until "done"
        received_tokens = []
        is_done = False
        while not is_done:
            msg = websocket.receive_json()
            if msg["type"] == "token":
                received_tokens.append(msg["content"])
            elif msg["type"] == "done":
                is_done = True
                assert len(msg["content"]) > 0

        assert is_done is True
        assert len(received_tokens) > 0
